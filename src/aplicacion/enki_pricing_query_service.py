from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import re
from typing import Iterable

from src.aplicacion.language_query_contract import (
    EconomicObjectKind,
    IntentAction,
    MarketScope,
    ParsedPricingQuery,
    QueryKind,
    PriceType,
)
from src.aplicacion.parser_consulta_pricing import parse_pricing_query
from src.aplicacion.pricing_evidence_engine import (
    CohortePricing,
    ResultadoEvidenciaPrecio,
    evaluar_precio,
)
from src.aplicacion.technical_need_evidence_probe import (
    TechnicalNeedEvidenceProbe,
    probe_technical_need_evidence,
)
from src.aplicacion.technical_need_market_resolution import (
    TechnicalNeedMarketResolution,
    TechnicalNeedPricingReadiness,
    evaluate_technical_need_pricing_readiness,
    resolve_technical_need_market,
)
from src.dominio.commercial_context import (
    CommercialContextCompatibility,
    compare_commercial_contexts,
)
from src.dominio.price_scope_contract import normalize_price_scope


@dataclass(frozen=True)
class EnkiPricingQueryResult:
    status: str
    parsed: ParsedPricingQuery
    evidence: ResultadoEvidenciaPrecio | None = None
    clarification_reason: str | None = None
    clarification_question: str | None = None
    unsupported_reason: str | None = None
    market_resolution: TechnicalNeedMarketResolution | None = None
    pricing_readiness: TechnicalNeedPricingReadiness | None = None
    evidence_probe: TechnicalNeedEvidenceProbe | None = None

    @property
    def decision_label(self) -> str | None:
        return self.evidence.decision_label if self.evidence else None


def _clarification(parsed: ParsedPricingQuery, *, reason: str | None = None, question: str | None = None) -> EnkiPricingQueryResult:
    return EnkiPricingQueryResult(
        status="CLARIFICATION_REQUIRED",
        parsed=parsed,
        clarification_reason=reason or parsed.metadata.clarification_reason,
        clarification_question=question or parsed.metadata.clarification_question,
    )


def _unsupported(parsed: ParsedPricingQuery, reason: str) -> EnkiPricingQueryResult:
    return EnkiPricingQueryResult(status="UNSUPPORTED_QUERY", parsed=parsed, unsupported_reason=reason)


def _has_explicit_unsupported_currency(text: str, parsed: ParsedPricingQuery) -> bool:
    if parsed.price.currency not in {"ARS", "UNKNOWN"}:
        return True
    if parsed.price.currency != "UNKNOWN" or parsed.price.value is None:
        return False
    return bool(re.search(r"\b(?:usdt|usdc|btc|eth)\b", text.casefold()))


def _has_terminal_bundle_fact(parsed: ParsedPricingQuery) -> bool:
    reason = parsed.metadata.clarification_reason or ""
    return (
        parsed.is_bundle
        and parsed.economic_object_kind == EconomicObjectKind.BUNDLE
        and "BUNDLE_REQUIRES_COMPARABLE_SCOPE" in reason.split("|")
    )


def _explicit_price_scope(text: str, parsed: ParsedPricingQuery) -> str:
    if parsed.price_scope.comparison_scope != "UNKNOWN":
        return parsed.price_scope.comparison_scope
    mapping = {
        PriceType.PER_HOUR: "PER_HOUR",
        PriceType.PER_MONTH: "PER_MONTH",
        PriceType.PER_VISIT: "PER_VISIT",
        PriceType.PER_UNIT: "PER_UNIT",
    }
    if parsed.price.type in mapping:
        return mapping[parsed.price.type]
    return normalize_price_scope(
        text,
        has_price=parsed.price.value is not None,
        is_range=parsed.price.min is not None and parsed.price.max is not None,
    ).comparison_scope


