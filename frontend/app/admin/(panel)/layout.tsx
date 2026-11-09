"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { AdminHeader } from "@/components/admin/AdminHeader";
import { AdminSidebar } from "@/components/admin/AdminSidebar";
import { useAuth } from "@/context/AuthContext";

const TITLES: Record<string, string> = {
  "/admin": "Visão geral",
  "/admin/ofertas": "Gestão de ofertas",
  "/admin/conectores": "Conectores",
  "/admin/configuracoes": "Configurações",
  "/admin/logs": "Logs de integração",
};

export default function AdminPanelLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading && !user) {
      router.replace(`/admin/login?next=${encodeURIComponent(pathname)}`);
    }
  }, [loading, user, router, pathname]);

  if (loading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-100 text-slate-600">
        Validando sessão...
      </div>
    );
  }

  const title = TITLES[pathname] || "Admin";

  return (
    <div className="flex min-h-screen bg-slate-100">
      <AdminSidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <AdminHeader title={title} />
        <div className="flex-1 p-6">{children}</div>
      </div>
    </div>
  );
}
