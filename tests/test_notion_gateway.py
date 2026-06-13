"""Tests for parsing and validating Notion API article responses."""

import logging

from publisher.notion_gateway import NotionGateway


class JsonResponse:
    """Minimal HTTP response returning a configured JSON object."""

    status_code = 200
    headers: dict[str, str] = {}
    text = ""

    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def json(self) -> dict[str, object]:
        """Return the configured payload."""

        return self.payload


class SequenceSession:
    """Return Notion API responses in request order."""

    def __init__(self, payloads: list[dict[str, object]]) -> None:
        self.headers: dict[str, str] = {}
        self.responses = [JsonResponse(payload) for payload in payloads]
        self.requests: list[tuple[str, str, dict[str, object]]] = []

    def request(self, method: str, url: str, timeout: int, **kwargs: object) -> JsonResponse:
        """Record a request and return the next response."""

        self.requests.append((method, url, kwargs))
        return self.responses.pop(0)


def rich_text(value: str) -> list[dict[str, str]]:
    """Create a minimal Notion rich-text value."""

    return [{"plain_text": value}]


def test_gateway_queries_and_parses_article_with_related_thesis() -> None:
    """Gateway converts current Notion data source responses into an article."""

    article_page = {
        "id": "article-1",
        "properties": {
            "Заголовок": {"title": rich_text("Article")},
            "URL": {"url": "https://example.com"},
            "Мова": {"select": {"name": "EN"}},
            "Саммари": {"rich_text": rich_text("Summary")},
            "Дата додавання": {"date": {"start": "2026-06-12"}},
            "Дата публікації": {"date": None},
            "Тезиси": {"relation": [{"id": "thesis-1"}]},
        },
    }
    thesis_page = {
        "properties": {
            "Тезис": {"type": "title", "title": rich_text("Related thesis")}
        }
    }
    session = SequenceSession(
        [
            {"results": [article_page], "has_more": False},
            thesis_page,
        ]
    )
    gateway = NotionGateway(
        "token",
        "data-source",
        max_retries=1,
        retry_pause_sec=0,
        logger=logging.getLogger("test"),
        session=session,  # type: ignore[arg-type]
    )

    articles = gateway.get_articles_to_publish()

    assert len(articles) == 1
    assert articles[0].publish_at.isoformat() == "2026-06-12T00:00:00"
    assert articles[0].theses == ("Related thesis",)
    query_payload = session.requests[0][2]["json"]
    assert query_payload["filter"]["and"][0]["select"]["equals"] == "Публікувати"

