import { DecisionIntentOption } from "@/components/enki/DecisionIntentOption";
import { EnkiHeader } from "@/components/enki/EnkiHeader";
import { HomeIntro } from "@/components/enki/HomeIntro";

const decisionIntents = [
  {
    href: "/cotizacion?intent=sending_quote",
    iconSrc: "/figma-assets/file-text.svg",
    title: "Estoy por enviar una cotización",
    description: "Quiero revisar lo que voy a cobrar.",
  },
  {
    href: "/cotizacion?intent=received_quote",
    iconSrc: "/figma-assets/inbox.svg",
    title: "Recibí una propuesta",
    description: "Quiero entender lo que me están ofreciendo.",
  },
];

export default function Home() {
  return (
    <main className="min-h-dvh bg-[var(--enki-page)] text-[var(--enki-ink)]">
      <section className="mx-auto flex min-h-dvh w-full max-w-[402px] flex-col overflow-hidden border-x border-[var(--enki-line)] bg-[var(--enki-bg)] sm:my-6 sm:min-h-[874px] sm:rounded-[18px] sm:border">
        <div className="flex flex-1 flex-col">
          <EnkiHeader />
          <div className="flex flex-1 flex-col px-6 py-6">
            <HomeIntro />
            <div className="mt-6">
              <p className="font-mono text-xs font-semibold uppercase leading-none tracking-normal">¿Qué tenés entre manos?</p>
              <div className="mt-5 flex flex-col gap-6">
                {decisionIntents.map((intent) => (
                  <DecisionIntentOption key={intent.href} {...intent} />
                ))}
              </div>
            </div>
          </div>
        </div>
        <div className="px-0 pb-0">
          <div aria-hidden="true" className="mx-auto h-[5px] w-[134px] rounded-full bg-[var(--enki-home-indicator)]" />
          <div aria-hidden="true" className="mt-[61px] h-[3px] w-[52px] bg-[var(--enki-accent)]" />
          <div aria-hidden="true" className="mx-auto mt-[53px] h-px w-[88%] bg-[var(--enki-line)]" />
          <div aria-hidden="true" className="mx-auto mt-[55px] h-px w-[88%] bg-[var(--enki-line)]" />
          <p className="mt-[55px] max-w-[354px] text-xs leading-[17.4px] text-[var(--enki-muted)]">Sin registro para empezar. Primero entendé la decisión; después elegís cuánto profundizar.</p>
        </div>
      </section>
    </main>
  );
}