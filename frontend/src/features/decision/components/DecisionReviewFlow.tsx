"use client";

import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Chip } from "@/components/ui/chip";
import { DecisionState } from "@/components/enki/decision-state";
import { DimensionList } from "@/components/enki/dimension-list";
import { EvidenceMeta } from "@/components/enki/evidence-meta";
import { PriceDisplay } from "@/components/enki/price-display";
import { decisionIntentLabels } from "@/features/decision/decision-intent";
import { supportQuoteText } from "@/features/decision/fixtures/support-quote";
import { QuoteComposer } from "@/features/decision/components/QuoteComposer";
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
  const interpretation = useMemo(() => interpretQuoteForReview(), []);
  const readout = useMemo(() => createDecisionReadout(), []);

  function analyzeQuote(nextQuoteText: string) {
    setQuoteText(nextQuoteText);
    setStep("interpretation");
  }

  return (
    <main className="min-h-dvh bg-[var(--enki-page)] text-[var(--enki-ink-900)]">
      <section className="mx-auto w-full max-w-6xl px-4 py-5 sm:px-6 sm:py-8">
        <ReviewHeader intent={initialIntent} />

        {step === "quote" ? (
          <QuoteInput
            intent={initialIntent}
            quoteText={quoteText}
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

type ReviewHeaderProps = {
  intent: DecisionIntent;
};

function ReviewHeader({ intent }: ReviewHeaderProps) {
  return (
    <header className="mb-5 flex flex-col gap-3 rounded-[18px] border border-[var(--enki-line)] bg-[var(--enki-white)] p-4 shadow-[var(--enki-shadow-soft)] sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p className="text-xs font-bold uppercase tracking-[0.04em] text-[var(--enki-ink-600)]">Revisión de cotización</p>
        <h1 className="mt-1 text-2xl font-extrabold text-[var(--enki-ink-900)]">Soporte IT mensual</h1>
      </div>
      <Chip tone="neutral">{decisionIntentLabels[intent]}</Chip>
    </header>
  );
}

type QuoteInputProps = {
  intent: DecisionIntent;
  quoteText: string;
  onAnalyze: (quoteText: string) => void;
};

function QuoteInput({ intent, quoteText, onAnalyze }: QuoteInputProps) {
  return (
    <div className="grid gap-5 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
      <section className="rounded-[18px] border border-[var(--enki-line)] bg-[var(--enki-white)] p-5 shadow-[var(--enki-shadow-soft)]">
        <Chip tone="new">{decisionIntentLabels[intent]}</Chip>
        <h2 className="mt-5 text-[32px] font-extrabold leading-[38px]">Pegá la cotización que querés entender.</h2>
        <p className="mt-3 text-base leading-7 text-[var(--enki-ink-600)]">En este sprint Enki usa un fixture controlado para revisar el flujo. No conectamos backend ni inventamos comparabilidad.</p>
      </section>
      <QuoteComposer
        actionLabel="Analizar"
        compact
        emptyMessage="Pegá una cotización para analizarla."
        initialText={quoteText}
        onEvaluate={onAnalyze}
      />
    </div>
  );
}

type InterpretationSummaryProps = {
  interpretation: QuoteInterpretationView;
  onConfirm: () => void;
  onCorrect: () => void;
};

function InterpretationSummary({ interpretation, onConfirm, onCorrect }: InterpretationSummaryProps) {
  return (
    <div className="grid gap-5 lg:grid-cols-[1fr_360px]">
      <div className="space-y-5">
        <section className="rounded-[18px] border border-[var(--enki-line)] bg-[var(--enki-white)] p-5 shadow-[var(--enki-shadow-soft)]">
          <p className="text-xs font-bold uppercase tracking-[0.04em] text-[var(--enki-ink-600)]">Interpretación</p>
          <h2 className="mt-3 text-[32px] font-extrabold leading-[38px]">Esto es lo que entendimos.</h2>
          <p className="mt-3 text-base leading-7 text-[var(--enki-ink-600)]">Confirmalo si representa la cotización. Si algo no está bien, corregí el texto original.</p>
        </section>
        <DimensionList title="Qué entendimos" dimensions={interpretation.understood} />
        <DimensionList title="Lo que falta aclarar" dimensions={interpretation.missing} variant="missing" />
      </div>
      <aside className="space-y-5">
        <PriceDisplay label={interpretation.priceLabel} />
        <DecisionState state="indeterminate" />
        <div className="grid gap-3">
          <Button onClick={onConfirm}>Confirmar</Button>
          <Button variant="secondary" onClick={onCorrect}>Corregir</Button>
        </div>
      </aside>
    </div>
  );
}

type DecisionReadoutProps = {
  readout: DecisionReadoutView;
  onReviewAgain: () => void;
};

function DecisionReadout({ readout, onReviewAgain }: DecisionReadoutProps) {
  return (
    <div className="grid gap-5 lg:grid-cols-[1fr_360px]">
      <div className="space-y-5">
        <section className="rounded-[18px] border border-[var(--enki-line)] bg-[var(--enki-white)] p-5 shadow-[var(--enki-shadow-soft)]">
          <p className="text-xs font-bold uppercase tracking-[0.04em] text-[var(--enki-ink-600)]">¿Se puede comparar?</p>
          <h2 className="mt-3 text-[32px] font-extrabold leading-[38px]">{readout.summary}</h2>
          <p className="mt-3 text-base leading-7 text-[var(--enki-ink-600)]">Con lo que sabemos, el precio está identificado. La comparación todavía depende de datos que no aparecen en la cotización.</p>
        </section>
        <DimensionList title="Qué sabemos" dimensions={readout.known} />
        <DimensionList title="Qué puede cambiar la comparación" dimensions={readout.missing} variant="missing" />
      </div>
      <aside className="space-y-5">
        <DecisionState state={readout.state} description="Estado: información insuficiente." />
        <PriceDisplay eyebrow="Precio conocido" label={readout.priceLabel} />
        <EvidenceMeta sourceLabel="Sin evidencia externa conectada" freshnessLabel="Fixture local" />
        <section className="rounded-[14px] border border-[var(--enki-line)] bg-[var(--enki-teal-50)] p-4">
          <p className="text-xs font-bold uppercase tracking-[0.04em] text-[var(--enki-teal-700)]">Qué conviene hacer ahora</p>
          <p className="mt-2 text-sm font-semibold leading-6">{readout.nextAction}</p>
        </section>
        <Button variant="secondary" onClick={onReviewAgain}>Revisar texto</Button>
      </aside>
    </div>
  );
}