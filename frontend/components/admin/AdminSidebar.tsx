"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Cable,
  ClipboardList,
  LayoutDashboard,
  Settings2,
  Tags,
} from "lucide-react";
import { BrandMark } from "@/components/layout/BrandMark";
import { cn } from "@/lib/utils";

const links = [
  { href: "/admin", label: "Visão geral", icon: LayoutDashboard },
  { href: "/admin/ofertas", label: "Ofertas", icon: Tags },
  { href: "/admin/conectores", label: "Conectores", icon: Cable },
  { href: "/admin/configuracoes", label: "Configurações", icon: Settings2 },
  { href: "/admin/logs", label: "Logs", icon: ClipboardList },
];

export function AdminSidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex w-64 shrink-0 flex-col border-r border-slate-800 bg-slate-950 text-slate-200">
      <div className="border-b border-slate-800 px-5 py-5">
        <BrandMark href="/admin" tone="light" size="sm" />
        <p className="mt-1 text-xs uppercase tracking-[0.16em] text-emerald-400">
          Painel Admin
        </p>
      </div>
      <nav className="flex flex-1 flex-col gap-1 p-3">
        {links.map(({ href, label, icon: Icon }) => {
          const active =
            href === "/admin" ? pathname === href : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition",
                active
                  ? "bg-brand-600 text-white"
                  : "text-slate-300 hover:bg-slate-900 hover:text-white",
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-slate-800 p-4 text-xs text-slate-500">
        <Link href="/" className="hover:text-emerald-400">
          ← Voltar ao site público
        </Link>
      </div>
    </aside>
  );
}
