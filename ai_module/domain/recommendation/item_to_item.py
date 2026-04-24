import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class InteractionSignal:
    user_id: str
    article_id: str
    focus_time: int
    viewed_pages: int
    liked: bool
    saved: bool
    disliked: bool
    reposted: bool
    last_viewed_at: datetime | None


@dataclass(frozen=True)
class RankedRecommendation:
    article_id: str
    score: float


@dataclass
class ItemToItemModel:
    user_seen: dict[str, set[str]]
    user_positive: dict[str, list[tuple[str, float]]]
    neighbors_by_item: dict[str, list[tuple[str, float]]]
    popular_items: list[tuple[str, float]]

    def score_candidates_for_user(self, user_id: str, min_score: float = 0.0) -> dict[str, float]:
        seen = self.user_seen.get(user_id, set())
        scores: dict[str, float] = defaultdict(float)

        for item_id, user_weight in self.user_positive.get(user_id, []):
            for neighbor_id, similarity in self.neighbors_by_item.get(item_id, []):
                if neighbor_id in seen:
                    continue
                scores[neighbor_id] += user_weight * similarity

        return {
            article_id: score
            for article_id, score in scores.items()
            if score >= min_score
        }

    def recommend_for_user(self, user_id: str, top_k: int, min_score: float = 0.0) -> list[RankedRecommendation]:
        if top_k <= 0:
            return []

        seen = self.user_seen.get(user_id, set())
        scores = self.score_candidates_for_user(user_id=user_id, min_score=min_score)

        ranked = sorted(
            scores.items(),
            key=lambda row: (-row[1], row[0]),
        )

        recommendations: list[RankedRecommendation] = [
            RankedRecommendation(article_id=article_id, score=score)
            for article_id, score in ranked[:top_k]
        ]

        if len(recommendations) >= top_k:
            return recommendations

        existing = {row.article_id for row in recommendations}
        for article_id, popularity_score in self.popular_items:
            if len(recommendations) >= top_k:
                break
            if article_id in seen or article_id in existing:
                continue
            recommendations.append(RankedRecommendation(article_id=article_id, score=popularity_score))
            existing.add(article_id)

        return recommendations


def _to_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def compute_interaction_weight(
    signal: InteractionSignal,
    *,
    now: datetime,
    half_life_days: float,
) -> float:
    positive_reaction = 0.0
    positive_reaction += 2.0 if signal.liked else 0.0
    positive_reaction += 2.5 if signal.saved else 0.0
    positive_reaction += 3.0 if signal.reposted else 0.0
    positive_reaction -= 3.0 if signal.disliked else 0.0

    bounded_focus_time = max(0, int(signal.focus_time))
    bounded_viewed_pages = max(0, int(signal.viewed_pages))

    engagement = math.log1p(bounded_focus_time) / 6.0
    engagement += min(bounded_viewed_pages, 10) * 0.15

    base_score = positive_reaction + engagement
    if base_score <= 0:
        return 0.0

    if half_life_days <= 0:
        return base_score

    last_viewed_at = _to_utc(signal.last_viewed_at)
    if last_viewed_at is None:
        return base_score

    now_utc = _to_utc(now)
    if now_utc is None:
        return base_score

    age_seconds = max(0.0, (now_utc - last_viewed_at).total_seconds())
    age_days = age_seconds / 86400.0
    decay = math.exp(-math.log(2.0) * age_days / half_life_days)
    return base_score * decay


def build_item_to_item_model(
    interactions: list[InteractionSignal],
    *,
    now: datetime,
    half_life_days: float,
    max_items_per_user: int,
    neighbors_per_item: int,
) -> ItemToItemModel:
    user_seen: dict[str, set[str]] = defaultdict(set)
    user_positive_weights: dict[str, dict[str, float]] = defaultdict(dict)
    item_popularity: dict[str, float] = defaultdict(float)

    for signal in interactions:
        user_seen[signal.user_id].add(signal.article_id)
        interaction_weight = compute_interaction_weight(signal, now=now, half_life_days=half_life_days)
        if interaction_weight <= 0:
            continue

        existing = user_positive_weights[signal.user_id].get(signal.article_id, 0.0)
        if interaction_weight > existing:
            user_positive_weights[signal.user_id][signal.article_id] = interaction_weight
        item_popularity[signal.article_id] += interaction_weight

    user_positive: dict[str, list[tuple[str, float]]] = {}
    for user_id, weights in user_positive_weights.items():
        ranked = sorted(weights.items(), key=lambda row: (-row[1], row[0]))
        if max_items_per_user > 0:
            ranked = ranked[:max_items_per_user]
        user_positive[user_id] = ranked

    item_norms: dict[str, float] = defaultdict(float)
    pair_dot_products: dict[tuple[str, str], float] = defaultdict(float)

    for items in user_positive.values():
        if not items:
            continue

        for item_id, weight in items:
            item_norms[item_id] += weight * weight

        for left_index in range(len(items)):
            left_item, left_weight = items[left_index]
            for right_index in range(left_index + 1, len(items)):
                right_item, right_weight = items[right_index]
                if left_item == right_item:
                    continue
                pair_key = (left_item, right_item) if left_item < right_item else (right_item, left_item)
                pair_dot_products[pair_key] += left_weight * right_weight

    neighbors_by_item: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for (left_item, right_item), dot_product in pair_dot_products.items():
        denominator = math.sqrt(item_norms[left_item] * item_norms[right_item])
        if denominator <= 0:
            continue

        similarity = dot_product / denominator
        if similarity <= 0:
            continue

        neighbors_by_item[left_item].append((right_item, similarity))
        neighbors_by_item[right_item].append((left_item, similarity))

    if neighbors_per_item > 0:
        for item_id, neighbors in list(neighbors_by_item.items()):
            neighbors.sort(key=lambda row: (-row[1], row[0]))
            neighbors_by_item[item_id] = neighbors[:neighbors_per_item]

    popular_items = sorted(item_popularity.items(), key=lambda row: (-row[1], row[0]))

    return ItemToItemModel(
        user_seen={user_id: set(items) for user_id, items in user_seen.items()},
        user_positive=user_positive,
        neighbors_by_item={item_id: list(neighbors) for item_id, neighbors in neighbors_by_item.items()},
        popular_items=popular_items,
    )
