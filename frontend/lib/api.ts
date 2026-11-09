import type {
  Category,
  OfferDetail,
  OfferFilters,
  OfferListItem,
  Page,
  ProductDetail,
} from "./types";

function apiBase(): string {
  if (typeof window === "undefined") {
    return process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${apiBase()}${path}`;
  let response: Response;
  try {
    response = await fetch(url, {
      ...init,
      headers: {
        Accept: "application/json",
        ...(init?.headers || {}),
      },
      next: { revalidate: 60 },
    });
  } catch {
    throw new ApiError(503, "Não foi possível conectar à API.");
  }

  if (!response.ok) {
    const text = await response.text();
    throw new ApiError(response.status, text || response.statusText);
  }

  return response.json() as Promise<T>;
}

function toQuery(filters: OfferFilters = {}): string {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value));
    }
  });
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

const emptyPage = <T,>(): Page<T> => ({
  items: [],
  meta: { page: 1, page_size: 20, total: 0, pages: 0 },
});

export async function getOffers(
  filters: OfferFilters = {},
): Promise<Page<OfferListItem>> {
  try {
    return await apiFetch<Page<OfferListItem>>(`/api/v1/offers${toQuery(filters)}`);
  } catch {
    return emptyPage();
  }
}

export async function getFeaturedOffers(
  band = "high",
  pageSize = 8,
): Promise<Page<OfferListItem>> {
  try {
    return await apiFetch<Page<OfferListItem>>(
      `/api/v1/offers/featured${toQuery({ band, page_size: pageSize })}`,
    );
  } catch {
    return emptyPage();
  }
}

export async function getOffer(id: string): Promise<OfferDetail | null> {
  try {
    return await apiFetch<OfferDetail>(`/api/v1/offers/${id}`);
  } catch {
    return null;
  }
}

export async function getProduct(id: string): Promise<ProductDetail | null> {
  try {
    return await apiFetch<ProductDetail>(`/api/v1/products/${id}`);
  } catch {
    return null;
  }
}

export async function getCategories(): Promise<Category[]> {
  try {
    return await apiFetch<Category[]>("/api/v1/categories");
  } catch {
    return [];
  }
}

export async function getCategory(slug: string): Promise<Category | null> {
  try {
    return await apiFetch<Category>(`/api/v1/categories/${slug}`);
  } catch {
    return null;
  }
}
