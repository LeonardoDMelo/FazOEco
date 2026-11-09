"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import {
  putRankingSettings,
  putSystemSettings,
  type SystemSettings,
} from "@/lib/auth";

const WEIGHT_FIELDS = [
  "discount",
  "rating",
  "sales",
  "reviews",
  "engagement",
] as const;

export function SettingsForm({
  initialSystem,
  initialWeights,
}: {
  initialSystem: SystemSettings;
  initialWeights: Record<string, number>;
}) {
  const [system, setSystem] = useState<SystemSettings>(initialSystem);
  const [weights, setWeights] = useState(initialWeights);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setMessage(null);
    setError(null);
    try {
      await Promise.all([
        putSystemSettings(system),
        putRankingSettings(weights),
      ]);
      setMessage("Configurações salvas com sucesso.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao salvar");
    } finally {
      setSaving(false);
    }
  }

  const weightSum = WEIGHT_FIELDS.reduce((acc, key) => acc + Number(weights[key] || 0), 0);

  return (
    <form onSubmit={onSubmit} className="space-y-8">
      <section className="rounded-2xl border border-slate-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-slate-900">Publicação e revalidação</h2>
        <div className="mt-4 space-y-4">
          <label className="flex items-center justify-between gap-4 text-sm">
            <span className="font-medium text-slate-700">Auto-publicar ofertas</span>
            <input
              type="checkbox"
              checked={system.auto_publish_enabled}
              onChange={(e) =>
                setSystem((s) => ({ ...s, auto_publish_enabled: e.target.checked }))
              }
              className="h-4 w-4 accent-brand-600"
            />
          </label>
          <label className="flex items-center justify-between gap-4 text-sm">
            <span className="font-medium text-slate-700">Preferir modo simulação/mock</span>
            <input
              type="checkbox"
              checked={system.simulation_mode_preferred}
              onChange={(e) =>
                setSystem((s) => ({
                  ...s,
                  simulation_mode_preferred: e.target.checked,
                }))
              }
              className="h-4 w-4 accent-brand-600"
            />
          </label>
          <label className="block space-y-1.5 text-sm">
            <span className="font-medium text-slate-700">
              Limite de revalidação de preço (horas)
            </span>
            <input
              type="number"
              min={1}
              max={168}
              value={system.price_revalidation_hours}
              onChange={(e) =>
                setSystem((s) => ({
                  ...s,
                  price_revalidation_hours: Number(e.target.value),
                }))
              }
              className="w-full rounded-lg border border-slate-200 px-3 py-2 outline-none focus:border-brand-500"
            />
          </label>
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-6">
        <div className="flex items-end justify-between gap-3">
          <h2 className="text-lg font-semibold text-slate-900">
            Pesos do ranking (0–100 pts)
          </h2>
          <p className="text-xs text-slate-500">Soma atual: {weightSum}</p>
        </div>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          {WEIGHT_FIELDS.map((field) => (
            <label key={field} className="block space-y-1.5 text-sm capitalize">
              <span className="font-medium text-slate-700">{field}</span>
              <input
                type="number"
                min={0}
                step="0.01"
                value={weights[field] ?? 0}
                onChange={(e) =>
                  setWeights((w) => ({ ...w, [field]: Number(e.target.value) }))
                }
                className="w-full rounded-lg border border-slate-200 px-3 py-2 outline-none focus:border-brand-500"
              />
            </label>
          ))}
        </div>
      </section>

      {message && (
        <p className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          {message}
        </p>
      )}
      {error && (
        <p className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
          {error}
        </p>
      )}

      <Button type="submit" disabled={saving}>
        {saving ? "Salvando..." : "Salvar configurações"}
      </Button>
    </form>
  );
}
