"""Amazon Product Advertising / Associates connector."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.connectors.base import BaseConnector, ConnectorError, NormalizedOffer


class AmazonConnector(BaseConnector):
    """Fetches Amazon BR offers via PA-API style endpoints (or simulation)."""

    store_key = "amazon"
    store_name = "Amazon"
    affiliate_network = "amazon_associates"
    base_url = "https://webservices.amazon.com.br"

    def has_credentials(self) -> bool:
        return bool(
            self.settings.amazon_access_key
            and self.settings.amazon_secret_key
            and self.settings.amazon_partner_tag
        )

    def _default_headers(self) -> dict[str, str]:
        headers = super()._default_headers()
        if self.settings.amazon_access_key:
            headers["X-Amz-Access-Key"] = self.settings.amazon_access_key
        return headers

    def _normalize_item(self, item: dict[str, Any]) -> NormalizedOffer:
        item_info = item.get("ItemInfo") or {}
        offers = ((item.get("Offers") or {}).get("Listings") or [{}])[0]
        price_info = (offers.get("Price") or {})
        saving = (offers.get("SavingBasis") or {})
        title = ((item_info.get("Title") or {}).get("DisplayValue")) or item.get(
            "title", "Untitled"
        )
        external_id = str(item.get("ASIN") or item.get("external_offer_id") or "")
        if not external_id:
            raise ConnectorError(self.store_name, "item missing ASIN")

        current = price_info.get("Amount", item.get("current_price"))
        original = saving.get("Amount", item.get("original_price"))
        rating = (item.get("CustomerReviews") or {}).get("StarRating")
        ratings_count = int(
            (item.get("CustomerReviews") or {}).get("Count")
            or item.get("ratings_count")
            or 0
        )

        return NormalizedOffer(
            store_name=self.store_name,
            affiliate_network=self.affiliate_network,
            external_offer_id=external_id,
            title=str(title),
            affiliate_url=str(
                item.get("DetailPageURL")
                or item.get("affiliate_url")
                or f"https://www.amazon.com.br/dp/{external_id}"
                f"?tag={self.settings.amazon_partner_tag or 'fazoeeco-20'}"
            ),
            current_price=Decimal(str(current if current is not None else "0")),
            original_price=Decimal(str(original)) if original is not None else None,
            currency=str(price_info.get("Currency") or item.get("currency") or "BRL"),
            gtin=(item.get("gtin") or (item.get("Identifiers") or {}).get("EAN")),
            brand=((item_info.get("ByLineInfo") or {}).get("Brand") or {}).get(
                "DisplayValue"
            )
            or item.get("brand"),
            image_url=(
                ((item.get("Images") or {}).get("Primary") or {}).get("Large") or {}
            ).get("URL")
            or item.get("image_url"),
            average_rating=Decimal(str(rating)) if rating is not None else None,
            ratings_count=ratings_count,
            reviews_count=int(item.get("reviews_count") or ratings_count),
            sales_count=item.get("sales_count"),
            is_available=bool(offers.get("Availability", {}).get("Type", "Now") != "OutOfStock")
            if offers
            else bool(item.get("is_available", True)),
            raw=item,
        )

    async def _fetch_live(self, query: str, *, limit: int) -> list[NormalizedOffer]:
        """
        Live PA-API SearchItems call.

        Note: real Amazon PA-API requires AWS SigV4. This connector posts to the
        configured search path with partner credentials; signing can be layered later.
        """
        payload = {
            "Keywords": query or "ofertas",
            "PartnerTag": self.settings.amazon_partner_tag,
            "PartnerType": "Associates",
            "Marketplace": "www.amazon.com.br",
            "ItemCount": min(limit, 10),
            "Resources": [
                "ItemInfo.Title",
                "ItemInfo.ByLineInfo",
                "Offers.Listings.Price",
                "Offers.Listings.SavingBasis",
                "Offers.Listings.Availability.Type",
                "Images.Primary.Large",
                "CustomerReviews.StarRating",
                "CustomerReviews.Count",
            ],
        }
        response = await self.request(
            "POST",
            "/paapi5/searchitems",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        data = response.json()
        items = ((data.get("SearchResult") or {}).get("Items")) or data.get("items") or []
        return [self._normalize_item(item) for item in items[:limit]]
