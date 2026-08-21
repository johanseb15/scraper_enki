from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import re
import unicodedata
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


def _fold(text: str) -> str:
    x = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in x if not unicodedata.combining(ch)).lower()


def _explicit_price_scope(text: str, parsed: ParsedPricingQuery) -> str:
    mapping = {
        PriceType.PER_HOUR: "PER_HOUR",
        PriceType.PER_MONTH: "PER_MONTH",
        PriceType.PER_VISIT: "PER_VISIT",
        PriceType.PER_UNIT: "PER_UNIT",
    }
    if parsed.price.type in mapping:
        return mapping[parsed.price.type]
    x = _fold(text)
    if re.search(r"\bpor\s+hora\b|\bla\s+hora\b", x):
        return "PER_HOUR"
    if re.search(r"\bpor\s+mes\b|\bal\s+mes\b|\bmensual(?:mente)?\b", x):
        return "PER_MONTH"
    if re.search(r"\bpor\s+visita\b|\bcada\s+visita\b", x):
        return "PER_VISIT"
    if re.search(r"\bpor\s+(?:equipo|unidad|pc|notebook)\b", x):
        return "PER_UNIT"
    return "UNKNOWN"


def _commercial_context(text: str) -> str:
    x = _fold(text)
    if re.search(r"\burgenc(?:ia|ias)\b|\bfuera\s+de\s+horario\b|\bfin(?:es)?\s+de\s+semana\b|\bferiado(?:s)?\b", x):
        return "URGENCY"
    return "STANDARD"


def resolver_consulta_pricing(
    texto: str,
    *,
    local_cohortes: Iterable[CohortePricing],
    remote_cohortes: Iterable[CohortePricing],
    language_evidence_type: str = "OBSERVED_USER",
) -> EnkiPricingQueryResult:
    parsed = parse_pricing_query(texto, language_evidence_type=language_evidence_type)

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
    commercial_context = _commercial_context(texto)

    service_cohorts = [
        c for c in cohorts
        if c.market == market
        and c.canonical_service == canonical_service
        and c.commercial_context == commercial_context
    ]
    known_scopes = {c.price_scope for c in service_cohorts if c.price_scope != "UNKNOWN"}
    if price_scope == "UNKNOWN" and known_scopes:
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
