export function SkeletonCard() {
  return (
    <div className="animate-pulse overflow-hidden rounded-2xl border border-slate-200/80 bg-white">
      <div className="aspect-[4/3] bg-slate-200" />
      <div className="space-y-3 p-4">
        <div className="h-3 w-1/3 rounded bg-slate-200" />
        <div className="h-4 w-full rounded bg-slate-200" />
        <div className="h-4 w-2/3 rounded bg-slate-200" />
        <div className="h-8 w-1/2 rounded bg-slate-200" />
        <div className="h-10 w-full rounded bg-slate-200" />
      </div>
    </div>
  );
}
