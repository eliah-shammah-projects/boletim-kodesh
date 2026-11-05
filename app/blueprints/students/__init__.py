"""Alunos: lista com busca, cadastro (com aviso de nome igual), página do aluno e edição."""

from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import select

from app.extensions import db
from app.models import Enrollment, KodeshClass, Student, StudentYear
from app.services import students as svc
from app.services.errors import ConflictError, DomainError
from app.services.reports import SCHOOL_GRADE_LABELS
from app.web import admin_required, back, flash_error, selected_year

bp = Blueprint("students", __name__, url_prefix="/alunos")


def _form_data() -> svc.StudentData:
    f = request.form
    birth = f.get("birth_date") or None
    return svc.StudentData(
        first_name=f.get("first_name", ""),
        last_name=f.get("last_name", ""),
        hebrew_name=f.get("hebrew_name"),
        external_id=f.get("external_id"),
        birth_date=date.fromisoformat(birth) if birth else None,
        parent_name=f.get("parent_name"),
        parent_phone=f.get("parent_phone"),
        parent_email=f.get("parent_email"),
        parent_email_2=f.get("parent_email_2"),
        notes=f.get("notes"),
    )


@bp.get("/")
@login_required
def index():
    q = request.args.get("q", "")
    year = selected_year()
    found = svc.search_students(q)
    classes = {}
    if year:
        rows = db.session.execute(
            select(StudentYear.student_id, KodeshClass)
            .join(Enrollment, Enrollment.student_year_id == StudentYear.id)
            .join(KodeshClass, Enrollment.kodesh_class_id == KodeshClass.id)
            .where(StudentYear.academic_year_id == year.id, Enrollment.end_date.is_(None))
        )
        classes = {sid: kc for sid, kc in rows}
    return render_template("students/index.html", students=found, q=q, classes=classes, year=year)


@bp.post("/novo")
@admin_required
def create():
    year = selected_year()
    data = _form_data()
    grade = request.form.get("school_grade", type=int)
    class_id = request.form.get("class_id", type=int)
    kclass = db.session.get(KodeshClass, class_id) if class_id else None
    confirm = request.form.get("confirm_same_name") == "1"
    try:
        student = svc.create_student(
            data,
            year=year if grade else None,
            school_grade=grade,
            kodesh_class=kclass,
            confirm_same_name=confirm,
        )
    except ConflictError as exc:
        # Busca os parecidos antes de desfazer: o rollback não pode apagar a resposta.
        matches = [] if confirm else svc.same_name(data.first_name, data.last_name)
        db.session.rollback()
        if matches:
            # Nome igual: mostra os alunos parecidos e pede confirmação.
            return render_template(
                "students/confirm_same_name.html", data=request.form, matches=matches, year=year
            )
        flash_error(exc)
        return back("students.index")
    except DomainError as exc:
        db.session.rollback()
        flash_error(exc)
        return back("students.index")
    db.session.commit()
    where = f" no {kclass.name}" if kclass else (" sem shiur por enquanto" if grade else "")
    flash(f"{student.full_name} foi cadastrado{where}.", "success")
    return redirect(request.form.get("next") or url_for("students.detail", student_id=student.id))


@bp.get("/<int:student_id>")
@login_required
def detail(student_id: int):
    student = db.session.get(Student, student_id) or abort(404)
    years = list(
        db.session.scalars(select(StudentYear).where(StudentYear.student_id == student.id))
    )
    years.sort(key=lambda sy: sy.academic_year.name, reverse=True)
    history = []
    for sy in years:
        enrollments = list(
            db.session.scalars(
                select(Enrollment)
                .where(Enrollment.student_year_id == sy.id)
                .order_by(Enrollment.start_date)
            )
        )
        history.append((sy, enrollments))
    return render_template(
        "students/detail.html",
        student=student,
        history=history,
        grades=SCHOOL_GRADE_LABELS,
        year=selected_year(),
    )


@bp.route("/<int:student_id>/editar", methods=["GET", "POST"])
@admin_required
def edit(student_id: int):
    student = db.session.get(Student, student_id) or abort(404)
    if request.method == "POST":
        try:
            svc.update_student(student, _form_data())
        except DomainError as exc:
            db.session.rollback()
            flash_error(exc)
            return render_template("students/form.html", student=student, form=request.form)
        db.session.commit()
        flash("Dados do aluno salvos.", "success")
        return redirect(url_for("students.detail", student_id=student.id))
    return render_template("students/form.html", student=student, form=None)


@bp.post("/<int:student_id>/ativo")
@admin_required
def toggle_active(student_id: int):
    student = db.session.get(Student, student_id) or abort(404)
    svc.set_active(student, not student.is_active)
    db.session.commit()
    flash(
        f"{student.full_name} foi {'reativado' if student.is_active else 'desativado'}.", "success"
    )
    return redirect(url_for("students.detail", student_id=student.id))
