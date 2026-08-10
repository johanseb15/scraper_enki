import Link from "next/link";

export function EnkiHeader() {
  return (
    <header className="border-b border-[var(--enki-soft-line)] bg-[color-mix(in_srgb,var(--enki-white)_86%,transparent)] backdrop-blur">
      <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-4 sm:px-6">
        <Link className="flex items-center gap-2 rounded-md outline-none focus-visible:ring-2 focus-visible:ring-[var(--enki-teal-600)]" href="/">
          <span className="relative size-8" aria-hidden="true">
            <span className="absolute left-1 top-2 size-4 rotate-45 rounded-[6px] border-2 border-[var(--enki-teal-600)]" />
            <span className="absolute right-1 top-2 size-4 rotate-45 rounded-[6px] border-2 border-[var(--enki-teal-400)]" />
          </span>
          <span className="text-xl font-extrabold text-[var(--enki-ink-900)]">Enki</span>
        </Link>
        <nav aria-label="Principal" className="hidden items-center gap-6 text-sm font-bold text-[var(--enki-ink-600)] sm:flex">
          <Link className="text-[var(--enki-teal-700)] underline decoration-[var(--enki-teal-400)] decoration-2 underline-offset-[18px]" href="/">Inicio</Link>
        </nav>
        <div className="flex items-center gap-2">
          <span className="hidden rounded-full bg-[var(--enki-teal-50)] px-3 py-1.5 text-xs font-bold text-[var(--enki-teal-700)] sm:inline-flex">Nuevo</span>
          <span className="grid size-9 place-items-center rounded-full bg-[var(--enki-amber-100)] text-xs font-extrabold text-[var(--enki-ink-900)]">AR</span>
        </div>
      </div>
    </header>
  );
}