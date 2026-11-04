"""Revisão por shiur e trimestre: open -> ready_for_review -> approved. E travar o trimestre.

- Marcar como pronto: o rabino da turma (ou a direção).
- Devolver para o rabino e liberar: só a direção.
- Liberado (approved) trava o shiur no trimestre. Só a direção reabre.
"""

from datetime import datetime

from app.extensions import db
from app.models import ClassTermStatus, KodeshClass, ReviewStatus, Term, User, UserRole
from app.services.classes import class_term_status, review_status
from app.services.errors import ConflictError, LockedError, PermissionDenied
from app.services.years import ensure_year_editable


def _require_admin(user: User) -> None:
    if user.role != UserRole.ADMIN:
        raise PermissionDenied("Só a direção pode fazer isto.")


def submit_for_review(user: User, kodesh_class: KodeshClass, term: Term) -> ClassTermStatus:
    if user.role != UserRole.ADMIN and kodesh_class.homeroom_rabbi_id != user.id:
        raise PermissionDenied("Só o rabino da turma marca o shiur como pronto.")
    ensure_year_editable(kodesh_class.academic_year)
    if term.is_locked:
        raise LockedError(f"O {term.name} está travado.")
    status = class_term_status(kodesh_class, term)
    if status.status != ReviewStatus.OPEN:
        raise ConflictError("O shiur já foi marcado como pronto.")
    status.status = ReviewStatus.READY_FOR_REVIEW
    status.submitted_by = user.id
    status.submitted_at = datetime.now()
    db.session.flush()
    return status


def return_to_rabbi(user: User, kodesh_class: KodeshClass, term: Term) -> ClassTermStatus:
    _require_admin(user)
    status = class_term_status(kodesh_class, term)
    if status.status != ReviewStatus.READY_FOR_REVIEW:
        raise ConflictError("Só dá para devolver um shiur que está em revisão.")
    status.status = ReviewStatus.OPEN
    db.session.flush()
    return status


def approve(user: User, kodesh_class: KodeshClass, term: Term) -> ClassTermStatus:
    """Libera os boletins do shiur no trimestre (e trava a edição)."""
    _require_admin(user)
    status = class_term_status(kodesh_class, term)
    if status.status != ReviewStatus.READY_FOR_REVIEW:
        raise ConflictError("O rabino da turma precisa marcar o shiur como pronto antes.")
    status.status = ReviewStatus.APPROVED
    status.approved_by = user.id
    status.approved_at = datetime.now()
    db.session.flush()
    return status


def reopen(user: User, kodesh_class: KodeshClass, term: Term) -> ClassTermStatus:
    _require_admin(user)
    ensure_year_editable(kodesh_class.academic_year)
    status = class_term_status(kodesh_class, term)
    if status.status != ReviewStatus.APPROVED:
        raise ConflictError("Só dá para reabrir um shiur liberado.")
    status.status = ReviewStatus.OPEN
    status.approved_by = None
    status.approved_at = None
    db.session.flush()
    return status


def lock_term(user: User, term: Term) -> None:
    _require_admin(user)
    term.is_locked = True
    db.session.flush()


def unlock_term(user: User, term: Term) -> None:
    _require_admin(user)
    ensure_year_editable(term.academic_year)
    term.is_locked = False
    db.session.flush()


def can_send_reports(kodesh_class: KodeshClass, term: Term) -> bool:
    """Só boletim de shiur liberado é enviado aos pais."""
    return review_status(kodesh_class, term) == ReviewStatus.APPROVED
