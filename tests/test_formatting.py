from decimal import Decimal

import pytest

from app.services.formatting import format_decimal, format_percent, format_score


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (Decimal("10"), "10"),
        (Decimal("10.0"), "10"),
        (Decimal("6.6"), "6,6"),
        (Decimal("9.50"), "9,5"),
        (Decimal("0"), "0"),
        (Decimal("0.0"), "0"),
        (Decimal("7.25"), "7,3"),  # meio para cima, como na escola
        (None, ""),
    ],
)
def test_format_decimal(value, expected):
    assert format_decimal(value) == expected


def test_score_on_year_scale_has_no_max():
    assert format_score(Decimal("8.5"), Decimal("10"), Decimal("10")) == "8,5"


def test_score_with_own_max_shows_max():
    assert format_score(Decimal("18"), Decimal("20"), Decimal("10")) == "18/20"


def test_format_percent():
    assert format_percent(Decimal("95.8")) == "95,8%"
    assert format_percent(Decimal("100.0")) == "100%"
