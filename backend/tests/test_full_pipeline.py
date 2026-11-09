"""
Suíte E2E — 20 casos de teste obrigatórios do pipeline FazOEco.

Cobertura: pricing → ranking → dedup → conectores → API pública/admin →
segurança (headers, SSRF, rate limit) → ofertas expiradas (SEO).
"""

from __future__ import annotations

import os
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

os.environ.setdefault("RATE_LIMIT_ENABLED", "false")

from app.connectors import AmazonConnector, MercadoLivreConnector, ShopeeConnector, run_connectors
from app.connectors.base import ConnectorError
from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import get_rate_limiter, hash_password
from app.main import create_app
from app.models.category import Category
from app.models.offer import Offer
from app.models.product import Product
from app.models.user import User
from app.services.deduplication_service import (
    DedupAction,
    DeduplicationService,
    OfferIdentity,
)
from app.services.http_client import SSRFError, assert_url_safe
from app.services.pricing_service import PricingService
from app.services.ranking_service import RankingInput, RankingService


@pytest.fixture
async def pipeline_ctx():
    """App ASGI + dados mínimos para o pipeline completo."""
    get_settings.cache_clear()
    settings = get_settings()
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    suffix = uuid4().hex[:8]
    async with session_factory() as db:
        admin = User(
            email=f"pipe_admin_{suffix}@fazoeeco.test",
            username=f"pipe_admin_{suffix}",
            hashed_password=hash_password("Admin123!"),
            is_active=True,
            is_superuser=True,
        )
        category = Category(
            name=f"Pipeline {suffix}",
            slug=f"pipeline-{suffix}",
            is_active=True,
        )
        db.add_all([admin, category])
        await db.flush()

        product = Product(
            category_id=category.id,
            name=f"Notebook Pipeline {suffix}",
            slug=f"notebook-pipeline-{suffix}",
            brand="EcoBrand",
            average_rating=Decimal("4.60"),
            ratings_count=200,
            reviews_count=80,
            sales_count=900,
            ranking_score=Decimal("88.00"),
            is_active=True,
        )
        db.add(product)
        await db.flush()

        active = Offer(
            product_id=product.id,
            store_name="Amazon",
            affiliate_network="amazon_associates",
            affiliate_url=f"https://amazon.example/{suffix}-active",
            external_offer_id=f"PIPE-{suffix}-A",
            current_price=Decimal("149.90"),
            original_price=Decimal("229.90"),
            discount_percent=Decimal("34.80"),
            currency="BRL",
            is_available=True,
            approval_status="approved",
        )
        pending = Offer(
            product_id=product.id,
            store_name="Shopee",
            affiliate_network="shopee_affiliates",
            affiliate_url=f"https://shopee.example/{suffix}-pend",
            external_offer_id=f"PIPE-{suffix}-P",
            current_price=Decimal("139.90"),
            original_price=Decimal("219.90"),
            discount_percent=Decimal("36.38"),
            currency="BRL",
            is_available=True,
            approval_status="pending",
        )
        expired = Offer(
            product_id=product.id,
            store_name="Mercado Livre",
            affiliate_network="mercado_livre_affiliates",
            affiliate_url=f"https://ml.example/{suffix}-exp",
            external_offer_id=f"PIPE-{suffix}-E",
            current_price=Decimal("159.90"),
            original_price=Decimal("249.90"),
            discount_percent=Decimal("36.01"),
            currency="BRL",
            is_available=False,
            approval_status="approved",
        )
        db.add_all([active, pending, expired])
        await db.commit()

        data = {
            "admin_username": admin.username,
            "admin_password": "Admin123!",
            "suffix": suffix,
            "category_slug": category.slug,
            "product_id": str(product.id),
            "active_offer_id": str(active.id),
            "pending_offer_id": str(pending.id),
            "expired_offer_id": str(expired.id),
            "ids": {
                "admin": admin.id,
                "category": category.id,
                "product": product.id,
                "active": active.id,
                "pending": pending.id,
                "expired": expired.id,
            },
        }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, data, app

    async with session_factory() as db:
        for model, obj_id in [
            (Offer, data["ids"]["active"]),
            (Offer, data["ids"]["pending"]),
            (Offer, data["ids"]["expired"]),
            (Product, data["ids"]["product"]),
            (Category, data["ids"]["category"]),
            (User, data["ids"]["admin"]),
        ]:
            row = await db.get(model, obj_id)
            if row is not None:
                await db.delete(row)
        await db.commit()

    app.dependency_overrides.clear()
    await engine.dispose()
    get_settings.cache_clear()
    get_rate_limiter().reset()


# ---------------------------------------------------------------------------
# TC01–TC07 — motor de negócio
# ---------------------------------------------------------------------------


def test_tc01_pricing_discount_decimal_half_up() -> None:
    """TC01: desconto Decimal com arredondamento HALF_UP em 2 casas."""
    service = PricingService()
    assert service.calculate_discount_percent("199.90", "299.90") == Decimal("33.34")


