import pytest

from ai_module.application.pipelines.text_quality_pipeline import TextQualityPipeline
from ai_module.core.errors import ProviderError, ValidationError
from ai_module.domain.entities import (
    Article,
    ArticleStatus,
    BlockIcon,
    BlockParagraph,
    BlockType,
    Content,
    Layout,
    Page,
    Topic,
)
from ai_module.providers.llm.prompt_builder import PromptBuilder


class StubLLMProvider:
    def generate_json(self, *, prompt: str) -> dict:
        assert "<USER_TEXT>" in prompt
        return {
            "summary": "ok",
            "suggestions": [
                {
                    "category": "style",
                    "severity": "minor",
                    "message": "Слишком разговорный оборот",
                    "proposed_fix": "Сделать формулировку нейтральнее",
                }
            ],
        }


class FailingLLMProvider:
    def generate_json(self, *, prompt: str) -> dict:
        raise ProviderError("broken json")


def build_article_with_blocks() -> Article:
    content = Content(
        article_id="a1",
        topics=[Topic(id="t1", article_id="a1", title="Тема", order=1)],
        pages=[Page(id="p1", topic_id="t1", order=1)],
        blocks=[
            BlockParagraph(
                id="b1",
                page_id="p1",
                type=BlockType.PARAGRAPH,
                layout=Layout(i="b1", x=0, y=1, w=1, h=2),
                content="Итак, погнали разбираться.",
            ),
            BlockIcon(
                id="b2",
                page_id="p1",
                type=BlockType.ICON,
                layout=Layout(i="b2", x=1, y=1, w=1, h=2),
                name="rocket",
            ),
        ],
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


def test_pipeline_returns_suggestions_for_paragraph_blocks_only() -> None:
    pipeline = TextQualityPipeline(
        llm_provider=StubLLMProvider(),
        prompt_builder=PromptBuilder(),
    )
    suggestions = pipeline.run_for_article(build_article_with_blocks())
    assert len(suggestions) == 1
    assert suggestions[0].block_id == "b1"
    assert suggestions[0].message


def test_pipeline_skips_block_if_provider_fails() -> None:
    pipeline = TextQualityPipeline(
        llm_provider=FailingLLMProvider(),
        prompt_builder=PromptBuilder(),
    )
    suggestions = pipeline.run_for_article(build_article_with_blocks())
    assert suggestions == []


def test_pipeline_raises_when_page_missing_for_block() -> None:
    bad_content = Content(
        article_id="a1",
        topics=[Topic(id="t1", article_id="a1", title="Тема", order=1)],
        pages=[],
        blocks=[
            BlockParagraph(
                id="b1",
                page_id="p1",
                type=BlockType.PARAGRAPH,
                layout=Layout(i="b1", x=0, y=1, w=1, h=2),
                content="Текст",
            )
        ],
    )
    article = Article(
        id="a1",
        title="Статья",
        description=None,
        content=bad_content,
        author_id="u1",
        main_category_id="c1",
        status=ArticleStatus.DRAFT,
    )
    pipeline = TextQualityPipeline(
        llm_provider=StubLLMProvider(),
        prompt_builder=PromptBuilder(),
    )
    with pytest.raises(ValidationError):
        pipeline.run_for_article(article)
