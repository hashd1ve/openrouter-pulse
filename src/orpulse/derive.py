"""Statistical marts: the ones SQL is the wrong tool for.

`sql/marts.sql` handles everything set-based. This module handles estimators —
survival with censoring, robust regression, concentration indices — and writes
their output back out as Parquet alongside the rest, so consumers cannot tell
which marts came from which engine.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from . import analytics, config
from .transform import load_marts

log = logging.getLogger(__name__)

# A model counts as silent once its last day with traffic is this many days
# before the capture. See `survival_marts` for why this number is contested.
DEATH_THRESHOLD_DAYS = 2
SENSITIVITY_THRESHOLDS = (2, 3, 7, 14)


# --- market structure ------------------------------------------------------


def _concentration(values: pd.Series) -> dict:
    v = values.to_numpy(dtype=float)
    v = v[np.isfinite(v) & (v >= 0)]
    return {
        "n": int(v.size),
        "hhi": analytics.herfindahl(v),
        "gini": analytics.gini(v),
        "top1_share": analytics.top_n_share(v, 1),
        "top5_share": analytics.top_n_share(v, 5),
        "top10_share": analytics.top_n_share(v, 10),
    }


def market_structure(marts: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """How concentrated the market is, by attention and by money.

    Computed over two different measures on purpose. Token share says who the
    machines talk to; value share says who gets paid. They disagree sharply,
    and any single concentration number would hide that.
    """
    fp = marts["mart_model_fingerprint"]
    econ = marts.get("mart_model_economics", pd.DataFrame())
    rows = []

    for snapshot, g in fp.groupby("snapshot_date"):
        rows.append({"snapshot_date": snapshot, "measure": "tokens",
                     "segment": "all", **_concentration(g["month_tokens"])})
        rows.append({"snapshot_date": snapshot, "measure": "requests",
                     "segment": "all", **_concentration(g["month_requests"])})
        # Labs, not models: a lab with five popular models is more powerful
        # than the per-model numbers suggest.
        by_author = g.groupby("author", dropna=True)["month_tokens"].sum()
        rows.append({"snapshot_date": snapshot, "measure": "tokens_by_author",
                     "segment": "all", **_concentration(by_author)})
        for archetype, ga in g.groupby("archetype"):
            rows.append({"snapshot_date": snapshot, "measure": "tokens",
                         "segment": archetype, **_concentration(ga["month_tokens"])})

    if not econ.empty:
        for snapshot, g in econ.groupby("snapshot_date"):
            rows.append({"snapshot_date": snapshot, "measure": "implied_value",
                         "segment": "all", **_concentration(g["implied_gross_value"])})
            by_author = g.groupby("author", dropna=True)["implied_gross_value"].sum()
            rows.append({"snapshot_date": snapshot, "measure": "implied_value_by_author",
                         "segment": "all", **_concentration(by_author)})
            for archetype, ga in g.groupby("archetype"):
                rows.append({"snapshot_date": snapshot, "measure": "implied_value",
                             "segment": archetype,
                             **_concentration(ga["implied_gross_value"])})

    return pd.DataFrame(rows).sort_values(
        ["snapshot_date", "measure", "segment"]
    ).reset_index(drop=True)


# --- survival --------------------------------------------------------------


def _survival_frame(fp: pd.DataFrame, threshold: int) -> pd.DataFrame:
    """Durations and event flags for the survival estimator."""
    snapshot = pd.Timestamp(fp["snapshot_date"].max())
    d = fp.dropna(subset=["created_ts"]).copy()
    d["created"] = pd.to_datetime(d["created_ts"], utc=True).dt.tz_localize(None)
    d["last_activity"] = pd.to_datetime(d["source_last_activity_date"])
    d["days_silent"] = (snapshot - d["last_activity"]).dt.days
    d["died"] = d["days_silent"] >= threshold
    # A dead model's life ran to its last active day; a living one's life is
    # only known to be at least its current age -- that is the censoring.
    d["duration"] = np.where(
        d["died"],
        (d["last_activity"] - d["created"]).dt.days,
        (snapshot - d["created"]).dt.days,
    )
    return d[d["duration"] >= 0]


def survival_marts(marts: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Kaplan-Meier curve for model lifetime, plus a threshold sensitivity table.

    ⚠ PRELIMINARY, and the reason is worth stating precisely.

    Death is inferred from `source_last_activity_date`, which creates two
    biases pulling in opposite directions:

    1. **Right truncation.** A model silent for more than about 30 days leaves
       the monthly window entirely, so long-dead models are not in the data at
       all. Every subject is conditioned on recent presence, which biases
       survival UPWARD. The giveaway is in the sensitivity table: at a 30-day
       threshold there are zero events, which is a property of the feed rather
       than of the market.
    2. **Resurrection.** At a 2-day threshold, a model that merely had a quiet
       Tuesday is recorded as dead, which biases survival DOWNWARD.

    Their relative magnitudes are unknown, so the curve is published as an
    illustration of the method rather than as a finding.

    What fixes it: once the archive holds several weeks of captures, death is
    *observed* -- a model present on day N and absent on day N+k -- instead of
    inferred from a truncated field. The estimator does not change; the input
    stops being biased. This is the clearest case in the project of a metric
    that only a growing archive can make real.
    """
    fp = marts["mart_model_fingerprint"]
    latest = fp[fp["snapshot_date"] == fp["snapshot_date"].max()]

    sensitivity = []
    for threshold in SENSITIVITY_THRESHOLDS:
        d = _survival_frame(latest, threshold)
        km = analytics.kaplan_meier(d["duration"], d["died"])
        sensitivity.append({
            "snapshot_date": latest["snapshot_date"].max(),
            "threshold_days": threshold,
            "n_subjects": km.n_subjects,
            "n_events": km.n_events,
            "n_censored": km.n_subjects - km.n_events,
            "median_survival_days": km.quantile(0.5),
            "survival_at_90d": km.at(90),
            "survival_at_180d": km.at(180),
            "survival_at_365d": km.at(365),
        })

    d = _survival_frame(latest, DEATH_THRESHOLD_DAYS)
    km = analytics.kaplan_meier(d["duration"], d["died"])
    curve = pd.DataFrame({
        "snapshot_date": latest["snapshot_date"].max(),
        "threshold_days": DEATH_THRESHOLD_DAYS,
        "day": km.time,
        "at_risk": km.at_risk,
        "events": km.events,
        "censored": km.censored,
        "survival": km.survival,
        "ci_low": km.ci_low,
        "ci_high": km.ci_high,
    })
    return curve, pd.DataFrame(sensitivity)


