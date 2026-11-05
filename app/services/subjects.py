"""Catálogo global de matérias (Gemara, Chumash...). Não se apaga: desativa."""

from sqlalchemy import func, select

from app.extensions import db
from app.models import Subject
from app.services.errors import ConflictError, ValidationError


def list_subjects(active_only: bool = False) -> list[Subject]:
    stmt = select(Subject).order_by(Subject.sort_order, Subject.name)
    if active_only:
        stmt = stmt.where(Subject.is_active.is_(True))
    return list(db.session.scalars(stmt))


def create_subject(name: str) -> Subject:
    name = _check_name(name)
    last = db.session.scalar(select(func.max(Subject.sort_order)))
    subject = Subject(name=name, sort_order=(last or 0) + 1)
    db.session.add(subject)
    db.session.flush()
    return subject


def rename_subject(subject: Subject, name: str) -> None:
    subject.name = _check_name(name, exclude_id=subject.id)
    db.session.flush()


def set_subject_active(subject: Subject, active: bool) -> None:
    subject.is_active = active
    db.session.flush()


def _check_name(name: str, exclude_id: int | None = None) -> str:
    name = (name or "").strip()
    if not name:
        raise ValidationError("Escreva o nome da matéria.")
    stmt = select(Subject).where(func.lower(Subject.name) == name.lower())
    if exclude_id:
        stmt = stmt.where(Subject.id != exclude_id)
    if db.session.scalar(stmt):
        raise ConflictError(f"A matéria {name} já existe.")
    return name
