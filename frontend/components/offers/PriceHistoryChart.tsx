import { formatBRL } from "@/lib/formatters";
import type { PricePoint } from "@/lib/types";

export function PriceHistoryChart({
  points,
  currentPrice,
  originalPrice,
}: {
  points?: PricePoint[];
  currentPrice?: number;
  originalPrice?: number | null;
}) {
  const data =
    points && points.length > 0
      ? points
      : [
          {
            label: "Antes",
            price: originalPrice || currentPrice || 0,
          },
          {
            label: "Agora",
            price: currentPrice || 0,
          },
        ];

  const max = Math.max(...data.map((p) => p.price), 1);

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5">
      <h3 className="text-lg font-semibold text-slate-900">Histórico de preço</h3>
      <p className="mt-1 text-sm text-slate-500">
        Visualização simplificada com base nos valores capturados.
      </p>
      <div className="mt-6 flex h-40 items-end gap-3">
        {data.map((point) => {
          const height = Math.max(8, (point.price / max) * 100);
          return (
            <div key={point.label} className="flex flex-1 flex-col items-center gap-2">
              <span className="text-xs font-medium text-slate-600">
                {formatBRL(point.price)}
              </span>
              <div
                className="w-full rounded-t-lg bg-gradient-to-t from-brand-700 to-brand-400 transition-all duration-700"
                style={{ height: `${height}%` }}
                title={formatBRL(point.price)}
              />
              <span className="text-xs text-slate-500">{point.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
