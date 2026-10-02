import pytest

from src.aplicacion.parser_consulta_pricing import parse_pricing_query
from src.aplicacion.enki_pricing_query_service import resolver_consulta_pricing


@pytest.mark.parametrize("amount,currency,value", [
    ("USD 100", "USD", 100),
    ("100 USD", "USD", 100),
    ("u$s 100", "USD", 100),
    ("100 u$s", "USD", 100),
    ("ARS 35.000,50", "ARS", 35000.5),
    ("35.000,50 ARS", "ARS", 35000.5),
    ("35000 pesos", "ARS", 35000),
    ("35.000,50 pesos argentinos", "ARS", 35000.5),
    ("$35.000,50", "ARS", 35000.5),
])
def test_explicit_currency_keeps_amount_and_hourly_scope(amount, currency, value):
    parsed = parse_pricing_query(
        f"Me cobran {amount} por hora por soporte remoto a todo el país"
    )

    assert parsed.price.currency == currency
    assert parsed.price.value == value
    assert "UNKNOWN_CURRENCY" not in (parsed.metadata.clarification_reason or "")
    assert parsed.price_scope.comparison_scope == "PER_HOUR"


def test_unmarked_amount_still_requires_currency_clarification():
    result = resolver_consulta_pricing(
        "Me cobran 100 por hora por soporte remoto a todo el país",
        local_cohortes=[], remote_cohortes=[],
    )
    assert result.parsed.price.currency == "UNKNOWN"
    assert result.status == "CLARIFICATION_REQUIRED"
    assert "UNKNOWN_CURRENCY" in result.clarification_reason
    assert "moneda" in result.clarification_question


@pytest.mark.parametrize("amount", ["USD 100 ARS", "ARS 100 USD", "$100 USD"])
def test_conflicting_currency_markers_require_clarification(amount):
    result = resolver_consulta_pricing(
        f"Me cobran {amount} por hora por soporte remoto a todo el país",
        local_cohortes=[], remote_cohortes=[],
    )
    assert result.parsed.price.currency == "UNKNOWN"
    assert result.status == "CLARIFICATION_REQUIRED"
    assert "UNKNOWN_CURRENCY" in result.clarification_reason


def test_two_prefix_currency_amounts_require_clarification():
    parsed = parse_pricing_query(
        "Me cobran ARS 35000 más ARS 10000 por hora por soporte remoto a todo el país"
    )
    assert parsed.metadata.clarification_required
    assert "MULTIPLE_MONETARY_MENTIONS" in parsed.metadata.clarification_reason
