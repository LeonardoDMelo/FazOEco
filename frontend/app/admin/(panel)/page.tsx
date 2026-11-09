"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { MetricCard } from "@/components/admin/MetricCard";
import { getAdminLogs, getAdminStats, type AdminLog, type AdminStats } from "@/lib/auth";
import { formatDateTimeSP } from "@/lib/formatters";

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [logs, setLogs] = useState<AdminLog[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const [s, l] = await Promise.all([
          getAdminStats(),
          getAdminLogs({ page_size: 5 }),
        ]);
        setStats(s);
        setLogs(l.items);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Falha ao carregar dashboard");
      }
    })();
  }, []);

  if (error) {
    return <p className="text-rose-700">{error}</p>;
  }

  if (!stats) {
    return <p className="text-slate-500">Carregando métricas...</p>;
  }

  return (
    <div className="space-y-8">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Ofertas publicadas"
          value={stats.offers_approved}
          tone="success"
          hint="approval_status = approved"
        />
        <MetricCard
          label="Pendentes (draft)"
          value={stats.offers_pending}
          tone="warning"
        />
        <MetricCard
          label="Rejeitadas"
          value={stats.offers_rejected}
          tone="danger"
        />
        <MetricCard
          label="Conectores"
          value={`${stats.connectors_ready}/${stats.connectors_total}`}
          hint={
            stats.simulation_enabled
              ? "Simulação ativa no runtime"
              : "Modo live no runtime"
          }
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <section className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Últimos logs</h2>
            <Link href="/admin/logs" className="text-sm font-medium text-brand-700">
              Ver todos
            </Link>
          </div>
          <ul className="divide-y divide-slate-100">
            {logs.length === 0 && (
              <li className="py-6 text-sm text-slate-500">Nenhum log ainda.</li>
            )}
            {logs.map((log) => (
              <li key={log.id} className="py-3">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-medium text-slate-900">{log.message}</p>
                  <span className="text-xs text-slate-500">
                    {formatDateTimeSP(log.created_at)}
                  </span>
                </div>
                <p className="mt-1 text-xs text-slate-500">
                  {log.level} · {log.source}
                </p>
              </li>
            ))}
          </ul>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-5">
          <h2 className="text-lg font-semibold text-slate-900">Atalhos</h2>
          <div className="mt-4 flex flex-col gap-2 text-sm">
            <Link className="rounded-lg bg-slate-50 px-3 py-2 hover:bg-brand-50" href="/admin/ofertas?status=pending">
              Moderar drafts pendentes ({stats.offers_pending})
            </Link>
            <Link className="rounded-lg bg-slate-50 px-3 py-2 hover:bg-brand-50" href="/admin/conectores">
              Rodar conectores
            </Link>
            <Link className="rounded-lg bg-slate-50 px-3 py-2 hover:bg-brand-50" href="/admin/configuracoes">
              Ajustar pesos e auto-publish
            </Link>
          </div>
          <p className="mt-6 text-xs text-slate-500">
            Indisponíveis/expiradas: {stats.offers_unavailable} · Logs totais:{" "}
            {stats.logs_total}
          </p>
        </section>
      </div>
    </div>
  );
}
