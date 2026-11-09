import Link from "next/link";
import { ProductImage } from "@/components/offers/ProductImage";
import { ExternalLink, Star } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import {
  formatBRL,
  formatDateTimeSP,
  formatDiscount,
  formatRating,
  toNumber,
} from "@/lib/formatters";
import type { OfferListItem } from "@/lib/types";

export function OfferCard({ offer }: { offer: OfferListItem }) {
  const discount = formatDiscount(offer.discount_percent);
  const rating = toNumber(offer.ranking_score);
  const image = offer.product_image_url;

  return (
    <article className="group flex h-full flex-col overflow-hidden rounded-2xl border border-neutral-200 bg-white shadow-sm transition duration-300 hover:-translate-y-1 hover:shadow-lg hover:shadow-neutral-200/80">
      <Link href={`/ofertas/${offer.id}`} className="relative block aspect-[4/3] bg-neutral-100">
        <ProductImage
          src={image}
          alt={offer.product_name}
          sizes="(max-width:768px) 100vw, 33vw"
          className="transition duration-500 group-hover:scale-[1.03]"
        />
        {discount && (
          <div className="absolute left-3 top-3">
            <Badge variant="discount" className="text-sm shadow">
              {discount}
            </Badge>
          </div>
        )}
      </Link>

      <div className="flex flex-1 flex-col gap-3 p-4">
        <div className="flex items-center justify-between gap-2">
          <Badge variant="coupon">{offer.store_name}</Badge>
          <span className="inline-flex items-center gap-1 text-xs text-neutral-600">
            <Star className="h-3.5 w-3.5 fill-accent-400 text-accent-500" />
            Ranking {formatRating(rating)}
          </span>
        </div>

        <Link href={`/ofertas/${offer.id}`} className="line-clamp-2 text-base font-semibold text-neutral-800 hover:text-brand-600">
          {offer.product_name}
        </Link>

        <div className="mt-auto">
          {offer.original_price && (
            <p className="text-sm text-neutral-400 line-through">
              {formatBRL(offer.original_price)}
            </p>
          )}
          <p className="mt-1 inline-flex rounded-md bg-accent-300 px-2 py-0.5 text-2xl font-bold tracking-tight text-neutral-900">
            {formatBRL(offer.current_price)}
          </p>
          <p className="mt-1 text-xs text-neutral-500">
            Atualizado {formatDateTimeSP(offer.created_at)}
          </p>
        </div>

        <Button href={offer.affiliate_url} external variant="store">
          Ir para a loja
          <ExternalLink className="h-4 w-4" />
        </Button>
      </div>
    </article>
  );
}
