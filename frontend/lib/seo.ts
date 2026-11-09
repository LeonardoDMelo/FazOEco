import type { Metadata } from "next";
import { formatBRL, formatDiscount, toNumber } from "@/lib/formatters";
import type { Category, OfferDetail, OfferListItem } from "@/lib/types";

export function siteUrl(): string {
  return (
    process.env.NEXT_PUBLIC_SITE_URL ||
    process.env.SITE_URL ||
    "http://localhost:3000"
  ).replace(/\/$/, "");
}

export function absoluteUrl(path = "/"): string {
  if (path.startsWith("http")) return path;
  return `${siteUrl()}${path.startsWith("/") ? path : `/${path}`}`;
}

export function buildPageMetadata({
  title,
  description,
  path = "/",
  image,
  noIndex = false,
}: {
  title: string;
  description: string;
  path?: string;
  image?: string | null;
  noIndex?: boolean;
}): Metadata {
  const url = absoluteUrl(path);
  const ogImage = image || absoluteUrl("/og-default.png");

  return {
    title,
    description,
    alternates: { canonical: url },
    robots: noIndex
      ? { index: false, follow: false }
      : { index: true, follow: true },
    openGraph: {
      type: "website",
      locale: "pt_BR",
      url,
      siteName: "FazOEco",
      title,
      description,
      images: [{ url: ogImage, width: 1200, height: 630, alt: title }],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [ogImage],
    },
  };
}

export function homeJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "WebSite",
    name: "FazOEco",
    url: siteUrl(),
    description:
      "Portal de ofertas e afiliados com ranking de qualidade e descontos reais.",
    potentialAction: {
      "@type": "SearchAction",
      target: `${siteUrl()}/busca?q={search_term_string}`,
      "query-input": "required name=search_term_string",
    },
  };
}

export function categoryJsonLd(category: Category) {
  return {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    name: category.name,
    description: category.description || `Ofertas em ${category.name}`,
    url: absoluteUrl(`/categoria/${category.slug}`),
    isPartOf: { "@type": "WebSite", name: "FazOEco", url: siteUrl() },
  };
}

export function offerProductJsonLd(offer: OfferDetail) {
  const price = toNumber(offer.current_price);
  const availability = offer.is_available
    ? "https://schema.org/InStock"
    : "https://schema.org/OutOfStock";
  const discount = formatDiscount(offer.discount_percent);

  const product: Record<string, unknown> = {
    "@context": "https://schema.org",
    "@type": "Product",
    name: offer.product_name,
    image: offer.product_image_url ? [offer.product_image_url] : undefined,
    brand: offer.brand
      ? { "@type": "Brand", name: offer.brand }
      : undefined,
    sku: offer.external_offer_id,
    url: absoluteUrl(`/ofertas/${offer.id}`),
    description: discount
      ? `${offer.product_name} com ${discount} na ${offer.store_name}.`
      : `${offer.product_name} na ${offer.store_name}.`,
    offers: {
      "@type": "AggregateOffer",
      url: absoluteUrl(`/ofertas/${offer.id}`),
      priceCurrency: offer.currency || "BRL",
      lowPrice: price,
      highPrice: toNumber(offer.original_price) || price,
      offerCount: 1,
      availability,
      priceValidUntil: new Date(Date.now() + 1000 * 60 * 60 * 24 * 7)
        .toISOString()
        .slice(0, 10),
      seller: {
        "@type": "Organization",
        name: offer.store_name,
      },
    },
  };

  const rating = toNumber(offer.average_rating);
  if (rating > 0 && offer.ratings_count > 0) {
    product.aggregateRating = {
      "@type": "AggregateRating",
      ratingValue: rating,
      reviewCount: offer.ratings_count,
      bestRating: 5,
      worstRating: 1,
    };
  }

  return product;
}

export function offerMetaDescription(offer: OfferDetail): string {
  const discount = formatDiscount(offer.discount_percent);
  const price = formatBRL(offer.current_price);
  if (!offer.is_available) {
    return `Oferta encerrada: ${offer.product_name}. Confira alternativas semelhantes no FazOEco.`;
  }
  return discount
    ? `${offer.product_name} por ${price} (${discount}) na ${offer.store_name}. Compare no FazOEco.`
    : `${offer.product_name} por ${price} na ${offer.store_name}. Compare no FazOEco.`;
}

export function breadcrumbJsonLd(
  items: { name: string; path: string }[],
) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, index) => ({
      "@type": "ListItem",
      position: index + 1,
      name: item.name,
      item: absoluteUrl(item.path),
    })),
  };
}

export function itemListJsonLd(offers: OfferListItem[], listName: string) {
  return {
    "@context": "https://schema.org",
    "@type": "ItemList",
    name: listName,
    itemListElement: offers.slice(0, 20).map((offer, index) => ({
      "@type": "ListItem",
      position: index + 1,
      url: absoluteUrl(`/ofertas/${offer.id}`),
      name: offer.product_name,
    })),
  };
}