def test_tc02_pricing_discount_bands() -> None:
    """TC02: faixas dinâmicas none/low/medium/high/extreme."""
    service = PricingService()
    assert service.categorize_band(Decimal("4.99")) == "none"
    assert service.categorize_band(Decimal("10")) == "low"
    assert service.categorize_band(Decimal("20")) == "medium"
    assert service.categorize_band(Decimal("35")) == "high"
    assert service.categorize_band(Decimal("55")) == "extreme"


def test_tc03_pricing_publish_criteria() -> None:
    """TC03: oferta com desconto fraco não é publicável."""
    service = PricingService()
    weak = service.evaluate("96.00", "100.00")
    assert weak.is_publishable is False
    assert "discount_below_minimum" in weak.reasons

    strong = service.evaluate("70.00", "100.00")
    assert strong.is_publishable is True
    assert strong.band == "high"


def test_tc04_ranking_score_bounds() -> None:
    """TC04: score de qualidade permanece em [0, 100]."""
    service = RankingService()
    result = service.calculate(
        RankingInput(
            discount_percent=Decimal("40"),
            average_rating=Decimal("4.8"),
            ratings_count=500,
            reviews_count=120,
            sales_count=2000,
        )
    )
    assert Decimal("0") <= result.total_score <= Decimal("100")


def test_tc05_ranking_missing_pillars_redistribution() -> None:
    """TC05: ausência de popularidade redistribui pesos e expõe missing_pillars."""
    service = RankingService()
    result = service.calculate(
        RankingInput(
            discount_percent=Decimal("30"),
            average_rating=Decimal("4.5"),
            ratings_count=10,
            reviews_count=None,
            sales_count=None,
        )
    )
    assert "sales" in result.missing_pillars or "reviews" in result.missing_pillars
    assert result.redistributed is True
    assert Decimal("0") <= result.total_score <= Decimal("100")


def test_tc06_dedup_normalize_gtin() -> None:
    """TC06: normalização GTIN/EAN remove máscara e valida tamanho."""
    assert DeduplicationService.normalize_gtin("789.1234.567-895") == "7891234567895"
    assert DeduplicationService.normalize_gtin("123") is None
    assert DeduplicationService.normalize_gtin("0000000000000") is None


@pytest.mark.asyncio
async def test_tc07_dedup_update_existing_offer(pipeline_ctx) -> None:
    """TC07: mesma loja + external_id decide UPDATE_OFFER."""
    _, data, _ = pipeline_ctx
    get_settings.cache_clear()
    settings = get_settings()
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    service = DeduplicationService()
    async with session_factory() as db:
        decision = await service.resolve(
            db,
            OfferIdentity(
                store_name="Amazon",
                external_offer_id=f"PIPE-{data['suffix']}-A",
                affiliate_url="https://amazon.example/dup",
                gtin="7891234567895",
            ),
        )
    await engine.dispose()
    assert decision.action == DedupAction.UPDATE_OFFER
    assert decision.should_update_existing is True
    assert decision.offer_id is not None


# ---------------------------------------------------------------------------
# TC08–TC09 — conectores
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tc08_connectors_simulation_returns_offers() -> None:
    """TC08: modo simulação retorna ofertas normalizadas por loja."""
    get_settings.cache_clear()
    connectors = [AmazonConnector(), MercadoLivreConnector(), ShopeeConnector()]
    try:
        results = await run_connectors(connectors, query="fone", limit=3)
    finally:
        for c in connectors:
            await c.aclose()
    assert len(results) == 3
    assert all(r.success for r in results)
    assert all(r.simulated for r in results)
    assert sum(len(r.offers) for r in results) >= 1


@pytest.mark.asyncio
async def test_tc09_connector_isolates_failure() -> None:
    """TC09: falha em um conector não derruba os demais do pipeline."""

    class BoomConnector(AmazonConnector):
        async def _fetch_simulated(self, query: str, *, limit: int):
            raise ConnectorError(self.store_name, "forced failure", retriable=False)

    boom = BoomConnector()
    ok = MercadoLivreConnector()
    try:
        results = await run_connectors([boom, ok], query="fone", limit=2)
    finally:
        await boom.aclose()
        await ok.aclose()

    assert results[0].success is False
    assert results[0].error is not None
    assert results[1].success is True
    assert results[1].simulated is True


# ---------------------------------------------------------------------------
# TC10–TC17 — API pública / admin
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tc10_health_and_security_headers(pipeline_ctx) -> None:
    """TC10: /api/health OK e headers de segurança presentes."""
    client, _, _ = pipeline_ctx
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert "content-security-policy" in {k.lower() for k in response.headers.keys()}


@pytest.mark.asyncio
async def test_tc11_login_success_jwt(pipeline_ctx) -> None:
    """TC11: login admin devolve access_token JWT."""
    client, data, _ = pipeline_ctx
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": data["admin_username"], "password": data["admin_password"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 20


