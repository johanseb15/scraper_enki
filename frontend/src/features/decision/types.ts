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

export type DecisionPricingParsed = {
  intent_action: string;
  intent_side: string;
  economic_object_kind: string;
  canonical_services: string[];
  market_scope: string;
  modality: string;
  price: DecisionPricingPrice;
  geography: {
    province: string | null;
    city: string | null;
  };
  device_type: string | null;
  condition: string;
  is_bundle: boolean;
  parts_scope: string;
  clarification_required: boolean;
  clarification_reason: string | null;
  clarification_question: string | null;
};

export type DecisionPricingEvidence = {
  market: string;
  canonical_service: string;
  observations_n: number;
  lineage_gate_version?: string | null;
  observation_ids?: string[];
  providers_n: number;
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
  parsed: DecisionPricingParsed;
  evidence: DecisionPricingEvidence | null;
};
