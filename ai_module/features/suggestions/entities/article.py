from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Union

from ai_module.shared.exceptions import ValidationError


DateTimeLike = Union[datetime, str]


class ArticleStatus(str, Enum):
    PUBLISHED = "published"
    DRAFT = "draft"
    ARCHIVED = "archived"
    REVIEW = "review"


class BlockType(str, Enum):
    PARAGRAPH = "paragraph"
    IMAGE = "image"
    ICON = "icon"


@dataclass(frozen=True)
class Topic:
    id: str
    article_id: str
    title: str
    order: int

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValidationError("topic.id cannot be empty")
        if not self.article_id.strip():
            raise ValidationError("topic.article_id cannot be empty")
        if not self.title.strip():
            raise ValidationError("topic.title cannot be empty")
        if self.order < 1:
            raise ValidationError("topic.order must be >= 1")


@dataclass(frozen=True)
class Page:
    id: str
    topic_id: str
    order: int

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValidationError("page.id cannot be empty")
        if not self.topic_id.strip():
            raise ValidationError("page.topic_id cannot be empty")


@dataclass(frozen=True)
class Object3D:
    depth: int
    translate_x: int
    translate_y: int
    translate_z: int
    rotate_x: int
    rotate_y: int
    rotate_z: int
    scale: float

    def __post_init__(self) -> None:
        if not 1 <= self.depth <= 5:
            raise ValidationError("object3d.depth must be in range 1..5")
        if not 1 <= self.translate_x <= 5:
            raise ValidationError("object3d.translate_x must be in range 1..5")
        if not 1 <= self.translate_y <= 5:
            raise ValidationError("object3d.translate_y must be in range 1..5")
        if not 1 <= self.translate_z <= 5:
            raise ValidationError("object3d.translate_z must be in range 1..5")
        if not -15 <= self.rotate_x <= 15:
            raise ValidationError("object3d.rotate_x must be in range -15..15")
        if not -15 <= self.rotate_y <= 15:
            raise ValidationError("object3d.rotate_y must be in range -15..15")
        if not -15 <= self.rotate_z <= 15:
            raise ValidationError("object3d.rotate_z must be in range -15..15")
        if not 0.5 <= self.scale <= 1.5:
            raise ValidationError("object3d.scale must be in range 0.5..1.5")


@dataclass(frozen=True)
class Layout:
    i: str
    x: int
    y: int
    w: int
    h: int

    def __post_init__(self) -> None:
        if not self.i.strip():
            raise ValidationError("layout.i cannot be empty")
        if not 0 <= self.x <= 1:
            raise ValidationError("layout.x must be in range 0..1")
        if not 1 <= self.y <= 6:
            raise ValidationError("layout.y must be in range 1..6")
        if not 1 <= self.w <= 2:
            raise ValidationError("layout.w must be in range 1..2")
        if not 2 <= self.h <= 8:
            raise ValidationError("layout.h must be in range 2..8")

    @property
    def reading_index(self) -> int:
        return self.x * 8 + self.y


@dataclass(frozen=True)
class BlockBase:
    id: str
    page_id: str
    type: BlockType
    layout: Layout
    object3d: Optional[Object3D] = None

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValidationError("block.id cannot be empty")
        if not self.page_id.strip():
            raise ValidationError("block.page_id cannot be empty")


@dataclass(frozen=True)
class BlockParagraph(BlockBase):
    content: str = ""

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.type != BlockType.PARAGRAPH:
            raise ValidationError("BlockParagraph.type must be 'paragraph'")


@dataclass(frozen=True)
class BlockImage(BlockBase):
    url: str = ""
    source: Optional[str] = None
    source_url: Optional[str] = None
    label: Optional[str] = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.type != BlockType.IMAGE:
            raise ValidationError("BlockImage.type must be 'image'")
        if not self.url.strip():
            raise ValidationError("block_image.url cannot be empty")


@dataclass(frozen=True)
class BlockIcon(BlockBase):
    name: str = ""

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.type != BlockType.ICON:
            raise ValidationError("BlockIcon.type must be 'icon'")
        if not self.name.strip():
            raise ValidationError("block_icon.name cannot be empty")


Block = Union[BlockParagraph, BlockImage, BlockIcon]


@dataclass(frozen=True)
class Content:
    article_id: str
    topics: list[Topic] = field(default_factory=list)
    pages: list[Page] = field(default_factory=list)
    blocks: list[Block] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.article_id.strip():
            raise ValidationError("content.article_id cannot be empty")

    def blocks_in_reading_order(self, page_id: str) -> list[Block]:
        page_blocks = [b for b in self.blocks if b.page_id == page_id]
        return sorted(page_blocks, key=lambda b: b.layout.reading_index)


@dataclass(frozen=True)
class Article:
    id: str
    title: str
    description: Optional[str]
    content: Content
    author_id: str
    main_category_id: str
    categories: list[str] = field(default_factory=list)
    status: ArticleStatus = ArticleStatus.DRAFT
    published_at: Optional[DateTimeLike] = None
    created_at: DateTimeLike = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: DateTimeLike = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValidationError("article.id cannot be empty")
        if not self.author_id.strip():
            raise ValidationError("article.author_id cannot be empty")
        if not self.main_category_id.strip():
            raise ValidationError("article.main_category_id cannot be empty")



