type BenchmarkRailProps = {
  min: number;
  q1: number;
  median: number;
  q3: number;
  max: number;
  userPrice?: number | null;
};

function money(value: number) {
  return `$${Math.round(value).toLocaleString("es-AR")}`;
}

function clampPercent(value: number, min: number, max: number) {
  if (max <= min) return 50;
  return Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100));
}

function centralPositionLabel(userPrice: number, q1: number, q3: number) {
  if (userPrice < q1) return "Por debajo del intervalo central observado";
  if (userPrice > q3) return "Por encima del intervalo central observado";
  return "Dentro del intervalo central observado";
}

export function BenchmarkRail({
  min,
  q1,
  median,
  q3,
  max,
  userPrice = null,
}: BenchmarkRailProps) {
  if (
    ![min, q1, median, q3, max].every(Number.isFinite) ||
    !(min <= q1 && q1 <= median && median <= q3 && q3 <= max) ||
    max <= min
  ) {
    return null;
  }

  const validUserPrice =
    userPrice != null && Number.isFinite(userPrice) ? userPrice : null;

  const q1Position = clampPercent(q1, min, max);
  const q3Position = clampPercent(q3, min, max);
  const medianPosition = clampPercent(median, min, max);
  const userPosition =
    validUserPrice != null
      ? clampPercent(validUserPrice, min, max)
      : null;
  const positionLabel =
    validUserPrice != null
      ? centralPositionLabel(validUserPrice, q1, q3)
      : null;

  const accessibleSummary = [
    `Rango comparable de precios publicados de ${money(min)} a ${money(max)}.`,
    `Intervalo central observado de ${money(q1)} a ${money(q3)}.`,
    `Mediana ${money(median)}.`,
    validUserPrice != null
      ? `Precio consultado ${money(validUserPrice)}${positionLabel ? `: ${positionLabel.toLowerCase()}` : ""}.`
      : null,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <section
      className="border-y border-[var(--enki-line)] py-5"
      aria-label={accessibleSummary}
    >
      <div className="flex items-baseline justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.04em] text-[var(--enki-ink-600)]">
            Rango comparable de precios publicados
          </p>
          <p className="mt-1 text-sm text-[var(--enki-ink-600)]">
            La banda marca el intervalo central observado; no es un precio recomendado.
          </p>
        </div>
      </div>

      <div className="relative mt-5 h-64 sm:hidden" aria-hidden="true">
        <div className="absolute bottom-0 left-8 top-0 w-[2px] bg-[var(--enki-ink-500)]" />

        <div
          className="absolute left-[26px] w-3 bg-[var(--enki-teal-100)]"
          style={{
            top: `${100 - q3Position}%`,
            height: `${q3Position - q1Position}%`,
          }}
        />

        <div
          className="absolute left-[22px] h-[2px] w-5 bg-[var(--enki-ink-900)]"
          style={{
            top: `${100 - medianPosition}%`,
            transform: "translateY(-50%)",
          }}
        />

        {userPosition != null ? (
          <div
            className="absolute left-5 size-6 rounded-full border-2 border-[var(--enki-teal-700)] bg-[var(--enki-white)]"
            style={{
              top: `${100 - userPosition}%`,
              transform: "translateY(-50%)",
            }}
          />
        ) : null}

        <div className="absolute left-14 top-0 font-mono text-xs tabular-nums text-[var(--enki-ink-600)]">
          {money(max)}
        </div>
        <div className="absolute bottom-0 left-14 font-mono text-xs tabular-nums text-[var(--enki-ink-600)]">
          {money(min)}
        </div>
      </div>

      <div className="relative mt-5 hidden h-16 sm:block" aria-hidden="true">
        <div className="absolute left-0 right-0 top-7 h-[2px] bg-[var(--enki-ink-500)]" />

        <div
          className="absolute top-[22px] h-3 bg-[var(--enki-teal-100)]"
          style={{
            left: `${q1Position}%`,
            width: `${q3Position - q1Position}%`,
          }}
        />

        <div
          className="absolute top-[18px] h-5 w-[2px] bg-[var(--enki-ink-900)]"
          style={{
            left: `${medianPosition}%`,
            transform: "translateX(-50%)",
          }}
        />

        {userPosition != null ? (
          <div
            className="absolute top-[17px] size-6 rounded-full border-2 border-[var(--enki-teal-700)] bg-[var(--enki-white)]"
            style={{
              left: `${userPosition}%`,
              transform: "translateX(-50%)",
            }}
          />
        ) : null}

        <div className="absolute bottom-0 left-0 font-mono text-xs tabular-nums text-[var(--enki-ink-600)]">
          {money(min)}
        </div>
        <div className="absolute bottom-0 right-0 font-mono text-xs tabular-nums text-[var(--enki-ink-600)]">
          {money(max)}
        </div>
      </div>

      <div className="mt-3 grid gap-1 text-sm text-[var(--enki-ink-600)] sm:grid-cols-2">
        <p>
          Intervalo central observado:{" "}
          <span className="font-mono tabular-nums text-[var(--enki-ink-900)]">
            {money(q1)} – {money(q3)}
          </span>
        </p>
        <p className="font-mono tabular-nums text-[var(--enki-ink-900)]">
          Mediana: {money(median)}
        </p>
      </div>

      {validUserPrice != null && positionLabel ? (
        <div className="mt-4 border-l-2 border-[var(--enki-teal-700)] pl-3">
          <p className="text-xs font-bold uppercase tracking-[0.04em] text-[var(--enki-ink-600)]">
            Precio consultado
          </p>
          <p className="mt-1 font-mono text-xl font-extrabold tabular-nums text-[var(--enki-ink-900)]">
            {money(validUserPrice)}
          </p>
          <p className="mt-1 text-sm font-semibold text-[var(--enki-ink-900)]">
            {positionLabel}
          </p>
        </div>
      ) : null}
    </section>
  );
}