"""Regras sem banco: leitura da nota digitada, validação da nota e da frequência, % de presença."""

from decimal import Decimal

import pytest

from app.models import ScoreStatus
from app.services.attendance import presence_percent, validate_attendance
from app.services.errors import ValidationError
from app.services.grades import parse_score_input, validate_score
from app.services.reports import SCHOOL_GRADE_LABELS

TEN = Decimal("10")


@pytest.mark.parametrize(
    ("raw", "status", "score"),
    [
        ("8,5", ScoreStatus.GRADED, Decimal("8.5")),
        ("8.5", ScoreStatus.GRADED, Decimal("8.5")),
        (" 10 ", ScoreStatus.GRADED, Decimal("10.0")),
        ("0", ScoreStatus.GRADED, Decimal("0.0")),
        ("a", ScoreStatus.ABSENT, None),
        ("A", ScoreStatus.ABSENT, None),
        ("Ausente", ScoreStatus.ABSENT, None),
        ("d", ScoreStatus.EXEMPT, None),
        ("Dispensado", ScoreStatus.EXEMPT, None),
        ("", None, None),
        ("   ", None, None),
    ],
)
def test_parse_score_input(raw, status, score):
    parsed = parse_score_input(raw, TEN)
    assert parsed.status == status
    assert parsed.score == score


@pytest.mark.parametrize("raw", ["11", "10,1", "-1", "8,55", "8.5.1", "x", "1e1", "8,"])
def test_parse_score_input_rejects(raw):
    with pytest.raises(ValidationError):
        parse_score_input(raw, TEN)


def test_score_above_own_max_is_ok_when_max_is_20():
    assert parse_score_input("18", Decimal("20")).score == Decimal("18.0")


def test_validate_score_message_tells_the_range():
    with pytest.raises(ValidationError, match="entre 0 e 10"):
        validate_score(Decimal("12"), TEN)


def test_validate_score_rejects_two_decimals():
    with pytest.raises(ValidationError, match="1 casa"):
        validate_score(Decimal("7.25"), TEN)


@pytest.mark.parametrize(
    ("held", "absences", "expected"),
    [
        (48, 0, Decimal("100.0")),
        (48, 2, Decimal("95.8")),
        (48, 5, Decimal("89.6")),
        (3, 1, Decimal("66.7")),  # arredonda meio para cima
        (10, 10, Decimal("0.0")),
    ],
)
def test_presence_percent(held, absences, expected):
    assert presence_percent(held, absences) == expected


def test_presence_without_classes_is_none():
    assert presence_percent(0, 0) is None


def test_lates_count_as_presence():
    # Atrasos não entram na conta: só as faltas tiram presença.
    assert presence_percent(48, 0) == Decimal("100.0")


@pytest.mark.parametrize(
    ("held", "absences", "lates"), [(10, 11, 0), (10, 0, 11), (-1, 0, 0), (10, -1, 0)]
)
def test_validate_attendance_rejects(held, absences, lates):
    with pytest.raises(ValidationError):
        validate_attendance(held, absences, lates)


def test_validate_attendance_accepts_limits():
    validate_attendance(10, 10, 10)


def test_school_grade_labels():
    assert SCHOOL_GRADE_LABELS[8] == "8º ano"
    assert SCHOOL_GRADE_LABELS[10] == "1º colegial"
    assert SCHOOL_GRADE_LABELS[12] == "3º colegial"
