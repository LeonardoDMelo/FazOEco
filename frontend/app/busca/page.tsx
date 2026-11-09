import { Suspense } from "react";
import { OfferFilters } from "@/components/filters/OfferFilters";
import { SortSelector } from "@/components/filters/SortSelector";
import { OfferGrid } from "@/components/offers/OfferGrid";
import { getOffers } from "@/lib/api";
import type { OfferSort } from "@/lib/types";

export const dynamic = "force-dynamic";

type SearchParams = {
  q?: string;
  store?: string;
  band?: string;
  max_price?: string;
  min_discount?: string;
  sort?: string;
  page?: string;
  category_id?: string;
};

export default async function SearchPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const sort = (searchParams.sort as OfferSort) || "newest";
  const page = Number(searchParams.page || "1") || 1;

  const results = await getOffers({
    q: searchParams.q,
    store: searchParams.store,
    band: searchParams.band,
    max_price: searchParams.max_price ? Number(searchParams.max_price) : undefined,
    min_discount: searchParams.min_discount
      ? Number(searchParams.min_discount)
      : undefined,
    category_id: searchParams.category_id,
    sort,
    page,
    page_size: 24,
  });

  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
      <div className="mb-8">
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-brand-600">
          Busca
        </p>
        <h1 className="mt-2 text-3xl font-bold text-slate-900">
          {searchParams.q ? `Resultados para “${searchParams.q}”` : "Todas as ofertas"}
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          {results.meta.total} resultado{results.meta.total === 1 ? "" : "s"}
        </p>
      </div>

      <div className="grid gap-8 lg:grid-cols-[260px_1fr]">
        <aside>
          <Suspense fallback={<div className="h-64 animate-pulse rounded-2xl bg-slate-100" />}>
            <OfferFilters />
          </Suspense>
        </aside>

        <div>
          <div className="mb-5 flex justify-end">
            <Suspense fallback={null}>
              <SortSelector current={sort} />
            </Suspense>
          </div>
          <OfferGrid
            offers={results.items}
            emptyMessage="Nenhuma oferta combina com esses filtros. Tente ampliar a busca."
          />
        </div>
      </div>
    </div>
  );
}
