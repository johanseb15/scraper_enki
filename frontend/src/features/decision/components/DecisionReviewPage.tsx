"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { parseDecisionIntent } from "@/features/decision/decision-intent";
import { supportQuoteText } from "@/features/decision/fixtures/support-quote";
import { DecisionReviewFlow } from "@/features/decision/components/DecisionReviewFlow";

export function DecisionReviewPage() {
  const searchParams = useSearchParams();
  const intent = parseDecisionIntent(searchParams.get("intent"));
  const [quoteText] = useState(() => {
    if (typeof window === "undefined") {
      return supportQuoteText;
    }

    return window.sessionStorage.getItem("enki.quoteDraft") ?? supportQuoteText;
  });

  return <DecisionReviewFlow initialIntent={intent} initialQuoteText={quoteText} />;
}
