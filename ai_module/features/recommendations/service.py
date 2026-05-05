import logging
from dataclasses import dataclass
from datetime import UTC, datetime
import math

from ai_module.app.config import settings
from ai_module.features.recommendations.ranking import (
    InteractionSignal,
    RankedRecommendation,
    build_item_to_item_model,
    compute_interaction_weight,
)
from ai_module.infra.db import get_connection
from ai_module.features.recommendations.repository import FeedRepository

logger = logging.getLogger("ai_module")


@dataclass(frozen=True)
class RecomputeFeedResult:
    users_total: int
    users_updated: int
    rows_written: int
    interactions_total: int
    lock_acquired: bool


def _normalize_scores(scores: dict[str, float]) -> dict[str, float]:
    if not scores:
        return {}
    max_value = max(scores.values())
    if max_value <= 0:
        return {key: 0.0 for key in scores}
    return {key: value / max_value for key, value in scores.items()}


def _compute_freshness_score(
    published_at: datetime | None,
    *,
    now: datetime,
    half_life_days: float,
) -> float:
    if published_at is None:
        return 0.0

    normalized_now = now if now.tzinfo is not None else now.replace(tzinfo=UTC)
    normalized_published = (
        published_at if published_at.tzinfo is not None else published_at.replace(tzinfo=UTC)
    )
    age_days = max(0.0, (normalized_now - normalized_published).total_seconds() / 86400.0)

    if half_life_days <= 0:
        return 1.0
    return math.exp(-math.log(2.0) * age_days / half_life_days)


def _build_category_preferences(
    interactions: list[InteractionSignal],
    *,
    article_categories: dict[str, tuple[str, ...]],
    now: datetime,
    half_life_days: float,
) -> dict[str, dict[str, float]]:
    preferences: dict[str, dict[str, float]] = {}

    for signal in interactions:
        categories = article_categories.get(signal.article_id, ())
        if not categories:
            continue

        weight = compute_interaction_weight(signal, now=now, half_life_days=half_life_days)
        if weight <= 0:
            continue

        user_preferences = preferences.setdefault(signal.user_id, {})
        for category_id in categories:
            user_preferences[category_id] = user_preferences.get(category_id, 0.0) + weight

    return preferences


def _build_hybrid_recommendations_for_user(
    *,
    user_id: str,
    top_k: int,
    min_score: float,
    seen_ids: set[str],
    all_published_ids: list[str],
    article_categories: dict[str, tuple[str, ...]],
    article_published_at: dict[str, datetime | None],
    cf_scores_raw: dict[str, float],
    category_preferences: dict[str, float],
    popularity_scores_normalized: dict[str, float],
    now: datetime,
    freshness_half_life_days: float,
    weight_cf: float,
    weight_category: float,
    weight_freshness: float,
    weight_popularity: float,
) -> list[RankedRecommendation]:
    if top_k <= 0:
        return []

    unseen_ids = [article_id for article_id in all_published_ids if article_id not in seen_ids]
    if not unseen_ids:
        return []

    cf_scores = _normalize_scores({k: v for k, v in cf_scores_raw.items() if k in unseen_ids})

    category_scores_raw: dict[str, float] = {}
    if category_preferences:
        for article_id in unseen_ids:
            categories = article_categories.get(article_id, ())
            if not categories:
                continue
            score = sum(category_preferences.get(category_id, 0.0) for category_id in categories)
            if score > 0:
                category_scores_raw[article_id] = score
    category_scores = _normalize_scores(category_scores_raw)

    combined: list[RankedRecommendation] = []
    for article_id in unseen_ids:
        cf_score = cf_scores.get(article_id, 0.0)
        category_score = category_scores.get(article_id, 0.0)
        freshness_score = _compute_freshness_score(
            article_published_at.get(article_id),
            now=now,
            half_life_days=freshness_half_life_days,
        )
        popularity_score = popularity_scores_normalized.get(article_id, 0.0)

        final_score = (
            weight_cf * cf_score
            + weight_category * category_score
            + weight_freshness * freshness_score
            + weight_popularity * popularity_score
        )

        combined.append(RankedRecommendation(article_id=article_id, score=final_score))

    combined.sort(key=lambda row: (-row.score, row.article_id))

    if min_score > 0:
        above_threshold = [row for row in combined if row.score >= min_score]
        if len(above_threshold) >= top_k:
            return above_threshold[:top_k]

    return combined[:top_k]


