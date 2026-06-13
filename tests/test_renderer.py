"""Tests for Hugo Markdown rendering."""

from datetime import datetime, timezone

import yaml

from publisher.models import Article
from publisher.renderer import render_article


def test_render_article_contains_site_metadata_and_summary() -> None:
    """Rendered Markdown matches the custom AI Bureau article template."""

    article = Article(
        notion_page_id="page-1",
        title="Verified AI",
        source_url="https://example.com/article",
        language="EN",
        summary="A concise summary.",
        added_at=datetime(2026, 6, 12),
        publish_at=datetime(2026, 6, 15, 10, 0, tzinfo=timezone.utc),
        theses=("AI output must be verifiable.",),
    )

    rendered = render_article(article)
    _, yaml_text, body = rendered.split("---", maxsplit=2)
    metadata = yaml.safe_load(yaml_text)

    assert metadata["publishDate"] == "2026-06-15T10:00:00+00:00"
    assert metadata["sourceURL"] == "https://example.com/article"
    assert metadata["thesis"] == "AI output must be verifiable."
    assert "**AI Bureau summary:** A concise summary." in body

