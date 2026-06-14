"""Tests for parsing and validating bilingual Notion publications."""

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


def rich_text(value: str) -> list[dict[str, object]]:
    """Create a minimal Notion rich-text value."""

    return [{"plain_text": value, "annotations": {}}]


def block(block_type: str, value: str = "") -> dict[str, object]:
    """Create a minimal Notion block."""

    return {
        "id": f"{block_type}-{value}",
        "type": block_type,
        block_type: {"rich_text": rich_text(value)},
        "has_children": False,
    }


def publication_page(slug: str = "hands-for-ai") -> dict[str, object]:
    """Create a valid publication row."""

    return {
        "id": "publication-1",
        "properties": {
            "Назва": {"title": rich_text("AI has hands")},
            "Slug": {"rich_text": rich_text(slug)},
            "Заголовок UA": {"rich_text": rich_text("У машин з'явилися руки")},
            "Заголовок EN": {"rich_text": rich_text("Machines have hands")},
            "Опис UA": {"rich_text": rich_text("Що тепер можна делегувати машині.")},
            "Опис EN": {"rich_text": rich_text("What can now be delegated to machines.")},
            "Дата публікації": {"date": {"start": "2026-06-14"}},
            "Тезиси": {"relation": [{"id": "thesis-1"}]},
        },
    }


def valid_blocks() -> dict[str, object]:
    """Create valid UA and EN page sections."""

    return {
        "results": [
            block("heading_1", "UA"),
            block("paragraph", "Машині можна делегувати рутину."),
            block("heading_2", "Безпека"),
            block("paragraph", "Результат треба перевіряти."),
            block("heading_1", "EN"),
            block("paragraph", "Routine can be delegated to a machine."),
        ],
        "has_more": False,
    }


def make_gateway(payloads: list[dict[str, object]]) -> tuple[NotionGateway, SequenceSession]:
    """Create a gateway backed by ordered fake responses."""

    session = SequenceSession(payloads)
    gateway = NotionGateway(
        "token",
        "data-source",
        max_retries=1,
        retry_pause_sec=0,
        logger=logging.getLogger("test"),
        session=session,  # type: ignore[arg-type]
    )
    return gateway, session


def test_gateway_queries_and_parses_bilingual_publication() -> None:
    """Gateway reads properties, page sections, and a related thesis."""

    thesis_page = {
        "properties": {
            "Тезис": {"type": "title", "title": rich_text("Related thesis")}
        }
    }
    gateway, session = make_gateway(
        [
            {"results": [publication_page()], "has_more": False},
            valid_blocks(),
            thesis_page,
        ]
    )

    publications = gateway.get_publications_to_publish()

    assert len(publications) == 1
    assert publications[0].slug == "hands-for-ai"
    assert publications[0].theses == ("Related thesis",)
    assert "## Безпека" in publications[0].ua.body
    assert publications[0].en.body == "Routine can be delegated to a machine."
    query_payload = session.requests[0][2]["json"]
    assert query_payload["filter"]["and"][0]["select"]["equals"] == "Публікувати"


def test_gateway_skips_invalid_slug(caplog: object) -> None:
    """An invalid stable slug prevents publication."""

    gateway, _ = make_gateway(
        [{"results": [publication_page("Invalid Slug")], "has_more": False}]
    )

    assert gateway.get_publications_to_publish() == []


def test_gateway_skips_missing_language_section() -> None:
    """Both exact language sections are mandatory."""

    gateway, _ = make_gateway(
        [
            {"results": [publication_page()], "has_more": False},
            {
                "results": [
                    block("heading_1", "UA"),
                    block("paragraph", "Український текст."),
                ],
                "has_more": False,
            },
        ]
    )

    assert gateway.get_publications_to_publish() == []


def test_gateway_skips_reversed_language_sections() -> None:
    """The stable page contract requires UA before EN."""

    gateway, _ = make_gateway(
        [
            {"results": [publication_page()], "has_more": False},
            {
                "results": [
                    block("heading_1", "EN"),
                    block("paragraph", "English text."),
                    block("heading_1", "UA"),
                    block("paragraph", "Український текст."),
                ],
                "has_more": False,
            },
        ]
    )

    assert gateway.get_publications_to_publish() == []


def test_gateway_skips_unsupported_block() -> None:
    """Unknown Notion blocks stop publication instead of losing content."""

    blocks = valid_blocks()
    blocks["results"].insert(2, block("table", "data"))  # type: ignore[union-attr]
    gateway, _ = make_gateway(
        [{"results": [publication_page()], "has_more": False}, blocks]
    )

    assert gateway.get_publications_to_publish() == []
