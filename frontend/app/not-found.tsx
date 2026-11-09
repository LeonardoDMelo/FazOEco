import { Button } from "@/components/ui/Button";

export default function NotFound() {
  return (
    <div className="mx-auto flex min-h-[50vh] max-w-xl flex-col items-center justify-center px-4 py-20 text-center">
      <p className="text-sm font-semibold uppercase tracking-[0.18em] text-brand-600">
        404
      </p>
      <h1 className="mt-3 text-3xl font-bold text-slate-900">Página não encontrada</h1>
      <p className="mt-3 text-slate-600">
        A oferta ou página que você procura não está disponível.
      </p>
      <Button href="/" className="mt-6">
        Voltar ao início
      </Button>
    </div>
  );
}
