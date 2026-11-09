import Link from "next/link";
import { cn } from "@/lib/utils";

type Variant = "primary" | "secondary" | "ghost" | "store";

const variants: Record<Variant, string> = {
  // Vermelho — CTAs
  primary:
    "bg-brand-600 text-white hover:bg-brand-700 shadow-sm shadow-brand-600/25",
  secondary:
    "border border-neutral-300 bg-white text-neutral-800 hover:border-neutral-500 hover:text-neutral-950",
  ghost: "text-neutral-700 hover:bg-neutral-100",
  store:
    "bg-brand-600 text-white hover:bg-brand-700 shadow-sm shadow-brand-600/20 w-full justify-center",
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
    "inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600",
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
