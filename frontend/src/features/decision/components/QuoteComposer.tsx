"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Chip } from "@/components/ui/chip";

type QuoteComposerProps = {
  initialText?: string;
  actionLabel?: string;
  emptyMessage?: string;
  compact?: boolean;
  onEvaluate: (quoteText: string) => void;
};

const quickExamples = [
  "Soporte IT mensual",
  "Servicio técnico",
  "Proyecto de infraestructura",
  "Equipamiento",
];

export function QuoteComposer({
  initialText = "",
  actionLabel = "Evaluar",
  emptyMessage = "Pegá una cotización para evaluarla.",
  compact = false,
  onEvaluate,
}: QuoteComposerProps) {
  const [quoteText, setQuoteText] = useState(initialText);
  const [showEmptyMessage, setShowEmptyMessage] = useState(false);

  function submitQuote() {
    if (!quoteText.trim()) {
      setShowEmptyMessage(true);
      return;
    }

    setShowEmptyMessage(false);
    onEvaluate(quoteText);
  }

  return (
    <section className={`rounded-[22px] border border-[var(--enki-line)] bg-[var(--enki-white)] shadow-[var(--enki-shadow-composer)] ${compact ? "p-4" : "p-4 sm:p-6"}`}>
      <label className="sr-only" htmlFor="quote-composer">
        Cotización a evaluar
      </label>
      <textarea
        className={`${compact ? "min-h-[170px]" : "min-h-[150px] sm:min-h-[138px]"} w-full resize-none bg-transparent text-base leading-6 text-[var(--enki-ink-900)] outline-none placeholder:text-[var(--enki-ink-500)]`}
        id="quote-composer"
        placeholder="Pegá una cotización o describí lo que querés evaluar"
        value={quoteText}
        onChange={(event) => setQuoteText(event.target.value)}
      />

      {showEmptyMessage ? (
        <p className="mt-2 text-sm font-semibold text-[var(--enki-amber-700)]">{emptyMessage}</p>
      ) : null}

      <div className="mt-4 flex flex-col gap-4 border-t border-[var(--enki-soft-line)] pt-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap gap-2" aria-label="Ejemplos rápidos">
          {quickExamples.map((example) => (
            <Chip key={example}>{example}</Chip>
          ))}
        </div>
        <Button className="sm:min-w-[124px]" onClick={submitQuote}>
          {actionLabel} →
        </Button>
      </div>
    </section>
  );
}