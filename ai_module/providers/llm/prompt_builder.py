from pathlib import Path

from ai_module.domain.entities import Article, BlockParagraph, Page, Topic


class PromptBuilder:
    def __init__(self, templates_dir: Path | None = None) -> None:
        base_dir = Path(__file__).resolve().parent
        self.templates_dir = templates_dir or (base_dir / "prompt_templates")

    def build_block_text_review_prompt(
        self,
        *,
        article: Article,
        topic: Topic,
        page: Page,
        block: BlockParagraph,
    ) -> str:
        template = (self.templates_dir / "block_text_review_ru.txt").read_text(
            encoding="utf-8"
        )
        return template.format(
            article_id=article.id,
            article_title=article.title,
            topic_id=topic.id,
            topic_title=topic.title,
            page_id=page.id,
            block_id=block.id,
            block_text=block.content,
        )

