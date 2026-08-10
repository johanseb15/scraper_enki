import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DecisionState } from "@/components/enki/decision-state";
import { MissingDimension } from "@/components/enki/missing-dimension";
import { QuoteComposer } from "@/features/decision/components/QuoteComposer";

describe("modular Enki product UI", () => {
  it("renders indeterminate DecisionState without inventing a score", () => {
    render(<DecisionState state="indeterminate" />);

    expect(
      screen.getByText(/nos falta información para compararlo bien/i),
    ).toBeInTheDocument();
    expect(screen.queryByText(/%/)).not.toBeInTheDocument();
  });

  it("renders a missing dimension as attention, not as an error", () => {
    render(<MissingDimension label="Horario de atención" importance="Importante" />);

    expect(screen.getByText(/horario de atención/i)).toBeInTheDocument();
    expect(screen.getByText(/importante/i)).toBeInTheDocument();
    expect(screen.queryByText(/error/i)).not.toBeInTheDocument();
  });

  it("keeps QuoteComposer from starting an evaluation with empty text", async () => {
    const user = userEvent.setup();
    const onEvaluate = vi.fn();
    render(<QuoteComposer onEvaluate={onEvaluate} />);

    await user.click(screen.getByRole("button", { name: /evaluar/i }));

    expect(onEvaluate).not.toHaveBeenCalled();
    expect(screen.getByText(/pegá una cotización para evaluarla/i)).toBeInTheDocument();
  });

  it("submits QuoteComposer text exactly as written", async () => {
    const user = userEvent.setup();
    const onEvaluate = vi.fn();
    render(<QuoteComposer onEvaluate={onEvaluate} />);

    const text = "Servicio técnico mensual\n$350.000 por mes";
    await user.type(screen.getByLabelText(/cotización a evaluar/i), text);
    await user.click(screen.getByRole("button", { name: /evaluar/i }));

    expect(onEvaluate).toHaveBeenCalledWith(text);
  });
});