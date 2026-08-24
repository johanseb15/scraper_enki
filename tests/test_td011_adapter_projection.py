from __future__ import annotations

import pytest

from src.aplicacion.pricing_dimensions import normalize_source_price_scope
from src.dominio.price_scope_contract import (
    comparison_scope_from_charged_unit,
    project_price_scope_dimension,
)
from src.infraestructura.economic_dimensions_adapter import _explicit_price_scope as explicit_v1
from src.infraestructura.economic_dimensions_v2_adapter import (
    _charged_unit_to_scope,
    _explicit_price_scope as explicit_v2,
)


@pytest.mark.parametrize(
    ("phrase", "expected"),
    (
        ("hora inicial", "PER_HOUR"),
        ("hora adicional", "PER_HOUR"),
        ("por proyecto", "PER_PROJECT"),
        ("precio total", "FIXED_TOTAL"),
        ("total final", "FIXED_TOTAL"),
        ("desde 15000", "LOWER_BOUND"),
        ("a partir de 20000", "LOWER_BOUND"),
        ("sin modalidad de cobro", None),
    ),
)
def test_both_economic_adapters_project_from_the_single_typed_engine(phrase, expected):
    typed = normalize_source_price_scope(phrase, has_price=any(ch.isdigit() for ch in phrase))
    assert project_price_scope_dimension(typed) == expected
    assert explicit_v1(phrase) == expected
    assert explicit_v2(phrase) == expected


@pytest.mark.parametrize(
    ("unit", "expected"),
    (
        ("HOUR", "PER_HOUR"),
        ("VISIT", "PER_VISIT"),
        ("UNIT", "PER_UNIT"),
        ("PROJECT", "PER_PROJECT"),
        ("TOTAL", "FIXED_TOTAL"),
        ("UNKNOWN", None),
    ),
)
def test_charged_unit_projection_is_centralized(unit, expected):
    assert comparison_scope_from_charged_unit(unit) == expected
    assert _charged_unit_to_scope(unit) == expected


def test_month_source_claim_keeps_billing_period_compatibility_projection():
    assert _charged_unit_to_scope("MONTH") == "PER_MONTH"
