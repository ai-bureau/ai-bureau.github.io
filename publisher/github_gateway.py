"""Publish Markdown files through the GitHub Git data and contents APIs.

Input: repository path and UTF-8 Markdown content.
Output: one atomic GitHub commit or existing file content.
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

    def create_files(self, files: dict[str, str], message: str) -> None:
        """Create multiple Markdown files in one commit.

        Args:
            files: Repository-relative paths mapped to UTF-8 content.
            message: Git commit message.
        """

        if not files:
            raise ValueError("files cannot be empty")
        head = self._http.request(
            "GET",
            f"{GITHUB_API_BASE}/repos/{self._repository}/git/ref/heads/{self._branch}",
            expected_statuses={200},
        ).json()["object"]["sha"]
        base_tree = self._http.request(
            "GET",
            f"{GITHUB_API_BASE}/repos/{self._repository}/git/commits/{head}",
            expected_statuses={200},
        ).json()["tree"]["sha"]
        tree_entries = []
        for path, content in files.items():
            blob = self._http.request(
                "POST",
                f"{GITHUB_API_BASE}/repos/{self._repository}/git/blobs",
                expected_statuses={201},
                json={"content": content, "encoding": "utf-8"},
            ).json()
            tree_entries.append(
                {"path": path, "mode": "100644", "type": "blob", "sha": blob["sha"]}
            )
        tree = self._http.request(
            "POST",
            f"{GITHUB_API_BASE}/repos/{self._repository}/git/trees",
            expected_statuses={201},
            json={"base_tree": base_tree, "tree": tree_entries},
        ).json()
        commit = self._http.request(
            "POST",
            f"{GITHUB_API_BASE}/repos/{self._repository}/git/commits",
            expected_statuses={201},
            json={"message": message, "tree": tree["sha"], "parents": [head]},
        ).json()
        self._http.request(
            "PATCH",
            f"{GITHUB_API_BASE}/repos/{self._repository}/git/refs/heads/{self._branch}",
            expected_statuses={200},
            json={"sha": commit["sha"], "force": False},
        )

    def _content_url(self, path: str) -> str:
        """Build the contents API URL for one repository path."""

        encoded_path = quote(path, safe="/")
        return f"{GITHUB_API_BASE}/repos/{self._repository}/contents/{encoded_path}"
