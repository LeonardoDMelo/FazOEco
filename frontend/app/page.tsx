import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { DiscountTierSection } from "@/components/offers/DiscountTierSection";
import { OfferGrid } from "@/components/offers/OfferGrid";
import { JsonLd } from "@/components/seo/JsonLd";
import { Button } from "@/components/ui/Button";
import { getFeaturedOffers, getOffers } from "@/lib/api";
import {
  buildPageMetadata,
  homeJsonLd,
  itemListJsonLd,
} from "@/lib/seo";
import type { DiscountBand, OfferListItem } from "@/lib/types";

export const revalidate = 60;

export const metadata: Metadata = buildPageMetadata({
  title: "Ofertas e Afiliados com Transparência",
  description:
    "Compare descontos reais com ranking de qualidade, faixas dinâmicas e links de afiliados transparentes no FazOEco.",
  path: "/",
});

async function loadTier(): Promise<Partial<Record<DiscountBand, OfferListItem[]>>> {
  const bands: DiscountBand[] = ["extreme", "high", "medium"];
  const entries = await Promise.all(
    bands.map(async (band) => {
      const page = await getOffers({
        band,
        sort: "discount_desc",
        page_size: 4,
      });
      return [band, page.items] as const;
    }),
  );
  return Object.fromEntries(entries);
}

export default async function HomePage() {
  const [ranking, tiers] = await Promise.all([
    getOffers({ sort: "ranking_desc", page_size: 8 }),
    loadTier(),
  ]);
  const featured = await getFeaturedOffers("high", 4);
  const highlightOffers = ranking.items.length ? ranking.items : featured.items;

  return (
    <>
      <JsonLd
        data={[
          homeJsonLd(),
          itemListJsonLd(highlightOffers, "Destaques do ranking FazOEco"),
        ]}
      />

      <section className="relative overflow-hidden border-b border-brand-900/10">
        <div
          aria-hidden
          className="absolute inset-0 bg-[linear-gradient(135deg,#052e16_0%,#14532d_45%,#0f766e_100%)]"
        />
        <div
          aria-hidden
          className="absolute inset-0 opacity-30 bg-[radial-gradient(circle_at_20%_20%,rgba(255,255,255,0.25),transparent_35%),radial-gradient(circle_at_80%_10%,rgba(134,239,172,0.2),transparent_30%)]"
        />
        <div className="relative mx-auto flex min-h-[78vh] max-w-6xl flex-col justify-center px-4 py-20 text-white">
          <p className="animate-fade-up text-sm font-semibold uppercase tracking-[0.22em] text-emerald-200">
            Portal de ofertas inteligentes
          </p>
          <h1 className="animate-fade-up-delay mt-4 max-w-3xl text-5xl font-bold tracking-tight text-balance sm:text-6xl lg:text-7xl">
            FazOEco
          </h1>
          <p className="animate-fade-up-delay-2 mt-5 max-w-xl text-lg leading-relaxed text-emerald-50/90">
            Descontos reais, ranking de qualidade e links de afiliados com
            transparência — para você clicar com confiança.
          </p>
          <div className="animate-fade-up-delay-2 mt-8 flex flex-wrap gap-3">
            <Button
              href="/busca?sort=discount_desc"
              className="bg-white text-brand-800 hover:bg-emerald-50"
            >
              Ver ofertas em alta
              <ArrowRight className="h-4 w-4" />
            </Button>
            <Button
              href="/transparencia"
              variant="secondary"
              className="border-white/30 bg-transparent text-white hover:border-white hover:bg-white/10"
            >
              Como funcionam os afiliados
            </Button>
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-6xl space-y-16 px-4 py-14">
        <section>
          <div className="mb-6 flex items-end justify-between gap-4">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-brand-600">
                Destaques
              </p>
              <h2 className="mt-1 text-2xl font-bold text-slate-900 sm:text-3xl">
                Melhores do ranking
              </h2>
            </div>
            <Link
              href="/busca?sort=ranking_desc"
              className="text-sm font-semibold text-brand-700 hover:underline"
            >
              Ver ranking completo
            </Link>
          </div>
          <OfferGrid
            offers={highlightOffers}
            emptyMessage="Ainda não há ofertas aprovadas. Em breve novos descontos aparecerão aqui."
          />
        </section>

        <DiscountTierSection tiers={tiers} />
      </div>
    </>
  );
}
