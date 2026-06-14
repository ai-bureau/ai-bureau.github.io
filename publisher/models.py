"""Domain models used by the AI Bureau bilingual publication publisher.

Input: validated publication values read from Notion.
Output: immutable publication, language version, and result objects.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ArticleVersion:
    """Represent one ready-to-publish language version.

    Args:
        language: Site language code, either ``UA`` or ``EN``.
        title: Public article title.
        description: Short description used by Hugo and search engines.
        body: Complete Markdown body without front matter.
    """

    language: str
    title: str
    description: str
    body: str


@dataclass(frozen=True)
class Publication:
    """Represent one approved bilingual Notion publication.

    Args:
        notion_page_id: Notion page identifier used when updating status.
        name: Internal working name used in logs and commit messages.
        slug: Stable URL slug shared by both language versions.
        publish_at: Date and optional time when Hugo may show the article.
        theses: Human-readable related thesis titles.
        ua: Final Ukrainian version.
        en: Final English version.
    """

    notion_page_id: str
    name: str
    slug: str
    publish_at: datetime
    theses: tuple[str, ...]
    ua: ArticleVersion
    en: ArticleVersion


@dataclass(frozen=True)
class PublicationResult:
    """Describe repository paths selected for a bilingual publication.

    Args:
        paths: Repository-relative Markdown paths.
        already_exists: Whether both identical files were already committed.
    """

    paths: tuple[str, str]
    already_exists: bool
