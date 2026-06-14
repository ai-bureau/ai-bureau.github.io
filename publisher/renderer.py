"""Render validated bilingual publications as Hugo-compatible Markdown.

Input: ``Publication`` and ``ArticleVersion`` objects.
Output: deterministic UTF-8 Markdown strings.
"""

from datetime import datetime

import yaml

from publisher.models import ArticleVersion, Publication


def render_article(publication: Publication, version: ArticleVersion) -> str:
    """Render one language version with shared translation metadata.

    Args:
        publication: Shared publication metadata.
        version: Final language-specific title, description, and body.

    Returns:
        Complete Markdown document with YAML front matter.
    """

    front_matter = {
        "title": version.title,
        "description": version.description,
        "date": _format_datetime(publication.publish_at),
        "publishDate": _format_datetime(publication.publish_at),
        "translationKey": publication.slug,
        "thesis": " ".join(publication.theses),
        "draft": False,
    }
    yaml_text = yaml.safe_dump(
        front_matter,
        allow_unicode=True,
        sort_keys=False,
        width=1000,
    ).strip()
    return f"---\n{yaml_text}\n---\n\n{version.body.strip()}\n"


def _format_datetime(value: datetime) -> str:
    """Format a date or datetime without losing a supplied timezone."""

    if value.time() == datetime.min.time() and value.tzinfo is None:
        return value.date().isoformat()
    return value.isoformat()
