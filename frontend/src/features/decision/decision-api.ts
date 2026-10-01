import { resolveDecisionPresentation } from "@/features/decision/decision-presentation-contract";
import type { DecisionPresentation } from "@/features/decision/decision-presentation-contract";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_ENKI_API_URL ?? "http://127.0.0.1:8000";

export async function analyzePricingQuery(
  query: string,
): Promise<DecisionPresentation> {
  const response = await fetch(`${API_BASE_URL}/decision/pricing`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json; charset=utf-8",
    },
    body: JSON.stringify({ query }),
  });

  if (!response.ok) {
    throw new Error(`Enki API respondió HTTP ${response.status}`);
  }

  const payload: unknown = await response.json();
  return resolveDecisionPresentation(payload);
}
