"""Tests for deterministic article slug generation."""

from publisher.slug import generate_slug


def test_generate_slug_transliterates_ukrainian_title() -> None:
    """Ukrainian text becomes lowercase ASCII kebab case."""

    assert generate_slug("Машини повинні працювати!") == "mashini-povinni-pratsiuvati"


def test_generate_slug_has_fallback_for_symbols_only() -> None:
    """A title without letters or digits still produces a valid path."""

    assert generate_slug("***") == "article"

