"""Regras de negócio da seção 4 do PLAN.md (app/services), contra MySQL."""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy import func, select

from app.extensions import db
from app.models import (
    AssessmentFile,
    AssessmentScore,
    AuditLog,
    ClassSubjectTerm,
    CommentCategory,
    FileKind,
    ReviewStatus,
    ScoreStatus,
    YearStatus,
)
from app.services import attendance, comments, grades, review, years
from app.services.classes import (
    active_enrollment,
    effective_teacher,
    enroll,
    enrollments_in_term,
    move_to_class,
    remove_from_class,
    review_status,
    transfer,
)
from app.services.errors import (
    ConflictError,
    LockedError,
    PermissionDenied,
    ValidationError,
)
from app.services.reports import build_annual_report, build_term_report
from tests.factories import (
    AdminFactory,
    AssessmentFactory,
    ClassFactory,
    ClassSubjectFactory,
    EnrollmentFactory,
    SubjectFactory,
    TermFactory,
    UserFactory,
    YearFactory,
)

pytestmark = pytest.mark.usefixtures("_database")


@pytest.fixture
def w(db_session):
    """Um ano com 2 trimestres, um shiur com Gemara (do rabino da turma) e Chumash (outro rabino),
    um aluno matriculado e uma prova de Gemara no 1º trimestre."""
    year = YearFactory(name="2100", grade_scale_max=Decimal("10.0"))
    t1 = TermFactory(
        academic_year=year, number=1, start_date=date(2100, 2, 1), end_date=date(2100, 5, 31)
    )
    t2 = TermFactory(academic_year=year, number=2)
    rabbi = UserFactory(name="Rav Levi")
    other = UserFactory(name="Rav Cohen")
    admin = AdminFactory()
    kclass = ClassFactory(academic_year=year, name="Shiur Alef", homeroom_rabbi=rabbi)
    gemara = ClassSubjectFactory(kodesh_class=kclass, subject=SubjectFactory(name="Gemara"))
    chumash = ClassSubjectFactory(
        kodesh_class=kclass, subject=SubjectFactory(name="Chumash"), default_teacher=other
    )
    enrollment = EnrollmentFactory(kodesh_class=kclass, start_date=date(2100, 2, 1))
    prova = AssessmentFactory(class_subject=gemara, term=t1, name="Prova 1", sort_order=1)
    return SimpleNamespace(
        s=db_session,
        year=year,
        t1=t1,
        t2=t2,
        rabbi=rabbi,
        other=other,
        admin=admin,
        kclass=kclass,
        gemara=gemara,
        chumash=chumash,
        enrollment=enrollment,
        sy=enrollment.student_year,
        prova=prova,
    )


# ---------- Ano letivo ----------


def test_create_year_with_three_terms(db_session):
    year = years.create_year("2101", date(2101, 2, 1))
    assert year.status == YearStatus.ACTIVE
    assert [t.name for t in year.terms] == ["1º trimestre", "2º trimestre", "3º trimestre"]


def test_only_one_active_year(w):
    with pytest.raises(ConflictError, match="Feche"):
        years.create_year("2101", date(2101, 2, 1))
    years.archive_year(w.year)
    new = years.create_year("2101", date(2101, 2, 1))
    assert years.get_active_year() == new
    assert years.count_active_years() == 1


def test_archived_year_is_read_only(w):
    years.archive_year(w.year)
    with pytest.raises(LockedError, match="fechado"):
        grades.set_score(w.rabbi, w.prova, w.enrollment, "8")
    with pytest.raises(LockedError):
        years.set_grade_scale(w.year, Decimal("20"))


def test_scale_cannot_change_after_scores(w):
    years.set_grade_scale(w.year, Decimal("20"))  # sem notas: pode
    assert w.year.grade_scale_max == Decimal("20")
    grades.set_score(w.rabbi, w.prova, w.enrollment, "8")
    with pytest.raises(ConflictError, match="notas"):
        years.set_grade_scale(w.year, Decimal("10"))


# ---------- Rabino efetivo ----------


