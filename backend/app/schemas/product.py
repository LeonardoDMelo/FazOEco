"""Product Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field, field_validator

from app.core.timezone import to_display_tz
from app.schemas.common import ORMModel


class ProductBase(ORMModel):
    category_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=280)
    description: str | None = None
    brand: str | None = Field(default=None, max_length=120)
    image_url: str | None = Field(default=None, max_length=500)
    external_sku: str | None = Field(default=None, max_length=120)
    is_active: bool = True

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, value: str) -> str:
        return value.strip().lower()


class ProductCreate(ProductBase):
    """Payload for creating a product."""

    average_rating: Decimal = Field(default=Decimal("0.00"), ge=0, le=5)
    ratings_count: int = Field(default=0, ge=0)
    reviews_count: int = Field(default=0, ge=0)
    sales_count: int = Field(default=0, ge=0)
    ranking_score: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)


class ProductUpdate(ORMModel):
    category_id: UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=280)
    description: str | None = None
    brand: str | None = Field(default=None, max_length=120)
    image_url: str | None = Field(default=None, max_length=500)
    external_sku: str | None = Field(default=None, max_length=120)
    average_rating: Decimal | None = Field(default=None, ge=0, le=5)
    ratings_count: int | None = Field(default=None, ge=0)
    reviews_count: int | None = Field(default=None, ge=0)
    sales_count: int | None = Field(default=None, ge=0)
    ranking_score: Decimal | None = Field(default=None, ge=0, le=100)
    is_active: bool | None = None

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, value: str | None) -> str | None:
        return value.strip().lower() if value else value


class ProductRead(ProductBase):
    id: UUID
    average_rating: Decimal
    ratings_count: int
    reviews_count: int
    sales_count: int
    ranking_score: Decimal
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at", mode="after")
    @classmethod
    def as_sao_paulo(cls, value: datetime) -> datetime:
        return to_display_tz(value)