def resolver_consulta_pricing(
    texto: str,
    *,
    local_cohortes: Iterable[CohortePricing],
    remote_cohortes: Iterable[CohortePricing],
    language_evidence_type: str = "OBSERVED_USER",
    parsed_query: ParsedPricingQuery | None = None,
) -> EnkiPricingQueryResult:
    parsed = parsed_query or parse_pricing_query(texto, language_evidence_type=language_evidence_type)

    if parsed.query_kind == QueryKind.TECHNICAL_NEED:
        market_resolution = resolve_technical_need_market(
            parsed.technical_need,
            geography=parsed.geography,
        )
        pricing_readiness = evaluate_technical_need_pricing_readiness(market_resolution)
        evidence_probe = probe_technical_need_evidence(
            pricing_readiness,
            local_cohortes=local_cohortes,
            remote_cohortes=remote_cohortes,
        )
        return EnkiPricingQueryResult(
            status="TECHNICAL_NEED_ROUTED",
            parsed=parsed,
            clarification_reason=market_resolution.clarification_reason or parsed.metadata.clarification_reason,
            clarification_question=market_resolution.clarification_question or parsed.metadata.clarification_question,
            market_resolution=market_resolution,
            pricing_readiness=pricing_readiness,
            evidence_probe=evidence_probe,
        )

    # Terminal facts already positively known outrank clarification.
    if _has_terminal_bundle_fact(parsed):
        return _unsupported(parsed, "SINGLE_CANONICAL_SERVICE_REQUIRED")

    if (
        parsed.intent_action == IntentAction.EVALUATE_PRICE
        and _has_explicit_unsupported_currency(texto, parsed)
    ):
        return _unsupported(parsed, "ARS_ONLY_V1")

    if parsed.metadata.clarification_required:
        return _clarification(parsed)

    if parsed.is_bundle or len(parsed.canonical_services) != 1:
        return _unsupported(parsed, "SINGLE_CANONICAL_SERVICE_REQUIRED")

    if parsed.economic_object_kind != EconomicObjectKind.SERVICE:
        return _unsupported(parsed, "SERVICE_ONLY_V1")

    canonical_service = parsed.canonical_services[0]

    if parsed.market_scope == MarketScope.LOCAL:
        if not parsed.geography.province:
            return _clarification(parsed)
        market = parsed.geography.province
        cohorts = tuple(local_cohortes)
    elif parsed.market_scope == MarketScope.REMOTE_NATIONAL:
        market = "AR"
        cohorts = tuple(remote_cohortes)
    else:
        return _unsupported(parsed, "UNSUPPORTED_MARKET_SCOPE")

    price_scope = _explicit_price_scope(texto, parsed)
    commercial_context = parsed.commercial_context

    service_cohorts = [
        c for c in cohorts
        if c.market == market
        and c.canonical_service == canonical_service
        and compare_commercial_contexts(c.commercial_context, commercial_context)
        is CommercialContextCompatibility.COMPATIBLE
    ]
    if price_scope == "UNKNOWN" and service_cohorts:
        return _clarification(
            parsed,
            reason="PRICE_SCOPE_REQUIRED",
            question="¿Ese precio corresponde a una hora, una visita, un abono mensual u otra unidad de cobro?",
        )

    proposed_price: Decimal | None = None

    if parsed.intent_action == IntentAction.EVALUATE_PRICE:
        if parsed.price.currency != "ARS":
            return _unsupported(parsed, "ARS_ONLY_V1")
        if parsed.price.value is None:
            return _unsupported(parsed, "EXACT_PRICE_REQUIRED_FOR_EVALUATION")
        if parsed.price.type not in {PriceType.EXACT, PriceType.PER_HOUR, PriceType.PER_MONTH, PriceType.PER_VISIT, PriceType.PER_UNIT}:
            return _unsupported(parsed, "EXACT_PRICE_REQUIRED_FOR_EVALUATION")
        proposed_price = Decimal(str(parsed.price.value))
    elif parsed.intent_action in {IntentAction.SUGGEST_PRICE, IntentAction.MARKET_REFERENCE}:
        proposed_price = None
    else:
        return _unsupported(parsed, "UNSUPPORTED_INTENT")

    evidence = evaluar_precio(
        cohorts,
        market=market,
        canonical_service=canonical_service,
        price_scope=price_scope,
        commercial_context=commercial_context,
        proposed_price_ars=proposed_price,
    )
    return EnkiPricingQueryResult(status=evidence.status, parsed=parsed, evidence=evidence)
