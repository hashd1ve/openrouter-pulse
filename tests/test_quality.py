"""Every check must actually catch the failure it claims to catch.

A quality suite that only tests the happy path proves nothing: it would pass
just as well if the checks were `return True`.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

from orpulse import config, quality


def usage_df(rows):
    df = pd.DataFrame(rows)
    df["total_tokens"] = df.prompt_tokens + df.completion_tokens
    return df


def row(date="2026-07-31", window="month", model="a/m-1", variant="standard",
        prompt=1000, completion=100, requests=10):
    return {
        "snapshot_date": date, "usage_window": window, "model_permaslug": model,
        "variant": variant, "prompt_tokens": prompt, "completion_tokens": completion,
        "requests": requests,
    }


def nested_ok(date="2026-07-31", model="a/m-1"):
    return [
        row(date, "day", model, prompt=100, completion=10),
        row(date, "week", model, prompt=700, completion=70),
        row(date, "month", model, prompt=3000, completion=300),
    ]


# --- grain / nulls / signs -------------------------------------------------


def test_grain_unique_passes_on_clean_data():
    assert quality.check_grain_unique(usage_df(nested_ok())).passed


def test_grain_unique_catches_duplicates():
    result = quality.check_grain_unique(usage_df(nested_ok() + [row()]))
    assert not result.passed and result.blocking


def test_keys_not_null_catches_a_missing_variant():
    result = quality.check_keys_not_null(usage_df(nested_ok() + [row(variant=None)]))
    assert not result.passed and result.blocking


def test_non_negative_catches_a_negative_token_count():
    result = quality.check_non_negative(usage_df(nested_ok() + [row(model="a/m-2", prompt=-1)]))
    assert not result.passed and result.blocking


# --- the semantic invariant ------------------------------------------------


def test_nested_windows_passes_when_windows_nest():
    assert quality.check_nested_windows(usage_df(nested_ok())).passed


def test_nested_windows_catches_day_exceeding_week():
    """This is the check that would have caught misreading the feed as a series."""
    rows = [
        row(window="day", prompt=5000, completion=500),
        row(window="week", prompt=700, completion=70),
        row(window="month", prompt=3000, completion=300),
    ]
    result = quality.check_nested_windows(usage_df(rows))
    assert not result.passed and result.blocking
    assert "day>week" in result.detail


def test_nested_windows_catches_week_exceeding_month():
    rows = [
        row(window="day", prompt=100, completion=10),
        row(window="week", prompt=9000, completion=900),
        row(window="month", prompt=3000, completion=300),
    ]
    result = quality.check_nested_windows(usage_df(rows))
    assert not result.passed


def test_nested_windows_tolerates_small_recomputation_skew():
    """Slack absorbs windows recomputed moments apart.

    The check compares total tokens, so: day = 110, week = 105 -> day exceeds
    week by 4.8%. Strict fails, a 10% tolerance forgives it.
    """
    rows = [
        row(window="day", prompt=100, completion=10),   # total 110
        row(window="week", prompt=95, completion=10),   # total 105
        row(window="month", prompt=3000, completion=300),
    ]
    strict = quality.check_nested_windows(usage_df(rows), tolerance=0.0)
    loose = quality.check_nested_windows(usage_df(rows), tolerance=0.10)
    assert not strict.passed
    assert loose.passed


def test_nested_windows_catches_a_missing_window_entirely():
    rows = [row(window="day"), row(window="week")]
    result = quality.check_nested_windows(usage_df(rows))
    assert not result.passed
    assert "missing" in result.detail


# --- coverage / freshness --------------------------------------------------


def test_coverage_is_skipped_with_a_single_snapshot():
    result = quality.check_coverage(usage_df(nested_ok()))
    assert result.passed and not result.blocking


def test_coverage_catches_a_silent_halving_of_the_feed():
    old = [r for m in range(20) for r in nested_ok("2026-07-30", f"a/m-{m}")]
    new = [r for m in range(8) for r in nested_ok("2026-07-31", f"a/m-{m}")]
    result = quality.check_coverage(usage_df(old + new))
    assert not result.passed and result.blocking


def test_coverage_tolerates_normal_churn():
    old = [r for m in range(20) for r in nested_ok("2026-07-30", f"a/m-{m}")]
    new = [r for m in range(19) for r in nested_ok("2026-07-31", f"a/m-{m}")]
    assert quality.check_coverage(usage_df(old + new)).passed


def test_freshness_flags_a_dead_cron():
    df = usage_df(nested_ok("2026-07-01"))
    result = quality.check_freshness(df, now=datetime(2026, 7, 31, tzinfo=timezone.utc))
    assert not result.passed
    assert not result.blocking, "staleness warns; it does not invalidate the data"


def test_freshness_passes_for_a_recent_snapshot():
    df = usage_df(nested_ok("2026-07-31"))
    result = quality.check_freshness(df, now=datetime(2026, 7, 31, 6, tzinfo=timezone.utc))
    assert result.passed


# --- fingerprint / stability ----------------------------------------------


def test_fingerprint_coverage_reports_classified_share():
    fp = pd.DataFrame([
        {"snapshot_date": "2026-07-31", "archetype": "agentic", "month_tokens": 990},
        {"snapshot_date": "2026-07-31", "archetype": "unclassified", "month_tokens": 10},
    ])
    result = quality.check_fingerprint_coverage(fp)
    assert result.passed
    assert "99.0%" in result.detail


def test_fingerprint_coverage_warns_when_classification_collapses():
    fp = pd.DataFrame([
        {"snapshot_date": "2026-07-31", "archetype": "agentic", "month_tokens": 100},
        {"snapshot_date": "2026-07-31", "archetype": "unclassified", "month_tokens": 900},
    ])
    result = quality.check_fingerprint_coverage(fp)
    assert not result.passed and not result.blocking


def test_empty_fingerprint_is_blocking():
    assert quality.check_fingerprint_coverage(pd.DataFrame()).blocking


def test_archetype_stability_warns_above_target():
    stab = pd.DataFrame([{"snapshot_date": "2026-07-31", "reassignment_rate": 0.40}])
    result = quality.check_archetype_stability(stab)
    assert not result.passed and not result.blocking


# --- runner ----------------------------------------------------------------


def test_run_all_on_real_marts_passes(built_marts):
    results = quality.run_all(built_marts)
    blocking = [r for r in results if r.blocking]
    assert not blocking, f"blocking failures on fixture data: {blocking}"


def test_enforce_raises_only_on_blocking_failures():
    ok = [quality.CheckResult("a", False, quality.WARN, "meh")]
    quality.enforce(ok)  # must not raise
    bad = [quality.CheckResult("b", False, quality.ERROR, "broken")]
    with pytest.raises(quality.DataQualityError):
        quality.enforce(bad)


def test_missing_usage_mart_is_blocking():
    results = quality.run_all({"fct_model_usage_snapshot": pd.DataFrame()})
    assert results[0].blocking