def _resolve_params(
    *,
    top_k: int | None,
    lookback_days: int | None,
    half_life_days: float | None,
    max_items_per_user: int | None,
    neighbors_per_item: int | None,
    min_score: float | None,
) -> tuple[int, int, float, int, int, float, float, float, float, float, float]:
    resolved_top_k = settings.reco_top_k if top_k is None else top_k
    resolved_lookback_days = settings.reco_lookback_days if lookback_days is None else lookback_days
    resolved_half_life = settings.reco_half_life_days if half_life_days is None else half_life_days
    resolved_max_items = settings.reco_max_items_per_user if max_items_per_user is None else max_items_per_user
    resolved_neighbors = settings.reco_neighbors_per_item if neighbors_per_item is None else neighbors_per_item
    resolved_min_score = settings.reco_min_score if min_score is None else min_score
    resolved_weight_cf = settings.reco_weight_cf
    resolved_weight_category = settings.reco_weight_category
    resolved_weight_freshness = settings.reco_weight_freshness
    resolved_weight_popularity = settings.reco_weight_popularity
    resolved_freshness_half_life = settings.reco_freshness_half_life_days
    return (
        resolved_top_k,
        resolved_lookback_days,
        resolved_half_life,
        resolved_max_items,
        resolved_neighbors,
        resolved_min_score,
        resolved_weight_cf,
        resolved_weight_category,
        resolved_weight_freshness,
        resolved_weight_popularity,
        resolved_freshness_half_life,
    )


def _recompute_for_user_ids(
    *,
    repository: FeedRepository,
    connection: object,
    user_ids: list[str],
    top_k: int,
    lookback_days: int,
    half_life_days: float,
    max_items_per_user: int,
    neighbors_per_item: int,
    min_score: float,
    weight_cf: float,
    weight_category: float,
    weight_freshness: float,
    weight_popularity: float,
    freshness_half_life_days: float,
) -> RecomputeFeedResult:
    target_user_ids = list(dict.fromkeys(user_ids))
    if not target_user_ids:
        return RecomputeFeedResult(
            users_total=0,
            users_updated=0,
            rows_written=0,
            interactions_total=0,
            lock_acquired=True,
        )

    interactions = repository.fetch_interactions(lookback_days=lookback_days)
    published_articles = repository.fetch_published_articles()
    published_ids = [article.article_id for article in published_articles]
    article_categories = {
        article.article_id: article.category_ids
        for article in published_articles
    }
    article_published_at = {
        article.article_id: article.published_at
        for article in published_articles
    }

    now = datetime.now(tz=UTC)
    model = build_item_to_item_model(
        interactions=interactions,
        now=now,
        half_life_days=half_life_days,
        max_items_per_user=max_items_per_user,
        neighbors_per_item=neighbors_per_item,
    )
    category_preferences_by_user = _build_category_preferences(
        interactions,
        article_categories=article_categories,
        now=now,
        half_life_days=half_life_days,
    )
    popularity_scores = {
        article_id: score
        for article_id, score in model.popular_items
    }
    popularity_scores_normalized = _normalize_scores(popularity_scores)

    users_updated = 0
    rows_written = 0

    with connection.transaction():
        for user_id in target_user_ids:
            recommendations = _build_hybrid_recommendations_for_user(
                user_id=user_id,
                top_k=top_k,
                min_score=min_score,
                seen_ids=model.user_seen.get(user_id, set()),
                all_published_ids=published_ids,
                article_categories=article_categories,
                article_published_at=article_published_at,
                cf_scores_raw=model.score_candidates_for_user(
                    user_id=user_id,
                    min_score=0.0,
                ),
                category_preferences=category_preferences_by_user.get(user_id, {}),
                popularity_scores_normalized=popularity_scores_normalized,
                now=now,
                freshness_half_life_days=freshness_half_life_days,
                weight_cf=weight_cf,
                weight_category=weight_category,
                weight_freshness=weight_freshness,
                weight_popularity=weight_popularity,
            )
            written = repository.replace_user_feed(user_id, recommendations)
            users_updated += 1
            rows_written += written

    logger.info(
        "recompute_user_feed completed users_total=%s users_updated=%s rows_written=%s interactions_total=%s",
        len(target_user_ids),
        users_updated,
        rows_written,
        len(interactions),
    )

    return RecomputeFeedResult(
        users_total=len(target_user_ids),
        users_updated=users_updated,
        rows_written=rows_written,
        interactions_total=len(interactions),
        lock_acquired=True,
    )


