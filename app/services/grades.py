"""Provas e notas. A nota pertence a uma prova: Decimal, até 1 casa, entre 0 e o max_score."""

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from sqlalchemy import exists, select

from app.extensions import db
from app.models import (
    Assessment,
    AssessmentFile,
    AssessmentScore,
    ClassSubject,
    Enrollment,
    ScoreStatus,
    Term,
    User,
)
from app.services import audit
from app.services.classes import ensure_editable
from app.services.errors import ConflictError, ValidationError

_NUMBER = re.compile(r"^\d{1,3}([.,]\d)?$")


@dataclass(frozen=True)
class ParsedScore:
    status: ScoreStatus | None  # None = campo vazio (apagar a nota)
    score: Decimal | None


def parse_score_input(raw: str, max_score: Decimal) -> ParsedScore:
    """Texto digitado na grade -> nota. Aceita vírgula ou ponto, A (ausente) e D (dispensado)."""
    text = (raw or "").strip()
    if text == "":
        return ParsedScore(None, None)
    lower = text.lower()
    if lower in ("a", "ausente"):
        return ParsedScore(ScoreStatus.ABSENT, None)
    if lower in ("d", "dispensado"):
        return ParsedScore(ScoreStatus.EXEMPT, None)
    if not _NUMBER.match(text):
        raise ValidationError(
            "Use um número com até 1 casa (ex: 8,5), A para ausente ou D para dispensado."
        )
    return ParsedScore(
        ScoreStatus.GRADED, validate_score(Decimal(text.replace(",", ".")), max_score)
    )


def validate_score(value: Decimal, max_score: Decimal) -> Decimal:
    try:
        value = Decimal(value)
    except (InvalidOperation, TypeError) as exc:
        raise ValidationError("A nota precisa ser um número.") from exc
    if value != value.quantize(Decimal("0.1")):
        raise ValidationError("A nota pode ter no máximo 1 casa decimal.")
    if value < 0 or value > Decimal(max_score):
        raise ValidationError(f"A nota precisa estar entre 0 e {_fmt(max_score)}.")
    return value.quantize(Decimal("0.1"))


def create_assessment(
    user: User,
    class_subject: ClassSubject,
    term: Term,
    name: str,
    max_score: Decimal | None = None,
    include_in_report: bool = True,
    when=None,
) -> Assessment:
    """Cria a prova. Sem nota máxima própria, usa a escala do ano."""
    kodesh_class = class_subject.kodesh_class
    ensure_editable(user, kodesh_class, term)
    name = (name or "").strip()
    if not name:
        raise ValidationError("Dê um nome para a prova (ex: Prova 1).")
    scale = kodesh_class.academic_year.grade_scale_max
    max_score = Decimal(max_score) if max_score is not None else scale
    if max_score <= 0 or max_score != max_score.quantize(Decimal("0.1")):
        raise ValidationError("A nota máxima precisa ser maior que 0, com até 1 casa decimal.")
    last = db.session.scalar(
        select(Assessment.sort_order)
        .where(Assessment.class_subject_id == class_subject.id, Assessment.term_id == term.id)
        .order_by(Assessment.sort_order.desc())
        .limit(1)
    )
    assessment = Assessment(
        class_subject_id=class_subject.id,
        term_id=term.id,
        name=name,
        date=when,
        max_score=max_score,
        include_in_report=include_in_report,
        sort_order=(last or 0) + 1,
        created_by=user.id,
    )
    db.session.add(assessment)
    db.session.flush()
    audit.record(user, "create", assessment, None, audit.snapshot(assessment))
    return assessment


def delete_assessment(user: User, assessment: Assessment) -> None:
    """Só apaga prova sem notas e sem scans."""
    ensure_editable(user, assessment.class_subject.kodesh_class, assessment.term)
    has_scores = db.session.scalar(
        select(exists().where(AssessmentScore.assessment_id == assessment.id))
    )
    has_files = db.session.scalar(
        select(exists().where(AssessmentFile.assessment_id == assessment.id))
    )
    if has_scores or has_files:
        raise ConflictError("Esta prova já tem notas ou scans. Apague as notas e os scans antes.")
    audit.record(user, "delete", assessment, audit.snapshot(assessment), None)
    db.session.delete(assessment)
    db.session.flush()


def set_score(
    user: User, assessment: Assessment, enrollment: Enrollment, raw: str
) -> AssessmentScore | None:
    """Lança, corrige ou apaga (campo vazio) a nota do aluno na prova. Grava no audit_log."""
    kodesh_class = assessment.class_subject.kodesh_class
    if enrollment.kodesh_class_id != kodesh_class.id:
        raise ValidationError("O aluno não está neste shiur.")
    ensure_editable(user, kodesh_class, assessment.term)
    parsed = parse_score_input(raw, assessment.max_score)
    existing = db.session.scalar(
        select(AssessmentScore).where(
            AssessmentScore.assessment_id == assessment.id,
            AssessmentScore.enrollment_id == enrollment.id,
        )
    )
    before = audit.snapshot(existing) if existing else None

    if parsed.status is None:
        if existing is not None:
            audit.record(user, "delete", existing, before, None)
            db.session.delete(existing)
            db.session.flush()
        return None

    if existing is None:
        existing = AssessmentScore(assessment_id=assessment.id, enrollment_id=enrollment.id)
        db.session.add(existing)
    existing.status = parsed.status
    existing.score = parsed.score
    existing.updated_by = user.id
    db.session.flush()
    audit.record(user, "update" if before else "create", existing, before, audit.snapshot(existing))
    return existing


def _fmt(value: Decimal) -> str:
    text = format(Decimal(value).normalize(), "f")
    return text.replace(".", ",")
