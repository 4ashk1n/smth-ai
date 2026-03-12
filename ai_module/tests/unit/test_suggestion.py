import pytest

from ai_module.core.errors import ValidationError
from ai_module.domain.entities import (
    Suggestion,
    SuggestionCategory,
    SuggestionScope,
    SuggestionSeverity,
)


def test_block_scope_requires_block_id() -> None:
    with pytest.raises(ValidationError):
        Suggestion(
            suggestion_id="s1",
            article_id="a1",
            scope=SuggestionScope.BLOCK,
            category=SuggestionCategory.STYLE,
            severity=SuggestionSeverity.MINOR,
            message="msg",
        )


def test_page_scope_requires_page_id() -> None:
    with pytest.raises(ValidationError):
        Suggestion(
            suggestion_id="s2",
            article_id="a1",
            scope=SuggestionScope.PAGE,
            category=SuggestionCategory.COHERENCE,
            severity=SuggestionSeverity.MAJOR,
            message="msg",
        )


def test_valid_article_scope_suggestion() -> None:
    suggestion = Suggestion(
        suggestion_id="s3",
        article_id="a1",
        scope=SuggestionScope.ARTICLE,
        category=SuggestionCategory.STYLE,
        severity=SuggestionSeverity.INFO,
        message="ok",
    )
    assert suggestion.article_id == "a1"
    assert suggestion.scope == SuggestionScope.ARTICLE

