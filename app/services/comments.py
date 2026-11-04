"""Comentários do boletim e anotações internas.

Públicos (geral e comportamento): só o rabino da turma escreve. A direção não escreve nem
corrige (decisão do usuário): para mudar, devolve o shiur para o rabino. No máximo um de
cada por aluno por trimestre, mesmo que o aluno tenha trocado de turma no trimestre.
Internos: qualquer rabino, ilimitados, nunca saem do sistema.
"""

from sqlalchemy import select

from app.extensions import db
from app.models import (
    Comment,
    CommentCategory,
    CommentVisibility,
    Enrollment,
    Term,
    User,
)
from app.services import audit
from app.services.classes import ensure_editable
from app.services.errors import PermissionDenied, ValidationError

MAX_PUBLIC_LENGTH = 600


def can_write_public(user: User, enrollment: Enrollment) -> bool:
    return enrollment.kodesh_class.homeroom_rabbi_id == user.id


def save_public_comment(
    user: User, enrollment: Enrollment, term: Term, category: CommentCategory, text: str
) -> Comment:
    """Cria ou substitui o comentário geral ou de comportamento do aluno no trimestre."""
    if not can_write_public(user, enrollment):
        raise PermissionDenied("Só o rabino da turma escreve os comentários do boletim.")
    ensure_editable(user, enrollment.kodesh_class, term)
    text = (text or "").strip()
    if not text:
        raise ValidationError("Escreva o comentário antes de salvar.")
    if len(text) > MAX_PUBLIC_LENGTH:
        raise ValidationError(f"O comentário pode ter até {MAX_PUBLIC_LENGTH} caracteres.")

    # O limite é por aluno no trimestre: procura em todas as matrículas do aluno no ano.
    existing = db.session.scalar(
        select(Comment)
        .join(Enrollment, Comment.enrollment_id == Enrollment.id)
        .where(
            Enrollment.student_year_id == enrollment.student_year_id,
            Comment.term_id == term.id,
            Comment.category == category,
            Comment.visibility == CommentVisibility.PUBLIC,
        )
    )
    before = audit.snapshot(existing) if existing else None
    if existing is None:
        existing = Comment(
            enrollment_id=enrollment.id,
            term_id=term.id,
            category=category,
            visibility=CommentVisibility.PUBLIC,
        )
        db.session.add(existing)
    existing.text = text
    existing.author_id = user.id
    db.session.flush()
    audit.record(user, "update" if before else "create", existing, before, audit.snapshot(existing))
    return existing


def add_internal_note(user: User, enrollment: Enrollment, term: Term, text: str) -> Comment:
    """Anotação interna de qualquer rabino. Nunca vai para o boletim."""
    ensure_editable(user, enrollment.kodesh_class, term)
    text = (text or "").strip()
    if not text:
        raise ValidationError("Escreva a anotação antes de salvar.")
    note = Comment(
        enrollment_id=enrollment.id,
        term_id=term.id,
        category=CommentCategory.GENERAL,
        visibility=CommentVisibility.INTERNAL,
        text=text,
        author_id=user.id,
    )
    db.session.add(note)
    db.session.flush()
    audit.record(user, "create", note, None, audit.snapshot(note))
    return note
