"""Fixtures de teste. Os testes de banco rodam sempre contra MySQL, nunca SQLite.

Sem MySQL de teste disponível, os testes de banco são pulados localmente.
No CI (variável CI definida) a falta do banco é erro.
"""

import os

import pytest
from flask_migrate import upgrade
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, scoped_session

from app import create_app
from app.extensions import db


@pytest.fixture(scope="session")
def app():
    app = create_app("testing")
    url = make_url(app.config["SQLALCHEMY_DATABASE_URI"])
    if url.get_backend_name() != "mysql":
        pytest.exit("Os testes rodam só contra MySQL.", returncode=1)
    if not (url.database or "").endswith("_test"):
        pytest.exit("O banco de testes precisa terminar em _test.", returncode=1)
    with app.app_context():
        yield app


@pytest.fixture(scope="session")
def _database(app):
    try:
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError:
        if os.environ.get("CI"):
            raise
        pytest.skip("MySQL de teste indisponível. Estes testes rodam no GitHub Actions.")
    upgrade()
    yield
    db.engine.dispose()


@pytest.fixture
def db_conn(_database):
    """Conexão dentro de uma transação desfeita no fim do teste."""
    with db.engine.connect() as conn:
        trans = conn.begin()
        yield conn
        trans.rollback()


@pytest.fixture
def db_session(_database, monkeypatch):
    """`db.session` ligado a uma transação desfeita no fim do teste.

    Commits dentro do teste viram savepoints, então nada fica no banco.
    """
    with db.engine.connect() as conn:
        trans = conn.begin()
        session = scoped_session(
            lambda: Session(bind=conn, join_transaction_mode="create_savepoint")
        )
        monkeypatch.setattr(db, "session", session)
        yield session
        session.remove()
        trans.rollback()
