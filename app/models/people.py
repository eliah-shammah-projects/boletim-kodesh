"""Usuários (direção e rabinos), alunos e o ano letivo."""

from datetime import date, datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    MYSQL_TABLE_OPTIONS,
    Base,
    Score,
    UserRole,
    YearStatus,
    created_at_column,
    enum_column,
)


class User(Base):
    """Admin ou rabino. Rabino vindo da importação fica inativo e sem senha até o admin ativar."""

    __tablename__ = "users"
    __table_args__ = (MYSQL_TABLE_OPTIONS,)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(120))
    email: Mapped[str | None] = mapped_column(sa.String(255), unique=True)
    password_hash: Mapped[str | None] = mapped_column(sa.String(255))
    role: Mapped[UserRole] = mapped_column(enum_column(UserRole, "user_role"))
    is_active: Mapped[bool] = mapped_column(default=True, server_default=sa.true())
    created_at: Mapped[datetime] = created_at_column()

    def __repr__(self) -> str:  # sem dados pessoais em logs
        return f"<User {self.id}>"


class Student(Base):
    """Cadastro único do aluno, que continua entre os anos. Nunca é apagado: usar is_active."""

    __tablename__ = "students"
    __table_args__ = (MYSQL_TABLE_OPTIONS,)

    id: Mapped[int] = mapped_column(primary_key=True)  # código interno, mostrado na tela
    external_id: Mapped[str | None] = mapped_column(sa.String(50), unique=True)  # matrícula
    first_name: Mapped[str] = mapped_column(sa.String(80))
    last_name: Mapped[str] = mapped_column(sa.String(80))
    hebrew_name: Mapped[str | None] = mapped_column(sa.String(120))
    birth_date: Mapped[date | None]
    parent_name: Mapped[str | None] = mapped_column(sa.String(160))
    parent_phone: Mapped[str | None] = mapped_column(sa.String(40))
    parent_email: Mapped[str | None] = mapped_column(sa.String(255))
    parent_email_2: Mapped[str | None] = mapped_column(sa.String(255))
    is_active: Mapped[bool] = mapped_column(default=True, server_default=sa.true())
    notes: Mapped[str | None] = mapped_column(sa.Text)
    created_at: Mapped[datetime] = created_at_column()

    years: Mapped[list["StudentYear"]] = relationship(back_populates="student")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<Student {self.id}>"


class AcademicYear(Base):
    """Ano letivo. Só um 'active' por vez (regra em app/services). 'archived' é só leitura."""

    __tablename__ = "academic_years"
    __table_args__ = (
        sa.CheckConstraint("grade_scale_max > 0", name="scale_positive"),
        sa.CheckConstraint("end_date IS NULL OR end_date >= start_date", name="dates_order"),
        MYSQL_TABLE_OPTIONS,
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(20), unique=True)  # civil, ex: "2027"
    start_date: Mapped[date]
    end_date: Mapped[date | None]
    status: Mapped[YearStatus] = mapped_column(
        enum_column(YearStatus, "year_status"), default=YearStatus.ACTIVE
    )
    grade_scale_max: Mapped[Decimal] = mapped_column(
        Score, default=Decimal("10.0"), server_default="10.0"
    )

    terms: Mapped[list["Term"]] = relationship(
        back_populates="academic_year", order_by="Term.number"
    )

    def __repr__(self) -> str:
        return f"<AcademicYear {self.name}>"


class Term(Base):
    """Trimestre. Travado bloqueia provas, notas, scans, frequência e comentários."""

    __tablename__ = "terms"
    __table_args__ = (
        sa.UniqueConstraint("academic_year_id", "number"),
        sa.CheckConstraint("number >= 1", name="number_positive"),
        sa.CheckConstraint("end_date IS NULL OR end_date >= start_date", name="dates_order"),
        MYSQL_TABLE_OPTIONS,
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    academic_year_id: Mapped[int] = mapped_column(sa.ForeignKey("academic_years.id"))
    number: Mapped[int] = mapped_column(sa.SmallInteger)
    name: Mapped[str] = mapped_column(sa.String(40))  # "1º trimestre"
    start_date: Mapped[date | None]
    end_date: Mapped[date | None]
    is_locked: Mapped[bool] = mapped_column(default=False, server_default=sa.false())

    academic_year: Mapped[AcademicYear] = relationship(back_populates="terms")

    def __repr__(self) -> str:
        return f"<Term {self.academic_year_id}/{self.number}>"


class StudentYear(Base):
    """O aluno naquele ano: série escolar e turma laica (só anotação)."""

    __tablename__ = "student_years"
    __table_args__ = (
        sa.UniqueConstraint("student_id", "academic_year_id"),
        sa.CheckConstraint("school_grade BETWEEN 8 AND 12", name="school_grade_range"),
        MYSQL_TABLE_OPTIONS,
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(sa.ForeignKey("students.id"))
    academic_year_id: Mapped[int] = mapped_column(sa.ForeignKey("academic_years.id"))
    # 8..12, exibido como 8º ano, 9º ano, 1º colegial, 2º colegial, 3º colegial
    school_grade: Mapped[int] = mapped_column(sa.SmallInteger)
    secular_class_label: Mapped[str | None] = mapped_column(sa.String(20))  # ex: "9º B"
    notes: Mapped[str | None] = mapped_column(sa.Text)

    student: Mapped[Student] = relationship(back_populates="years")
    academic_year: Mapped[AcademicYear] = relationship()

    def __repr__(self) -> str:
        return f"<StudentYear {self.id}>"
