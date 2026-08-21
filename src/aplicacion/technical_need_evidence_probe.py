from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from src.aplicacion.pricing_evidence_engine import CohortePricing, evaluar_precio
from src.aplicacion.technical_need_market_resolution import (
    TechnicalNeedPricingReadiness,
    TechnicalRoutePricingReadiness,
)


@dataclass(frozen=True)
class EvidenceProbeResult:
    route: str
    status: str
    market: str | None = None
    canonical_service: str | None = None
    observations_n: int = 0
    providers_n: int = 0
    evidence_confidence: str = "NONE"
    observed_min: Decimal | None = None
    observed_max: Decimal | None = None
    median: Decimal | None = None
    reason: str | None = None


@dataclass(frozen=True)
class TechnicalNeedEvidenceProbe:
    probes: tuple[EvidenceProbeResult, ...]


def _probe_status(engine_status: str) -> str:
    if engine_status in {"RANGE_READY", "DECISION_READY"}:
        return "EVIDENCE_AVAILABLE"
    if engine_status == "INSUFFICIENT_EVIDENCE":
        return "INSUFFICIENT_EVIDENCE"
    if engine_status == "NO_EVIDENCE":
        return "NO_EVIDENCE"
    return "NO_EVIDENCE"


def probe_pricing_evidence(
    readiness: TechnicalRoutePricingReadiness,
    *,
    local_cohortes: Iterable[CohortePricing],
    remote_cohortes: Iterable[CohortePricing],
) -> EvidenceProbeResult:
    if not readiness.ready:
        return EvidenceProbeResult(
            route=readiness.route,
            status="NOT_PROBED",
            market=readiness.market,
            canonical_service=readiness.canonical_service,
            reason=readiness.status,
        )

    if not readiness.market or not readiness.canonical_service:
        return EvidenceProbeResult(
            route=readiness.route,
            status="NOT_PROBED",
            market=readiness.market,
            canonical_service=readiness.canonical_service,
            reason="INCOMPLETE_PRICING_READINESS",
        )

    cohortes = tuple(remote_cohortes) if readiness.market_scope == "REMOTE_NATIONAL" else tuple(local_cohortes)
    evidence = evaluar_precio(
        cohortes,
        market=readiness.market,
        canonical_service=readiness.canonical_service,
        proposed_price_ars=None,
    )
    return EvidenceProbeResult(
        route=readiness.route,
        status=_probe_status(evidence.status),
        market=evidence.market,
        canonical_service=evidence.canonical_service,
        observations_n=evidence.observations_n,
        providers_n=evidence.providers_n,
        evidence_confidence=evidence.evidence_confidence,
        observed_min=evidence.min_ars,
        observed_max=evidence.max_ars,
        median=evidence.median_ars,
        reason=evidence.status,
    )


def probe_technical_need_evidence(
    pricing_readiness: TechnicalNeedPricingReadiness | None,
    *,
    local_cohortes: Iterable[CohortePricing],
    remote_cohortes: Iterable[CohortePricing],
) -> TechnicalNeedEvidenceProbe | None:
    if pricing_readiness is None:
        return None
    return TechnicalNeedEvidenceProbe(
        probes=tuple(
            probe_pricing_evidence(
                route_readiness,
                local_cohortes=local_cohortes,
                remote_cohortes=remote_cohortes,
            )
            for route_readiness in pricing_readiness.routes
        )
    )
