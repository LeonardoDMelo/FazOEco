"use client";

import { useMemo, useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { formatBRL, formatDiscount } from "@/lib/formatters";
import { moderateOffer } from "@/lib/auth";
import type { OfferListItem } from "@/lib/types";

const STATUS_UI: Record<string, { label: string; variant: "brand" | "warning" | "neutral" | "discount" }> = {
  pending: { label: "draft / pendente", variant: "warning" },
  approved: { label: "published", variant: "brand" },
  rejected: { label: "rejected", variant: "discount" },
};

export function OffersTable({
  initialItems,
  onChanged,
}: {
  initialItems: OfferListItem[];
  onChanged?: () => void;
}) {
  const [items, setItems] = useState(initialItems);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const rows = useMemo(() => items, [items]);

  async function act(id: string, action: "approve" | "reject" | "expire") {
    setBusyId(id);
    setError(null);
    try {
      const updated = (await moderateOffer(id, action)) as OfferListItem;
      setItems((prev) =>
        prev.map((item) => (item.id === id ? { ...item, ...updated } : item)),
      );
      onChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha na moderação");
    } finally {
      setBusyId(null);
    }
  }

  if (!rows.length) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-6 py-12 text-center text-slate-600">
        Nenhuma oferta neste filtro.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
      {error && (
        <div className="border-b border-rose-200 bg-rose-50 px-4 py-2 text-sm text-rose-700">
          {error}
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3">Produto</th>
              <th className="px-4 py-3">Loja</th>
              <th className="px-4 py-3">Preço</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Disponível</th>
              <th className="px-4 py-3 text-right">Ações</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((offer) => {
              const status = STATUS_UI[offer.approval_status] || STATUS_UI.pending;
              const expired = !offer.is_available;
              return (
                <tr key={offer.id} className="border-t border-slate-100">
                  <td className="px-4 py-3">
                    <p className="max-w-xs font-medium text-slate-900 line-clamp-2">
                      {offer.product_name}
                    </p>
                    <p className="text-xs text-slate-500">
                      {formatDiscount(offer.discount_percent) || "sem desconto"}
                    </p>
                  </td>
                  <td className="px-4 py-3 text-slate-700">{offer.store_name}</td>
                  <td className="px-4 py-3 font-semibold text-slate-900">
                    {formatBRL(offer.current_price)}
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant={expired ? "neutral" : status.variant}>
                      {expired ? "expired" : status.label}
                    </Badge>
                  </td>
                  <td className="px-4 py-3">{offer.is_available ? "sim" : "não"}</td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-2">
                      <Button
                        variant="primary"
                        className="!px-3 !py-1.5 text-xs"
                        disabled={busyId === offer.id}
                        onClick={() => void act(offer.id, "approve")}
                      >
                        Aprovar
                      </Button>
                      <Button
                        variant="secondary"
                        className="!px-3 !py-1.5 text-xs"
                        disabled={busyId === offer.id}
                        onClick={() => void act(offer.id, "reject")}
                      >
                        Rejeitar
                      </Button>
                      <Button
                        variant="ghost"
                        className="!px-3 !py-1.5 text-xs"
                        disabled={busyId === offer.id}
                        onClick={() => void act(offer.id, "expire")}
                      >
                        Expirar
                      </Button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