def test_effective_teacher_chain(w):
    # sem rabino próprio: o rabino da turma
    assert effective_teacher(w.gemara, w.t1) == w.rabbi
    # com rabino padrão
    assert effective_teacher(w.chumash, w.t1) == w.other
    # com rabino do trimestre: vale só naquele trimestre
    substitute = UserFactory(name="Rav Azulay")
    w.s.add(
        ClassSubjectTerm(class_subject_id=w.chumash.id, term_id=w.t2.id, teacher_id=substitute.id)
    )
    w.s.flush()
    assert effective_teacher(w.chumash, w.t2) == substitute
    assert effective_teacher(w.chumash, w.t1) == w.other


# ---------- Matrículas e troca de turma ----------


def test_one_active_enrollment(w):
    assert active_enrollment(w.sy) == w.enrollment
    with pytest.raises(ConflictError, match="troca de turma"):
        enroll(w.sy, w.kclass, date(2100, 3, 1))


def test_transfer_closes_old_and_opens_new(w):
    bet = ClassFactory(academic_year=w.year, name="Shiur Bet")
    new = transfer(w.sy, bet, date(2100, 4, 1))
    w.s.refresh(w.enrollment)
    assert w.enrollment.end_date == date(2100, 3, 31)
    assert active_enrollment(w.sy) == new
    assert new.kodesh_class_id == bet.id
    # as duas matrículas aparecem no 1º trimestre
    assert [e.id for e in enrollments_in_term(w.sy, w.t1)] == [w.enrollment.id, new.id]


def test_transfer_to_class_of_other_year_is_rejected(w):
    other_year = YearFactory(name="2099", status=YearStatus.ARCHIVED)
    old_class = ClassFactory(academic_year=other_year)
    with pytest.raises(ValidationError, match="outro ano"):
        transfer(w.sy, old_class, date(2100, 4, 1))
    # nada mudou: o aluno continua no shiur atual
    assert active_enrollment(w.sy) == w.enrollment
    assert w.enrollment.end_date is None


def test_remove_from_class_keeps_the_enrollment(w):
    closed = remove_from_class(w.sy, date(2100, 4, 1))
    assert closed.id == w.enrollment.id
    assert closed.end_date == date(2100, 4, 1)
    assert active_enrollment(w.sy) is None


def test_move_without_records_just_corrects_the_class(w):
    bet = ClassFactory(academic_year=w.year, name="Shiur Bet")
    moved = move_to_class(w.sy, bet, w.enrollment.start_date)  # mesmo dia: correção
    assert moved.id == w.enrollment.id
    assert moved.kodesh_class_id == bet.id
    assert moved.end_date is None


def test_move_with_records_is_a_transfer(w):
    grades.set_score(w.rabbi, w.prova, w.enrollment, "8")
    bet = ClassFactory(academic_year=w.year, name="Shiur Bet")
    new = move_to_class(w.sy, bet, date(2100, 4, 1))
    assert new.id != w.enrollment.id
    w.s.refresh(w.enrollment)
    assert w.enrollment.kodesh_class_id == w.kclass.id  # a nota fica no shiur antigo
    assert w.enrollment.end_date == date(2100, 3, 31)


# ---------- Notas ----------


def test_set_score_creates_updates_deletes_and_audits(w):
    score = grades.set_score(w.rabbi, w.prova, w.enrollment, "8,5")
    assert score.score == Decimal("8.5")
    assert score.status == ScoreStatus.GRADED
    grades.set_score(w.rabbi, w.prova, w.enrollment, "a")
    w.s.refresh(score)
    assert score.status == ScoreStatus.ABSENT
    assert score.score is None
    assert grades.set_score(w.rabbi, w.prova, w.enrollment, "") is None
    remaining = w.s.scalar(select(func.count()).select_from(AssessmentScore))
    assert remaining == 0
    actions = list(
        w.s.scalars(
            select(AuditLog.action)
            .where(AuditLog.entity_type == "assessment_scores")
            .order_by(AuditLog.id)
        )
    )
    assert actions == ["create", "update", "delete"]


