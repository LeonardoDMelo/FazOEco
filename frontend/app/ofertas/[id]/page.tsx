import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ExternalLink, ShieldCheck, Star } from "lucide-react";
import { PriceHistoryChart } from "@/components/offers/PriceHistoryChart";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { getOffer } from "@/lib/api";
import {
  formatBRL,
  formatDateTimeSP,
  formatDiscount,
  formatRating,
  toNumber,
} from "@/lib/formatters";

export const revalidate = 60;

type Props = { params: { id: string } };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const offer = await getOffer(params.id);
  if (!offer) return { title: "Oferta não encontrada" };
  return {
    title: offer.product_name,
    description: `Oferta ${offer.store_name}: ${offer.product_name} por ${formatBRL(offer.current_price)}`,
  };
}

export default async function OfferDetailPage({ params }: Props) {
  const offer = await getOffer(params.id);
  if (!offer) notFound();

  const discount = formatDiscount(offer.discount_percent);

  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
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

      <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="relative aspect-square overflow-hidden rounded-3xl bg-slate-100 lg:aspect-[4/3]">
          {offer.product_image_url ? (
            <Image
              src={offer.product_image_url}
              alt={offer.product_name}
              fill
              className="object-cover"
              sizes="(max-width:1024px) 100vw, 50vw"
              unoptimized
              priority
            />
          ) : (
            <div className="flex h-full items-center justify-center text-slate-400">
              Sem imagem
            </div>
          )}
        </div>

        <div className="flex flex-col gap-5">
          <div className="flex flex-wrap gap-2">
            <Badge variant="neutral">{offer.store_name}</Badge>
            {discount && <Badge variant="discount">{discount}</Badge>}
            {offer.brand && <Badge variant="brand">{offer.brand}</Badge>}
          </div>

          <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            {offer.product_name}
          </h1>

          <div className="flex flex-wrap items-center gap-4 text-sm text-slate-600">
            <span className="inline-flex items-center gap-1">
              <Star className="h-4 w-4 fill-amber-500 text-amber-500" />
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
              Preço verificado em {formatDateTimeSP(offer.last_checked_at || offer.updated_at || offer.created_at)}
            </p>
          </div>

          <Button href={offer.affiliate_url} external variant="store" className="text-base">
            Ir para {offer.store_name}
            <ExternalLink className="h-4 w-4" />
          </Button>

          <div className="flex items-start gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
            <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0" />
            <p>
              Link de afiliado: a FazOEco pode receber comissão se você comprar
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
              A FazOEco não vende produtos: redirecionamos para parceiros
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
    </div>
  );
}
