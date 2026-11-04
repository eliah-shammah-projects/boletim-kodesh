"""Modelo de dados (Fase 2a): migração, collation e as regras que o próprio banco garante.

Rodam contra o MySQL de teste (no GitHub Actions; localmente são pulados sem MySQL).
"""

from datetime import date
from decimal import Decimal

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, OperationalError

from app.extensions import db
from app.models import (
    AcademicYear,
    Assessment,
    AssessmentScore,
    ClassSubject,
    Enrollment,
    KodeshClass,
    ScoreStatus,
    Student,
    StudentYear,
    Subject,
    Term,
    TermAttendance,
    User,
    UserRole,
)

pytestmark = pytest.mark.usefixtures("_database")

# Violação de CHECK no MySQL chega como OperationalError (3819); de UNIQUE, como IntegrityError.
DB_ERRORS = (IntegrityError, OperationalError)


def test_migration_matches_models(db_conn):
    """Nada no código que a migração não tenha (e vice-versa)."""
    context = MigrationContext.configure(db_conn, opts={"compare_type": True})
    diff = compare_metadata(context, db.metadata)
    assert diff == []


def test_all_tables_use_utf8mb4_unicode_ci(db_conn):
    rows = db_conn.execute(
        text(
            "SELECT TABLE_NAME, TABLE_COLLATION FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = DATABASE()"
        )
    ).all()
    tables = {name: collation for name, collation in rows}
    assert set(db.metadata.tables) <= set(tables)
    wrong = {n: c for n, c in tables.items() if c != "utf8mb4_unicode_ci"}
    assert wrong == {}


@pytest.fixture
def setup(db_session):
    """Um ano, um trimestre, um rabino, um shiur com Gemara, um aluno matriculado e uma prova."""
    s = db_session
    rabbi = User(name="Rav Teste", role=UserRole.RABBI)
    year = AcademicYear(name="2099", start_date=date(2099, 2, 1))
    s.add_all([rabbi, year])
    s.flush()
    term = Term(academic_year_id=year.id, number=1, name="1º trimestre")
    kclass = KodeshClass(academic_year_id=year.id, name="Shiur Teste", homeroom_rabbi_id=rabbi.id)
    subject = Subject(name="Gemara Teste")
    student = Student(first_name="Ariel", last_name="Szwarc", hebrew_name="אריאל")
    s.add_all([term, kclass, subject, student])
    s.flush()
    cs = ClassSubject(kodesh_class_id=kclass.id, subject_id=subject.id)
    sy = StudentYear(student_id=student.id, academic_year_id=year.id, school_grade=10)
    s.add_all([cs, sy])
    s.flush()
    enrollment = Enrollment(
        student_year_id=sy.id, kodesh_class_id=kclass.id, start_date=date(2099, 2, 1)
    )
    assessment = Assessment(
        class_subject_id=cs.id, term_id=term.id, name="Prova 1", max_score=Decimal("10")
    )
    s.add_all([enrollment, assessment])
    s.flush()
    return {
        "s": s,
        "year": year,
        "term": term,
        "class": kclass,
        "enrollment": enrollment,
        "assessment": assessment,
        "student": student,
        "student_year": sy,
    }


def test_defaults(setup):
    year, kclass, student = setup["year"], setup["class"], setup["student"]
    setup["s"].refresh(year)
    setup["s"].refresh(kclass)
    assert year.grade_scale_max == Decimal("10.0")
    assert kclass.color == "azul"
    assert student.is_active is True
    assert student.created_at is not None


def test_hebrew_name_round_trip(setup):
    s = setup["s"]
    s.expire_all()
    student = s.scalar(select(Student).where(Student.id == setup["student"].id))
    assert student.hebrew_name == "אריאל"


