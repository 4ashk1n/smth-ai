from ai_module.features.suggestions.entities import Article, Suggestion
from ai_module.features.suggestions.llm.layout_rules import LayoutRulesEngine


class LayoutQualityPipeline:
    def __init__(self, rules_engine: LayoutRulesEngine | None = None) -> None:
        self.rules_engine = rules_engine or LayoutRulesEngine()

    def run_for_article(self, article: Article) -> list[Suggestion]:
        topics_by_id = {topic.id: topic for topic in article.content.topics}
        suggestions: list[Suggestion] = []

        for page in article.content.pages:
            topic = topics_by_id.get(page.topic_id)
            if topic is None:
                continue
            suggestions.extend(
                self.rules_engine.evaluate_page(
                    article=article,
                    topic=topic,
                    page=page,
                )
            )

        return suggestions




