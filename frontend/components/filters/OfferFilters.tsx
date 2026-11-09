"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/Button";

const STORES = ["Amazon", "Mercado Livre", "Shopee"];
const BANDS = [
  { value: "", label: "Todas as faixas" },
  { value: "extreme", label: "50% OFF ou mais" },
  { value: "high", label: "30% a 49% OFF" },
  { value: "medium", label: "15% a 29% OFF" },
  { value: "low", label: "5% a 14% OFF" },
];

export function OfferFilters() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [store, setStore] = useState(searchParams.get("store") || "");
  const [band, setBand] = useState(searchParams.get("band") || "");
  const [maxPrice, setMaxPrice] = useState(searchParams.get("max_price") || "");
  const [minDiscount, setMinDiscount] = useState(
    searchParams.get("min_discount") || "",
  );

  function applyFilters(e: React.FormEvent) {
    e.preventDefault();
    const params = new URLSearchParams(searchParams.toString());
    const setOrDelete = (key: string, value: string) => {
      if (value) params.set(key, value);
      else params.delete(key);
    };
    setOrDelete("store", store);
    setOrDelete("band", band);
    setOrDelete("max_price", maxPrice);
    setOrDelete("min_discount", minDiscount);
    params.delete("page");
    router.push(`/busca?${params.toString()}`);
  }

  function clearFilters() {
    const q = searchParams.get("q");
    const sort = searchParams.get("sort");
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (sort) params.set("sort", sort);
    router.push(`/busca?${params.toString()}`);
  }

  return (
    <form
      onSubmit={applyFilters}
      className="space-y-5 rounded-2xl border border-slate-200 bg-white p-5"
    >
      <h2 className="text-base font-semibold text-slate-900">Filtros</h2>

      <label className="block space-y-1.5 text-sm">
        <span className="font-medium text-slate-700">Loja</span>
        <select
          value={store}
          onChange={(e) => setStore(e.target.value)}
          className="w-full rounded-lg border border-slate-200 px-3 py-2 outline-none focus:border-brand-500"
        >
          <option value="">Todas</option>
          {STORES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </label>

      <label className="block space-y-1.5 text-sm">
        <span className="font-medium text-slate-700">Faixa de desconto</span>
        <select
          value={band}
          onChange={(e) => setBand(e.target.value)}
          className="w-full rounded-lg border border-slate-200 px-3 py-2 outline-none focus:border-brand-500"
        >
          {BANDS.map((b) => (
            <option key={b.value || "all"} value={b.value}>
              {b.label}
            </option>
          ))}
        </select>
      </label>

      <label className="block space-y-1.5 text-sm">
        <span className="font-medium text-slate-700">Preço máximo (R$)</span>
        <input
          type="number"
          min={0}
          step="0.01"
          value={maxPrice}
          onChange={(e) => setMaxPrice(e.target.value)}
          className="w-full rounded-lg border border-slate-200 px-3 py-2 outline-none focus:border-brand-500"
          placeholder="Ex: 200"
        />
      </label>

      <label className="block space-y-1.5 text-sm">
        <span className="font-medium text-slate-700">Desconto mínimo (%)</span>
        <input
          type="number"
          min={0}
          max={100}
          value={minDiscount}
          onChange={(e) => setMinDiscount(e.target.value)}
          className="w-full rounded-lg border border-slate-200 px-3 py-2 outline-none focus:border-brand-500"
          placeholder="Ex: 20"
        />
      </label>

      <div className="flex flex-col gap-2">
        <Button type="submit" className="w-full justify-center">
          Aplicar filtros
        </Button>
        <Button
          type="button"
          variant="ghost"
          className="w-full justify-center"
          onClick={clearFilters}
        >
          Limpar
        </Button>
      </div>
    </form>
  );
}
