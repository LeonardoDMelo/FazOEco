import Link from "next/link";
import { OfferGrid } from "@/components/offers/OfferGrid";
import { bandLabel } from "@/lib/formatters";
import type { DiscountBand, OfferListItem } from "@/lib/types";

const TIERS: { band: DiscountBand; eyebrow: string }[] = [
  { band: "extreme", eyebrow: "Mega descontos" },
  { band: "high", eyebrow: "Altas ofertas" },
  { band: "medium", eyebrow: "Boas chances" },
];

export function DiscountTierSection({
  tiers,
}: {
  tiers: Partial<Record<DiscountBand, OfferListItem[]>>;
}) {
  return (
    <div className="space-y-14">
      {TIERS.map(({ band, eyebrow }) => {
        const offers = tiers[band] || [];
        if (!offers.length) return null;
        return (
          <section key={band} className="scroll-mt-28">
            <div className="mb-6 flex items-end justify-between gap-4">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.18em] text-accent-600">
                  {eyebrow}
                </p>
                <h2 className="mt-1 text-2xl font-bold text-neutral-950 sm:text-3xl">
                  {bandLabel(band)}
                </h2>
              </div>
              <Link
                href={`/busca?band=${band}&sort=discount_desc`}
                className="text-sm font-semibold text-brand-800 hover:text-accent-600 hover:underline"
              >
                Ver todas
              </Link>
            </div>
            <OfferGrid offers={offers} />
          </section>
        );
      })}
    </div>
  );
}
