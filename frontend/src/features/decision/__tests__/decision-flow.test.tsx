import { render, screen, waitFor } from "@testing-library/react";
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

    expect(screen.getByText(clarificationQuestion)).toBeVisible();

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
