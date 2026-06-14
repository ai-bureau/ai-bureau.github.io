"""Tests for bilingual Hugo Markdown rendering."""

from datetime import datetime, timezone

import yaml

from publisher.models import ArticleVersion, Publication
from publisher.renderer import render_article


def test_render_article_contains_translation_metadata_and_full_body() -> None:
    """Rendered Markdown preserves the supplied body and shared translation key."""

    publication = Publication(
        notion_page_id="page-1",
        name="Verified AI",
        slug="verified-ai",
        publish_at=datetime(2026, 6, 15, 10, 0, tzinfo=timezone.utc),
        theses=("AI output must be verifiable.",),
        ua=ArticleVersion("UA", "Перевірений AI", "Опис статті.", "Текст."),
        en=ArticleVersion("EN", "Verified AI", "Article description.", "Full **body**."),
    )

    rendered = render_article(publication, publication.en)
    _, yaml_text, body = rendered.split("---", maxsplit=2)
    metadata = yaml.safe_load(yaml_text)

    assert metadata["publishDate"] == "2026-06-15T10:00:00+00:00"
    assert metadata["translationKey"] == "verified-ai"
    assert metadata["thesis"] == "AI output must be verifiable."
    assert "sourceURL" not in metadata
    assert body.strip() == "Full **body**."
