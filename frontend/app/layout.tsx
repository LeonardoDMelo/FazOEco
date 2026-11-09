import type { Metadata } from "next";
import { Outfit } from "next/font/google";
import { AffiliateNoticeBar } from "@/components/layout/AffiliateNoticeBar";
import { Footer } from "@/components/layout/Footer";
import { Header } from "@/components/layout/Header";
import { getCategories } from "@/lib/api";
import "./globals.css";

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "FazOEco — Ofertas e Afiliados com Transparência",
    template: "%s · FazOEco",
  },
  description:
    "Encontre descontos reais com ranking de qualidade, faixas dinâmicas e links de afiliados transparentes.",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const categories = await getCategories();

  return (
    <html lang="pt-BR">
      <body className={`${outfit.variable} flex min-h-screen flex-col font-sans antialiased`}>
        <AffiliateNoticeBar />
        <Header categories={categories} />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
