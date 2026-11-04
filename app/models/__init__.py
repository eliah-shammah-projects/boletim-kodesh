"""Modelos SQLAlchemy (PLAN.md, seção 4).

Importar daqui. Importar este pacote registra todas as tabelas no metadata (migrações).
"""

from app.models.admin import AppSetting, AuditLog, Document, ImportBatch, ReportDelivery
from app.models.base import (
    SHIUR_COLORS,
    AttendanceSource,
    Base,
    CommentCategory,
    CommentVisibility,
    DeliveryStatus,
    FileKind,
    ImportKind,
    ImportStatus,
    ReviewStatus,
    ScoreStatus,
    UserRole,
    YearStatus,
)
from app.models.classes import (
    ClassSubject,
    ClassSubjectTerm,
    ClassTermStatus,
    Enrollment,
    KodeshClass,
    Subject,
)
from app.models.grades import (
    Assessment,
    AssessmentFile,
    AssessmentScore,
    Comment,
    TermAttendance,
)
from app.models.people import AcademicYear, Student, StudentYear, Term, User

__all__ = [
    "SHIUR_COLORS",
    "AcademicYear",
    "AppSetting",
    "Assessment",
    "AssessmentFile",
    "AssessmentScore",
    "AttendanceSource",
    "AuditLog",
    "Base",
    "ClassSubject",
    "ClassSubjectTerm",
    "ClassTermStatus",
    "Comment",
    "CommentCategory",
    "CommentVisibility",
    "DeliveryStatus",
    "Document",
    "Enrollment",
    "FileKind",
    "ImportBatch",
    "ImportKind",
    "ImportStatus",
    "KodeshClass",
    "ReportDelivery",
    "ReviewStatus",
    "ScoreStatus",
    "Student",
    "StudentYear",
    "Subject",
    "Term",
    "TermAttendance",
    "User",
    "UserRole",
    "YearStatus",
]
