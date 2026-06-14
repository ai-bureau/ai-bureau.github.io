"""Run one AI Bureau article publication pass.

Input: configuration from ``.env`` and optional ``--dry-run`` CLI flag.
Output: GitHub commits, Notion status updates, and daily logs.
"""

import argparse
import logging
import sys

from publisher.config import load_settings
from publisher.github_gateway import GitHubGateway
from publisher.logging_config import configure_logging
from publisher.notion_gateway import NotionGateway
from publisher.service import PublisherService


def main() -> int:
    """Build dependencies and execute one publisher run.

    Returns:
        Process exit code.
    """

    parser = argparse.ArgumentParser(description="Publish approved AI Bureau articles")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="validate and select paths without modifying GitHub or Notion",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="path to the environment file (default: .env)",
    )
    args = parser.parse_args()

    try:
        settings = load_settings(args.env_file)
        logger = configure_logging(settings.log_dir)
        notion = NotionGateway(
            settings.notion_token,
            settings.notion_publications_data_source_id,
            settings.max_retries,
            settings.retry_pause_sec,
            logger,
        )
        github = GitHubGateway(
            settings.github_token,
            settings.github_repo,
            settings.github_branch,
            settings.max_retries,
            settings.retry_pause_sec,
            logger,
        )
        service = PublisherService(notion, github, logger, dry_run=args.dry_run)
        service.run()
        return 1 if service.had_errors else 0
    except Exception:
        logging.basicConfig(
            level=logging.ERROR,
            format="%(asctime)s | %(levelname)s | %(message)s",
        )
        logging.getLogger("publisher").exception("Publisher terminated with an error")
        return 1


if __name__ == "__main__":
    sys.exit(main())
