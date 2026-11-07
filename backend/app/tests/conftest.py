"""Shared pytest fixtures for service unit tests."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from app.services.deduplication_service import DeduplicationService, OfferIdentity
from app.services.pricing_service import PricingConfig, PricingService
from app.services.ranking_service import RankingConfig, RankingService


@pytest.fixture
def pricing_service() -> PricingService:
    return PricingService(PricingConfig())


@pytest.fixture
def ranking_service() -> RankingService:
    return RankingService(RankingConfig())


@pytest.fixture
def dedup_service() -> DeduplicationService:
    return DeduplicationService()


@pytest.fixture
def sample_offer_identity() -> OfferIdentity:
    return OfferIdentity(
        store_name="Magazine Luiza",
        external_offer_id="MLZ-123",
        affiliate_url="https://affiliate.example/offer/123",
        gtin="7891234567895",
        product_id=None,
    )


@pytest.fixture
def money() -> type[Decimal]:
    return Decimal
