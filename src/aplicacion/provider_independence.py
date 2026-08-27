from __future__ import annotations

from src.dominio.economic_evidence import (
    DimensionStatus,
    EconomicEvidenceDimensionsV2,
)


PROVIDER_INDEPENDENCE_VERSION = "provider-independence-contract-v1"


def stable_provider_id(
    dimensions: EconomicEvidenceDimensionsV2 | None,
) -> str | None:
    if dimensions is None:
        return None

    provider = dimensions.provider_identity
    if provider.status not in {
        DimensionStatus.OBSERVED,
        DimensionStatus.INFERRED,
    }:
        return None
    if provider.value is None:
        return None

    provider_id = str(provider.value.provider_id or "").strip()
    return provider_id or None
