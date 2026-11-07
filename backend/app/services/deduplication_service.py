"""Deduplication by GTIN/EAN and existing marketplace offer keys."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.offer import Offer
from app.models.product import Product


_GTIN_RE = re.compile(r"\D+")


class DedupAction(str, Enum):
    CREATE_PRODUCT = "create_product"
    UPDATE_PRODUCT = "update_product"
    CREATE_OFFER = "create_offer"
    UPDATE_OFFER = "update_offer"


@dataclass(frozen=True, slots=True)
class OfferIdentity:
    """Inbound offer identity used for matching."""

    store_name: str
    external_offer_id: str
    affiliate_url: str
    gtin: str | None = None
    product_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class DedupDecision:
    action: DedupAction
    product_id: UUID | None = None
    offer_id: UUID | None = None
    matched_by: str | None = None
    normalized_gtin: str | None = None
    should_update_existing: bool = False


class DeduplicationService:
    """Finds GTIN/EAN and offer matches to avoid duplicate catalog rows."""

    VALID_GTIN_LENGTHS = frozenset({8, 12, 13, 14})

    @classmethod
    def normalize_gtin(cls, value: str | None) -> str | None:
        """Strip non-digits and validate GTIN/EAN length (8/12/13/14)."""
        if value is None:
            return None
        digits = _GTIN_RE.sub("", value.strip())
        if not digits or len(digits) not in cls.VALID_GTIN_LENGTHS:
            return None
        # Reject all-zeros / trivial codes
        if set(digits) == {"0"}:
            return None
        return digits

    @classmethod
    def gtin_checksum_valid(cls, gtin: str) -> bool:
        """Optional GS1 checksum validation (last digit)."""
        if len(gtin) not in cls.VALID_GTIN_LENGTHS:
            return False
        digits = [int(ch) for ch in gtin]
        check = digits.pop()
        # Right-to-left: odd positions *3, even *1 (GS1)
        total = 0
        for index, digit in enumerate(reversed(digits)):
            total += digit * (3 if index % 2 == 0 else 1)
        calculated = (10 - (total % 10)) % 10
        return calculated == check

    def decide(
        self,
        *,
        identity: OfferIdentity,
        existing_product: Product | None,
        existing_offer: Offer | None,
        normalized_gtin: str | None,
    ) -> DedupDecision:
        """Pure decision matrix used by resolve() and unit tests."""
        if existing_offer is not None:
            return DedupDecision(
                action=DedupAction.UPDATE_OFFER,
                product_id=existing_offer.product_id,
                offer_id=existing_offer.id,
                matched_by="store_external_id_or_url",
                normalized_gtin=normalized_gtin,
                should_update_existing=True,
            )

        if existing_product is not None:
            return DedupDecision(
                action=DedupAction.CREATE_OFFER,
                product_id=existing_product.id,
                offer_id=None,
                matched_by="gtin" if normalized_gtin else "product_id",
                normalized_gtin=normalized_gtin,
                should_update_existing=False,
            )

        if identity.product_id is not None:
            return DedupDecision(
                action=DedupAction.CREATE_OFFER,
                product_id=identity.product_id,
                matched_by="explicit_product_id",
                normalized_gtin=normalized_gtin,
                should_update_existing=False,
            )

        return DedupDecision(
            action=DedupAction.CREATE_PRODUCT,
            product_id=None,
            offer_id=None,
            matched_by=None,
            normalized_gtin=normalized_gtin,
            should_update_existing=False,
        )

    async def find_product_by_gtin(
        self,
        session: AsyncSession,
        gtin: str,
    ) -> Product | None:
        stmt = select(Product).where(Product.external_sku == gtin).limit(1)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_offer(
        self,
        session: AsyncSession,
        identity: OfferIdentity,
    ) -> Offer | None:
        stmt = (
            select(Offer)
            .where(
                (
                    (Offer.store_name == identity.store_name)
                    & (Offer.external_offer_id == identity.external_offer_id)
                )
                | (Offer.affiliate_url == identity.affiliate_url)
            )
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def resolve(
        self,
        session: AsyncSession,
        identity: OfferIdentity,
    ) -> DedupDecision:
        """Look up DB matches and return the action to take."""
        normalized = self.normalize_gtin(identity.gtin)
        existing_offer = await self.find_offer(session, identity)

        existing_product: Product | None = None
        if identity.product_id is not None:
            existing_product = await session.get(Product, identity.product_id)
        elif normalized is not None:
            existing_product = await self.find_product_by_gtin(session, normalized)

        # If offer exists, product is already known via FK
        return self.decide(
            identity=identity,
            existing_product=existing_product,
            existing_offer=existing_offer,
            normalized_gtin=normalized,
        )

    def merge_offer_fields(
        self,
        offer: Offer,
        updates: dict[str, Any],
        *,
        allowed: frozenset[str] | None = None,
    ) -> Offer:
        """Apply inbound updates onto an existing Offer (in-memory)."""
        permitted = allowed or frozenset(
            {
                "current_price",
                "original_price",
                "discount_percent",
                "commission_rate",
                "currency",
                "is_available",
                "affiliate_url",
                "affiliate_network",
                "last_checked_at",
            }
        )
        for key, value in updates.items():
            if key in permitted:
                setattr(offer, key, value)
        return offer
