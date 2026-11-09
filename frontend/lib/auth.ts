import type { Page } from "./types";

export type AdminUser = {
  id: string;
  email: string;
  username: string;
  full_name: string | null;
  is_active: boolean;
  is_superuser: boolean;
};

function apiBase(): string {
  if (typeof window === "undefined") {
    return process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
}

export async function loginRequest(username: string, password: string): Promise<void> {
  const body = new URLSearchParams();
  body.set("username", username);
  body.set("password", password);

  const response = await fetch(`${apiBase()}/api/v1/auth/login`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      Accept: "application/json",
    },
    body,
  });

  if (!response.ok) {
    throw new Error("Usuário ou senha inválidos.");
  }
}

export async function logoutRequest(): Promise<void> {
  await fetch(`${apiBase()}/api/v1/auth/logout`, {
    method: "POST",
    credentials: "include",
  });
}

export async function fetchMe(): Promise<AdminUser> {
  const response = await fetch(`${apiBase()}/api/v1/auth/me`, {
    credentials: "include",
    headers: { Accept: "application/json" },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Sessão inválida.");
  }
  return response.json();
}

export async function authFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${apiBase()}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      ...(init.headers || {}),
    },
    cache: "no-store",
  });

  if (response.status === 401) {
    if (typeof window !== "undefined") {
      window.location.href = "/admin/login";
    }
    throw new Error("Sessão expirada.");
  }

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Erro ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export type AdminStats = {
  offers_approved: number;
  offers_pending: number;
  offers_rejected: number;
  offers_unavailable: number;
  connectors_ready: number;
  connectors_total: number;
  logs_total: number;
  simulation_enabled: boolean;
};

export type ConnectorStatus = {
  store_key: string;
  store_name: string;
  has_credentials: boolean;
  simulation_enabled: boolean;
};

export type AdminLog = {
  id: string;
  level: string;
  source: string;
  message: string;
  context: Record<string, unknown> | null;
  user_id: string | null;
  created_at: string;
};

export type SettingRecord = {
  id: string;
  key: string;
  value: Record<string, unknown> | null;
  description: string | null;
  updated_at: string;
};

export type SystemSettings = {
  auto_publish_enabled: boolean;
  simulation_mode_preferred: boolean;
  price_revalidation_hours: number;
  connectors_enabled: Record<string, boolean>;
};

export async function getAdminStats() {
  return authFetch<AdminStats>("/api/v1/admin/stats");
}

export async function getAdminOffers(params: Record<string, string | number | undefined>) {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== "") qs.set(k, String(v));
  });
  return authFetch<Page<import("./types").OfferListItem>>(
    `/api/v1/admin/offers?${qs.toString()}`,
  );
}

export async function moderateOffer(
  id: string,
  action: "approve" | "reject" | "expire",
) {
  if (action === "expire") {
    return authFetch(`/api/v1/admin/offers/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ is_available: false }),
    });
  }
  return authFetch(`/api/v1/admin/offers/${id}/${action}`, {
    method: "POST",
  });
}

export async function getConnectors() {
  return authFetch<ConnectorStatus[]>("/api/v1/admin/connectors");
}

export async function runConnectors(query = "", stores?: string[]) {
  return authFetch<{ results: unknown[] }>("/api/v1/admin/connectors/run", {
    method: "POST",
    body: JSON.stringify({ query, stores, limit: 10 }),
  });
}

export async function getRankingSettings() {
  return authFetch<SettingRecord>("/api/v1/admin/settings/ranking");
}

export async function putRankingSettings(weights: Record<string, number>) {
  return authFetch<SettingRecord>("/api/v1/admin/settings/ranking", {
    method: "PUT",
    body: JSON.stringify(weights),
  });
}

export async function getSystemSettings() {
  return authFetch<SettingRecord>("/api/v1/admin/settings/system");
}

export async function putSystemSettings(payload: SystemSettings) {
  return authFetch<SettingRecord>("/api/v1/admin/settings/system", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function getAdminLogs(params: Record<string, string | number | undefined> = {}) {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== "") qs.set(k, String(v));
  });
  return authFetch<Page<AdminLog>>(`/api/v1/admin/logs?${qs.toString()}`);
}
