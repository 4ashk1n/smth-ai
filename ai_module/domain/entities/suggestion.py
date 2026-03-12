from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ai_module.core.errors import ValidationError


class SuggestionSeverity(str, Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    INFO = "info"


class SuggestionCategory(str, Enum):
    GRAMMAR = "grammar"
    PUNCTUATION = "punctuation"
    STYLE = "style"
    COHERENCE = "coherence"
    LAYOUT = "layout"
    FACTUALITY = "factuality"


class SuggestionScope(str, Enum):
    BLOCK = "block"
    PAGE = "page"
    TOPIC = "topic"
    ARTICLE = "article"


@dataclass(frozen=True)
class Suggestion:
    suggestion_id: str
    article_id: str
    scope: SuggestionScope
    category: SuggestionCategory
    severity: SuggestionSeverity
    message: str
    topic_id: str | None = None
    page_id: str | None = None
    block_id: str | None = None
    proposed_fix: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.suggestion_id.strip():
            raise ValidationError("suggestion_id cannot be empty")
        if not self.article_id.strip():
            raise ValidationError("article_id cannot be empty")
        if not self.message.strip():
            raise ValidationError("message cannot be empty")
        if self.scope == SuggestionScope.TOPIC and not self.topic_id:
            raise ValidationError("topic_id is required for topic-level suggestion")
        if self.scope == SuggestionScope.PAGE and not self.page_id:
            raise ValidationError("page_id is required for page-level suggestion")
        if self.scope == SuggestionScope.BLOCK and not self.block_id:
            raise ValidationError("block_id is required for block-level suggestion")
