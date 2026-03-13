from ai_module.api.schemas import ArticleIn, BlockIn
from ai_module.domain.entities import (
    Article,
    ArticleStatus,
    Block,
    BlockIcon,
    BlockImage,
    BlockParagraph,
    BlockType,
    Content,
    Layout,
    Object3D,
    Page,
    Suggestion,
    Topic,
)


def to_domain_article(payload: ArticleIn) -> Article:
    topics = [
        Topic(
            id=topic.id,
            article_id=topic.articleId,
            title=topic.title,
            order=topic.order,
        )
        for topic in payload.content.topics
    ]
    pages = [
        Page(id=page.id, topic_id=page.topicId, order=page.order)
        for page in payload.content.pages
    ]
    blocks = [to_domain_block(block) for block in payload.content.blocks]

    content = Content(
        article_id=payload.content.articleId,
        topics=topics,
        pages=pages,
        blocks=blocks,
    )
    return Article(
        id=payload.id,
        title=payload.title,
        description=payload.description,
        content=content,
        author_id=payload.authorId,
        main_category_id=payload.mainCategoryId,
        categories=payload.categories,
        status=ArticleStatus(payload.status),
        published_at=payload.publishedAt,
        created_at=payload.createdAt,
        updated_at=payload.updatedAt,
    )


def to_domain_block(block: BlockIn) -> Block:
    layout = Layout(
        i=block.layout.i,
        x=block.layout.x,
        y=block.layout.y,
        w=block.layout.w,
        h=block.layout.h,
    )
    object3d = None
    if block.object3d is not None:
        object3d = Object3D(
            depth=block.object3d.depth,
            translate_x=block.object3d.translateX,
            translate_y=block.object3d.translateY,
            translate_z=block.object3d.translateZ,
            rotate_x=block.object3d.rotateX,
            rotate_y=block.object3d.rotateY,
            rotate_z=block.object3d.rotateZ,
            scale=block.object3d.scale,
        )

    block_type = _map_block_type(block.type)
    if block_type == BlockType.PARAGRAPH:
        return BlockParagraph(
            id=block.id,
            page_id=block.pageId,
            type=block_type,
            layout=layout,
            object3d=object3d,
            content=block.content or "",
        )
    if block_type == BlockType.IMAGE:
        return BlockImage(
            id=block.id,
            page_id=block.pageId,
            type=block_type,
            layout=layout,
            object3d=object3d,
            url=block.url or "",
            source=block.source,
            source_url=block.sourceUrl,
            label=block.label,
        )
    return BlockIcon(
        id=block.id,
        page_id=block.pageId,
        type=block_type,
        layout=layout,
        object3d=object3d,
        name=block.name or "",
    )


def _map_block_type(value: str) -> BlockType:
    normalized = value.strip().lower()
    mapping = {
        "paragraph": BlockType.PARAGRAPH,
        "text": BlockType.PARAGRAPH,
        "image": BlockType.IMAGE,
        "icon": BlockType.ICON,
    }
    return mapping.get(normalized, BlockType.PARAGRAPH)


def to_api_suggestion(item: Suggestion) -> dict:
    return {
        "suggestionId": item.suggestion_id,
        "articleId": item.article_id,
        "topicId": item.topic_id,
        "pageId": item.page_id,
        "blockId": item.block_id,
        "scope": item.scope.value,
        "category": item.category.value,
        "severity": item.severity.value,
        "message": item.message,
        "proposedFix": item.proposed_fix,
        "meta": item.meta,
    }

