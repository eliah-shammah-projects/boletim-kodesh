"""Tela inicial (pendências, Fase 14b) e verificação de disponibilidade."""

from flask import Blueprint

bp = Blueprint("main", __name__)


@bp.get("/healthz")
def healthz():
    return {"status": "ok"}
