import Link from "next/link";
import { BrandMark } from "@/components/layout/BrandMark";

const links = [
  { href: "/sobre", label: "Sobre" },
  { href: "/transparencia", label: "Transparência de Afiliados" },
  { href: "/termos", label: "Termos de Uso" },
  { href: "/privacidade", label: "Privacidade" },
];

export function Footer() {
  return (
    <footer className="mt-auto border-t border-neutral-800 bg-neutral-900 text-neutral-300">
      <div className="mx-auto grid max-w-6xl gap-8 px-4 py-12 sm:grid-cols-[1.4fr_1fr]">
        <div>
          <BrandMark href="/" tone="light" />
          <p className="mt-3 max-w-md text-sm leading-relaxed text-neutral-400">
            Portal automatizado de ofertas e afiliados. Comparamos preços e
            destacamos descontos reais com transparência.
          </p>
        </div>
        <div>
          <p className="text-sm font-semibold uppercase tracking-wider text-accent-400">
            Institucional
          </p>
          <ul className="mt-3 space-y-2 text-sm">
            {links.map((link) => (
              <li key={link.href}>
                <Link href={link.href} className="hover:text-accent-300">
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </div>
      <div className="border-t border-white/10 px-4 py-4 text-center text-xs text-neutral-500">
        © {new Date().getFullYear()} Echonomiza. Como afiliados, podemos receber
        comissão por compras realizadas através dos nossos links.
      </div>
    </footer>
  );
}
