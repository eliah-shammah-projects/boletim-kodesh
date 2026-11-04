"""Grava e lê do MySQL texto com acentos e com hebraico.

Usa uma tabela temporária (some ao fechar a conexão), porque os modelos
só existem a partir da Fase 2a.
"""

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.usefixtures("_database")

SAMPLES = [
    "João Conceição",
    "Ação, atenção, é, à, ô, ü, ç",
    "גמרא",
    "שָׁלוֹם עֲלֵיכֶם",  # com nikud
    "Gemara גמרא - Prova 1",  # misto, como em nomes de provas
    "𝄞 caractere de 4 bytes (exige utf8mb4, não utf8mb3)",
]


@pytest.fixture
def unicode_table(db_conn):
    db_conn.execute(
        text(
            "CREATE TEMPORARY TABLE unicode_check ("
            " id INT AUTO_INCREMENT PRIMARY KEY,"
            " short_text VARCHAR(255) NOT NULL,"
            " long_text TEXT NOT NULL)"
        )
    )
    yield db_conn
    db_conn.execute(text("DROP TEMPORARY TABLE IF EXISTS unicode_check"))


def test_table_inherits_utf8mb4_unicode_ci(unicode_table):
    rows = unicode_table.execute(text("SHOW FULL COLUMNS FROM unicode_check")).mappings()
    collations = {row["Field"]: row["Collation"] for row in rows}
    assert collations["short_text"] == "utf8mb4_unicode_ci"
    assert collations["long_text"] == "utf8mb4_unicode_ci"


@pytest.mark.parametrize("value", SAMPLES)
def test_roundtrip(unicode_table, value):
    unicode_table.execute(
        text("INSERT INTO unicode_check (short_text, long_text) VALUES (:s, :l)"),
        {"s": value, "l": value * 20},
    )
    row = unicode_table.execute(
        text("SELECT short_text, long_text FROM unicode_check WHERE short_text = :s"),
        {"s": value},
    ).one()
    assert row.short_text == value
    assert row.long_text == value * 20


def test_hebrew_length_is_counted_in_characters(unicode_table):
    unicode_table.execute(
        text("INSERT INTO unicode_check (short_text, long_text) VALUES (:v, '')"),
        {"v": "גמרא"},
    )
    length = unicode_table.execute(
        text("SELECT CHAR_LENGTH(short_text) FROM unicode_check")
    ).scalar_one()
    assert length == 4


def test_collation_ignores_accents_when_searching(unicode_table):
    """Documenta o comportamento de utf8mb4_unicode_ci: 'Jose' encontra 'José'."""
    unicode_table.execute(
        text("INSERT INTO unicode_check (short_text, long_text) VALUES ('José', '')")
    )
    found = unicode_table.execute(
        text("SELECT COUNT(*) FROM unicode_check WHERE short_text = 'Jose'")
    ).scalar_one()
    assert found == 1


def test_roundtrip_through_session(db_session):
    value = "שָׁלוֹם João"
    assert db_session.execute(text("SELECT :v"), {"v": value}).scalar_one() == value
