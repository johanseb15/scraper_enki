import type { DecisionReadoutState } from "@/features/decision/types";
import { Chip } from "@/components/ui/chip";

type DecisionStateProps = {
  state: DecisionReadoutState;
  description?: string;
};

const stateCopy: Record<DecisionReadoutState, { label: string; tone: "positive" | "attention" | "neutral"; description: string }> = {
  potentially_comparable: {
    label: "Orientación posible",
    tone: "positive",
    description: "Podemos orientarte con referencias parecidas.",
  },
  not_comparable: {
    label: "No comparable todavía",
    tone: "attention",
    description: "Estas propuestas no incluyen lo mismo.",
  },
  indeterminate: {
    label: "Información insuficiente",
    tone: "attention",
    description: "Nos falta información para compararlo bien.",
  },
};

export function DecisionState({ state, description }: DecisionStateProps) {
  const copy = stateCopy[state];

  return (
    <section className="rounded-[14px] border border-[var(--enki-amber-200)] bg-[var(--enki-amber-50)] p-4">
      <div className="flex items-start gap-3">
        <span aria-hidden="true" className="mt-0.5 grid size-8 shrink-0 place-items-center rounded-full bg-[var(--enki-amber-400)] text-[var(--enki-ink-900)]">
          !
        </span>
        <div className="min-w-0">
          <Chip tone={copy.tone}>{copy.label}</Chip>
          <p className="mt-2 text-sm font-bold leading-5 text-[var(--enki-ink-900)]">
            {description ?? copy.description}
          </p>
        </div>
      </div>
    </section>
  );
}