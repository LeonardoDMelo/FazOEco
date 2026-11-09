import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { OfferGrid } from "@/components/offers/OfferGrid";
import { JsonLd } from "@/components/seo/JsonLd";
import { ApiStatus } from "@/components/ui/ApiStatus";
import { getCategories, getCategory, loadCategory, loadOffers } from "@/lib/api";
import {
  breadcrumbJsonLd,
  buildPageMetadata,
  categoryJsonLd,
  itemListJsonLd,
} from "@/lib/seo";

export const revalidate = 60;

type Props = { params: { slug: string } };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const category = await getCategory(params.slug);
  if (!category) {
    return buildPageMetadata({
      title: "Categoria não encontrada",
      description: "A categoria solicitada não existe no FazOEco.",
      path: `/categoria/${params.slug}`,
      noIndex: true,
    });
  }

  return buildPageMetadata({
    title: `Ofertas em ${category.name}`,
    description:
      category.description ||
      `Compare as melhores ofertas da categoria ${category.name} no FazOEco.`,
    path: `/categoria/${category.slug}`,
  });
}

export async function generateStaticParams() {
  const categories = await getCategories();
  return categories.map((c) => ({ slug: c.slug }));
}

export default async function CategoryPage({ params }: Props) {
  const loadedCategory = await loadCategory(params.slug);
  if (loadedCategory.unavailable) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-10">
        <ApiStatus unavailable />
      </div>
    );
  }
  const category = loadedCategory.data;
  if (!category) notFound();

  const loadedOffers = await loadOffers({
    category_id: category.id,
    sort: "ranking_desc",
    page_size: 24,
  });
  const offers = loadedOffers.data;

  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
      <JsonLd
        data={[
          categoryJsonLd(category),
          breadcrumbJsonLd([
            { name: "Início", path: "/" },
            { name: category.name, path: `/categoria/${category.slug}` },
          ]),
          itemListJsonLd(offers.items, `Ofertas em ${category.name}`),
        ]}
      />

      <p className="text-sm font-semibold uppercase tracking-[0.18em] text-brand-600">
        Categoria
      </p>
      <h1 className="mt-2 text-3xl font-bold text-slate-900 sm:text-4xl">
        {category.name}
      </h1>
      {category.description && (
        <p className="mt-3 max-w-2xl text-slate-600">{category.description}</p>
      )}
      <ApiStatus unavailable={loadedOffers.unavailable} />
      <p className="mt-2 text-sm text-slate-500">
        {offers.meta.total} oferta{offers.meta.total === 1 ? "" : "s"} encontrada
        {offers.meta.total === 1 ? "" : "s"}
      </p>

      <div className="mt-8">
        <OfferGrid
          offers={offers.items}
          emptyMessage={`Ainda não há ofertas publicadas em ${category.name}.`}
        />
      </div>
    </div>
  );
}
