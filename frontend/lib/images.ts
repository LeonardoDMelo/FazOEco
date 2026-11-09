/** Hosts the Next.js image optimizer is allowed to fetch. Anything else uses a plain img. */

export const OPTIMIZED_IMAGE_HOSTS = [
  "m.media-amazon.com",
  "images-na.ssl-images-amazon.com",
  "images-eu.ssl-images-amazon.com",
  "http2.mlstatic.com",
  "cf.shopee.com.br",
  "down-br.img.susercontent.com",
] as const;

export function isOptimizableImage(src: string): boolean {
  try {
    const host = new URL(src).hostname.toLowerCase();
    return OPTIMIZED_IMAGE_HOSTS.some(
      (allowed) => host === allowed || host.endsWith(`.${allowed}`),
    );
  } catch {
    return false;
  }
}
