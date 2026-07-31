"""The modelling SQL, exercised against hand-built staging.

Synthetic input rather than fixtures here, because these tests are about
arithmetic and edge cases (age correction, SCD2 boundaries, Pareto dominance)
that need exact numbers, not realistic ones.
"""

from __future__ import annotations

import pandas as pd
import pytest

from orpulse import config, transform


def _staging(models=None, usage=None, endpoints=None, apps=None):
    """Build a staging dict with the right columns, filling in blanks."""
    out = {}
    for name, rows in (
        ("stg_models", models),
        ("stg_model_usage", usage),
        ("stg_endpoint_perf", endpoints),
        ("stg_apps", apps),
    ):
        cols = transform._EMPTY_COLUMNS[name]
        out[name] = (
            pd.DataFrame(rows).reindex(columns=cols) if rows else pd.DataFrame(columns=cols)
        )
    return out


def model_row(permaslug="a/m-1", date="2026-07-31", created="2026-06-01T00:00:00+00:00", **kw):
    base = {
        "snapshot_date": date,
        "model_permaslug": permaslug,
        "model_id": permaslug,
        "name": "M1",
        "author": "a",
        "context_length": 100_000,
        "created_ts": created,
        "price_prompt": 1e-6,
        "price_completion": 2e-6,
    }
    return {**base, **kw}


def usage_rows(permaslug="a/m-1", date="2026-07-31", day=(100, 10, 1),
               week=(700, 70, 7), month=(3000, 300, 30), variant="standard"):
    """(prompt_tokens, completion_tokens, requests) per window."""
    out = []
    for window, (p, c, r) in (("day", day), ("week", week), ("month", month)):
        out.append({
            "snapshot_date": date, "usage_window": window, "model_permaslug": permaslug,
            "variant": variant, "prompt_tokens": p, "completion_tokens": c, "requests": r,
            "source_last_activity_date": date, "source_change": None,
            "total_native_tokens_cached": 0, "total_native_tokens_reasoning": 0,
            "total_tool_calls": 0, "requests_with_tool_call_errors": 0,
        })
    return out


def build(staging):
    con = transform.build_marts(staging)
    return {t: con.execute(f"SELECT * FROM {t}").df()
            for t in ("dim_model", "fct_model_usage_snapshot", "mart_model_fingerprint",
                      "mart_archetype_stability", "mart_endpoint_price_perf")}


@pytest.fixture(autouse=True)
def _isolate_marts(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "MARTS_DIR", tmp_path / "marts")


# --- fingerprint arithmetic ------------------------------------------------


def test_pc_ratio_and_tokens_per_request(fixture_snapshot):
    staging = _staging(
        models=[model_row()],
        usage=usage_rows(month=(9000, 300, 30)),
    )
    fp = build(staging)["mart_model_fingerprint"].iloc[0]
    assert fp.pc_ratio == pytest.approx(30.0)              # 9000 / 300
    assert fp.tokens_per_request == pytest.approx(310.0)   # 9300 / 30


def test_momentum_is_corrected_for_model_age(fixture_snapshot):
    """A 10-day-old model must divide its month total by 10, not by 30."""
    staging = _staging(
        models=[model_row(created="2026-07-21T00:00:00+00:00")],  # 10 days before snapshot
        usage=usage_rows(day=(1000, 100, 2_000_000), month=(11000, 1000, 2_000_000)),
    )
    fp = build(staging)["mart_model_fingerprint"].iloc[0]
    assert fp.effective_days == 10
    # corrected:   1100 / (12000 / 10) = 0.9167
    assert fp.momentum == pytest.approx(1100 / (12000 / 10), rel=1e-6)
    # uncorrected: 1100 / (12000 / 30) = 2.75  -> 3x inflation
    assert fp.momentum_uncorrected == pytest.approx(1100 / (12000 / 30), rel=1e-6)
    assert fp.momentum_uncorrected > fp.momentum * 2.9


def test_mature_model_is_unaffected_by_the_correction(fixture_snapshot):
    staging = _staging(
        models=[model_row(created="2025-01-01T00:00:00+00:00")],
        usage=usage_rows(day=(1000, 100, 2_000_000), month=(30000, 3000, 2_000_000)),
    )
    fp = build(staging)["mart_model_fingerprint"].iloc[0]
    assert fp.effective_days == 30
    assert fp.momentum == pytest.approx(fp.momentum_uncorrected)


def test_unknown_age_is_never_rated(fixture_snapshot):
    """Assuming 30 days would report an uncorrected number as corrected."""
    staging = _staging(
        models=[model_row(created=None)],
        usage=usage_rows(day=(1000, 100, 2_000_000), month=(30000, 3000, 2_000_000)),
    )
    fp = build(staging)["mart_model_fingerprint"].iloc[0]
    assert not fp.is_ratable
    assert pd.isna(fp.momentum)


def test_too_young_and_too_small_are_not_rated(fixture_snapshot):
    staging = _staging(
        models=[model_row(permaslug="a/young", created="2026-07-29T00:00:00+00:00"),
                model_row(permaslug="a/tiny", created="2025-01-01T00:00:00+00:00")],
        usage=(usage_rows("a/young", month=(30000, 3000, 5_000_000))
               + usage_rows("a/tiny", month=(30000, 3000, 10))),
    )
    fp = build(staging)["mart_model_fingerprint"].set_index("model_permaslug")
    assert not fp.loc["a/young"].is_ratable, "2 days old"
    assert not fp.loc["a/tiny"].is_ratable, "10 requests"


# --- archetypes ------------------------------------------------------------


