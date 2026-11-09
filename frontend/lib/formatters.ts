const brl = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
});

const dateTimeSP = new Intl.DateTimeFormat("pt-BR", {
  timeZone: "America/Sao_Paulo",
  day: "2-digit",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

export function formatBRL(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === "") return "—";
  const n = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(n)) return "—";
  return brl.format(n);
}

export function formatDiscount(
  value: string | number | null | undefined,
): string | null {
  if (value === null || value === undefined || value === "") return null;
  const n = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(n) || n <= 0) return null;
  return `${Math.round(n)}% OFF`;
}

export function formatDateTimeSP(value: string | null | undefined): string {
  if (!value) return "atualização recente";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "atualização recente";
  return dateTimeSP.format(d);
}

export function formatRating(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  const n = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(n)) return "—";
  return n.toFixed(1);
}

export function bandLabel(band: string | null | undefined): string {
  switch (band) {
    case "extreme":
      return "50% OFF ou mais";
    case "high":
      return "30% a 49% OFF";
    case "medium":
      return "15% a 29% OFF";
    case "low":
      return "5% a 14% OFF";
    default:
      return "Outras ofertas";
  }
}

export function toNumber(value: string | number | null | undefined): number {
  if (value === null || value === undefined) return 0;
  const n = typeof value === "number" ? value : Number(value);
  return Number.isNaN(n) ? 0 : n;
}
