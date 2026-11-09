import Link from "next/link";

export function AffiliateNoticeBar() {
  return (
    <div className="border-b border-neutral-800 bg-neutral-900 text-neutral-100">
      <div className="mx-auto flex max-w-6xl items-center justify-center gap-2 px-4 py-2 text-center text-xs sm:text-sm">
        <span>
          Este site contém links de afiliados. Podemos receber comissão sem custo
          extra para você.
        </span>
        <Link
          href="/transparencia"
          className="whitespace-nowrap font-semibold text-accent-400 underline underline-offset-2 hover:text-accent-300"
        >
          Saiba mais
        </Link>
      </div>
    </div>
  );
}
