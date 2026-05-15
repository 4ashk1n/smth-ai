from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Iterator

import pytest
from psycopg import Connection, connect
from psycopg.rows import dict_row


@pytest.fixture(scope="session")
def db_url() -> str:
    value = os.getenv("DATABASE_URL", "").strip()
    if not value:
        pytest.skip("DATABASE_URL is empty. Use scripts/run_tests.py with ai_module/.env.test")
    return value


@pytest.fixture(scope="session")
def db_connection(db_url: str) -> Iterator[Connection]:
    conn = connect(db_url, row_factory=dict_row, autocommit=True)
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture(autouse=True)
def clean_reco_tables(db_connection: Connection) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute('TRUNCATE TABLE "user_feed", "reco_dirty_users", "user_article_metrics" RESTART IDENTITY CASCADE')


@pytest.fixture
def seed_reco_demo_data(db_connection: Connection) -> dict[str, str]:
    user_id = "2b7f3d85-d8f6-40eb-af26-2f9f5c6d56bf"
    user2_id = "7fef4f0f-3ff7-4d68-8aef-13f55b1ec9df"
    category_id = "91f47ea8-0e80-4dd5-b48c-ee0b6f79e4c9"
    article_1 = "9082d221-a0d8-4da1-b58a-e99d58d6d0d7"
    article_2 = "f5e6346a-231e-42a8-b094-cf76e00a66ef"

    now = datetime(2026, 5, 9, 10, 0, tzinfo=UTC)

    with db_connection.cursor() as cursor:
        cursor.execute(
            '''
            INSERT INTO "users" (
              "id", "username", "firstname", "lastname", "avatar", "role", "email", "isBanned", "provider", "createdAt", "updatedAt"
            ) VALUES
              (%s, 'alina.astro', 'Алина', 'Воронцова', 'https://api.dicebear.com/9.x/adventurer/svg?seed=AlinaAstro', 'user', 'alina.astro@demo-smth.ru', false, 'local', %s, %s),
              (%s, 'maks.space', 'Макс', 'Орлов', 'https://api.dicebear.com/9.x/adventurer/svg?seed=MaksSpace', 'user', 'maks.space@demo-smth.ru', false, 'local', %s, %s)
            ON CONFLICT ("id") DO UPDATE SET "updatedAt" = EXCLUDED."updatedAt"
            ''',
            (user_id, now, now, user2_id, now, now),
        )

        cursor.execute(
            '''
            INSERT INTO "categories" ("id", "name", "emoji", "colors", "createdAt", "updatedAt")
            VALUES (%s, 'Космос', '🚀', '{"accentColor":"#4C6FFF","darkColor":"#1D2A52","lightColor":"#DCE5FF"}'::jsonb, %s, %s)
            ON CONFLICT ("id") DO UPDATE SET "updatedAt" = EXCLUDED."updatedAt"
            ''',
            (category_id, now, now),
        )

        cursor.execute(
            '''
            INSERT INTO "articles" (
              "id", "title", "description", "content", "authorId", "mainCategoryId", "status", "publishedAt", "createdAt", "updatedAt"
            ) VALUES
              (%s, 'Взгляд назад', 'Почему телескопы смотрят в прошлое', '{}'::jsonb, %s, %s, 'published', %s, %s, %s),
              (%s, 'Свет далёких галактик', 'Как телескопы собирают древний свет', '{}'::jsonb, %s, %s, 'published', %s, %s, %s)
            ON CONFLICT ("id") DO UPDATE SET "updatedAt" = EXCLUDED."updatedAt"
            ''',
            (article_1, user_id, category_id, now, now, now, article_2, user2_id, category_id, now, now, now),
        )

        cursor.execute(
            '''
            INSERT INTO "_ArticleCategories" ("A", "B") VALUES (%s, %s), (%s, %s)
            ON CONFLICT DO NOTHING
            ''',
            (article_1, category_id, article_2, category_id),
        )

        cursor.execute(
            '''
            INSERT INTO "user_article_metrics" (
              "userId", "articleId", "focusTime", "viewedPages", "liked", "saved", "disliked", "reposted", "subscribed", "lastViewedAt", "updatedAt"
            ) VALUES
              (%s, %s, 120, 3, true, false, false, false, false, %s, %s),
              (%s, %s, 45, 1, true, false, false, false, false, %s, %s)
            ''',
            (user_id, article_1, now, now, user2_id, article_2, now, now),
        )

    return {
        "user_id": user_id,
        "user2_id": user2_id,
        "category_id": category_id,
        "article_1": article_1,
        "article_2": article_2,
    }

