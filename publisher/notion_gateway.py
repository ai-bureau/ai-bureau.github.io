"""Read approved articles from Notion and mark successful publications.

Input: Notion data source rows and related thesis pages.
Output: validated ``Article`` objects and publication status updates.
"""

import logging
from datetime import datetime
from typing import Any

import requests

from publisher.http import RetryingHttpClient
from publisher.models import Article

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_API_VERSION = "2025-09-03"


class ArticleValidationError(ValueError):
    """Raised when a Notion article is missing required publication data."""


class NotionGateway:
    """Provide the Notion operations required by the publisher."""

    def __init__(
        self,
        token: str,
        data_source_id: str,
        max_retries: int,
        retry_pause_sec: float,
        logger: logging.Logger,
        session: requests.Session | None = None,
    ) -> None:
        """Initialize a Notion API gateway.

        Args:
            token: Notion integration token.
            data_source_id: Articles data source identifier.
            max_retries: Maximum attempts per external request.
            retry_pause_sec: Pause between transient failures.
            logger: Application logger.
            session: Optional injectable requests session.
        """

        api_session = session or requests.Session()
        api_session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Notion-Version": NOTION_API_VERSION,
                "Content-Type": "application/json",
            }
        )
        self._data_source_id = data_source_id
        self._logger = logger
        self._http = RetryingHttpClient(
            api_session, max_retries, retry_pause_sec, logger
        )

    def get_articles_to_publish(self) -> list[Article]:
        """Return all approved and not-yet-published articles.

        Returns:
            Validated articles ready for rendering.

        Raises:
            ArticleValidationError: If an approved row is incomplete.
        """

        articles: list[Article] = []
        for page in self._query_approved_pages():
            try:
                articles.append(self._parse_article(page))
            except ArticleValidationError as error:
                self._logger.warning("[SKIP] %s", error)
        return articles

    def mark_published(self, page_id: str, published_at: datetime) -> None:
        """Mark a Notion article as published.

        Args:
            page_id: Notion article page identifier.
            published_at: Actual publication timestamp.
        """

        payload = {
            "properties": {
                "Статус": {"select": {"name": "Опубліковано"}},
                "Опубліковано": {"date": {"start": published_at.isoformat()}},
            }
        }
        self._http.request(
            "PATCH",
            f"{NOTION_API_BASE}/pages/{page_id}",
            expected_statuses={200},
            json=payload,
        )

    def _query_approved_pages(self) -> list[dict[str, Any]]:
        """Query every approved page using Notion cursor pagination."""

        pages: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            payload: dict[str, Any] = {
                "page_size": 100,
                "filter": {
                    "and": [
                        {
                            "property": "Статус",
                            "select": {"equals": "Публікувати"},
                        },
                        {
                            "property": "Опубліковано",
                            "date": {"is_empty": True},
                        },
                    ]
                },
            }
            if cursor:
                payload["start_cursor"] = cursor
            response = self._http.request(
                "POST",
                f"{NOTION_API_BASE}/data_sources/{self._data_source_id}/query",
                expected_statuses={200},
                json=payload,
            ).json()
            pages.extend(response["results"])
            if not response.get("has_more"):
                return pages
            cursor = response.get("next_cursor")

    def _parse_article(self, page: dict[str, Any]) -> Article:
        """Convert one Notion page response into a validated article."""

        properties = page.get("properties", {})
        title = _rich_text_value(properties.get("Заголовок", {}), "title")
        source_url = properties.get("URL", {}).get("url")
        language = _select_value(properties.get("Мова", {}))
        summary = _rich_text_value(properties.get("Саммари", {}), "rich_text")
        added_at = _date_value(properties.get("Дата додавання", {}))
        publish_at = _date_value(properties.get("Дата публікації", {})) or added_at
        relation_ids = [
            relation["id"]
            for relation in properties.get("Тезиси", {}).get("relation", [])
            if relation.get("id")
        ]

        missing = [
            name
            for name, value in (
                ("Заголовок", title),
                ("URL", source_url),
                ("Мова", language),
                ("Саммари", summary),
                ("Дата додавання", added_at),
            )
            if not value
        ]
        if missing:
            raise ArticleValidationError(
                f"Notion page {page.get('id')} is missing: {', '.join(missing)}"
            )
        if language not in {"UA", "EN"}:
            raise ArticleValidationError(
                f"Notion page {page.get('id')} has unsupported language: {language}"
            )

        theses = tuple(self._retrieve_page_title(page_id) for page_id in relation_ids)
        return Article(
            notion_page_id=page["id"],
            title=title,
            source_url=source_url,
            language=language,
            summary=summary,
            added_at=added_at,
            publish_at=publish_at,
            theses=theses,
        )

    def _retrieve_page_title(self, page_id: str) -> str:
        """Retrieve the title value from a related Notion page."""

        page = self._http.request(
            "GET",
            f"{NOTION_API_BASE}/pages/{page_id}",
            expected_statuses={200},
        ).json()
        for property_value in page.get("properties", {}).values():
            if property_value.get("type") == "title":
                return _rich_text_value(property_value, "title")
        return page_id


def _rich_text_value(property_value: dict[str, Any], key: str) -> str:
    """Join plain text fragments from a Notion rich-text property."""

    return "".join(
        item.get("plain_text", "") for item in property_value.get(key, [])
    ).strip()


def _select_value(property_value: dict[str, Any]) -> str | None:
    """Extract the selected option name from a Notion select property."""

    selected = property_value.get("select")
    return selected.get("name") if selected else None


def _date_value(property_value: dict[str, Any]) -> datetime | None:
    """Parse a Notion date property, accepting dates and datetimes."""

    date_value = property_value.get("date")
    if not date_value or not date_value.get("start"):
        return None
    iso_value = date_value["start"].replace("Z", "+00:00")
    return datetime.fromisoformat(iso_value)
