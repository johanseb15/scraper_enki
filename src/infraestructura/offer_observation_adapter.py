from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Mapping

from src.dominio.offer_observation import (
    OfferObservation,
    PriceExpressionIdentity,
)


class OfferObservationAdaptationStatus(Enum):
    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"
    CONFLICTED = "CONFLICTED"


@dataclass(frozen=True)
class OfferObservationAdaptation:
    status: OfferObservationAdaptationStatus
    observation: OfferObservation | None
    reason: str | None


def adapt_legacy_offer_observation(
    *,
    identity_row: Mapping[str, Any],
    evidence_row: Mapping[str, Any],
    raw_expression: str,
    price_expression: PriceExpressionIdentity,
) -> OfferObservationAdaptation:
    identity_status = _clean(identity_row.get("status"))

    if identity_status != "RESOLVED":
        return _unresolved(
            f"IDENTITY_STATUS_{identity_status or 'UNKNOWN'}"
        )

    identity_observation_id = _clean(
        identity_row.get("observation_id")
    )
    evidence_observation_id = _clean(
        evidence_row.get("observation_id")
    )

    if identity_observation_id != evidence_observation_id:
        return _conflicted(
            "OBSERVATION_ID_MISMATCH: "
            f"identity={identity_observation_id or 'UNKNOWN'}; "
            f"evidence={evidence_observation_id or 'UNKNOWN'}"
        )

    lineage = evidence_row.get("lineage")
    if not isinstance(lineage, Mapping):
        return _unresolved("MISSING_EVIDENCE_LINEAGE")

    lineage_observation_id = _clean(
        lineage.get("observation_id")
    )

    if (
        lineage_observation_id
        and lineage_observation_id != identity_observation_id
    ):
        return _conflicted(
            "OBSERVATION_ID_MISMATCH: "
            f"identity={identity_observation_id}; "
            f"lineage={lineage_observation_id}"
        )

    identity_source = _clean(identity_row.get("source"))
    evidence_source = _clean(lineage.get("source_id"))

    if identity_source != evidence_source:
        return _conflicted(
            "SOURCE_ID_MISMATCH: "
            f"identity={identity_source or 'UNKNOWN'}; "
            f"evidence={evidence_source or 'UNKNOWN'}"
        )

    identity_raw_document_id = _clean(
        identity_row.get("raw_document_id")
    )
    evidence_raw_document_id = _clean(
        lineage.get("raw_document_id")
    )

    if not identity_raw_document_id:
        return _unresolved("MISSING_IDENTITY_RAW_DOCUMENT_ID")

    if not evidence_raw_document_id:
        return _unresolved("MISSING_EVIDENCE_RAW_DOCUMENT_ID")

    if identity_raw_document_id != evidence_raw_document_id:
        return _conflicted(
            "RAW_DOCUMENT_ID_MISMATCH: "
            f"identity={identity_raw_document_id}; "
            f"evidence={evidence_raw_document_id}"
        )

    offer_key = _clean(identity_row.get("offer_key"))
    if not offer_key:
        return _unresolved("MISSING_LOGICAL_OFFER_KEY")

    logical_offer_key = _logical_offer_key(
        offer_key,
        price_expression,
    )

    if not logical_offer_key:
        return _unresolved("INVALID_LOGICAL_OFFER_KEY")

    try:
        observation = OfferObservation.create(
            source_observation_id=identity_observation_id,
            source_id=identity_source,
            logical_offer_key=logical_offer_key,
            raw_document_id=identity_raw_document_id,
            raw_expression=raw_expression,
            price_expression=price_expression,
        )
    except ValueError as exc:
        return _unresolved(
            f"INVALID_OFFER_OBSERVATION: {exc}"
        )

    return OfferObservationAdaptation(
        status=OfferObservationAdaptationStatus.RESOLVED,
        observation=observation,
        reason=None,
    )


def _logical_offer_key(
    offer_key: str,
    price_expression: PriceExpressionIdentity,
) -> str:
    parts = offer_key.rsplit("|", 2)

    if len(parts) != 3:
        return offer_key

    candidate, legacy_price, legacy_currency = parts

    if (
        _same_numeric_value(
            legacy_price,
            price_expression.price_value,
        )
        and _clean(legacy_currency)
        == _clean(price_expression.currency)
    ):
        return candidate.strip()

    # Do not strip arbitrary suffixes merely because they contain pipes.
    return offer_key


def _same_numeric_value(left: str, right: str) -> bool:
    try:
        return Decimal(_clean(left)) == Decimal(_clean(right))
    except (InvalidOperation, ValueError):
        return _clean(left) == _clean(right)


def _clean(value: object) -> str:
    return str(value or "").strip()


def _unresolved(reason: str) -> OfferObservationAdaptation:
    return OfferObservationAdaptation(
        status=OfferObservationAdaptationStatus.UNRESOLVED,
        observation=None,
        reason=reason,
    )


def _conflicted(reason: str) -> OfferObservationAdaptation:
    return OfferObservationAdaptation(
        status=OfferObservationAdaptationStatus.CONFLICTED,
        observation=None,
        reason=reason,
    )
