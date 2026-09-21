type EvidenceMetaProps = {
  sourceLabel: string;
  temporalLabel: string;
};

export function EvidenceMeta({ sourceLabel, temporalLabel }: EvidenceMetaProps) {
  return (
    <section className="rounded-[14px] border border-[var(--enki-line)] bg-[var(--enki-white)] p-4 shadow-[var(--enki-shadow-soft)]">
      <h2 className="text-sm font-extrabold text-[var(--enki-ink-900)]">Evidencia</h2>
      <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-[var(--enki-ink-600)]">Fuente</dt>
          <dd className="font-bold text-[var(--enki-ink-900)]">{sourceLabel}</dd>
        </div>
        <div>
          <dt className="text-[var(--enki-ink-600)]">Temporalidad</dt>
          <dd className="font-bold text-[var(--enki-ink-900)]">{temporalLabel}</dd>
        </div>
      </dl>
    </section>
  );
}