import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Home from "@/app/page";
import { DecisionReviewFlow } from "@/features/decision/components/DecisionReviewFlow";
import type { DecisionPricingResponse } from "@/features/decision/types";

const hourlyQuery =
  "me quieren cobrar 35 lucas la hora por soporte remoto, está bien?";

const rangeReadyResponse = {
  status: "RANGE_READY",
  headline: "Rango de mercado disponible",
  summary:
    "Hay evidencia suficiente para mostrar un rango empírico, pero no para emitir BAJO/RAZONABLE/ALTO.",
  evidence_line:
    "Rango observado $28.000–$40.000; mediana $30.000; 3 precios de 3 proveedores.",
  caveat: "Confianza de evidencia: LOW.",
  clarification_reason: null,
  clarification_question: null,
  unsupported_reason: null,
  market_resolution: null,
  pricing_readiness: null,
  evidence_probe: null,
  parsed: {
    query_kind: "ECONOMIC_QUERY",
    intent_action: "EVALUATE_PRICE",
    intent_side: "BUY",
    economic_object_kind: "SERVICE",
    canonical_services: ["SOPORTE_REMOTO"],
    market_scope: "REMOTE_NATIONAL",
    modality: "REMOTE",
    price: {
      type: "PER_HOUR",
      value: 35000,
      min: null,
      max: null,
      currency: "ARS",
      is_approximate: false,
    },
    geography: { province: null, city: null },
    device_type: null,
    condition: "UNKNOWN",
    is_bundle: false,
    goods_components: [],
    parts_scope: "UNKNOWN",
    commercial_context: {
      value: "STANDARD",
      status: "OBSERVED",
      origin: "CONTROLLED_FIXTURE",
      raw_basis: [],
      resolution_method: "commercial-context-v1",
    },
    clarification_required: false,
    clarification_reason: null,
    clarification_question: null,
    technical_need: null,
    monetary_components: [],
  },
  evidence: {
    market: "AR",
    canonical_service: "SOPORTE_REMOTO",
    observations_n: 3,
    providers_n: 3,
    source_count: 4,
    provider_independence_version: null,
    min_ars: 28000,
    q1_ars: 29000,
    median_ars: 30000,
    q3_ars: 35000,
    max_ars: 40000,
    evidence_confidence: "LOW",
    price_position: "WITHIN_OBSERVED_RANGE",
    decision_label: null,
    price_scope: "PER_HOUR",
    commercial_context: "STANDARD",
    commercial_context_provenance: {
      value: "STANDARD",
      status: "OBSERVED",
      origin: "CONTROLLED_FIXTURE",
      raw_basis: [],
      resolution_method: "commercial-context-v1",
    },
    evidence_commercial_context: null,
    lineage_gate_version: null,
    service_reach_gate_version: null,
    temporal_gate_version: null,
    temporal_state: null,
    acquired_at_min: null,
    acquired_at_max: null,
    freshness_policy_version: null,
    observation_ids: [],
  },
} satisfies DecisionPricingResponse;

const clarificationQuestion =
  "¿Ese precio corresponde a una hora, una visita o al trabajo completo?";

const clarificationResponse = {
  ...rangeReadyResponse,
  status: "CLARIFICATION_REQUIRED",
  headline: "Necesito una aclaración",
  summary: clarificationQuestion,
  evidence_line: null,
  caveat: "PRICE_SCOPE_REQUIRED",
  clarification_reason: "PRICE_SCOPE_REQUIRED",
  clarification_question: clarificationQuestion,
  parsed: {
    ...rangeReadyResponse.parsed,
    price: {
      ...rangeReadyResponse.parsed.price,
      type: "EXACT",
    },
    clarification_required: true,
    clarification_reason: "PRICE_SCOPE_REQUIRED",
    clarification_question: clarificationQuestion,
  },
  evidence: null,
} satisfies DecisionPricingResponse;

