"""Convert supported Notion blocks into publication-safe Markdown.

Input: expanded Notion block dictionaries.
Output: Markdown or an explicit validation error for unsupported content.
"""

from typing import Any


class UnsupportedNotionBlockError(ValueError):
    """Raised when a Notion block cannot be published without data loss."""


def render_blocks(blocks: list[dict[str, Any]]) -> str:
    """Render a sequence of supported Notion blocks as Markdown.

    Args:
        blocks: Top-level blocks with optional expanded ``_children`` lists.

    Returns:
        Markdown body with stable spacing.
    """

    rendered: list[str] = []
    previous_list_type: str | None = None
    for block in blocks:
        block_type = block.get("type", "")
        current_list_type = block_type if block_type in _LIST_TYPES else None
        text = _render_block(block)
        if not text:
            continue
        separator = "\n" if current_list_type == previous_list_type else "\n\n"
        if rendered:
            rendered.append(separator)
        rendered.append(text)
        previous_list_type = current_list_type
    return "".join(rendered).strip()


_LIST_TYPES = {"bulleted_list_item", "numbered_list_item"}


def _render_block(block: dict[str, Any]) -> str:
    """Render one supported block and its children."""

    block_type = block.get("type", "")
    value = block.get(block_type, {})
    rich_text = value.get("rich_text", [])
    text = _render_rich_text(rich_text)

    if block_type == "paragraph":
        rendered = text
    elif block_type == "heading_2":
        rendered = f"## {text}"
    elif block_type == "heading_3":
        rendered = f"### {text}"
    elif block_type == "bulleted_list_item":
        rendered = f"- {text}"
    elif block_type == "numbered_list_item":
        rendered = f"1. {text}"
    elif block_type == "quote":
        rendered = "\n".join(f"> {line}" for line in text.splitlines())
    elif block_type == "code":
        language = value.get("language", "")
        rendered = f"```{language}\n{text}\n```"
    elif block_type == "divider":
        rendered = "---"
    else:
        raise UnsupportedNotionBlockError(f"unsupported Notion block: {block_type}")

    children = block.get("_children", [])
    if children:
        child_markdown = render_blocks(children)
        if block_type in _LIST_TYPES:
            child_markdown = "\n".join(f"  {line}" for line in child_markdown.splitlines())
        rendered = f"{rendered}\n{child_markdown}"
    return rendered


def _render_rich_text(items: list[dict[str, Any]]) -> str:
    """Render Notion rich text spans while preserving basic annotations."""

    parts: list[str] = []
    for item in items:
        text = item.get("plain_text", "")
        annotations = item.get("annotations", {})
        if annotations.get("code"):
            text = f"`{text}`"
        if annotations.get("bold"):
            text = f"**{text}**"
        if annotations.get("italic"):
            text = f"*{text}*"
        if annotations.get("strikethrough"):
            text = f"~~{text}~~"
        link = item.get("href") or item.get("text", {}).get("link", {}).get("url")
        if link:
            text = f"[{text}]({link})"
        parts.append(text)
    return "".join(parts)
