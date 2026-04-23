from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import uuid4

from ai_module.domain.recommendation import InteractionSignal, RankedRecommendation

if TYPE_CHECKING:
    from psycopg import Connection


_ADVISORY_LOCK_KEY = 913_117_521


@dataclass
class FeedWriteStats:
    users_updated: int = 0
    rows_written: int = 0


@dataclass(frozen=True)
class PublishedArticle:
    article_id: str
    published_at: datetime | None
    category_ids: tuple[str, ...]


class FeedRepository:
    def __init__(self, connection: "Connection") -> None:
        self.connection = connection
        self._lock_acquired = False

    def try_acquire_lock(self) -> bool:
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT pg_try_advisory_lock(%s) AS locked", (_ADVISORY_LOCK_KEY,))
            row = cursor.fetchone()
        self._lock_acquired = bool(row and row["locked"])
        return self._lock_acquired

    def release_lock(self) -> None:
        if not self._lock_acquired:
            return
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_unlock(%s)", (_ADVISORY_LOCK_KEY,))
        self._lock_acquired = False

    def fetch_user_ids(self) -> list[str]:
        with self.connection.cursor() as cursor:
            cursor.execute('SELECT "id" FROM "users" ORDER BY "id"')
            rows = cursor.fetchall()
        return [row["id"] for row in rows]

    def fetch_interactions(self, *, lookback_days: int) -> list[InteractionSignal]:
        where_clauses = ['a."status" = %s']
        params: list[object] = ["published"]

        if lookback_days > 0:
            cutoff = datetime.now(tz=UTC) - timedelta(days=lookback_days)
            where_clauses.append(
                '(COALESCE(m."lastViewedAt", m."updatedAt", NOW()) >= %s)'
            )
            params.append(cutoff)

        query = f'''
            SELECT
                m."userId" AS user_id,
                m."articleId" AS article_id,
                m."focusTime" AS focus_time,
                m."viewedPages" AS viewed_pages,
                m."liked" AS liked,
                m."saved" AS saved,
                m."disliked" AS disliked,
                m."reposted" AS reposted,
                m."lastViewedAt" AS last_viewed_at
            FROM "user_article_metrics" m
            INNER JOIN "articles" a ON a."id" = m."articleId"
            WHERE {' AND '.join(where_clauses)}
        '''

        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

        return [
            InteractionSignal(
                user_id=row["user_id"],
                article_id=row["article_id"],
                focus_time=int(row["focus_time"]),
                viewed_pages=int(row["viewed_pages"]),
                liked=bool(row["liked"]),
                saved=bool(row["saved"]),
                disliked=bool(row["disliked"]),
                reposted=bool(row["reposted"]),
                last_viewed_at=row["last_viewed_at"],
            )
            for row in rows
        ]

    def fetch_published_articles(self) -> list[PublishedArticle]:
        query = '''
            SELECT
                a."id" AS article_id,
                a."publishedAt" AS published_at,
                a."mainCategoryId" AS main_category_id,
                ARRAY_REMOVE(ARRAY_AGG(DISTINCT ac."B"), NULL) AS category_ids
            FROM "articles" a
            LEFT JOIN "_ArticleCategories" ac ON ac."A" = a."id"
            WHERE a."status" = 'published'
            GROUP BY a."id", a."publishedAt", a."mainCategoryId"
        '''

        with self.connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

        result: list[PublishedArticle] = []
        for row in rows:
            category_ids = set(row["category_ids"] or [])
            if row["main_category_id"]:
                category_ids.add(row["main_category_id"])
            result.append(
                PublishedArticle(
                    article_id=row["article_id"],
                    published_at=row["published_at"],
                    category_ids=tuple(sorted(category_ids)),
                )
            )
        return result

    def replace_user_feed(self, user_id: str, recommendations: list[RankedRecommendation]) -> int:
        with self.connection.cursor() as cursor:
            cursor.execute('DELETE FROM "user_feed" WHERE "userId" = %s', (user_id,))

            if not recommendations:
                return 0

            rows = [
                (
                    str(uuid4()),
                    position,
                    recommendation.article_id,
                    user_id,
                    float(recommendation.score),
                )
                for position, recommendation in enumerate(recommendations)
            ]

            cursor.executemany(
                '''
                INSERT INTO "user_feed" ("id", "position", "articleId", "userId", "score", "createdAt")
                VALUES (%s, %s, %s, %s, %s, NOW())
                ''',
                rows,
            )

            return len(rows)
