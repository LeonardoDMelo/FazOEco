import Link from "next/link";
import { Search } from "lucide-react";
import { BrandMark } from "@/components/layout/BrandMark";
import type { Category } from "@/lib/types";

export function Header({ categories = [] }: { categories?: Category[] }) {
  const topCategories = categories.slice(0, 6);

  return (
    <header className="sticky top-0 z-40 border-b border-neutral-200 bg-white/95 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:gap-6">
        <BrandMark />

        <form action="/busca" method="get" className="relative w-full flex-1">
          <Search
            className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-400"
            aria-hidden
          />
          <input
            type="search"
            name="q"
            placeholder="Buscar ofertas, marcas ou produtos..."
            className="w-full rounded-xl border border-neutral-200 bg-neutral-50 py-2.5 pl-10 pr-4 text-sm text-neutral-900 outline-none transition focus:border-brand-700 focus:bg-white focus:ring-2 focus:ring-brand-700/15"
          />
        </form>

        <nav className="hidden items-center gap-4 text-sm font-medium text-brand-800 lg:flex">
          <Link href="/busca" className="hover:text-accent-600">
            Ofertas
          </Link>
          <Link href="/sobre" className="hover:text-accent-600">
            Sobre
          </Link>
        </nav>
      </div>

      {topCategories.length > 0 && (
        <div className="border-t border-neutral-100 bg-brand-950 text-white">
          <div className="mx-auto flex max-w-6xl gap-1 overflow-x-auto px-4 py-2 text-sm">
            {topCategories.map((cat) => (
              <Link
                key={cat.id}
                href={`/categoria/${cat.slug}`}
                className="whitespace-nowrap rounded-lg px-3 py-1.5 text-white/80 transition hover:bg-white/10 hover:text-accent-300"
              >
                {cat.name}
              </Link>
            ))}
          </div>
        </div>
      )}
    </header>
  );
}
