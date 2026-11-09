/** Types espelhando os schemas públicos da API FastAPI. */

export type DiscountBand = "none" | "low" | "medium" | "high" | "extreme";

export type OfferSort =
  | "discount_desc"
  | "ranking_desc"
  | "price_asc"
  | "newest";

export interface PageMeta {
  page: number;
  page_size: number;
  total: number;
  pages: number;
}

export interface Page<T> {
  items: T[];
  meta: PageMeta;
}

export interface OfferListItem {
  id: string;
  product_id: string;
  product_name: string;
  product_slug: string;
  product_image_url: string | null;
  ranking_score: string | number;
  store_name: string;
  affiliate_network: string | null;
  affiliate_url: string;
  external_offer_id: string;
  current_price: string | number;
  original_price: string | number | null;
  currency: string;
  discount_percent: string | number | null;
  discount_band: string | null;
  is_available: boolean;
  approval_status: string;
  created_at: string;
}

export interface OfferDetail extends OfferListItem {
  clicks_count: number;
  conversions_count: number;
  commission_rate: string | number | null;
  last_checked_at: string | null;
  updated_at: string | null;
  brand: string | null;
  average_rating: string | number | null;
  ratings_count: number;
  reviews_count: number;
  sales_count: number;
}

export interface ProductDetail {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  brand: string | null;
  image_url: string | null;
  external_sku: string | null;
  category_id: string;
  average_rating: string | number;
  ratings_count: number;
  reviews_count: number;
  sales_count: number;
  ranking_score: string | number;
  offers: OfferListItem[];
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  parent_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface OfferFilters {
  q?: string;
  store?: string;
  category_id?: string;
  band?: DiscountBand | string;
  min_discount?: number;
  max_price?: number;
  sort?: OfferSort;
  page?: number;
  page_size?: number;
}

export interface PricePoint {
  label: string;
  price: number;
}
