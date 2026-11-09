import type { Metadata } from "next";
import { Outfit } from "next/font/google";
import { AppShell } from "@/components/layout/AppShell";
import { getCategories } from "@/lib/api";
import { LOGO_SRC } from "@/lib/brand";
import { siteUrl } from "@/lib/seo";
import "./globals.css";

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl()),
  title: {
    default: "Echonomiza — Ofertas e Afiliados com Transparência",
    template: "%s · Echonomiza",
  },
  description:
    "Encontre descontos reais com ranking de qualidade, faixas dinâmicas e links de afiliados transparentes.",
  openGraph: {
    type: "website",
    locale: "pt_BR",
    siteName: "Echonomiza",
  },
  twitter: {
    card: "summary_large_image",
  },
  icons: {
    icon: LOGO_SRC,
    apple: LOGO_SRC,
  },
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
        <AppShell categories={categories}>{children}</AppShell>
      </body>
    </html>
  );
}
