"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Chip } from "@/components/ui/chip";
import { DecisionState } from "@/components/enki/decision-state";
import { DimensionList } from "@/components/enki/dimension-list";
import { EvidenceMeta } from "@/components/enki/evidence-meta";
import { PriceDisplay } from "@/components/enki/price-display";
import { decisionIntentLabels } from "@/features/decision/decision-intent";
import { supportQuoteText } from "@/features/decision/fixtures/support-quote";
import { QuoteComposer } from "@/features/decision/components/QuoteComposer";
import { analyzePricingQuery } from "@/features/decision/decision-api";
import type {
  DecisionIntent,
  DecisionPricingResponse,
  DecisionReadoutState,
  InterpretationAttribute,
} from "@/features/decision/types";

type FlowStep = "quote" | "interpretation" | "readout";

type DecisionReviewFlowProps = {
  initialIntent: DecisionIntent;
  initialQuoteText?: string;
};

function money(value: number | null | undefined, currency = "ARS") {
  if (value == null) return "—";
  if (currency !== "ARS") return `${value.toLocaleString("es-AR")} ${currency}`;
  return `$${Math.round(value).toLocaleString("es-AR")}`;
}

function humanize(value: string | null | undefined) {
  if (!value || value === "UNKNOWN") return null;
  return value.toLowerCase().replaceAll("_", " ");
}

function buildUnderstood(result: DecisionPricingResponse): InterpretationAttribute[] {
  const parsed = result.parsed;
  const items: string[] = [];

  if (parsed.canonical_services.length) {
    items.push(
      parsed.canonical_services
        .map((service) => humanize(service))
        .filter(Boolean)
        .join(" + "),
    );
  }

  if (parsed.price.value != null) {
    const cadence = humanize(parsed.price.type);
    items.push(
      cadence && cadence !== "exact"
        ? `${money(parsed.price.value, parsed.price.currency)} · ${cadence}`
        : money(parsed.price.value, parsed.price.currency),
    );
  }

  if (parsed.geography.city || parsed.geography.province) {
    items.push(
      [parsed.geography.city, parsed.geography.province]
        .filter(Boolean)
        .join(", "),
    );
  }

  const modality = humanize(parsed.modality);
  if (modality) items.push(`Modalidad: ${modality}`);

  const partsScope = humanize(parsed.parts_scope);
  if (partsScope) items.push(`Alcance: ${partsScope}`);

  return items.filter(Boolean).map((label) => ({ label }));
}

function buildMissing(result: DecisionPricingResponse): InterpretationAttribute[] {
  const question =
    result.clarification_question ??
    result.parsed.clarification_question ??
    null;

  if (question) return [{ label: question }];

  if (result.status === "UNSUPPORTED_QUERY" && result.unsupported_reason) {
    return [{ label: `Fuera del alcance actual: ${humanize(result.unsupported_reason)}` }];
  }

  return [];
}

function priceLabel(result: DecisionPricingResponse) {
  const price = result.parsed.price;
  if (price.value != null) return money(price.value, price.currency);
  if (price.min != null && price.max != null) {
    return `${money(price.min, price.currency)} – ${money(price.max, price.currency)}`;
  }
  return "Precio no identificado";
}

function readoutState(result: DecisionPricingResponse): DecisionReadoutState {
  if (result.status === "DECISION_READY" || result.status === "RANGE_READY") {
    return "potentially_comparable";
  }
  if (result.status === "NO_EVIDENCE" || result.status === "UNSUPPORTED_QUERY") {
    return "not_comparable";
  }
  return "indeterminate";
}

