"""Base dos modelos: nomes de constraints, opções de tabela MySQL, enums e tipos comuns.

Modelo de dados: PLAN.md, seção 4. Não criar tabelas ou campos novos sem perguntar.
"""

import enum
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Nomes previsíveis para índices e constraints: as migrações ficam estáveis.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# Toda tabela em InnoDB, utf8mb4 / utf8mb4_unicode_ci (CLAUDE.md).
MYSQL_TABLE_OPTIONS = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


class Base(DeclarativeBase):
    metadata = sa.MetaData(naming_convention=NAMING_CONVENTION)


# Nota com até 1 casa decimal, sempre Decimal (nunca float).
Score = sa.Numeric(5, 1, asdecimal=True)


def enum_column(py_enum: type[enum.Enum], name: str) -> sa.Enum:
    """ENUM do MySQL guardando o valor (ex: 'admin'), não o nome do membro."""
    return sa.Enum(
        py_enum,
        name=name,
        values_callable=lambda e: [m.value for m in e],
        validate_strings=True,
    )


def created_at_column() -> Mapped[datetime]:
    return mapped_column(sa.DateTime, server_default=sa.func.now(), nullable=False)


def updated_at_column() -> Mapped[datetime]:
    return mapped_column(
        sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False
    )


def user_fk(nullable: bool = True) -> Mapped[int | None]:
    return mapped_column(sa.ForeignKey("users.id"), nullable=nullable)


# ---------- Enums ----------


class UserRole(enum.Enum):
    ADMIN = "admin"
    RABBI = "rabbi"


class YearStatus(enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class ScoreStatus(enum.Enum):
    GRADED = "graded"
    ABSENT = "absent"
    EXEMPT = "exempt"


class FileKind(enum.Enum):
    STUDENT_SCAN = "student_scan"
    BLANK_EXAM = "blank_exam"
    ANSWER_KEY = "answer_key"


class AttendanceSource(enum.Enum):
    MANUAL = "manual"
    IMPORT = "import"


class CommentCategory(enum.Enum):
    GENERAL = "general"
    BEHAVIOR = "behavior"


class CommentVisibility(enum.Enum):
    PUBLIC = "public"
    INTERNAL = "internal"


class ReviewStatus(enum.Enum):
    OPEN = "open"
    READY_FOR_REVIEW = "ready_for_review"
    APPROVED = "approved"


class DeliveryStatus(enum.Enum):
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"


class ImportKind(enum.Enum):
    STUDENTS = "students"
    ATTENDANCE = "attendance"


class ImportStatus(enum.Enum):
    PREVIEW = "preview"
    APPLIED = "applied"
    DISCARDED = "discarded"


# Paleta das cores de fita dos shiurim (decisão do usuário). Todas com contraste para texto branco.
SHIUR_COLORS = {
    "azul": "#2F6FA3",
    "verde": "#2E7D4F",
    "vinho": "#8E2C48",
    "laranja": "#B4561F",
    "marrom": "#7A4A2A",
    "dourado": "#8F6B12",
    "petroleo": "#1F6F73",
    "grafite": "#4A5560",
}
