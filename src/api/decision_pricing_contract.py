from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class _StrictContractModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )


class DecisionPricingPriceResponse(
    _StrictContractModel
):
    type: str
    value: int | float | None
    min: int | float | None
    max: int | float | None
    currency: str
    is_approximate: bool


class DecisionPricingGeographyResponse(
    _StrictContractModel
):
    province: str | None
    city: str | None


class CommercialContextResponse(
    _StrictContractModel
):
    value: str
    status: str
    origin: str
    raw_basis: list[str]
    resolution_method: str


class TechnicalNeedResponse(
    _StrictContractModel
):
    domain: str
    technical_problem: str
    economic_intent_explicit: bool
    candidate_routes: list[str]
    product_purchase_recommendation: str
    clarification_required: bool


class DecisionPricingParsedResponse(
    _StrictContractModel
):
    query_kind: str
    intent_action: str
    intent_side: str
    economic_object_kind: str
    canonical_services: list[str]
    market_scope: str
    modality: str
    price: DecisionPricingPriceResponse
    geography: DecisionPricingGeographyResponse
    device_type: str | None
    condition: str
    is_bundle: bool
    parts_scope: str
    commercial_context: CommercialContextResponse
    clarification_required: bool
    clarification_reason: str | None
    clarification_question: str | None
    technical_need: TechnicalNeedResponse | None


class MarketResolutionItemResponse(
    _StrictContractModel
):
    route: str
    status: str
    canonical_service: str | None
    economic_object_kind: str | None
    market_scope: str | None
    market: str | None
    market_key: str | None
    market_status: str | None
    resolution_reason: str | None


class MarketResolutionResponse(
    _StrictContractModel
):
    clarification_required: bool
    clarification_reason: str | None
    clarification_question: str | None
    resolutions: list[MarketResolutionItemResponse]


class PricingReadinessItemResponse(
    _StrictContractModel
):
    route: str
    status: str
    ready: bool
    canonical_service: str | None
    market_scope: str | None
    market: str | None
    market_key: str | None
    reason: str | None
    pricing_status: str | None


class PricingReadinessResponse(
    _StrictContractModel
):
    routes: list[PricingReadinessItemResponse]
    ready_routes: list[PricingReadinessItemResponse]
    blocked_routes: list[PricingReadinessItemResponse]


class EvidenceProbeItemResponse(
    _StrictContractModel
):
    route: str
    status: str
    market: str | None
    canonical_service: str | None
    observations_n: int
    providers_n: int
    source_count: int
    evidence_confidence: str
    observed_min: int | float | None
    observed_max: int | float | None
    median: int | float | None
    reason: str | None


class EvidenceProbeResponse(
    _StrictContractModel
):
    probes: list[EvidenceProbeItemResponse]


class DecisionPricingEvidenceResponse(
    _StrictContractModel
):
    market: str
    canonical_service: str
    observations_n: int
    providers_n: int
    source_count: int
    provider_independence_version: str | None
    min_ars: int | float | None
    q1_ars: int | float | None
    median_ars: int | float | None
    q3_ars: int | float | None
    max_ars: int | float | None
    evidence_confidence: str
    price_position: str | None
    decision_label: str | None
    price_scope: str
    commercial_context: str
    commercial_context_provenance: CommercialContextResponse
    evidence_commercial_context: CommercialContextResponse | None
    lineage_gate_version: str | None
    service_reach_gate_version: str | None
    temporal_gate_version: str | None
    temporal_state: str | None
    acquired_at_min: str | None
    acquired_at_max: str | None
    freshness_policy_version: str | None
    observation_ids: list[str]


class DecisionPricingResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    status: str
    headline: str
    summary: str
    evidence_line: str | None
    caveat: str | None
    clarification_reason: str | None
    clarification_question: str | None
    unsupported_reason: str | None

    market_resolution: MarketResolutionResponse | None
    pricing_readiness: PricingReadinessResponse | None
    evidence_probe: EvidenceProbeResponse | None

    parsed: DecisionPricingParsedResponse
    evidence: DecisionPricingEvidenceResponse | None
