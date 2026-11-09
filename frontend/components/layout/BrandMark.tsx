import Image from "next/image";
import Link from "next/link";
import { LOGO_SRC, SITE_NAME } from "@/lib/brand";

type BrandMarkProps = {
  href?: string;
  tone?: "dark" | "light";
  size?: "sm" | "md" | "lg";
  wordmark?: boolean;
};

const sizes = {
  sm: { box: "h-8 w-8", text: "text-lg" },
  md: { box: "h-10 w-10", text: "text-2xl" },
  lg: { box: "h-16 w-16 sm:h-20 sm:w-20", text: "text-5xl sm:text-6xl" },
};

export function BrandMark({
  href = "/",
  tone = "dark",
  size = "md",
  wordmark = true,
}: BrandMarkProps) {
  const { box, text } = sizes[size];
  const color = tone === "light" ? "text-white" : "text-brand-950";

  return (
    <Link href={href} className={`inline-flex items-center gap-3 font-bold tracking-tight ${color}`}>
      <Image
        src={LOGO_SRC}
        alt=""
        width={160}
        height={160}
        priority={size !== "sm"}
        className={`${box} shrink-0 rounded-2xl bg-white object-contain`}
      />
      {wordmark && <span className={text}>{SITE_NAME}</span>}
    </Link>
  );
}
