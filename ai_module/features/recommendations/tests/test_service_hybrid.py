from datetime import UTC, datetime, timedelta

from ai_module.features.recommendations.service import (
    _build_category_preferences,
    _build_hybrid_recommendations_for_user,
    _compute_freshness_score,
    _normalize_scores,
)
from ai_module.features.recommendations.ranking import InteractionSignal


def test_normalize_scores_basic() -> None:
    result = _normalize_scores({"a": 2.0, "b": 1.0})
    assert result["a"] == 1.0
    assert result["b"] == 0.5


def test_freshness_score_newer_article_higher() -> None:
    now = datetime(2026, 5, 13, tzinfo=UTC)
    new_item = _compute_freshness_score(now - timedelta(days=1), now=now, half_life_days=14)
    old_item = _compute_freshness_score(now - timedelta(days=30), now=now, half_life_days=14)
    assert new_item > old_item


def test_category_preferences_accumulate_positive_weights() -> None:
    now = datetime(2026, 5, 13, tzinfo=UTC)
    interactions = [
        InteractionSignal("u1", "a1", 100, 3, True, False, False, False, now),
        InteractionSignal("u1", "a2", 80, 2, True, False, False, False, now),
    ]
    article_categories = {
        "a1": ("space",),
        "a2": ("space", "science"),
    }

    prefs = _build_category_preferences(
        interactions,
        article_categories=article_categories,
        now=now,
        half_life_days=30,
    )

    assert prefs["u1"]["space"] > 0
    assert prefs["u1"]["science"] > 0
    assert prefs["u1"]["space"] > prefs["u1"]["science"]


def test_build_hybrid_recommendations_excludes_seen_and_sorts() -> None:
    now = datetime(2026, 5, 13, tzinfo=UTC)
    published_ids = ["a1", "a2", "a3"]
    article_categories = {"a2": ("space",), "a3": ("science",)}
    article_published_at = {
        "a1": now - timedelta(days=2),
        "a2": now - timedelta(days=1),
        "a3": now - timedelta(days=10),
    }

    reco = _build_hybrid_recommendations_for_user(
        user_id="u1",
        top_k=2,
        min_score=0.0,
        seen_ids={"a1"},
        all_published_ids=published_ids,
        article_categories=article_categories,
        article_published_at=article_published_at,
        cf_scores_raw={"a2": 0.9, "a3": 0.3},
        category_preferences={"space": 2.0, "science": 0.5},
        popularity_scores_normalized={"a2": 0.6, "a3": 0.2},
        now=now,
        freshness_half_life_days=14,
        weight_cf=0.5,
        weight_category=0.25,
        weight_freshness=0.15,
        weight_popularity=0.1,
    )

    ids = [item.article_id for item in reco]
    assert "a1" not in ids
    assert ids == ["a2", "a3"]

