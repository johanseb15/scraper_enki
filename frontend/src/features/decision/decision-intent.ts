import type { DecisionIntent } from "./types";

export const decisionIntentLabels: Record<DecisionIntent, string> = {
  sending_quote: "Estoy por enviar una cotización",
  received_quote: "Recibí una propuesta",
};

export function parseDecisionIntent(value: string | null): DecisionIntent {
  return value === "received_quote" ? "received_quote" : "sending_quote";
}