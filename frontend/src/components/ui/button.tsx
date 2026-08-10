import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  children: ReactNode;
};

const variants: Record<ButtonVariant, string> = {
  primary:
    "bg-[var(--enki-teal-600)] text-white shadow-[var(--enki-shadow-action)] hover:bg-[var(--enki-teal-700)]",
  secondary:
    "border border-[var(--enki-line)] bg-[var(--enki-white)] text-[var(--enki-ink-900)] hover:bg-[var(--enki-stone-50)]",
  ghost:
    "text-[var(--enki-teal-700)] hover:bg-[var(--enki-teal-50)]",
};

export function Button({
  variant = "primary",
  className = "",
  children,
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      className={`inline-flex min-h-11 items-center justify-center rounded-[10px] px-5 text-sm font-bold outline-none transition focus-visible:ring-2 focus-visible:ring-[var(--enki-teal-600)] focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60 ${variants[variant]} ${className}`}
      type={type}
      {...props}
    >
      {children}
    </button>
  );
}