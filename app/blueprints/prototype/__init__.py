"""Protótipo navegável da Fase 1, com dados fictícios.

Só é registrado com PROTOTYPE_ENABLED (ligado em desenvolvimento e testes).
"""

from decimal import ROUND_HALF_UP, Decimal

from flask import Blueprint, render_template, url_for

from app.blueprints.prototype import data

bp = Blueprint("prototype", __name__, url_prefix="/prototipo")


def _nav(persona: str, active: str) -> list[dict]:
    if persona == "admin":
        items = [
            ("inicio", "Início", "house", "prototype.home_admin"),
            ("shiurim", "Shiurim", "users", "prototype.shiur"),
            ("alunos", "Alunos", "user", "prototype.index"),
            ("config", "Ajustes", "settings", "prototype.components"),
        ]
    else:
        items = [
            ("inicio", "Início", "house", "prototype.home_rabbi"),
            ("shiurim", "Meus shiurim", "users", "prototype.shiur"),
            ("notas", "Notas", "clipboard-list", "prototype.grades"),
        ]
    return [
        {"label": label, "icon": ico, "href": url_for(endpoint), "active": key == active}
        for key, label, ico, endpoint in items
    ]


def _page(template: str, persona: str = "rabbi", active: str = "", **context):
    user = "Direção" if persona == "admin" else data.RABBIS["levi"]
    home = "prototype.home_admin" if persona == "admin" else "prototype.home_rabbi"
    return render_template(
        f"prototype/{template}",
        nav_items=_nav(persona, active),
        user_name=user,
        home_href=url_for(home),
        d=data,
        **context,
    )


def _percent(held: int, absences: int) -> Decimal:
    value = Decimal(held - absences) * 100 / Decimal(held)
    return value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


@bp.get("/")
def index():
    return _page("index.html", active="")


@bp.get("/componentes")
def components():
    return _page("components.html", persona="admin", active="config")


@bp.get("/inicio/rabino")
def home_rabbi():
    return _page("home_rabbi.html", active="inicio")


@bp.get("/inicio/direcao")
def home_admin():
    return _page("home_admin.html", persona="admin", active="inicio")


@bp.get("/shiur")
def shiur():
    return _page("shiur.html", active="shiurim")


@bp.get("/notas")
def grades():
    return _page("grades.html", active="notas")


@bp.get("/scans")
def scans():
    return _page("scans.html", active="notas")


@bp.get("/frequencia")
def attendance():
    rows = [
        {**s, "absences": data.ATTENDANCE[s["id"]][0], "lates": data.ATTENDANCE[s["id"]][1]}
        for s in data.STUDENTS
    ]
    return _page("attendance.html", active="shiurim", rows=rows)


@bp.get("/boletim")
def report():
    att = data.REPORT["attendance"]
    return _page(
        "report.html",
        active="shiurim",
        presence=_percent(att["held"], att["absences"]),
    )
