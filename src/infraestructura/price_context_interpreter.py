from __future__ import annotations

from collections.abc import Mapping
import re
import unicodedata

from src.dominio.semantic_observation import (
    PriceContextKind,
    PriceContextMeaning,
    SemanticObservation,
    SemanticObservationRole,
)

from src.aplicacion.pricing_dimensions import normalize_source_price_scope


def interpret_price_context(
    observation: SemanticObservation,
    *,
    row: Mapping[str, str] | None = None,
) -> PriceContextMeaning:
    if observation.semantic_role is not SemanticObservationRole.PRICE_CONTEXT:
        raise ValueError("interpret_price_context requires a PRICE_CONTEXT observation.")

    row = row or {}
    raw = observation.raw_expression
    folded = _fold(raw)
    context_kind = _context_kind(folded)

    return PriceContextMeaning(
        source_expression=raw,
        context_kind=context_kind,
        provenance=observation.interpretation_provenance,
        price_scope=_price_scope(folded),
        published_currency=_clean(row.get("currency")) or "UNKNOWN",
        raw_currency_markers=_currency_markers(folded),
        percent_value=_percent_value(folded),
        quantity_unit=_quantity_unit(folded),
    )


def _context_kind(folded: str) -> PriceContextKind:
    if re.search(r"\bticket\b", folded):
        return PriceContextKind.TICKET_TIER
    if re.search(r"precio original|precio actual", folded):
        return PriceContextKind.PRICE_CHANGE
    if re.search(r"\badicional\b|\bextras?\b", folded):
        return PriceContextKind.ADDITIONAL_CHARGE
    if re.search(r"\boff\b|\bdescuento\b", folded):
        return PriceContextKind.PAYMENT_DISCOUNT
    if re.search(r"precio especial transferencia", folded):
        return PriceContextKind.PAYMENT_SPECIFIC_PRICE
    if re.search(r"precios? por cantidad|equipos?:", folded):
        return PriceContextKind.QUANTITY_PRICE_TABLE
    if re.search(r"\b\d+\s*hs\b|\bdemora\b", folded):
        return PriceContextKind.TURNAROUND_TIME
    return PriceContextKind.UNKNOWN


def _price_scope(folded: str) -> str:
    return normalize_source_price_scope(folded).comparison_scope


def _currency_markers(folded: str) -> tuple[str, ...]:
    markers = []
    if re.search(r"\bu\$s\b|\busd\b|\bdolares\b", folded):
        markers.append("USD")
    if re.search(r"(?<!u)\$|\bars\b|\bpesos\b", folded):
        markers.append("ARS")
    return tuple(dict.fromkeys(markers))


def _percent_value(folded: str) -> float | None:
    match = re.search(r"\b(\d+(?:[,.]\d+)?)\s*%", folded)
    if not match:
        return None
    return float(match.group(1).replace(",", "."))


def _quantity_unit(folded: str) -> str | None:
    if re.search(r"\bequipos?\b", folded):
        return "EQUIPMENT_COUNT"
    return None


def _fold(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    without_marks = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    return " ".join(without_marks.lower().split())


def _clean(value: object) -> str:
    return str(value or "").strip()
