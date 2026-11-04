"""`flask seed` (Fase 2c): gera o que o PLAN.md pede, passando pelas regras de app/services."""

import pytest
from sqlalchemy import func, select

from app import create_app
from app.models import (
    AcademicYear,
    AssessmentScore,
    ClassSubjectTerm,
    Comment,
    CommentVisibility,
    Enrollment,
    KodeshClass,
    ScoreStatus,
    Student,
    StudentYear,
    TermAttendance,
)
from app.seed import SeedError, seed_demo
from app.services.years import get_active_year

pytestmark = pytest.mark.usefixtures("_database")


@pytest.fixture
def seeded(db_session):
    summary = seed_demo()
    return db_session, summary


def count(s, stmt):
    return s.scalar(select(func.count()).select_from(stmt.subquery()))


def test_seed_years(seeded):
    s, _ = seeded
    statuses = sorted(y.status.value for y in s.scalars(select(AcademicYear)))
    assert statuses == ["active", "archived"]
    assert get_active_year().name == "2027"
    assert all(len(y.terms) == 3 for y in s.scalars(select(AcademicYear)))


def test_seed_classes_and_students(seeded):
    s, summary = seeded
    active = get_active_year()
    assert count(s, select(KodeshClass).where(KodeshClass.academic_year_id == active.id)) == 6
    assert summary.students == 75
    assert count(s, select(StudentYear).where(StudentYear.academic_year_id == active.id)) == 75


def test_seed_has_two_students_with_the_same_name(seeded):
    s, _ = seeded
    same = count(
        s, select(Student).where(Student.first_name == "Gabriel", Student.last_name == "Cohen")
    )
    assert same == 2


def test_seed_has_rabbis_changing_between_terms(seeded):
    s, _ = seeded
    assert count(s, select(ClassSubjectTerm)) > 0


def test_seed_scores_have_decimals_and_absents(seeded):
    s, _ = seeded
    scores = list(s.scalars(select(AssessmentScore)))
    assert any(x.score is not None and x.score % 1 != 0 for x in scores)
    assert any(x.status == ScoreStatus.ABSENT for x in scores)
    assert any(x.status == ScoreStatus.EXEMPT for x in scores)


def test_seed_has_one_class_transfer(seeded):
    s, _ = seeded
    active = get_active_year()
    closed = count(
        s,
        select(Enrollment)
        .join(KodeshClass, Enrollment.kodesh_class_id == KodeshClass.id)
        .where(KodeshClass.academic_year_id == active.id, Enrollment.end_date.is_not(None)),
    )
    assert closed == 1


def test_seed_has_attendance_and_comments(seeded):
    s, _ = seeded
    assert count(s, select(TermAttendance)) > 0
    assert count(s, select(Comment).where(Comment.visibility == CommentVisibility.PUBLIC)) > 0
    assert count(s, select(Comment).where(Comment.visibility == CommentVisibility.INTERNAL)) > 0


def test_seed_refuses_a_database_with_data(seeded):
    with pytest.raises(SeedError, match="já tem dados"):
        seed_demo()


def test_seed_command_is_blocked_in_production(monkeypatch):
    from config import ProductionConfig

    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", "x")
    monkeypatch.setattr(ProductionConfig, "SQLALCHEMY_DATABASE_URI", "mysql+pymysql://u:p@h/db")
    app = create_app("production")
    result = app.test_cli_runner().invoke(args=["seed"])
    assert result.exit_code != 0
    assert "produção" in result.output