const insufficientEvidenceResponse = {
  ...rangeReadyResponse,
  status: "INSUFFICIENT_EVIDENCE",
  headline: "Evidencia insuficiente",
  summary:
    "Hay precios observados, pero la muestra o diversidad de proveedores todavía no alcanza para una decisión confiable.",
  evidence_line: null,
  caveat: "Enki retiene la decisión en lugar de sobreinterpretar la muestra.",
  clarification_reason: null,
  clarification_question: null,
  unsupported_reason: null,
  evidence: {
    ...rangeReadyResponse.evidence,
    observations_n: 3,
    providers_n: 1,
    evidence_confidence: "INSUFFICIENT",
    price_position: null,
    decision_label: null,
  },
} satisfies DecisionPricingResponse;

const decisionReadyResponse = {
  ...rangeReadyResponse,
  status: "DECISION_READY",
  headline: "ALTO",
  summary:
    "El precio consultado está alto para esta cohorte. El cuartil superior comienza por encima de $75.000.",
  evidence_line:
    "Rango observado $45.000–$95.000; mediana $65.000; 6 precios de 4 proveedores.",
  caveat: "Confianza de evidencia: MEDIUM.",
  clarification_reason: null,
  clarification_question: null,
  unsupported_reason: null,
  parsed: {
    ...rangeReadyResponse.parsed,
    canonical_services: ["FORMATEO_NOTEBOOK"],
    market_scope: "LOCAL",
    modality: "ONSITE",
    price: {
      ...rangeReadyResponse.parsed.price,
      type: "EXACT",
      value: 80000,
    },
    geography: {
      province: "Córdoba",
      city: "Córdoba",
    },
  },
  evidence: {
    ...rangeReadyResponse.evidence,
    canonical_service: "FORMATEO_NOTEBOOK",
    observations_n: 6,
    providers_n: 4,
    source_count: 4,
    min_ars: 45000,
    q1_ars: 55000,
    median_ars: 65000,
    q3_ars: 75000,
    max_ars: 95000,
    evidence_confidence: "MEDIUM",
    price_position: "WITHIN_OBSERVED_RANGE",
    decision_label: "ALTO",
    price_scope: "TOTAL",
    temporal_state: "CURRENT_REPRODUCIBLE",
  },
} satisfies DecisionPricingResponse;

