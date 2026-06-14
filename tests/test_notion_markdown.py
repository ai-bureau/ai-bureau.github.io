"""Tests for publication-safe Notion block rendering."""

import pytest

from publisher.notion_markdown import UnsupportedNotionBlockError, render_blocks


def test_render_blocks_preserves_links_annotations_and_lists() -> None:
    """Supported rich text and adjacent list items become Markdown."""

    blocks = [
        {
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "plain_text": "Source",
                        "href": "https://example.com",
                        "annotations": {"bold": True},
                    }
                ]
            },
        },
        {
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"plain_text": "One", "annotations": {}}]},
        },
        {
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"plain_text": "Two", "annotations": {}}]},
        },
    ]

    assert render_blocks(blocks) == "[**Source**](https://example.com)\n\n- One\n- Two"


def test_render_blocks_rejects_unsupported_content() -> None:
    """Unsupported blocks raise rather than disappearing."""

    with pytest.raises(UnsupportedNotionBlockError):
        render_blocks([{"type": "image", "image": {}}])
