"""Configure immediate console and daily file logging for the publisher.

Input: target log directory.
Output: configured standard-library logger.
"""

import logging
from datetime import date
from pathlib import Path


def configure_logging(log_dir: Path) -> logging.Logger:
    """Configure and return the publisher logger.

    Args:
        log_dir: Directory where daily log files are stored.

    Returns:
        Configured logger named ``publisher``.
    """

    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("publisher")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    file_handler = logging.FileHandler(
        log_dir / f"publisher_{date.today().isoformat()}.log",
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

