import { cn } from "@/lib/utils";

type BadgeVariant = "brand" | "discount" | "neutral" | "warning";

const variants: Record<BadgeVariant, string> = {
  brand: "bg-brand-100 text-brand-700",
  discount: "bg-amber-500 text-white",
  neutral: "bg-slate-100 text-slate-700",
  warning: "bg-orange-100 text-orange-800",
};

export function Badge({
  children,
  variant = "neutral",
  className,
}: {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-semibold tracking-wide",
        variants[variant],
        className,
      )}
    >
      {children}
    </span>
  );
}
