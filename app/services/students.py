"""Cadastro de alunos. O aluno é identificado pelo cadastro, nunca só pelo nome.

Nome igual a outro aluno sempre pede confirmação. Aluno nunca é apagado: desativa.
"""

from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, or_, select

from app.extensions import db
from app.models import AcademicYear, Enrollment, KodeshClass, Student, StudentYear
from app.services.classes import active_enrollment, enroll
from app.services.errors import ConflictError, ValidationError
from app.services.years import ensure_year_editable


@dataclass
class StudentData:
    first_name: str
    last_name: str
    hebrew_name: str | None = None
    external_id: str | None = None
    birth_date: date | None = None
    parent_name: str | None = None
    parent_phone: str | None = None
    parent_email: str | None = None
    parent_email_2: str | None = None
    notes: str | None = None


def _clean(data: StudentData) -> StudentData:
    def c(value):
        return value.strip() or None if isinstance(value, str) else value

    data.first_name = (data.first_name or "").strip()
    data.last_name = (data.last_name or "").strip()
    for name in (
        "hebrew_name",
        "external_id",
        "parent_name",
        "parent_phone",
        "parent_email",
        "parent_email_2",
        "notes",
    ):
        setattr(data, name, c(getattr(data, name)))
    if not data.first_name or not data.last_name:
        raise ValidationError("Preencha o nome e o sobrenome do aluno.")
    return data


def same_name(first_name: str, last_name: str, exclude_id: int | None = None) -> list[Student]:
    """Alunos já cadastrados com o mesmo nome (sem diferenciar acento e maiúscula)."""
    stmt = select(Student).where(
        func.lower(Student.first_name) == first_name.strip().lower(),
        func.lower(Student.last_name) == last_name.strip().lower(),
    )
    if exclude_id:
        stmt = stmt.where(Student.id != exclude_id)
    return list(db.session.scalars(stmt))


def create_student(
    data: StudentData,
    year: AcademicYear | None = None,
    school_grade: int | None = None,
    kodesh_class: KodeshClass | None = None,
    confirm_same_name: bool = False,
    on_date: date | None = None,
) -> Student:
    """Cadastra o aluno. Com ano e série, já entra no ano; com shiur, já entra no shiur.

    Nome igual a outro aluno: recusa até vir confirm_same_name=True.
    """
    data = _clean(data)
    if not confirm_same_name and same_name(data.first_name, data.last_name):
        raise ConflictError(
            f"Já existe um aluno chamado {data.first_name} {data.last_name}. "
            "Confira se não é a mesma pessoa e confirme para cadastrar outro."
        )
    _check_external_id(data.external_id)
    student = Student(**data.__dict__)
    db.session.add(student)
    db.session.flush()
    if year is not None and school_grade is not None:
        sy = add_to_year(student, year, school_grade)
        if kodesh_class is not None:
            enroll(sy, kodesh_class, on_date or max(date.today(), year.start_date))
    return student


def update_student(student: Student, data: StudentData) -> Student:
    data = _clean(data)
    _check_external_id(data.external_id, exclude_id=student.id)
    for key, value in data.__dict__.items():
        setattr(student, key, value)
    db.session.flush()
    return student


def set_active(student: Student, active: bool) -> None:
    student.is_active = active
    db.session.flush()


def add_to_year(
    student: Student, year: AcademicYear, school_grade: int, secular_class_label: str | None = None
) -> StudentYear:
    ensure_year_editable(year)
    if school_grade not in range(8, 13):
        raise ValidationError("Escolha a série (8º ano a 3º colegial).")
    existing = student_year(student, year)
    if existing:
        raise ConflictError("O aluno já está neste ano letivo.")
    sy = StudentYear(
        student_id=student.id,
        academic_year_id=year.id,
        school_grade=school_grade,
        secular_class_label=(secular_class_label or "").strip() or None,
    )
    db.session.add(sy)
    db.session.flush()
    return sy


def student_year(student: Student, year: AcademicYear) -> StudentYear | None:
    return db.session.scalar(
        select(StudentYear).where(
            StudentYear.student_id == student.id, StudentYear.academic_year_id == year.id
        )
    )


def search_students(query: str = "", active_only: bool = False, limit: int = 200) -> list[Student]:
    """Busca por nome, sobrenome, nome em hebraico, número ou matrícula da secretaria."""
    stmt = select(Student)
    q = (query or "").strip()
    if q:
        like = f"%{q}%"
        conditions = [
            Student.first_name.ilike(like),
            Student.last_name.ilike(like),
            (Student.first_name + " " + Student.last_name).ilike(like),
            Student.hebrew_name.ilike(like),
            Student.external_id.ilike(like),
        ]
        if q.isdigit():
            conditions.append(Student.id == int(q))
        stmt = stmt.where(or_(*conditions))
    if active_only:
        stmt = stmt.where(Student.is_active.is_(True))
    return list(
        db.session.scalars(stmt.order_by(Student.first_name, Student.last_name).limit(limit))
    )


def current_class(student: Student, year: AcademicYear) -> KodeshClass | None:
    sy = student_year(student, year)
    if sy is None:
        return None
    enrollment = active_enrollment(sy)
    return enrollment.kodesh_class if enrollment else None


def students_without_class(year: AcademicYear) -> list[StudentYear]:
    """Alunos do ano sem matrícula ativa."""
    active = select(Enrollment.student_year_id).where(Enrollment.end_date.is_(None))
    return list(
        db.session.scalars(
            select(StudentYear).where(
                StudentYear.academic_year_id == year.id, StudentYear.id.not_in(active)
            )
        )
    )


def _check_external_id(external_id: str | None, exclude_id: int | None = None) -> None:
    if not external_id:
        return
    stmt = select(Student).where(Student.external_id == external_id)
    if exclude_id:
        stmt = stmt.where(Student.id != exclude_id)
    other = db.session.scalar(stmt)
    if other:
        raise ConflictError(f"A matrícula {external_id} já é de {other.full_name} (nº {other.id}).")
