from uuid import uuid4

from ai_module.domain.entities import (
    Article,
    Block,
    BlockParagraph,
    Page,
    Suggestion,
    SuggestionCategory,
    SuggestionScope,
    SuggestionSeverity,
    Topic,
)


class LayoutRulesEngine:
    """Deterministic UX/layout checks for 2-column article pages."""

    def evaluate_page(self, *, article: Article, topic: Topic, page: Page) -> list[Suggestion]:
        blocks = article.content.blocks_in_reading_order(page.id)
        if not blocks:
            return []

        suggestions: list[Suggestion] = []
        suggestions.extend(self._check_overlap(article=article, topic=topic, page=page, blocks=blocks))
        suggestions.extend(self._check_row_overflow(article=article, topic=topic, page=page, blocks=blocks))
        suggestions.extend(self._check_first_block_is_visual(article=article, topic=topic, page=page, blocks=blocks))
        suggestions.extend(
            self._check_visual_sequence_before_text(article=article, topic=topic, page=page, blocks=blocks)
        )
        suggestions.extend(self._check_no_paragraphs(article=article, topic=topic, page=page, blocks=blocks))
        return suggestions

    def _check_overlap(
        self, *, article: Article, topic: Topic, page: Page, blocks: list[Block]
    ) -> list[Suggestion]:
        suggestions: list[Suggestion] = []
        for i in range(len(blocks)):
            for j in range(i + 1, len(blocks)):
                left = blocks[i]
                right = blocks[j]
                if _intersects(left, right):
                    suggestions.append(
                        self._suggestion(
                            article_id=article.id,
                            topic_id=topic.id,
                            page_id=page.id,
                            block_id=right.id,
                            severity=SuggestionSeverity.CRITICAL,
                            message=(
                                f"Блок пересекается с блоком {left.id}: элементы накладываются и ломают чтение."
                            ),
                            proposed_fix="Разведите блоки по координатам x/y или уменьшите w/h.",
                        )
                    )
        return suggestions

    def _check_row_overflow(
        self, *, article: Article, topic: Topic, page: Page, blocks: list[Block]
    ) -> list[Suggestion]:
        suggestions: list[Suggestion] = []
        for block in blocks:
            bottom = block.layout.y + block.layout.h - 1
            if bottom > 8:
                suggestions.append(
                    self._suggestion(
                        article_id=article.id,
                        topic_id=topic.id,
                        page_id=page.id,
                        block_id=block.id,
                        severity=SuggestionSeverity.MAJOR,
                        message=(
                            f"Блок выходит за пределы комфортной зоны 2x8 (нижняя граница: {bottom})."
                        ),
                        proposed_fix="Сократите высоту блока или сдвиньте его выше по оси y.",
                    )
                )
        return suggestions

    def _check_first_block_is_visual(
        self, *, article: Article, topic: Topic, page: Page, blocks: list[Block]
    ) -> list[Suggestion]:
        first = blocks[0]
        if isinstance(first, BlockParagraph):
            return []
        return [
            self._suggestion(
                article_id=article.id,
                topic_id=topic.id,
                page_id=page.id,
                block_id=first.id,
                severity=SuggestionSeverity.MAJOR,
                message="Страница начинается с визуального блока без текстового контекста.",
                proposed_fix="Поставьте короткий вводный текстовый блок первым в пути чтения.",
            )
        ]

    def _check_visual_sequence_before_text(
        self, *, article: Article, topic: Topic, page: Page, blocks: list[Block]
    ) -> list[Suggestion]:
        lead_visual: list[Block] = []
        for block in blocks:
            if isinstance(block, BlockParagraph):
                break
            lead_visual.append(block)

        if len(lead_visual) < 2:
            return []

        return [
            self._suggestion(
                article_id=article.id,
                topic_id=topic.id,
                page_id=page.id,
                block_id=lead_visual[-1].id,
                severity=SuggestionSeverity.MINOR,
                message=f"Перед первым текстом идет {len(lead_visual)} визуальных блока подряд.",
                proposed_fix="Сократите визуальную прелюдию до 1 блока или добавьте ранний поясняющий текст.",
            )
        ]

    def _check_no_paragraphs(
        self, *, article: Article, topic: Topic, page: Page, blocks: list[Block]
    ) -> list[Suggestion]:
        if any(isinstance(block, BlockParagraph) for block in blocks):
            return []
        return [
            self._suggestion(
                article_id=article.id,
                topic_id=topic.id,
                page_id=page.id,
                block_id=None,
                severity=SuggestionSeverity.MAJOR,
                message="На странице нет текстовых блоков, смысл может считываться неоднозначно.",
                proposed_fix="Добавьте хотя бы один текстовый блок с главным тезисом страницы.",
                scope=SuggestionScope.PAGE,
            )
        ]

    def _suggestion(
        self,
        *,
        article_id: str,
        topic_id: str,
        page_id: str,
        block_id: str | None,
        severity: SuggestionSeverity,
        message: str,
        proposed_fix: str,
        scope: SuggestionScope = SuggestionScope.BLOCK,
    ) -> Suggestion:
        return Suggestion(
            suggestion_id=str(uuid4()),
            article_id=article_id,
            topic_id=topic_id,
            page_id=page_id,
            block_id=block_id,
            scope=scope,
            category=SuggestionCategory.LAYOUT,
            severity=severity,
            message=message,
            proposed_fix=proposed_fix,
            meta={"engine": "layout_rules_v1"},
        )


def _intersects(first: Block, second: Block) -> bool:
    # Grid is 2 columns with row units. Use closed intervals.
    first_x1 = first.layout.x
    first_x2 = first.layout.x + first.layout.w - 1
    first_y1 = first.layout.y
    first_y2 = first.layout.y + first.layout.h - 1

    second_x1 = second.layout.x
    second_x2 = second.layout.x + second.layout.w - 1
    second_y1 = second.layout.y
    second_y2 = second.layout.y + second.layout.h - 1

    x_overlap = first_x1 <= second_x2 and second_x1 <= first_x2
    y_overlap = first_y1 <= second_y2 and second_y1 <= first_y2
    return x_overlap and y_overlap

