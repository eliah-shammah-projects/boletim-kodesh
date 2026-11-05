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


# ---------- Montagem do ano: shiurim, matérias, rabinos ----------


def create_class(
    year,
    name: str,
    level: str | None,
    homeroom_rabbi: User | None,
    color: str = "azul",
) -> KodeshClass:
    from app.models import SHIUR_COLORS

    ensure_year_editable(year)
    name = (name or "").strip()
    if not name:
        raise ValidationError("Dê um nome para o shiur (ex: Shiur Alef).")
    if color not in SHIUR_COLORS:
        raise ValidationError("Escolha uma das cores da paleta.")
    exists_ = db.session.scalar(
        select(KodeshClass).where(KodeshClass.academic_year_id == year.id, KodeshClass.name == name)
    )
    if exists_:
        raise ConflictError(f"Já existe um {name} em {year.name}.")
    last = db.session.scalar(
        select(KodeshClass.sort_order)
        .where(KodeshClass.academic_year_id == year.id)
        .order_by(KodeshClass.sort_order.desc())
        .limit(1)
    )
    kclass = KodeshClass(
        academic_year_id=year.id,
        name=name,
        level=(level or "").strip() or None,
        homeroom_rabbi_id=homeroom_rabbi.id if homeroom_rabbi else None,
        color=color,
        sort_order=(last or 0) + 1,
    )
    db.session.add(kclass)
    db.session.flush()
    return kclass


def update_class(
    kclass: KodeshClass, name: str, level: str | None, homeroom_rabbi: User | None, color: str
) -> KodeshClass:
    from app.models import SHIUR_COLORS

    ensure_year_editable(kclass.academic_year)
    name = (name or "").strip()
    if not name:
        raise ValidationError("Dê um nome para o shiur.")
    if color not in SHIUR_COLORS:
        raise ValidationError("Escolha uma das cores da paleta.")
    other = db.session.scalar(
        select(KodeshClass).where(
            KodeshClass.academic_year_id == kclass.academic_year_id,
            KodeshClass.name == name,
            KodeshClass.id != kclass.id,
        )
    )
    if other:
        raise ConflictError(f"Já existe um {name} neste ano.")
    kclass.name = name
    kclass.level = (level or "").strip() or None
    kclass.homeroom_rabbi_id = homeroom_rabbi.id if homeroom_rabbi else None
    kclass.color = color
    db.session.flush()
    return kclass


def add_class_subject(
    kclass: KodeshClass, subject, default_teacher: User | None = None
) -> ClassSubject:
    ensure_year_editable(kclass.academic_year)
    existing = db.session.scalar(
        select(ClassSubject).where(
            ClassSubject.kodesh_class_id == kclass.id, ClassSubject.subject_id == subject.id
        )
    )
    if existing is not None:
        if existing.is_active:
            raise ConflictError(f"{subject.name} já está neste shiur.")
        existing.is_active = True  # matéria desativada volta
        db.session.flush()
        return existing
    last = db.session.scalar(
        select(ClassSubject.sort_order)
        .where(ClassSubject.kodesh_class_id == kclass.id)
        .order_by(ClassSubject.sort_order.desc())
        .limit(1)
    )
    cs = ClassSubject(
        kodesh_class_id=kclass.id,
        subject_id=subject.id,
        default_teacher_id=default_teacher.id if default_teacher else None,
        sort_order=(last or 0) + 1,
    )
    db.session.add(cs)
    db.session.flush()
    return cs


def update_class_subject(
    cs: ClassSubject, default_teacher: User | None, report_label: str | None
) -> ClassSubject:
    ensure_year_editable(cs.kodesh_class.academic_year)
    cs.default_teacher_id = default_teacher.id if default_teacher else None
    cs.report_label = (report_label or "").strip() or None
    db.session.flush()
    return cs


def set_term_teacher(cs: ClassSubject, term: Term, teacher: User | None) -> None:
    """Rabino da matéria só naquele trimestre. Vazio = volta para o rabino padrão."""
    ensure_year_editable(cs.kodesh_class.academic_year)
    current = db.session.scalar(
        select(ClassSubjectTerm).where(
            ClassSubjectTerm.class_subject_id == cs.id, ClassSubjectTerm.term_id == term.id
        )
    )
    if teacher is None:
        if current is not None:
            db.session.delete(current)
    elif current is None:
        db.session.add(
            ClassSubjectTerm(class_subject_id=cs.id, term_id=term.id, teacher_id=teacher.id)
        )
    else:
        current.teacher_id = teacher.id
    db.session.flush()


def set_class_subject_active(cs: ClassSubject, active: bool) -> None:
    """Matéria não é apagada do shiur: desativa (as provas e notas ficam guardadas)."""
    ensure_year_editable(cs.kodesh_class.academic_year)
    cs.is_active = active
    db.session.flush()


def move_class_subject(cs: ClassSubject, direction: int) -> None:
    """Sobe (-1) ou desce (+1) a matéria na ordem do boletim."""
    siblings = list(
        db.session.scalars(
            select(ClassSubject)
            .where(ClassSubject.kodesh_class_id == cs.kodesh_class_id)
            .order_by(ClassSubject.sort_order, ClassSubject.id)
        )
    )
    i = siblings.index(cs)
    j = i + direction
    if 0 <= j < len(siblings):
        siblings[i], siblings[j] = siblings[j], siblings[i]
        for n, item in enumerate(siblings, start=1):
            item.sort_order = n
        db.session.flush()


def enrollment_has_records(enrollment: Enrollment) -> bool:
    """A matrícula já tem notas, scans, frequência ou comentários?"""
    from sqlalchemy import exists

    from app.models import AssessmentFile, AssessmentScore, Comment, TermAttendance

    for model in (AssessmentScore, AssessmentFile, TermAttendance, Comment):
        if db.session.scalar(select(exists().where(model.enrollment_id == enrollment.id))):
            return True
    return False


def move_to_class(student_year: StudentYear, new_class: KodeshClass, on_date: date) -> Enrollment:
    """Coloca o aluno em outro shiur.

    Sem nada lançado na matrícula atual (ex: colocado no shiur errado no começo do ano),
    só corrige o shiur. Com notas ou frequência, faz a troca de turma: a matrícula antiga
    fica guardada com tudo o que foi lançado nela.
    """
    ensure_year_editable(student_year.academic_year)
    if new_class.academic_year_id != student_year.academic_year_id:
        raise ValidationError("O shiur é de outro ano letivo.")
    current = active_enrollment(student_year)
    if current is None:
        return enroll(student_year, new_class, on_date)
    if current.kodesh_class_id == new_class.id:
        raise ConflictError("O aluno já está neste shiur.")
    if not enrollment_has_records(current):
        current.kodesh_class_id = new_class.id
        db.session.flush()
        db.session.refresh(current)
        return current
    return transfer(student_year, new_class, on_date)
