"""Read approved bilingual publications from Notion and update their status.

Input: publication data source rows, page blocks, and related thesis pages.
Output: validated ``Publication`` objects and publication status updates.
"""

import logging
import re
from datetime import datetime
from typing import Any

import requests

from publisher.http import RetryingHttpClient
from publisher.models import ArticleVersion, Publication
from publisher.notion_markdown import UnsupportedNotionBlockError, render_blocks

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_API_VERSION = "2025-09-03"
VALID_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CYRILLIC = re.compile(r"[А-Яа-яІіЇїЄєҐґ]")
UKRAINIAN_SPECIFIC = re.compile(r"[ІіЇїЄєҐґ]")
LETTER = re.compile(r"[A-Za-zА-Яа-яІіЇїЄєҐґ]")


class PublicationValidationError(ValueError):
    """Raised when a Notion publication is not safe to publish."""


class NotionGateway:
    """Provide Notion operations required by the bilingual publisher."""

    def __init__(
        self,
        token: str,
        data_source_id: str,
        max_retries: int,
        retry_pause_sec: float,
        logger: logging.Logger,
        session: requests.Session | None = None,
    ) -> None:
        """Initialize a Notion API gateway."""

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

    def get_publications_to_publish(self) -> list[Publication]:
        """Return all approved, unpublished, and valid bilingual publications."""

        publications: list[Publication] = []
        for page in self._query_approved_pages():
            try:
                publications.append(self._parse_publication(page))
            except PublicationValidationError as error:
                self._logger.warning("[SKIP] %s", error)
        return publications

    def mark_published(self, page_id: str, published_at: datetime) -> None:
        """Mark a Notion publication as successfully published."""

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
                        {"property": "Статус", "select": {"equals": "Публікувати"}},
                        {"property": "Опубліковано", "date": {"is_empty": True}},
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

    def _parse_publication(self, page: dict[str, Any]) -> Publication:
        """Convert one Notion page and its blocks into a validated publication."""

        properties = page.get("properties", {})
        page_id = page.get("id", "")
        name = _rich_text_value(properties.get("Назва", {}), "title")
        slug = _rich_text_value(properties.get("Slug", {}), "rich_text")
        title_ua = _rich_text_value(properties.get("Заголовок UA", {}), "rich_text")
        title_en = _rich_text_value(properties.get("Заголовок EN", {}), "rich_text")
        description_ua = _rich_text_value(properties.get("Опис UA", {}), "rich_text")
        description_en = _rich_text_value(properties.get("Опис EN", {}), "rich_text")
        publish_at = _date_value(properties.get("Дата публікації", {}))

        missing = [
            property_name
            for property_name, value in (
                ("Назва", name),
                ("Slug", slug),
                ("Заголовок UA", title_ua),
                ("Заголовок EN", title_en),
                ("Опис UA", description_ua),
                ("Опис EN", description_en),
                ("Дата публікації", publish_at),
            )
            if not value
        ]
        if missing:
            raise PublicationValidationError(
                f"Notion page {page_id} is missing: {', '.join(missing)}"
            )
        if not VALID_SLUG.fullmatch(slug):
            raise PublicationValidationError(
                f"Notion page {page_id} has invalid Slug: {slug}"
            )

        try:
            bodies = self._read_language_bodies(page_id)
        except UnsupportedNotionBlockError as error:
            raise PublicationValidationError(f"Notion page {page_id}: {error}") from error
        self._validate_languages(
            page_id,
            title_ua,
            description_ua,
            bodies["UA"],
            title_en,
            description_en,
            bodies["EN"],
        )

        relation_ids = [
            relation["id"]
            for relation in properties.get("Тезиси", {}).get("relation", [])
            if relation.get("id")
        ]
        theses = tuple(self._retrieve_page_title(relation_id) for relation_id in relation_ids)
        return Publication(
            notion_page_id=page_id,
            name=name,
            slug=slug,
            publish_at=publish_at,
            theses=theses,
            ua=ArticleVersion("UA", title_ua, description_ua, bodies["UA"]),
            en=ArticleVersion("EN", title_en, description_en, bodies["EN"]),
        )

    def _read_language_bodies(self, page_id: str) -> dict[str, str]:
        """Read page blocks and split them at exact ``# UA`` and ``# EN`` markers."""

        sections: dict[str, list[dict[str, Any]]] = {"UA": [], "EN": []}
        current_language: str | None = None
        seen: set[str] = set()
        expected_markers = iter(("UA", "EN"))
        expected_marker = next(expected_markers)
        for block in self._retrieve_block_children(page_id):
            if block.get("type") == "heading_1":
                marker = _rich_text_value(block["heading_1"], "rich_text")
                if marker != expected_marker:
                    raise PublicationValidationError(
                        f"Notion page {page_id} expected # {expected_marker}, got # {marker}"
                    )
                current_language = marker
                seen.add(marker)
                expected_marker = next(expected_markers, "")
                continue
            if current_language is None:
                if block.get("type") != "paragraph" or _block_has_text(block):
                    raise PublicationValidationError(
                        f"Notion page {page_id} has content before # UA"
                    )
                continue
            sections[current_language].append(block)

        if seen != {"UA", "EN"}:
            raise PublicationValidationError(
                f"Notion page {page_id} must contain exact # UA and # EN sections"
            )
        rendered = {language: render_blocks(blocks) for language, blocks in sections.items()}
        empty = [language for language, body in rendered.items() if not body]
        if empty:
            raise PublicationValidationError(
                f"Notion page {page_id} has empty sections: {', '.join(empty)}"
            )
        return rendered

    def _retrieve_block_children(self, block_id: str) -> list[dict[str, Any]]:
        """Retrieve and recursively expand all direct children of a Notion block."""

        blocks: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            params: dict[str, Any] = {"page_size": 100}
            if cursor:
                params["start_cursor"] = cursor
            response = self._http.request(
                "GET",
                f"{NOTION_API_BASE}/blocks/{block_id}/children",
                expected_statuses={200},
                params=params,
            ).json()
            for block in response["results"]:
                if block.get("has_children"):
                    block["_children"] = self._retrieve_block_children(block["id"])
                blocks.append(block)
            if not response.get("has_more"):
                return blocks
            cursor = response.get("next_cursor")

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

    @staticmethod
    def _validate_languages(
        page_id: str,
        title_ua: str,
        description_ua: str,
        body_ua: str,
        title_en: str,
        description_en: str,
        body_en: str,
    ) -> None:
        """Reject obvious language mismatches before publishing."""

        if not UKRAINIAN_SPECIFIC.search(f"{title_ua} {description_ua} {body_ua}"):
            raise PublicationValidationError(
                f"Notion page {page_id} UA version does not look Ukrainian"
            )
        english_text = f"{title_en} {description_en} {body_en}"
        if _character_ratio(english_text, CYRILLIC) > 0.1:
            raise PublicationValidationError(
                f"Notion page {page_id} EN version contains too much Cyrillic text"
            )


def _rich_text_value(property_value: dict[str, Any], key: str) -> str:
    """Join plain text fragments from a Notion rich-text property."""

    return "".join(
        item.get("plain_text", "") for item in property_value.get(key, [])
    ).strip()


def _date_value(property_value: dict[str, Any]) -> datetime | None:
    """Parse a Notion date property, accepting dates and datetimes."""

    date_value = property_value.get("date")
    if not date_value or not date_value.get("start"):
        return None
    return datetime.fromisoformat(date_value["start"].replace("Z", "+00:00"))


def _block_has_text(block: dict[str, Any]) -> bool:
    """Return whether a block contains visible rich text."""

    block_type = block.get("type", "")
    value = block.get(block_type, {})
    return bool(_rich_text_value(value, "rich_text"))


def _character_ratio(value: str, pattern: re.Pattern[str]) -> float:
    """Return the share of alphabetic characters matched by a pattern."""

    letters = LETTER.findall(value)
    if not letters:
        return 0.0
    return len(pattern.findall(value)) / len(letters)
