import { Chip } from "@/components/ui/chip";

type MissingDimensionProps = {
  label: string;
  importance?: string;
};

export function MissingDimension({ label, importance = "Importante" }: MissingDimensionProps) {
  return (
    <li className="flex items-center justify-between gap-3 rounded-[10px] border border-[var(--enki-amber-200)] bg-[var(--enki-amber-50)] px-3 py-2.5">
      <span className="text-sm font-semibold text-[var(--enki-ink-900)]">{label}</span>
      <Chip tone="attention">{importance}</Chip>
    </li>
  );
}