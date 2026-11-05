"""Protótipo navegável da Fase 1, com dados fictícios.

Só é registrado com PROTOTYPE_ENABLED (ligado em desenvolvimento e testes).
"""

from decimal import ROUND_HALF_UP, Decimal

from flask import Blueprint, abort, render_template, request, url_for

from app.blueprints.prototype import data

bp = Blueprint("prototype", __name__, url_prefix="/prototipo")


def _nav(persona: str, active: str) -> list[dict]:
    items = [
        ("shiurim", "Shiurim", "users", "prototype.index"),
        ("alunos", "Alunos", "user", "prototype.students"),
    ]
    return [
        {"label": label, "icon": ico, "href": url_for(endpoint), "active": key == active}
        for key, label, ico, endpoint in items
    ]


def _page(template: str, persona: str = "rabbi", active: str = "", **context):
    user = "Direção" if persona == "admin" else data.RABBIS["levi"]
    years = dict(data.YEARS)
    selected = request.args.get("ano", data.YEAR)
    if selected not in years:
        selected = data.YEAR
    return render_template(
        f"prototype/{template}",
        nav_items=_nav(persona, active),
        user_name=user,
        home_href=url_for("prototype.index"),
        year_options=[
            (name, url_for("prototype.index", ano=name), archived)
            for name, archived in data.YEARS
        ],
        selected_year=selected,
        year_archived=years[selected],
        d=data,
        **context,
    )


def _percent(held: int, absences: int) -> Decimal:
    value = Decimal(held - absences) * 100 / Decimal(held)
    return value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


@bp.get("/")
def index():
    """Primeira tela: os shiurim do ano, criar shiur, inserir aluno e exportar."""
    return _page("shiurim.html", active="shiurim")


@bp.get("/alunos")
def students():
    return _page("students.html", active="alunos")


@bp.get("/aluno/<int:student_id>")
def student(student_id: int):
    st = next((s for s in data.STUDENTS if s["id"] == student_id), None)
    if st is None:
        abort(404)
    absences, lates = data.ATTENDANCE[student_id]
    gemara = [
        (a["name"], data.SCORES[(student_id, a["id"])], a["max"], a["in_report"])
        for a in data.ASSESSMENTS
    ]
    return _page(
        "student.html",
        active="shiurim",
        st=st,
        gemara=gemara,
        absences=absences,
        lates=lates,
        presence=_percent(data.CLASSES_HELD, absences),
    )


@bp.get("/componentes")
def components():
    return _page("components.html", persona="admin", active="config")


@bp.get("/shiur", defaults={"slug": "alef"})
@bp.get("/shiur/<slug>")
def shiur(slug: str):
    c = next((c for c in data.CLASSES if c["slug"] == slug), None)
    if c is None:
        abort(404)
    return _page("shiur.html", active="shiurim", c=c)


@bp.get("/criar-shiur")
def create_shiur():
    return _page("create_shiur.html", active="shiurim")


@bp.get("/notas")
def grades():
    return _page("grades.html", active="shiurim")


@bp.get("/scans")
def scans():
    return _page("scans.html", active="shiurim")


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
    review = request.args.get("revisao") == "1"
    return _page(
        "report.html",
        persona="admin" if review else "rabbi",
        active="shiurim",
        presence=_percent(att["held"], att["absences"]),
        review=review,
    )
