"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { fetchMe, loginRequest, logoutRequest, type AdminUser } from "@/lib/auth";

type AuthContextValue = {
  user: AdminUser | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AdminUser | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const me = await fetchMe();
      setUser(me.is_superuser ? me : null);
      if (!me.is_superuser) {
        await logoutRequest();
      }
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const login = useCallback(async (username: string, password: string) => {
    await loginRequest(username, password);
    const me = await fetchMe();
    if (!me.is_superuser) {
      await logoutRequest();
      throw new Error("Conta sem privilégios de administrador.");
    }
    setUser(me);
  }, []);

  const logout = useCallback(() => {
    void logoutRequest().finally(() => {
      setUser(null);
      window.location.href = "/admin/login";
    });
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, logout, refresh }),
    [user, loading, login, logout, refresh],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth deve ser usado dentro de AuthProvider");
  }
  return ctx;
}
