"""Frequência por aluno e trimestre, uma só para o shiur. Atraso conta como presença."""

from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select

from app.extensions import db
from app.models import AttendanceSource, Enrollment, Term, TermAttendance, User
from app.services import audit
from app.services.classes import ensure_editable
from app.services.errors import ValidationError


def presence_percent(classes_held: int, absences: int) -> Decimal | None:
    """(aulas dadas - faltas) / aulas dadas * 100, com 1 casa. Sem aulas dadas: None."""
    if not classes_held:
        return None
    value = Decimal(classes_held - absences) * 100 / Decimal(classes_held)
    return value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def validate_attendance(classes_held: int, absences: int, lates: int) -> None:
    for label, value in (("Aulas dadas", classes_held), ("Faltas", absences), ("Atrasos", lates)):
        if value is None or value < 0:
            raise ValidationError(f"{label} precisa ser um número igual ou maior que 0.")
    if absences > classes_held:
        raise ValidationError("As faltas não podem passar das aulas dadas.")
    if lates > classes_held:
        raise ValidationError("Os atrasos não podem passar das aulas dadas.")


def save_attendance(
    user: User,
    enrollment: Enrollment,
    term: Term,
    classes_held: int,
    absences: int,
    lates: int,
    source: AttendanceSource = AttendanceSource.MANUAL,
) -> TermAttendance:
    ensure_editable(user, enrollment.kodesh_class, term)
    validate_attendance(classes_held, absences, lates)
    record = db.session.scalar(
        select(TermAttendance).where(
            TermAttendance.enrollment_id == enrollment.id, TermAttendance.term_id == term.id
        )
    )
    before = audit.snapshot(record) if record else None
    if record is None:
        record = TermAttendance(enrollment_id=enrollment.id, term_id=term.id)
        db.session.add(record)
    record.classes_held = classes_held
    record.absences = absences
    record.lates = lates
    record.source = source
    record.updated_by = user.id
    db.session.flush()
    audit.record(user, "update" if before else "create", record, before, audit.snapshot(record))
    return record
