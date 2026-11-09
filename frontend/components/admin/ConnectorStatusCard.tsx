"use client";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import type { ConnectorStatus } from "@/lib/auth";

export function ConnectorStatusCard({
  connector,
  enabled,
  onToggle,
  onRun,
  busy,
}: {
  connector: ConnectorStatus;
  enabled: boolean;
  onToggle: (storeKey: string, enabled: boolean) => void;
  onRun: (storeKey: string) => void;
  busy?: boolean;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">{connector.store_name}</h3>
          <p className="mt-1 text-xs uppercase tracking-wide text-slate-500">
            {connector.store_key}
          </p>
        </div>
        <Badge variant={enabled ? "brand" : "neutral"}>
          {enabled ? "ativo" : "desativado"}
        </Badge>
      </div>

      <dl className="mt-4 space-y-2 text-sm text-slate-600">
        <div className="flex justify-between gap-3">
          <dt>Credenciais</dt>
          <dd className="font-medium text-slate-900">
            {connector.has_credentials ? "configuradas" : "ausentes"}
          </dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt>Simulação (runtime)</dt>
          <dd className="font-medium text-slate-900">
            {connector.simulation_enabled ? "ligada" : "desligada"}
          </dd>
        </div>
      </dl>

      <div className="mt-5 flex flex-wrap gap-2">
        <Button
          variant={enabled ? "secondary" : "primary"}
          className="!py-2 text-xs"
          disabled={busy}
          onClick={() => onToggle(connector.store_key, !enabled)}
        >
          {enabled ? "Desativar" : "Ativar"}
        </Button>
        <Button
          variant="ghost"
          className="!py-2 text-xs"
          disabled={busy || !enabled}
          onClick={() => onRun(connector.store_key)}
        >
          Executar agora
        </Button>
      </div>
    </div>
  );
}
