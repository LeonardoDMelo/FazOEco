import Image from "next/image";
import { isOptimizableImage } from "@/lib/images";

type ProductImageProps = {
  src: string | null;
  alt: string;
  sizes: string;
  className?: string;
  priority?: boolean;
};

export function ProductImage({
  src,
  alt,
  sizes,
  className = "",
  priority = false,
}: ProductImageProps) {
  if (!src) {
    return (
      <div className="flex h-full items-center justify-center bg-gradient-to-br from-brand-50 to-slate-100 text-sm font-medium text-slate-400">
        Sem imagem
      </div>
    );
  }

  if (isOptimizableImage(src)) {
    return (
      <Image
        src={src}
        alt={alt}
        fill
        priority={priority}
        sizes={sizes}
        className={`object-cover ${className}`}
      />
    );
  }

  return (
    // Hosts outside the marketplace allowlist skip the optimizer (unknown CDNs, mocks).
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={src}
      alt={alt}
      className={`absolute inset-0 h-full w-full object-cover ${className}`}
    />
  );
}
