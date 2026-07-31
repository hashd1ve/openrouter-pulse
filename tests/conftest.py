"""Shared fixtures.

The JSON fixtures under `tests/fixtures/` are real API responses trimmed to
three models. Real shape, no network: if OpenRouter changes the schema these
tests keep passing and `test_contract.py` is what goes red — which is the
intended division of labour.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str):
    return json.loads((FIXTURES / f"{name}.json").read_text())


@pytest.fixture
def fixture_snapshot(tmp_path, monkeypatch):
    """Materialise the fixtures as a completed raw snapshot in a temp dir."""
    from orpulse import config
    from orpulse.client import write_gzip_json

    date = "2026-07-31"
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "RAW_DIR", tmp_path / "raw")
    monkeypatch.setattr(config, "STAGING_DIR", tmp_path / "staging")
    monkeypatch.setattr(config, "MARTS_DIR", tmp_path / "marts")

    snap = tmp_path / "raw" / date
    for name in (
        "models",
        "rankings_models_day",
        "rankings_models_week",
        "rankings_models_month",
        "endpoint_stats",
        "rankings_apps",
    ):
        write_gzip_json(snap / f"{name}.json.gz", load_fixture(name))

    (snap / "_manifest.json").write_text(
        json.dumps(
            {
                "snapshot_date": date,
                "snapshot_ts": f"{date}T00:00:00+00:00",
                "started_ts": f"{date}T00:00:00+00:00",
                "complete": True,
                "requests_ok": 6,
                "requests_failed": 0,
                "bytes_received": 1234,
                "files": {},
                "failures": [],
            }
        )
    )
    return date


@pytest.fixture
def built_marts(fixture_snapshot):
    """Staging + SQL marts + statistical marts from the fixture snapshot."""
    from orpulse import derive, transform

    staging = transform.build_staging([fixture_snapshot])
    transform.build_marts(staging)
    derive.build_all(transform.load_marts())
    return transform.load_marts()