def test_score_above_max_is_rejected(w):
    with pytest.raises(ValidationError, match="entre 0 e 10"):
        grades.set_score(w.rabbi, w.prova, w.enrollment, "11")


def test_score_for_student_of_other_class_is_rejected(w):
    outsider = EnrollmentFactory(kodesh_class=ClassFactory(academic_year=w.year))
    with pytest.raises(ValidationError, match="não está neste shiur"):
        grades.set_score(w.rabbi, w.prova, outsider, "8")


def test_new_assessment_uses_year_scale_by_default(w):
    prova = grades.create_assessment(w.rabbi, w.gemara, w.t1, "Prova 2")
    assert prova.max_score == Decimal("10.0")
    assert prova.sort_order == 2
    trabalho = grades.create_assessment(
        w.rabbi, w.gemara, w.t1, "Trabalho", max_score=Decimal("20")
    )
    assert trabalho.max_score == Decimal("20")


def test_assessment_with_scores_cannot_be_deleted(w):
    grades.set_score(w.rabbi, w.prova, w.enrollment, "8")
    with pytest.raises(ConflictError, match="notas ou scans"):
        grades.delete_assessment(w.rabbi, w.prova)


def test_assessment_with_scan_cannot_be_deleted(w):
    w.s.add(
        AssessmentFile(
            assessment_id=w.prova.id,
            enrollment_id=w.enrollment.id,
            kind=FileKind.STUDENT_SCAN,
            storage_key="scans/teste-1.pdf",
            mime_type="application/pdf",
            size_bytes=10,
        )
    )
    w.s.flush()
    with pytest.raises(ConflictError):
        grades.delete_assessment(w.rabbi, w.prova)


def test_empty_assessment_can_be_deleted(w):
    prova = grades.create_assessment(w.rabbi, w.gemara, w.t1, "Prova errada")
    grades.delete_assessment(w.rabbi, prova)
    assert w.s.get(type(prova), prova.id) is None


# ---------- Travamento ----------


def test_locked_term_blocks_editing(w):
    review.lock_term(w.admin, w.t1)
    with pytest.raises(LockedError, match="travado"):
        grades.set_score(w.rabbi, w.prova, w.enrollment, "8")
    with pytest.raises(LockedError):
        attendance.save_attendance(w.rabbi, w.enrollment, w.t1, 40, 1, 0)
    with pytest.raises(LockedError):
        comments.save_public_comment(w.rabbi, w.enrollment, w.t1, CommentCategory.GENERAL, "Bom.")
    review.unlock_term(w.admin, w.t1)
    grades.set_score(w.rabbi, w.prova, w.enrollment, "8")


def test_only_admin_locks_terms(w):
    with pytest.raises(PermissionDenied):
        review.lock_term(w.rabbi, w.t1)


def test_ready_for_review_only_admin_edits(w):
    review.submit_for_review(w.rabbi, w.kclass, w.t1)
    with pytest.raises(LockedError, match="revisão"):
        grades.set_score(w.rabbi, w.prova, w.enrollment, "8")
    grades.set_score(w.admin, w.prova, w.enrollment, "8")  # a direção pode corrigir notas


def test_approved_blocks_everyone(w):
    review.submit_for_review(w.rabbi, w.kclass, w.t1)
    review.approve(w.admin, w.kclass, w.t1)
    with pytest.raises(LockedError, match="liberados"):
        grades.set_score(w.admin, w.prova, w.enrollment, "8")


# ---------- Frequência ----------


def test_save_attendance_and_update(w):
    rec = attendance.save_attendance(w.rabbi, w.enrollment, w.t1, 48, 2, 1)
    assert attendance.presence_percent(rec.classes_held, rec.absences) == Decimal("95.8")
    attendance.save_attendance(w.rabbi, w.enrollment, w.t1, 48, 3, 1)
    w.s.refresh(rec)
    assert rec.absences == 3
    with pytest.raises(ValidationError, match="faltas"):
        attendance.save_attendance(w.rabbi, w.enrollment, w.t1, 10, 11, 0)


# ---------- Comentários ----------


