"""Peças comuns das telas: usuário logado, ano escolhido, menu, avisos e permissões nas rotas."""

from functools import wraps

from flask import Flask, abort, flash, redirect, request, session, url_for
from flask_login import current_user
from sqlalchemy import select

from app.extensions import db, login_manager
from app.models import AcademicYear, KodeshClass, User, YearStatus
from app.services.errors import DomainError

YEAR_SESSION_KEY = "year_id"


@login_manager.user_loader
def _load_user(user_id: str) -> User | None:
    user = db.session.get(User, int(user_id))
    return user if user and user.is_active else None


def selected_year() -> AcademicYear | None:
    """Ano escolhido no topo da tela (padrão: o ano ativo)."""
    year_id = session.get(YEAR_SESSION_KEY)
    year = db.session.get(AcademicYear, year_id) if year_id else None
    if year is None:
        year = db.session.scalar(
            select(AcademicYear).where(AcademicYear.status == YearStatus.ACTIVE)
        )
    return year


def admin_required(view):
    """Só a direção. Rabino que tenta entrar vê 'sem permissão'."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)

    return wrapper


def flash_error(error: DomainError) -> None:
    flash(error.message, "danger")


def back(default_endpoint: str, **values):
    """Volta para a página anterior (só dentro do site)."""
    target = request.form.get("next") or request.args.get("next")
    if target and target.startswith("/") and not target.startswith("//"):
        return redirect(target)
    return redirect(url_for(default_endpoint, **values))


def _nav_items() -> list[dict]:
    if not current_user.is_authenticated:
        return []
    endpoint = request.endpoint or ""
    items = [
        ("Shiurim", "users", "main.index", endpoint.startswith(("main.index", "classes."))),
        ("Alunos", "user", "students.index", endpoint.startswith("students.")),
    ]
    if current_user.is_admin:
        items.append(("Cadastros", "settings", "admin.index", endpoint.startswith("admin.")))
    return [
        {"label": label, "icon": ico, "href": url_for(ep), "active": active}
        for label, ico, ep, active in items
    ]


def register_web(app: Flask) -> None:
    login_manager.init_app(app)
    login_manager.login_view = "main.dev_login" if app.config.get("DEV_LOGIN") else None
    login_manager.login_message = "Entre para continuar."
    login_manager.login_message_category = "info"

    @app.context_processor
    def _layout_context():
        if request.blueprint == "prototype" or not current_user.is_authenticated:
            return {}
        year = selected_year()
        years = list(db.session.scalars(select(AcademicYear).order_by(AcademicYear.name.desc())))
        return {
            "nav_items": _nav_items(),
            "user_name": current_user.name,
            "home_href": url_for("main.index"),
            "year_options": [
                (
                    y.name,
                    url_for("main.choose_year", year_id=y.id, next=request.path),
                    y.status == YearStatus.ARCHIVED,
                )
                for y in years
            ],
            "selected_year": year.name if year else None,
            "year_archived": bool(year and year.status == YearStatus.ARCHIVED),
            "current_year": year,
            "year_classes": list(
                db.session.scalars(
                    select(KodeshClass)
                    .where(KodeshClass.academic_year_id == year.id)
                    .order_by(KodeshClass.sort_order, KodeshClass.name)
                )
            )
            if year
            else [],
            "logout_href": url_for("main.logout"),
        }
