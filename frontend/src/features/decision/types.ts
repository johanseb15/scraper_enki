export type DecisionIntent = "sending_quote" | "received_quote";

export type InterpretationAttribute = {
  label: string;
};

export type QuoteInterpretationView = {
  priceLabel: string;
  understood: InterpretationAttribute[];
  missing: InterpretationAttribute[];
};

export type DecisionReadoutState =
  | "potentially_comparable"
  | "not_comparable"
  | "indeterminate";

export type DecisionDimension = {
  label: string;
};

export type DecisionReadoutView = {
  state: DecisionReadoutState;
  priceLabel: string;
  summary: string;
  known: DecisionDimension[];
  missing: DecisionDimension[];
  nextAction: string;
};