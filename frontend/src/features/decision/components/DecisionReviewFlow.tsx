"use client";

import { useMemo, useState } from "react";
import { decisionIntentLabels } from "@/features/decision/decision-intent";
import { supportQuoteText } from "@/features/decision/fixtures/support-quote";
import {
  createDecisionReadout,
  interpretQuoteForReview,
} from "@/features/decision/interpret-quote";
import type {
  DecisionIntent,
  DecisionReadoutView,
  QuoteInterpretationView,
} from "@/features/decision/types";

type FlowStep = "quote" | "interpretation" | "readout";

type DecisionReviewFlowProps = {
  initialIntent: DecisionIntent;
  initialQuoteText?: string;
};

export function DecisionReviewFlow({
  initialIntent,
  initialQuoteText = supportQuoteText,
}: DecisionReviewFlowProps) {
  const [step, setStep] = useState<FlowStep>("quote");
  const [quoteText, setQuoteText] = useState(initialQuoteText);
  const [showEmptyMessage, setShowEmptyMessage] = useState(false);
  const interpretation = useMemo(() => interpretQuoteForReview(), []);
  const readout = useMemo(() => createDecisionReadout(), []);

  function analyzeQuote() {
    if (!quoteText.trim()) {
      setShowEmptyMessage(true);
      return;
    }

    setShowEmptyMessage(false);
    setStep("interpretation");
  }

  return (
    <main className="min-h-dvh bg-[var(--enki-page)] text-[var(--enki-ink)]">
      <section className="mx-auto flex min-h-dvh w-full max-w-[402px] flex-col border-x border-[var(--enki-line)] bg-[var(--enki-bg)] px-6 py-8 sm:my-6 sm:min-h-[874px] sm:rounded-[18px] sm:border">
        {step === "quote" ? (
          <QuoteInput
            intent={initialIntent}
            quoteText={quoteText}
            showEmptyMessage={showEmptyMessage}
            onQuoteTextChange={setQuoteText}
            onAnalyze={analyzeQuote}
          />
        ) : null}

        {step === "interpretation" ? (
          <InterpretationSummary
            interpretation={interpretation}
            onConfirm={() => setStep("readout")}
            onCorrect={() => setStep("quote")}
          />
        ) : null}

        {step === "readout" ? (
          <DecisionReadout readout={readout} onReviewAgain={() => setStep("quote")} />
        ) : null}
      </section>
    </main>
  );
}

type QuoteInputProps = {
  intent: DecisionIntent;
  quoteText: string;
  showEmptyMessage: boolean;
  onQuoteTextChange: (value: string) => void;
  onAnalyze: () => void;
};

function QuoteInput({
  intent,
  quoteText,
  showEmptyMessage,
  onQuoteTextChange,
  onAnalyze,
}: QuoteInputProps) {
  return (
    <div className="flex flex-1 flex-col">
      <p className="font-mono text-xs font-semibold uppercase leading-none">
        {decisionIntentLabels[intent]}
      </p>
      <h1 className="mt-8 text-[32px] font-extrabold leading-[38px]">
        Pegá la cotización que querés entender.
      </h1>
      <p className="mt-3 text-base leading-6 text-[var(--enki-muted)]">
        Podés editar el texto antes de analizar. Enki va a mostrar qué entiende y qué todavía falta, sin conectar backend en este sprint.
      </p>

      <label className="mt-8 block text-[15px] font-bold" htmlFor="quote-text">
        Cotización
      </label>
      <textarea
        className="mt-3 min-h-[220px] w-full resize-none rounded-lg border border-[var(--enki-line)] bg-[var(--enki-input)] p-4 text-base leading-6 outline-none focus-visible:ring-2 focus-visible:ring-[var(--enki-accent)]"
        id="quote-text"
        value={quoteText}
        onChange={(event) => onQuoteTextChange(event.target.value)}
      />

      {showEmptyMessage ? (
        <p className="mt-3 text-sm leading-5 text-[var(--enki-caution)]">
          Pegá una cotización para analizarla.
        </p>
      ) : null}

      <button
        className="mt-6 min-h-12 rounded-lg bg-[var(--enki-accent)] px-5 text-base font-bold text-white outline-none transition-colors hover:bg-[var(--enki-accent-strong)] focus-visible:ring-2 focus-visible:ring-[var(--enki-accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--enki-bg)]"
        type="button"
        onClick={onAnalyze}
      >
        Analizar
      </button>
    </div>
  );
}

