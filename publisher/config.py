"""Load and validate publisher configuration from environment variables.

Input: environment variables, optionally loaded from a local ``.env`` file.
Output: a validated ``Settings`` object.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """Hold all runtime configuration required by the publisher."""

    notion_token: str
    notion_publications_data_source_id: str
    github_token: str
    github_repo: str
    github_branch: str
    retry_pause_sec: float
    max_retries: int
    log_dir: Path


def load_settings(env_file: str | Path = ".env") -> Settings:
    """Load settings and reject missing or invalid values.

    Args:
        env_file: Path to the dotenv file.

    Returns:
        Validated publisher settings.

    Raises:
        ValueError: If a required variable or numeric setting is invalid.
    """

    load_dotenv(env_file)
    required_names = (
        "NOTION_TOKEN",
        "NOTION_PUBLICATIONS_DATA_SOURCE_ID",
        "GITHUB_TOKEN",
        "GITHUB_REPO",
    )
    missing = [name for name in required_names if not os.getenv(name)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    max_retries = _positive_int("MAX_RETRIES", default=3)
    retry_pause_sec = _non_negative_float("RETRY_PAUSE_SEC", default=60.0)
    github_repo = os.environ["GITHUB_REPO"].strip()
    if github_repo.count("/") != 1:
        raise ValueError("GITHUB_REPO must use the owner/repository format")

    return Settings(
        notion_token=os.environ["NOTION_TOKEN"].strip(),
        notion_publications_data_source_id=os.environ[
            "NOTION_PUBLICATIONS_DATA_SOURCE_ID"
        ].strip(),
        github_token=os.environ["GITHUB_TOKEN"].strip(),
        github_repo=github_repo,
        github_branch=os.getenv("GITHUB_BRANCH", "main").strip(),
        retry_pause_sec=retry_pause_sec,
        max_retries=max_retries,
        log_dir=Path(os.getenv("LOG_DIR", "logs")),
    )


def _positive_int(name: str, default: int) -> int:
    """Read a positive integer environment variable."""

    raw_value = os.getenv(name, str(default))
    try:
        value = int(raw_value)
    except ValueError as error:
        raise ValueError(f"{name} must be an integer") from error
    if value < 1:
        raise ValueError(f"{name} must be at least 1")
    return value


def _non_negative_float(name: str, default: float) -> float:
    """Read a non-negative floating-point environment variable."""

    raw_value = os.getenv(name, str(default))
    try:
        value = float(raw_value)
    except ValueError as error:
        raise ValueError(f"{name} must be a number") from error
    if value < 0:
        raise ValueError(f"{name} cannot be negative")
    return value
