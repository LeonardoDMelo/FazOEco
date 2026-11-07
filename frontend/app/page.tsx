export default function HomePage() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  return (
    <main className="relative min-h-screen overflow-hidden bg-gradient-to-br from-slate-50 via-emerald-50/40 to-slate-100">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(22,163,74,0.12),_transparent_55%)]"
      />

      <section className="relative mx-auto flex min-h-screen max-w-3xl flex-col justify-center px-6 py-16">
        <p className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-brand-600">
          Fase 1 · Base pronta
        </p>
        <h1 className="text-5xl font-bold tracking-tight text-slate-900 sm:text-6xl">
          FazOEco
        </h1>
        <p className="mt-4 max-w-xl text-lg leading-relaxed text-slate-600">
          Portal Automatizado de Ofertas e Afiliados. Stack Next.js, FastAPI e
          PostgreSQL em execução via Docker Compose.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <a
            href={`${apiUrl}/docs`}
            className="rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-brand-700"
          >
            Abrir API Docs
          </a>
          <a
            href={`${apiUrl}/api/health`}
            className="rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-medium text-slate-700 transition hover:border-brand-500 hover:text-brand-700"
          >
            Health check
          </a>
        </div>
      </section>
    </main>
  );
}
