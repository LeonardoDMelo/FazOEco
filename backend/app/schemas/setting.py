"""Setting Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from app.core.timezone import to_display_tz
from app.schemas.common import ORMModel


class SettingBase(ORMModel):
    key: str = Field(..., min_length=1, max_length=120)
    value: Any = None
    description: str | None = None


class SettingCreate(SettingBase):
    """Payload for creating a setting."""


class SettingUpdate(ORMModel):
    value: Any = None
    description: str | None = None


class SettingRead(SettingBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at", mode="after")
    @classmethod
    def as_sao_paulo(cls, value: datetime) -> datetime:
        return to_display_tz(value)
