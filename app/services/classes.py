"""Rabino efetivo da matéria, matrículas, troca de turma e travamento do trimestre."""

from datetime import date, timedelta

from sqlalchemy import or_, select

from app.extensions import db
from app.models import (
    ClassSubject,
    ClassSubjectTerm,
    ClassTermStatus,
    Enrollment,
    KodeshClass,
    ReviewStatus,
    StudentYear,
    Term,
    User,
    UserRole,
)
from app.services.errors import ConflictError, LockedError, ValidationError
from app.services.years import ensure_year_editable

# ---------- Rabino efetivo ----------


def effective_teacher(class_subject: ClassSubject, term: Term) -> User | None:
    """class_subject_terms -> class_subjects.default_teacher -> rabino da turma."""
    override = db.session.scalar(
        select(ClassSubjectTerm).where(
            ClassSubjectTerm.class_subject_id == class_subject.id,
            ClassSubjectTerm.term_id == term.id,
        )
    )
    if override is not None:
        return override.teacher
    if class_subject.default_teacher is not None:
        return class_subject.default_teacher
    return class_subject.kodesh_class.homeroom_rabbi


# ---------- Matrículas ----------


def active_enrollment(student_year: StudentYear) -> Enrollment | None:
    return db.session.scalar(
        select(Enrollment).where(
            Enrollment.student_year_id == student_year.id, Enrollment.end_date.is_(None)
        )
    )


def enroll(student_year: StudentYear, kodesh_class: KodeshClass, start_date: date) -> Enrollment:
    """Coloca o aluno no shiur. Um aluno só tem uma matrícula ativa por vez."""
    ensure_year_editable(student_year.academic_year)
    if kodesh_class.academic_year_id != student_year.academic_year_id:
        raise ValidationError("O shiur é de outro ano letivo.")
    if active_enrollment(student_year) is not None:
        raise ConflictError("O aluno já está num shiur. Use a troca de turma.")
    enrollment = Enrollment(
        student_year_id=student_year.id, kodesh_class_id=kodesh_class.id, start_date=start_date
    )
    db.session.add(enrollment)
    db.session.flush()
    return enrollment


def transfer(student_year: StudentYear, new_class: KodeshClass, on_date: date) -> Enrollment:
    """Troca de turma no meio do ano: fecha a matrícula atual e abre outra.

    A matrícula antiga termina no dia anterior. Notas, scans e frequência ficam nela.
    """
    # Valida tudo antes de mexer: nunca deixar o aluno sem shiur por um erro no meio.
    ensure_year_editable(student_year.academic_year)
    if new_class.academic_year_id != student_year.academic_year_id:
        raise ValidationError("O shiur é de outro ano letivo.")
    current = active_enrollment(student_year)
    if current is None:
        raise ConflictError("O aluno não está em nenhum shiur. Use Inserir no shiur.")
    if current.kodesh_class_id == new_class.id:
        raise ConflictError("O aluno já está neste shiur.")
    if on_date <= current.start_date:
        raise ValidationError("A data da troca precisa ser depois da entrada no shiur atual.")
    current.end_date = on_date - timedelta(days=1)
    db.session.flush()
    return enroll(student_year, new_class, on_date)


def remove_from_class(student_year: StudentYear, on_date: date) -> Enrollment:
    """Tira o aluno do shiur sem apagar nada: só fecha a matrícula."""
    current = active_enrollment(student_year)
    if current is None:
        raise ConflictError("O aluno não está em nenhum shiur.")
    ensure_year_editable(student_year.academic_year)
    current.end_date = max(on_date, current.start_date)
    db.session.flush()
    return current


def enrollments_in_term(student_year: StudentYear, term: Term) -> list[Enrollment]:
    """Matrículas do aluno que tocam o trimestre (sem datas no trimestre, todas do ano)."""
    stmt = select(Enrollment).where(Enrollment.student_year_id == student_year.id)
    if term.start_date is not None:
        stmt = stmt.where(
            or_(Enrollment.end_date.is_(None), Enrollment.end_date >= term.start_date)
        )
    if term.end_date is not None:
        stmt = stmt.where(Enrollment.start_date <= term.end_date)
    return list(db.session.scalars(stmt.order_by(Enrollment.start_date)))


# ---------- Travamento e revisão ----------


def review_status(kodesh_class: KodeshClass, term: Term) -> ReviewStatus:
    """Status de revisão sem criar nada (sem registro = 'open')."""
    status = db.session.scalar(
        select(ClassTermStatus.status).where(
            ClassTermStatus.kodesh_class_id == kodesh_class.id, ClassTermStatus.term_id == term.id
        )
    )
    return status or ReviewStatus.OPEN


def class_term_status(kodesh_class: KodeshClass, term: Term) -> ClassTermStatus:
    """Status de revisão do shiur no trimestre (criado como 'open' na primeira vez)."""
    status = db.session.scalar(
        select(ClassTermStatus).where(
            ClassTermStatus.kodesh_class_id == kodesh_class.id, ClassTermStatus.term_id == term.id
        )
    )
    if status is None:
        status = ClassTermStatus(
            kodesh_class_id=kodesh_class.id, term_id=term.id, status=ReviewStatus.OPEN
        )
        db.session.add(status)
        db.session.flush()
    return status


def ensure_editable(user: User, kodesh_class: KodeshClass, term: Term) -> None:
    """Pode editar provas, notas, scans, frequência e comentários deste shiur no trimestre?

    - ano arquivado: ninguém
    - trimestre travado ou shiur liberado (approved): ninguém (só o admin destrava/reabre)
    - pronto para revisão: só a direção
    """
    ensure_year_editable(kodesh_class.academic_year)
    if term.academic_year_id != kodesh_class.academic_year_id:
        raise ValidationError("O trimestre é de outro ano letivo.")
    if term.is_locked:
        raise LockedError(f"O {term.name} está travado. Peça à direção para destravar.")
    status = review_status(kodesh_class, term)
    if status == ReviewStatus.APPROVED:
        raise LockedError("Os boletins deste shiur já foram liberados. Só a direção pode reabrir.")
    if status == ReviewStatus.READY_FOR_REVIEW and user.role != UserRole.ADMIN:
        raise LockedError(
            "O shiur está em revisão pela direção. Peça para devolver se precisar mudar."
        )