def test_only_homeroom_rabbi_writes_public_comments(w):
    comments.save_public_comment(w.rabbi, w.enrollment, w.t1, CommentCategory.GENERAL, "Muito bom.")
    with pytest.raises(PermissionDenied, match="rabino da turma"):
        comments.save_public_comment(w.other, w.enrollment, w.t1, CommentCategory.GENERAL, "x")
    with pytest.raises(PermissionDenied):  # nem a direção (decisão do usuário)
        comments.save_public_comment(w.admin, w.enrollment, w.t1, CommentCategory.BEHAVIOR, "x")


def test_one_public_comment_of_each_kind_per_term(w):
    first = comments.save_public_comment(w.rabbi, w.enrollment, w.t1, CommentCategory.GENERAL, "A")
    again = comments.save_public_comment(w.rabbi, w.enrollment, w.t1, CommentCategory.GENERAL, "B")
    assert first.id == again.id
    assert again.text == "B"
    behavior = comments.save_public_comment(
        w.rabbi, w.enrollment, w.t1, CommentCategory.BEHAVIOR, "C"
    )
    assert behavior.id != first.id
    other_term = comments.save_public_comment(
        w.rabbi, w.enrollment, w.t2, CommentCategory.GENERAL, "D"
    )
    assert other_term.id != first.id


def test_public_comment_limit_survives_class_change(w):
    first = comments.save_public_comment(w.rabbi, w.enrollment, w.t1, CommentCategory.GENERAL, "A")
    bet_rabbi = UserFactory()
    bet = ClassFactory(academic_year=w.year, homeroom_rabbi=bet_rabbi)
    new = transfer(w.sy, bet, date(2100, 4, 1))
    again = comments.save_public_comment(bet_rabbi, new, w.t1, CommentCategory.GENERAL, "B")
    assert again.id == first.id


def test_empty_or_long_comment_is_rejected(w):
    with pytest.raises(ValidationError):
        comments.save_public_comment(w.rabbi, w.enrollment, w.t1, CommentCategory.GENERAL, "  ")
    with pytest.raises(ValidationError, match="600"):
        comments.save_public_comment(
            w.rabbi, w.enrollment, w.t1, CommentCategory.GENERAL, "x" * 601
        )


def test_internal_notes_any_rabbi_unlimited(w):
    comments.add_internal_note(w.other, w.enrollment, w.t1, "Nota 1")
    comments.add_internal_note(w.other, w.enrollment, w.t1, "Nota 2")


# ---------- Revisão ----------


def test_review_flow(w):
    assert review_status(w.kclass, w.t1) == ReviewStatus.OPEN
    with pytest.raises(PermissionDenied):
        review.submit_for_review(w.other, w.kclass, w.t1)
    with pytest.raises(ConflictError, match="pronto antes"):
        review.approve(w.admin, w.kclass, w.t1)
    review.submit_for_review(w.rabbi, w.kclass, w.t1)
    review.return_to_rabbi(w.admin, w.kclass, w.t1)
    assert review_status(w.kclass, w.t1) == ReviewStatus.OPEN
    review.submit_for_review(w.rabbi, w.kclass, w.t1)
    with pytest.raises(PermissionDenied):
        review.approve(w.rabbi, w.kclass, w.t1)
    assert review.can_send_reports(w.kclass, w.t1) is False
    review.approve(w.admin, w.kclass, w.t1)
    assert review.can_send_reports(w.kclass, w.t1) is True
    review.reopen(w.admin, w.kclass, w.t1)
    assert review_status(w.kclass, w.t1) == ReviewStatus.OPEN


# ---------- Boletim ----------


