import type { Metadata } from "next";
import Link from "next/link";
import { ProductImage } from "@/components/offers/ProductImage";
import { notFound } from "next/navigation";
import { AlertTriangle, ExternalLink, ShieldCheck, Star } from "lucide-react";
import { OfferGrid } from "@/components/offers/OfferGrid";
import { PriceHistoryChart } from "@/components/offers/PriceHistoryChart";
import { JsonLd } from "@/components/seo/JsonLd";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { getOffer, getOfferAlternatives } from "@/lib/api";
import {
  formatBRL,
  formatDateTimeSP,
  formatDiscount,
  formatRating,
  toNumber,
} from "@/lib/formatters";
import {
  breadcrumbJsonLd,
  buildPageMetadata,
  offerMetaDescription,
  offerProductJsonLd,
} from "@/lib/seo";

export const revalidate = 60;

type Props = { params: { id: string } };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const offer = await getOffer(params.id);
  if (!offer) {
    return buildPageMetadata({
      title: "Oferta não encontrada",
      description: "A oferta solicitada não está disponível no Echonomiza.",
      path: `/ofertas/${params.id}`,
      noIndex: true,
    });
  }

  return buildPageMetadata({
    title: offer.is_available
      ? `${offer.product_name} — ${formatBRL(offer.current_price)}`
      : `${offer.product_name} (oferta encerrada)`,
    description: offerMetaDescription(offer),
    path: `/ofertas/${offer.id}`,
    image: offer.product_image_url,
  });
}

export default async function OfferDetailPage({ params }: Props) {
  const offer = await getOffer(params.id);
  if (!offer) notFound();

  const discount = formatDiscount(offer.discount_percent);
  const expired = !offer.is_available;
  const alternatives = expired
    ? await getOfferAlternatives(offer.id, 8)
    : { items: [], meta: { page: 1, page_size: 8, total: 0, pages: 0 } };

  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
      <JsonLd
        data={[
          offerProductJsonLd(offer),
          breadcrumbJsonLd([
            { name: "Início", path: "/" },
            { name: "Ofertas", path: "/busca" },
            { name: offer.product_name, path: `/ofertas/${offer.id}` },
          ]),
        ]}
      />

      <div className="mb-6 text-sm text-slate-500">
        <Link href="/" className="hover:text-brand-700">
          Início
        </Link>
        <span className="mx-2">/</span>
        <Link href="/busca" className="hover:text-brand-700">
          Ofertas
        </Link>
        <span className="mx-2">/</span>
        <span className="text-slate-800">{offer.product_name}</span>
      </div>

      {expired && (
        <div className="mb-6 flex items-start gap-3 rounded-2xl border border-accent-300 bg-accent-50 px-4 py-4 text-accent-950">
          <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-accent-600" />
          <div>
            <p className="font-semibold">Esta oferta foi encerrada</p>
            <p className="mt-1 text-sm text-accent-900/90">
              O preço ou a disponibilidade mudaram na loja. Mantemos a página
              para referência e sugerimos alternativas da mesma categoria abaixo.
            </p>
          </div>
        </div>
      )}

      <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="relative aspect-square overflow-hidden rounded-3xl bg-slate-100 lg:aspect-[4/3]">
          <ProductImage
            src={offer.product_image_url}
            alt={offer.product_name}
            sizes="(max-width:1024px) 100vw, 50vw"
            priority
            className={expired ? "opacity-70 grayscale" : ""}
          />
        </div>

        <div className="flex flex-col gap-5">
          <div className="flex flex-wrap gap-2">
            <Badge variant="neutral">{offer.store_name}</Badge>
            {expired ? (
              <Badge variant="warning">Encerrada</Badge>
            ) : (
              discount && <Badge variant="discount">{discount}</Badge>
            )}
            {offer.brand && <Badge variant="brand">{offer.brand}</Badge>}
          </div>

          <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            {offer.product_name}
          </h1>

          <div className="flex flex-wrap items-center gap-4 text-sm text-slate-600">
            <span className="inline-flex items-center gap-1">
              <Star className="h-4 w-4 fill-accent-400 text-accent-500" />
              Nota {formatRating(offer.average_rating)} ({offer.ratings_count} avaliações)
            </span>
            <span>{offer.sales_count} vendas sinalizadas</span>
            <span>Ranking {formatRating(offer.ranking_score)}</span>
          </div>

          <div>
            {offer.original_price && (
              <p className="text-base text-slate-400 line-through">
                {formatBRL(offer.original_price)}
              </p>
            )}
            <p className="text-4xl font-bold text-slate-900">
              {formatBRL(offer.current_price)}
            </p>
            <p className="mt-2 text-sm text-slate-500">
              Preço verificado em{" "}
              {formatDateTimeSP(
                offer.last_checked_at || offer.updated_at || offer.created_at,
              )}
            </p>
          </div>

          {!expired ? (
            <Button href={offer.affiliate_url} external variant="store" className="text-base">
              Ir para {offer.store_name}
              <ExternalLink className="h-4 w-4" />
            </Button>
          ) : (
            <Button href="/busca?sort=ranking_desc" variant="primary" className="justify-center">
              Ver ofertas ativas
            </Button>
          )}

          <div className="flex items-start gap-2 rounded-xl border border-brand-200 bg-brand-50 p-4 text-sm text-brand-900">
            <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-accent-600" />
            <p>
              Link de afiliado: a Echonomiza pode receber comissão se você comprar
              nesta loja. O preço final é definido pelo marketplace.
            </p>
          </div>
        </div>
      </div>

      <div className="mt-10 grid gap-6 lg:grid-cols-2">
        <PriceHistoryChart
          currentPrice={toNumber(offer.current_price)}
          originalPrice={
            offer.original_price != null ? toNumber(offer.original_price) : null
          }
        />
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <h2 className="text-lg font-semibold text-slate-900">Avisos legais</h2>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-relaxed text-slate-600">
            <li>
              Os preços e a disponibilidade podem mudar sem aviso no site da loja.
            </li>
            <li>
              A Echonomiza não vende produtos: redirecionamos para parceiros
              afiliados.
            </li>
            <li>
              Consulte{" "}
              <Link href="/transparencia" className="font-medium text-brand-700 underline">
                Transparência de Afiliados
              </Link>{" "}
              e os{" "}
              <Link href="/termos" className="font-medium text-brand-700 underline">
                Termos de Uso
              </Link>
              .
            </li>
          </ul>
        </div>
      </div>

      {expired && (
        <section className="mt-12">
          <h2 className="text-2xl font-bold text-slate-900">
            Alternativas na mesma categoria
          </h2>
          <p className="mt-2 text-sm text-slate-600">
            Selecionamos ofertas ativas parecidas para você continuar comparando.
          </p>
          <div className="mt-6">
            <OfferGrid
              offers={alternatives.items}
              emptyMessage="Não encontramos alternativas ativas no momento."
            />
          </div>
        </section>
      )}
    </div>
  );
}
