import Image from "next/image";

export function EnkiHeader() {
  return (
    <header>
      <div className="flex items-center justify-between px-6 pb-2.5 pt-3.5">
        <p className="font-mono text-sm font-semibold leading-none">9:41</p>
        <div className="flex items-center gap-1.5" aria-hidden="true">
          <Image src="/figma-assets/ios-signal.svg" alt="" width={18} height={18} priority />
          <Image src="/figma-assets/ios-wifi-signal.svg" alt="" width={18} height={18} priority />
          <Image src="/figma-assets/ios-battery-full.svg" alt="" width={26} height={18} priority />
        </div>
      </div>
      <div className="border-b border-[var(--enki-soft-line)] px-6 py-4">
        <p className="text-xl font-extrabold leading-none">Enki</p>
      </div>
    </header>
  );
}
