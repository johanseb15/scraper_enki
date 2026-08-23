from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from enum import Enum

from src.dominio.economic_evidence import (
    DimensionStatus,
    EconomicEvidenceDimensionsV2,
)


SERVICE_REACH_GATE_VERSION = "offer-service-reach-admission-gate-v1"
EXCLUSION_REASON_MISSING_SERVICE_REACH = "MISSING_SERVICE_REACH"
EXCLUSION_REASON_SERVICE_REACH_MARKET_MISMATCH = (
    "SERVICE_REACH_MARKET_MISMATCH"
)


class GeographicFactKind(Enum):
    PROVIDER_LOCATION = "PROVIDER_LOCATION"
    SERVICE_REACH = "SERVICE_REACH"
    REMOTE_CAPABILITY = "REMOTE_CAPABILITY"
    NAMED_AREA = "NAMED_AREA"
    PROVINCE_REACH = "PROVINCE_REACH"
    NATIONAL_REACH = "NATIONAL_REACH"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ServiceReachAdmissionDecision:
    observation_id: str
    provider_location: str | None
    runtime_market: str
    market_scope: str
    service_reach: str | None
    service_reach_status: str
    reach_kind: GeographicFactKind
    remote_capability: bool
    admitted: bool
    exclusion_reason: str | None
    exclusion_detail: str | None


def _fold(value: str | None) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    return " ".join(
        "".join(char for char in normalized if not unicodedata.combining(char))
        .casefold()
        .split()
    )


def _reach_kind(value: str | None) -> GeographicFactKind:
    if not value:
        return GeographicFactKind.UNKNOWN
    if value == "NATIONAL":
        return GeographicFactKind.NATIONAL_REACH
    if value.startswith("PROVINCE:"):
        return GeographicFactKind.PROVINCE_REACH
    if value.startswith("NAMED_AREA:"):
        return GeographicFactKind.NAMED_AREA
    return GeographicFactKind.SERVICE_REACH


def _excluded(
    *,
    observation_id: str,
    provider_location: str | None,
    runtime_market: str,
    market_scope: str,
    service_reach: str | None,
    service_reach_status: str,
    reach_kind: GeographicFactKind,
    remote_capability: bool,
    reason: str,
    detail: str,
) -> ServiceReachAdmissionDecision:
    return ServiceReachAdmissionDecision(
        observation_id=observation_id,
        provider_location=provider_location,
        runtime_market=runtime_market,
        market_scope=market_scope,
        service_reach=service_reach,
        service_reach_status=service_reach_status,
        reach_kind=reach_kind,
        remote_capability=remote_capability,
        admitted=False,
        exclusion_reason=reason,
        exclusion_detail=detail,
    )


def evaluate_service_reach(
    *,
    observation_id: str,
    provider_location: str | None,
    runtime_market: str,
    market_scope: str,
    dimensions: EconomicEvidenceDimensionsV2 | None,
) -> ServiceReachAdmissionDecision:
    """Admit only source-observed reach that exactly supports the runtime market."""
    reach_dimension = dimensions.geographic_reach if dimensions else None
    delivery_dimension = dimensions.delivery_mode if dimensions else None
    reach = reach_dimension.value if reach_dimension else None
    reach_status = (
        reach_dimension.status.value if reach_dimension else DimensionStatus.UNKNOWN.value
    )
    remote_capability = bool(
        delivery_dimension
        and delivery_dimension.is_usable
        and delivery_dimension.value in {"REMOTE", "HYBRID"}
    )
    kind = _reach_kind(reach)

    if reach_dimension is None or reach_dimension.status is DimensionStatus.UNKNOWN:
        detail = (
            "REMOTE_CAPABILITY_WITHOUT_NATIONAL_REACH"
            if market_scope == "REMOTE_NATIONAL_SERVICE" and remote_capability
            else "GEOGRAPHIC_REACH_UNKNOWN"
        )
        return _excluded(
            observation_id=observation_id,
            provider_location=provider_location,
            runtime_market=runtime_market,
            market_scope=market_scope,
            service_reach=reach,
            service_reach_status=reach_status,
            reach_kind=kind,
            remote_capability=remote_capability,
            reason=EXCLUSION_REASON_MISSING_SERVICE_REACH,
            detail=detail,
        )
    if reach_dimension.status is not DimensionStatus.OBSERVED:
        return _excluded(
            observation_id=observation_id,
            provider_location=provider_location,
            runtime_market=runtime_market,
            market_scope=market_scope,
            service_reach=reach,
            service_reach_status=reach_status,
            reach_kind=kind,
            remote_capability=remote_capability,
            reason=EXCLUSION_REASON_MISSING_SERVICE_REACH,
            detail="SERVICE_REACH_NOT_SOURCE_OBSERVED",
        )

    if market_scope == "REMOTE_NATIONAL_SERVICE":
        matches = reach == "NATIONAL"
    elif market_scope == "LOCAL_SERVICE":
        prefix, separator, named_area = (reach or "").partition(":")
        matches = (
            bool(separator)
            and prefix in {"NAMED_AREA", "PROVINCE"}
            and _fold(named_area) == _fold(runtime_market)
        )
    else:
        matches = False

    if not matches:
        return _excluded(
            observation_id=observation_id,
            provider_location=provider_location,
            runtime_market=runtime_market,
            market_scope=market_scope,
            service_reach=reach,
            service_reach_status=reach_status,
            reach_kind=kind,
            remote_capability=remote_capability,
            reason=EXCLUSION_REASON_SERVICE_REACH_MARKET_MISMATCH,
            detail="EXACT_CONSERVATIVE_REACH_MISMATCH",
        )

    return ServiceReachAdmissionDecision(
        observation_id=observation_id,
        provider_location=provider_location,
        runtime_market=runtime_market,
        market_scope=market_scope,
        service_reach=reach,
        service_reach_status=reach_status,
        reach_kind=kind,
        remote_capability=remote_capability,
        admitted=True,
        exclusion_reason=None,
        exclusion_detail=None,
    )
