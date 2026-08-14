from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from src.aplicacion.language_query_contract import (
    EconomicObjectKind,
    IntentAction,
    MarketScope,
    ParsedPricingQuery,
    PriceType,
)
from src.aplicacion.parser_consulta_pricing import parse_pricing_query
from src.aplicacion.pricing_evidence_engine import (
    CohortePricing,
    ResultadoEvidenciaPrecio,
    evaluar_precio,
)


@dataclass(frozen=True)
class EnkiPricingQueryResult:
    status: str
    parsed: ParsedPricingQuery
    evidence: ResultadoEvidenciaPrecio | None = None
    clarification_reason: str | None = None
    clarification_question: str | None = None
    unsupported_reason: str | None = None

    @property
    def decision_label(self) -> str | None:
        return self.evidence.decision_label if self.evidence else None


def _clarification(parsed: ParsedPricingQuery) -> EnkiPricingQueryResult:
    return EnkiPricingQueryResult(
        status="CLARIFICATION_REQUIRED",
        parsed=parsed,
        clarification_reason=parsed.metadata.clarification_reason,
        clarification_question=parsed.metadata.clarification_question,
    )


def _unsupported(
    parsed: ParsedPricingQuery,
    reason: str,
) -> EnkiPricingQueryResult:
    return EnkiPricingQueryResult(
        status="UNSUPPORTED_QUERY",
        parsed=parsed,
        unsupported_reason=reason,
    )


def resolver_consulta_pricing(
    texto: str,
    *,
    local_cohortes: Iterable[CohortePricing],
    remote_cohortes: Iterable[CohortePricing],
    language_evidence_type: str = "OBSERVED_USER",
) -> EnkiPricingQueryResult:
    """Resolve one human pricing query against empirical Enki cohorts.

    v1 is deliberately narrow:
    - service pricing only
    - one canonical service only
    - ARS only
    - exact scalar price for EVALUATE_PRICE
    - local requires province
    - remote uses national AR cohort

    The function never upgrades evidence confidence. All BAJO/RAZONABLE/ALTO
    authority remains inside pricing_evidence_engine.evaluar_precio().
    """
    parsed = parse_pricing_query(
        texto,
        language_evidence_type=language_evidence_type,
    )

    if parsed.metadata.clarification_required:
        return _clarification(parsed)

    # Important ordering: a bundle is semantically understood, but v1 refuses
    # to allocate one quoted price across multiple atomic services. Report that
    # precise reason before the generic non-service guard.
    if parsed.is_bundle or len(parsed.canonical_services) != 1:
        return _unsupported(parsed, "SINGLE_CANONICAL_SERVICE_REQUIRED")

    if parsed.economic_object_kind != EconomicObjectKind.SERVICE:
        return _unsupported(parsed, "SERVICE_ONLY_V1")

    canonical_service = parsed.canonical_services[0]

    if parsed.market_scope == MarketScope.LOCAL:
        if not parsed.geography.province:
            return _clarification(parsed)
        market = parsed.geography.province
        cohorts = local_cohortes
    elif parsed.market_scope == MarketScope.REMOTE_NATIONAL:
        market = "AR"
        cohorts = remote_cohortes
    else:
        return _unsupported(parsed, "UNSUPPORTED_MARKET_SCOPE")

    proposed_price: Decimal | None = None

    if parsed.intent_action == IntentAction.EVALUATE_PRICE:
        if parsed.price.currency != "ARS":
            return _unsupported(parsed, "ARS_ONLY_V1")
        if parsed.price.type != PriceType.EXACT or parsed.price.value is None:
            return _unsupported(parsed, "EXACT_PRICE_REQUIRED_FOR_EVALUATION")
        proposed_price = Decimal(str(parsed.price.value))

    elif parsed.intent_action in {
        IntentAction.SUGGEST_PRICE,
        IntentAction.MARKET_REFERENCE,
    }:
        proposed_price = None

    else:
        return _unsupported(parsed, "UNSUPPORTED_INTENT")

    evidence = evaluar_precio(
        cohorts,
        market=market,
        canonical_service=canonical_service,
        proposed_price_ars=proposed_price,
    )

    return EnkiPricingQueryResult(
        status=evidence.status,
        parsed=parsed,
        evidence=evidence,
    )
