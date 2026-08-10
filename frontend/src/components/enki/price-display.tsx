type PriceDisplayProps = {
  label: string;
  eyebrow?: string;
};

export function PriceDisplay({ label, eyebrow = "Precio identificado" }: PriceDisplayProps) {
  return (
    <section className="rounded-[14px] border border-[var(--enki-line)] bg-[var(--enki-white)] p-4 shadow-[var(--enki-shadow-soft)]">
      <p className="text-xs font-bold uppercase tracking-[0.04em] text-[var(--enki-ink-600)]">{eyebrow}</p>
      <p className="mt-2 font-mono text-2xl font-extrabold tabular-nums text-[var(--enki-ink-900)]">{label}</p>
    </section>
  );
}