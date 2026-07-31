"""HTTP access to OpenRouter's public endpoints, all unauthenticated.

``/api/v1/*`` is documented and stable. ``/api/frontend/*`` backs
openrouter.ai/rankings, has no contract, and can change shape without notice;
``tests/test_contract.py`` watches it from a separate workflow.
"""

from __future__ import annotations

import gzip
import json
import logging
import random
import threading
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlencode

import requests

from . import config

log = logging.getLogger(__name__)


class FetchError(RuntimeError):
    """A request failed in a way that retrying did not fix."""

    def __init__(self, url: str, status: int | None, detail: str):
        super().__init__(f"{url} -> {status or 'no response'}: {detail}")
        self.url = url
        self.status = status
        self.detail = detail


@dataclass
class FetchResult:
    """One completed request, successful or not.

    Both outcomes are recorded so the run manifest can distinguish "this model
    genuinely has no endpoint data" from "we never asked".
    """

    path: str
    ok: bool
    status: int | None
    bytes_received: int
    duration_ms: float
    body: Any | None = None
    error: str | None = None


class _RateLimiter:
    """Simple thread-safe minimum-interval gate."""

    def __init__(self, per_second: float):
        self._min_interval = 1.0 / per_second if per_second > 0 else 0.0
        self._lock = threading.Lock()
        self._next_allowed = 0.0

    def wait(self) -> None:
        if self._min_interval <= 0:
            return
        with self._lock:
            now = time.monotonic()
            sleep_for = self._next_allowed - now
            if sleep_for > 0:
                time.sleep(sleep_for)
                now = time.monotonic()
            self._next_allowed = now + self._min_interval


class OpenRouterClient:
    """Polite, retrying client for OpenRouter's public surface."""

    # Retrying a 404 is pointless; retrying a 429 or a 5xx is not.
    RETRYABLE_STATUS = frozenset({408, 425, 429, 500, 502, 503, 504})

    def __init__(
        self,
        base_url: str = config.BASE_URL,
        *,
        session: requests.Session | None = None,
        rps: float = config.REQUESTS_PER_SECOND,
        max_retries: int = config.MAX_RETRIES,
        timeout: float = config.TIMEOUT_SECONDS,
        sleep=time.sleep,
    ):
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.session.headers.update(
            {"User-Agent": config.USER_AGENT, "Accept": "application/json"}
        )
        self.max_retries = max_retries
        self.timeout = timeout
        self._limiter = _RateLimiter(rps)
        self._sleep = sleep

    # -- core ---------------------------------------------------------------

    def fetch(self, path: str, params: dict[str, str] | None = None) -> FetchResult:
        """Fetch one path, never raising. The caller decides what a failure means.

        A partial failure (one model 404s) must not abort a 365-request sweep,
        so failures come back as data rather than exceptions.
        """
        url = f"{self.base_url}{path}"
        if params:
            url = f"{url}?{urlencode(params)}"
        started = time.monotonic()
        last_status: int | None = None
        last_detail = "unknown"

        for attempt in range(self.max_retries + 1):
            self._limiter.wait()
            try:
                resp = self.session.get(url, timeout=self.timeout)
                last_status = resp.status_code
                if resp.ok:
                    try:
                        body = resp.json()
                    except ValueError as exc:
                        # A 200 that is not JSON means we hit an HTML error page.
                        last_detail = f"non-JSON body: {exc}"
                        break
                    return FetchResult(
                        path=path,
                        ok=True,
                        status=resp.status_code,
                        bytes_received=len(resp.content),
                        duration_ms=(time.monotonic() - started) * 1000,
                        body=body,
                    )
                last_detail = resp.text[:200]
                if resp.status_code not in self.RETRYABLE_STATUS:
                    break
            except requests.RequestException as exc:
                last_status = None
                last_detail = str(exc)[:200]

            if attempt < self.max_retries:
                # Exponential backoff with jitter, so a sweep that trips a rate
                # limit does not resynchronise into a thundering herd.
                backoff = (2**attempt) * 0.5
                self._sleep(backoff + random.uniform(0, backoff))

        return FetchResult(
            path=path,
            ok=False,
            status=last_status,
            bytes_received=0,
            duration_ms=(time.monotonic() - started) * 1000,
            error=last_detail,
        )

    def fetch_or_raise(self, path: str, params: dict[str, str] | None = None) -> Any:
        """For endpoints whose failure invalidates the whole run."""
        result = self.fetch(path, params)
        if not result.ok:
            raise FetchError(path, result.status, result.error or "")
        return result.body

    # -- documented endpoints ----------------------------------------------

    def models(self) -> Any:
        return self.fetch_or_raise("/api/v1/models")

    def providers(self) -> Any:
        return self.fetch_or_raise("/api/v1/providers")

    # -- undocumented endpoints --------------------------------------------

    def rankings_models(self, window: str) -> Any:
        return self.fetch_or_raise(
            "/api/frontend/v1/rankings/models", {"view": window}
        )

    def rankings_apps(self) -> Any:
        return self.fetch_or_raise("/api/frontend/v1/rankings/apps")

    def endpoint_stats(self, permaslug: str, variant: str = "standard") -> FetchResult:
        """Per-provider performance for one model.

        Returns the raw FetchResult: some permaslugs legitimately 404 here, and
        the sweep needs to record that rather than crash.
        """
        return self.fetch(
            "/api/frontend/v1/stats/endpoint",
            {"permaslug": permaslug, "variant": variant},
        )


def write_gzip_json(path, payload: Any) -> int:
    """Write JSON gzipped, returning bytes written.

    Raw snapshots are the one artefact that cannot be regenerated later, so they
    are stored verbatim and compressed rather than pre-parsed.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    with gzip.open(path, "wb") as fh:
        fh.write(encoded)
    return path.stat().st_size


def read_gzip_json(path) -> Any:
    with gzip.open(path, "rb") as fh:
        return json.loads(fh.read().decode())
