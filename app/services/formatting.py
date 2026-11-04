"""Formatação de números no padrão brasileiro (vírgula decimal)."""

from decimal import ROUND_HALF_UP, Decimal


def format_decimal(value: Decimal | int | None, places: int = 1) -> str:
    """Até `places` casas, sem zero inútil: 10 -> "10", 6.6 -> "6,6", 9.50 -> "9,5"."""
    if value is None:
        return ""
    quantized = Decimal(value).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
    text = format(quantized.normalize(), "f")
    return text.replace(".", ",")


def format_score(score: Decimal | None, max_score: Decimal, scale_max: Decimal) -> str:
    """Nota como foi dada. Se a prova tem máximo diferente da escala do ano, mostra o máximo."""
    text = format_decimal(score)
    if Decimal(max_score) != Decimal(scale_max):
        text += "/" + format_decimal(max_score)
    return text


def format_percent(value: Decimal | None) -> str:
    if value is None:
        return ""
    return format_decimal(value) + "%"
