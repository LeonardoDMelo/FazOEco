"""Deterministic mock catalog used when ENABLE_SIMULATION_MODE=true."""

from __future__ import annotations

from decimal import Decimal
from typing import Any


MOCK_CATALOG: dict[str, list[dict[str, Any]]] = {
    "amazon": [
        {
            "external_offer_id": "B0MOCKAMZ01",
            "title": "Fone Bluetooth Noise Cancelling Pro",
            "gtin": "7891234567895",
            "brand": "SoundMax",
            "image_url": "https://cdn.example/amazon/fone.jpg",
            "affiliate_url": "https://www.amazon.com.br/dp/B0MOCKAMZ01?tag=fazoeeco-20",
            "current_price": Decimal("249.90"),
            "original_price": Decimal("399.90"),
            "currency": "BRL",
            "average_rating": Decimal("4.60"),
            "ratings_count": 1842,
            "reviews_count": 920,
            "sales_count": 5600,
            "is_available": True,
        },
        {
            "external_offer_id": "B0MOCKAMZ02",
            "title": "Cafeteira Espresso Compacta",
            "gtin": "7896543210987",
            "brand": "CaféLar",
            "image_url": "https://cdn.example/amazon/cafeteira.jpg",
            "affiliate_url": "https://www.amazon.com.br/dp/B0MOCKAMZ02?tag=fazoeeco-20",
            "current_price": Decimal("189.00"),
            "original_price": Decimal("279.00"),
            "currency": "BRL",
            "average_rating": Decimal("4.20"),
            "ratings_count": 430,
            "reviews_count": 210,
            "sales_count": 1200,
            "is_available": True,
        },
    ],
    "mercadolivre": [
        {
            "external_offer_id": "MLB1234567890",
            "title": "Fone Bluetooth Noise Cancelling Pro",
            "gtin": "7891234567895",
            "brand": "SoundMax",
            "image_url": "https://cdn.example/ml/fone.jpg",
            "affiliate_url": "https://www.mercadolivre.com.br/sec/MOCKML01",
            "current_price": Decimal("239.99"),
            "original_price": Decimal("389.99"),
            "currency": "BRL",
            "average_rating": Decimal("4.70"),
            "ratings_count": 2105,
            "reviews_count": 1100,
            "sales_count": 8900,
            "is_available": True,
        },
        {
            "external_offer_id": "MLB9876543210",
            "title": "Panela Elétrica Multifuncional 5L",
            "gtin": "7901234567890",
            "brand": "CookEasy",
            "image_url": "https://cdn.example/ml/panela.jpg",
            "affiliate_url": "https://www.mercadolivre.com.br/sec/MOCKML02",
            "current_price": Decimal("159.90"),
            "original_price": Decimal("229.90"),
            "currency": "BRL",
            "average_rating": Decimal("4.40"),
            "ratings_count": 980,
            "reviews_count": 450,
            "sales_count": 3400,
            "is_available": True,
        },
    ],
    "shopee": [
        {
            "external_offer_id": "SHOPEE-10001",
            "title": "Fone Bluetooth Noise Cancelling Pro",
            "gtin": "7891234567895",
            "brand": "SoundMax",
            "image_url": "https://cdn.example/shopee/fone.jpg",
            "affiliate_url": "https://shopee.com.br/product/10001?utm_source=fazoeeco",
            "current_price": Decimal("229.90"),
            "original_price": Decimal("359.90"),
            "currency": "BRL",
            "average_rating": Decimal("4.50"),
            "ratings_count": 760,
            "reviews_count": 310,
            "sales_count": 4100,
            "is_available": True,
        },
        {
            "external_offer_id": "SHOPEE-10002",
            "title": "Kit Organizador de Cabos 10un",
            "gtin": None,
            "brand": "OrganizeJá",
            "image_url": "https://cdn.example/shopee/cabos.jpg",
            "affiliate_url": "https://shopee.com.br/product/10002?utm_source=fazoeeco",
            "current_price": Decimal("29.90"),
            "original_price": Decimal("49.90"),
            "currency": "BRL",
            "average_rating": Decimal("4.10"),
            "ratings_count": 155,
            "reviews_count": 60,
            "sales_count": 9500,
            "is_available": True,
        },
    ],
}


def get_mock_offers(store_key: str, query: str | None = None) -> list[dict[str, Any]]:
    """Return mock offers optionally filtered by query substring (case-insensitive)."""
    items = list(MOCK_CATALOG.get(store_key, []))
    if not query:
        return items
    needle = query.strip().lower()
    return [item for item in items if needle in str(item.get("title", "")).lower()]
