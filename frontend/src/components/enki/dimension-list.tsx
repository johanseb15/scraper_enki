import { MissingDimension } from "@/components/enki/missing-dimension";

type DimensionListProps = {
  title: string;
  dimensions: { label: string }[];
  variant?: "known" | "missing";
};

export function DimensionList({ title, dimensions, variant = "known" }: DimensionListProps) {
  return (
    <section className="rounded-[14px] border border-[var(--enki-line)] bg-[var(--enki-white)] p-4 shadow-[var(--enki-shadow-soft)]">
      <h2 className="text-sm font-extrabold text-[var(--enki-ink-900)]">{title}</h2>
      {variant === "missing" ? (
        <ul className="mt-3 space-y-2">
          {dimensions.map((dimension) => (
            <MissingDimension key={dimension.label} label={dimension.label} />
          ))}
        </ul>
      ) : (
        <ul className="mt-3 flex flex-wrap gap-2">
          {dimensions.map((dimension) => (
            <li className="rounded-full bg-[var(--enki-teal-50)] px-3 py-2 text-sm font-semibold text-[var(--enki-teal-700)]" key={dimension.label}>
              {dimension.label}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}