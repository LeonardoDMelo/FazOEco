"""Offer Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field, field_validator

from app.core.timezone import to_display_tz, to_utc
from app.schemas.common import ORMModel


class OfferBase(ORMModel):
    product_id: UUID
    store_name: str = Field(..., min_length=1, max_length=120)
    affiliate_network: str | None = Field(default=None, max_length=80)
    affiliate_url: str = Field(..., min_length=1, max_length=1000)
    external_offer_id: str = Field(..., min_length=1, max_length=180)
    current_price: Decimal = Field(..., ge=0)
    original_price: Decimal | None = Field(default=None, ge=0)
    currency: str = Field(default="BRL", min_length=3, max_length=3)
    discount_percent: Decimal | None = Field(default=None, ge=0, le=100)
    commission_rate: Decimal | None = Field(default=None, ge=0, le=100)
    is_available: bool = True

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, value: str) -> str:
        return value.upper()


class OfferCreate(OfferBase):
    """Payload for creating an affiliate offer."""


class OfferUpdate(ORMModel):
    store_name: str | None = Field(default=None, min_length=1, max_length=120)
    affiliate_network: str | None = Field(default=None, max_length=80)
    affiliate_url: str | None = Field(default=None, min_length=1, max_length=1000)
    external_offer_id: str | None = Field(default=None, min_length=1, max_length=180)
    current_price: Decimal | None = Field(default=None, ge=0)
    original_price: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    discount_percent: Decimal | None = Field(default=None, ge=0, le=100)
    commission_rate: Decimal | None = Field(default=None, ge=0, le=100)
    is_available: bool | None = None
    last_checked_at: datetime | None = None

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, value: str | None) -> str | None:
        return value.upper() if value else value

    @field_validator("last_checked_at", mode="before")
    @classmethod
    def normalize_last_checked(cls, value: datetime | None) -> datetime | None:
        return to_utc(value) if isinstance(value, datetime) else value


class OfferRead(OfferBase):
    id: UUID
    clicks_count: int
    conversions_count: int
    last_checked_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at", "last_checked_at", mode="after")
    @classmethod
    def as_sao_paulo(cls, value: datetime | None) -> datetime | None:
        return to_display_tz(value) if value else value
