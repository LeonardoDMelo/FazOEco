"""Async ingestion / revalidation jobs for affiliate offers."""

from __future__ import annotations

import logging
import re
import unicodedata
from contextlib import asynccontextmanager
from decimal import Decimal
from typing import Any, AsyncIterator
from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.connectors import (
    AmazonConnector,
    MercadoLivreConnector,
    NormalizedOffer,
    ShopeeConnector,
)
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.timezone import utc_now
from app.models.category import Category
from app.models.log import Log
from app.models.offer import Offer
from app.models.price_history import PriceHistory
from app.models.product import Product
from app.models.setting import Setting
from app.services.deduplication_service import DeduplicationService, OfferIdentity
from app.services.pricing_service import PricingConfig, PricingService
from app.services.ranking_service import RankingInput, RankingService

logger = logging.getLogger(__name__)

SYSTEM_SETTING_KEY = "system_settings"
LOCK_INGESTION = 810_001
LOCK_REVALIDATION = 810_002
MIN_DISCOUNT_FOR_INGESTION = Decimal("20.00")

_slug_re = re.compile(r"[^a-z0-9]+")


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    slug = _slug_re.sub("-", normalized.lower()).strip("-")
    return (slug or "produto")[:240]


@asynccontextmanager
async def job_lock(session: AsyncSession, lock_id: int) -> AsyncIterator[bool]:
    """PostgreSQL session-level advisory lock to prevent overlapping runs."""
    acquired = bool(
        (await session.execute(text("SELECT pg_try_advisory_lock(:lock_id)"), {"lock_id": lock_id})).scalar()
    )
    try:
        yield acquired
    finally:
        if acquired:
            await session.execute(
                text("SELECT pg_advisory_unlock(:lock_id)"),
                {"lock_id": lock_id},
            )


async def _write_log(
    session: AsyncSession,
    *,
    level: str,
    source: str,
    message: str,
    context: dict[str, Any] | None = None,
) -> None:
    session.add(
        Log(
            level=level,
            source=source,
            message=message,
            context=context,
        )
    )


async def _load_system_settings(session: AsyncSession) -> dict[str, Any]:
    result = await session.execute(select(Setting).where(Setting.key == SYSTEM_SETTING_KEY))
    setting = result.scalar_one_or_none()
    if setting and isinstance(setting.value, dict):
        return dict(setting.value)
    return {
        "auto_publish_enabled": False,
        "simulation_mode_preferred": True,
        "price_revalidation_hours": 6,
        "price_revalidation_minutes": 30,
        "connectors_enabled": {
            "amazon": True,
            "mercadolivre": True,
            "shopee": True,
        },
    }


async def _ensure_default_category(session: AsyncSession) -> Category:
    result = await session.execute(select(Category).where(Category.slug == "geral"))
    category = result.scalar_one_or_none()
    if category:
        return category
    category = Category(
        name="Geral",
        slug="geral",
        description="Categoria padrão para ingestão automática",
        is_active=True,
    )
    session.add(category)
    await session.flush()
    return category


def _connector_factory() -> dict[str, AmazonConnector | MercadoLivreConnector | ShopeeConnector]:
    settings = get_settings()
    return {
        "amazon": AmazonConnector(settings=settings),
        "mercadolivre": MercadoLivreConnector(settings=settings),
        "shopee": ShopeeConnector(settings=settings),
    }


def _pricing() -> PricingService:
    return PricingService(
        PricingConfig(
            min_discount_percent=MIN_DISCOUNT_FOR_INGESTION,
            max_discount_percent=Decimal("90.00"),
        )
    )


