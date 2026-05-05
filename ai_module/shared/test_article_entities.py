import pytest

from ai_module.shared.exceptions import ValidationError
from ai_module.features.suggestions.entities import BlockParagraph, BlockType, Content, Layout, Page, Topic


def test_layout_reading_index_left_then_right_column() -> None:
    left_col_second_row = Layout(i="b1", x=0, y=2, w=1, h=2)
    right_col_first_row = Layout(i="b2", x=1, y=1, w=1, h=2)
    assert left_col_second_row.reading_index < right_col_first_row.reading_index


def test_layout_bounds_validation() -> None:
    with pytest.raises(ValidationError):
        Layout(i="bad", x=2, y=1, w=1, h=2)


def test_blocks_in_reading_order_for_page() -> None:
    content = Content(
        article_id="a1",
        topics=[Topic(id="t1", article_id="a1", title="Topic", order=1)],
        pages=[Page(id="p1", topic_id="t1", order=1)],
        blocks=[
            BlockParagraph(
                id="b2",
                page_id="p1",
                type=BlockType.PARAGRAPH,
                layout=Layout(i="b2", x=1, y=1, w=1, h=2),
                content="Second",
            ),
            BlockParagraph(
                id="b1",
                page_id="p1",
                type=BlockType.PARAGRAPH,
                layout=Layout(i="b1", x=0, y=1, w=1, h=2),
                content="First",
            ),
        ],
    )
    ordered = content.blocks_in_reading_order("p1")
    assert [block.id for block in ordered] == ["b1", "b2"]




