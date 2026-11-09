import type {
  Category,
  DiscountBand,
  OfferDetail,
  OfferFilters,
  OfferListItem,
  Page,
  ProductDetail,
} from "./types";

export type LoadResult<T> = {
  data: T;
  unavailable: boolean;
};

export type HomeShowcase = {
  ranking: OfferListItem[];
  tiers: Partial<Record<DiscountBand, OfferListItem[]>>;
};

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

export async function loadOffers(
  filters: OfferFilters = {},
): Promise<LoadResult<Page<OfferListItem>>> {
  try {
    return {
      data: await apiFetch<Page<OfferListItem>>(`/api/v1/offers${toQuery(filters)}`),
      unavailable: false,
    };
  } catch {
    return { data: emptyPage(), unavailable: true };
  }
}

export async function getOffers(
  filters: OfferFilters = {},
): Promise<Page<OfferListItem>> {
  return (await loadOffers(filters)).data;
}

export async function loadHomeShowcase(): Promise<LoadResult<HomeShowcase>> {
  try {
    return {
      data: await apiFetch<HomeShowcase>("/api/v1/offers/home"),
      unavailable: false,
    };
  } catch {
    return {
      data: { ranking: [], tiers: {} },
      unavailable: true,
    };
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

export async function getOfferAlternatives(
  id: string,
  pageSize = 8,
): Promise<Page<OfferListItem>> {
  try {
    return await apiFetch<Page<OfferListItem>>(
      `/api/v1/offers/${id}/alternatives?page_size=${pageSize}`,
    );
  } catch {
    return emptyPage();
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

export async function loadCategory(
  slug: string,
): Promise<LoadResult<Category | null>> {
  try {
    return {
      data: await apiFetch<Category>(`/api/v1/categories/${encodeURIComponent(slug)}`),
      unavailable: false,
    };
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return { data: null, unavailable: false };
    }
    return { data: null, unavailable: true };
  }
}

export async function getCategory(slug: string): Promise<Category | null> {
  return (await loadCategory(slug)).data;
}