@pytest.mark.parametrize(
    "prompt,completion,requests,expected",
    [
        (1_000_000, 10_000, 20,      "agentic"),        # pc 100, tpr 50k
        (100_000,   10_000, 20,      "conversational"), # pc 10,  tpr 5.5k
        (1_000_000, 10_000, 10_000,  "extractive"),     # pc 100, tpr 101
        (10_000,    10_000, 20,      "output_heavy"),   # pc 1
    ],
)
def test_archetype_assignment(fixture_snapshot, prompt, completion, requests, expected):
    staging = _staging(
        models=[model_row()],
        usage=usage_rows(month=(prompt, completion, requests)),
    )
    assert build(staging)["mart_model_fingerprint"].iloc[0].archetype == expected


def test_zero_completion_tokens_is_unclassified_not_a_crash(fixture_snapshot):
    staging = _staging(models=[model_row()], usage=usage_rows(month=(1000, 0, 10)))
    fp = build(staging)["mart_model_fingerprint"].iloc[0]
    assert fp.archetype == "unclassified"
    assert pd.isna(fp.pc_ratio)


# --- SCD type 2 ------------------------------------------------------------


def test_price_change_opens_a_new_version(fixture_snapshot):
    staging = _staging(
        models=[model_row(date="2026-07-29", price_prompt=1e-6),
                model_row(date="2026-07-30", price_prompt=1e-6),
                model_row(date="2026-07-31", price_prompt=5e-6)],
        usage=usage_rows(date="2026-07-31"),
    )
    dim = build(staging)["dim_model"].sort_values("version_num")
    assert len(dim) == 2
    assert dim.iloc[0].valid_from == "2026-07-29"
    assert dim.iloc[0].valid_to == "2026-07-31"
    assert not dim.iloc[0].is_current
    assert dim.iloc[1].price_prompt == 5e-6
    assert dim.iloc[1].is_current


def test_stable_attributes_produce_a_single_version(fixture_snapshot):
    staging = _staging(
        models=[model_row(date=d) for d in ("2026-07-29", "2026-07-30", "2026-07-31")],
        usage=usage_rows(),
    )
    dim = build(staging)["dim_model"]
    assert len(dim) == 1
    assert dim.iloc[0].is_current
    assert dim.iloc[0].last_seen == "2026-07-31"


def test_fingerprint_joins_only_the_current_version(fixture_snapshot):
    """Two SCD rows must not fan the fact table out to two rows per model."""
    staging = _staging(
        models=[model_row(date="2026-07-30", context_length=1000),
                model_row(date="2026-07-31", context_length=2000)],
        usage=usage_rows(date="2026-07-31"),
    )
    fp = build(staging)["mart_model_fingerprint"]
    assert len(fp) == 1
    assert fp.iloc[0].context_length == 2000


# --- stability -------------------------------------------------------------


def test_archetype_stability_needs_two_snapshots(fixture_snapshot):
    staging = _staging(models=[model_row()], usage=usage_rows())
    assert build(staging)["mart_archetype_stability"].empty


def test_archetype_stability_counts_reassignments(fixture_snapshot):
    staging = _staging(
        models=[model_row(date="2026-07-30"), model_row(date="2026-07-31")],
        usage=(usage_rows(date="2026-07-30", month=(1_000_000, 10_000, 20))       # agentic
               + usage_rows(date="2026-07-31", month=(100_000, 10_000, 20))),     # conversational
    )
    stab = build(staging)["mart_archetype_stability"]
    assert len(stab) == 1
    assert stab.iloc[0].models_compared == 1
    assert stab.iloc[0].reassignments == 1
    assert stab.iloc[0].reassignment_rate == 1.0


# --- Pareto dominance ------------------------------------------------------


def endpoint_row(eid, model="a/m-1", price=2e-6, thr=50, reqs=1000, date="2026-07-31", **kw):
    base = {
        "snapshot_date": date, "endpoint_id": eid, "model_permaslug": model,
        "variant": "standard", "provider_name": f"prov-{eid}", "price_completion": price,
        "p50_throughput": thr, "p50_latency": 1000, "stat_request_count": reqs,
        "is_disabled": False, "window_minutes": 30,
    }
    return {**base, **kw}


def test_dominated_endpoint_is_flagged(fixture_snapshot):
    staging = _staging(
        models=[model_row()], usage=usage_rows(),
        endpoints=[endpoint_row("cheap-fast", price=1e-6, thr=100),
                   endpoint_row("dear-slow", price=5e-6, thr=10)],
    )
    pp = build(staging)["mart_endpoint_price_perf"].set_index("endpoint_id")
    assert bool(pp.loc["dear-slow"].is_dominated)
    assert not bool(pp.loc["cheap-fast"].is_dominated)


def test_identical_endpoints_do_not_dominate_each_other(fixture_snapshot):
    staging = _staging(
        models=[model_row()], usage=usage_rows(),
        endpoints=[endpoint_row("a"), endpoint_row("b")],
    )
    pp = build(staging)["mart_endpoint_price_perf"]
    assert not pp.is_dominated.any()


def test_endpoints_for_different_models_are_never_compared(fixture_snapshot):
    staging = _staging(
        models=[model_row()], usage=usage_rows(),
        endpoints=[endpoint_row("x", model="a/m-1", price=5e-6, thr=10),
                   endpoint_row("y", model="a/m-2", price=1e-6, thr=100)],
    )
    pp = build(staging)["mart_endpoint_price_perf"]
    assert not pp.is_dominated.any()


def test_low_volume_endpoints_are_excluded_as_noise(fixture_snapshot):
    """Percentiles over a handful of requests are not measurement."""
    staging = _staging(
        models=[model_row()], usage=usage_rows(),
        endpoints=[endpoint_row("busy", reqs=5000), endpoint_row("quiet", reqs=3)],
    )
    pp = build(staging)["mart_endpoint_price_perf"]
    assert set(pp.endpoint_id) == {"busy"}
