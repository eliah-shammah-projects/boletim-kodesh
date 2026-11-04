from flask import Flask

from app.blueprints.admin import bp as admin_bp
from app.blueprints.attendance import bp as attendance_bp
from app.blueprints.auth import bp as auth_bp
from app.blueprints.classes import bp as classes_bp
from app.blueprints.files import bp as files_bp
from app.blueprints.grades import bp as grades_bp
from app.blueprints.imports import bp as imports_bp
from app.blueprints.main import bp as main_bp
from app.blueprints.reports import bp as reports_bp
from app.blueprints.students import bp as students_bp

BLUEPRINTS = (
    main_bp,
    auth_bp,
    admin_bp,
    students_bp,
    classes_bp,
    grades_bp,
    attendance_bp,
    files_bp,
    imports_bp,
    reports_bp,
)


def register_blueprints(app: Flask) -> None:
    for bp in BLUEPRINTS:
        app.register_blueprint(bp)
