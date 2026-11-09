"use client";

import { useEffect, useState } from "react";
import { SettingsForm } from "@/components/admin/SettingsForm";
import {
  getRankingSettings,
  getSystemSettings,
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

const DEFAULT_WEIGHTS = {
  discount: 30,
  rating: 25,
  sales: 20,
  reviews: 15,
  engagement: 10,
};

export default function AdminSettingsPage() {
  const [ready, setReady] = useState(false);
  const [system, setSystem] = useState<SystemSettings>(DEFAULT_SYSTEM);
  const [weights, setWeights] = useState(DEFAULT_WEIGHTS);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const [sys, ranking] = await Promise.all([
          getSystemSettings(),
          getRankingSettings(),
        ]);
        const sysValue = (sys.value || {}) as Partial<SystemSettings>;
        setSystem({
          ...DEFAULT_SYSTEM,
          ...sysValue,
          connectors_enabled: {
            ...DEFAULT_SYSTEM.connectors_enabled,
            ...(sysValue.connectors_enabled || {}),
          },
        });
        const rankingValue = (ranking.value || {}) as Record<string, string | number>;
        setWeights({
          discount: Number(rankingValue.discount ?? 30),
          rating: Number(rankingValue.rating ?? 25),
          sales: Number(rankingValue.sales ?? 20),
          reviews: Number(rankingValue.reviews ?? 15),
          engagement: Number(rankingValue.engagement ?? 10),
        });
        setReady(true);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Falha ao carregar configurações");
      }
    })();
  }, []);

  if (error) return <p className="text-rose-700">{error}</p>;
  if (!ready) return <p className="text-slate-500">Carregando configurações...</p>;

  return <SettingsForm initialSystem={system} initialWeights={weights} />;
}