def evaluate_offer_for_ingestion(
    normalized: NormalizedOffer,
    *,
    pricing: PricingService | None = None,
    ranking: RankingService | None = None,
) -> dict[str, Any]:
    """Pure evaluation used by the job and unit tests."""
    pricing = pricing or _pricing()
    ranking = ranking or RankingService()
    price_result = pricing.evaluate(
        normalized.current_price,
        normalized.original_price,
        is_available=normalized.is_available,
    )
    rank = ranking.calculate(
        RankingInput(
            discount_percent=price_result.discount_percent,
            average_rating=normalized.average_rating,
            ratings_count=normalized.ratings_count,
            sales_count=normalized.sales_count,
            reviews_count=normalized.reviews_count,
            is_available=normalized.is_available,
        )
    )
    return {
        "pricing": price_result,
        "ranking_score": rank.total_score,
        "eligible": price_result.is_publishable,
        "discount_band": price_result.band,
    }


async def _upsert_from_normalized(
    session: AsyncSession,
    normalized: NormalizedOffer,
    *,
    auto_publish: bool,
    category: Category,
) -> str:
    """Persist product/offer; returns action label."""
    evaluation = evaluate_offer_for_ingestion(normalized)
    if not evaluation["eligible"]:
        return "skipped_pricing"

    dedup = DeduplicationService()
    identity = OfferIdentity(
        store_name=normalized.store_name,
        external_offer_id=normalized.external_offer_id,
        affiliate_url=normalized.affiliate_url,
        gtin=normalized.gtin,
    )
    decision = await dedup.resolve(session, identity)
    pricing_result = evaluation["pricing"]
    ranking_score = evaluation["ranking_score"]
    approval = "approved" if auto_publish else "pending"
    now = utc_now()

    product: Product | None = None
    if decision.product_id:
        product = await session.get(Product, decision.product_id)

    if decision.action.value == "create_product" or product is None:
        slug_base = _slugify(normalized.title)
        slug = f"{slug_base}-{uuid4().hex[:6]}"
        product = Product(
            category_id=category.id,
            name=normalized.title[:255],
            slug=slug,
            brand=normalized.brand,
            image_url=normalized.image_url,
            external_sku=decision.normalized_gtin or normalized.gtin,
            average_rating=normalized.average_rating or Decimal("0.00"),
            ratings_count=normalized.ratings_count,
            reviews_count=normalized.reviews_count,
            sales_count=normalized.sales_count or 0,
            ranking_score=ranking_score,
            is_active=True,
        )
        session.add(product)
        await session.flush()
        action = "created_product_offer"
    else:
        product.name = normalized.title[:255]
        product.brand = normalized.brand or product.brand
        product.image_url = normalized.image_url or product.image_url
        product.average_rating = normalized.average_rating or product.average_rating
        product.ratings_count = normalized.ratings_count or product.ratings_count
        product.reviews_count = normalized.reviews_count or product.reviews_count
        if normalized.sales_count is not None:
            product.sales_count = normalized.sales_count
        product.ranking_score = ranking_score
        action = "updated_product"

    if decision.offer_id:
        offer = await session.get(Offer, decision.offer_id)
        if offer is None:
            return "offer_missing"
        previous_price = offer.current_price
        offer.current_price = pricing_result.current_price
        offer.original_price = pricing_result.original_price
        offer.discount_percent = pricing_result.discount_percent
        offer.affiliate_url = normalized.affiliate_url
        offer.affiliate_network = normalized.affiliate_network
        offer.is_available = normalized.is_available
        offer.last_checked_at = now
        if auto_publish and offer.approval_status == "pending":
            offer.approval_status = "approved"
        if previous_price != offer.current_price:
            session.add(
                PriceHistory(offer_id=offer.id, price=offer.current_price, recorded_at=now)
            )
        return "updated_offer"

    offer = Offer(
        product_id=product.id,
        store_name=normalized.store_name,
        affiliate_network=normalized.affiliate_network,
        affiliate_url=normalized.affiliate_url,
        external_offer_id=normalized.external_offer_id,
        current_price=pricing_result.current_price,
        original_price=pricing_result.original_price,
        currency=normalized.currency,
        discount_percent=pricing_result.discount_percent,
        is_available=normalized.is_available,
        approval_status=approval,
        last_checked_at=now,
    )
    session.add(offer)
    await session.flush()
    session.add(PriceHistory(offer_id=offer.id, price=offer.current_price, recorded_at=now))
    return action if action.startswith("created") else "created_offer"


