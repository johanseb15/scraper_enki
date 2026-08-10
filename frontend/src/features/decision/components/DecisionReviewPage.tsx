"use client";

import { useSearchParams } from "next/navigation";
import { parseDecisionIntent } from "@/features/decision/decision-intent";
import { DecisionReviewFlow } from "@/features/decision/components/DecisionReviewFlow";

export function DecisionReviewPage() {
  const searchParams = useSearchParams();
  const intent = parseDecisionIntent(searchParams.get("intent"));

  return <DecisionReviewFlow initialIntent={intent} />;
}