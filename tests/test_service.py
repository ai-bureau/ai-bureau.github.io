"""Tests for end-to-end publisher coordination without external APIs."""

import logging
from datetime import datetime

import pytest

from publisher.models import Article
from publisher.renderer import render_article
from publisher.service import PublisherService


class FakeNotion:
    """In-memory Notion port for service tests."""

    def __init__(self, articles: list[Article]) -> None:
        self.articles = articles
        self.marked: list[tuple[str, datetime]] = []

    def get_articles_to_publish(self) -> list[Article]:
        """Return configured test articles."""

        return self.articles

    def mark_published(self, page_id: str, published_at: datetime) -> None:
        """Record status updates."""

        self.marked.append((page_id, published_at))


class FakeGitHub:
    """In-memory GitHub port for service tests."""

    def __init__(
        self,
        files: dict[str, str] | None = None,
        fail_create: bool = False,
    ) -> None:
        self.files = files or {}
        self.created: list[str] = []
        self.fail_create = fail_create

    def get_file_content(self, path: str) -> str | None:
        """Return configured repository content."""

        return self.files.get(path)

    def create_file(self, path: str, content: str, message: str) -> None:
        """Create a file or simulate an API failure."""

        if self.fail_create:
            raise RuntimeError("GitHub unavailable")
        self.files[path] = content
        self.created.append(path)


def make_article(title: str = "Test Article") -> Article:
    """Create a valid article fixture."""

    return Article(
        notion_page_id="page-1",
        title=title,
        source_url="https://example.com",
        language="EN",
        summary="Summary.",
        added_at=datetime(2026, 6, 12),
        publish_at=datetime(2026, 6, 12),
        theses=("Thesis.",),
    )


def test_publish_creates_github_file_then_marks_notion() -> None:
    """Normal publication writes GitHub and updates Notion."""

    notion = FakeNotion([make_article()])
    github = FakeGitHub()
    clock = datetime(2026, 6, 13, 9, 0)

    count = PublisherService(
        notion,
        github,
        logging.getLogger("test"),
        now=lambda: clock,
    ).run()

    assert count == 1
    assert github.created == ["content/en/blog/test-article.md"]
    assert notion.marked == [("page-1", clock)]


def test_slug_collision_adds_numeric_suffix() -> None:
    """Different content at the preferred path produces a suffixed slug."""

    notion = FakeNotion([make_article()])
    github = FakeGitHub({"content/en/blog/test-article.md": "different"})

    PublisherService(notion, github, logging.getLogger("test")).run()

    assert github.created == ["content/en/blog/test-article-2.md"]


def test_identical_existing_file_repairs_notion_without_duplicate() -> None:
    """A prior GitHub success is recognized after a failed Notion update."""

    article = make_article()
    path = "content/en/blog/test-article.md"
    notion = FakeNotion([article])
    github = FakeGitHub({path: render_article(article)})

    PublisherService(notion, github, logging.getLogger("test")).run()

    assert github.created == []
    assert len(notion.marked) == 1


def test_github_failure_does_not_mark_notion() -> None:
    """Notion remains unchanged when GitHub cannot create the file."""

    notion = FakeNotion([make_article()])
    github = FakeGitHub(fail_create=True)

    service = PublisherService(notion, github, logging.getLogger("test"))
    count = service.run()

    assert count == 0
    assert notion.marked == []
    assert service.had_errors is True


def test_dry_run_writes_nothing() -> None:
    """Dry-run validates paths without external writes."""

    notion = FakeNotion([make_article()])
    github = FakeGitHub()

    count = PublisherService(
        notion,
        github,
        logging.getLogger("test"),
        dry_run=True,
    ).run()

    assert count == 1
    assert github.created == []
    assert notion.marked == []
