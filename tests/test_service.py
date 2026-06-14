"""Tests for bilingual publisher coordination without external APIs."""

import logging
from datetime import datetime

import pytest

from publisher.models import ArticleVersion, Publication
from publisher.renderer import render_article
from publisher.service import PublisherService


class FakeNotion:
    """In-memory Notion port for service tests."""

    def __init__(self, publications: list[Publication]) -> None:
        self.publications = publications
        self.marked: list[tuple[str, datetime]] = []

    def get_publications_to_publish(self) -> list[Publication]:
        """Return configured test publications."""

        return self.publications

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
        self.commits: list[dict[str, str]] = []
        self.fail_create = fail_create

    def get_file_content(self, path: str) -> str | None:
        """Return configured repository content."""

        return self.files.get(path)

    def create_files(self, files: dict[str, str], message: str) -> None:
        """Create files atomically or simulate an API failure."""

        if self.fail_create:
            raise RuntimeError("GitHub unavailable")
        self.files.update(files)
        self.commits.append(files)


def make_publication() -> Publication:
    """Create a valid bilingual publication fixture."""

    return Publication(
        notion_page_id="page-1",
        name="Test Article",
        slug="test-article",
        publish_at=datetime(2026, 6, 12),
        theses=("Thesis.",),
        ua=ArticleVersion("UA", "Тестова стаття", "Короткий опис.", "Повний текст."),
        en=ArticleVersion("EN", "Test Article", "Short description.", "Full text."),
    )


def test_publish_creates_both_files_in_one_commit_then_marks_notion() -> None:
    """Normal publication commits both versions before updating Notion."""

    notion = FakeNotion([make_publication()])
    github = FakeGitHub()
    clock = datetime(2026, 6, 13, 9, 0)

    count = PublisherService(
        notion,
        github,
        logging.getLogger("test"),
        now=lambda: clock,
    ).run()

    assert count == 1
    assert len(github.commits) == 1
    assert set(github.commits[0]) == {
        "content/uk/blog/test-article.md",
        "content/en/blog/test-article.md",
    }
    assert notion.marked == [("page-1", clock)]


def test_different_existing_content_stops_publication() -> None:
    """A stable slug collision does not silently create a different URL."""

    notion = FakeNotion([make_publication()])
    github = FakeGitHub({"content/en/blog/test-article.md": "different"})

    service = PublisherService(notion, github, logging.getLogger("test"))
    count = service.run()

    assert count == 0
    assert github.commits == []
    assert notion.marked == []
    assert service.had_errors is True


def test_identical_existing_files_repair_notion_without_duplicate() -> None:
    """A prior GitHub success is recognized after a failed Notion update."""

    publication = make_publication()
    files = {
        "content/uk/blog/test-article.md": render_article(publication, publication.ua),
        "content/en/blog/test-article.md": render_article(publication, publication.en),
    }
    notion = FakeNotion([publication])
    github = FakeGitHub(files)

    PublisherService(notion, github, logging.getLogger("test")).run()

    assert github.commits == []
    assert len(notion.marked) == 1


def test_github_failure_does_not_mark_notion() -> None:
    """Notion remains unchanged when GitHub cannot create the commit."""

    notion = FakeNotion([make_publication()])
    github = FakeGitHub(fail_create=True)

    service = PublisherService(notion, github, logging.getLogger("test"))
    count = service.run()

    assert count == 0
    assert notion.marked == []
    assert service.had_errors is True


def test_dry_run_writes_nothing_and_reports_both_paths(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Dry-run validates both paths without external writes."""

    notion = FakeNotion([make_publication()])
    github = FakeGitHub()

    with caplog.at_level(logging.INFO):
        count = PublisherService(
            notion,
            github,
            logging.getLogger("test"),
            dry_run=True,
        ).run()

    assert count == 1
    assert github.commits == []
    assert notion.marked == []
    assert "content/uk/blog/test-article.md" in caplog.text
    assert "content/en/blog/test-article.md" in caplog.text
    assert "[OK] published" not in caplog.text
