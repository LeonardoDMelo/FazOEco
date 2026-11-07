"""Unit tests for DeduplicationService."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.deduplication_service import (
    DedupAction,
    DeduplicationService,
    OfferIdentity,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("789.1234.567895", "7891234567895"),
        (" 7891234567895 ", "7891234567895"),
        ("12345670", "12345670"),  # EAN-8
        ("123", None),
        ("0000000000000", None),
        (None, None),
        ("ABC", None),
    ],
)
def test_normalize_gtin(
    dedup_service: DeduplicationService,
    raw: str | None,
    expected: str | None,
) -> None:
    assert dedup_service.normalize_gtin(raw) == expected


def test_gtin_checksum_valid_example(dedup_service: DeduplicationService) -> None:
    # Well-known valid EAN-13 pattern check using computed code
    # 4006381333931 is a commonly cited valid GTIN-13
    assert dedup_service.gtin_checksum_valid("4006381333931") is True
    assert dedup_service.gtin_checksum_valid("4006381333932") is False


def test_decide_update_existing_offer(
    dedup_service: DeduplicationService,
    sample_offer_identity: OfferIdentity,
) -> None:
    product_id = uuid4()
    offer_id = uuid4()
    existing_offer = SimpleNamespace(id=offer_id, product_id=product_id)

    decision = dedup_service.decide(
        identity=sample_offer_identity,
        existing_product=None,
        existing_offer=existing_offer,  # type: ignore[arg-type]
        normalized_gtin="7891234567895",
    )

    assert decision.action == DedupAction.UPDATE_OFFER
    assert decision.should_update_existing is True
    assert decision.offer_id == offer_id
    assert decision.product_id == product_id
    assert decision.matched_by == "store_external_id_or_url"


def test_decide_create_offer_when_product_matched_by_gtin(
    dedup_service: DeduplicationService,
    sample_offer_identity: OfferIdentity,
) -> None:
    product_id = uuid4()
    existing_product = SimpleNamespace(id=product_id)

    decision = dedup_service.decide(
        identity=sample_offer_identity,
        existing_product=existing_product,  # type: ignore[arg-type]
        existing_offer=None,
        normalized_gtin="7891234567895",
    )

    assert decision.action == DedupAction.CREATE_OFFER
    assert decision.product_id == product_id
    assert decision.matched_by == "gtin"
    assert decision.should_update_existing is False


def test_decide_create_product_when_no_match(dedup_service: DeduplicationService) -> None:
    identity = OfferIdentity(
        store_name="Amazon",
        external_offer_id="ASIN-1",
        affiliate_url="https://amazon.example/1",
        gtin=None,
    )
    decision = dedup_service.decide(
        identity=identity,
        existing_product=None,
        existing_offer=None,
        normalized_gtin=None,
    )
    assert decision.action == DedupAction.CREATE_PRODUCT
    assert decision.should_update_existing is False


def test_decide_explicit_product_id(dedup_service: DeduplicationService) -> None:
    product_id = uuid4()
    identity = OfferIdentity(
        store_name="Amazon",
        external_offer_id="ASIN-2",
        affiliate_url="https://amazon.example/2",
        product_id=product_id,
    )
    decision = dedup_service.decide(
        identity=identity,
        existing_product=None,
        existing_offer=None,
        normalized_gtin=None,
    )
    assert decision.action == DedupAction.CREATE_OFFER
    assert decision.product_id == product_id
    assert decision.matched_by == "explicit_product_id"


def test_merge_offer_fields_only_allowed(dedup_service: DeduplicationService) -> None:
    offer = SimpleNamespace(
        current_price=100,
        original_price=120,
        store_name="Old Store",
        discount_percent=None,
    )
    dedup_service.merge_offer_fields(
        offer,  # type: ignore[arg-type]
        {
            "current_price": 80,
            "discount_percent": 33.33,
            "store_name": "Hacked",
        },
    )
    assert offer.current_price == 80
    assert offer.discount_percent == 33.33
    assert offer.store_name == "Old Store"
