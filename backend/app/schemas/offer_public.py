"""Public/admin offer response schemas enriched with product context."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field, field_validator

from app.core.timezone import to_display_tz
from app.schemas.common import ORMModel
from app.schemas.offer import OfferUpdate


class OfferListItem(ORMModel):
    id: UUID
    product_id: UUID
    product_name: str
    product_slug: str
    product_image_url: str | None = None
    ranking_score: Decimal
    store_name: str
    affiliate_network: str | None = None
    affiliate_url: str
    external_offer_id: str
    current_price: Decimal
    original_price: Decimal | None = None
    currency: str
    discount_percent: Decimal | None = None
    discount_band: str | None = None
    is_available: bool
    approval_status: str
    created_at: datetime

    @field_validator("created_at", mode="after")
    @classmethod
    def as_sao_paulo(cls, value: datetime) -> datetime:
        return to_display_tz(value)


class OfferDetail(OfferListItem):
    clicks_count: int = 0
    conversions_count: int = 0
    commission_rate: Decimal | None = None
    last_checked_at: datetime | None = None
    updated_at: datetime | None = None
    brand: str | None = None
    average_rating: Decimal | None = None
    ratings_count: int = 0
    reviews_count: int = 0
    sales_count: int = 0

    @field_validator("last_checked_at", "updated_at", mode="after")
    @classmethod
    def as_sao_paulo_optional(cls, value: datetime | None) -> datetime | None:
        return to_display_tz(value) if value else value


class OfferModerationUpdate(ORMModel):
    approval_status: str = Field(..., pattern="^(pending|approved|rejected)$")


class OfferAdminUpdate(OfferUpdate):
    approval_status: str | None = Field(
        default=None, pattern="^(pending|approved|rejected)$"
    )


class HomeShowcase(ORMModel):
    """Single payload for the public home: ranking plus discount tiers."""

    ranking: list[OfferListItem]
    tiers: dict[str, list[OfferListItem]]


class ProductDetail(ORMModel):
    id: UUID
    name: str
    slug: str
    description: str | None = None
    brand: str | None = None
    image_url: str | None = None
    external_sku: str | None = None
    category_id: UUID
    average_rating: Decimal
    ratings_count: int
    reviews_count: int
    sales_count: int
    ranking_score: Decimal
    offers: list[OfferListItem] = Field(default_factory=list)
