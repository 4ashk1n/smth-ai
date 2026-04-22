from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TopicIn(BaseModel):
    id: str
    articleId: str
    title: str
    order: int


class PageIn(BaseModel):
    id: str
    topicId: str
    order: int


class Object3DIn(BaseModel):
    depth: int
    translateX: int
    translateY: int
    translateZ: int
    rotateX: int
    rotateY: int
    rotateZ: int
    scale: float


class LayoutIn(BaseModel):
    i: str
    x: int
    y: int
    w: int
    h: int


class BlockIn(BaseModel):
    id: str
    pageId: str
    type: str
    layout: LayoutIn
    object3d: Object3DIn | None = None
    content: str | None = None
    url: str | None = None
    source: str | None = None
    sourceUrl: str | None = None
    label: str | None = None
    name: str | None = None


class ContentIn(BaseModel):
    articleId: str
    topics: list[TopicIn]
    pages: list[PageIn]
    blocks: list[BlockIn]


class ArticleIn(BaseModel):
    id: str
    title: str
    description: str | None = None
    content: ContentIn
    authorId: str
    mainCategoryId: str
    categories: list[str] = Field(default_factory=list)
    status: Literal["published", "draft", "archived", "review"]
    publishedAt: datetime | str | None = None
    createdAt: datetime | str
    updatedAt: datetime | str


class SuggestionOut(BaseModel):
    suggestionId: str
    articleId: str
    topicId: str | None = None
    pageId: str | None = None
    blockId: str | None = None
    scope: str
    category: str
    severity: str
    message: str
    proposedFix: str
    meta: dict = Field(default_factory=dict)


class SuggestionsResponse(BaseModel):
    suggestions: list[SuggestionOut]

