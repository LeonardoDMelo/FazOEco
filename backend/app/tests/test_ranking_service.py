"""Unit tests for RankingService."""

from __future__ import annotations

from decimal import Decimal

from app.services.ranking_service import RankingInput, RankingService, RankingWeights


def test_full_data_score_within_bounds(ranking_service: RankingService) -> None:
    result = ranking_service.calculate(
        RankingInput(
            discount_percent=Decimal("30"),
            average_rating=Decimal("4.5"),
            ratings_count=200,
            sales_count=1500,
            reviews_count=400,
            clicks_count=8000,
            conversions_count=320,
            is_available=True,
            treat_zero_popularity_as_missing=True,
        )
    )
    assert Decimal("0") <= result.total_score <= Decimal("100")
    assert result.missing_pillars == ()
    assert result.redistributed is False
    assert sum(p.applied_weight for p in result.pillars) == Decimal("100.00")


def test_missing_popularity_redistributes_weights(ranking_service: RankingService) -> None:
    result = ranking_service.calculate(
        RankingInput(
            discount_percent=Decimal("25"),
            average_rating=None,
            ratings_count=0,
            sales_count=0,
            reviews_count=0,
            clicks_count=0,
            conversions_count=0,
            treat_zero_popularity_as_missing=True,
        )
    )
    assert "rating" in result.missing_pillars
    assert "sales" in result.missing_pillars
    assert "reviews" in result.missing_pillars
    assert result.redistributed is True

    available = [p for p in result.pillars if p.data_available]
    assert {p.key for p in available} == {"discount", "engagement"}
    assert sum(p.applied_weight for p in available) == Decimal("100.00")
    for missing in result.missing_pillars:
        pillar = next(p for p in result.pillars if p.key == missing)
        assert pillar.applied_weight == Decimal("0.00")
        assert pillar.contribution == Decimal("0.00")


def test_zero_popularity_can_count_as_data() -> None:
    service = RankingService()
    result = service.calculate(
        RankingInput(
            discount_percent=Decimal("20"),
            average_rating=Decimal("0"),
            ratings_count=1,  # rating present but low
            sales_count=0,
            reviews_count=0,
            treat_zero_popularity_as_missing=False,
        )
    )
    assert "sales" not in result.missing_pillars
    assert "reviews" not in result.missing_pillars


def test_custom_weights_are_normalized() -> None:
    from app.services.ranking_service import RankingConfig

    service = RankingService(
        RankingConfig(
            weights=RankingWeights(
                discount=Decimal("2"),
                rating=Decimal("2"),
                sales=Decimal("2"),
                reviews=Decimal("2"),
                engagement=Decimal("2"),
            )
        )
    )
    result = service.calculate(
        RankingInput(
            discount_percent=Decimal("40"),
            average_rating=Decimal("5"),
            ratings_count=10,
            sales_count=100,
            reviews_count=50,
            clicks_count=100,
            conversions_count=10,
            treat_zero_popularity_as_missing=False,
        )
    )
    assert sum(p.configured_weight for p in result.pillars) == Decimal("100.00")


def test_discount_pillar_only_still_scores(ranking_service: RankingService) -> None:
    result = ranking_service.calculate(
        RankingInput(
            discount_percent=Decimal("40"),
            average_rating=None,
            ratings_count=0,
            sales_count=None,
            reviews_count=None,
            clicks_count=0,
            conversions_count=0,
        )
    )
    discount = next(p for p in result.pillars if p.key == "discount")
    assert discount.raw_score == Decimal("100.00")
    assert result.total_score > Decimal("0")


def test_pillar_keys_are_exactly_five(ranking_service: RankingService) -> None:
    result = ranking_service.calculate(RankingInput(discount_percent=Decimal("10")))
    assert [p.key for p in result.pillars] == [
        "discount",
        "rating",
        "sales",
        "reviews",
        "engagement",
    ]