async def run_deal_ingestion_job(query: str = "ofertas") -> dict[str, Any]:
    """Collect offers from active connectors, dedupe, score and persist."""
    summary: dict[str, Any] = {
        "job": "ingestion",
        "processed": 0,
        "created": 0,
        "updated": 0,
        "skipped": 0,
        "errors": [],
        "stores": {},
    }

    async with AsyncSessionLocal() as session:
        async with job_lock(session, LOCK_INGESTION) as acquired:
            if not acquired:
                summary["skipped_lock"] = True
                await _write_log(
                    session,
                    level="WARNING",
                    source="scheduler.ingestion",
                    message="Ingestion skipped: lock not acquired",
                )
                await session.commit()
                return summary

            system = await _load_system_settings(session)
            auto_publish = bool(system.get("auto_publish_enabled"))
            enabled_map = system.get("connectors_enabled") or {}
            category = await _ensure_default_category(session)
            connectors = _connector_factory()

            try:
                for store_key, connector in connectors.items():
                    if enabled_map.get(store_key, True) is False:
                        summary["stores"][store_key] = {"skipped": "disabled"}
                        continue

                    store_stats = {"ok": 0, "skipped": 0, "errors": 0}
                    try:
                        result = await connector.fetch_offers(query, limit=20)
                        if not result.success:
                            store_stats["errors"] += 1
                            summary["errors"].append(result.error or store_key)
                            await _write_log(
                                session,
                                level="ERROR",
                                source="scheduler.ingestion",
                                message=f"Connector failed: {store_key}",
                                context={"error": result.error},
                            )
                        else:
                            for item in result.offers:
                                summary["processed"] += 1
                                try:
                                    action = await _upsert_from_normalized(
                                        session,
                                        item,
                                        auto_publish=auto_publish,
                                        category=category,
                                    )
                                    if action.startswith("created"):
                                        summary["created"] += 1
                                        store_stats["ok"] += 1
                                    elif action.startswith("updated"):
                                        summary["updated"] += 1
                                        store_stats["ok"] += 1
                                    else:
                                        summary["skipped"] += 1
                                        store_stats["skipped"] += 1
                                except Exception as exc:  # noqa: BLE001
                                    store_stats["errors"] += 1
                                    summary["errors"].append(str(exc))
                                    logger.exception("ingestion item failed store=%s", store_key)
                    except Exception as exc:  # noqa: BLE001
                        store_stats["errors"] += 1
                        summary["errors"].append(f"{store_key}: {exc}")
                        logger.exception("ingestion store failed store=%s", store_key)
                    finally:
                        await connector.aclose()

                    summary["stores"][store_key] = store_stats

                await _write_log(
                    session,
                    level="INFO",
                    source="scheduler.ingestion",
                    message="Deal ingestion finished",
                    context=summary,
                )
                await session.commit()
            except Exception as exc:  # noqa: BLE001
                await session.rollback()
                logger.exception("ingestion job crashed")
                summary["errors"].append(str(exc))
                async with AsyncSessionLocal() as log_session:
                    await _write_log(
                        log_session,
                        level="ERROR",
                        source="scheduler.ingestion",
                        message="Deal ingestion crashed",
                        context={"error": str(exc)},
                    )
                    await log_session.commit()

    return summary


def should_expire_offer(
    *,
    is_available: bool,
    discount_percent: Decimal,
    min_discount: Decimal = MIN_DISCOUNT_FOR_INGESTION,
) -> bool:
    """Expire when unavailable or discount drops below threshold."""
    if not is_available:
        return True
    return discount_percent < min_discount


async def _refresh_offer_from_source(
    offer: Offer,
    connectors: dict[str, Any],
) -> NormalizedOffer | None:
    store_key = {
        "Amazon": "amazon",
        "Mercado Livre": "mercadolivre",
        "Shopee": "shopee",
    }.get(offer.store_name)
    if not store_key or store_key not in connectors:
        return None
    connector = connectors[store_key]
    query = offer.product.name if offer.product else offer.external_offer_id
    result = await connector.fetch_offers(query or "", limit=20)
    if not result.success:
        return None
    for item in result.offers:
        if item.external_offer_id == offer.external_offer_id:
            return item
    return None


