"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { getAdminLogs, type AdminLog } from "@/lib/auth";
import { formatDateTimeSP } from "@/lib/formatters";

export default function AdminLogsPage() {
  const [logs, setLogs] = useState<AdminLog[]>([]);
  const [level, setLevel] = useState("");
  const [source, setSource] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      setError(null);
      try {
        const page = await getAdminLogs({
          page_size: 50,
          level: level || undefined,
          source: source || undefined,
        });
        setLogs(page.items);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Falha ao carregar logs");
      }
    })();
  }, [level, source]);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap gap-3">
        <select
          value={level}
          onChange={(e) => setLevel(e.target.value)}
          className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
        >
          <option value="">Todos os níveis</option>
          <option value="INFO">INFO</option>
          <option value="WARNING">WARNING</option>
          <option value="ERROR">ERROR</option>
        </select>
        <input
          value={source}
          onChange={(e) => setSource(e.target.value)}
          placeholder="Filtrar por source (ex: admin.connectors)"
          className="min-w-[260px] flex-1 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
        />
      </div>

      {error && <p className="text-sm text-rose-700">{error}</p>}

      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
        <ul className="divide-y divide-slate-100">
          {logs.length === 0 && (
            <li className="px-5 py-10 text-center text-sm text-slate-500">
              Nenhum log encontrado.
            </li>
          )}
          {logs.map((log) => (
            <li key={log.id} className="px-5 py-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Badge
                    variant={
                      log.level === "ERROR"
                        ? "discount"
                        : log.level === "WARNING"
                          ? "warning"
                          : "neutral"
                    }
                  >
                    {log.level}
                  </Badge>
                  <span className="text-xs font-medium uppercase tracking-wide text-slate-500">
                    {log.source}
                  </span>
                </div>
                <span className="text-xs text-slate-500">
                  {formatDateTimeSP(log.created_at)}
                </span>
              </div>
              <p className="mt-2 text-sm font-medium text-slate-900">{log.message}</p>
              {log.context && (
                <pre className="mt-2 overflow-x-auto rounded-lg bg-slate-50 p-3 text-xs text-slate-600">
                  {JSON.stringify(log.context, null, 2)}
                </pre>
              )}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
