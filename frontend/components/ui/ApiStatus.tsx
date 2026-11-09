export function ApiStatus({ unavailable }: { unavailable: boolean }) {
  if (!unavailable) return null;

  return (
    <div
      role="alert"
      className="mb-6 rounded-2xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-950"
    >
      Não foi possível carregar as ofertas agora. A vitrine volta sozinha quando a
      API responder de novo.
    </div>
  );
}
