from datetime import UTC, datetime, timedelta

from ai_module.features.recommendations.ranking import (
    InteractionSignal,
    build_item_to_item_model,
    compute_interaction_weight,
)


def test_compute_interaction_weight_rewards_positive_signals() -> None:
    now = datetime(2026, 4, 22, tzinfo=UTC)
    positive = InteractionSignal(
        user_id="u1",
        article_id="a1",
        focus_time=120,
        viewed_pages=3,
        liked=True,
        saved=False,
        disliked=False,
        reposted=False,
        last_viewed_at=now - timedelta(days=1),
    )
    negative = InteractionSignal(
        user_id="u1",
        article_id="a2",
        focus_time=0,
        viewed_pages=0,
        liked=False,
        saved=False,
        disliked=True,
        reposted=False,
        last_viewed_at=now - timedelta(days=1),
    )

    assert compute_interaction_weight(positive, now=now, half_life_days=30) > 0
    assert compute_interaction_weight(negative, now=now, half_life_days=30) == 0


def test_item_to_item_builds_cross_item_recommendation() -> None:
    now = datetime(2026, 4, 22, tzinfo=UTC)
    interactions = [
        InteractionSignal("u1", "a1", 120, 2, True, False, False, False, now),
        InteractionSignal("u1", "a2", 30, 1, True, False, False, False, now),
        InteractionSignal("u2", "a1", 90, 1, True, False, False, False, now),
        InteractionSignal("u2", "a3", 40, 1, True, False, False, False, now),
    ]
    model = build_item_to_item_model(
        interactions=interactions,
        now=now,
        half_life_days=30,
        max_items_per_user=200,
        neighbors_per_item=100,
    )

    recommendations = model.recommend_for_user("u1", top_k=5, min_score=0.0)
    recommended_ids = [row.article_id for row in recommendations]

    assert "a3" in recommended_ids
    assert "a1" not in recommended_ids
    assert "a2" not in recommended_ids


def test_cold_start_fallback_uses_popular_items() -> None:
    now = datetime(2026, 4, 22, tzinfo=UTC)
    interactions = [
        InteractionSignal("u1", "a1", 120, 2, True, False, False, False, now),
        InteractionSignal("u2", "a2", 180, 2, True, True, False, False, now),
    ]
    model = build_item_to_item_model(
        interactions=interactions,
        now=now,
        half_life_days=30,
        max_items_per_user=200,
        neighbors_per_item=100,
    )

    recommendations = model.recommend_for_user("new-user", top_k=2, min_score=0.0)
    assert len(recommendations) == 2
    assert {row.article_id for row in recommendations} == {"a1", "a2"}