@pytest.mark.asyncio
async def test_tc12_login_invalid_credentials(pipeline_ctx) -> None:
    """TC12: credenciais inválidas retornam 401."""
    client, data, _ = pipeline_ctx
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": data["admin_username"], "password": "wrong-password"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_tc13_public_search_hides_pending(pipeline_ctx) -> None:
    """TC13: busca pública lista aprovadas e oculta pending."""
    client, data, _ = pipeline_ctx
    response = await client.get("/api/v1/offers", params={"q": data["suffix"]})
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()["items"]}
    assert data["active_offer_id"] in ids
    assert data["pending_offer_id"] not in ids


@pytest.mark.asyncio
async def test_tc14_featured_and_offer_detail(pipeline_ctx) -> None:
    """TC14: destaques e detalhe de oferta ativa."""
    client, data, _ = pipeline_ctx
    featured = await client.get("/api/v1/offers/featured", params={"band": "high"})
    assert featured.status_code == 200
    detail = await client.get(f"/api/v1/offers/{data['active_offer_id']}")
    assert detail.status_code == 200
    assert detail.json()["brand"] == "EcoBrand"
    assert detail.json()["is_available"] is True


@pytest.mark.asyncio
async def test_tc15_expired_offer_seo_and_alternatives(pipeline_ctx) -> None:
    """TC15: oferta expirada permanece 200 (SEO) e expõe alternativas."""
    client, data, _ = pipeline_ctx
    detail = await client.get(f"/api/v1/offers/{data['expired_offer_id']}")
    assert detail.status_code == 200
    assert detail.json()["is_available"] is False

    alts = await client.get(f"/api/v1/offers/{data['expired_offer_id']}/alternatives")
    assert alts.status_code == 200
    alt_items = alts.json()["items"]
    alt_ids = {item["id"] for item in alt_items}
    assert data["expired_offer_id"] not in alt_ids
    assert data["active_offer_id"] in alt_ids


@pytest.mark.asyncio
async def test_tc16_admin_requires_auth(pipeline_ctx) -> None:
    """TC16: rotas admin exigem JWT."""
    client, _, _ = pipeline_ctx
    response = await client.get("/api/v1/admin/connectors")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_tc17_admin_approve_pending_offer(pipeline_ctx) -> None:
    """TC17: admin aprova oferta pending e ela passa a listagem pública."""
    client, data, _ = pipeline_ctx
    login = await client.post(
        "/api/v1/auth/login",
        data={"username": data["admin_username"], "password": data["admin_password"]},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    approve = await client.post(
        f"/api/v1/admin/offers/{data['pending_offer_id']}/approve",
        headers=headers,
    )
    assert approve.status_code == 200
    assert approve.json()["approval_status"] == "approved"
    public = await client.get("/api/v1/offers", params={"q": data["suffix"]})
    assert data["pending_offer_id"] in {i["id"] for i in public.json()["items"]}


# ---------------------------------------------------------------------------
# TC18–TC20 — segurança
# ---------------------------------------------------------------------------


def test_tc18_ssrf_blocks_private_and_metadata() -> None:
    """TC18: SSRF bloqueia localhost, RFC1918 e metadata cloud."""
    blocked = [
        "http://127.0.0.1/latest",
        "https://169.254.169.254/latest/meta-data/",
        "https://10.0.0.5/admin",
        "https://192.168.1.1/",
        "https://evil.example/path",
    ]
    for url in blocked:
        with pytest.raises(SSRFError):
            assert_url_safe(url, resolve_dns=False)


def test_tc19_ssrf_allows_marketplace_hosts() -> None:
    """TC19: hosts oficiais de marketplace/API são permitidos."""
    allowed = [
        "https://webservices.amazon.com.br/paapi5/searchitems",
        "https://api.mercadolibre.com/sites/MLB/search",
        "https://open-api.affiliate.shopee.com.br/api/v1/products",
    ]
    for url in allowed:
        assert assert_url_safe(url, resolve_dns=False) == url


@pytest.mark.asyncio
async def test_tc20_rate_limit_login_returns_429(pipeline_ctx) -> None:
    """TC20: rate limit no login responde 429 após exceder a janela."""
    client, data, _ = pipeline_ctx
    get_settings.cache_clear()
    os.environ["RATE_LIMIT_ENABLED"] = "true"
    os.environ["RATE_LIMIT_LOGIN"] = "3/minute"
    get_settings.cache_clear()
    get_rate_limiter().reset()

    try:
        statuses: list[int] = []
        for _ in range(5):
            response = await client.post(
                "/api/v1/auth/login",
                data={"username": data["admin_username"], "password": "wrong"},
            )
            statuses.append(response.status_code)
        assert 429 in statuses
        assert statuses.count(429) >= 1
    finally:
        os.environ["RATE_LIMIT_ENABLED"] = "false"
        get_settings.cache_clear()
        get_rate_limiter().reset()
