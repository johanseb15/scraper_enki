from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from src.dominio.offer_observation import (
    OfferObservation,
    PriceExpressionIdentity,
)
from src.infraestructura.offer_observation_adapter import (
    adapt_legacy_offer_observation,
)


class OfferSnapshotProjectionStatus(Enum):
    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class OfferSnapshotProjection:
    source_observation_id: str
    source_id: str
    raw_document_id: str
    provenance_kind: str
    status: OfferSnapshotProjectionStatus
    observation: OfferObservation | None
    reason: str | None


def project_legacy_offer_snapshots(
    *,
    identity_row: Mapping[str, Any],
    evidence_row: Mapping[str, Any],
    raw_expression: str,
    price_expression: PriceExpressionIdentity,
) -> tuple[OfferSnapshotProjection, ...]:
    source_observation_id = _clean(
        identity_row.get("observation_id")
        or evidence_row.get("observation_id")
    )

    identity_source = _clean(identity_row.get("source"))

    lineage = evidence_row.get("lineage")
    lineage = lineage if isinstance(lineage, Mapping) else {}

    evidence_source = _clean(lineage.get("source_id"))

    source_id = identity_source or evidence_source

    rows: dict[str, OfferSnapshotProjection] = {}

    targeted_raw_id = _clean(
        identity_row.get("raw_document_id")
    )

    if (
        _clean(identity_row.get("status")) == "RESOLVED"
        and targeted_raw_id
    ):
        synthetic_evidence = {
            "observation_id": source_observation_id,
            "lineage": {
                "observation_id": source_observation_id,
                "source_id": identity_source,
                "raw_document_id": targeted_raw_id,
            },
        }

        adapted = adapt_legacy_offer_observation(
            identity_row=identity_row,
            evidence_row=synthetic_evidence,
            raw_expression=raw_expression,
            price_expression=price_expression,
        )

        if adapted.observation is not None:
            rows[targeted_raw_id] = OfferSnapshotProjection(
                source_observation_id=source_observation_id,
                source_id=identity_source,
                raw_document_id=targeted_raw_id,
                provenance_kind="TARGETED_EXACT_OFFER_IDENTITY",
                status=OfferSnapshotProjectionStatus.RESOLVED,
                observation=adapted.observation,
                reason=None,
            )
        else:
            rows[targeted_raw_id] = OfferSnapshotProjection(
                source_observation_id=source_observation_id,
                source_id=identity_source,
                raw_document_id=targeted_raw_id,
                provenance_kind="TARGETED_EXACT_OFFER_IDENTITY",
                status=OfferSnapshotProjectionStatus.UNRESOLVED,
                observation=None,
                reason=adapted.reason or "TARGETED_IDENTITY_NOT_RESOLVED",
            )

    historical_raw_id = _clean(
        lineage.get("raw_document_id")
    )

    if historical_raw_id:
        if historical_raw_id in rows:
            return tuple(
                rows[key]
                for key in sorted(rows)
            )

        rows[historical_raw_id] = OfferSnapshotProjection(
            source_observation_id=source_observation_id,
            source_id=evidence_source or source_id,
            raw_document_id=historical_raw_id,
            provenance_kind="HISTORICAL_OFFER_EVIDENCE",
            status=OfferSnapshotProjectionStatus.UNRESOLVED,
            observation=None,
            reason="MISSING_LOGICAL_OFFER_IDENTITY",
        )

    return tuple(
        rows[key]
        for key in sorted(rows)
    )


def _clean(value: object) -> str:
    return str(value or "").strip()