export function DecisionReviewFlow({
  initialIntent,
  initialQuoteText = supportQuoteText,
}: DecisionReviewFlowProps) {
  const [step, setStep] = useState<FlowStep>("quote");
  const [quoteText, setQuoteText] = useState(initialQuoteText);
  const [result, setResult] = useState<DecisionPricingResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  async function analyzeQuote(nextQuoteText: string) {
    setQuoteText(nextQuoteText);
    setIsLoading(true);
    setApiError(null);

    try {
      const nextResult = await analyzePricingQuery(nextQuoteText);
      setResult(nextResult);
      setStep("interpretation");
    } catch (error) {
      setApiError(
        error instanceof Error
          ? error.message
          : "No pudimos conectar con Enki API.",
      );
    } finally {
      setIsLoading(false);
    }
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
            isLoading={isLoading}
            apiError={apiError}
          />
        ) : null}

        {step === "interpretation" && result ? (
          <InterpretationSummary
            result={result}
            onConfirm={() => setStep("readout")}
            onCorrect={() => setStep("quote")}
          />
        ) : null}

        {step === "readout" && result ? (
          <DecisionReadout
            result={result}
            onReviewAgain={() => setStep("quote")}
          />
        ) : null}
      </section>
    </main>
  );
}

function ReviewHeader({ intent }: { intent: DecisionIntent }) {
  return (
    <header className="mb-5 flex flex-col gap-3 rounded-[18px] border border-[var(--enki-line)] bg-[var(--enki-white)] p-4 shadow-[var(--enki-shadow-soft)] sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p className="text-xs font-bold uppercase tracking-[0.04em] text-[var(--enki-ink-600)]">
          Enki Decision
        </p>
        <h1 className="mt-1 text-2xl font-extrabold text-[var(--enki-ink-900)]">
          Revisá un precio con evidencia real
        </h1>
      </div>
      <Chip tone="neutral">{decisionIntentLabels[intent]}</Chip>
    </header>
  );
}

function QuoteInput({
  intent,
  quoteText,
  onAnalyze,
  isLoading,
  apiError,
}: {
  intent: DecisionIntent;
  quoteText: string;
  onAnalyze: (quoteText: string) => void;
  isLoading: boolean;
  apiError: string | null;
}) {
  return (
    <div className="grid gap-5 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
      <section className="rounded-[18px] border border-[var(--enki-line)] bg-[var(--enki-white)] p-5 shadow-[var(--enki-shadow-soft)]">
        <Chip tone="new">{decisionIntentLabels[intent]}</Chip>
        <h2 className="mt-5 text-[32px] font-extrabold leading-[38px]">
          Contale a Enki qué te quieren cobrar o cuánto pensás cobrar.
        </h2>
        <p className="mt-3 text-base leading-7 text-[var(--enki-ink-600)]">
          La consulta se procesa con el parser y el motor de evidencia del backend real.
          Si falta un dato para comparar de forma segura, Enki te lo va a pedir.
        </p>
        <div className="mt-5 rounded-[14px] bg-[var(--enki-teal-50)] p-4">
          <p className="text-xs font-bold uppercase tracking-[0.04em] text-[var(--enki-teal-700)]">
            Probá este caso
          </p>
          <p className="mt-2 text-sm font-semibold leading-6">
            “Me quieren cobrar 35 lucas la hora por soporte remoto, ¿está bien?”
          </p>
        </div>
        {isLoading ? (
          <p className="mt-4 text-sm font-bold text-[var(--enki-teal-700)]">
            Analizando con Enki…
          </p>
        ) : null}
        {apiError ? (
          <p className="mt-4 text-sm font-semibold text-[var(--enki-amber-700)]">
            {apiError}. Verificá que FastAPI esté corriendo en el puerto 8000.
          </p>
        ) : null}
      </section>
      <QuoteComposer
        actionLabel={isLoading ? "Analizando" : "Analizar"}
        compact
        emptyMessage="Escribí una consulta para analizarla."
        initialText={quoteText}
        onEvaluate={onAnalyze}
      />
    </div>
  );
}

