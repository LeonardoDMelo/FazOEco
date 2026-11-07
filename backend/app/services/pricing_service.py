"""Pricing engine: Decimal discounts, dynamic bands and publish rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Sequence


TWOPLACES = Decimal("0.01")
HUNDRED = Decimal("100")
ZERO = Decimal("0")


@dataclass(frozen=True, slots=True)
class DiscountBand:
    """Inclusive lower bound, exclusive upper bound (None = +inf)."""

    name: str
    min_percent: Decimal
    max_percent: Decimal | None = None


@dataclass(frozen=True, slots=True)
class PricingConfig:
    """Tunable publication and band thresholds."""

    min_discount_percent: Decimal = Decimal("5.00")
    max_discount_percent: Decimal = Decimal("90.00")
    min_current_price: Decimal = Decimal("0.01")
    require_original_price: bool = True
    bands: Sequence[DiscountBand] = field(
        default_factory=lambda: (
            DiscountBand("none", Decimal("0"), Decimal("5")),
            DiscountBand("low", Decimal("5"), Decimal("15")),
            DiscountBand("medium", Decimal("15"), Decimal("30")),
            DiscountBand("high", Decimal("30"), Decimal("50")),
            DiscountBand("extreme", Decimal("50"), None),
        )
    )


@dataclass(frozen=True, slots=True)
class PricingResult:
    discount_percent: Decimal
    band: str
    is_publishable: bool
    reasons: tuple[str, ...]
    current_price: Decimal
    original_price: Decimal | None


class PricingService:
    """Calculates exact discounts and validates minimum publish criteria."""

    def __init__(self, config: PricingConfig | None = None) -> None:
        self.config = config or PricingConfig()

    @staticmethod
    def _money(value: Decimal | int | float | str) -> Decimal:
        return Decimal(str(value)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)

    def calculate_discount_percent(
        self,
        current_price: Decimal | int | float | str,
        original_price: Decimal | int | float | str | None,
    ) -> Decimal:
        """Return discount % with two decimal places (HALF_UP on the final ratio)."""
        if original_price is None:
            return ZERO

        current = Decimal(str(current_price))
        original = Decimal(str(original_price))
        if original <= ZERO or current < ZERO or current >= original:
            return ZERO

        raw = (original - current) / original * HUNDRED
        return raw.quantize(TWOPLACES, rounding=ROUND_HALF_UP)

    def categorize_band(self, discount_percent: Decimal | int | float | str) -> str:
        """Map a discount percentage into a dynamic band name."""
        discount = self._money(discount_percent)
        for band in self.config.bands:
            upper_ok = band.max_percent is None or discount < band.max_percent
            if discount >= band.min_percent and upper_ok:
                return band.name
        return "none"

    def evaluate(
        self,
        current_price: Decimal | int | float | str,
        original_price: Decimal | int | float | str | None = None,
        *,
        is_available: bool = True,
    ) -> PricingResult:
        """Full pricing pipeline: discount → band → publishability."""
        current = self._money(current_price)
        original = self._money(original_price) if original_price is not None else None
        discount = self.calculate_discount_percent(current, original)
        band = self.categorize_band(discount)
        reasons: list[str] = []

        if not is_available:
            reasons.append("offer_unavailable")
        if current < self.config.min_current_price:
            reasons.append("current_price_below_minimum")
        if self.config.require_original_price and original is None:
            reasons.append("missing_original_price")
        if original is not None and original <= ZERO:
            reasons.append("invalid_original_price")
        if original is not None and current >= original:
            reasons.append("no_actual_discount")
        if discount < self.config.min_discount_percent:
            reasons.append("discount_below_minimum")
        if discount > self.config.max_discount_percent:
            reasons.append("discount_above_maximum")

        return PricingResult(
            discount_percent=discount,
            band=band,
            is_publishable=len(reasons) == 0,
            reasons=tuple(reasons),
            current_price=current,
            original_price=original,
        )