# --- elasticity ------------------------------------------------------------


def price_elasticity(marts: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Association between price and volume, by archetype.

    NOT a causal elasticity. This is a cross-section of different models at
    different prices, not one model observed at several prices, so the estimate
    absorbs everything that makes cheap models cheap -- smaller, weaker, newer.
    A steep slope is as consistent with "buyers chase cheap tokens" as with
    "cheap models are the ones built for bulk work".

    It is reported because the magnitude still bounds the story, and because
    the differences BETWEEN archetypes are more informative than any single
    coefficient: agentic buyers and chat buyers do not respond alike.
    """
    econ = marts.get("mart_model_economics", pd.DataFrame())
    if econ.empty:
        return pd.DataFrame()

    latest = econ[econ["snapshot_date"] == econ["snapshot_date"].max()]
    rows = []
    segments = [("all", latest)] + [
        (name, g) for name, g in latest.groupby("archetype") if len(g) >= 15
    ]
    for name, g in segments:
        for weighted, label in ((False, "unweighted"), (True, "request_weighted")):
            result = analytics.log_log_elasticity(
                g["price_completion"], g["month_tokens"],
                weights=g["month_requests"] if weighted else None,
            )
            if result is None:
                continue
            slope = result.summary()["log_price"]
            rows.append({
                "snapshot_date": latest["snapshot_date"].max(),
                "segment": name,
                "weighting": label,
                "elasticity": slope["coef"],
                "se": slope["se"],
                "t_stat": slope["t"],
                "ci_low": slope["ci_low"],
                "ci_high": slope["ci_high"],
                "r_squared": result.r_squared,
                "n": result.n,
                "significant_at_95": (slope["ci_low"] > 0) or (slope["ci_high"] < 0),
            })
    return pd.DataFrame(rows)


# --- runner ----------------------------------------------------------------

BUILDERS = {
    "mart_market_structure": market_structure,
    "mart_price_elasticity": price_elasticity,
}


def build_all(marts: dict[str, pd.DataFrame] | None = None) -> dict[str, pd.DataFrame]:
    """Materialise the statistical marts next to the SQL ones."""
    marts = marts if marts is not None else load_marts()
    if "mart_model_fingerprint" not in marts:
        raise RuntimeError("run the SQL marts first: `orpulse build`")

    out = {name: fn(marts) for name, fn in BUILDERS.items()}
    curve, sensitivity = survival_marts(marts)
    out["mart_model_survival"] = curve
    out["mart_survival_sensitivity"] = sensitivity

    config.MARTS_DIR.mkdir(parents=True, exist_ok=True)
    for name, df in out.items():
        if df.empty:
            log.warning("%s is empty; skipping", name)
            continue
        df.to_parquet(config.MARTS_DIR / f"{name}.parquet", index=False)
        log.info("wrote %s (%d rows)", name, len(df))
    return out
