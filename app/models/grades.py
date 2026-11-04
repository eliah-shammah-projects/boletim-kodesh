"""Provas, notas, scans, frequência e comentários. Tudo ligado à matrícula (enrollment)."""

import datetime as dt
from datetime import datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    MYSQL_TABLE_OPTIONS,
    AttendanceSource,
    Base,
    CommentCategory,
    CommentVisibility,
    FileKind,
    Score,
    ScoreStatus,
    created_at_column,
    enum_column,
    updated_at_column,
    user_fk,
)
from app.models.classes import ClassSubject, Enrollment
from app.models.people import Term


class Assessment(Base):
    """Prova de uma matéria no trimestre. Recuperação e segunda chamada também são provas."""

    __tablename__ = "assessments"
    __table_args__ = (
        sa.CheckConstraint("max_score > 0", name="max_score_positive"),
        MYSQL_TABLE_OPTIONS,
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    class_subject_id: Mapped[int] = mapped_column(sa.ForeignKey("class_subjects.id"))
    term_id: Mapped[int] = mapped_column(sa.ForeignKey("terms.id"))
    name: Mapped[str] = mapped_column(sa.String(120))
    date: Mapped[dt.date | None] = mapped_column(sa.Date)
    # Padrão: grade_scale_max do ano (definido no service ao criar).
    max_score: Mapped[Decimal] = mapped_column(Score)
    include_in_report: Mapped[bool] = mapped_column(default=True, server_default=sa.true())
    sort_order: Mapped[int] = mapped_column(default=0, server_default="0")
    created_by: Mapped[int | None] = user_fk()
    created_at: Mapped[datetime] = created_at_column()

    class_subject: Mapped[ClassSubject] = relationship()
    term: Mapped[Term] = relationship()
    scores: Mapped[list["AssessmentScore"]] = relationship(back_populates="assessment")
    files: Mapped[list["AssessmentFile"]] = relationship(back_populates="assessment")

    def __repr__(self) -> str:
        return f"<Assessment {self.id}>"


class AssessmentScore(Base):
    """Nota do aluno na prova. 'absent' e 'exempt' não têm nota; 'graded' sempre tem.

    O limite superior (max_score da prova) é validado em app/services.
    """

    __tablename__ = "assessment_scores"
    __table_args__ = (
        sa.UniqueConstraint("assessment_id", "enrollment_id"),
        sa.CheckConstraint("score IS NULL OR score >= 0", name="score_not_negative"),
        sa.CheckConstraint(
            "(status = 'graded' AND score IS NOT NULL) OR (status <> 'graded' AND score IS NULL)",
            name="score_matches_status",
        ),
        MYSQL_TABLE_OPTIONS,
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(sa.ForeignKey("assessments.id"))
    enrollment_id: Mapped[int] = mapped_column(sa.ForeignKey("enrollments.id"))
    score: Mapped[Decimal | None] = mapped_column(Score)
    status: Mapped[ScoreStatus] = mapped_column(
        enum_column(ScoreStatus, "score_status"), default=ScoreStatus.GRADED
    )
    updated_by: Mapped[int | None] = user_fk()
    updated_at: Mapped[datetime] = updated_at_column()

    assessment: Mapped[Assessment] = relationship(back_populates="scores")
    enrollment: Mapped[Enrollment] = relationship()

    def __repr__(self) -> str:  # sem a nota: dados de menores não vão para logs
        return f"<AssessmentScore {self.id}>"


class AssessmentFile(Base):
    """Scan da prova do aluno (com enrollment_id), prova em branco ou gabarito.

    O arquivo fica no storage; aqui só a chave e os metadados. Nunca vai para o boletim.
    A regra "student_scan tem aluno, os outros não" é validada em app/services.
    """

    __tablename__ = "assessment_files"
    __table_args__ = (
        sa.CheckConstraint("size_bytes >= 0", name="size_not_negative"),
        MYSQL_TABLE_OPTIONS,
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(sa.ForeignKey("assessments.id"))
    enrollment_id: Mapped[int | None] = mapped_column(sa.ForeignKey("enrollments.id"))
    kind: Mapped[FileKind] = mapped_column(enum_column(FileKind, "file_kind"))
    storage_key: Mapped[str] = mapped_column(sa.String(255), unique=True)
    mime_type: Mapped[str] = mapped_column(sa.String(100))
    size_bytes: Mapped[int] = mapped_column(sa.BigInteger)
    page_count: Mapped[int | None] = mapped_column(sa.SmallInteger)
    uploaded_by: Mapped[int | None] = user_fk()
    created_at: Mapped[datetime] = created_at_column()

    assessment: Mapped[Assessment] = relationship(back_populates="files")
    enrollment: Mapped[Enrollment | None] = relationship()


class TermAttendance(Base):
    """Frequência do aluno no trimestre, uma só para o shiur (não por matéria).

    Presença % = (aulas dadas - faltas) / aulas dadas * 100. Atraso conta como presença.
    """

    __tablename__ = "term_attendance"
    __table_args__ = (
        sa.UniqueConstraint("enrollment_id", "term_id"),
        sa.CheckConstraint("classes_held >= 0", name="held_not_negative"),
        sa.CheckConstraint("absences >= 0 AND absences <= classes_held", name="absences_range"),
        sa.CheckConstraint("lates >= 0 AND lates <= classes_held", name="lates_range"),
        MYSQL_TABLE_OPTIONS,
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    enrollment_id: Mapped[int] = mapped_column(sa.ForeignKey("enrollments.id"))
    term_id: Mapped[int] = mapped_column(sa.ForeignKey("terms.id"))
    classes_held: Mapped[int] = mapped_column(sa.SmallInteger)
    absences: Mapped[int] = mapped_column(sa.SmallInteger, default=0, server_default="0")
    lates: Mapped[int] = mapped_column(sa.SmallInteger, default=0, server_default="0")
    source: Mapped[AttendanceSource] = mapped_column(
        enum_column(AttendanceSource, "attendance_source"), default=AttendanceSource.MANUAL
    )
    updated_by: Mapped[int | None] = user_fk()
    updated_at: Mapped[datetime] = updated_at_column()

    enrollment: Mapped[Enrollment] = relationship()
    term: Mapped[Term] = relationship()


class Comment(Base):
    """Comentário do aluno no trimestre.

    Público (geral e comportamento): só o rabino da turma, no máximo um de cada por aluno
    por trimestre. Interno: qualquer rabino, ilimitado, nunca sai do sistema.
    Os limites e permissões são validados em app/services.
    """

    __tablename__ = "comments"
    __table_args__ = (MYSQL_TABLE_OPTIONS,)

    id: Mapped[int] = mapped_column(primary_key=True)
    enrollment_id: Mapped[int] = mapped_column(sa.ForeignKey("enrollments.id"))
    term_id: Mapped[int] = mapped_column(sa.ForeignKey("terms.id"))
    category: Mapped[CommentCategory] = mapped_column(
        enum_column(CommentCategory, "comment_category")
    )
    visibility: Mapped[CommentVisibility] = mapped_column(
        enum_column(CommentVisibility, "comment_visibility")
    )
    text: Mapped[str] = mapped_column(sa.Text)
    author_id: Mapped[int] = mapped_column(sa.ForeignKey("users.id"))
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()

    enrollment: Mapped[Enrollment] = relationship()
    term: Mapped[Term] = relationship()
