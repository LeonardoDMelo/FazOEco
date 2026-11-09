export function InstitutionalPage({
  eyebrow,
  title,
  children,
}: {
  eyebrow: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <p className="text-sm font-semibold uppercase tracking-[0.18em] text-brand-600">
        {eyebrow}
      </p>
      <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
        {title}
      </h1>
      <div className="prose-fazoeeco mt-8 space-y-4 text-base leading-relaxed text-slate-600">
        {children}
      </div>
    </div>
  );
}
