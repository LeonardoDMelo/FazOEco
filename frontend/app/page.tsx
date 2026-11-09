import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { DiscountTierSection } from "@/components/offers/DiscountTierSection";
import { OfferGrid } from "@/components/offers/OfferGrid";
import { JsonLd } from "@/components/seo/JsonLd";
import { ApiStatus } from "@/components/ui/ApiStatus";
import { BrandMark } from "@/components/layout/BrandMark";
import { Button } from "@/components/ui/Button";
import { loadHomeShowcase } from "@/lib/api";
import { buildPageMetadata, homeJsonLd, itemListJsonLd } from "@/lib/seo";

export const revalidate = 60;

export const metadata: Metadata = buildPageMetadata({
  title: "Ofertas e Afiliados com Transparência",
  description:
    "Compare descontos reais com ranking de qualidade, faixas dinâmicas e links de afiliados transparentes no Echonomiza.",
  path: "/",
});

export default async function HomePage() {
  const showcase = await loadHomeShowcase();
  const highlightOffers = showcase.data.ranking;

  return (
    <>
      <JsonLd
        data={[
          homeJsonLd(),
          itemListJsonLd(highlightOffers, "Destaques do ranking Echonomiza"),
        ]}
      />

      <section className="relative overflow-hidden border-b border-brand-800 bg-white">
        <div
          aria-hidden
          className="absolute inset-0 bg-[linear-gradient(135deg,#9f1239_0%,#e11d48_48%,#f43f5e_100%)]"
        />
        <div
          aria-hidden
          className="absolute inset-0 opacity-40 bg-[radial-gradient(circle_at_18%_20%,rgba(250,204,21,0.35),transparent_34%),radial-gradient(circle_at_88%_12%,rgba(255,255,255,0.18),transparent_30%)]"
        />
        <div className="relative mx-auto flex min-h-[78vh] max-w-6xl flex-col justify-center px-4 py-20 text-white">
          <p className="animate-fade-up inline-flex w-fit items-center rounded-md bg-accent-300 px-2.5 py-1 text-xs font-bold uppercase tracking-[0.18em] text-neutral-900">
            Ofertas relâmpago
          </p>
          <h1 className="animate-fade-up-delay mt-4">
            <BrandMark tone="light" size="lg" />
          </h1>
          <p className="animate-fade-up-delay-2 mt-5 max-w-xl text-lg leading-relaxed text-white/90">
            Descontos reais, ranking de qualidade e links de afiliados com
            transparência — para você clicar com confiança.
          </p>
          <div className="animate-fade-up-delay-2 mt-8 flex flex-wrap gap-3">
            <Button
              href="/busca?sort=discount_desc"
              className="bg-accent-300 text-neutral-900 hover:bg-accent-400 shadow-accent-300/30"
            >
              Ver ofertas em alta
              <ArrowRight className="h-4 w-4" />
            </Button>
            <Button
              href="/transparencia"
              variant="secondary"
              className="border-white/50 bg-transparent text-white hover:border-accent-300 hover:bg-white/10 hover:text-white"
            >
              Como funcionam os afiliados
            </Button>
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-6xl space-y-16 px-4 py-14">
        <ApiStatus unavailable={showcase.unavailable} />
        <section>
          <div className="mb-6 flex items-end justify-between gap-4">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-brand-600">
                Destaques
              </p>
              <h2 className="mt-1 text-2xl font-bold text-neutral-800 sm:text-3xl">
                Melhores do ranking
              </h2>
            </div>
            <Link
              href="/busca?sort=ranking_desc"
              className="text-sm font-semibold text-neutral-700 hover:text-brand-600 hover:underline"
            >
              Ver ranking completo
            </Link>
          </div>
          <OfferGrid
            offers={highlightOffers}
            emptyMessage="Ainda não há ofertas aprovadas. Em breve novos descontos aparecerão aqui."
          />
        </section>

        <DiscountTierSection tiers={showcase.data.tiers} />
      </div>
    </>
  );
}
