"""Coordinate bilingual rendering, GitHub publishing, and Notion updates.

Input: Notion and GitHub gateways.
Output: one completed publication pass.
"""

import logging
from collections.abc import Callable
from datetime import datetime
from typing import Protocol

from publisher.models import Publication, PublicationResult
from publisher.renderer import render_article


class NotionPort(Protocol):
    """Describe Notion operations consumed by the publishing service."""

    def get_publications_to_publish(self) -> list[Publication]:
        """Return bilingual publications approved by the owner."""

    def mark_published(self, page_id: str, published_at: datetime) -> None:
        """Mark a publication as published."""


class GitHubPort(Protocol):
    """Describe GitHub operations consumed by the publishing service."""

    def get_file_content(self, path: str) -> str | None:
        """Return existing content or ``None``."""

    def create_files(self, files: dict[str, str], message: str) -> None:
        """Create multiple files in one commit."""


class PublisherService:
    """Publish every currently approved bilingual Notion publication once."""

    def __init__(
        self,
        notion: NotionPort,
        github: GitHubPort,
        logger: logging.Logger,
        *,
        dry_run: bool = False,
        now: Callable[[], datetime] = datetime.now,
    ) -> None:
        """Initialize the publication coordinator."""

        self._notion = notion
        self._github = github
        self._logger = logger
        self._dry_run = dry_run
        self._now = now
        self.had_errors = False

    def run(self) -> int:
        """Execute one publication pass and return the successful count."""

        publications = self._notion.get_publications_to_publish()
        if not publications:
            self._logger.info("Нових публікацій немає")
            return 0

        published_count = 0
        for publication in publications:
            try:
                result = self._publish(publication)
                published_count += 1
                if self._dry_run:
                    continue
                action = "already exists" if result.already_exists else "published"
                self._logger.info(
                    "[OK] %s: %s -> %s",
                    action,
                    publication.name,
                    ", ".join(result.paths),
                )
            except Exception:
                self.had_errors = True
                self._logger.exception(
                    "[ERROR] Не вдалося опублікувати: %s", publication.name
                )
        self._logger.info(
            "Публікацію завершено: %d з %d матеріалів",
            published_count,
            len(publications),
        )
        return published_count

    def _publish(self, publication: Publication) -> PublicationResult:
        """Publish both language versions before updating Notion."""

        paths = (
            f"content/uk/blog/{publication.slug}.md",
            f"content/en/blog/{publication.slug}.md",
        )
        expected = {
            paths[0]: render_article(publication, publication.ua),
            paths[1]: render_article(publication, publication.en),
        }
        missing: dict[str, str] = {}
        for path, content in expected.items():
            existing = self._github.get_file_content(path)
            if existing is None:
                missing[path] = content
            elif existing != content:
                raise ValueError(f"publication path already contains different content: {path}")

        result = PublicationResult(paths=paths, already_exists=not missing)
        if self._dry_run:
            self._logger.info("[DRY RUN] %s -> %s", publication.name, ", ".join(paths))
            return result

        if missing:
            self._github.create_files(missing, f"Publish article: {publication.name}")
        self._notion.mark_published(publication.notion_page_id, self._now())
        return result
