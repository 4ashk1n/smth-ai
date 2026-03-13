from fastapi.testclient import TestClient

from ai_module.api.main import app
from ai_module.domain.entities import (
    Suggestion,
    SuggestionCategory,
    SuggestionScope,
    SuggestionSeverity,
)


def _payload() -> dict:
    return {
        "id": "a1",
        "title": "Тестовая статья",
        "description": None,
        "content": {
            "articleId": "a1",
            "topics": [{"id": "t1", "articleId": "a1", "title": "Тема", "order": 1}],
            "pages": [{"id": "p1", "topicId": "t1", "order": 1}],
            "blocks": [
                {
                    "id": "b1",
                    "pageId": "p1",
                    "type": "icon",
                    "layout": {"i": "b1", "x": 0, "y": 1, "w": 1, "h": 2},
                    "object3d": None,
                    "name": "rocket",
                },
                {
                    "id": "b2",
                    "pageId": "p1",
                    "type": "paragraph",
                    "layout": {"i": "b2", "x": 0, "y": 3, "w": 1, "h": 2},
                    "object3d": None,
                    "content": "Текст блока",
                },
            ],
        },
        "authorId": "u1",
        "mainCategoryId": "c1",
        "categories": [],
        "status": "draft",
        "publishedAt": None,
        "createdAt": "2026-03-12T10:00:00Z",
        "updatedAt": "2026-03-12T10:00:00Z",
    }


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_layout_suggestions_endpoint_returns_results() -> None:
    client = TestClient(app)
    response = client.post("/api/v1/suggestions/layout", json=_payload())
    assert response.status_code == 200
    body = response.json()
    assert "suggestions" in body
    assert len(body["suggestions"]) >= 1


def test_text_suggestions_endpoint_with_stub(monkeypatch) -> None:
    from ai_module.api.routers import suggestions as router_module

    class StubTextPipeline:
        def run_for_article(self, article):
            return [
                Suggestion(
                    suggestion_id="s1",
                    article_id=article.id,
                    topic_id="t1",
                    page_id="p1",
                    block_id="b2",
                    scope=SuggestionScope.BLOCK,
                    category=SuggestionCategory.STYLE,
                    severity=SuggestionSeverity.MINOR,
                    message="Сделайте стиль чуть нейтральнее.",
                    proposed_fix="Уберите разговорный оборот.",
                )
            ]

    monkeypatch.setattr(router_module, "get_text_pipeline", lambda: StubTextPipeline())

    client = TestClient(app)
    response = client.post("/api/v1/suggestions/text", json=_payload())
    assert response.status_code == 200
    body = response.json()
    assert len(body["suggestions"]) == 1
    assert body["suggestions"][0]["suggestionId"] == "s1"

