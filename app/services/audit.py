"""Histórico de alterações (audit_log) de provas, notas, scans, frequência e comentários.

Grava no banco, nunca em log de texto: os dados são de menores.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from sqlalchemy import inspect

from app.extensions import db
from app.models import AuditLog, User


def _jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime | date):
        return value.isoformat()
    return value


def snapshot(obj: Any) -> dict[str, Any]:
    """Valores das colunas do objeto, prontos para JSON."""
    mapper = inspect(obj).mapper
    return {col.key: _jsonable(getattr(obj, col.key)) for col in mapper.column_attrs}


def record(
    user: User | None,
    action: str,
    obj: Any,
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
) -> AuditLog:
    """Registra a alteração. Chamar depois do flush (para o objeto ter id)."""
    entry = AuditLog(
        user_id=user.id if user else None,
        action=action,
        entity_type=obj.__tablename__,
        entity_id=obj.id,
        before_json=before,
        after_json=after,
    )
    db.session.add(entry)
    return entry
