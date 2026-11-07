"""Price history Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field, field_validator

from app.core.timezone import to_display_tz, to_utc
from app.schemas.common import ORMModel


class PriceHistoryCreate(ORMModel):
    offer_id: UUID
    price: Decimal = Field(..., ge=0)
    recorded_at: datetime | None = None

    @field_validator("recorded_at", mode="before")
    @classmethod
    def normalize_recorded_at(cls, value: datetime | None) -> datetime | None:
        return to_utc(value) if isinstance(value, datetime) else value


class PriceHistoryRead(ORMModel):
    id: UUID
    offer_id: UUID
    price: Decimal
    recorded_at: datetime

    @field_validator("recorded_at", mode="after")
    @classmethod
    def as_sao_paulo(cls, value: datetime) -> datetime:
        return to_display_tz(value)
