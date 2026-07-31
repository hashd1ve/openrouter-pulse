"""Staging: JSON from the API becomes flat, typed records."""

from __future__ import annotations

import pandas as pd

from orpulse import transform


def test_models_are_flattened_with_permaslug_as_key(fixture_snapshot):
    df = transform.stage_models(fixture_snapshot)
    assert len(df) == 3
    # The rankings feed calls this model_permaslug; /api/v1/models calls it
    # canonical_slug. Getting this join key wrong silently orphans every fact.
    assert "anthropic/claude-opus-5-20260723" in set(df.model_permaslug)
    row = df[df.model_permaslug == "anthropic/claude-opus-5-20260723"].iloc[0]
    assert row.author == "anthropic"
    assert row.price_prompt > 0
    assert row.created_ts.startswith("2026-")


def test_usage_covers_all_three_windows(fixture_snapshot):
    df = transform.stage_model_usage(fixture_snapshot)
    assert set(df.usage_window) == {"day", "week", "month"}
    assert df.prompt_tokens.min() >= 0


def test_source_date_is_captured_as_an_attribute_not_a_key(fixture_snapshot):
    """The API's `date` is the last day with traffic, not a time index."""
    df = transform.stage_model_usage(fixture_snapshot)
    assert "source_last_activity_date" in df.columns
    assert df.snapshot_date.nunique() == 1
    assert (df.snapshot_date == fixture_snapshot).all()


def test_dormant_fields_are_ingested_but_empty(fixture_snapshot):
    """They are zero in the public feed today; carried in case that changes."""
    df = transform.stage_model_usage(fixture_snapshot)
    for field in transform._DORMANT_FIELDS:
        assert field in df.columns
        assert (df[field] == 0).all()


def test_endpoint_perf_carries_the_sampling_window(fixture_snapshot):
    """window_minutes must travel with the percentiles or they get misread."""
    df = transform.stage_endpoint_perf(fixture_snapshot)
    assert not df.empty
    assert "window_minutes" in df.columns
    assert (df.window_minutes.dropna() == 30).all()


def test_apps_are_flattened_per_window(fixture_snapshot):
    df = transform.stage_apps(fixture_snapshot)
    assert not df.empty
    assert set(df.usage_window) <= {"day", "week", "month"}
    assert df.total_tokens.dtype.kind in "iu"


def test_prices_parse_from_decimal_strings():
    assert transform._f("0.000005") == 5e-6
    assert transform._f("") is None
    assert transform._f(None) is None
    assert transform._f("not-a-number") is None


def test_missing_files_yield_empty_frames(tmp_path, monkeypatch):
    from orpulse import config

    monkeypatch.setattr(config, "RAW_DIR", tmp_path / "raw")
    assert transform.stage_models("2026-01-01").empty
    assert transform.stage_model_usage("2026-01-01").empty


def test_staging_rebuilds_from_all_snapshots(fixture_snapshot):
    staging = transform.build_staging([fixture_snapshot])
    assert set(staging) == {"stg_models", "stg_model_usage", "stg_endpoint_perf", "stg_apps"}
    assert not staging["stg_model_usage"].empty
