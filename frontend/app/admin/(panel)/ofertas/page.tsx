"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { OffersTable } from "@/components/admin/OffersTable";
import { getAdminOffers } from "@/lib/auth";
import type { OfferListItem } from "@/lib/types";

const STATUS_FILTERS = [
  { value: "", label: "Todos" },
  { value: "pending", label: "draft / pendente" },
  { value: "approved", label: "published" },
  { value: "rejected", label: "rejected" },
  { value: "expired", label: "expired" },
];

function OffersManager() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const status = searchParams.get("status") || "";
  const [items, setItems] = useState<OfferListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    void (async () => {
      setItems(null);
      setError(null);
      try {
        const params: Record<string, string | number | undefined> = {
          page_size: 50,
          sort: "newest",
        };
        if (status === "expired") {
          params.is_available = "false";
        } else if (status) {
          params.approval_status = status;
        }
        const page = await getAdminOffers(params);
        setItems(page.items);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Falha ao carregar ofertas");
      }
    })();
  }, [status, tick]);

  function setStatus(next: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (next) params.set("status", next);
    else params.delete("status");
    router.push(`/admin/ofertas?${params.toString()}`);
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap gap-2">
        {STATUS_FILTERS.map((filter) => (
          <button
            key={filter.value || "all"}
            type="button"
            onClick={() => setStatus(filter.value)}
            className={`rounded-lg px-3 py-1.5 text-sm font-medium transition ${
              status === filter.value
                ? "bg-brand-600 text-white"
                : "bg-white text-slate-700 ring-1 ring-slate-200 hover:bg-slate-50"
            }`}
          >
            {filter.label}
          </button>
        ))}
      </div>

      {error && <p className="text-sm text-rose-700">{error}</p>}
      {items === null ? (
        <p className="text-slate-500">Carregando ofertas...</p>
      ) : (
        <OffersTable initialItems={items} onChanged={() => setTick((t) => t + 1)} />
      )}
    </div>
  );
}

export default function AdminOffersPage() {
  return (
    <Suspense fallback={<p className="text-slate-500">Carregando ofertas...</p>}>
      <OffersManager />
    </Suspense>
  );
}
