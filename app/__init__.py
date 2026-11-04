import os

from flask import Flask

from app.blueprints import register_blueprints
from app.extensions import csrf, db, migrate
from app.services.formatting import format_decimal, format_percent, format_score
from config import CONFIGS


def create_app(config_name: str | None = None) -> Flask:
    config_name = config_name or os.environ.get("FLASK_CONFIG", "development")
    app = Flask(__name__)
    app.config.from_object(CONFIGS[config_name])

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY não definida.")
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        raise RuntimeError("DATABASE_URL não definida.")

    from app import models  # noqa: F401  registra as tabelas no metadata

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    app.jinja_env.filters.update(decimal=format_decimal, percent=format_percent)
    app.jinja_env.globals.update(format_score=format_score)

    register_blueprints(app)
    return app
