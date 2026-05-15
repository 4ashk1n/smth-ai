from ai_module.features.recommendations.ranking import RankedRecommendation
from ai_module.features.recommendations.repository import FeedRepository


def test_fetch_interactions_and_published_articles(db_connection, seed_reco_demo_data) -> None:
    repository = FeedRepository(db_connection)

    interactions = repository.fetch_interactions(lookback_days=180)
    published = repository.fetch_published_articles()

    interaction_article_ids = {item.article_id for item in interactions}
    published_article_ids = {item.article_id for item in published}

    assert seed_reco_demo_data["article_1"] in interaction_article_ids
    assert seed_reco_demo_data["article_2"] in interaction_article_ids
    assert seed_reco_demo_data["article_1"] in published_article_ids
    assert seed_reco_demo_data["article_2"] in published_article_ids


def test_replace_user_feed_rewrites_rows(db_connection, seed_reco_demo_data) -> None:
    repository = FeedRepository(db_connection)
    user_id = seed_reco_demo_data["user_id"]

    first = [
        RankedRecommendation(article_id=seed_reco_demo_data["article_1"], score=0.7),
    ]
    second = [
        RankedRecommendation(article_id=seed_reco_demo_data["article_2"], score=0.9),
    ]

    written_first = repository.replace_user_feed(user_id, first)
    assert written_first == 1

    written_second = repository.replace_user_feed(user_id, second)
    assert written_second == 1

    with db_connection.cursor() as cursor:
        cursor.execute('SELECT "articleId", "score" FROM "user_feed" WHERE "userId" = %s ORDER BY "position" ASC', (user_id,))
        rows = cursor.fetchall()

    assert len(rows) == 1
    assert rows[0]["articleId"] == seed_reco_demo_data["article_2"]
    assert float(rows[0]["score"]) == 0.9

