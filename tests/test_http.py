"""Tests for bounded external API retries."""

import logging

import requests

from publisher.http import RetryingHttpClient


class FakeSession:
    """Return a predefined sequence of HTTP responses."""

    def __init__(self, responses: list[requests.Response]) -> None:
        self.responses = responses
        self.calls = 0

    def request(self, method: str, url: str, timeout: int, **kwargs: object) -> requests.Response:
        """Return the next configured response."""

        response = self.responses[self.calls]
        self.calls += 1
        return response


def make_response(status_code: int) -> requests.Response:
    """Create a minimal requests response fixture."""

    response = requests.Response()
    response.status_code = status_code
    response._content = b"{}"
    return response


def test_retrying_client_retries_transient_failure() -> None:
    """A server error is retried before returning success."""

    session = FakeSession([make_response(500), make_response(200)])
    sleeps: list[float] = []
    client = RetryingHttpClient(
        session,  # type: ignore[arg-type]
        max_retries=3,
        retry_pause_sec=1,
        logger=logging.getLogger("test"),
        sleep=sleeps.append,
    )

    response = client.request("GET", "https://example.com", expected_statuses={200})

    assert response.status_code == 200
    assert session.calls == 2
    assert sleeps == [1]

