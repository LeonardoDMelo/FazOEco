"""Quality ranking engine (0–100 pts) with 5 configurable pillars."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from math import log10
from typing import Mapping


TWOPLACES = Decimal("0.01")
HUNDRED = Decimal("100")
ZERO = Decimal("0")


@dataclass(frozen=True, slots=True)
class RankingWeights:
    """Five pillars; weights should sum to 100 (normalized if they don't)."""

    discount: Decimal = Decimal("30")
    rating: Decimal = Decimal("25")
    sales: Decimal = Decimal("20")
    reviews: Decimal = Decimal("15")
    engagement: Decimal = Decimal("10")

    def as_mapping(self) -> dict[str, Decimal]:
        return {
            "discount": self.discount,
            "rating": self.rating,
            "sales": self.sales,
            "reviews": self.reviews,
            "engagement": self.engagement,
        }


@dataclass(frozen=True, slots=True)
class RankingInput:
    """Signals used to score an offer/product pair."""

    discount_percent: Decimal = ZERO
    average_rating: Decimal | None = None  # 0–5; None/0 with no ratings = missing
    ratings_count: int = 0
    sales_count: int | None = None  # None or 0 with unknown = missing when None
    reviews_count: int | None = None
    clicks_count: int = 0
    conversions_count: int = 0
    is_available: bool = True
    # When True, treat zero sales/reviews as "no data" instead of zero score
    treat_zero_popularity_as_missing: bool = True


@dataclass(frozen=True, slots=True)
class PillarScore:
    key: str
    raw_score: Decimal
    configured_weight: Decimal
    applied_weight: Decimal
    contribution: Decimal
    data_available: bool


@dataclass(frozen=True, slots=True)
class RankingResult:
    total_score: Decimal
    pillars: tuple[PillarScore, ...]
    missing_pillars: tuple[str, ...]
    redistributed: bool


@dataclass(frozen=True, slots=True)
class RankingConfig:
    weights: RankingWeights = field(default_factory=RankingWeights)
    # Caps used to normalize log-scaled popularity into 0–100
    sales_cap: int = 10_000
    reviews_cap: int = 5_000
    clicks_cap: int = 50_000
    ideal_discount_percent: Decimal = Decimal("40.00")


class RankingService:
    """Computes a transparent 0–100 quality score across five pillars."""

    def __init__(self, config: RankingConfig | None = None) -> None:
        self.config = config or RankingConfig()

    @staticmethod
    def _q(value: Decimal) -> Decimal:
        return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)

    def _log_scale(self, value: int, cap: int) -> Decimal:
        if value <= 0 or cap <= 0:
            return ZERO
        capped = min(value, cap)
        # log10(1+x) / log10(1+cap) → 0..1 then *100
        ratio = Decimal(str(log10(1 + capped) / log10(1 + cap)))
        return self._q(ratio * HUNDRED)

    def score_discount(self, discount_percent: Decimal) -> Decimal:
        ideal = self.config.ideal_discount_percent
        if discount_percent <= ZERO:
            return ZERO
        if discount_percent >= ideal:
            # Soft penalty above ideal (fake/extreme discounts)
            over = discount_percent - ideal
            penalty = min(over / ideal * Decimal("25"), Decimal("25"))
            return self._q(max(HUNDRED - penalty, Decimal("60")))
        return self._q(discount_percent / ideal * HUNDRED)

    def score_rating(self, average_rating: Decimal | None, ratings_count: int) -> tuple[Decimal, bool]:
        if average_rating is None or ratings_count <= 0:
            return ZERO, False
        raw = average_rating / Decimal("5") * HUNDRED
        return self._q(raw), True

    def score_sales(self, sales_count: int | None, *, missing_zeros: bool) -> tuple[Decimal, bool]:
        if sales_count is None or (missing_zeros and sales_count == 0):
            return ZERO, False
        return self._log_scale(sales_count, self.config.sales_cap), True

    def score_reviews(self, reviews_count: int | None, *, missing_zeros: bool) -> tuple[Decimal, bool]:
        if reviews_count is None or (missing_zeros and reviews_count == 0):
            return ZERO, False
        return self._log_scale(reviews_count, self.config.reviews_cap), True

    def score_engagement(
        self,
        clicks_count: int,
        conversions_count: int,
        *,
        is_available: bool,
    ) -> tuple[Decimal, bool]:
        if clicks_count <= 0 and conversions_count <= 0:
            # Availability alone is a weak signal — still counts as available data
            base = Decimal("50.00") if is_available else Decimal("10.00")
            return base, True

        click_score = self._log_scale(clicks_count, self.config.clicks_cap)
        conversion_rate = ZERO
        if clicks_count > 0:
            conversion_rate = min(
                Decimal(conversions_count) / Decimal(clicks_count) * HUNDRED,
                HUNDRED,
            )
        blended = click_score * Decimal("0.6") + conversion_rate * Decimal("0.4")
        if not is_available:
            blended *= Decimal("0.5")
        return self._q(blended), True

    def _raw_pillars(self, data: RankingInput) -> dict[str, tuple[Decimal, bool]]:
        missing_zeros = data.treat_zero_popularity_as_missing
        rating_score, rating_ok = self.score_rating(data.average_rating, data.ratings_count)
        sales_score, sales_ok = self.score_sales(data.sales_count, missing_zeros=missing_zeros)
        reviews_score, reviews_ok = self.score_reviews(
            data.reviews_count, missing_zeros=missing_zeros
        )
        engagement_score, engagement_ok = self.score_engagement(
            data.clicks_count,
            data.conversions_count,
            is_available=data.is_available,
        )
        return {
            "discount": (self.score_discount(Decimal(str(data.discount_percent))), True),
            "rating": (rating_score, rating_ok),
            "sales": (sales_score, sales_ok),
            "reviews": (reviews_score, reviews_ok),
            "engagement": (engagement_score, engagement_ok),
        }

    def _normalize_weights(self, weights: Mapping[str, Decimal]) -> dict[str, Decimal]:
        total = sum(weights.values(), ZERO)
        if total <= ZERO:
            equal = self._q(HUNDRED / Decimal(len(weights)))
            return {key: equal for key in weights}
        return {key: self._q(value / total * HUNDRED) for key, value in weights.items()}

    def calculate(self, data: RankingInput) -> RankingResult:
        """Score all pillars, redistribute weights when popularity data is missing."""
        configured = self._normalize_weights(self.config.weights.as_mapping())
        raw = self._raw_pillars(data)

        available = {key: weight for key, weight in configured.items() if raw[key][1]}
        missing = tuple(key for key, (_, ok) in raw.items() if not ok)
        redistributed = len(missing) > 0

        if not available:
            # Degenerate case: nothing usable → zero score, keep configured weights
            pillars = tuple(
                PillarScore(
                    key=key,
                    raw_score=raw[key][0],
                    configured_weight=configured[key],
                    applied_weight=configured[key],
                    contribution=ZERO,
                    data_available=False,
                )
                for key in configured
            )
            return RankingResult(
                total_score=ZERO,
                pillars=pillars,
                missing_pillars=missing,
                redistributed=True,
            )

        applied = self._normalize_weights(available)
        pillars_list: list[PillarScore] = []
        total = ZERO

        for key, conf_weight in configured.items():
            score, ok = raw[key]
            weight = applied.get(key, ZERO) if ok else ZERO
            contribution = self._q(score * weight / HUNDRED) if ok else ZERO
            total += contribution
            pillars_list.append(
                PillarScore(
                    key=key,
                    raw_score=score,
                    configured_weight=conf_weight,
                    applied_weight=weight,
                    contribution=contribution,
                    data_available=ok,
                )
            )

        return RankingResult(
            total_score=self._q(min(total, HUNDRED)),
            pillars=tuple(pillars_list),
            missing_pillars=missing,
            redistributed=redistributed,
        )
