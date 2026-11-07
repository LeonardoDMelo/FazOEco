"""Affiliate offer ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.price_history import PriceHistory
    from app.models.product import Product


class Offer(Base):
    """Affiliate offer linked to a product on an external marketplace."""

    __tablename__ = "offers"
    __table_args__ = (
        UniqueConstraint(
            "store_name",
            "external_offer_id",
            name="uq_offers_store_external_id",
        ),
        UniqueConstraint("affiliate_url", name="uq_offers_affiliate_url"),
        CheckConstraint("current_price >= 0", name="ck_offers_current_price_nonneg"),
        CheckConstraint(
            "original_price IS NULL OR original_price >= 0",
            name="ck_offers_original_price_nonneg",
        ),
        CheckConstraint(
            "commission_rate IS NULL OR (commission_rate >= 0 AND commission_rate <= 100)",
            name="ck_offers_commission_rate_range",
        ),
        CheckConstraint("clicks_count >= 0", name="ck_offers_clicks_nonneg"),
        CheckConstraint("conversions_count >= 0", name="ck_offers_conversions_nonneg"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    store_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    affiliate_network: Mapped[str | None] = mapped_column(String(80), nullable=True)
    affiliate_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    external_offer_id: Mapped[str] = mapped_column(String(180), nullable=False)

    current_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    original_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="BRL", server_default="BRL")
    discount_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    commission_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)

    is_available: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    clicks_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    conversions_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    product: Mapped[Product] = relationship(back_populates="offers")
    price_history: Mapped[list[PriceHistory]] = relationship(
        back_populates="offer",
        cascade="all, delete-orphan",
        order_by="PriceHistory.recorded_at.desc()",
    )
