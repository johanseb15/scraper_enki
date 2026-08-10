"use client";

import { useRouter } from "next/navigation";
import { Chip } from "@/components/ui/chip";
import { DecisionIntentOption } from "@/components/enki/DecisionIntentOption";
import { EnkiHeader } from "@/components/enki/EnkiHeader";
import { HomeIntro } from "@/components/enki/HomeIntro";
import { QuoteComposer } from "@/features/decision/components/QuoteComposer";

const decisionIntents = [
  { href: "/cotizacion?intent=sending_quote", iconSrc: "/figma-assets/file-text.svg", title: "Estoy por enviar una cotización", description: "Quiero revisar lo que voy a cobrar." },
  { href: "/cotizacion?intent=received_quote", iconSrc: "/figma-assets/inbox.svg", title: "Recibí una propuesta", description: "Quiero entender lo que me están ofreciendo." },
];

const demoExamples = [
  { title: "Soporte IT mensual", status: "Información insuficiente" },
  { title: "Servicio técnico", status: "Lo que falta aclarar" },
  { title: "Equipamiento", status: "Interpretación inicial" },
];

export default function Home() {
  const router = useRouter();

  function startEvaluation(quoteText: string) {
    window.sessionStorage.setItem("enki.quoteDraft", quoteText);
    router.push("/cotizacion?intent=sending_quote");
  }

  return (
    <main className="min-h-dvh bg-[var(--enki-page)] text-[var(--enki-ink-900)]">
      <EnkiHeader />
      <section className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 sm:py-12">
        <div className="grid gap-8 lg:grid-cols-[1fr_320px] lg:items-center">
          <div>
            <HomeIntro />
            <div className="mt-7"><QuoteComposer onEvaluate={startEvaluation} /></div>
          </div>
          <DocumentClarityVisual />
        </div>

        <section className="mt-10 grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-[18px] border border-[var(--enki-line)] bg-[var(--enki-white)] p-4 shadow-[var(--enki-shadow-soft)] sm:p-5">
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-base font-extrabold">Elegí cómo querés revisar</h2>
              <Chip tone="new">Flujo guiado</Chip>
            </div>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {decisionIntents.map((intent) => <DecisionIntentOption key={intent.href} {...intent} />)}
            </div>
          </div>

          <div className="rounded-[18px] border border-[var(--enki-line)] bg-[var(--enki-white)] p-4 shadow-[var(--enki-shadow-soft)] sm:p-5">
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-base font-extrabold">Ejemplos de análisis</h2>
              <a className="text-sm font-bold text-[var(--enki-teal-700)]" href="/cotizacion?intent=received_quote">Probar</a>
            </div>
            <div className="mt-4 space-y-3">
              {demoExamples.map((example) => (
                <article className="flex items-center justify-between gap-3 rounded-[12px] border border-[var(--enki-soft-line)] p-3" key={example.title}>
                  <div>
                    <h3 className="text-sm font-bold">{example.title}</h3>
                    <p className="mt-1 text-xs text-[var(--enki-ink-600)]">Caso demo, sin historial guardado</p>
                  </div>
                  <Chip tone="attention">{example.status}</Chip>
                </article>
              ))}
            </div>
          </div>
        </section>
      </section>
    </main>
  );
}

function DocumentClarityVisual() {
  return (
    <div className="relative hidden min-h-[260px] rounded-[24px] bg-[linear-gradient(135deg,var(--enki-amber-100),var(--enki-teal-50))] p-8 lg:block" aria-hidden="true">
      <div className="absolute left-9 top-14 h-36 w-28 rotate-[-5deg] rounded-[16px] bg-[var(--enki-white)] shadow-[var(--enki-shadow-soft)]" />
      <div className="absolute right-10 top-8 h-44 w-32 rounded-[18px] bg-[var(--enki-white)] shadow-[var(--enki-shadow-composer)]">
        <div className="m-5 h-3 w-14 rounded-full bg-[var(--enki-teal-400)]" />
        <div className="mx-5 mt-5 space-y-3"><div className="h-2 rounded-full bg-[var(--enki-stone-100)]" /><div className="h-2 rounded-full bg-[var(--enki-stone-100)]" /><div className="h-2 w-16 rounded-full bg-[var(--enki-stone-100)]" /></div>
      </div>
      <div className="absolute bottom-10 right-16 grid size-12 place-items-center rounded-full bg-[var(--enki-teal-600)] text-2xl font-black text-white">✓</div>
    </div>
  );
}
