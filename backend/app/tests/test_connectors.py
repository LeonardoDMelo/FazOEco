"""Unit and simulated integration tests for marketplace connectors."""

from __future__ import annotations

from decimal import Decimal

import httpx
import pytest
import respx

from app.connectors import (
    AmazonConnector,
    MercadoLivreConnector,
    ShopeeConnector,
    run_connectors,
)
from app.connectors.base import ConnectorError
from app.core.config import Settings, get_settings


@pytest.fixture
def simulation_settings() -> Settings:
    get_settings.cache_clear()
    settings = Settings(
        ENABLE_SIMULATION_MODE=True,
        AMAZON_ACCESS_KEY=None,
        AMAZON_SECRET_KEY=None,
        AMAZON_PARTNER_TAG=None,
        MERCADOLIVRE_SITE_ID="MLB",
        MERCADOLIVRE_ACCESS_TOKEN=None,
        SHOPEE_PARTNER_ID=None,
        SHOPEE_PARTNER_KEY=None,
        SHOPEE_SHOP_ID=None,
    )
    yield settings
    get_settings.cache_clear()


@pytest.fixture
def live_settings() -> Settings:
    get_settings.cache_clear()
    settings = Settings(
        ENABLE_SIMULATION_MODE=False,
        AMAZON_ACCESS_KEY="ak",
        AMAZON_SECRET_KEY="sk",
        AMAZON_PARTNER_TAG="fazoeeco-20",
        MERCADOLIVRE_SITE_ID="MLB",
        MERCADOLIVRE_ACCESS_TOKEN="ml-token",
        MERCADOLIVRE_AFFILIATE_ID="aff-1",
        SHOPEE_PARTNER_ID="1001",
        SHOPEE_PARTNER_KEY="secret",
        SHOPEE_SHOP_ID="2002",
    )
    yield settings
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_simulation_mode_returns_mock_offers(simulation_settings: Settings) -> None:
    amazon = AmazonConnector(settings=simulation_settings)
    result = await amazon.fetch_offers("Fone", limit=10)

    assert result.success is True
    assert result.simulated is True
    assert len(result.offers) >= 1
    offer = result.offers[0]
    assert offer.store_name == "Amazon"
    assert offer.current_price > Decimal("0")
    assert offer.affiliate_url.startswith("http")
    assert offer.average_rating is not None
    assert offer.ratings_count > 0
    await amazon.aclose()


@pytest.mark.asyncio
async def test_all_connectors_simulation_in_parallel(simulation_settings: Settings) -> None:
    connectors = [
        AmazonConnector(settings=simulation_settings),
        MercadoLivreConnector(settings=simulation_settings),
        ShopeeConnector(settings=simulation_settings),
    ]
    results = await run_connectors(connectors, query="Fone", limit=5)

    assert len(results) == 3
    assert all(r.success for r in results)
    assert all(r.simulated for r in results)
    stores = {r.store_name for r in results}
    assert stores == {"Amazon", "Mercado Livre", "Shopee"}

    for connector in connectors:
        await connector.aclose()


@pytest.mark.asyncio
async def test_missing_credentials_isolated_failure(live_settings: Settings) -> None:
    amazon_settings = live_settings.model_copy(
        update={
            "amazon_access_key": None,
            "amazon_secret_key": None,
            "amazon_partner_tag": None,
            "enable_simulation_mode": False,
        }
    )
    ml_settings = live_settings.model_copy(update={"enable_simulation_mode": True})

    amazon = AmazonConnector(settings=amazon_settings)
    ml = MercadoLivreConnector(settings=ml_settings)

    results = await run_connectors([amazon, ml], query="oferta")
    by_store = {r.store_name: r for r in results}

    assert by_store["Amazon"].success is False
    assert "credentials" in (by_store["Amazon"].error or "").lower()
    assert by_store["Mercado Livre"].success is True

    await amazon.aclose()
    await ml.aclose()


