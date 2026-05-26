"""
Centralised HTTP client used by all test suites.

Provides a single get() helper so neither test file duplicates the
timing / timeout logic. Import this instead of calling requests.get directly.
"""
from __future__ import annotations

import time

import requests


def get(
    url: str,
    params: dict | None = None,
    timeout: int = 10,
) -> tuple[requests.Response, float]:
    """
    Issue a GET request and return (response, elapsed_seconds).

    Args:
        url:     Full URL to request.
        params:  Optional query-string parameters.
        timeout: Request timeout in seconds (default 10).
                 Pass 15 for slow parametrized fixture calls.

    Returns:
        A two-tuple of (requests.Response, float elapsed seconds).
    """
    start = time.monotonic()
    response = requests.get(url, params=params, timeout=timeout)
    elapsed = time.monotonic() - start
    return response, elapsed
