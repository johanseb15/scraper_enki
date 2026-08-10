import type {
  DecisionReadoutView,
  QuoteInterpretationView,
} from "@/features/decision/types";

export const supportQuoteText = [
  "Abono mensual de soporte para 15 PCs.",
  "Incluye soporte remoto,",
  "mantenimiento preventivo",
  "y dos visitas mensuales.",
  "$350.000 por mes.",
].join("\n");

export const supportQuoteInterpretation: QuoteInterpretationView = {
  priceLabel: "$350.000 / mes",
  understood: [
    { label: "15 computadoras" },
    { label: "Soporte remoto" },
    { label: "2 visitas presenciales" },
    { label: "1 sede física" },
  ],
  missing: [
    { label: "Horario de atención" },
    { label: "Servidores" },
    { label: "Tiempo de respuesta" },
  ],
};

export const supportQuoteReadout: DecisionReadoutView = {
  state: "indeterminate",
  priceLabel: "$350.000 / mes",
  summary: "Nos falta información para compararlo bien.",
  known: [
    { label: "15 computadoras" },
    { label: "Soporte remoto" },
    { label: "2 visitas presenciales" },
    { label: "1 sede física" },
  ],
  missing: [
    { label: "Horario de atención" },
    { label: "Servidores" },
    { label: "Tiempo de respuesta" },
  ],
  nextAction:
    "Pedí esos tres datos antes de comparar precio contra otra propuesta.",
};