def test_report_content(w):
    hidden = AssessmentFactory(
        class_subject=w.gemara, term=w.t1, name="Controle", include_in_report=False
    )
    trabalho = AssessmentFactory(
        class_subject=w.gemara, term=w.t1, name="Trabalho", max_score=Decimal("20"), sort_order=2
    )
    grades.set_score(w.rabbi, w.prova, w.enrollment, "9,5")
    grades.set_score(w.rabbi, hidden, w.enrollment, "3")
    grades.set_score(w.rabbi, trabalho, w.enrollment, "18")
    attendance.save_attendance(w.rabbi, w.enrollment, w.t1, 48, 2, 3)
    comments.save_public_comment(
        w.rabbi, w.enrollment, w.t1, CommentCategory.GENERAL, "Ótimo trimestre."
    )
    comments.save_public_comment(
        w.rabbi, w.enrollment, w.t1, CommentCategory.BEHAVIOR, "Respeitoso."
    )
    comments.add_internal_note(w.rabbi, w.enrollment, w.t1, "ANOTAÇÃO SECRETA")

    report = build_term_report(w.sy, w.t1)

    # Chumash não tem prova marcada: não aparece.
    assert [s.name for s in report.subjects] == ["Gemara"]
    gemara = report.subjects[0]
    assert gemara.teacher_name == "Rav Levi"
    assert [(x.assessment_name, x.score, x.max_score) for x in gemara.scores] == [
        ("Prova 1", Decimal("9.5"), Decimal("10.0")),
        ("Trabalho", Decimal("18.0"), Decimal("20.0")),
    ]
    assert report.attendance.presence == Decimal("95.8")
    assert report.attendance.lates == 3
    assert report.general_comment == "Ótimo trimestre."
    assert report.behavior_comment == "Respeitoso."
    assert "ANOTAÇÃO SECRETA" not in repr(report)
    assert report.school_grade == "1º colegial"
    assert report.homeroom_rabbi_name == "Rav Levi"
    assert report.is_draft is True
    assert report.changed_class is False


def test_report_never_has_scans(w):
    w.s.add(
        AssessmentFile(
            assessment_id=w.prova.id,
            enrollment_id=w.enrollment.id,
            kind=FileKind.STUDENT_SCAN,
            storage_key="scans/segredo.pdf",
            mime_type="application/pdf",
            size_bytes=10,
        )
    )
    w.s.flush()
    grades.set_score(w.rabbi, w.prova, w.enrollment, "8")
    assert "segredo" not in repr(build_term_report(w.sy, w.t1))


def test_report_is_final_only_after_approval(w):
    review.submit_for_review(w.rabbi, w.kclass, w.t1)
    assert build_term_report(w.sy, w.t1).is_draft is True
    review.approve(w.admin, w.kclass, w.t1)
    assert build_term_report(w.sy, w.t1).is_draft is False


def test_report_joins_both_classes_after_transfer(w):
    grades.set_score(w.rabbi, w.prova, w.enrollment, "7")
    bet_rabbi = UserFactory(name="Rav Bet")
    bet = ClassFactory(academic_year=w.year, name="Shiur Bet", homeroom_rabbi=bet_rabbi)
    bet_gemara = ClassSubjectFactory(kodesh_class=bet, subject=w.gemara.subject)
    new = transfer(w.sy, bet, date(2100, 4, 1))
    bet_prova = AssessmentFactory(class_subject=bet_gemara, term=w.t1, name="Prova Bet")
    grades.set_score(bet_rabbi, bet_prova, new, "9")
    attendance.save_attendance(w.rabbi, w.enrollment, w.t1, 20, 1, 0)
    attendance.save_attendance(bet_rabbi, new, w.t1, 28, 1, 1)

    report = build_term_report(w.sy, w.t1)
    assert report.class_names == ["Shiur Alef", "Shiur Bet"]
    assert report.changed_class is True
    assert report.homeroom_rabbi_name == "Rav Bet"
    assert [s.teacher_name for s in report.subjects] == ["Rav Levi", "Rav Bet"]
    assert (report.attendance.classes_held, report.attendance.absences) == (48, 2)


def test_annual_report_has_every_term(w):
    assert len(build_annual_report(w.sy)) == 2


def test_report_does_not_create_review_rows(w):
    from app.models import ClassTermStatus

    build_term_report(w.sy, w.t1)
    assert w.s.scalar(select(func.count()).select_from(ClassTermStatus)) == 0
    assert db.session is w.s