describe("Decision review flow", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => rangeReadyResponse,
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  function respondWith(response: DecisionPricingResponse) {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: async () => response,
    }));
  }

  async function openInterpretation() {
    const user = userEvent.setup();
    render(<DecisionReviewFlow initialIntent="received_quote" />);
    await user.click(screen.getByRole("button", { name: /analizar/i }));
    await screen.findByText(/esto es lo que Enki entendió/i);
    return user;
  }

  it("preserves Argentine cents in interpretation and the consulted price on readout", async () => {
    respondWith({
      ...decisionReadyResponse,
      parsed: { ...decisionReadyResponse.parsed, price: {
        ...decisionReadyResponse.parsed.price, value: 35000.5,
      } },
    });
    const user = await openInterpretation();
    expect(screen.getAllByText("$35.000,50")).toHaveLength(2);
    expect(screen.queryByText("$35.001")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /ver resultado/i }));
    expect(screen.getAllByText("$35.000,50").length).toBeGreaterThan(0);
    expect(screen.getByRole("region", { name: /precio consultado \$35\.000,50/i })).toBeVisible();
  });

  it("preserves cents in the observed rail and its accessible reference prices", async () => {
    respondWith({ ...decisionReadyResponse, evidence: {
      ...decisionReadyResponse.evidence,
      min_ars: 28000.1, q1_ars: 29000.2, median_ars: 30000.5,
      q3_ars: 35000.75, max_ars: 40000.99,
    } });
    const user = await openInterpretation();
    await user.click(screen.getByRole("button", { name: /ver resultado/i }));
    for (const label of ["$28.000,10", "$29.000,20", "$30.000,50", "$35.000,75", "$40.000,99"]) {
      expect(screen.getAllByText(label, { exact: false }).length).toBeGreaterThan(0);
    }
    expect(screen.getByRole("region", { name: /mediana \$30\.000,50/i })).toBeVisible();
  });

  it("preserves cents in references when the backend does not supply quartiles", async () => {
    respondWith({ ...rangeReadyResponse, evidence: {
      ...rangeReadyResponse.evidence,
      min_ars: 28000.1, median_ars: 30000.5, max_ars: 40000.99,
      q1_ars: null, q3_ars: null,
    } });
    const user = await openInterpretation();
    await user.click(screen.getByRole("button", { name: /ver resultado/i }));
    expect(screen.getByText("Rango observado: $28.000,10 – $40.000,99")).toBeVisible();
    expect(screen.getByText("Mediana: $30.000,50")).toBeVisible();
  });

  it("preserves cents in a price range in interpretation and readout", async () => {
    respondWith({ ...rangeReadyResponse, parsed: {
      ...rangeReadyResponse.parsed, price: {
        ...rangeReadyResponse.parsed.price,
        type: "RANGE", value: null, min: 35000.5, max: 40000.75,
      },
    } });
    const user = await openInterpretation();
    expect(screen.getByText("$35.000,50 – $40.000,75")).toBeVisible();
    await user.click(screen.getByRole("button", { name: /ver resultado/i }));
    expect(screen.getByText("$35.000,50 – $40.000,75")).toBeVisible();
  });

  it.each([
    ["USD", "35.000,50 USD"],
    ["UNKNOWN", "35.000,50 · moneda sin confirmar"],
  ])("shows %s without rounding or exposing unknown currency tokens", async (currency, label) => {
    respondWith({ ...clarificationResponse, parsed: {
      ...clarificationResponse.parsed, price: {
        ...clarificationResponse.parsed.price, value: 35000.5, currency,
      },
    } });
    await openInterpretation();
    expect(screen.getAllByText(label)).toHaveLength(2);
    expect(screen.queryByText(/UNKNOWN/)).not.toBeInTheDocument();
  });

  it.each([
    ["NO_EVIDENCE", "Sin evidencia comparable", "No encontré precios comparables para este servicio y mercado."],
    ["UNSUPPORTED_QUERY", "Fuera del alcance actual", "La consulta está fuera del alcance seguro de Enki Decision v1."],
    ["INSUFFICIENT_EVIDENCE", "Evidencia insuficiente", insufficientEvidenceResponse.summary],
  ])("expresses the actual %s cause in interpretation and readout", async (status, label, summary) => {
    respondWith({
      ...rangeReadyResponse, status, headline: "No puedo evaluar el precio", summary,
      evidence_line: null, caveat: "La decisión queda retenida.",
      unsupported_reason: status === "UNSUPPORTED_QUERY" ? "ARS_ONLY_V1" : null,
      evidence: status === "INSUFFICIENT_EVIDENCE" ? insufficientEvidenceResponse.evidence : null,
    });
    const user = await openInterpretation();
    expect(screen.getByText(label, { exact: true })).toBeVisible();
    expect(screen.getAllByText(summary).length).toBeGreaterThan(0);
    expect(screen.queryByText(/estas propuestas no incluyen lo mismo/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/no comparable todavía/i)).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /ver resultado/i }));
    expect(screen.getByRole("heading", { name: "No puedo evaluar el precio" })).toBeVisible();
    expect(screen.getByText(label, { exact: true })).toBeVisible();
    expect(screen.getAllByText(summary).length).toBeGreaterThan(0);
    expect(screen.queryByText(new RegExp(`Estado: ${status}`))).not.toBeInTheDocument();
    expect(screen.queryByText(/estas propuestas no incluyen lo mismo/i)).not.toBeInTheDocument();
    expect(screen.getByText("La decisión queda retenida.")).toBeVisible();
  });

  it("uses the backend clarification question without blaming the evidence or alleging incompatibility", async () => {
    respondWith(clarificationResponse);
    await openInterpretation();
    expect(screen.getByText("Falta aclarar la consulta")).toBeVisible();
    expect(screen.getAllByText(clarificationQuestion).length).toBeGreaterThan(0);
    expect(screen.queryByText(/estas propuestas no incluyen lo mismo/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /ver resultado/i })).not.toBeInTheDocument();
  });

  it("does not infer proven incompatibility from a NO_EVIDENCE response with rejected context", async () => {
    respondWith({ ...rangeReadyResponse,
      status: "NO_EVIDENCE", headline: "Sin evidencia comparable",
      summary: "No encontré precios comparables para este servicio y mercado.",
      evidence_line: null, caveat: null,
      evidence: { ...rangeReadyResponse.evidence, observations_n: 0, providers_n: 0,
        min_ars: null, q1_ars: null, median_ars: null, q3_ars: null, max_ars: null,
        evidence_confidence: "INSUFFICIENT", commercial_context: "UNKNOWN",
      },
    });
    const user = await openInterpretation();
    expect(screen.queryByText(/estas propuestas no incluyen lo mismo/i)).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /ver resultado/i }));
    expect(screen.queryByText(/^evidencia comparable$/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/estas propuestas no incluyen lo mismo/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("region", { name: /rango comparable/i })).not.toBeInTheDocument();
  });

  it("preserves the backend explanation for an unrecognized status without inventing a cause", async () => {
    const summary = "No se puede emitir una evaluación segura en este estado.";
    respondWith({ ...rangeReadyResponse, status: "UNRECOGNIZED_STATUS", summary,
      evidence: null, evidence_line: null,
    });
    const user = await openInterpretation();
    expect(screen.getByText(summary)).toBeVisible();
    expect(screen.queryByText(/estas propuestas no incluyen lo mismo/i)).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /ver resultado/i }));
    expect(screen.getAllByText(summary).length).toBeGreaterThan(0);
    expect(screen.queryByText(/^Estado:/)).not.toBeInTheDocument();
  });

  it.each(["NONE", "UNKNOWN"])("does not expose %s confidence when no evidence was admitted", async (confidence) => {
    respondWith({ ...rangeReadyResponse,
      status: "NO_EVIDENCE", headline: "Sin evidencia comparable",
      summary: "No encontré precios comparables para este servicio y mercado.",
      evidence_line: null, caveat: null,
      evidence: { ...rangeReadyResponse.evidence, observations_n: 0, providers_n: 0,
        min_ars: null, q1_ars: null, median_ars: null, q3_ars: null, max_ars: null,
        evidence_confidence: confidence,
      },
    });
    const user = await openInterpretation();
    await user.click(screen.getByRole("button", { name: /ver resultado/i }));
    expect(screen.getByRole("heading", { name: "Sin evidencia comparable" })).toBeVisible();
    expect(screen.queryByText(/^Confianza:/)).not.toBeInTheDocument();
  });

  it("preserves sending_quote intent when the user enters the quote flow from Home", () => {
    render(<Home />);
    expect(
      screen.getByRole("link", { name: /estoy por enviar una cotización/i }),
    ).toHaveAttribute("href", "/cotizacion?intent=sending_quote");
  });

  it("does not call the API when Quote Input is empty", async () => {
    const user = userEvent.setup();
    render(<DecisionReviewFlow initialIntent="sending_quote" />);

    await user.clear(screen.getByLabelText(/cotización/i));
    await user.click(screen.getByRole("button", { name: /analizar/i }));

    expect(
      screen.getByText(/escribí una consulta para analizarla/i),
    ).toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
  });

  it("calls Enki API and shows the real interpretation", async () => {
    const user = userEvent.setup();
    render(
      <DecisionReviewFlow
        initialIntent="received_quote"
        initialQuoteText={hourlyQuery}
      />,
    );

    await user.click(screen.getByRole("button", { name: /analizar/i }));

    await screen.findByText(/esto es lo que Enki entendió/i);
    expect(screen.getByText(/soporte remoto/i)).toBeInTheDocument();
    expect(screen.getAllByText(/\$35\.000/i)).toHaveLength(2);

    expect(fetch).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/decision/pricing",
      expect.objectContaining({
        method: "POST",
      }),
    );
  });

  it("blocks pricing readout while CLARIFICATION_REQUIRED", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => clarificationResponse,
      }),
    );

    const user = userEvent.setup();

    render(
      <DecisionReviewFlow
        initialIntent="received_quote"
        initialQuoteText="me quieren cobrar 35 lucas por soporte remoto, está bien?"
      />,
    );

    await user.click(screen.getByRole("button", { name: /analizar/i }));

    await screen.findByText(/esto es lo que Enki entendió/i);

    const missingSection = screen.getByRole("heading", { name: "Lo que falta aclarar" }).closest("section")!;
    expect(within(missingSection).getByText(clarificationQuestion)).toBeVisible();

    expect(
      screen.getByRole("button", { name: /corregir consulta/i }),
    ).toBeEnabled();

    expect(
      screen.queryByRole("button", { name: /ver resultado/i }),
    ).not.toBeInTheDocument();

    expect(
      screen.queryByText(/resultado Enki/i),
    ).not.toBeInTheDocument();
  });

  it("shows evidence after confirming the interpretation", async () => {
    const user = userEvent.setup();
    render(
      <DecisionReviewFlow
        initialIntent="received_quote"
        initialQuoteText={hourlyQuery}
      />,
    );

    await user.click(screen.getByRole("button", { name: /analizar/i }));
    await screen.findByText(/esto es lo que Enki entendió/i);
    await user.click(screen.getByRole("button", { name: /ver resultado/i }));

    expect(
      screen.getByText("Rango de mercado disponible"),
    ).toBeInTheDocument();
    expect(screen.getByText(/mediana: \$30\.000/i)).toBeInTheDocument();
    expect(
      screen.getAllByText(/3 precios de 3 proveedores/i),
    ).toHaveLength(2);
    expect(screen.getByText(/confianza: low/i)).toBeInTheDocument();
  });

  it("does not present RANGE_READY as decision-oriented guidance", async () => {
    const user = userEvent.setup();

    render(
      <DecisionReviewFlow
        initialIntent="received_quote"
        initialQuoteText={hourlyQuery}
      />,
    );

    await user.click(screen.getByRole("button", { name: /analizar/i }));
    await screen.findByText(/esto es lo que Enki entendió/i);
    await user.click(screen.getByRole("button", { name: /ver resultado/i }));

    expect(
      screen.getByText("Rango de mercado disponible"),
    ).toBeInTheDocument();

    expect(
      screen.queryByText(/^(BAJO|RAZONABLE|ALTO)$/i),
    ).not.toBeInTheDocument();

    expect(
      screen.queryByText(/^orientación posible$/i),
    ).not.toBeInTheDocument();
  });

  it("does not turn INSUFFICIENT_EVIDENCE into a benchmark from structured evidence", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => insufficientEvidenceResponse,
      }),
    );

    const user = userEvent.setup();

    render(
      <DecisionReviewFlow
        initialIntent="received_quote"
        initialQuoteText={hourlyQuery}
      />,
    );

    await user.click(screen.getByRole("button", { name: /analizar/i }));
    await screen.findByText(/esto es lo que Enki entendió/i);
    await user.click(screen.getByRole("button", { name: /ver resultado/i }));

    expect(
      screen.getByRole("heading", { name: /evidencia insuficiente/i }),
    ).toBeInTheDocument();

    expect(
      screen.queryByText(/rango observado:/i),
    ).not.toBeInTheDocument();

    expect(
      screen.queryByText(/mediana:/i),
    ).not.toBeInTheDocument();
  });

  it("does not describe INSUFFICIENT_EVIDENCE as comparable evidence", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => insufficientEvidenceResponse,
      }),
    );

    const user = userEvent.setup();

    render(
      <DecisionReviewFlow
        initialIntent="received_quote"
        initialQuoteText={hourlyQuery}
      />,
    );

    await user.click(screen.getByRole("button", { name: /analizar/i }));
    await screen.findByText(/esto es lo que Enki entendió/i);
    await user.click(screen.getByRole("button", { name: /ver resultado/i }));

    expect(
      screen.getByRole("heading", { name: /evidencia insuficiente/i }),
    ).toBeInTheDocument();

    expect(
      screen.getByText(/3 precios de 1 proveedores/i),
    ).toBeInTheDocument();

    expect(
      screen.queryByText(/^evidencia comparable$/i),
    ).not.toBeInTheDocument();
  });

  it("does not expose the raw INSUFFICIENT confidence enum to users", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => insufficientEvidenceResponse,
      }),
    );

    const user = userEvent.setup();

    render(
      <DecisionReviewFlow
        initialIntent="received_quote"
        initialQuoteText={hourlyQuery}
      />,
    );

    await user.click(screen.getByRole("button", { name: /analizar/i }));
    await screen.findByText(/esto es lo que Enki entendió/i);
    await user.click(screen.getByRole("button", { name: /ver resultado/i }));

    expect(
      screen.getByRole("heading", { name: /evidencia insuficiente/i }),
    ).toBeInTheDocument();

    expect(
      screen.getByText(/3 precios de 1 proveedores/i),
    ).toBeInTheDocument();

    expect(
      screen.queryByText(/^confianza:\s*insufficient$/i),
    ).not.toBeInTheDocument();
  });

  it("presents DECISION_READY with a human classification distinct from observed-range position", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => decisionReadyResponse,
      }),
    );

    const user = userEvent.setup();

    render(
      <DecisionReviewFlow
        initialIntent="received_quote"
        initialQuoteText="Me quieren cobrar $80.000 por formatear una notebook en Córdoba. ¿Está bien?"
      />,
    );

    await user.click(screen.getByRole("button", { name: /analizar/i }));
    await screen.findByText(/esto es lo que Enki entendió/i);
    await user.click(screen.getByRole("button", { name: /ver resultado/i }));

    expect(screen.getByText("Precio consultado")).toBeInTheDocument();
    expect(screen.getAllByText(/\$80\.000/i).length).toBeGreaterThan(0);

    expect(
      screen.getByText("Por encima del intervalo central observado"),
    ).toBeInTheDocument();
  });

  it("returns to the original query when the user corrects it", async () => {
    const user = userEvent.setup();
    render(
      <DecisionReviewFlow
        initialIntent="received_quote"
        initialQuoteText={hourlyQuery}
      />,
    );

    await user.click(screen.getByRole("button", { name: /analizar/i }));
    await screen.findByText(/esto es lo que Enki entendió/i);
    await user.click(screen.getByRole("button", { name: /corregir consulta/i }));

    expect(screen.getByLabelText(/cotización/i)).toHaveValue(hourlyQuery);
  });

  it("shows a visible API error without advancing the flow", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new Error("Failed to fetch")),
    );

    const user = userEvent.setup();
    render(
      <DecisionReviewFlow
        initialIntent="received_quote"
        initialQuoteText={hourlyQuery}
      />,
    );

    await user.click(screen.getByRole("button", { name: /analizar/i }));

    await waitFor(() => {
      expect(screen.getByText(/failed to fetch/i)).toBeInTheDocument();
    });
    expect(
      screen.queryByText(/esto es lo que Enki entendió/i),
    ).not.toBeInTheDocument();
  });
});