def recompute_user_feed_for_user_ids(
    user_ids: list[str],
    *,
    top_k: int | None = None,
    lookback_days: int | None = None,
    half_life_days: float | None = None,
    max_items_per_user: int | None = None,
    neighbors_per_item: int | None = None,
    min_score: float | None = None,
) -> RecomputeFeedResult:
    (
        resolved_top_k,
        resolved_lookback_days,
        resolved_half_life,
        resolved_max_items,
        resolved_neighbors,
        resolved_min_score,
        resolved_weight_cf,
        resolved_weight_category,
        resolved_weight_freshness,
        resolved_weight_popularity,
        resolved_freshness_half_life,
    ) = _resolve_params(
        top_k=top_k,
        lookback_days=lookback_days,
        half_life_days=half_life_days,
        max_items_per_user=max_items_per_user,
        neighbors_per_item=neighbors_per_item,
        min_score=min_score,
    )

    with get_connection() as connection:
        repository = FeedRepository(connection)
        lock_acquired = repository.try_acquire_lock()
        if not lock_acquired:
            logger.info("recompute_user_feed_for_user_ids skipped: advisory lock is already held")
            return RecomputeFeedResult(
                users_total=0,
                users_updated=0,
                rows_written=0,
                interactions_total=0,
                lock_acquired=False,
            )

        try:
            return _recompute_for_user_ids(
                repository=repository,
                connection=connection,
                user_ids=user_ids,
                top_k=resolved_top_k,
                lookback_days=resolved_lookback_days,
                half_life_days=resolved_half_life,
                max_items_per_user=resolved_max_items,
                neighbors_per_item=resolved_neighbors,
                min_score=resolved_min_score,
                weight_cf=resolved_weight_cf,
                weight_category=resolved_weight_category,
                weight_freshness=resolved_weight_freshness,
                weight_popularity=resolved_weight_popularity,
                freshness_half_life_days=resolved_freshness_half_life,
            )
        finally:
            repository.release_lock()


def recompute_user_feed_once(
    *,
    top_k: int | None = None,
    lookback_days: int | None = None,
    half_life_days: float | None = None,
    max_items_per_user: int | None = None,
    neighbors_per_item: int | None = None,
    min_score: float | None = None,
) -> RecomputeFeedResult:
    (
        resolved_top_k,
        resolved_lookback_days,
        resolved_half_life,
        resolved_max_items,
        resolved_neighbors,
        resolved_min_score,
        resolved_weight_cf,
        resolved_weight_category,
        resolved_weight_freshness,
        resolved_weight_popularity,
        resolved_freshness_half_life,
    ) = _resolve_params(
        top_k=top_k,
        lookback_days=lookback_days,
        half_life_days=half_life_days,
        max_items_per_user=max_items_per_user,
        neighbors_per_item=neighbors_per_item,
        min_score=min_score,
    )

    with get_connection() as connection:
        repository = FeedRepository(connection)
        lock_acquired = repository.try_acquire_lock()
        if not lock_acquired:
            logger.info("recompute_user_feed skipped: advisory lock is already held")
            return RecomputeFeedResult(
                users_total=0,
                users_updated=0,
                rows_written=0,
                interactions_total=0,
                lock_acquired=False,
            )

        try:
            user_ids = repository.fetch_user_ids()
            return _recompute_for_user_ids(
                repository=repository,
                connection=connection,
                user_ids=user_ids,
                top_k=resolved_top_k,
                lookback_days=resolved_lookback_days,
                half_life_days=resolved_half_life,
                max_items_per_user=resolved_max_items,
                neighbors_per_item=resolved_neighbors,
                min_score=resolved_min_score,
                weight_cf=resolved_weight_cf,
                weight_category=resolved_weight_category,
                weight_freshness=resolved_weight_freshness,
                weight_popularity=resolved_weight_popularity,
                freshness_half_life_days=resolved_freshness_half_life,
            )
        finally:
            repository.release_lock()



