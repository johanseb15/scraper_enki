import Image from "next/image";
import Link from "next/link";

type DecisionIntentOptionProps = {
  href: string;
  iconSrc: string;
  title: string;
  description: string;
};

export function DecisionIntentOption({
  href,
  iconSrc,
  title,
  description,
}: DecisionIntentOptionProps) {
  return (
    <Link
      className="group flex min-h-16 items-center gap-4 rounded-lg p-4 -mx-4 outline-none transition-colors hover:bg-[var(--enki-option-hover)] focus-visible:ring-2 focus-visible:ring-[var(--enki-accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--enki-bg)]"
      href={href}
    >
      <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-[var(--enki-question)]">
        <Image src={iconSrc} alt="" width={20} height={20} />
      </span>
      <span className="min-w-0 flex-1 text-[var(--enki-ink)]">
        <span className="block text-[15px] font-bold leading-normal">
          {title}
        </span>
        <span className="mt-1 block text-[13px] leading-normal">
          {description}
        </span>
      </span>
    </Link>
  );
}
