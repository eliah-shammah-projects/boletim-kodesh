"""Shiurim (turmas de kodesh), matérias, rabinos por trimestre, matrículas e revisão."""

from datetime import date, datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    MYSQL_TABLE_OPTIONS,
    SHIUR_COLORS,
    Base,
    ReviewStatus,
    enum_column,
    user_fk,
)
from app.models.people import AcademicYear, StudentYear, Term, User

_COLOR_LIST = ", ".join(f"'{c}'" for c in SHIUR_COLORS)


class KodeshClass(Base):
    """Shiur do ano. O rabino da turma dá Gemara e é o responsável (comentários e revisão)."""

    __tablename__ = "kodesh_classes"
    __table_args__ = (
        sa.UniqueConstraint("academic_year_id", "name"),
        sa.CheckConstraint(f"color IN ({_COLOR_LIST})", name="color_in_palette"),
        MYSQL_TABLE_OPTIONS,
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    academic_year_id: Mapped[int] = mapped_column(sa.ForeignKey("academic_years.id"))
    name: Mapped[str] = mapped_column(sa.String(60))
    level: Mapped[str | None] = mapped_column(sa.String(40))
    # Pode ficar vazio só enquanto um shiur novo da importação ainda não tem rabino ativado.
    homeroom_rabbi_id: Mapped[int | None] = user_fk()
    # Cor de fita, escolhida pelo rabino numa paleta fixa (decisão do usuário).
    color: Mapped[str] = mapped_column(sa.String(20), default="azul", server_default="azul")
    sort_order: Mapped[int] = mapped_column(default=0, server_default="0")

    academic_year: Mapped[AcademicYear] = relationship()
    homeroom_rabbi: Mapped[User | None] = relationship()
    subjects: Mapped[list["ClassSubject"]] = relationship(
        back_populates="kodesh_class", order_by="ClassSubject.sort_order"
    )

    def __repr__(self) -> str:
        return f"<KodeshClass {self.id}>"


class Subject(Base):
    """Catálogo global de matérias (Gemara, Chumash, Halachá...)."""

    __tablename__ = "subjects"
    __table_args__ = (MYSQL_TABLE_OPTIONS,)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(80), unique=True)
    is_active: Mapped[bool] = mapped_column(default=True, server_default=sa.true())
    sort_order: Mapped[int] = mapped_column(default=0, server_default="0")

    def __repr__(self) -> str:
        return f"<Subject {self.name}>"


class ClassSubject(Base):
    """Matéria dentro de um shiur. Com provas ou notas, não se apaga: desativa."""

    __tablename__ = "class_subjects"
    __table_args__ = (
        sa.UniqueConstraint("kodesh_class_id", "subject_id"),
        MYSQL_TABLE_OPTIONS,
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    kodesh_class_id: Mapped[int] = mapped_column(sa.ForeignKey("kodesh_classes.id"))
    subject_id: Mapped[int] = mapped_column(sa.ForeignKey("subjects.id"))
    default_teacher_id: Mapped[int | None] = user_fk()
    report_label: Mapped[str | None] = mapped_column(sa.String(80))
    sort_order: Mapped[int] = mapped_column(default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(default=True, server_default=sa.true())

    kodesh_class: Mapped[KodeshClass] = relationship(back_populates="subjects")
    subject: Mapped[Subject] = relationship()
    default_teacher: Mapped[User | None] = relationship()
    term_teachers: Mapped[list["ClassSubjectTerm"]] = relationship(back_populates="class_subject")

    def __repr__(self) -> str:
        return f"<ClassSubject {self.id}>"


class ClassSubjectTerm(Base):
    """Quem dá a matéria naquele trimestre (se mudar de rabino entre trimestres)."""

    __tablename__ = "class_subject_terms"
    __table_args__ = (
        sa.UniqueConstraint("class_subject_id", "term_id"),
        MYSQL_TABLE_OPTIONS,
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    class_subject_id: Mapped[int] = mapped_column(sa.ForeignKey("class_subjects.id"))
    term_id: Mapped[int] = mapped_column(sa.ForeignKey("terms.id"))
    teacher_id: Mapped[int] = mapped_column(sa.ForeignKey("users.id"))

    class_subject: Mapped[ClassSubject] = relationship(back_populates="term_teachers")
    term: Mapped[Term] = relationship()
    teacher: Mapped[User] = relationship()


class Enrollment(Base):
    """Aluno num shiur. Uma ativa por vez por ano (regra em app/services). Nunca é apagada."""

    __tablename__ = "enrollments"
    __table_args__ = (
        sa.CheckConstraint("end_date IS NULL OR end_date >= start_date", name="dates_order"),
        MYSQL_TABLE_OPTIONS,
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_year_id: Mapped[int] = mapped_column(sa.ForeignKey("student_years.id"))
    kodesh_class_id: Mapped[int] = mapped_column(sa.ForeignKey("kodesh_classes.id"))
    start_date: Mapped[date]
    end_date: Mapped[date | None]

    student_year: Mapped[StudentYear] = relationship()
    kodesh_class: Mapped[KodeshClass] = relationship()

    def __repr__(self) -> str:
        return f"<Enrollment {self.id}>"


class ClassTermStatus(Base):
    """Revisão por shiur e trimestre: open -> ready_for_review -> approved."""

    __tablename__ = "class_term_status"
    __table_args__ = (
        sa.UniqueConstraint("kodesh_class_id", "term_id"),
        MYSQL_TABLE_OPTIONS,
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    kodesh_class_id: Mapped[int] = mapped_column(sa.ForeignKey("kodesh_classes.id"))
    term_id: Mapped[int] = mapped_column(sa.ForeignKey("terms.id"))
    status: Mapped[ReviewStatus] = mapped_column(
        enum_column(ReviewStatus, "review_status"), default=ReviewStatus.OPEN
    )
    submitted_by: Mapped[int | None] = user_fk()
    submitted_at: Mapped[datetime | None]
    approved_by: Mapped[int | None] = user_fk()
    approved_at: Mapped[datetime | None]
