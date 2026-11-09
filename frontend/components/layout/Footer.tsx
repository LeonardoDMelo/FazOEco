import Link from "next/link";

const links = [
  { href: "/sobre", label: "Sobre" },
  { href: "/transparencia", label: "Transparência de Afiliados" },
  { href: "/termos", label: "Termos de Uso" },
  { href: "/privacidade", label: "Privacidade" },
];

export function Footer() {
  return (
    <footer className="mt-auto border-t border-slate-200 bg-slate-900 text-slate-300">
      <div className="mx-auto grid max-w-6xl gap-8 px-4 py-12 sm:grid-cols-[1.4fr_1fr]">
        <div>
          <p className="text-2xl font-bold text-white">FazOEco</p>
          <p className="mt-3 max-w-md text-sm leading-relaxed text-slate-400">
            Portal automatizado de ofertas e afiliados. Comparamos preços e
            destacamos descontos reais com transparência.
          </p>
        </div>
        <div>
          <p className="text-sm font-semibold uppercase tracking-wider text-slate-400">
            Institucional
          </p>
          <ul className="mt-3 space-y-2 text-sm">
            {links.map((link) => (
              <li key={link.href}>
                <Link href={link.href} className="hover:text-white">
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </div>
      <div className="border-t border-slate-800 px-4 py-4 text-center text-xs text-slate-500">
        © {new Date().getFullYear()} FazOEco. Como afiliados, podemos receber
        comissão por compras realizadas através dos nossos links.
      </div>
    </footer>
  );
}
