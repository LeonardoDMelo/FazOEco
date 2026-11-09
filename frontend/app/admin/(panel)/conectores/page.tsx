"use client";

import { useEffect, useState } from "react";
import { ConnectorStatusCard } from "@/components/admin/ConnectorStatusCard";
import { Button } from "@/components/ui/Button";
import {
  getConnectors,
  getSystemSettings,
  putSystemSettings,
  runConnectors,
  type ConnectorStatus,
  type SystemSettings,
} from "@/lib/auth";

const DEFAULT_SYSTEM: SystemSettings = {
  auto_publish_enabled: false,
  simulation_mode_preferred: true,
  price_revalidation_hours: 6,
  connectors_enabled: {
    amazon: true,
    mercadolivre: true,
    shopee: true,
  },
};

export default function AdminConnectorsPage() {
  const [connectors, setConnectors] = useState<ConnectorStatus[]>([]);
  const [system, setSystem] = useState<SystemSettings>(DEFAULT_SYSTEM);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    const [list, settings] = await Promise.all([getConnectors(), getSystemSettings()]);
    setConnectors(list);
    const value = (settings.value || {}) as Partial<SystemSettings>;
    setSystem({
      ...DEFAULT_SYSTEM,
      ...value,
      connectors_enabled: {
        ...DEFAULT_SYSTEM.connectors_enabled,
        ...(value.connectors_enabled || {}),
      },
    });
  }

  useEffect(() => {
    void load().catch((err) =>
      setError(err instanceof Error ? err.message : "Falha ao carregar conectores"),
    );
  }, []);

  async function toggle(storeKey: string, enabled: boolean) {
    setBusy(true);
    setMessage(null);
    setError(null);
    try {
      const next: SystemSettings = {
        ...system,
        connectors_enabled: {
          ...system.connectors_enabled,
          [storeKey]: enabled,
        },
      };
      await putSystemSettings(next);
      setSystem(next);
      setMessage(`${storeKey} ${enabled ? "ativado" : "desativado"}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao atualizar");
    } finally {
      setBusy(false);
    }
  }

  async function toggleSimulation(preferred: boolean) {
    setBusy(true);
    setError(null);
    try {
      const next = { ...system, simulation_mode_preferred: preferred };
      await putSystemSettings(next);
      setSystem(next);
      setMessage(
        preferred
          ? "Preferência de simulação/mock salva (env ENABLE_SIMULATION_MODE ainda controla o runtime)."
          : "Preferência de modo live salva.",
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao salvar preferência");
    } finally {
      setBusy(false);
    }
  }

  async function run(storeKey?: string) {
    setBusy(true);
    setMessage(null);
    setError(null);
    try {
      const stores = storeKey
        ? [storeKey]
        : Object.entries(system.connectors_enabled)
            .filter(([, enabled]) => enabled)
            .map(([key]) => key);
      const result = await runConnectors("ofertas", stores);
      setMessage(`Execução concluída: ${result.results.length} conector(es).`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha na execução");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white p-4">
        <div>
          <p className="text-sm font-medium text-slate-800">Modo simulação preferido</p>
          <p className="text-xs text-slate-500">
            Runtime atual dos conectores:{" "}
            {connectors[0]?.simulation_enabled ? "simulação" : "live/credenciais"}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant={system.simulation_mode_preferred ? "primary" : "secondary"}
            className="!py-2 text-xs"
            disabled={busy}
            onClick={() => void toggleSimulation(true)}
          >
            Preferir mock
          </Button>
          <Button
            variant={!system.simulation_mode_preferred ? "primary" : "secondary"}
            className="!py-2 text-xs"
            disabled={busy}
            onClick={() => void toggleSimulation(false)}
          >
            Preferir live
          </Button>
          <Button
            variant="ghost"
            className="!py-2 text-xs"
            disabled={busy}
            onClick={() => void run()}
          >
            Rodar ativos
          </Button>
        </div>
      </div>

      {message && (
        <p className="rounded-lg border border-brand-200 bg-brand-50 px-4 py-3 text-sm text-brand-800">
          {message}
        </p>
      )}
      {error && (
        <p className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
          {error}
        </p>
      )}

      <div className="grid gap-4 lg:grid-cols-3">
        {connectors.map((connector) => (
          <ConnectorStatusCard
            key={connector.store_key}
            connector={connector}
            enabled={system.connectors_enabled[connector.store_key] ?? true}
            onToggle={(key, enabled) => void toggle(key, enabled)}
            onRun={(key) => void run(key)}
            busy={busy}
          />
        ))}
      </div>
    </div>
  );
}
