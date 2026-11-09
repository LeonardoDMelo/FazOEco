"""API v1 public + admin route tests."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import hash_password
from app.main import create_app
from app.models.category import Category
from app.models.offer import Offer
from app.models.product import Product
from app.models.user import User


@pytest.fixture
async def api_ctx():
    """App client + seeded data sharing a NullPool engine (avoids loop leaks)."""
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
            email=f"admin_{suffix}@fazoeeco.test",
            username=f"admin_{suffix}",
            hashed_password=hash_password("Admin123!"),
            full_name="Admin Test",
            is_active=True,
            is_superuser=True,
        )
        operator = User(
            email=f"ops_{suffix}@fazoeeco.test",
            username=f"ops_{suffix}",
            hashed_password=hash_password("Ops12345!"),
            is_active=True,
            is_superuser=False,
        )
        category = Category(
            name=f"Eletronicos {suffix}",
            slug=f"eletronicos-{suffix}",
            description="Cat teste",
            is_active=True,
        )
        db.add_all([admin, operator, category])
        await db.flush()

        product = Product(
            category_id=category.id,
            name=f"Fone Bluetooth {suffix}",
            slug=f"fone-bluetooth-{suffix}",
            brand="SoundMax",
            image_url="https://cdn.example/fone.jpg",
            external_sku=f"SKU{suffix}",
            average_rating=Decimal("4.50"),
            ratings_count=100,
            reviews_count=40,
            sales_count=500,
            ranking_score=Decimal("82.50"),
            is_active=True,
        )
        db.add(product)
        await db.flush()

        approved = Offer(
            product_id=product.id,
            store_name="Amazon",
            affiliate_network="amazon_associates",
            affiliate_url=f"https://amazon.example/{suffix}-ok",
            external_offer_id=f"ASIN-{suffix}-OK",
            current_price=Decimal("199.90"),
            original_price=Decimal("299.90"),
            discount_percent=Decimal("33.34"),
            currency="BRL",
            is_available=True,
            approval_status="approved",
        )
        pending = Offer(
            product_id=product.id,
            store_name="Shopee",
            affiliate_network="shopee_affiliates",
            affiliate_url=f"https://shopee.example/{suffix}-pend",
            external_offer_id=f"SHP-{suffix}-PEND",
            current_price=Decimal("189.90"),
            original_price=Decimal("279.90"),
            discount_percent=Decimal("32.15"),
            currency="BRL",
            is_available=True,
            approval_status="pending",
        )
        db.add_all([approved, pending])
        await db.commit()

        data = {
            "admin_username": admin.username,
            "admin_password": "Admin123!",
            "ops_username": operator.username,
            "ops_password": "Ops12345!",
            "category_slug": category.slug,
            "product_id": str(product.id),
            "approved_offer_id": str(approved.id),
            "pending_offer_id": str(pending.id),
            "suffix": suffix,
            "ids": {
                "admin": admin.id,
                "operator": operator.id,
                "category": category.id,
                "product": product.id,
                "approved": approved.id,
                "pending": pending.id,
            },
        }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, data

    async with session_factory() as db:
        for model, obj_id in [
            (Offer, data["ids"]["approved"]),
            (Offer, data["ids"]["pending"]),
            (Product, data["ids"]["product"]),
            (Category, data["ids"]["category"]),
            (User, data["ids"]["admin"]),
            (User, data["ids"]["operator"]),
        ]:
            row = await db.get(model, obj_id)
            if row is not None:
                await db.delete(row)
        await db.commit()

    app.dependency_overrides.clear()
    await engine.dispose()
    get_settings.cache_clear()


async def _login(client: AsyncClient, username: str, password: str) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_health(api_ctx) -> None:
    client, _ = api_ctx
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_login_and_me(api_ctx) -> None:
    client, data = api_ctx
    token = await _login(client, data["admin_username"], data["admin_password"])
    me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me.status_code == 200
    body = me.json()
    assert body["username"] == data["admin_username"]
    assert body["is_superuser"] is True


@pytest.mark.asyncio
async def test_login_invalid_credentials(api_ctx) -> None:
    client, data = api_ctx
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": data["admin_username"], "password": "wrong"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_public_list_offers_hides_pending(api_ctx) -> None:
    client, data = api_ctx
    response = await client.get(
        "/api/v1/offers",
        params={"q": data["suffix"], "sort": "discount_desc"},
    )
    assert response.status_code == 200
    body = response.json()
    ids = {item["id"] for item in body["items"]}
    assert data["approved_offer_id"] in ids
    assert data["pending_offer_id"] not in ids
    assert body["meta"]["total"] >= 1


@pytest.mark.asyncio
async def test_public_featured_and_detail(api_ctx) -> None:
    client, data = api_ctx
    featured = await client.get("/api/v1/offers/featured", params={"band": "high"})
    assert featured.status_code == 200

    detail = await client.get(f"/api/v1/offers/{data['approved_offer_id']}")
    assert detail.status_code == 200
    assert detail.json()["discount_band"] in {"high", "medium", "extreme", "low"}

    pending_detail = await client.get(f"/api/v1/offers/{data['pending_offer_id']}")
    assert pending_detail.status_code == 404


@pytest.mark.asyncio
async def test_product_detail_and_categories(api_ctx) -> None:
    client, data = api_ctx
    product = await client.get(f"/api/v1/products/{data['product_id']}")
    assert product.status_code == 200
    assert len(product.json()["offers"]) == 1

    categories = await client.get("/api/v1/categories")
    assert categories.status_code == 200
    slugs = {c["slug"] for c in categories.json()}
    assert data["category_slug"] in slugs

    one = await client.get(f"/api/v1/categories/{data['category_slug']}")
    assert one.status_code == 200


@pytest.mark.asyncio
async def test_admin_requires_auth(api_ctx) -> None:
    client, _ = api_ctx
    response = await client.get("/api/v1/admin/connectors")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_requires_superuser(api_ctx) -> None:
    client, data = api_ctx
    token = await _login(client, data["ops_username"], data["ops_password"])
    response = await client.get(
        "/api/v1/admin/connectors",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_approve_reject_and_connectors(api_ctx) -> None:
    client, data = api_ctx
    token = await _login(client, data["admin_username"], data["admin_password"])
    headers = {"Authorization": f"Bearer {token}"}

    connectors = await client.get("/api/v1/admin/connectors", headers=headers)
    assert connectors.status_code == 200
    assert len(connectors.json()) == 3

    approve = await client.post(
        f"/api/v1/admin/offers/{data['pending_offer_id']}/approve",
        headers=headers,
    )
    assert approve.status_code == 200
    assert approve.json()["approval_status"] == "approved"

    public = await client.get("/api/v1/offers", params={"q": data["suffix"]})
    public_ids = {item["id"] for item in public.json()["items"]}
    assert data["pending_offer_id"] in public_ids

    reject = await client.post(
        f"/api/v1/admin/offers/{data['pending_offer_id']}/reject",
        headers=headers,
    )
    assert reject.status_code == 200
    assert reject.json()["approval_status"] == "rejected"

    run = await client.post(
        "/api/v1/admin/connectors/run",
        headers=headers,
        json={"query": "Fone", "limit": 2},
    )
    assert run.status_code == 200
    assert len(run.json()["results"]) == 3


@pytest.mark.asyncio
async def test_admin_settings_and_logs(api_ctx) -> None:
    client, data = api_ctx
    token = await _login(client, data["admin_username"], data["admin_password"])
    headers = {"Authorization": f"Bearer {token}"}

    ranking = await client.put(
        "/api/v1/admin/settings/ranking",
        headers=headers,
        json={
            "discount": 35,
            "rating": 20,
            "sales": 20,
            "reviews": 15,
            "engagement": 10,
        },
    )
    assert ranking.status_code == 200
    assert ranking.json()["key"] == "ranking_weights"

    bands = await client.put(
        "/api/v1/admin/settings/discount-bands",
        headers=headers,
        json={
            "min_discount_percent": 5,
            "max_discount_percent": 85,
            "bands": [{"name": "high", "min": "30", "max": "50"}],
        },
    )
    assert bands.status_code == 200

    logs = await client.get("/api/v1/admin/logs", headers=headers)
    assert logs.status_code == 200
    assert logs.json()["meta"]["total"] >= 1


@pytest.mark.asyncio
async def test_sort_params(api_ctx) -> None:
    client, data = api_ctx
    for sort in ("discount_desc", "ranking_desc", "price_asc", "newest"):
        response = await client.get(
            "/api/v1/offers",
            params={"q": data["suffix"], "sort": sort},
        )
        assert response.status_code == 200
