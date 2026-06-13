"""Domain models used by the AI Bureau article publisher.

Input: validated values read from Notion.
Output: immutable article and publication result objects.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Article:
    """Represent one approved article ready for publication.

    Args:
        notion_page_id: Notion page identifier used when updating status.
        title: Public article title.
        source_url: URL of the original article.
        language: Notion language option, either ``UA`` or ``EN``.
        summary: AI Bureau summary shown on the website.
        added_at: Date the article was added to Notion.
        publish_at: Date and optional time when Hugo may show the article.
        theses: Human-readable related thesis titles.
    """

    notion_page_id: str
    title: str
    source_url: str
    language: str
    summary: str
    added_at: datetime
    publish_at: datetime
    theses: tuple[str, ...]


@dataclass(frozen=True)
class PublicationResult:
    """Describe the GitHub path selected for an article.

    Args:
        path: Repository-relative Markdown path.
        already_exists: Whether identical content was already committed.
    """

    path: str
    already_exists: bool

