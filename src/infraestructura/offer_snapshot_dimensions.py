from __future__ import annotations

from typing import TypeVar

from src.dominio.economic_evidence import (
    DimensionClaim,
    DimensionOrigin,
    DimensionStatus,
    DimensionValue,
    EconomicEvidenceDimensionsV2,
    resolve_scalar_dimension,
    resolve_set_dimension,
)


T = TypeVar("T")


_COMMERCIAL_CONTEXT_INCOMPATIBLE_PAIRS = tuple(
    ("STANDARD", value)
    for value in (
        "URGENCY",
        "AFTER_HOURS",
        "WEEKEND_HOLIDAY",
        "PROMOTION",
        "DISCOUNT",
    )
)


def compose_snapshot_dimension(
    source: DimensionValue[T],
    *,
    raw_document_id: str,
    set_valued: bool = False,
    incompatible_pairs: tuple[tuple[object, object], ...] = (),
) -> DimensionValue[T]:
    raw_document_id = str(raw_document_id or "").strip()

    if not raw_document_id:
        raise ValueError(
            "Snapshot dimension composition requires raw_document_id."
        )

    if source.status is DimensionStatus.UNKNOWN:
        return DimensionValue(
            value=None,
            status=DimensionStatus.UNKNOWN,
            claims=(),
        )

    compatible_claims = tuple(
        claim
        for claim in source.claims
        if _claim_is_snapshot_compatible(
            claim,
            raw_document_id=raw_document_id,
        )
    )

    if not compatible_claims:
        return DimensionValue(
            value=None,
            status=DimensionStatus.UNKNOWN,
            claims=(),
        )

    if set_valued:
        return resolve_set_dimension(
            *compatible_claims,
            incompatible_pairs=incompatible_pairs,
        )

    return resolve_scalar_dimension(*compatible_claims)


def compose_snapshot_economic_dimensions(
    source: EconomicEvidenceDimensionsV2,
    *,
    raw_document_id: str,
) -> EconomicEvidenceDimensionsV2:
    return EconomicEvidenceDimensionsV2(
        provider_identity=compose_snapshot_dimension(
            source.provider_identity,
            raw_document_id=raw_document_id,
        ),
        price_scope=compose_snapshot_dimension(
            source.price_scope,
            raw_document_id=raw_document_id,
        ),
        currency=compose_snapshot_dimension(
            source.currency,
            raw_document_id=raw_document_id,
        ),
        delivery_mode=compose_snapshot_dimension(
            source.delivery_mode,
            raw_document_id=raw_document_id,
        ),
        geographic_reach=compose_snapshot_dimension(
            source.geographic_reach,
            raw_document_id=raw_document_id,
        ),
        location=compose_snapshot_dimension(
            source.location,
            raw_document_id=raw_document_id,
        ),
        commercial_context=compose_snapshot_dimension(
            source.commercial_context,
            raw_document_id=raw_document_id,
            set_valued=True,
            incompatible_pairs=(
                _COMMERCIAL_CONTEXT_INCOMPATIBLE_PAIRS
            ),
        ),
        bundle_status=compose_snapshot_dimension(
            source.bundle_status,
            raw_document_id=raw_document_id,
        ),
        hardware_included=compose_snapshot_dimension(
            source.hardware_included,
            raw_document_id=raw_document_id,
        ),
        materials_included=compose_snapshot_dimension(
            source.materials_included,
            raw_document_id=raw_document_id,
        ),
        device_scope=compose_snapshot_dimension(
            source.device_scope,
            raw_document_id=raw_document_id,
            set_valued=True,
        ),
    )


def _claim_is_snapshot_compatible(
    claim: DimensionClaim[object],
    *,
    raw_document_id: str,
) -> bool:
    if (
        claim.origin
        is not DimensionOrigin.RAW_SOURCE_OBSERVATION
    ):
        return True

    claim_raw_document_id = _raw_document_id_from_reference(
        claim.provenance.origin_reference
    )

    return claim_raw_document_id == raw_document_id


def _raw_document_id_from_reference(
    reference: str,
) -> str | None:
    for part in str(reference or "").split(";"):
        key, separator, value = part.strip().partition("=")

        if (
            separator
            and key.strip() == "raw_document_id"
        ):
            cleaned = value.strip()
            return cleaned or None

    return None
