"""Publish Markdown files through the GitHub repository contents API.

Input: repository path and UTF-8 Markdown content.
Output: created GitHub commit or existing file content.
"""

import base64
import logging
from urllib.parse import quote

import requests

from publisher.http import RetryingHttpClient

GITHUB_API_BASE = "https://api.github.com"


class GitHubGateway:
    """Provide serial GitHub content reads and writes for one repository."""

    def __init__(
        self,
        token: str,
        repository: str,
        branch: str,
        max_retries: int,
        retry_pause_sec: float,
        logger: logging.Logger,
        session: requests.Session | None = None,
    ) -> None:
        """Initialize a GitHub API gateway.

        Args:
            token: GitHub personal access token.
            repository: Repository in ``owner/name`` format.
            branch: Target branch.
            max_retries: Maximum attempts per external request.
            retry_pause_sec: Pause between transient failures.
            logger: Application logger.
            session: Optional injectable requests session.
        """

        api_session = session or requests.Session()
        api_session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2026-03-10",
            }
        )
        self._repository = repository
        self._branch = branch
        self._http = RetryingHttpClient(
            api_session, max_retries, retry_pause_sec, logger
        )

    def get_file_content(self, path: str) -> str | None:
        """Return decoded file content or ``None`` when the path is unused.

        Args:
            path: Repository-relative path.

        Returns:
            UTF-8 file content or ``None``.
        """

        url = self._content_url(path)
        response = self._http.request(
            "GET",
            url,
            expected_statuses={200, 404},
            params={"ref": self._branch},
        )
        if response.status_code == 404:
            return None
        encoded_content = response.json().get("content", "")
        return base64.b64decode(encoded_content).decode("utf-8")

    def create_file(self, path: str, content: str, message: str) -> None:
        """Create a new Markdown file and commit it to the target branch.

        Args:
            path: Repository-relative path.
            content: UTF-8 Markdown content.
            message: Git commit message.
        """

        payload = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
            "branch": self._branch,
        }
        self._http.request(
            "PUT",
            self._content_url(path),
            expected_statuses={201},
            json=payload,
        )

    def _content_url(self, path: str) -> str:
        """Build the contents API URL for one repository path."""

        encoded_path = quote(path, safe="/")
        return f"{GITHUB_API_BASE}/repos/{self._repository}/contents/{encoded_path}"

