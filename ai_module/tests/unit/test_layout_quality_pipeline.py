from ai_module.application.pipelines.layout_quality_pipeline import LayoutQualityPipeline
from ai_module.domain.entities import (
    Article,
    ArticleStatus,
    BlockIcon,
    BlockImage,
    BlockParagraph,
    BlockType,
    Content,
    Layout,
    Page,
    SuggestionScope,
    Topic,
)


def _base_article(blocks: list) -> Article:
    content = Content(
        article_id="a1",
        topics=[Topic(id="t1", article_id="a1", title="Тема", order=1)],
        pages=[Page(id="p1", topic_id="t1", order=1)],
        blocks=blocks,
    )
    return Article(
        id="a1",
        title="Статья",
        description=None,
        content=content,
        author_id="u1",
        main_category_id="c1",
        status=ArticleStatus.DRAFT,
    )


def test_layout_pipeline_detects_visual_lead_and_sequence() -> None:
    article = _base_article(
        [
            BlockIcon(
                id="b1",
                page_id="p1",
                type=BlockType.ICON,
                layout=Layout(i="b1", x=0, y=1, w=1, h=2),
                name="rocket",
            ),
            BlockImage(
                id="b2",
                page_id="p1",
                type=BlockType.IMAGE,
                layout=Layout(i="b2", x=0, y=3, w=1, h=2),
                url="https://example.com/img.png",
            ),
            BlockParagraph(
                id="b3",
                page_id="p1",
                type=BlockType.PARAGRAPH,
                layout=Layout(i="b3", x=0, y=5, w=1, h=2),
                content="Вводный текст",
            ),
        ]
    )
    out = LayoutQualityPipeline().run_for_article(article)
    messages = [s.message for s in out]
    assert any("начинается с визуального" in msg for msg in messages)
    assert any("визуальных блока подряд" in msg for msg in messages)


def test_layout_pipeline_detects_overlap() -> None:
    article = _base_article(
        [
            BlockParagraph(
                id="b1",
                page_id="p1",
                type=BlockType.PARAGRAPH,
                layout=Layout(i="b1", x=0, y=1, w=1, h=4),
                content="Текст",
            ),
            BlockImage(
                id="b2",
                page_id="p1",
                type=BlockType.IMAGE,
                layout=Layout(i="b2", x=0, y=3, w=1, h=2),
                url="https://example.com/img.png",
            ),
        ]
    )
    out = LayoutQualityPipeline().run_for_article(article)
    assert any("пересекается" in s.message for s in out)


def test_layout_pipeline_detects_page_without_text() -> None:
    article = _base_article(
        [
            BlockImage(
                id="b1",
                page_id="p1",
                type=BlockType.IMAGE,
                layout=Layout(i="b1", x=0, y=1, w=1, h=2),
                url="https://example.com/img.png",
            )
        ]
    )
    out = LayoutQualityPipeline().run_for_article(article)
    assert any(s.scope == SuggestionScope.PAGE for s in out)
    assert any("нет текстовых блоков" in s.message for s in out)


def test_layout_pipeline_ok_case_returns_empty() -> None:
    article = _base_article(
        [
            BlockParagraph(
                id="b1",
                page_id="p1",
                type=BlockType.PARAGRAPH,
                layout=Layout(i="b1", x=0, y=1, w=1, h=2),
                content="Вводный тезис",
            ),
            BlockImage(
                id="b2",
                page_id="p1",
                type=BlockType.IMAGE,
                layout=Layout(i="b2", x=1, y=1, w=1, h=2),
                url="https://example.com/img.png",
            ),
        ]
    )
    out = LayoutQualityPipeline().run_for_article(article)
    assert out == []

