"""Conteúdo do boletim (o PDF vem na Fase 12).

- Cada matéria lista as provas com include_in_report, na ordem do rabino, com a nota como foi dada.
- Matéria sem nenhuma prova marcada não aparece.
- Mostra o rabino de cada matéria naquele trimestre.
- Junta as matrículas do aluno no trimestre e indica a troca de turma.
- Só comentários públicos. Scans e anotações internas nunca entram.
- Rascunho enquanto o shiur não foi liberado.
"""

from dataclasses import dataclass, field
from decimal import Decimal

from sqlalchemy import select

from app.extensions import db
from app.models import (
    Assessment,
    AssessmentScore,
    ClassSubject,
    Comment,
    CommentCategory,
    CommentVisibility,
    ReviewStatus,
    ScoreStatus,
    StudentYear,
    Term,
    TermAttendance,
)
from app.services.attendance import presence_percent
from app.services.classes import effective_teacher, enrollments_in_term, review_status

SCHOOL_GRADE_LABELS = {
    8: "8º ano",
    9: "9º ano",
    10: "1º colegial",
    11: "2º colegial",
    12: "3º colegial",
}


@dataclass
class ReportScore:
    assessment_name: str
    status: ScoreStatus | None  # None = sem nota lançada
    score: Decimal | None
    max_score: Decimal


@dataclass
class ReportSubject:
    name: str
    teacher_name: str | None
    scores: list[ReportScore]


@dataclass
class ReportAttendance:
    classes_held: int
    absences: int
    lates: int

    @property
    def presence(self) -> Decimal | None:
        return presence_percent(self.classes_held, self.absences)


@dataclass
class TermReport:
    student_name: str
    hebrew_name: str | None
    school_grade: str
    term_name: str
    year_name: str
    scale_max: Decimal
    class_names: list[str]  # mais de um = trocou de turma no trimestre
    homeroom_rabbi_name: str | None  # do shiur atual (última matrícula do trimestre)
    subjects: list[ReportSubject] = field(default_factory=list)
    attendance: ReportAttendance | None = None
    general_comment: str | None = None
    behavior_comment: str | None = None
    is_draft: bool = True

    @property
    def changed_class(self) -> bool:
        return len(self.class_names) > 1


def build_term_report(student_year: StudentYear, term: Term) -> TermReport:
    student = student_year.student
    year = student_year.academic_year
    enrollments = enrollments_in_term(student_year, term)
    last = enrollments[-1] if enrollments else None

    report = TermReport(
        student_name=student.full_name,
        hebrew_name=student.hebrew_name,
        school_grade=SCHOOL_GRADE_LABELS.get(student_year.school_grade, ""),
        term_name=term.name,
        year_name=year.name,
        scale_max=year.grade_scale_max,
        class_names=[e.kodesh_class.name for e in enrollments],
        homeroom_rabbi_name=(
            last.kodesh_class.homeroom_rabbi.name
            if last and last.kodesh_class.homeroom_rabbi
            else None
        ),
    )
    if not enrollments:
        return report

    # Notas: por matrícula, cada matéria ativa do shiur, provas marcadas para o boletim.
    for enrollment in enrollments:
        class_subjects = db.session.scalars(
            select(ClassSubject)
            .where(
                ClassSubject.kodesh_class_id == enrollment.kodesh_class_id,
                ClassSubject.is_active.is_(True),
            )
            .order_by(ClassSubject.sort_order, ClassSubject.id)
        )
        for cs in class_subjects:
            assessments = list(
                db.session.scalars(
                    select(Assessment)
                    .where(
                        Assessment.class_subject_id == cs.id,
                        Assessment.term_id == term.id,
                        Assessment.include_in_report.is_(True),
                    )
                    .order_by(Assessment.sort_order, Assessment.id)
                )
            )
            if not assessments:
                continue
            scores = {
                s.assessment_id: s
                for s in db.session.scalars(
                    select(AssessmentScore).where(
                        AssessmentScore.enrollment_id == enrollment.id,
                        AssessmentScore.assessment_id.in_([a.id for a in assessments]),
                    )
                )
            }
            teacher = effective_teacher(cs, term)
            report.subjects.append(
                ReportSubject(
                    name=cs.report_label or cs.subject.name,
                    teacher_name=teacher.name if teacher else None,
                    scores=[
                        ReportScore(
                            assessment_name=a.name,
                            status=scores[a.id].status if a.id in scores else None,
                            score=scores[a.id].score if a.id in scores else None,
                            max_score=a.max_score,
                        )
                        for a in assessments
                    ],
                )
            )

    # Frequência: soma das matrículas do trimestre.
    records = list(
        db.session.scalars(
            select(TermAttendance).where(
                TermAttendance.enrollment_id.in_([e.id for e in enrollments]),
                TermAttendance.term_id == term.id,
            )
        )
    )
    if records:
        report.attendance = ReportAttendance(
            classes_held=sum(r.classes_held for r in records),
            absences=sum(r.absences for r in records),
            lates=sum(r.lates for r in records),
        )

    # Comentários: só os públicos.
    comments = db.session.scalars(
        select(Comment).where(
            Comment.enrollment_id.in_([e.id for e in enrollments]),
            Comment.term_id == term.id,
            Comment.visibility == CommentVisibility.PUBLIC,
        )
    )
    for c in comments:
        if c.category == CommentCategory.GENERAL:
            report.general_comment = c.text
        elif c.category == CommentCategory.BEHAVIOR:
            report.behavior_comment = c.text

    # Rascunho enquanto o shiur atual não foi liberado.
    report.is_draft = review_status(last.kodesh_class, term) != ReviewStatus.APPROVED
    return report


def build_annual_report(student_year: StudentYear) -> list[TermReport]:
    """Boletim anual: os trimestres do ano, em ordem (pedido do usuário)."""
    return [build_term_report(student_year, t) for t in student_year.academic_year.terms]
