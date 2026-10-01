import { describe, expect, it } from "vitest";
import { resolveDecisionPresentation } from "@/features/decision/decision-presentation-contract";

const payload = (status: string, decisionLabel: unknown = null) => ({
  status,
  headline: "Rango observado",
  summary: status === "RANGE_READY"
    ? "Hay evidencia suficiente para mostrar un rango empírico, pero no para emitir BAJO/RAZONABLE/ALTO."
    : "El resultado describe la evidencia observada.",
  evidence_line: null,
  caveat: null,
  clarification_reason: null,
  clarification_question: null,
  unsupported_reason: null,
  market_resolution: null,
  pricing_readiness: null,
  evidence_probe: null,
  parsed: {
    canonical_services: [],
    price: {
      type: "EXACT",
      value: 1000,
      min: null,
      max: null,
      currency: "ARS",
      is_approximate: false,
    },
    geography: { province: null, city: null },
    modality: "UNKNOWN",
    parts_scope: "UNKNOWN",
    clarification_required: false,
    clarification_question: null,
  },
  evidence: {
    market: "AR",
    canonical_service: "SOPORTE",
    observations_n: 3,
    providers_n: 3,
    source_count: 3,
    min_ars: 800,
    q1_ars: 900,
    median_ars: 1000,
    q3_ars: 1100,
    max_ars: 1200,
    evidence_confidence: "LOW",
    price_position: null,
    decision_label: decisionLabel,
    price_scope: "TOTAL",
    temporal_state: null,
    observation_ids: [],
  },
});

describe("resolveDecisionPresentation", () => {
  it("accepts RANGE_READY without an economic classification", () => {
    const result = resolveDecisionPresentation(payload("RANGE_READY"));

    expect(result.kind).toBe("accepted");
    if (result.kind === "accepted") {
      expect(result.state).toBe("RANGE_READY");
      expect(result.decisionLabel).toBeNull();
    }
  });

  it("accepts DECISION_READY with exactly one supported classification", () => {
    const result = resolveDecisionPresentation(payload("DECISION_READY", "ALTO"));

    expect(result.kind).toBe("accepted");
    if (result.kind === "accepted") {
      expect(result.state).toBe("DECISION_READY");
      expect(result.decisionLabel).toBe("ALTO");
    }
  });

  it("allows negated classification wording in a RANGE_READY explanation", () => {
    const result = resolveDecisionPresentation(payload("RANGE_READY"));
    expect(result.kind).toBe("accepted");
  });

  it("denies readout permission for clarification and allows it for other accepted states", () => {
    const clarificationPayload = payload("CLARIFICATION_REQUIRED");
    const clarification = {
      ...clarificationPayload,
      evidence: null,
      parsed: { ...clarificationPayload.parsed, clarification_required: true },
    };
    const clarificationResult = resolveDecisionPresentation(clarification);
    const rangeResult = resolveDecisionPresentation(payload("RANGE_READY"));

    expect(clarificationResult.kind).toBe("accepted");
    if (clarificationResult.kind === "accepted") expect(clarificationResult.readoutAllowed).toBe(false);
    expect(rangeResult.kind).toBe("accepted");
    if (rangeResult.kind === "accepted") expect(rangeResult.readoutAllowed).toBe(true);
  });

  it.each([
    ["unknown status", payload("FUTURE_READY", "RAZONABLE")],
    ["range with classification", payload("RANGE_READY", "ALTO")],
    ["range conclusion with classification wording", { ...payload("RANGE_READY"), summary: "El precio es RAZONABLE." }],
    ["decision without classification", payload("DECISION_READY", null)],
    ["missing parsed.price", (() => { const value = structuredClone(payload("RANGE_READY")); delete (value.parsed as Record<string, unknown>).price; return value; })()],
    ["economic classification assertion", { ...payload("RANGE_READY"), summary: "El precio es RAZONABLE." }],
    ["missing observation IDs", (() => { const value = structuredClone(payload("RANGE_READY")); delete (value.evidence as Record<string, unknown>).observation_ids; return value; })()],
    ["invalid observation IDs type", (() => { const value = structuredClone(payload("RANGE_READY")); (value.evidence as Record<string, unknown>).observation_ids = "not-an-array"; return value; })()],
  ])("fails closed for %s", (_case, value) => {
    expect(resolveDecisionPresentation(value)).toEqual({
      kind: "abstention",
      conclusion: "No puedo interpretar este resultado con seguridad.",
    });
  });
});
