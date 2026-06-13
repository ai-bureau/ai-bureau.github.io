"""Render validated articles as Hugo-compatible Markdown.

Input: ``Article`` objects.
Output: deterministic UTF-8 Markdown strings.
"""

from datetime import datetime

import yaml

from publisher.models import Article


def render_article(article: Article) -> str:
    """Render one article for the current AI Bureau Hugo templates.

    Args:
        article: Validated source article.

    Returns:
        Complete Markdown document with YAML front matter.
    """

    thesis = " ".join(article.theses)
    front_matter = {
        "title": article.title,
        "description": article.summary,
        "date": _format_datetime(article.added_at),
        "publishDate": _format_datetime(article.publish_at),
        "sourceName": article.title,
        "sourceURL": article.source_url,
        "thesis": thesis,
        "draft": False,
    }
    yaml_text = yaml.safe_dump(
        front_matter,
        allow_unicode=True,
        sort_keys=False,
        width=1000,
    ).strip()
    body_label = "Саммарі AI Bureau" if article.language == "UA" else "AI Bureau summary"
    return f"---\n{yaml_text}\n---\n\n**{body_label}:** {article.summary}\n"


def _format_datetime(value: datetime) -> str:
    """Format a date or datetime without losing a supplied timezone."""

    if value.time() == datetime.min.time() and value.tzinfo is None:
        return value.date().isoformat()
    return value.isoformat()

