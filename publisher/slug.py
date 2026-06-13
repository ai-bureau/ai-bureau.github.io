"""Generate stable URL-safe article slugs.

Input: article titles.
Output: lowercase ASCII kebab-case slugs.
"""

import re

from unidecode import unidecode

FALLBACK_SLUG = "article"


def generate_slug(title: str) -> str:
    """Convert a Ukrainian or English title to lowercase kebab case.

    Args:
        title: Article title.

    Returns:
        Non-empty ASCII slug.
    """

    transliterated = unidecode(title).lower()
    slug = re.sub(r"[^a-z0-9]+", "-", transliterated).strip("-")
    return slug or FALLBACK_SLUG

