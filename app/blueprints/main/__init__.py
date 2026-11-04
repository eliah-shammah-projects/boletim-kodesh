"""Tela inicial (pendências, Fase 14b) e verificação de disponibilidade."""

from flask import Blueprint, render_template

bp = Blueprint("main", __name__)


@bp.get("/")
def index():
    return render_template("main/index.html")


@bp.get("/healthz")
def healthz():
    return {"status": "ok"}
