import Link from "next/link";
import { Search } from "lucide-react";
import type { Category } from "@/lib/types";

export function Header({ categories = [] }: { categories?: Category[] }) {
  const topCategories = categories.slice(0, 6);

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200/80 bg-white/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:gap-6">
        <Link href="/" className="shrink-0 text-2xl font-bold tracking-tight text-brand-700">
          FazOEco
        </Link>

        <form action="/busca" method="get" className="relative w-full flex-1">
          <Search
            className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
            aria-hidden
          />
          <input
            type="search"
            name="q"
            placeholder="Buscar ofertas, marcas ou produtos..."
            className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-10 pr-4 text-sm outline-none transition focus:border-brand-500 focus:bg-white focus:ring-2 focus:ring-brand-500/20"
          />
        </form>

        <nav className="hidden items-center gap-4 text-sm font-medium text-slate-600 lg:flex">
          <Link href="/busca" className="hover:text-brand-700">
            Ofertas
          </Link>
          <Link href="/sobre" className="hover:text-brand-700">
            Sobre
          </Link>
        </nav>
      </div>

      {topCategories.length > 0 && (
        <div className="border-t border-slate-100 bg-slate-50/80">
          <div className="mx-auto flex max-w-6xl gap-1 overflow-x-auto px-4 py-2 text-sm">
            {topCategories.map((cat) => (
              <Link
                key={cat.id}
                href={`/categoria/${cat.slug}`}
                className="whitespace-nowrap rounded-lg px-3 py-1.5 text-slate-600 transition hover:bg-white hover:text-brand-700"
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
