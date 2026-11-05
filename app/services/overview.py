"""Resumo do que falta em cada shiur (primeira coisa que aparece na lista de shiurim)."""

from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, select

from app.extensions import db
from app.models import (
    AcademicYear,
    Assessment,
    AssessmentScore,
    ClassSubject,
    Comment,
    CommentVisibility,
    Enrollment,
    KodeshClass,
    ReviewStatus,
    Term,
    TermAttendance,
)
from app.services.classes import review_status


def current_term(year: AcademicYear, today: date | None = None) -> Term | None:
    """Trimestre de hoje; antes do ano, o primeiro; depois, o último."""
    terms = list(year.terms)
    if not terms:
        return None
    today = today or date.today()
    for term in terms:
        if term.start_date and term.end_date and term.start_date <= today <= term.end_date:
            return term
    dated = [t for t in terms if t.start_date]
    if dated and today < dated[0].start_date:
        return terms[0]
    return terms[-1] if dated else terms[0]


@dataclass
class ClassSummary:
    kodesh_class: KodeshClass
    students: int
    subjects: int
    missing_scores: int
    missing_attendance: int
    missing_comments: int
    status: ReviewStatus

    @property
    def todo(self) -> str:
        """O que falta, em uma frase."""
        if self.status == ReviewStatus.APPROVED:
            return "Boletins liberados"
        if self.status == ReviewStatus.READY_FOR_REVIEW:
            return "Aguardando a revisão da direção"
        if self.students == 0:
            return "Nenhum aluno no shiur ainda"
        if self.subjects == 0:
            return "Nenhuma matéria no shiur ainda"
        parts = []
        if self.missing_scores:
            parts.append(f"{self.missing_scores} {'nota' if self.missing_scores == 1 else 'notas'}")
        if self.missing_attendance:
            parts.append("a frequência")
        if self.missing_comments:
            n = self.missing_comments
            parts.append(f"{n} {'comentário' if n == 1 else 'comentários'}")
        if not parts:
            return "Tudo lançado. Pode marcar como pronto"
        return "Faltam " + _join(parts)

    @property
    def has_todo(self) -> bool:
        return self.status == ReviewStatus.OPEN and not self.todo.startswith("Tudo")


def class_summary(kclass: KodeshClass, term: Term | None) -> ClassSummary:
    enrollments = list(
        db.session.scalars(
            select(Enrollment).where(
                Enrollment.kodesh_class_id == kclass.id, Enrollment.end_date.is_(None)
            )
        )
    )
    enrollment_ids = [e.id for e in enrollments]
    subjects = db.session.scalar(
        select(func.count()).where(
            ClassSubject.kodesh_class_id == kclass.id, ClassSubject.is_active.is_(True)
        )
    )
    missing_scores = missing_attendance = missing_comments = 0
    status = review_status(kclass, term) if term else ReviewStatus.OPEN
    if term is not None and enrollment_ids:
        assessments = db.session.scalar(
            select(func.count())
            .select_from(Assessment)
            .join(ClassSubject, Assessment.class_subject_id == ClassSubject.id)
            .where(ClassSubject.kodesh_class_id == kclass.id, Assessment.term_id == term.id)
        )
        scores = db.session.scalar(
            select(func.count())
            .select_from(AssessmentScore)
            .join(Assessment, AssessmentScore.assessment_id == Assessment.id)
            .where(Assessment.term_id == term.id, AssessmentScore.enrollment_id.in_(enrollment_ids))
        )
        missing_scores = max(0, assessments * len(enrollment_ids) - scores)
        with_attendance = db.session.scalar(
            select(func.count()).where(
                TermAttendance.term_id == term.id, TermAttendance.enrollment_id.in_(enrollment_ids)
            )
        )
        missing_attendance = len(enrollment_ids) - with_attendance
        commented = db.session.scalar(
            select(func.count(func.distinct(Comment.enrollment_id))).where(
                Comment.term_id == term.id,
                Comment.visibility == CommentVisibility.PUBLIC,
                Comment.enrollment_id.in_(enrollment_ids),
            )
        )
        missing_comments = len(enrollment_ids) - commented
    return ClassSummary(
        kodesh_class=kclass,
        students=len(enrollment_ids),
        subjects=subjects,
        missing_scores=missing_scores,
        missing_attendance=missing_attendance,
        missing_comments=missing_comments,
        status=status,
    )


def year_overview(year: AcademicYear, term: Term | None) -> list[ClassSummary]:
    classes = db.session.scalars(
        select(KodeshClass)
        .where(KodeshClass.academic_year_id == year.id)
        .order_by(KodeshClass.sort_order, KodeshClass.name)
    )
    return [class_summary(c, term) for c in classes]


def _join(parts: list[str]) -> str:
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " e " + parts[-1]
