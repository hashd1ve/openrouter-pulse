"""The advanced marts: economics, context, competition, variants, derived stats.

Synthetic staging where the point is arithmetic, fixture marts where the point
is that the whole chain holds together.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from orpulse import config, derive, transform

from .test_marts import _staging, build, model_row, usage_rows, endpoint_row


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "MARTS_DIR", tmp_path / "marts")


def build_all(staging):
    con = transform.build_marts(staging)
    return {t: con.execute(f"SELECT * FROM {t}").df() for t in (
        "mart_model_economics", "mart_context_utilization",
        "mart_provider_competition", "mart_provider_scoreboard",
        "mart_variant_economics", "mart_model_fingerprint",
    )}


# --- economics -------------------------------------------------------------


def test_implied_value_multiplies_each_token_class_by_its_own_price(fixture_snapshot):
    staging = _staging(
        models=[model_row(price_prompt=1e-6, price_completion=10e-6)],
        usage=usage_rows(month=(1_000_000, 100_000, 100)),
    )
    e = build_all(staging)["mart_model_economics"].iloc[0]
    # 1e6 * 1e-6 + 1e5 * 1e-5 = 1.0 + 1.0
    assert e.implied_gross_value == pytest.approx(2.0)
    assert e.cost_per_request == pytest.approx(2.0 / 100)
    assert e.blended_price_per_token == pytest.approx(2.0 / 1_100_000)


def test_blended_price_falls_below_sticker_when_traffic_is_prompt_heavy(fixture_snapshot):
    """The core buyer-facing result: the output price overstates the real cost."""
    staging = _staging(
        models=[model_row(price_prompt=1e-6, price_completion=10e-6)],
        usage=usage_rows(month=(10_000_000, 100_000, 100)),  # 100:1 prompt-heavy
    )
    e = build_all(staging)["mart_model_economics"].iloc[0]
    assert e.blended_to_sticker_ratio < 0.25
    assert e.blended_price_per_token < e.price_completion


def test_models_without_a_price_are_excluded_not_zeroed(fixture_snapshot):
    """A missing price is unknown value, never zero value."""
    staging = _staging(
        models=[model_row(permaslug="a/priced"),
                model_row(permaslug="a/free", price_prompt=None, price_completion=None)],
        usage=usage_rows("a/priced") + usage_rows("a/free"),
    )
    econ = build_all(staging)["mart_model_economics"]
    assert set(econ.model_permaslug) == {"a/priced"}


def test_token_rank_and_value_rank_can_disagree(fixture_snapshot):
    """The whole point of section 2: volume leader, value nobody."""
    staging = _staging(
        models=[model_row(permaslug="a/cheap", price_prompt=1e-9, price_completion=1e-9),
                model_row(permaslug="a/dear", price_prompt=1e-4, price_completion=1e-4)],
        usage=(usage_rows("a/cheap", month=(1_000_000_000, 1_000_000, 1000))
               + usage_rows("a/dear", month=(1_000_000, 1_000, 10))),
    )
    econ = build_all(staging)["mart_model_economics"].set_index("model_permaslug")
    assert econ.loc["a/cheap"].token_rank < econ.loc["a/dear"].token_rank
    assert econ.loc["a/cheap"].value_rank > econ.loc["a/dear"].value_rank


# --- context ---------------------------------------------------------------


def test_window_utilisation_is_interaction_size_over_advertised_window(fixture_snapshot):
    staging = _staging(
        models=[model_row(context_length=100_000)],
        usage=usage_rows(month=(9_000, 1_000, 1)),  # 10k tokens in one request
    )
    c = build_all(staging)["mart_context_utilization"].iloc[0]
    assert c.mean_window_utilisation == pytest.approx(0.10)


def test_models_without_a_context_length_are_skipped(fixture_snapshot):
    staging = _staging(models=[model_row(context_length=0)], usage=usage_rows())
    assert build_all(staging)["mart_context_utilization"].empty


# --- provider competition --------------------------------------------------


def test_provider_hhi_of_a_sole_server_is_a_monopoly(fixture_snapshot):
    staging = _staging(
        models=[model_row()], usage=usage_rows(),
        endpoints=[endpoint_row("only", reqs=1000)],
    )
    c = build_all(staging)["mart_provider_competition"].iloc[0]
    assert c.provider_hhi == pytest.approx(10_000)
    assert c.leader_share == pytest.approx(1.0)


def test_provider_hhi_of_an_even_split(fixture_snapshot):
    staging = _staging(
        models=[model_row()], usage=usage_rows(),
        endpoints=[endpoint_row("a", reqs=500), endpoint_row("b", reqs=500)],
    )
    c = build_all(staging)["mart_provider_competition"].iloc[0]
    assert c.provider_hhi == pytest.approx(5_000)


def test_price_spread_is_dearest_over_cheapest(fixture_snapshot):
    staging = _staging(
        models=[model_row()], usage=usage_rows(),
        endpoints=[endpoint_row("a", price=1e-6), endpoint_row("b", price=7e-6)],
    )
    c = build_all(staging)["mart_provider_competition"].iloc[0]
    assert c.price_spread_ratio == pytest.approx(7.0)


def test_jitter_index_is_tail_over_median_latency(fixture_snapshot):
    staging = _staging(
        models=[model_row()], usage=usage_rows(),
        endpoints=[endpoint_row("a", p50_latency=100, p99_latency=800)],
    )
    c = build_all(staging)["mart_provider_competition"].iloc[0]
    assert c.jitter_index == pytest.approx(8.0)


# --- variants --------------------------------------------------------------


def test_variant_economics_only_covers_models_with_several_variants(fixture_snapshot):
    staging = _staging(
        models=[model_row(permaslug="a/dual"), model_row(permaslug="a/solo")],
        usage=(usage_rows("a/dual", variant="standard", month=(800, 200, 10))
               + usage_rows("a/dual", variant="free", month=(3_200, 800, 40))
               + usage_rows("a/solo", month=(100, 10, 1))),
    )
    v = build_all(staging)["mart_variant_economics"]
    assert set(v.model_permaslug) == {"a/dual"}
    assert v.iloc[0].free_token_share == pytest.approx(4000 / 5000)


def test_free_to_paid_intensity_compares_interaction_size(fixture_snapshot):
    """>1 means free interactions are larger: substitution, not a funnel."""
    staging = _staging(
        models=[model_row(permaslug="a/dual")],
        usage=(usage_rows("a/dual", variant="standard", month=(900, 100, 10))
               + usage_rows("a/dual", variant="free", month=(1_800, 200, 10))),
    )
    v = build_all(staging)["mart_variant_economics"].iloc[0]
    assert v.free_to_paid_intensity == pytest.approx(2.0)


# --- derived statistical marts ---------------------------------------------


def test_market_structure_reports_both_measures(built_marts):
    ms = built_marts["mart_market_structure"]
    assert not ms.empty
    assert {"tokens", "implied_value", "tokens_by_author"} <= set(ms["measure"])
    assert (ms["hhi"].dropna() <= 10_000).all()
    assert (ms["gini"].dropna().between(0, 1)).all()


def test_survival_curve_is_monotone_non_increasing(built_marts):
    curve = built_marts.get("mart_model_survival", pd.DataFrame())
    if curve.empty:
        pytest.skip("fixture has too few models for a curve")
    s = curve.sort_values("day")["survival"].to_numpy()
    assert (np.diff(s) <= 1e-12).all(), "survival can never increase"
    assert (s <= 1.0 + 1e-12).all() and (s >= -1e-12).all()


def test_survival_sensitivity_covers_every_threshold(built_marts):
    sens = built_marts.get("mart_survival_sensitivity", pd.DataFrame())
    if sens.empty:
        pytest.skip("no survival output for the fixture")
    assert set(sens["threshold_days"]) == set(derive.SENSITIVITY_THRESHOLDS)
    # A stricter definition of death can never find more deaths.
    ordered = sens.sort_values("threshold_days")["n_events"].to_numpy()
    assert (np.diff(ordered) <= 0).all()


def test_derive_refuses_to_run_before_the_sql_marts():
    with pytest.raises(RuntimeError, match="orpulse build"):
        derive.build_all({})


def test_market_structure_handles_a_single_holder():
    fp = pd.DataFrame([{
        "snapshot_date": "2026-07-31", "model_permaslug": "a/x", "author": "a",
        "archetype": "agentic", "month_tokens": 100, "month_requests": 10,
    }])
    ms = derive.market_structure({"mart_model_fingerprint": fp})
    tokens = ms[(ms["measure"] == "tokens") & (ms["segment"] == "all")].iloc[0]
    assert tokens["hhi"] == pytest.approx(10_000)
    assert tokens["top1_share"] == pytest.approx(1.0)