type InterpretationSummaryProps = {
  interpretation: QuoteInterpretationView;
  onConfirm: () => void;
  onCorrect: () => void;
};

function InterpretationSummary({
  interpretation,
  onConfirm,
  onCorrect,
}: InterpretationSummaryProps) {
  return (
    <div className="flex flex-1 flex-col">
      <p className="font-mono text-xs font-semibold uppercase leading-none">
        Interpretación
      </p>
      <h1 className="mt-8 text-[32px] font-extrabold leading-[38px]">
        Esto es lo que entendimos.
      </h1>
      <p className="mt-3 text-base leading-6 text-[var(--enki-muted)]">
        Confirmalo si representa la cotización. Si algo no está bien, corregí el texto original.
      </p>

      <section className="mt-8 border-y border-[var(--enki-line)] py-5">
        <p className="font-mono text-xs font-semibold uppercase">Precio</p>
        <p className="mt-2 text-2xl font-extrabold">{interpretation.priceLabel}</p>
      </section>

      <DimensionList title="Qué entendimos" dimensions={interpretation.understood} />
      <DimensionList title="Qué todavía falta" dimensions={interpretation.missing} muted />

      <div className="mt-auto flex flex-col gap-3 pt-8">
        <button
          className="min-h-12 rounded-lg bg-[var(--enki-accent)] px-5 text-base font-bold text-white outline-none hover:bg-[var(--enki-accent-strong)] focus-visible:ring-2 focus-visible:ring-[var(--enki-accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--enki-bg)]"
          type="button"
          onClick={onConfirm}
        >
          Confirmar
        </button>
        <button
          className="min-h-12 rounded-lg border border-[var(--enki-line)] px-5 text-base font-bold outline-none hover:bg-[var(--enki-option-hover)] focus-visible:ring-2 focus-visible:ring-[var(--enki-accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--enki-bg)]"
          type="button"
          onClick={onCorrect}
        >
          Corregir
        </button>
      </div>
    </div>
  );
}

type DecisionReadoutProps = {
  readout: DecisionReadoutView;
  onReviewAgain: () => void;
};

function DecisionReadout({ readout, onReviewAgain }: DecisionReadoutProps) {
  return (
    <div className="flex flex-1 flex-col">
      <p className="font-mono text-xs font-semibold uppercase leading-none">
        ¿Se puede comparar?
      </p>
      <h1 className="mt-8 text-[32px] font-extrabold leading-[38px]">
        {readout.summary}
      </h1>
      <p className="mt-3 text-base leading-6 text-[var(--enki-muted)]">
        Con lo que sabemos, el precio está identificado. La comparación todavía depende de datos que no aparecen en la cotización.
      </p>

      <section className="mt-8 border-y border-[var(--enki-line)] py-5">
        <p className="font-mono text-xs font-semibold uppercase">Precio conocido</p>
        <p className="mt-2 text-2xl font-extrabold">{readout.priceLabel}</p>
      </section>

      <DimensionList title="Qué sabemos" dimensions={readout.known} />
      <DimensionList title="Qué puede cambiar la comparación" dimensions={readout.missing} muted />

      <section className="mt-6 rounded-lg bg-[var(--enki-question)] p-4">
        <p className="font-mono text-xs font-semibold uppercase">
          Qué conviene hacer ahora
        </p>
        <p className="mt-2 text-sm leading-5">{readout.nextAction}</p>
      </section>

      <button
        className="mt-auto min-h-12 rounded-lg border border-[var(--enki-line)] px-5 text-base font-bold outline-none hover:bg-[var(--enki-option-hover)] focus-visible:ring-2 focus-visible:ring-[var(--enki-accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--enki-bg)]"
        type="button"
        onClick={onReviewAgain}
      >
        Revisar texto
      </button>
    </div>
  );
}

type DimensionListProps = {
  title: string;
  dimensions: { label: string }[];
  muted?: boolean;
};

function DimensionList({ title, dimensions, muted = false }: DimensionListProps) {
  return (
    <section className="mt-6">
      <h2 className="font-mono text-xs font-semibold uppercase">{title}</h2>
      <ul className="mt-3 space-y-3">
        {dimensions.map((dimension) => (
          <li
            className={`border-l-2 pl-3 text-[15px] leading-6 ${
              muted
                ? "border-[var(--enki-line)] text-[var(--enki-muted)]"
                : "border-[var(--enki-accent)]"
            }`}
            key={dimension.label}
          >
            {dimension.label}
          </li>
        ))}
      </ul>
    </section>
  );
}