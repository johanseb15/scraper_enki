import type { DecisionPricingResponse } from "@/features/decision/types";

export type DecisionPresentationState =
  | "CLARIFICATION_REQUIRED"
  | "NO_EVIDENCE"
  | "INSUFFICIENT_EVIDENCE"
  | "UNSUPPORTED_QUERY"
  | "RANGE_READY"
  | "DECISION_READY";

export type EconomicDecisionLabel = "BAJO" | "RAZONABLE" | "ALTO";

export type AcceptedDecisionPresentation = {
  kind: "accepted";
  state: DecisionPresentationState;
  response: DecisionPricingResponse;
  conclusion: string;
  decisionLabel: EconomicDecisionLabel | null;
  benchmarkAllowed: boolean;
  readoutAllowed: boolean;
};

export type DecisionPresentation =
  | AcceptedDecisionPresentation
  | { kind: "abstention"; conclusion: string };

const abstention = {
  kind: "abstention",
  conclusion: "No puedo interpretar este resultado con seguridad.",
} as const;

const states = new Set<DecisionPresentationState>([
  "CLARIFICATION_REQUIRED",
  "NO_EVIDENCE",
  "INSUFFICIENT_EVIDENCE",
  "UNSUPPORTED_QUERY",
  "RANGE_READY",
  "DECISION_READY",
]);
const labels = new Set<EconomicDecisionLabel>(["BAJO", "RAZONABLE", "ALTO"]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isNullableString(value: unknown): value is string | null {
  return value === null || typeof value === "string";
}

function isNullableNumber(value: unknown): value is number | null {
  return value === null || (typeof value === "number" && Number.isFinite(value));
}

function hasPresentationShape(value: Record<string, unknown>): boolean {
  const parsed = value.parsed;
  if (!isRecord(parsed) || !Array.isArray(parsed.canonical_services)) return false;
  if (!parsed.canonical_services.every((item) => typeof item === "string")) return false;
  if (!isRecord(parsed.price) || !isRecord(parsed.geography)) return false;
  const price = parsed.price;
  const geography = parsed.geography;
  if (
    typeof price.type !== "string" ||
    !isNullableNumber(price.value) ||
    !isNullableNumber(price.min) ||
    !isNullableNumber(price.max) ||
    typeof price.currency !== "string" ||
    typeof price.is_approximate !== "boolean" ||
    !isNullableString(geography.city) ||
    !isNullableString(geography.province) ||
    !isNullableString(parsed.modality) ||
    !isNullableString(parsed.parts_scope) ||
    typeof parsed.clarification_required !== "boolean" ||
    !isNullableString(parsed.clarification_question) ||
    !isNullableString(value.summary) ||
    !isNullableString(value.evidence_line) ||
    !isNullableString(value.caveat) ||
    !isNullableString(value.unsupported_reason) ||
    !isNullableString(value.clarification_question)
  ) return false;

  if (value.evidence === null) return true;
  const evidence = value.evidence;
  if (!isRecord(evidence)) return false;
  return (
    typeof evidence.market === "string" &&
    typeof evidence.canonical_service === "string" &&
    typeof evidence.observations_n === "number" &&
    Number.isFinite(evidence.observations_n) &&
    typeof evidence.providers_n === "number" &&
    Number.isFinite(evidence.providers_n) &&
    typeof evidence.source_count === "number" &&
    Number.isFinite(evidence.source_count) &&
    ["min_ars", "q1_ars", "median_ars", "q3_ars", "max_ars"].every((key) =>
      isNullableNumber(evidence[key]),
    ) &&
    typeof evidence.evidence_confidence === "string" &&
    isNullableString(evidence.price_position) &&
    isNullableString(evidence.decision_label) &&
    typeof evidence.price_scope === "string" &&
    isNullableString(evidence.temporal_state) &&
    Array.isArray(evidence.observation_ids) &&
    evidence.observation_ids.every((item) => typeof item === "string")
  );
}

export function resolveDecisionPresentation(payload: unknown): DecisionPresentation {
  if (!isRecord(payload) || typeof payload.status !== "string" || !states.has(payload.status as DecisionPresentationState)) {
    return abstention;
  }
  if (!hasPresentationShape(payload)) return abstention;

  const state = payload.status as DecisionPresentationState;
  const evidence = payload.evidence as Record<string, unknown> | null;
  const rawLabel = evidence?.decision_label ?? null;
  const decisionLabel = labels.has(rawLabel as EconomicDecisionLabel)
    ? (rawLabel as EconomicDecisionLabel)
    : null;

  if (state === "RANGE_READY" && (evidence === null || rawLabel !== null)) return abstention;
  if (state === "DECISION_READY" && (!evidence || !labels.has(rawLabel as EconomicDecisionLabel))) return abstention;
  if (state !== "DECISION_READY" && rawLabel !== null) return abstention;
  if (state === "CLARIFICATION_REQUIRED" && evidence !== null) return abstention;
  if ((state === "NO_EVIDENCE" || state === "UNSUPPORTED_QUERY") && evidence !== null) return abstention;

  const conclusion = payload.summary;
  if (typeof conclusion !== "string" || !conclusion.trim()) return abstention;
  if (decisionLabel && conclusion.trim().toUpperCase() === decisionLabel) return abstention;
  if (state === "CLARIFICATION_REQUIRED" && parsedClarification(payload) !== true) return abstention;
  if (state !== "CLARIFICATION_REQUIRED" && parsedClarification(payload) !== false) return abstention;
  if (state !== "DECISION_READY") {
    const visibleCopy = [payload.summary, payload.evidence_line, payload.caveat]
      .filter((value): value is string => typeof value === "string")
      .join(" ");
    const copyWithoutExplicitDenial = visibleCopy.replace(
      /\bno\s+para\s+emitir\s+BAJO\/RAZONABLE\/ALTO\b/i,
      "",
    );
    if (/\b(BAJO|RAZONABLE|ALTO)\b/i.test(copyWithoutExplicitDenial)) return abstention;
  }

  // The object crosses into the UI only after every field used by the flow has been checked.
  return {
    kind: "accepted",
    state,
    response: payload as unknown as DecisionPricingResponse,
    conclusion,
    decisionLabel,
    benchmarkAllowed: state === "RANGE_READY" || state === "DECISION_READY",
    readoutAllowed: state !== "CLARIFICATION_REQUIRED",
  };
}

function parsedClarification(payload: Record<string, unknown>) {
  return (payload.parsed as Record<string, unknown>).clarification_required;
}
