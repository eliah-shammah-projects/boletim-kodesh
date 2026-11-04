import pytest
from sqlalchemy import text

pytestmark = pytest.mark.usefixtures("_database")


def test_database_charset_and_collation(db_conn):
    row = db_conn.execute(text("SELECT @@character_set_database, @@collation_database")).one()
    assert tuple(row) == ("utf8mb4", "utf8mb4_unicode_ci")


def test_connection_uses_utf8mb4(db_conn):
    charset = db_conn.execute(text("SELECT @@character_set_connection")).scalar_one()
    assert charset == "utf8mb4"


def test_session_fixture_executes(db_session):
    assert db_session.execute(text("SELECT 1")).scalar_one() == 1
