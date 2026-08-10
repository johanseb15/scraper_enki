import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Home from "@/app/page";
import { DecisionReviewFlow } from "@/features/decision/components/DecisionReviewFlow";

const supportQuote = [
  "Abono mensual de soporte para 15 PCs.",
  "Incluye soporte remoto,",
  "mantenimiento preventivo",
  "y dos visitas mensuales.",
  "$350.000 por mes.",
].join("\n");

describe("Decision review flow", () => {
  it("preserves sending_quote intent when the user enters the quote flow from Home", () => {
    render(<Home />);

    const sendingQuote = screen.getByRole("link", {
      name: /estoy por enviar una cotización/i,
    });

    expect(sendingQuote).toHaveAttribute(
      "href",
      "/cotizacion?intent=sending_quote",
    );
  });

  it("does not advance when Quote Input is empty", async () => {
    const user = userEvent.setup();
    render(<DecisionReviewFlow initialIntent="sending_quote" />);

    await user.clear(screen.getByLabelText(/cotización/i));
    await user.click(screen.getByRole("button", { name: /analizar/i }));

    expect(
      screen.getByText(/pegá una cotización para analizarla/i),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(/esto es lo que entendimos/i),
    ).not.toBeInTheDocument();
  });

  it("shows Interpretation after analyzing a quote with text", async () => {
    const user = userEvent.setup();
    render(
      <DecisionReviewFlow
        initialIntent="sending_quote"
        initialQuoteText={supportQuote}
      />,
    );

    await user.click(screen.getByRole("button", { name: /analizar/i }));

    expect(screen.getByText(/esto es lo que entendimos/i)).toBeInTheDocument();
    expect(screen.getByText("$350.000 / mes")).toBeInTheDocument();
    expect(screen.getByText(/15 computadoras/i)).toBeInTheDocument();
    expect(screen.getByText(/soporte remoto/i)).toBeInTheDocument();
    expect(screen.getByText(/2 visitas/i)).toBeInTheDocument();
  });

  it("returns to Quote Input and preserves the original text when the user corrects", async () => {
    const user = userEvent.setup();
    render(
      <DecisionReviewFlow
        initialIntent="received_quote"
        initialQuoteText={supportQuote}
      />,
    );

    await user.click(screen.getByRole("button", { name: /analizar/i }));
    await user.click(screen.getByRole("button", { name: /corregir/i }));

    expect(screen.getByLabelText(/cotización/i)).toHaveValue(supportQuote);
  });

  it("shows Decision Readout after confirming Interpretation", async () => {
    const user = userEvent.setup();
    render(
      <DecisionReviewFlow
        initialIntent="sending_quote"
        initialQuoteText={supportQuote}
      />,
    );

    await user.click(screen.getByRole("button", { name: /analizar/i }));
    await user.click(screen.getByRole("button", { name: /confirmar/i }));

    expect(
      screen.getByText(/nos falta información para compararlo bien/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/horario de atención/i)).toBeInTheDocument();
    expect(screen.getByText(/servidores/i)).toBeInTheDocument();
    expect(screen.getByText(/tiempo de respuesta/i)).toBeInTheDocument();
  });
});
