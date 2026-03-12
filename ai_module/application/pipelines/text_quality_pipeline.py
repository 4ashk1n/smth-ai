from uuid import uuid4

from ai_module.core.errors import SuggestionBuildError, ValidationError
from ai_module.domain.entities import (
    Article,
    BlockParagraph,
    Suggestion,
    SuggestionCategory,
    SuggestionScope,
    SuggestionSeverity,
)
from ai_module.providers.llm.base import LLMProvider
from ai_module.providers.llm.prompt_builder import PromptBuilder


class TextQualityPipeline:
    def __init__(self, llm_provider: LLMProvider, prompt_builder: PromptBuilder) -> None:
        self.llm_provider = llm_provider
        self.prompt_builder = prompt_builder

    def run_for_article(self, article: Article) -> list[Suggestion]:
        pages_by_id = {page.id: page for page in article.content.pages}
        topics_by_id = {topic.id: topic for topic in article.content.topics}
        suggestions: list[Suggestion] = []

        for block in article.content.blocks:
            if not isinstance(block, BlockParagraph):
                continue

            page = pages_by_id.get(block.page_id)
            if page is None:
                raise ValidationError(f"Page not found for block {block.id}")
            topic = topics_by_id.get(page.topic_id)
            if topic is None:
                raise ValidationError(f"Topic not found for page {page.id}")

            prompt = self.prompt_builder.build_block_text_review_prompt(
                article=article,
                topic=topic,
                page=page,
                block=block,
            )
            raw = self.llm_provider.generate_json(prompt=prompt)
            suggestions.extend(
                self._to_suggestions(
                    article_id=article.id,
                    topic_id=topic.id,
                    page_id=page.id,
                    block_id=block.id,
                    raw=raw,
                )
            )

        return suggestions

    def _to_suggestions(
        self,
        *,
        article_id: str,
        topic_id: str,
        page_id: str,
        block_id: str,
        raw: dict,
    ) -> list[Suggestion]:
        raw_suggestions = raw.get("suggestions", [])
        if not isinstance(raw_suggestions, list):
            raise SuggestionBuildError("LLM output does not contain suggestions list")

        output: list[Suggestion] = []
        for item in raw_suggestions:
            if not isinstance(item, dict):
                continue

            category = self._map_category(item.get("category", "style"))
            severity = self._map_severity(item.get("severity", "minor"))
            message = str(item.get("message", "")).strip()
            proposed_fix = str(item.get("proposed_fix", "")).strip()

            if not message:
                continue

            output.append(
                Suggestion(
                    suggestion_id=str(uuid4()),
                    article_id=article_id,
                    topic_id=topic_id,
                    page_id=page_id,
                    block_id=block_id,
                    scope=SuggestionScope.BLOCK,
                    category=category,
                    severity=severity,
                    message=message,
                    proposed_fix=proposed_fix,
                )
            )

        return output

    @staticmethod
    def _map_category(value: str) -> SuggestionCategory:
        mapping = {
            "grammar": SuggestionCategory.GRAMMAR,
            "punctuation": SuggestionCategory.PUNCTUATION,
            "style": SuggestionCategory.STYLE,
            "coherence": SuggestionCategory.COHERENCE,
            "factuality": SuggestionCategory.FACTUALITY,
            "layout": SuggestionCategory.LAYOUT,
        }
        return mapping.get(str(value).lower(), SuggestionCategory.STYLE)

    @staticmethod
    def _map_severity(value: str) -> SuggestionSeverity:
        mapping = {
            "critical": SuggestionSeverity.CRITICAL,
            "major": SuggestionSeverity.MAJOR,
            "minor": SuggestionSeverity.MINOR,
            "info": SuggestionSeverity.INFO,
            "suggestion": SuggestionSeverity.INFO,
        }
        return mapping.get(str(value).lower(), SuggestionSeverity.MINOR)

