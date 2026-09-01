export type DecisionIntent = "sending_quote" | "received_quote";

export type InterpretationAttribute = {
  label: string;
};

export type QuoteInterpretationView = {
  priceLabel: string;
  understood: InterpretationAttribute[];
  missing: InterpretationAttribute[];
};

export type DecisionReadoutState =
  | "potentially_comparable"
  | "not_comparable"
  | "indeterminate";

export type DecisionDimension = {
  label: string;
};

export type DecisionReadoutView = {
  state: DecisionReadoutState;
  priceLabel: string;
  summary: string;
  known: DecisionDimension[];
  missing: DecisionDimension[];
  nextAction: string;
};

export type DecisionPricingPrice = {
  type: string;
  value: number | null;
  min: number | null;
  max: number | null;
  currency: string;
  is_approximate: boolean;
};

export type DecisionPricingGeography = {
  province: string | null;
  city: string | null;
};

export type CommercialContextContract = {
  value: string;
  status: string;
  origin: string;
  raw_basis: string[];
  resolution_method: string;
};

export type TechnicalNeedContract = {
  domain: string;
  technical_problem: string;
  economic_intent_explicit: boolean;
  candidate_routes: string[];
  product_purchase_recommendation: string;
  clarification_required: boolean;
};

export type UserQueryMonetaryComponentContract = {
  role: string;
  value: number;
  currency: string;
  origin: string;
  raw_expression: string | null;
  derivation_method: string | null;
  derived_from: string[];
};

export type DecisionPricingParsed = {
  query_kind: string;
  intent_action: string;
  intent_side: string;
  economic_object_kind: string;
  canonical_services: string[];
  market_scope: string;
  modality: string;
  price: DecisionPricingPrice;
  geography: DecisionPricingGeography;
  device_type: string | null;
  condition: string;
  is_bundle: boolean;
  parts_scope: string;
  commercial_context: CommercialContextContract;
  clarification_required: boolean;
  clarification_reason: string | null;
  clarification_question: string | null;
  technical_need: TechnicalNeedContract | null;
  monetary_components: UserQueryMonetaryComponentContract[];
};

export type MarketResolutionItem = {
  route: string;
  status: string;
  canonical_service: string | null;
  economic_object_kind: string | null;
  market_scope: string | null;
  market: string | null;
  market_key: string | null;
  market_status: string | null;
  resolution_reason: string | null;
};

export type MarketResolutionContract = {
  clarification_required: boolean;
  clarification_reason: string | null;
  clarification_question: string | null;
  resolutions: MarketResolutionItem[];
};

export type PricingReadinessItem = {
  route: string;
  status: string;
  ready: boolean;
  canonical_service: string | null;
  market_scope: string | null;
  market: string | null;
  market_key: string | null;
  reason: string | null;
  pricing_status: string | null;
};

export type PricingReadinessContract = {
  routes: PricingReadinessItem[];
  ready_routes: PricingReadinessItem[];
  blocked_routes: PricingReadinessItem[];
};

export type EvidenceProbeItem = {
  route: string;
  status: string;
  market: string | null;
  canonical_service: string | null;
  observations_n: number;
  providers_n: number;
  source_count: number;
  evidence_confidence: string;
  observed_min: number | null;
  observed_max: number | null;
  median: number | null;
  reason: string | null;
};

export type EvidenceProbeContract = {
  probes: EvidenceProbeItem[];
};

export type DecisionPricingEvidence = {
  market: string;
  canonical_service: string;
  observations_n: number;
  providers_n: number;
  source_count: number;
  provider_independence_version: string | null;
  min_ars: number | null;
  q1_ars: number | null;
  median_ars: number | null;
  q3_ars: number | null;
  max_ars: number | null;
  evidence_confidence: string;
  price_position: string | null;
  decision_label: string | null;
  price_scope: string;
  commercial_context: string;
  commercial_context_provenance: CommercialContextContract;
  evidence_commercial_context: CommercialContextContract | null;
  lineage_gate_version: string | null;
  service_reach_gate_version: string | null;
  temporal_gate_version: string | null;
  temporal_state: string | null;
  acquired_at_min: string | null;
  acquired_at_max: string | null;
  freshness_policy_version: string | null;
  observation_ids: string[];
};

export type DecisionPricingResponse = {
  status: string;
  headline: string;
  summary: string;
  evidence_line: string | null;
  caveat: string | null;
  clarification_reason: string | null;
  clarification_question: string | null;
  unsupported_reason: string | null;
  market_resolution: MarketResolutionContract | null;
  pricing_readiness: PricingReadinessContract | null;
  evidence_probe: EvidenceProbeContract | null;
  parsed: DecisionPricingParsed;
  evidence: DecisionPricingEvidence | null;
};