function InterpretationSummary({
  result,
  onConfirm,
  onCorrect,
}: {
  result: DecisionPricingResponse;
  onConfirm: () => void;
  onCorrect: () => void;
}) {
  const understood = buildUnderstood(result);
  const missing = buildMissing(result);

  return (
    <div className="grid gap-5 lg:grid-cols-[1fr_360px]">
      <div className="space-y-5">
        <section className="rounded-[18px] border border-[var(--enki-line)] bg-[var(--enki-white)] p-5 shadow-[var(--enki-shadow-soft)]">
          <p className="text-xs font-bold uppercase tracking-[0.04em] text-[var(--enki-ink-600)]">
            Interpretación real
          </p>
          <h2 className="mt-3 text-[32px] font-extrabold leading-[38px]">
            Esto es lo que Enki entendió.
          </h2>
          <p className="mt-3 text-base leading-7 text-[var(--enki-ink-600)]">
            Revisá la interpretación antes de mirar la evidencia.
          </p>
        </section>

        <DimensionList title="Qué entendimos" dimensions={understood} />

        {missing.length ? (
          <DimensionList
            title="Lo que falta aclarar"
            dimensions={missing}
            variant="missing"
          />
        ) : null}
      </div>

      <aside className="space-y-5">
        <PriceDisplay label={priceLabel(result)} />
        <DecisionState state={readoutState(result)} />
        <div className="grid gap-3">
          <Button onClick={onConfirm}>Ver resultado</Button>
          <Button variant="secondary" onClick={onCorrect}>
            Corregir consulta
          </Button>
        </div>
      </aside>
    </div>
  );
}

function DecisionReadout({
  result,
  onReviewAgain,
}: {
  result: DecisionPricingResponse;
  onReviewAgain: () => void;
}) {
  const evidence = result.evidence;
  const known: InterpretationAttribute[] = [];

  if (evidence) {
    known.push(
      { label: `Rango observado: ${money(evidence.min_ars)} – ${money(evidence.max_ars)}` },
      { label: `Mediana: ${money(evidence.median_ars)}` },
      { label: `${evidence.observations_n} precios de ${evidence.providers_n} proveedores` },
      { label: `Confianza: ${evidence.evidence_confidence}` },
    );
  } else {
    known.push(...buildUnderstood(result));
  }

  const missing = buildMissing(result);

  return (
    <div className="grid gap-5 lg:grid-cols-[1fr_360px]">
      <div className="space-y-5">
        <section className="rounded-[18px] border border-[var(--enki-line)] bg-[var(--enki-white)] p-5 shadow-[var(--enki-shadow-soft)]">
          <p className="text-xs font-bold uppercase tracking-[0.04em] text-[var(--enki-ink-600)]">
            Resultado Enki
          </p>
          <h2 className="mt-3 text-[32px] font-extrabold leading-[38px]">
            {result.headline}
          </h2>
          <p className="mt-3 text-base leading-7 text-[var(--enki-ink-600)]">
            {result.summary}
          </p>
          {result.evidence_line ? (
            <p className="mt-4 text-sm font-bold leading-6">
              {result.evidence_line}
            </p>
          ) : null}
        </section>

        <DimensionList
          title={evidence ? "Evidencia comparable" : "Qué entendimos"}
          dimensions={known}
        />

        {missing.length ? (
          <DimensionList
            title="Qué falta para avanzar"
            dimensions={missing}
            variant="missing"
          />
        ) : null}
      </div>

      <aside className="space-y-5">
        <DecisionState
          state={readoutState(result)}
          description={`Estado: ${result.status}.`}
        />
        <PriceDisplay eyebrow="Precio consultado" label={priceLabel(result)} />
        <EvidenceMeta
          sourceLabel={
            evidence
              ? `${evidence.providers_n} proveedores · ${evidence.observations_n} observaciones`
              : "Sin cohorte comparable"
          }
          freshnessLabel={
            evidence
              ? `${evidence.price_scope} · ${evidence.commercial_context}`
              : "Enki retuvo la decisión"
          }
        />
        {result.caveat ? (
          <section className="rounded-[14px] border border-[var(--enki-line)] bg-[var(--enki-teal-50)] p-4">
            <p className="text-xs font-bold uppercase tracking-[0.04em] text-[var(--enki-teal-700)]">
              Nota de evidencia
            </p>
            <p className="mt-2 text-sm font-semibold leading-6">
              {result.caveat}
            </p>
          </section>
        ) : null}
        <Button variant="secondary" onClick={onReviewAgain}>
          Revisar otra consulta
        </Button>
      </aside>
    </div>
  );
}
