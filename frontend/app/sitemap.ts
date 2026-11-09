import type { MetadataRoute } from "next";
import { getCategories, getOffers } from "@/lib/api";
import { absoluteUrl } from "@/lib/seo";

export const revalidate = 3600;

async function collectOfferUrls(): Promise<MetadataRoute.Sitemap> {
  const entries: MetadataRoute.Sitemap = [];
  let page = 1;
  let pages = 1;

  while (page <= pages && page <= 50) {
    const result = await getOffers({
      page,
      page_size: 100,
      sort: "newest",
    });
    pages = Math.max(result.meta.pages, 1);
    for (const offer of result.items) {
      entries.push({
        url: absoluteUrl(`/ofertas/${offer.id}`),
        lastModified: offer.created_at ? new Date(offer.created_at) : new Date(),
        changeFrequency: "hourly",
        priority: 0.8,
      });
    }
    page += 1;
    if (result.items.length === 0) break;
  }

  return entries;
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const [categories, offerEntries] = await Promise.all([
    getCategories(),
    collectOfferUrls(),
  ]);

  const staticRoutes: MetadataRoute.Sitemap = [
    "",
    "/busca",
    "/sobre",
    "/termos",
    "/privacidade",
    "/transparencia",
  ].map((path) => ({
    url: absoluteUrl(path || "/"),
    lastModified: new Date(),
    changeFrequency: path === "" || path === "/busca" ? "hourly" : "monthly",
    priority: path === "" ? 1 : 0.5,
  }));

  const categoryRoutes: MetadataRoute.Sitemap = categories.map((category) => ({
    url: absoluteUrl(`/categoria/${category.slug}`),
    lastModified: category.updated_at
      ? new Date(category.updated_at)
      : new Date(),
    changeFrequency: "daily",
    priority: 0.7,
  }));

  return [...staticRoutes, ...categoryRoutes, ...offerEntries];
}
