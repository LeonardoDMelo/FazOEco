"""Shopee Affiliate / product search connector."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.connectors.base import BaseConnector, ConnectorError, NormalizedOffer


class ShopeeConnector(BaseConnector):
    """Fetches Shopee BR offers via affiliate API (or simulation)."""

    store_key = "shopee"
    store_name = "Shopee"
    affiliate_network = "shopee_affiliates"
    base_url = "https://open-api.affiliate.shopee.com.br"

    def has_credentials(self) -> bool:
        return bool(
            self.settings.shopee_partner_id
            and self.settings.shopee_partner_key
            and self.settings.shopee_shop_id
        )

    def _default_headers(self) -> dict[str, str]:
        headers = super()._default_headers()
        if self.settings.shopee_partner_id:
            headers["X-Shopee-Partner-Id"] = self.settings.shopee_partner_id
        return headers

    def _normalize_item(self, item: dict[str, Any]) -> NormalizedOffer:
        external_id = str(
            item.get("item_id")
            or item.get("product_id")
            or item.get("external_offer_id")
            or ""
        )
        if not external_id:
            raise ConnectorError(self.store_name, "item missing product id")

        price_info = item.get("price_info") or {}
        current = price_info.get("price", item.get("current_price") or item.get("price"))
        original = price_info.get(
            "original_price", item.get("original_price") or item.get("price_before_discount")
        )
        rating = item.get("rating_star", item.get("average_rating"))
        affiliate = (
            item.get("offer_link")
            or item.get("affiliate_url")
            or f"https://shopee.com.br/product/{external_id}"
        )

        return NormalizedOffer(
            store_name=self.store_name,
            affiliate_network=self.affiliate_network,
            external_offer_id=external_id,
            title=str(item.get("item_name") or item.get("title") or "Untitled"),
            affiliate_url=str(affiliate),
            current_price=Decimal(str(current if current is not None else "0")),
            original_price=Decimal(str(original)) if original is not None else None,
            currency=str(item.get("currency") or "BRL"),
            gtin=item.get("gtin") or item.get("ean"),
            brand=item.get("brand"),
            image_url=(item.get("image_url") or (item.get("image_list") or [None])[0]),
            average_rating=Decimal(str(rating)) if rating is not None else None,
            ratings_count=int(item.get("rating_count") or item.get("ratings_count") or 0),
            reviews_count=int(item.get("comment_count") or item.get("reviews_count") or 0),
            sales_count=(
                int(item["sales"]) if item.get("sales") is not None else item.get("sales_count")
            ),
            is_available=bool(item.get("is_available", item.get("stock", 1) not in {0, "0"})),
            raw=item,
        )

    async def _fetch_live(self, query: str, *, limit: int) -> list[NormalizedOffer]:
        payload = {
            "partner_id": self.settings.shopee_partner_id,
            "shop_id": self.settings.shopee_shop_id,
            "keyword": query or "ofertas",
            "limit": min(limit, 50),
        }
        response = await self.request(
            "POST",
            "/api/v1/product/search",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        data = response.json()
        items = (
            ((data.get("data") or {}).get("products"))
            or data.get("products")
            or data.get("items")
            or []
        )
        return [self._normalize_item(item) for item in items[:limit]]
