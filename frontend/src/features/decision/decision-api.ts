import type { DecisionPricingResponse } from "@/features/decision/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_ENKI_API_URL ?? "http://127.0.0.1:8000";

export async function analyzePricingQuery(
  query: string,
): Promise<DecisionPricingResponse> {
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

  return (await response.json()) as DecisionPricingResponse;
}
