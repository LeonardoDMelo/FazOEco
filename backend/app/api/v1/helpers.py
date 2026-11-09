"""Shared query/response helpers for v1 routes."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Select, asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.offer import Offer
from app.models.product import Product
from app.schemas.offer_public import OfferListItem
from app.schemas.pagination import Page, PageMeta
from app.services.pricing_service import PricingService

SORT_MAP = {
    "discount_desc": desc(Offer.discount_percent),
    "ranking_desc": desc(Product.ranking_score),
    "price_asc": asc(Offer.current_price),
    "newest": desc(Offer.created_at),
}

pricing = PricingService()


def offer_to_list_item(offer: Offer) -> OfferListItem:
    product = offer.product
    discount = offer.discount_percent
    band = pricing.categorize_band(discount or Decimal("0"))
    return OfferListItem(
        id=offer.id,
        product_id=offer.product_id,
        product_name=product.name,
        product_slug=product.slug,
        product_image_url=product.image_url or offer.product.image_url,
        ranking_score=product.ranking_score,
        store_name=offer.store_name,
        affiliate_network=offer.affiliate_network,
        affiliate_url=offer.affiliate_url,
        external_offer_id=offer.external_offer_id,
        current_price=offer.current_price,
        original_price=offer.original_price,
        currency=offer.currency,
        discount_percent=discount,
        discount_band=band,
        is_available=offer.is_available,
        approval_status=offer.approval_status,
        created_at=offer.created_at,
    )


def base_offer_query(*, public_only: bool = True) -> Select[tuple[Offer]]:
    stmt = (
        select(Offer)
        .join(Product, Product.id == Offer.product_id)
        .options(joinedload(Offer.product))
    )
    if public_only:
        stmt = stmt.where(
            Offer.is_available.is_(True),
            Offer.approval_status == "approved",
            Product.is_active.is_(True),
        )
    return stmt


def apply_offer_filters(
    stmt: Select[tuple[Offer]],
    *,
    q: str | None = None,
    store: str | None = None,
    category_id: str | None = None,
    band: str | None = None,
    min_discount: Decimal | None = None,
    max_price: Decimal | None = None,
    approval_status: str | None = None,
) -> Select[tuple[Offer]]:
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Product.name.ilike(like), Offer.store_name.ilike(like)))
    if store:
        stmt = stmt.where(Offer.store_name.ilike(store.strip()))
    if category_id:
        stmt = stmt.where(Product.category_id == category_id)
    if approval_status:
        stmt = stmt.where(Offer.approval_status == approval_status)
    if min_discount is not None:
        stmt = stmt.where(Offer.discount_percent >= min_discount)
    if max_price is not None:
        stmt = stmt.where(Offer.current_price <= max_price)
    if band:
        # Filter in SQL by approximate band ranges matching PricingConfig defaults
        ranges = {
            "none": (Decimal("0"), Decimal("5")),
            "low": (Decimal("5"), Decimal("15")),
            "medium": (Decimal("15"), Decimal("30")),
            "high": (Decimal("30"), Decimal("50")),
            "extreme": (Decimal("50"), Decimal("100.01")),
        }
        bounds = ranges.get(band.lower())
        if bounds:
            low, high = bounds
            stmt = stmt.where(
                Offer.discount_percent >= low,
                Offer.discount_percent < high,
            )
    return stmt


def apply_sort(stmt: Select[tuple[Offer]], sort: str) -> Select[tuple[Offer]]:
    order_by = SORT_MAP.get(sort, SORT_MAP["newest"])
    return stmt.order_by(order_by, desc(Offer.id))


async def paginate_offers(
    db: AsyncSession,
    stmt: Select[tuple[Offer]],
    *,
    page: int,
    page_size: int,
) -> Page[OfferListItem]:
    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = int((await db.execute(count_stmt)).scalar_one())
    pages = (total + page_size - 1) // page_size if total else 0
    offset = (page - 1) * page_size
    rows = (
        await db.execute(stmt.offset(offset).limit(page_size))
    ).scalars().unique().all()
    return Page(
        items=[offer_to_list_item(row) for row in rows],
        meta=PageMeta(page=page, page_size=page_size, total=total, pages=pages),
    )
