"use client";

import { usePathname } from "next/navigation";
import { AffiliateNoticeBar } from "@/components/layout/AffiliateNoticeBar";
import { Footer } from "@/components/layout/Footer";
import { Header } from "@/components/layout/Header";
import type { Category } from "@/lib/types";

export function AppShell({
  categories,
  children,
}: {
  categories: Category[];
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const isAdmin = pathname.startsWith("/admin");

  if (isAdmin) {
    return <>{children}</>;
  }

  return (
    <>
      <AffiliateNoticeBar />
      <Header categories={categories} />
      <main className="flex-1">{children}</main>
      <Footer />
    </>
  );
}
