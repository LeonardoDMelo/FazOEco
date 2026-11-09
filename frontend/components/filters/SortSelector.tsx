"use client";

import { useRouter, useSearchParams } from "next/navigation";
import type { OfferSort } from "@/lib/types";

const OPTIONS: { value: OfferSort; label: string }[] = [
  { value: "ranking_desc", label: "Melhor ranking" },
  { value: "discount_desc", label: "Maior desconto" },
  { value: "price_asc", label: "Menor preço" },
  { value: "newest", label: "Mais recentes" },
];

export function SortSelector({ current }: { current?: string }) {
  const router = useRouter();
  const searchParams = useSearchParams();

  function onChange(value: string) {
    const params = new URLSearchParams(searchParams.toString());
    params.set("sort", value);
    params.delete("page");
    router.push(`/busca?${params.toString()}`);
  }

  return (
    <label className="flex items-center gap-2 text-sm text-slate-600">
      <span className="font-medium">Ordenar</span>
      <select
        className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-slate-800 outline-none focus:border-brand-500"
        value={current || "newest"}
        onChange={(e) => onChange(e.target.value)}
      >
        {OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </label>
  );
}
