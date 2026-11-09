"""Public offer and product endpoints."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.api.deps import DbSession
from app.api.v1.helpers import (
    apply_offer_filters,
    apply_sort,
    base_offer_query,
    offer_to_list_item,
    paginate_offers,
)
from app.models.offer import Offer
from app.models.product import Product
from app.schemas.offer_public import HomeShowcase, OfferDetail, OfferListItem, ProductDetail
from app.schemas.pagination import Page

router = APIRouter(tags=["offers"])


@router.get("/offers", response_model=Page[OfferListItem])
async def list_offers(
    db: DbSession,
    q: str | None = Query(default=None, max_length=120, description="Busca por nome ou loja"),
    store: str | None = Query(default=None, max_length=80),
    category_id: UUID | None = None,
    band: str | None = Query(
        default=None,
        description="Faixa: none|low|medium|high|extreme",
    ),
    min_discount: Decimal | None = Query(default=None, ge=0, le=100),
    max_price: Decimal | None = Query(default=None, ge=0),
    sort: str = Query(
        default="newest",
        description="discount_desc|ranking_desc|price_asc|newest",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> Page[OfferListItem]:
    """Listagem pública paginada de ofertas aprovadas."""
    stmt = base_offer_query(public_only=True)
    stmt = apply_offer_filters(
        stmt,
        q=q,
        store=store,
        category_id=str(category_id) if category_id else None,
        band=band,
        min_discount=min_discount,
        max_price=max_price,
    )
    stmt = apply_sort(stmt, sort)
    return await paginate_offers(db, stmt, page=page, page_size=page_size)


@router.get("/offers/home", response_model=HomeShowcase)
async def home_showcase(
    db: DbSession,
    ranking_size: int = Query(default=8, ge=1, le=24),
    tier_size: int = Query(default=4, ge=1, le=12),
) -> HomeShowcase:
    """Ranking and discount bands in one round-trip for the public home."""

    async def _slice(sort: str, *, band: str | None, size: int) -> list[OfferListItem]:
        stmt = base_offer_query(public_only=True)
        stmt = apply_offer_filters(stmt, band=band)
        stmt = apply_sort(stmt, sort)
        page = await paginate_offers(db, stmt, page=1, page_size=size)
        return page.items

    ranking = await _slice("ranking_desc", band=None, size=ranking_size)
    tiers = {
        band: await _slice("discount_desc", band=band, size=tier_size)
        for band in ("extreme", "high", "medium")
    }
    return HomeShowcase(ranking=ranking, tiers=tiers)


@router.get("/offers/featured", response_model=Page[OfferListItem])
async def featured_offers(
    db: DbSession,
    band: str = Query(default="high", description="Faixa de destaque"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
) -> Page[OfferListItem]:
    """Destaques filtrados por faixa dinâmica de desconto."""
    stmt = base_offer_query(public_only=True)
    stmt = apply_offer_filters(stmt, band=band)
    stmt = apply_sort(stmt, "discount_desc")
    return await paginate_offers(db, stmt, page=page, page_size=page_size)


@router.get("/offers/{offer_id}", response_model=OfferDetail)
async def get_offer(offer_id: UUID, db: DbSession) -> OfferDetail:
    """
    Detalhe público de oferta aprovada.

    Ofertas expiradas/indisponíveis continuam acessíveis (SEO orgânico),
    desde que tenham sido aprovadas anteriormente.
    """
    stmt = (
        base_offer_query(public_only=False)
        .where(
            Offer.id == offer_id,
            Offer.approval_status == "approved",
            Product.is_active.is_(True),
        )
    )
    offer = (await db.execute(stmt)).scalars().unique().first()
    if offer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")

    item = offer_to_list_item(offer)
    product = offer.product
    return OfferDetail(
        **item.model_dump(),
        clicks_count=offer.clicks_count,
        conversions_count=offer.conversions_count,
        commission_rate=offer.commission_rate,
        last_checked_at=offer.last_checked_at,
        updated_at=offer.updated_at,
        brand=product.brand,
        average_rating=product.average_rating,
        ratings_count=product.ratings_count,
        reviews_count=product.reviews_count,
        sales_count=product.sales_count,
    )


@router.get("/offers/{offer_id}/alternatives", response_model=Page[OfferListItem])
async def offer_alternatives(
    offer_id: UUID,
    db: DbSession,
    page_size: int = Query(default=8, ge=1, le=24),
) -> Page[OfferListItem]:
    """Sugestões ativas da mesma categoria (para páginas de oferta expirada)."""
    stmt = (
        base_offer_query(public_only=False)
        .where(Offer.id == offer_id, Offer.approval_status == "approved")
    )
    offer = (await db.execute(stmt)).scalars().unique().first()
    if offer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")

    related = base_offer_query(public_only=True).where(
        Product.category_id == offer.product.category_id,
        Offer.id != offer_id,
    )
    related = apply_sort(related, "ranking_desc")
    return await paginate_offers(db, related, page=1, page_size=page_size)


@router.get("/products/{product_id}", response_model=ProductDetail)
async def get_product(product_id: UUID, db: DbSession) -> ProductDetail:
    """Detalhe do produto com ofertas públicas aprovadas."""
    result = await db.execute(
        select(Product)
        .options(joinedload(Product.offers).joinedload(Offer.product))
        .where(Product.id == product_id, Product.is_active.is_(True))
    )
    product = result.scalars().unique().first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    public_offers = [
        offer_to_list_item(o)
        for o in product.offers
        if o.is_available and o.approval_status == "approved"
    ]
    return ProductDetail(
        id=product.id,
        name=product.name,
        slug=product.slug,
        description=product.description,
        brand=product.brand,
        image_url=product.image_url,
        external_sku=product.external_sku,
        category_id=product.category_id,
        average_rating=product.average_rating,
        ratings_count=product.ratings_count,
        reviews_count=product.reviews_count,
        sales_count=product.sales_count,
        ranking_score=product.ranking_score,
        offers=public_offers,
    )
