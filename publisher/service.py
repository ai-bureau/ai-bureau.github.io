"""Coordinate article validation, rendering, GitHub publishing, and Notion updates.

Input: Notion and GitHub gateways.
Output: one completed publication pass.
"""

import logging
from datetime import datetime
from collections.abc import Callable
from typing import Protocol

from publisher.models import Article, PublicationResult
from publisher.renderer import render_article
from publisher.slug import generate_slug


class NotionPort(Protocol):
    """Describe Notion operations consumed by the publishing service."""

    def get_articles_to_publish(self) -> list[Article]:
        """Return articles approved for publication."""

    def mark_published(self, page_id: str, published_at: datetime) -> None:
        """Mark an article as published."""


class GitHubPort(Protocol):
    """Describe GitHub operations consumed by the publishing service."""

    def get_file_content(self, path: str) -> str | None:
        """Return existing content or ``None``."""

    def create_file(self, path: str, content: str, message: str) -> None:
        """Create and commit a file."""


class PublisherService:
    """Publish every currently approved Notion article once."""

    def __init__(
        self,
        notion: NotionPort,
        github: GitHubPort,
        logger: logging.Logger,
        *,
        dry_run: bool = False,
        now: Callable[[], datetime] = datetime.now,
    ) -> None:
        """Initialize the publication coordinator.

        Args:
            notion: Notion gateway.
            github: GitHub gateway.
            logger: Application logger.
            dry_run: If true, do not write to GitHub or Notion.
            now: Injectable clock used by tests.
        """

        self._notion = notion
        self._github = github
        self._logger = logger
        self._dry_run = dry_run
        self._now = now
        self.had_errors = False

    def run(self) -> int:
        """Execute one publication pass.

        Returns:
            Number of articles processed successfully.
        """

        articles = self._notion.get_articles_to_publish()
        if not articles:
            self._logger.info("Нових статей для публікації немає")
            return 0

        published_count = 0
        for article in articles:
            try:
                result = self._publish_article(article)
                published_count += 1
                action = "already exists" if result.already_exists else "published"
                self._logger.info(
                    "[OK] %s: %s -> %s", action, article.title, result.path
                )
            except Exception:
                self.had_errors = True
                self._logger.exception("[ERROR] Не вдалося опублікувати: %s", article.title)
        self._logger.info(
            "Публікацію завершено: %d з %d статей", published_count, len(articles)
        )
        return published_count

    def _publish_article(self, article: Article) -> PublicationResult:
        """Publish one article and update Notion after GitHub succeeds."""

        content = render_article(article)
        result = self._select_path(article, content)
        if self._dry_run:
            self._logger.info("[DRY RUN] %s -> %s", article.title, result.path)
            return result

        if not result.already_exists:
            self._github.create_file(
                result.path,
                content,
                f"Publish article: {article.title}",
            )
        self._notion.mark_published(article.notion_page_id, self._now())
        return result

    def _select_path(self, article: Article, content: str) -> PublicationResult:
        """Find an unused path or recognize an identical previous commit."""

        directory = "content/uk/blog" if article.language == "UA" else "content/en/blog"
        base_slug = generate_slug(article.title)
        suffix = 1
        while True:
            slug = base_slug if suffix == 1 else f"{base_slug}-{suffix}"
            path = f"{directory}/{slug}.md"
            existing_content = self._github.get_file_content(path)
            if existing_content is None:
                return PublicationResult(path=path, already_exists=False)
            if existing_content == content:
                return PublicationResult(path=path, already_exists=True)
            self._logger.warning("[WARN] Slug already exists: %s", path)
            suffix += 1
