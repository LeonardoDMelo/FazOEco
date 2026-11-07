"""Product ORM model with popularity / ranking metrics."""

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
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.offer import Offer


class Product(Base):
    """Catalog product with reputation and ranking score (0–100)."""

    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_products_slug"),
        UniqueConstraint("external_sku", name="uq_products_external_sku"),
        CheckConstraint(
            "average_rating >= 0 AND average_rating <= 5",
            name="ck_products_average_rating_range",
        ),
        CheckConstraint(
            "ranking_score >= 0 AND ranking_score <= 100",
            name="ck_products_ranking_score_range",
        ),
        CheckConstraint("ratings_count >= 0", name="ck_products_ratings_count_nonneg"),
        CheckConstraint("reviews_count >= 0", name="ck_products_reviews_count_nonneg"),
        CheckConstraint("sales_count >= 0", name="ck_products_sales_count_nonneg"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(280), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    brand: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    external_sku: Mapped[str | None] = mapped_column(String(120), nullable=True)

    # Popularidade / reputação
    average_rating: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        default=Decimal("0.00"),
        server_default="0.00",
        nullable=False,
    )
    ratings_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    reviews_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    sales_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    # Ranking composto 0–100 pts
    ranking_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        server_default="0.00",
        nullable=False,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
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

    category: Mapped[Category] = relationship(back_populates="products")
    offers: Mapped[list[Offer]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )
