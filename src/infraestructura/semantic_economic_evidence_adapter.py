from __future__ import annotations

from collections.abc import Iterable, Mapping
from decimal import Decimal, InvalidOperation

from src.aplicacion.pricing_dimensions import (
    infer_commercial_context,
    infer_price_scope,
)
from src.dominio.economic_evidence import (
    EconomicEvidenceDimensions,
    EconomicEvidenceDimensionsV2,
    EconomicEvidenceRecord,
)
from src.dominio.semantic_understanding import SemanticUnderstandingEnvelope


def compose_economic_evidence_records(
    rows: Iterable[Mapping[str, str]],
    envelopes: Iterable[SemanticUnderstandingEnvelope],
    *,
    dimensions_by_observation_id: Mapping[
        str, EconomicEvidenceDimensions | EconomicEvidenceDimensionsV2
    ] | None = None,
) -> tuple[EconomicEvidenceRecord, ...]:
    row_items = tuple(rows)
    envelope_items = tuple(envelopes)
    if len(row_items) != len(envelope_items):
        raise ValueError(
            f"Evidence cardinality mismatch: rows={len(row_items)} envelopes={len(envelope_items)}"
        )

    records: list[EconomicEvidenceRecord] = []
    for row, envelope in zip(row_items, envelope_items):
        observation = envelope.observation
        if _clean(row.get("observation_id")) != observation.observation_id:
            raise ValueError("Evidence/envelope observation_id order mismatch.")
        raw_expression = observation.raw_expression
        records.append(
            EconomicEvidenceRecord(
                evidence_id=observation.observation_id,
                raw_expression=raw_expression,
                semantic_role=observation.semantic_role,
                understanding_status=envelope.status,
                market_scope=observation.market_scope,
                provider=_clean(row.get("provider")) or observation.provider,
                province=observation.province,
                canonical_service=observation.canonical_service,
                matched_services=observation.matched_services,
                currency=_clean(row.get("currency")) or "UNKNOWN",
                price_value=_decimal(row.get("price_value")),
                price_scope=infer_price_scope(raw_expression),
                commercial_context=infer_commercial_context(raw_expression),
                provenance=observation.observation_provenance,
                meaning=envelope.meaning,
                dimensions=(dimensions_by_observation_id or {}).get(observation.observation_id),
            )
        )
    return tuple(records)


def _decimal(value: object) -> Decimal | None:
    text = _clean(value)
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def _clean(value: object) -> str:
    return str(value or "").strip()
