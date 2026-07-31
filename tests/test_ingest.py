"""Snapshot integrity: the manifest is the commit point, failures are recorded."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from orpulse import config, ingest
from orpulse.client import FetchError, FetchResult

from .conftest import load_fixture


class StubClient:
    """Serves fixtures; lets individual endpoints be made to fail on demand."""

    def __init__(self, *, failing_slugs=(), apps_fails=False, rankings_fails=False):
        self.failing_slugs = set(failing_slugs)
        self.apps_fails = apps_fails
        self.rankings_fails = rankings_fails

    def models(self):
        return load_fixture("models")

    def rankings_models(self, window):
        if self.rankings_fails:
            raise FetchError("/rankings", 503, "down")
        return load_fixture(f"rankings_models_{window}")

    def fetch(self, path, params=None):
        if path.endswith("/rankings/apps"):
            if self.apps_fails:
                return FetchResult(path, False, 503, 0, 1.0, error="unavailable")
            return FetchResult(path, True, 200, 10, 1.0, body=load_fixture("rankings_apps"))
        return FetchResult(path, True, 200, 10, 1.0, body={"data": []})

    def endpoint_stats(self, permaslug, variant="standard"):
        if permaslug in self.failing_slugs:
            return FetchResult("/stats", False, 404, 0, 1.0, error="not found")
        stats = load_fixture("endpoint_stats").get(permaslug, {"data": []})
        return FetchResult("/stats", True, 200, 10, 1.0, body=stats)


@pytest.fixture
def temp_raw(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "RAW_DIR", tmp_path / "raw")
    return tmp_path / "raw"


NOW = datetime(2026, 7, 31, 12, 0, tzinfo=timezone.utc)


def test_snapshot_writes_manifest_and_files(temp_raw):
    manifest = ingest.run(StubClient(), now=NOW)
    assert manifest.complete
    snap = temp_raw / "2026-07-31"
    assert (snap / ingest.MANIFEST_NAME).exists()
    for name in ("models", "rankings_models_day", "rankings_models_month", "endpoint_stats"):
        assert (snap / f"{name}.json.gz").exists()


def test_partial_failure_is_recorded_but_does_not_abort(temp_raw):
    """A 404 on one model must not cost us the other 364."""
    client = StubClient(failing_slugs={"meta-llama/llama-guard-4-12b"})
    manifest = ingest.run(client, now=NOW)
    assert manifest.complete
    assert manifest.requests_failed == 1
    assert any("llama-guard" in f["label"] for f in manifest.failures)
    assert manifest.failures[0]["status"] == 404


def test_best_effort_endpoint_failure_is_not_fatal(temp_raw):
    manifest = ingest.run(StubClient(apps_fails=True), now=NOW)
    assert manifest.complete
    assert any("apps" in f["label"] for f in manifest.failures)
    assert not (temp_raw / "2026-07-31" / "rankings_apps.json.gz").exists()


def test_load_bearing_failure_writes_no_manifest(temp_raw):
    """The rule: never write an incomplete snapshot marked complete."""
    with pytest.raises(FetchError):
        ingest.run(StubClient(rankings_fails=True), now=NOW)
    assert not (temp_raw / "2026-07-31" / ingest.MANIFEST_NAME).exists()
    assert ingest.list_snapshots() == []


def test_incomplete_snapshot_is_invisible(temp_raw):
    """A directory with data but no manifest never enters the dataset."""
    ingest.run(StubClient(), now=NOW)
    snap = temp_raw / "2026-07-31"
    manifest = json.loads((snap / ingest.MANIFEST_NAME).read_text())
    manifest["complete"] = False
    (snap / ingest.MANIFEST_NAME).write_text(json.dumps(manifest))
    assert ingest.list_snapshots() == []


def test_unreadable_manifest_is_treated_as_failed(temp_raw):
    ingest.run(StubClient(), now=NOW)
    (temp_raw / "2026-07-31" / ingest.MANIFEST_NAME).write_text("{ not json")
    assert ingest.list_snapshots() == []


def test_rerunning_the_same_day_is_idempotent(temp_raw):
    """Re-ingesting must overwrite, never accumulate duplicate snapshots."""
    ingest.run(StubClient(), now=NOW)
    ingest.run(StubClient(), now=NOW)
    assert ingest.list_snapshots() == ["2026-07-31"]


def test_manifest_records_provenance(temp_raw):
    manifest = ingest.run(StubClient(), now=NOW)
    assert manifest.snapshot_date == "2026-07-31"
    assert manifest.user_agent
    assert manifest.duration_seconds is not None
    assert manifest.files
