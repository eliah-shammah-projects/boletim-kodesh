"""Shiurim do ano: criar, editar, página do shiur, matérias e rabinos por trimestre, alunos."""

from datetime import date, timedelta

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import select

from app.extensions import db
from app.models import (
    SHIUR_COLORS,
    ClassSubject,
    ClassSubjectTerm,
    Enrollment,
    KodeshClass,
    Student,
    Subject,
    User,
    UserRole,
)
from app.services import classes as svc
from app.services import students as student_svc
from app.services.errors import DomainError
from app.services.overview import class_summary, current_term
from app.services.reports import SCHOOL_GRADE_LABELS
from app.services.subjects import list_subjects
from app.web import admin_required, flash_error, selected_year

bp = Blueprint("classes", __name__, url_prefix="/shiurim")

COLOR_NAMES = {
    "azul": "Azul",
    "verde": "Verde",
    "vinho": "Vinho",
    "laranja": "Laranja",
    "marrom": "Marrom",
    "dourado": "Dourado",
    "petroleo": "Petróleo",
    "grafite": "Grafite",
}


def _rabbis() -> list[User]:
    return list(
        db.session.scalars(select(User).where(User.role == UserRole.RABBI).order_by(User.name))
    )


def _user(field: str) -> User | None:
    user_id = request.form.get(field, type=int)
    return db.session.get(User, user_id) if user_id else None


def _get_class(class_id: int) -> KodeshClass:
    return db.session.get(KodeshClass, class_id) or abort(404)


def _commit_or_flash(success: str) -> bool:
    db.session.commit()
    flash(success, "success")
    return True


@bp.route("/novo", methods=["GET", "POST"])
@admin_required
def create():
    year = selected_year() or abort(404)
    if request.method == "POST":
        try:
            kclass = svc.create_class(
                year,
                request.form.get("name", ""),
                request.form.get("level"),
                _user("homeroom_rabbi_id"),
                request.form.get("color", "azul"),
            )
            # Matérias marcadas: sem rabino próprio, valem com o rabino da turma até escolher outro.
            for sid in request.form.getlist("subject_ids", type=int):
                subject = db.session.get(Subject, sid)
                if subject:
                    svc.add_class_subject(kclass, subject)
        except DomainError as exc:
            db.session.rollback()
            flash_error(exc)
            return render_template(
                "classes/form.html",
                kclass=None,
                form=request.form,
                rabbis=_rabbis(),
                colors=COLOR_NAMES,
                subjects=list_subjects(True),
            )
        _commit_or_flash(f"{kclass.name} criado.")
        return redirect(url_for("classes.detail", class_id=kclass.id))
    return render_template(
        "classes/form.html",
        kclass=None,
        form=None,
        rabbis=_rabbis(),
        colors=COLOR_NAMES,
        subjects=list_subjects(True),
    )


@bp.route("/<int:class_id>/editar", methods=["GET", "POST"])
@admin_required
def edit(class_id: int):
    kclass = _get_class(class_id)
    if request.method == "POST":
        try:
            svc.update_class(
                kclass,
                request.form.get("name", ""),
                request.form.get("level"),
                _user("homeroom_rabbi_id"),
                request.form.get("color", kclass.color),
            )
        except DomainError as exc:
            db.session.rollback()
            flash_error(exc)
            return render_template(
                "classes/form.html",
                kclass=kclass,
                form=request.form,
                rabbis=_rabbis(),
                colors=COLOR_NAMES,
                subjects=[],
            )
        _commit_or_flash("Shiur salvo.")
        return redirect(url_for("classes.detail", class_id=kclass.id))
    return render_template(
        "classes/form.html",
        kclass=kclass,
        form=None,
        rabbis=_rabbis(),
        colors=COLOR_NAMES,
        subjects=[],
    )


@bp.get("/<int:class_id>")
@login_required
def detail(class_id: int):
    kclass = _get_class(class_id)
    year = kclass.academic_year
    term = current_term(year)
    class_subjects = list(
        db.session.scalars(
            select(ClassSubject)
            .where(ClassSubject.kodesh_class_id == kclass.id)
            .order_by(ClassSubject.sort_order, ClassSubject.id)
        )
    )
    term_teachers = {
        (ct.class_subject_id, ct.term_id): ct.teacher
        for ct in db.session.scalars(
            select(ClassSubjectTerm).where(
                ClassSubjectTerm.class_subject_id.in_([cs.id for cs in class_subjects] or [0])
            )
        )
    }
    enrollments = list(
        db.session.scalars(
            select(Enrollment).where(
                Enrollment.kodesh_class_id == kclass.id, Enrollment.end_date.is_(None)
            )
        )
    )
    enrollments.sort(key=lambda e: e.student_year.student.full_name)
    used = {cs.subject_id for cs in class_subjects if cs.is_active}
    return render_template(
        "classes/detail.html",
        kclass=kclass,
        year=year,
        term=term,
        terms=list(year.terms),
        class_subjects=class_subjects,
        term_teachers=term_teachers,
        effective={
            (cs.id, t.id): svc.effective_teacher(cs, t) for cs in class_subjects for t in year.terms
        },
        enrollments=enrollments,
        summary=class_summary(kclass, term),
        rabbis=_rabbis(),
        available_subjects=[s for s in list_subjects(True) if s.id not in used],
        grades=SCHOOL_GRADE_LABELS,
        colors=COLOR_NAMES,
        preset_class_id=kclass.id,
        can_edit=_can_admin(kclass),
    )


