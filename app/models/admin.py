"""Envio de boletins, documentos do aluno, importações, histórico de alterações e configurações."""

from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    MYSQL_TABLE_OPTIONS,
    Base,
    DeliveryStatus,
    ImportKind,
    ImportStatus,
    created_at_column,
    enum_column,
    updated_at_column,
    user_fk,
)
from app.models.classes import Enrollment
from app.models.people import Student


class ReportDelivery(Base):
    """Cada envio do boletim por email. Falhas podem ser reenviadas.

    term_id vazio = boletim anual (os 3 trimestres), pedido pelo usuário.
    """

    __tablename__ = "report_deliveries"
    __table_args__ = (MYSQL_TABLE_OPTIONS,)

    id: Mapped[int] = mapped_column(primary_key=True)
    enrollment_id: Mapped[int] = mapped_column(sa.ForeignKey("enrollments.id"))
    term_id: Mapped[int | None] = mapped_column(sa.ForeignKey("terms.id"))
    recipient_email: Mapped[str] = mapped_column(sa.String(255))
    status: Mapped[DeliveryStatus] = mapped_column(
        enum_column(DeliveryStatus, "delivery_status"), default=DeliveryStatus.QUEUED
    )
    error: Mapped[str | None] = mapped_column(sa.Text)
    sent_at: Mapped[datetime | None]
    sent_by: Mapped[int | None] = user_fk()

    enrollment: Mapped[Enrollment] = relationship()


class Document(Base):
    """Documento geral do aluno (fora das provas). Arquivo no storage, acesso por URL assinada."""

    __tablename__ = "documents"
    __table_args__ = (
        sa.CheckConstraint("size_bytes >= 0", name="size_not_negative"),
        MYSQL_TABLE_OPTIONS,
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(sa.ForeignKey("students.id"))
    academic_year_id: Mapped[int | None] = mapped_column(sa.ForeignKey("academic_years.id"))
    title: Mapped[str] = mapped_column(sa.String(160))
    storage_key: Mapped[str] = mapped_column(sa.String(255), unique=True)
    mime_type: Mapped[str] = mapped_column(sa.String(100))
    size_bytes: Mapped[int] = mapped_column(sa.BigInteger)
    uploaded_by: Mapped[int | None] = user_fk()
    created_at: Mapped[datetime] = created_at_column()

    student: Mapped[Student] = relationship()


class ImportBatch(Base):
    """Histórico de importações de Excel: preview -> applied (ou discarded)."""

    __tablename__ = "import_batches"
    __table_args__ = (MYSQL_TABLE_OPTIONS,)

    id: Mapped[int] = mapped_column(primary_key=True)
    academic_year_id: Mapped[int] = mapped_column(sa.ForeignKey("academic_years.id"))
    term_id: Mapped[int | None] = mapped_column(sa.ForeignKey("terms.id"))
    kind: Mapped[ImportKind] = mapped_column(enum_column(ImportKind, "import_kind"))
    filename: Mapped[str] = mapped_column(sa.String(255))
    uploaded_by: Mapped[int | None] = user_fk()
    created_at: Mapped[datetime] = created_at_column()
    status: Mapped[ImportStatus] = mapped_column(
        enum_column(ImportStatus, "import_status"), default=ImportStatus.PREVIEW
    )
    summary_json: Mapped[dict[str, Any] | None] = mapped_column(sa.JSON)


class AuditLog(Base):
    """Toda alteração de prova, nota, scan, frequência e comentário."""

    __tablename__ = "audit_log"
    __table_args__ = (
        sa.Index("ix_audit_log_entity", "entity_type", "entity_id"),
        MYSQL_TABLE_OPTIONS,
    )

    id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True)
    user_id: Mapped[int | None] = user_fk()
    action: Mapped[str] = mapped_column(sa.String(40))  # create | update | delete | ...
    entity_type: Mapped[str] = mapped_column(sa.String(60))
    entity_id: Mapped[int] = mapped_column(sa.BigInteger)
    before_json: Mapped[dict[str, Any] | None] = mapped_column(sa.JSON)
    after_json: Mapped[dict[str, Any] | None] = mapped_column(sa.JSON)
    created_at: Mapped[datetime] = created_at_column()


class AppSetting(Base):
    """Configurações editáveis pelo admin (ex: email e nome do remetente). Pedido do usuário."""

    __tablename__ = "app_settings"
    __table_args__ = (MYSQL_TABLE_OPTIONS,)

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(sa.String(80), unique=True)
    value: Mapped[str | None] = mapped_column(sa.Text)
    updated_by: Mapped[int | None] = user_fk()
    updated_at: Mapped[datetime] = updated_at_column()
