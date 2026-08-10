import { Suspense } from "react";
import { DecisionReviewPage } from "@/features/decision/components/DecisionReviewPage";

export default function QuoteReviewPage() {
  return (
    <Suspense>
      <DecisionReviewPage />
    </Suspense>
  );
}