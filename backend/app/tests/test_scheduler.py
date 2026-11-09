"""Unit tests for scheduler job helpers and evaluation rules."""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.connectors.base import NormalizedOffer
from app.scheduler.jobs import (
    MIN_DISCOUNT_FOR_INGESTION,
    evaluate_offer_for_ingestion,
    should_expire_offer,
)
from app.scheduler.manager import SchedulerManager


def _offer(**overrides) -> NormalizedOffer:
    base = dict(
        store_name="Amazon",
        affiliate_network="amazon_associates",
        external_offer_id="B0TEST",
        title="Fone Bluetooth",
        affiliate_url="https://amazon.example/x",
        current_price=Decimal("80.00"),
        original_price=Decimal("100.00"),
        currency="BRL",
        gtin="7891234567895",
        brand="SoundMax",
        image_url=None,
        average_rating=Decimal("4.5"),
        ratings_count=10,
        reviews_count=4,
        sales_count=100,
        is_available=True,
    )
    base.update(overrides)
    return NormalizedOffer(**base)


def test_evaluate_offer_requires_minimum_20_percent_discount() -> None:
    weak = evaluate_offer_for_ingestion(
        _offer(current_price=Decimal("90.00"), original_price=Decimal("100.00"))
    )
    assert weak["eligible"] is False
    assert weak["pricing"].discount_percent == Decimal("10.00")

    strong = evaluate_offer_for_ingestion(
        _offer(current_price=Decimal("70.00"), original_price=Decimal("100.00"))
    )
    assert strong["eligible"] is True
    assert strong["pricing"].discount_percent == Decimal("30.00")
    assert Decimal("0") <= strong["ranking_score"] <= Decimal("100")


def test_should_expire_when_unavailable_or_discount_drops() -> None:
    assert should_expire_offer(is_available=False, discount_percent=Decimal("40")) is True
    assert (
        should_expire_offer(
            is_available=True,
            discount_percent=Decimal("19.99"),
            min_discount=MIN_DISCOUNT_FOR_INGESTION,
        )
        is True
    )
    assert (
        should_expire_offer(
            is_available=True,
            discount_percent=Decimal("20.00"),
            min_discount=MIN_DISCOUNT_FOR_INGESTION,
        )
        is False
    )


def test_scheduler_manager_status_before_start() -> None:
    manager = SchedulerManager()
    status = manager.status()
    assert status["running"] is False
    assert status["jobs"] == []


@pytest.mark.asyncio
async def test_ingestion_job_respects_advisory_lock(monkeypatch: pytest.MonkeyPatch) -> None:
    """If lock is not acquired, job returns skipped_lock without processing."""
    from app.scheduler import jobs as jobs_module

    class FakeResult:
        def scalar(self):
            return False

    class FakeSession:
        async def execute(self, *_args, **_kwargs):
            return FakeResult()

        async def commit(self):
            return None

        def add(self, _obj):
            return None

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_exc):
            return False

    class FakeSessionMaker:
        def __call__(self):
            return FakeSession()

    monkeypatch.setattr(jobs_module, "AsyncSessionLocal", FakeSessionMaker())
    result = await jobs_module.run_deal_ingestion_job()
    assert result["skipped_lock"] is True


def test_trigger_endpoints_registered() -> None:
    from app.main import create_app

    app = create_app()
    paths = set(app.openapi()["paths"].keys())
    assert "/api/v1/admin/jobs/trigger-ingestion" in paths
    assert "/api/v1/admin/jobs/trigger-revalidation" in paths
    assert "/api/v1/admin/jobs/status" in paths
