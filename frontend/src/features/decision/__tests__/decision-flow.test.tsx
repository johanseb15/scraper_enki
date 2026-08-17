import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Home from "@/app/page";
import { DecisionReviewFlow } from "@/features/decision/components/DecisionReviewFlow";

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
  parsed: {
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
    clarification_required: false,
    clarification_reason: null,
    clarification_question: null,
  },
  evidence: {
    market: "AR",
    canonical_service: "SOPORTE_REMOTO",
    observations_n: 3,
    providers_n: 3,
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
  },
};

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
