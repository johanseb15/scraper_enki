import { render, screen } from "@testing-library/react";
import { EvidenceJourneyVisual } from "@/components/enki/EvidenceJourneyVisual";

describe("ADEL / rediseño ilustrativo de Enki", () => {
  it("explica el flujo sin simular una recomendación económica", () => {
    render(<EvidenceJourneyVisual />);

    expect(
      screen.getByRole("figure", { name: /cómo enki conserva el contexto/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/ejemplo ilustrativo/i)).toBeInTheDocument();
    expect(screen.getByText(/fuente/i)).toBeInTheDocument();
    expect(screen.getByText(/interpretación/i)).toBeInTheDocument();
    expect(screen.getByText(/sin evidencia suficiente, no se asigna un precio/i)).toBeInTheDocument();
    expect(screen.queryByText(/rango observado/i)).not.toBeInTheDocument();
  });
});
