"""Shared retrying HTTP helper for external API calls.

Input: configured ``requests.Session`` and request parameters.
Output: successful HTTP responses or contextual exceptions.
"""

import logging
import time
from collections.abc import Callable

import requests

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class ApiRequestError(RuntimeError):
    """Raised when an external API request cannot be completed."""


class RetryingHttpClient:
    """Execute HTTP requests with bounded retries for transient failures."""

    def __init__(
        self,
        session: requests.Session,
        max_retries: int,
        retry_pause_sec: float,
        logger: logging.Logger,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        """Initialize the retrying client.

        Args:
            session: Configured requests session.
            max_retries: Maximum number of total attempts.
            retry_pause_sec: Default pause between attempts.
            logger: Logger for retry warnings.
            sleep: Injectable sleep function used by tests.
        """

        self._session = session
        self._max_retries = max_retries
        self._retry_pause_sec = retry_pause_sec
        self._logger = logger
        self._sleep = sleep

    def request(
        self,
        method: str,
        url: str,
        *,
        expected_statuses: set[int],
        **kwargs: object,
    ) -> requests.Response:
        """Send an HTTP request and retry transient failures.

        Args:
            method: HTTP method.
            url: Full request URL.
            expected_statuses: Status codes considered successful.
            **kwargs: Additional arguments passed to ``requests``.

        Returns:
            Successful HTTP response.

        Raises:
            ApiRequestError: If all attempts fail or a permanent error occurs.
        """

        for attempt in range(1, self._max_retries + 1):
            try:
                response = self._session.request(method, url, timeout=30, **kwargs)
            except requests.RequestException as error:
                if attempt == self._max_retries:
                    raise ApiRequestError(
                        f"{method} {url} failed after {attempt} attempts"
                    ) from error
                self._warn_and_pause(method, url, attempt, str(error), None)
                continue

            if response.status_code in expected_statuses:
                return response
            if (
                response.status_code not in RETRYABLE_STATUS_CODES
                or attempt == self._max_retries
            ):
                detail = response.text[:500]
                raise ApiRequestError(
                    f"{method} {url} returned {response.status_code}: {detail}"
                )

            retry_after = response.headers.get("Retry-After")
            pause = float(retry_after) if retry_after else None
            self._warn_and_pause(
                method,
                url,
                attempt,
                f"HTTP {response.status_code}",
                pause,
            )

        raise ApiRequestError(f"{method} {url} failed unexpectedly")

    def _warn_and_pause(
        self,
        method: str,
        url: str,
        attempt: int,
        reason: str,
        pause: float | None,
    ) -> None:
        """Log one retry and sleep before the next attempt."""

        delay = self._retry_pause_sec if pause is None else pause
        self._logger.warning(
            "External request failed (%s %s, attempt %d/%d): %s. Retry in %.1fs",
            method,
            url,
            attempt,
            self._max_retries,
            reason,
            delay,
        )
        self._sleep(delay)