async def run_deal_revalidation_job() -> dict[str, Any]:
    """Re-check published offers and expire/update as needed."""
    summary: dict[str, Any] = {
        "job": "revalidation",
        "checked": 0,
        "updated": 0,
        "expired": 0,
        "errors": [],
    }
    pricing = _pricing()

    async with AsyncSessionLocal() as session:
        async with job_lock(session, LOCK_REVALIDATION) as acquired:
            if not acquired:
                summary["skipped_lock"] = True
                await _write_log(
                    session,
                    level="WARNING",
                    source="scheduler.revalidation",
                    message="Revalidation skipped: lock not acquired",
                )
                await session.commit()
                return summary

            system = await _load_system_settings(session)
            minutes = int(system.get("price_revalidation_minutes") or 0)
            if minutes <= 0:
                hours = system.get("price_revalidation_hours") or 0
                minutes = int(float(hours) * 60) if hours else 30
            if minutes <= 0:
                minutes = 30
            cutoff = utc_now().timestamp() - (minutes * 60)
            connectors = _connector_factory()

            try:
                stmt = (
                    select(Offer)
                    .options(selectinload(Offer.product))
                    .where(
                        Offer.approval_status == "approved",
                        Offer.is_available.is_(True),
                    )
                )
                offers = (await session.execute(stmt)).scalars().all()
                stale_offers = [
                    offer
                    for offer in offers
                    if offer.last_checked_at is None
                    or offer.last_checked_at.timestamp() <= cutoff
                ]

                for offer in stale_offers:
                    summary["checked"] += 1
                    try:
                        fresh = await _refresh_offer_from_source(offer, connectors)
                        now = utc_now()
                        if fresh is None:
                            offer.is_available = False
                            offer.last_checked_at = now
                            summary["expired"] += 1
                            continue

                        price_result = pricing.evaluate(
                            fresh.current_price,
                            fresh.original_price,
                            is_available=fresh.is_available,
                        )
                        if should_expire_offer(
                            is_available=fresh.is_available,
                            discount_percent=price_result.discount_percent,
                        ):
                            offer.is_available = False
                            offer.current_price = price_result.current_price
                            offer.original_price = price_result.original_price
                            offer.discount_percent = price_result.discount_percent
                            offer.last_checked_at = now
                            summary["expired"] += 1
                            continue

                        if offer.current_price != price_result.current_price:
                            session.add(
                                PriceHistory(
                                    offer_id=offer.id,
                                    price=price_result.current_price,
                                    recorded_at=now,
                                )
                            )
                        offer.current_price = price_result.current_price
                        offer.original_price = price_result.original_price
                        offer.discount_percent = price_result.discount_percent
                        offer.is_available = True
                        offer.last_checked_at = now
                        if offer.product:
                            rank = RankingService().calculate(
                                RankingInput(
                                    discount_percent=price_result.discount_percent,
                                    average_rating=fresh.average_rating,
                                    ratings_count=fresh.ratings_count,
                                    sales_count=fresh.sales_count,
                                    reviews_count=fresh.reviews_count,
                                    is_available=True,
                                )
                            )
                            offer.product.ranking_score = rank.total_score
                        summary["updated"] += 1
                    except Exception as exc:  # noqa: BLE001
                        summary["errors"].append(str(exc))
                        logger.exception("revalidation failed offer=%s", offer.id)

                for connector in connectors.values():
                    await connector.aclose()

                await _write_log(
                    session,
                    level="INFO",
                    source="scheduler.revalidation",
                    message="Deal revalidation finished",
                    context=summary,
                )
                await session.commit()
            except Exception as exc:  # noqa: BLE001
                await session.rollback()
                logger.exception("revalidation job crashed")
                summary["errors"].append(str(exc))

    return summary