def test_score_is_decimal_with_one_place(setup):
    s = setup["s"]
    score = AssessmentScore(
        assessment_id=setup["assessment"].id,
        enrollment_id=setup["enrollment"].id,
        score=Decimal("6.6"),
        status=ScoreStatus.GRADED,
    )
    s.add(score)
    s.flush()
    s.expire_all()
    stored = s.get(AssessmentScore, score.id)
    assert stored.score == Decimal("6.6")
    assert isinstance(stored.score, Decimal)


@pytest.mark.parametrize(
    ("score", "status"),
    [
        (None, ScoreStatus.GRADED),  # nota lançada precisa de valor
        (Decimal("5"), ScoreStatus.ABSENT),  # ausente não tem nota
        (Decimal("5"), ScoreStatus.EXEMPT),  # dispensado não tem nota
        (Decimal("-1"), ScoreStatus.GRADED),  # nota negativa
    ],
)
def test_invalid_score_is_rejected(setup, score, status):
    s = setup["s"]
    s.add(
        AssessmentScore(
            assessment_id=setup["assessment"].id,
            enrollment_id=setup["enrollment"].id,
            score=score,
            status=status,
        )
    )
    with pytest.raises(DB_ERRORS):
        s.flush()


def test_absent_without_score_is_accepted(setup):
    s = setup["s"]
    s.add(
        AssessmentScore(
            assessment_id=setup["assessment"].id,
            enrollment_id=setup["enrollment"].id,
            score=None,
            status=ScoreStatus.ABSENT,
        )
    )
    s.flush()


def test_one_score_per_student_per_assessment(setup):
    s = setup["s"]
    for _ in range(2):
        s.add(
            AssessmentScore(
                assessment_id=setup["assessment"].id,
                enrollment_id=setup["enrollment"].id,
                score=Decimal("8"),
                status=ScoreStatus.GRADED,
            )
        )
    with pytest.raises(DB_ERRORS):
        s.flush()


@pytest.mark.parametrize(("held", "absences", "lates"), [(10, 11, 0), (10, 0, 11), (-1, 0, 0)])
def test_attendance_cannot_exceed_classes_held(setup, held, absences, lates):
    s = setup["s"]
    s.add(
        TermAttendance(
            enrollment_id=setup["enrollment"].id,
            term_id=setup["term"].id,
            classes_held=held,
            absences=absences,
            lates=lates,
        )
    )
    with pytest.raises(DB_ERRORS):
        s.flush()


def test_school_grade_must_be_8_to_12(setup):
    s = setup["s"]
    other = Student(first_name="Outro", last_name="Aluno")
    s.add(other)
    s.flush()
    s.add(StudentYear(student_id=other.id, academic_year_id=setup["year"].id, school_grade=7))
    with pytest.raises(DB_ERRORS):
        s.flush()


def test_student_once_per_year(setup):
    s = setup["s"]
    s.add(
        StudentYear(
            student_id=setup["student"].id, academic_year_id=setup["year"].id, school_grade=10
        )
    )
    with pytest.raises(DB_ERRORS):
        s.flush()


def test_shiur_color_must_be_in_palette(setup):
    s = setup["s"]
    s.add(KodeshClass(academic_year_id=setup["year"].id, name="Shiur Roxo", color="roxo"))
    with pytest.raises(DB_ERRORS):
        s.flush()


def test_term_number_unique_per_year(setup):
    s = setup["s"]
    s.add(Term(academic_year_id=setup["year"].id, number=1, name="Repetido"))
    with pytest.raises(DB_ERRORS):
        s.flush()


def test_external_id_is_unique_but_optional(setup):
    s = setup["s"]
    s.add_all(
        [
            Student(first_name="A", last_name="Sem matrícula"),
            Student(first_name="B", last_name="Sem matrícula"),
        ]
    )
    s.flush()  # várias sem matrícula: ok
    s.add_all(
        [
            Student(first_name="C", last_name="X", external_id="123"),
            Student(first_name="D", last_name="Y", external_id="123"),
        ]
    )
    with pytest.raises(DB_ERRORS):
        s.flush()
