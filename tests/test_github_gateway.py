"""Tests for atomic GitHub publication commits."""

import logging

from publisher.github_gateway import GitHubGateway


class JsonResponse:
    """Minimal HTTP response returning configured JSON."""

    status_code = 200
    headers: dict[str, str] = {}
    text = ""

    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.status_code = 200

    def json(self) -> dict[str, object]:
        """Return configured JSON."""

        return self.payload


class SequenceSession:
    """Return configured GitHub API responses in order."""

    def __init__(self, payloads: list[dict[str, object]]) -> None:
        self.headers: dict[str, str] = {}
        self.responses = [JsonResponse(payload) for payload in payloads]
        self.requests: list[tuple[str, str, dict[str, object]]] = []

    def request(self, method: str, url: str, timeout: int, **kwargs: object) -> JsonResponse:
        """Record a request and return the next response."""

        self.requests.append((method, url, kwargs))
        response = self.responses.pop(0)
        response.status_code = 201 if method == "POST" else 200
        return response


def test_create_files_builds_one_commit_with_both_paths() -> None:
    """Both language files are included in one Git tree and commit."""

    session = SequenceSession(
        [
            {"object": {"sha": "head"}},
            {"tree": {"sha": "base-tree"}},
            {"sha": "ua-blob"},
            {"sha": "en-blob"},
            {"sha": "new-tree"},
            {"sha": "new-commit"},
            {},
        ]
    )
    gateway = GitHubGateway(
        "token",
        "ai-bureau/site",
        "main",
        max_retries=1,
        retry_pause_sec=0,
        logger=logging.getLogger("test"),
        session=session,  # type: ignore[arg-type]
    )

    gateway.create_files(
        {
            "content/uk/blog/article.md": "UA",
            "content/en/blog/article.md": "EN",
        },
        "Publish article",
    )

    tree_request = session.requests[4][2]["json"]
    assert {entry["path"] for entry in tree_request["tree"]} == {
        "content/uk/blog/article.md",
        "content/en/blog/article.md",
    }
    assert session.requests[-1][0] == "PATCH"
    assert session.requests[-1][2]["json"]["sha"] == "new-commit"
