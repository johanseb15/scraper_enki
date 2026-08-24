from __future__ import annotations

import pytest

from src.aplicacion.pricing_dimensions import infer_price_scope, normalize_source_price_scope
from src.dominio.price_scope_contract import (
    ChargedUnitMeaning,
    ScopeEpistemicStatus,
    normalize_price_scope,
)


@pytest.mark.parametrize(
    ("phrase", "expected"),
    (
        ("soporte por hora", "PER_HOUR"),
        ("hora inicial", "PER_HOUR"),
        ("hora adicional", "PER_HOUR"),
        ("hora de soporte", "PER_HOUR"),
        ("por mes", "PER_MONTH"),
        ("abono mensual", "PER_MONTH"),
        ("por visita", "PER_VISIT"),
        ("por equipo", "PER_UNIT"),
        ("por proyecto", "PER_PROJECT"),
        ("precio total", "FIXED_TOTAL"),
        ("total final", "FIXED_TOTAL"),
        ("servicio sin indicar modalidad de cobro", "UNKNOWN"),
    ),
)
def test_user_and_source_paths_share_one_scope_vocabulary(phrase, expected):
    user = normalize_price_scope(phrase, has_price=False)
    source = normalize_source_price_scope(phrase)

    assert user.comparison_scope == expected
    assert source.comparison_scope == expected
    assert infer_price_scope(phrase) == expected


def test_shared_engine_preserves_origin_without_changing_semantic_meaning():
    phrase = "hora adicional"
    user = normalize_price_scope(phrase, has_price=False)
    source = normalize_source_price_scope(phrase)

    assert user.charged_unit is ChargedUnitMeaning.HOUR
    assert source.charged_unit is ChargedUnitMeaning.HOUR
    assert user.status is source.status is ScopeEpistemicStatus.EXPLICIT
    assert user.raw_basis == source.raw_basis == "hora adicional"
    assert user.provenance == "raw_user_input"
    assert source.provenance == "raw_source_expression"


@pytest.mark.parametrize(
    ("phrase", "expected_bound"),
    (
        ("desde 15000", "FROM"),
        ("a partir de 20000", "FROM"),
    ),
)
def test_bound_semantics_are_shared_even_when_comparison_scope_is_unknown(phrase, expected_bound):
    user = normalize_price_scope(phrase, has_price=True)
    source = normalize_source_price_scope(phrase, has_price=True)

    assert user.comparison_scope == source.comparison_scope == "UNKNOWN"
    assert user.price_bound.value == source.price_bound.value == expected_bound
    assert user.status.value == source.status.value == "EXPLICIT"