@pytest.mark.asyncio
async def test_live_failure_does_not_break_other_stores(live_settings: Settings) -> None:
    amazon = AmazonConnector(settings=live_settings)
    shopee = ShopeeConnector(
        settings=live_settings.model_copy(update={"enable_simulation_mode": True})
    )

    with respx.mock(assert_all_called=False) as router:
        router.post("https://webservices.amazon.com.br/paapi5/searchitems").mock(
            return_value=httpx.Response(500, json={"message": "boom"})
        )
        results = await run_connectors([amazon, shopee], query="cafe")

    by_store = {r.store_name: r for r in results}
    assert by_store["Amazon"].success is False
    assert by_store["Shopee"].success is True
    assert by_store["Shopee"].simulated is True

    await amazon.aclose()
    await shopee.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_mercadolivre_live_normalization(live_settings: Settings) -> None:
    route = respx.get(
        url__regex=r"https://api\.mercadolibre\.com/sites/MLB/search.*"
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "id": "MLB999",
                        "title": "Panela Elétrica",
                        "price": 159.9,
                        "original_price": 229.9,
                        "currency_id": "BRL",
                        "permalink": "https://www.mercadolivre.com.br/panela",
                        "thumbnail": "https://cdn.example/panela.jpg",
                        "sold_quantity": 3400,
                        "status": "active",
                        "gtin": "7901234567890",
                        "rating": {"average": 4.4, "total": 980},
                    }
                ]
            },
        )
    )

    connector = MercadoLivreConnector(settings=live_settings)
    result = await connector.fetch_offers("Panela", limit=5)

    assert route.called
    assert result.success is True
    assert result.simulated is False
    assert len(result.offers) == 1
    offer = result.offers[0]
    assert offer.external_offer_id == "MLB999"
    assert offer.current_price == Decimal("159.9")
    assert offer.original_price == Decimal("229.9")
    assert offer.sales_count == 3400
    assert offer.average_rating == Decimal("4.4")
    assert "matt_tool=aff-1" in offer.affiliate_url
    await connector.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_shopee_live_normalization(live_settings: Settings) -> None:
    respx.post("https://open-api.affiliate.shopee.com.br/api/v1/product/search").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "products": [
                        {
                            "item_id": "SHOPEE-77",
                            "item_name": "Kit Cabos",
                            "price_info": {"price": 29.9, "original_price": 49.9},
                            "currency": "BRL",
                            "offer_link": "https://shopee.com.br/product/77",
                            "rating_star": 4.1,
                            "rating_count": 155,
                            "comment_count": 60,
                            "sales": 9500,
                            "stock": 12,
                        }
                    ]
                }
            },
        )
    )

    connector = ShopeeConnector(settings=live_settings)
    result = await connector.fetch_offers("Kit", limit=5)

    assert result.success is True
    offer = result.offers[0]
    assert offer.external_offer_id == "SHOPEE-77"
    assert offer.current_price == Decimal("29.9")
    assert offer.sales_count == 9500
    assert offer.reviews_count == 60
    await connector.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_amazon_live_normalization(live_settings: Settings) -> None:
    respx.post("https://webservices.amazon.com.br/paapi5/searchitems").mock(
        return_value=httpx.Response(
            200,
            json={
                "SearchResult": {
                    "Items": [
                        {
                            "ASIN": "B0TEST01",
                            "DetailPageURL": "https://www.amazon.com.br/dp/B0TEST01",
                            "ItemInfo": {
                                "Title": {"DisplayValue": "Fone Teste"},
                                "ByLineInfo": {
                                    "Brand": {"DisplayValue": "SoundMax"}
                                },
                            },
                            "Offers": {
                                "Listings": [
                                    {
                                        "Price": {"Amount": 249.9, "Currency": "BRL"},
                                        "SavingBasis": {"Amount": 399.9},
                                        "Availability": {"Type": "Now"},
                                    }
                                ]
                            },
                            "CustomerReviews": {"StarRating": 4.6, "Count": 1842},
                            "Images": {
                                "Primary": {"Large": {"URL": "https://cdn.example/a.jpg"}}
                            },
                        }
                    ]
                }
            },
        )
    )

    connector = AmazonConnector(settings=live_settings)
    result = await connector.fetch_offers("Fone", limit=5)

    assert result.success is True
    offer = result.offers[0]
    assert offer.external_offer_id == "B0TEST01"
    assert offer.brand == "SoundMax"
    assert offer.current_price == Decimal("249.9")
    assert offer.original_price == Decimal("399.9")
    assert offer.ratings_count == 1842
    await connector.aclose()


@pytest.mark.asyncio
async def test_request_maps_timeout_to_connector_error(live_settings: Settings) -> None:
    transport = httpx.MockTransport(lambda request: (_ for _ in ()).throw(httpx.TimeoutException("t")))
    client = httpx.AsyncClient(
        transport=transport,
        base_url="https://api.mercadolibre.com",
    )
    connector = MercadoLivreConnector(settings=live_settings, client=client)
    with pytest.raises(ConnectorError) as exc:
        await connector.request("GET", "/sites/MLB/search")
    assert exc.value.retriable is True
    await connector.aclose()
