"""Authentication schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.timezone import to_display_tz
from app.schemas.common import ORMModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    exp: datetime | None = None


class UserRead(ORMModel):
    id: UUID
    email: str
    username: str
    full_name: str | None = None
    is_active: bool
    is_superuser: bool
    created_at: datetime

    @field_validator("created_at", mode="after")
    @classmethod
    def as_sao_paulo(cls, value: datetime) -> datetime:
        return to_display_tz(value)


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=80)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=180)
    is_superuser: bool = False
