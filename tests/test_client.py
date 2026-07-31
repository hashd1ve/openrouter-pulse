"""Retry, backoff and failure-classification behaviour of the HTTP client."""

from __future__ import annotations

import pytest
import requests

from orpulse.client import FetchError, OpenRouterClient, read_gzip_json, write_gzip_json


class FakeResponse:
    def __init__(self, status: int, payload=None, text: str = "", json_error=False):
        self.status_code = status
        self._payload = payload
        self.text = text
        self.content = b"x" * 10
        self._json_error = json_error

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self):
        if self._json_error:
            raise ValueError("not json")
        return self._payload


class FakeSession:
    """Replays a scripted sequence of responses (or exceptions)."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.headers = {}

    def get(self, url, timeout=None):
        self.calls.append(url)
        item = self.responses.pop(0) if self.responses else FakeResponse(500)
        if isinstance(item, Exception):
            raise item
        return item


def make_client(responses, **kwargs):
    return OpenRouterClient(
        session=FakeSession(responses),
        rps=0,  # no real pacing in tests
        sleep=lambda _: None,  # no real backoff in tests
        **kwargs,
    )


def test_successful_fetch_returns_body():
    client = make_client([FakeResponse(200, {"data": [1, 2]})])
    result = client.fetch("/api/v1/models")
    assert result.ok
    assert result.body == {"data": [1, 2]}
    assert result.status == 200


def test_retries_on_retryable_status_then_succeeds():
    client = make_client(
        [FakeResponse(503, text="busy"), FakeResponse(429, text="slow down"),
         FakeResponse(200, {"data": []})],
        max_retries=3,
    )
    result = client.fetch("/api/v1/models")
    assert result.ok
    assert len(client.session.calls) == 3


def test_does_not_retry_a_404():
    """A missing model will still be missing on the fourth attempt."""
    client = make_client([FakeResponse(404, text="nope")], max_retries=3)
    result = client.fetch("/api/frontend/v1/stats/endpoint")
    assert not result.ok
    assert result.status == 404
    assert len(client.session.calls) == 1, "404 must not be retried"


def test_gives_up_after_max_retries():
    client = make_client([FakeResponse(500) for _ in range(10)], max_retries=2)
    result = client.fetch("/api/v1/models")
    assert not result.ok
    assert len(client.session.calls) == 3  # initial + 2 retries


def test_network_exception_is_retried_then_reported():
    client = make_client(
        [requests.ConnectionError("boom"), FakeResponse(200, {"ok": True})],
        max_retries=2,
    )
    result = client.fetch("/api/v1/models")
    assert result.ok


def test_html_error_page_with_200_is_a_failure():
    """OpenRouter serves a 200 HTML page for some bad frontend paths."""
    client = make_client([FakeResponse(200, json_error=True)])
    result = client.fetch("/api/frontend/v1/nope")
    assert not result.ok
    assert "non-JSON" in result.error


def test_fetch_never_raises_but_fetch_or_raise_does():
    client = make_client([FakeResponse(404, text="gone"), FakeResponse(404, text="gone")])
    assert client.fetch("/x").ok is False
    with pytest.raises(FetchError):
        client.fetch_or_raise("/x")


def test_params_are_encoded_into_the_url():
    client = make_client([FakeResponse(200, {})])
    client.fetch("/api/frontend/v1/stats/endpoint", {"permaslug": "a/b", "variant": "standard"})
    assert "permaslug=a%2Fb" in client.session.calls[0]
    assert "variant=standard" in client.session.calls[0]


def test_user_agent_is_identifiable_and_reachable():
    """Undocumented endpoints get scraped politely and traceably or not at all.

    A URL rather than an email: it reaches the issue tracker without stamping a
    personal address into somebody else's access logs on every request.
    """
    ua = make_client([]).session.headers["User-Agent"]
    assert ua.startswith("orpulse/")
    assert "https://" in ua, "the UA must carry a way to reach whoever is asking"


def test_gzip_roundtrip(tmp_path):
    payload = {"data": [{"a": 1}], "nested": {"b": [1, 2, 3]}}
    path = tmp_path / "x" / "y.json.gz"
    size = write_gzip_json(path, payload)
    assert size > 0
    assert read_gzip_json(path) == payload
