from __future__ import annotations

from dataclasses import dataclass

from src.aplicacion.language_query_contract import Geography, TechnicalNeed


KNOWN_CANONICAL_SERVICES = frozenset({
    "FORMATEO_INSTALACION_SO",
    "DIAGNOSTICO_REVISION",
    "SOPORTE_REMOTO",
})

ROUTE_TO_CANONICAL_SERVICE = {
    "OS_INSTALLATION_SERVICE": "FORMATEO_INSTALACION_SO",
    "DIAGNOSTIC_SERVICE": "DIAGNOSTICO_REVISION",
}

LOCAL_SERVICE_ROUTES = frozenset({
    "OS_INSTALLATION_SERVICE",
    "DIAGNOSTIC_SERVICE",
})

UNRESOLVED_REASONS = {
    "HARDWARE_DIAGNOSTIC": (
        "Hardware diagnostic is a plausible route, but it is not equivalent to "
        "a repair, replacement, product purchase, or known comparable service v1."
    ),
}


@dataclass(frozen=True)
class TechnicalRouteMarketResolution:
    route: str
    status: str
    canonical_service: str | None = None
    economic_object_kind: str | None = None
    market_scope: str | None = None
    market: str | None = None
    market_key: str | None = None
    market_status: str = "UNRESOLVED"
    resolution_reason: str | None = None


@dataclass(frozen=True)
class TechnicalNeedMarketResolution:
    resolutions: tuple[TechnicalRouteMarketResolution, ...]
    clarification_required: bool = False
    clarification_reason: str | None = None
    clarification_question: str | None = None



@dataclass(frozen=True)
class TechnicalRoutePricingReadiness:
    route: str
    status: str
    ready: bool
    canonical_service: str | None = None
    market_scope: str | None = None
    market: str | None = None
    market_key: str | None = None
    reason: str | None = None
    pricing_status: str | None = None


@dataclass(frozen=True)
class TechnicalNeedPricingReadiness:
    routes: tuple[TechnicalRoutePricingReadiness, ...]
    ready_routes: tuple[TechnicalRoutePricingReadiness, ...]
    blocked_routes: tuple[TechnicalRoutePricingReadiness, ...]


def evaluate_pricing_readiness(
    resolution: TechnicalRouteMarketResolution,
) -> TechnicalRoutePricingReadiness:
    if resolution.status != "RESOLVED":
        return TechnicalRoutePricingReadiness(
            route=resolution.route,
            status="UNRESOLVED_ROUTE",
            ready=False,
            reason=resolution.resolution_reason,
        )

    if not resolution.canonical_service:
        return TechnicalRoutePricingReadiness(
            route=resolution.route,
            status="UNRESOLVED_ROUTE",
            ready=False,
            reason="Resolved route is missing canonical service.",
        )

    if resolution.market_scope == "LOCAL":
        if not resolution.market:
            return TechnicalRoutePricingReadiness(
                route=resolution.route,
                status="MISSING_PROVINCE",
                ready=False,
                canonical_service=resolution.canonical_service,
                market_scope=resolution.market_scope,
                reason="Local pricing evidence requires province.",
            )
        return TechnicalRoutePricingReadiness(
            route=resolution.route,
            status="READY_FOR_PRICING",
            ready=True,
            canonical_service=resolution.canonical_service,
            market_scope=resolution.market_scope,
            market=resolution.market,
            market_key=resolution.market_key,
            reason="Canonical service and local market are complete for a pricing lookup.",
        )

    if resolution.market_scope == "REMOTE_NATIONAL":
        if resolution.market != "AR":
            return TechnicalRoutePricingReadiness(
                route=resolution.route,
                status="INSUFFICIENT_MARKET_CONTEXT",
                ready=False,
                canonical_service=resolution.canonical_service,
                market_scope=resolution.market_scope,
                reason="Remote national pricing requires explicit AR market.",
            )
        return TechnicalRoutePricingReadiness(
            route=resolution.route,
            status="READY_FOR_PRICING",
            ready=True,
            canonical_service=resolution.canonical_service,
            market_scope=resolution.market_scope,
            market=resolution.market,
            market_key=resolution.market_key,
            reason="Canonical service and remote national market are complete for a pricing lookup.",
        )

    return TechnicalRoutePricingReadiness(
        route=resolution.route,
        status="INSUFFICIENT_MARKET_CONTEXT",
        ready=False,
        canonical_service=resolution.canonical_service,
        market_scope=resolution.market_scope,
        reason="Unsupported or incomplete market scope for pricing lookup.",
    )


def evaluate_technical_need_pricing_readiness(
    market_resolution: TechnicalNeedMarketResolution | None,
) -> TechnicalNeedPricingReadiness | None:
    if market_resolution is None:
        return None
    routes = tuple(evaluate_pricing_readiness(r) for r in market_resolution.resolutions)
    return TechnicalNeedPricingReadiness(
        routes=routes,
        ready_routes=tuple(r for r in routes if r.ready),
        blocked_routes=tuple(r for r in routes if not r.ready),
    )

def resolve_technical_route(
    route: str,
    *,
    geography: Geography | None = None,
) -> TechnicalRouteMarketResolution:
    canonical_service = ROUTE_TO_CANONICAL_SERVICE.get(route)
    if canonical_service is None or canonical_service not in KNOWN_CANONICAL_SERVICES:
        return TechnicalRouteMarketResolution(
            route=route,
            status="UNRESOLVED",
            resolution_reason=UNRESOLVED_REASONS.get(
                route,
                "No safe canonical economic object exists for this technical route v1.",
            ),
        )

    if route in LOCAL_SERVICE_ROUTES:
        province = geography.province if geography else None
        if not province:
            return TechnicalRouteMarketResolution(
                route=route,
                status="RESOLVED",
                canonical_service=canonical_service,
                economic_object_kind="SERVICE",
                market_scope="LOCAL",
                market_status="MISSING_PROVINCE",
                resolution_reason="Route maps to a known local canonical service, but market requires province.",
            )
        return TechnicalRouteMarketResolution(
            route=route,
            status="RESOLVED",
            canonical_service=canonical_service,
            economic_object_kind="SERVICE",
            market_scope="LOCAL",
            market=province,
            market_key=f"{province}::{canonical_service}",
            market_status="READY",
            resolution_reason="Route maps to a known local canonical service.",
        )

    return TechnicalRouteMarketResolution(
        route=route,
        status="UNRESOLVED",
        resolution_reason="Route has no supported market scope v1.",
    )


def resolve_technical_need_market(
    technical_need: TechnicalNeed | None,
    *,
    geography: Geography | None = None,
) -> TechnicalNeedMarketResolution:
    if technical_need is None:
        return TechnicalNeedMarketResolution(resolutions=())

    resolutions = tuple(
        resolve_technical_route(route, geography=geography)
        for route in technical_need.candidate_routes
    )
    missing_local_market = any(
        r.status == "RESOLVED"
        and r.market_scope == "LOCAL"
        and r.market_status == "MISSING_PROVINCE"
        for r in resolutions
    )
    return TechnicalNeedMarketResolution(
        resolutions=resolutions,
        clarification_required=missing_local_market,
        clarification_reason="MISSING_PROVINCE_FOR_LOCAL_MARKET" if missing_local_market else None,
        clarification_question=(
            "¿En qué provincia se realizaría el servicio técnico?"
            if missing_local_market else None
        ),
    )
