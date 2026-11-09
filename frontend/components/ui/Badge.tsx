import { cn } from "@/lib/utils";

type BadgeVariant = "brand" | "discount" | "neutral" | "warning" | "coupon";

const variants: Record<BadgeVariant, string> = {
  brand: "bg-brand-100 text-brand-900",
  // % OFF — vermelho claro com texto escuro
  discount: "bg-brand-500 text-neutral-900",
  neutral: "bg-neutral-100 text-neutral-700",
  warning: "bg-neutral-800 text-white",
  coupon: "bg-accent-300 text-neutral-900",
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
