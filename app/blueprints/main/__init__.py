"""Tela inicial (shiurim do ano), escolha do ano, entrada provisória e /healthz."""

from flask import (
    Blueprint,
    abort,
    current_app,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import login_required, login_user, logout_user
from sqlalchemy import select

from app.extensions import db
from app.models import AcademicYear, User
from app.services.overview import current_term, year_overview
from app.services.subjects import list_subjects
from app.web import YEAR_SESSION_KEY, back, selected_year

bp = Blueprint("main", __name__)


@bp.get("/healthz")
def healthz():
    return {"status": "ok"}


@bp.get("/")
@login_required
def index():
    year = selected_year()
    if year is None:
        return render_template("main/no_year.html")
    term = current_term(year)
    rabbis = list(db.session.scalars(select(User).order_by(User.name)))
    return render_template(
        "main/index.html",
        year=year,
        term=term,
        summaries=year_overview(year, term),
        rabbis=rabbis,
        subjects=list_subjects(active_only=True),
    )


@bp.get("/ano/<int:year_id>")
@login_required
def choose_year(year_id: int):
    year = db.session.get(AcademicYear, year_id) or abort(404)
    session[YEAR_SESSION_KEY] = year.id
    return back("main.index")


# ---------- Entrada provisória (até a Fase 3: login com senha) ----------


@bp.route("/entrar-como", methods=["GET", "POST"])
def dev_login():
    if not current_app.config.get("DEV_LOGIN"):
        abort(404)
    users = list(
        db.session.scalars(
            select(User).where(User.is_active.is_(True)).order_by(User.role, User.name)
        )
    )
    if request.method == "POST":
        user = db.session.get(User, request.form.get("user_id", type=int) or 0)
        if user is None or not user.is_active:
            abort(400)
        login_user(user)
        return back("main.index")
    return render_template("main/dev_login.html", users=users, next=request.args.get("next", ""))


@bp.post("/sair")
def logout():
    logout_user()
    session.pop(YEAR_SESSION_KEY, None)
    return redirect(url_for("main.dev_login"))
