import type { ReactNode } from "react";

type ChipTone = "neutral" | "positive" | "attention" | "new";

type ChipProps = {
  tone?: ChipTone;
  children: ReactNode;
  className?: string;
};

const tones: Record<ChipTone, string> = {
  neutral: "bg-[var(--enki-stone-100)] text-[var(--enki-ink-600)]",
  positive: "bg-[var(--enki-teal-50)] text-[var(--enki-teal-700)]",
  attention: "bg-[var(--enki-amber-50)] text-[var(--enki-amber-700)]",
  new: "bg-[var(--enki-teal-100)] text-[var(--enki-teal-700)]",
};

export function Chip({ tone = "neutral", children, className = "" }: ChipProps) {
  return (
    <span className={`inline-flex min-h-7 items-center rounded-full px-3 text-xs font-bold ${tones[tone]} ${className}`}>
      {children}
    </span>
  );
}