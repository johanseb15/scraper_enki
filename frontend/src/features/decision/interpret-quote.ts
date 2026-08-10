import {
  supportQuoteInterpretation,
  supportQuoteReadout,
} from "@/features/decision/fixtures/support-quote";
import type {
  DecisionReadoutView,
  QuoteInterpretationView,
} from "@/features/decision/types";

export function interpretQuoteForReview(): QuoteInterpretationView {
  return supportQuoteInterpretation;
}

export function createDecisionReadout(): DecisionReadoutView {
  return supportQuoteReadout;
}