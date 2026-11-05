"""Cadastros da direção: anos letivos (trimestres, datas, escala, fechar) e catálogo de matérias."""

from datetime import date
from decimal import Decimal, InvalidOperation

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for
from sqlalchemy import select

from app.extensions import db
from app.models import AcademicYear, Subject, Term
from app.services import subjects as subject_svc
from app.services import years as year_svc
from app.services.errors import DomainError, ValidationError
from app.web import YEAR_SESSION_KEY, admin_required, flash_error

bp = Blueprint("admin", __name__, url_prefix="/cadastros")


def _date(field: str) -> date | None:
    value = request.form.get(field) or None
    try:
        return date.fromisoformat(value) if value else None
    except ValueError as exc:
        raise ValidationError("Use uma data válida.") from exc


def _decimal(field: str) -> Decimal:
    raw = (request.form.get(field) or "").replace(",", ".").strip()
    try:
        return Decimal(raw)
    except InvalidOperation as exc:
        raise ValidationError("A nota máxima precisa ser um número (ex: 10).") from exc


@bp.get("/")
@admin_required
def index():
    years = list(db.session.scalars(select(AcademicYear).order_by(AcademicYear.name.desc())))
    return render_template(
        "admin/index.html",
        years=years,
        subjects=subject_svc.list_subjects(),
        active=year_svc.get_active_year(),
        today=date.today(),
    )


@bp.post("/anos")
@admin_required
def create_year():
    try:
        year = year_svc.create_year(
            (request.form.get("name") or "").strip(),
            _date("start_date") or abort(400),
            _date("end_date"),
            _decimal("grade_scale_max"),
            request.form.get("terms", type=int) or 3,
        )
    except DomainError as exc:
        db.session.rollback()
        flash_error(exc)
        return redirect(url_for("admin.index"))
    db.session.commit()
    session[YEAR_SESSION_KEY] = year.id
    flash(f"Ano {year.name} criado, com {len(year.terms)} trimestres.", "success")
    return redirect(url_for("admin.year", year_id=year.id))


@bp.route("/anos/<int:year_id>", methods=["GET", "POST"])
@admin_required
def year(year_id: int):
    year = db.session.get(AcademicYear, year_id) or abort(404)
    if request.method == "POST":
        try:
            year_svc.ensure_year_editable(year)
            for term in year.terms:
                name = (request.form.get(f"term_{term.id}_name") or "").strip()
                if name:
                    term.name = name
                term.start_date = _date(f"term_{term.id}_start")
                term.end_date = _date(f"term_{term.id}_end")
                if term.start_date and term.end_date and term.end_date < term.start_date:
                    raise ValidationError(f"No {term.name}, o fim precisa ser depois do início.")
            scale = _decimal("grade_scale_max")
            if scale != year.grade_scale_max:
                year_svc.set_grade_scale(year, scale)
            db.session.flush()
        except DomainError as exc:
            db.session.rollback()
            flash_error(exc)
            return redirect(url_for("admin.year", year_id=year.id))
        db.session.commit()
        flash(f"Ano {year.name} salvo.", "success")
        return redirect(url_for("admin.year", year_id=year.id))
    return render_template(
        "admin/year.html",
        year=year,
        terms=list(year.terms),
        has_scores=year_svc.year_has_scores(year),
    )


@bp.post("/anos/<int:year_id>/fechar")
@admin_required
def close_year(year_id: int):
    year = db.session.get(AcademicYear, year_id) or abort(404)
    try:
        year_svc.archive_year(year)
    except DomainError as exc:
        db.session.rollback()
        flash_error(exc)
    else:
        db.session.commit()
        flash(f"Ano {year.name} fechado. Ele fica no arquivo, só para leitura.", "success")
    return redirect(url_for("admin.index"))


@bp.post("/anos/trimestre/<int:term_id>/travar")
@admin_required
def toggle_term_lock(term_id: int):
    from flask_login import current_user

    from app.services import review

    term = db.session.get(Term, term_id) or abort(404)
    try:
        if term.is_locked:
            review.unlock_term(current_user, term)
        else:
            review.lock_term(current_user, term)
    except DomainError as exc:
        db.session.rollback()
        flash_error(exc)
    else:
        db.session.commit()
        flash(f"{term.name} {'travado' if term.is_locked else 'destravado'}.", "success")
    return redirect(url_for("admin.year", year_id=term.academic_year_id))


# ---------- Matérias ----------


@bp.post("/materias")
@admin_required
def create_subject():
    try:
        subject = subject_svc.create_subject(request.form.get("name", ""))
    except DomainError as exc:
        db.session.rollback()
        flash_error(exc)
    else:
        db.session.commit()
        flash(f"{subject.name} incluída no catálogo.", "success")
    return redirect(url_for("admin.index") + "#materias")


@bp.post("/materias/<int:subject_id>")
@admin_required
def update_subject(subject_id: int):
    subject = db.session.get(Subject, subject_id) or abort(404)
    try:
        if "name" in request.form:
            subject_svc.rename_subject(subject, request.form["name"])
        if request.form.get("toggle") == "1":
            subject_svc.set_subject_active(subject, not subject.is_active)
    except DomainError as exc:
        db.session.rollback()
        flash_error(exc)
    else:
        db.session.commit()
        flash(f"{subject.name} salva.", "success")
    return redirect(url_for("admin.index") + "#materias")
