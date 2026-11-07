"""Mercado Livre public/affiliate search connector."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from urllib.parse import urlencode

from app.connectors.base import BaseConnector, NormalizedOffer


class MercadoLivreConnector(BaseConnector):
    """Fetches Mercado Livre BR search results (or simulation)."""

    store_key = "mercadolivre"
    store_name = "Mercado Livre"
    affiliate_network = "mercado_livre_affiliates"
    base_url = "https://api.mercadolibre.com"

    def has_credentials(self) -> bool:
        # Public search works without token; affiliate tag improves tracking.
        # Require at least site id; treat access token as optional enrichment.
        return bool(self.settings.mercadolivre_site_id)

    def _default_headers(self) -> dict[str, str]:
        headers = super()._default_headers()
        if self.settings.mercadolivre_access_token:
            headers["Authorization"] = f"Bearer {self.settings.mercadolivre_access_token}"
        return headers

    def _affiliate_url(self, permalink: str, external_id: str) -> str:
        tag = self.settings.mercadolivre_affiliate_id
        if tag:
            sep = "&" if "?" in permalink else "?"
            return f"{permalink}{sep}matt_tool={tag}"
        return permalink or f"https://www.mercadolivre.com.br/p/{external_id}"

    def _normalize_item(self, item: dict[str, Any]) -> NormalizedOffer:
        external_id = str(item.get("id") or item.get("external_offer_id") or "")
        current = item.get("price", item.get("current_price"))
        original = item.get("original_price", item.get("original_price"))
        rating_obj = item.get("rating") or {}
        permalink = str(item.get("permalink") or item.get("affiliate_url") or "")

        return NormalizedOffer(
            store_name=self.store_name,
            affiliate_network=self.affiliate_network,
            external_offer_id=external_id,
            title=str(item.get("title") or "Untitled"),
            affiliate_url=self._affiliate_url(permalink, external_id),
            current_price=Decimal(str(current if current is not None else "0")),
            original_price=Decimal(str(original)) if original is not None else None,
            currency=str(item.get("currency_id") or item.get("currency") or "BRL"),
            gtin=item.get("gtin") or item.get("ean"),
            brand=item.get("brand") or item.get("official_store_name"),
            image_url=(item.get("thumbnail") or item.get("image_url")),
            average_rating=(
                Decimal(str(rating_obj["average"]))
                if rating_obj.get("average") is not None
                else (
                    Decimal(str(item["average_rating"]))
                    if item.get("average_rating") is not None
                    else None
                )
            ),
            ratings_count=int(
                rating_obj.get("total")
                or item.get("ratings_count")
                or 0
            ),
            reviews_count=int(item.get("reviews_count") or rating_obj.get("total") or 0),
            sales_count=(
                int(item["sold_quantity"])
                if item.get("sold_quantity") is not None
                else item.get("sales_count")
            ),
            is_available=(
                bool(item["is_available"])
                if "is_available" in item
                else str(item.get("status") or "active") == "active"
            ),
            raw=item,
        )

    async def _fetch_live(self, query: str, *, limit: int) -> list[NormalizedOffer]:
        site = self.settings.mercadolivre_site_id or "MLB"
        params = {
            "q": query or "ofertas",
            "limit": min(limit, 50),
            "status": "active",
        }
        # Keep URL explicit for easier mocking in tests
        path = f"/sites/{site}/search?{urlencode(params)}"
        response = await self.request("GET", path)
        data = response.json()
        results = data.get("results") or data.get("items") or []
        return [self._normalize_item(item) for item in results[:limit]]
