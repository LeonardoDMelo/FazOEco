"""Unit tests for PricingService."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.services.pricing_service import PricingConfig, PricingService


def test_calculate_discount_exact_decimal(pricing_service: PricingService) -> None:
    discount = pricing_service.calculate_discount_percent("80.00", "100.00")
    assert discount == Decimal("20.00")


def test_calculate_discount_rounds_half_up(pricing_service: PricingService) -> None:
    # (100 - 66.665) / 100 * 100 = 33.335 → 33.34
    discount = pricing_service.calculate_discount_percent("66.665", "100.00")
    assert discount == Decimal("33.34")


def test_calculate_discount_without_original_is_zero(
    pricing_service: PricingService,
) -> None:
    assert pricing_service.calculate_discount_percent("50.00", None) == Decimal("0.00")


def test_calculate_discount_when_current_not_lower(
    pricing_service: PricingService,
) -> None:
    assert pricing_service.calculate_discount_percent("100.00", "100.00") == Decimal("0.00")
    assert pricing_service.calculate_discount_percent("120.00", "100.00") == Decimal("0.00")


@pytest.mark.parametrize(
    ("discount", "expected_band"),
    [
        (Decimal("0"), "none"),
        (Decimal("4.99"), "none"),
        (Decimal("5.00"), "low"),
        (Decimal("14.99"), "low"),
        (Decimal("15.00"), "medium"),
        (Decimal("29.99"), "medium"),
        (Decimal("30.00"), "high"),
        (Decimal("49.99"), "high"),
        (Decimal("50.00"), "extreme"),
        (Decimal("80.00"), "extreme"),
    ],
)
def test_dynamic_discount_bands(
    pricing_service: PricingService,
    discount: Decimal,
    expected_band: str,
) -> None:
    assert pricing_service.categorize_band(discount) == expected_band


def test_evaluate_publishable_offer(pricing_service: PricingService) -> None:
    result = pricing_service.evaluate("70.00", "100.00", is_available=True)
    assert result.is_publishable is True
    assert result.discount_percent == Decimal("30.00")
    assert result.band == "high"
    assert result.reasons == ()


def test_evaluate_rejects_below_minimum_discount(pricing_service: PricingService) -> None:
    result = pricing_service.evaluate("97.00", "100.00")
    assert result.is_publishable is False
    assert "discount_below_minimum" in result.reasons
    assert result.band == "none"


def test_evaluate_rejects_missing_original(pricing_service: PricingService) -> None:
    result = pricing_service.evaluate("50.00", None)
    assert result.is_publishable is False
    assert "missing_original_price" in result.reasons


def test_evaluate_rejects_unavailable(pricing_service: PricingService) -> None:
    result = pricing_service.evaluate("50.00", "100.00", is_available=False)
    assert result.is_publishable is False
    assert "offer_unavailable" in result.reasons


def test_evaluate_rejects_extreme_fake_discount(pricing_service: PricingService) -> None:
    result = pricing_service.evaluate("5.00", "100.00")
    assert result.discount_percent == Decimal("95.00")
    assert result.is_publishable is False
    assert "discount_above_maximum" in result.reasons


def test_custom_min_discount_config() -> None:
    service = PricingService(PricingConfig(min_discount_percent=Decimal("10.00")))
    result = service.evaluate("92.00", "100.00")
    assert result.is_publishable is False
    assert "discount_below_minimum" in result.reasons
