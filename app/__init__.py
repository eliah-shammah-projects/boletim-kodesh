import os

from flask import Flask

from app.blueprints import register_blueprints
from app.extensions import csrf, db, migrate
from config import CONFIGS


def create_app(config_name: str | None = None) -> Flask:
    config_name = config_name or os.environ.get("FLASK_CONFIG", "development")
    app = Flask(__name__)
    app.config.from_object(CONFIGS[config_name])

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY não definida.")
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        raise RuntimeError("DATABASE_URL não definida.")

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    register_blueprints(app)
    return app