def _can_admin(kclass: KodeshClass) -> bool:
    from flask_login import current_user

    return current_user.is_admin and kclass.academic_year.status.value == "active"


# ---------- Matérias do shiur ----------


@bp.post("/<int:class_id>/materias")
@admin_required
def add_subject(class_id: int):
    kclass = _get_class(class_id)
    subject = db.session.get(Subject, request.form.get("subject_id", type=int) or 0) or abort(400)
    try:
        svc.add_class_subject(kclass, subject, _user("default_teacher_id"))
    except DomainError as exc:
        db.session.rollback()
        flash_error(exc)
    else:
        _commit_or_flash(f"{subject.name} entrou no {kclass.name}.")
    return redirect(url_for("classes.detail", class_id=kclass.id) + "#materias")


@bp.post("/materia/<int:cs_id>")
@admin_required
def update_subject(cs_id: int):
    cs = db.session.get(ClassSubject, cs_id) or abort(404)
    try:
        svc.update_class_subject(cs, _user("default_teacher_id"), request.form.get("report_label"))
        for term in cs.kodesh_class.academic_year.terms:
            field = f"term_teacher_{term.id}"
            if field in request.form:
                svc.set_term_teacher(cs, term, _user(field))
    except DomainError as exc:
        db.session.rollback()
        flash_error(exc)
    else:
        _commit_or_flash(f"{cs.subject.name} salvo.")
    return redirect(url_for("classes.detail", class_id=cs.kodesh_class_id) + "#materias")


@bp.post("/materia/<int:cs_id>/ativa")
@admin_required
def toggle_subject(cs_id: int):
    cs = db.session.get(ClassSubject, cs_id) or abort(404)
    try:
        svc.set_class_subject_active(cs, not cs.is_active)
    except DomainError as exc:
        db.session.rollback()
        flash_error(exc)
    else:
        verb = "voltou para o" if cs.is_active else "foi desativado no"
        _commit_or_flash(
            f"{cs.subject.name} {verb} {cs.kodesh_class.name}. "
            "As provas e notas continuam guardadas."
        )
    return redirect(url_for("classes.detail", class_id=cs.kodesh_class_id) + "#materias")


@bp.post("/materia/<int:cs_id>/mover")
@admin_required
def move_subject(cs_id: int):
    cs = db.session.get(ClassSubject, cs_id) or abort(404)
    svc.move_class_subject(cs, -1 if request.form.get("direction") == "up" else 1)
    db.session.commit()
    return redirect(url_for("classes.detail", class_id=cs.kodesh_class_id) + "#materias")


# ---------- Alunos do shiur ----------


@bp.post("/<int:class_id>/alunos")
@admin_required
def add_student(class_id: int):
    """Coloca um aluno já cadastrado no shiur (entra no ano, se ainda não estiver)."""
    kclass = _get_class(class_id)
    student = db.session.get(Student, request.form.get("student_id", type=int) or 0) or abort(400)
    year = kclass.academic_year
    try:
        sy = student_svc.student_year(student, year)
        if sy is None:
            grade = request.form.get("school_grade", type=int) or 10
            sy = student_svc.add_to_year(student, year, grade)
        on = max(date.today(), year.start_date)
        current = svc.active_enrollment(sy)
        if current is not None and on <= current.start_date:
            on = current.start_date + timedelta(days=1)  # troca vale no mínimo no dia seguinte
        svc.move_to_class(sy, kclass, on)
    except DomainError as exc:
        db.session.rollback()
        flash_error(exc)
    else:
        _commit_or_flash(f"{student.full_name} entrou no {kclass.name}.")
    return redirect(url_for("classes.detail", class_id=kclass.id) + "#alunos")


@bp.post("/matricula/<int:enrollment_id>/sair")
@admin_required
def remove_student(enrollment_id: int):
    enrollment = db.session.get(Enrollment, enrollment_id) or abort(404)
    kclass = enrollment.kodesh_class
    name = enrollment.student_year.student.full_name
    try:
        svc.remove_from_class(enrollment.student_year, max(date.today(), enrollment.start_date))
    except DomainError as exc:
        db.session.rollback()
        flash_error(exc)
    else:
        _commit_or_flash(
            f"{name} saiu do {kclass.name}. As notas dele neste shiur continuam guardadas."
        )
    return redirect(url_for("classes.detail", class_id=kclass.id) + "#alunos")


@bp.get("/<int:class_id>/buscar-aluno")
@admin_required
def search_student(class_id: int):
    """Busca de aluno para colocar no shiur (HTMX)."""
    kclass = _get_class(class_id)
    q = request.args.get("q", "").strip()
    found = student_svc.search_students(q, active_only=True, limit=10) if len(q) >= 2 else []
    current = {
        e.student_year.student_id
        for e in db.session.scalars(
            select(Enrollment).where(
                Enrollment.kodesh_class_id == kclass.id, Enrollment.end_date.is_(None)
            )
        )
    }
    return render_template(
        "classes/_search_results.html",
        kclass=kclass,
        found=found,
        q=q,
        current=current,
        year=kclass.academic_year,
        where={s.id: student_svc.current_class(s, kclass.academic_year) for s in found},
    )


assert set(COLOR_NAMES) == set(SHIUR_COLORS)
