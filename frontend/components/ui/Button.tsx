import Link from "next/link";
import { cn } from "@/lib/utils";

type Variant = "primary" | "secondary" | "ghost" | "store";

const variants: Record<Variant, string> = {
  // Laranja enérgico — CTAs principais
  primary:
    "bg-accent-500 text-white hover:bg-accent-600 shadow-sm shadow-accent-500/30",
  secondary:
    "border border-neutral-300 bg-white text-neutral-900 hover:border-brand-700 hover:text-brand-800",
  ghost: "text-neutral-800 hover:bg-neutral-100",
  // CTA de loja / cupom
  store:
    "bg-accent-500 text-white hover:bg-accent-600 shadow-sm shadow-accent-500/25 w-full justify-center",
};

export function Button({
  children,
  className,
  variant = "primary",
  href,
  external,
  type = "button",
  ...props
}: {
  children: React.ReactNode;
  className?: string;
  variant?: Variant;
  href?: string;
  external?: boolean;
  type?: "button" | "submit";
} & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const classes = cn(
    "inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-500",
    variants[variant],
    className,
  );

  if (href) {
    if (external) {
      return (
        <a
          href={href}
          className={classes}
          target="_blank"
          rel="noopener noreferrer sponsored"
        >
          {children}
        </a>
      );
    }
    return (
      <Link href={href} className={classes}>
        {children}
      </Link>
    );
  }

  return (
    <button type={type} className={classes} {...props}>
      {children}
    </button>
  );
}
