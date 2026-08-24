from __future__ import annotations

from src.dominio.commercial_context import (
    CommercialContext,
    CommercialContextOrigin,
    resolve_commercial_context,
)
from src.dominio.price_scope_contract import PriceScopeMeaning, normalize_price_scope


def normalize_source_price_scope(
    economic_object_raw: str,
    *,
    has_price: bool = False,
    is_range: bool = False,
) -> PriceScopeMeaning:
    return normalize_price_scope(
        economic_object_raw,
        has_price=has_price,
        is_range=is_range,
        provenance="raw_source_expression",
    )


def infer_price_scope(economic_object_raw: str) -> str:
    # Compatibility projection over the single typed price-scope engine.
    return normalize_source_price_scope(economic_object_raw).comparison_scope


def infer_commercial_context(economic_object_raw: str) -> CommercialContext:
    return resolve_commercial_context(
        economic_object_raw,
        origin=CommercialContextOrigin.SOURCE_CLAIM,
    )
