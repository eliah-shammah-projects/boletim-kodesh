"""Ano letivo: só um ativo por vez, cada ano começa vazio, ano arquivado é só leitura."""

from datetime import date
from decimal import Decimal

from sqlalchemy import exists, func, select

from app.extensions import db
from app.models import (
    AcademicYear,
    Assessment,
    AssessmentScore,
    ClassSubject,
    KodeshClass,
    Term,
    YearStatus,
)
from app.services.errors import ConflictError, LockedError, ValidationError

DEFAULT_TERMS = 3


def get_active_year() -> AcademicYear | None:
    return db.session.scalar(select(AcademicYear).where(AcademicYear.status == YearStatus.ACTIVE))


def create_year(
    name: str,
    start_date: date,
    end_date: date | None = None,
    grade_scale_max: Decimal = Decimal("10"),
    terms: int = DEFAULT_TERMS,
) -> AcademicYear:
    """Cria o ano já ativo, com os trimestres. Exige que o ano anterior tenha sido fechado."""
    current = get_active_year()
    if current is not None:
        raise ConflictError(
            f"O ano {current.name} ainda está aberto. Feche-o antes de abrir um novo."
        )
    if terms < 1:
        raise ValidationError("O ano precisa de pelo menos 1 trimestre.")
    _check_scale(grade_scale_max)
    year = AcademicYear(
        name=name,
        start_date=start_date,
        end_date=end_date,
        status=YearStatus.ACTIVE,
        grade_scale_max=grade_scale_max,
    )
    db.session.add(year)
    db.session.flush()
    for n in range(1, terms + 1):
        db.session.add(Term(academic_year_id=year.id, number=n, name=f"{n}º trimestre"))
    db.session.flush()
    return year


def archive_year(year: AcademicYear) -> None:
    """Fecha o ano: tudo dele fica só para leitura."""
    if year.status == YearStatus.ARCHIVED:
        raise ConflictError(f"O ano {year.name} já está fechado.")
    year.status = YearStatus.ARCHIVED
    db.session.flush()


def ensure_year_editable(year: AcademicYear) -> None:
    if year.status == YearStatus.ARCHIVED:
        raise LockedError(f"O ano {year.name} está fechado. O arquivo é só para leitura.")


def year_has_scores(year: AcademicYear) -> bool:
    query = (
        select(AssessmentScore.id)
        .join(Assessment, AssessmentScore.assessment_id == Assessment.id)
        .join(ClassSubject, Assessment.class_subject_id == ClassSubject.id)
        .join(KodeshClass, ClassSubject.kodesh_class_id == KodeshClass.id)
        .where(KodeshClass.academic_year_id == year.id)
    )
    return db.session.scalar(select(exists(query))) or False


def set_grade_scale(year: AcademicYear, grade_scale_max: Decimal) -> None:
    """A escala do ano não pode mudar depois que houver notas."""
    ensure_year_editable(year)
    _check_scale(grade_scale_max)
    if year_has_scores(year):
        raise ConflictError("A escala não pode mudar porque já há notas lançadas neste ano.")
    year.grade_scale_max = grade_scale_max
    db.session.flush()


def count_active_years() -> int:
    stmt = select(func.count()).where(AcademicYear.status == YearStatus.ACTIVE)
    return db.session.scalar(stmt)


def _check_scale(value: Decimal) -> None:
    value = Decimal(value)
    if value <= 0 or value != value.quantize(Decimal("0.1")):
        raise ValidationError(
            "A nota máxima do ano precisa ser maior que 0, com até 1 casa decimal."
        )
