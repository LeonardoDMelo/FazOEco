"""Admin panel schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.core.timezone import to_display_tz
from app.schemas.common import ORMModel


class ConnectorStatus(BaseModel):
    store_key: str
    store_name: str
    has_credentials: bool
    simulation_enabled: bool


class ConnectorRunRequest(BaseModel):
    query: str = Field(default="", max_length=200)
    stores: list[str] | None = Field(
        default=None,
        description="Optional subset: amazon, mercadolivre, shopee",
    )
    limit: int = Field(default=10, ge=1, le=50)


class ConnectorRunResponse(BaseModel):
    results: list[dict[str, Any]]


class RankingWeightsUpdate(BaseModel):
    discount: Decimal = Field(..., ge=0)
    rating: Decimal = Field(..., ge=0)
    sales: Decimal = Field(..., ge=0)
    reviews: Decimal = Field(..., ge=0)
    engagement: Decimal = Field(..., ge=0)


class DiscountBandsUpdate(BaseModel):
    min_discount_percent: Decimal = Field(..., ge=0, le=100)
    max_discount_percent: Decimal = Field(..., ge=0, le=100)
    bands: list[dict[str, Any]] = Field(default_factory=list)


class SystemSettingsUpdate(BaseModel):
    auto_publish_enabled: bool = False
    simulation_mode_preferred: bool = True
    price_revalidation_hours: int = Field(default=6, ge=1, le=168)
    connectors_enabled: dict[str, bool] = Field(
        default_factory=lambda: {
            "amazon": True,
            "mercadolivre": True,
            "shopee": True,
        }
    )


class AdminStats(BaseModel):
    offers_approved: int = 0
    offers_pending: int = 0
    offers_rejected: int = 0
    offers_unavailable: int = 0
    connectors_ready: int = 0
    connectors_total: int = 0
    logs_total: int = 0
    simulation_enabled: bool = True


class LogRead(ORMModel):
    id: UUID
    level: str
    source: str
    message: str
    context: dict[str, Any] | None = None
    user_id: UUID | None = None
    created_at: datetime

    @field_validator("created_at", mode="after")
    @classmethod
    def as_sao_paulo(cls, value: datetime) -> datetime:
        return to_display_tz(value)


class SettingRead(ORMModel):
    id: UUID
    key: str
    value: Any = None
    description: str | None = None
    updated_at: datetime

    @field_validator("updated_at", mode="after")
    @classmethod
    def as_sao_paulo(cls, value: datetime) -> datetime:
        return to_display_tz(value)
