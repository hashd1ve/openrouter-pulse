"""Data quality checks that break the pipeline.

A check that only logs is a check that gets ignored. Everything at ERROR
severity aborts the build; WARN records a fact worth seeing but does not stop
anything.

The most valuable check here is `nested_windows_consistent`. It is a *semantic*
invariant rather than a structural one: `day <= week <= month` must hold because
the windows are nested. It is exactly the check that would have caught, in an
afternoon rather than a quarter, the misreading of this feed as a daily series.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import pandas as pd

from . import config

log = logging.getLogger(__name__)

ERROR = "error"
WARN = "warn"


@dataclass
class CheckResult:
    name: str
    passed: bool
    severity: str
    detail: str

    @property
    def blocking(self) -> bool:
        return not self.passed and self.severity == ERROR

    def __str__(self) -> str:
        mark = "PASS" if self.passed else ("FAIL" if self.severity == ERROR else "WARN")
        return f"[{mark}] {self.name}: {self.detail}"


class DataQualityError(RuntimeError):
    def __init__(self, failures: list[CheckResult]):
        super().__init__(
            "data quality checks failed:\n" + "\n".join(f"  {f}" for f in failures)
        )
        self.failures = failures


# --- individual checks -----------------------------------------------------


def check_grain_unique(usage: pd.DataFrame) -> CheckResult:
    keys = ["snapshot_date", "usage_window", "model_permaslug", "variant"]
    dupes = usage.duplicated(subset=keys).sum()
    return CheckResult(
        "grain_unique",
        dupes == 0,
        ERROR,
        f"{dupes} duplicate rows on {'+'.join(keys)} out of {len(usage)}",
    )


def check_keys_not_null(usage: pd.DataFrame) -> CheckResult:
    keys = ["snapshot_date", "usage_window", "model_permaslug", "variant"]
    nulls = int(usage[keys].isna().any(axis=1).sum())
    return CheckResult(
        "keys_not_null", nulls == 0, ERROR, f"{nulls} rows with a null key column"
    )


def check_non_negative(usage: pd.DataFrame) -> CheckResult:
    cols = ["prompt_tokens", "completion_tokens", "requests"]
    bad = int((usage[cols] < 0).any(axis=1).sum())
    return CheckResult(
        "non_negative_measures", bad == 0, ERROR, f"{bad} rows with a negative measure"
    )


def check_nested_windows(usage: pd.DataFrame, tolerance: float = 0.01) -> CheckResult:
    """`day <= week <= month` for the same model and variant.

    A 1% tolerance absorbs the case where OpenRouter recomputes the three
    windows at slightly different moments. Anything larger means the semantics
    of the feed changed and every downstream number is suspect.
    """
    pivot = usage.pivot_table(
        index=["snapshot_date", "model_permaslug", "variant"],
        columns="usage_window",
        values="total_tokens",
        aggfunc="max",
    )
    for w in config.WINDOWS:
        if w not in pivot.columns:
            return CheckResult(
                "nested_windows_consistent",
                False,
                ERROR,
                f"window '{w}' missing from the snapshot entirely",
            )
    limit = 1 + tolerance
    bad_dw = int((pivot["day"] > pivot["week"] * limit).sum())
    bad_wm = int((pivot["week"] > pivot["month"] * limit).sum())
    total = bad_dw + bad_wm
    return CheckResult(
        "nested_windows_consistent",
        total == 0,
        ERROR,
        f"{bad_dw} rows with day>week, {bad_wm} with week>month "
        f"(of {len(pivot)} model-variants, {tolerance:.0%} tolerance)",
    )


def check_coverage(usage: pd.DataFrame) -> CheckResult:
    """Model count must not swing wildly between captures.

    This is the net that catches silent partial degradation -- the failure mode
    where every request returns 200 but the feed only carries half the models.
    """
    counts = (
        usage[usage["usage_window"] == "month"]
        .groupby("snapshot_date")["model_permaslug"]
        .nunique()
        .sort_index()
    )
    if len(counts) < 2:
        return CheckResult(
            "coverage_stable", True, WARN, f"only {len(counts)} snapshot(s); nothing to compare"
        )
    latest, previous = counts.iloc[-1], counts.iloc[-2]
    drift = abs(latest - previous) / previous if previous else 0.0
    return CheckResult(
        "coverage_stable",
        drift <= config.COVERAGE_TOLERANCE,
        ERROR,
        f"{previous} -> {latest} models ({drift:.1%} drift, "
        f"tolerance {config.COVERAGE_TOLERANCE:.0%})",
    )


def check_freshness(usage: pd.DataFrame, now: datetime | None = None) -> CheckResult:
    now = now or datetime.now(timezone.utc)
    latest = pd.to_datetime(usage["snapshot_date"].max()).to_pydatetime().replace(
        tzinfo=timezone.utc
    )
    age = now - latest
    limit = timedelta(hours=config.MAX_STALENESS_HOURS)
    return CheckResult(
        "freshness",
        age <= limit,
        WARN,
        f"latest snapshot is {age.total_seconds() / 3600:.1f}h old "
        f"(limit {config.MAX_STALENESS_HOURS}h)",
    )


def check_fingerprint_coverage(fingerprint: pd.DataFrame) -> CheckResult:
    """How much of the traffic actually gets classified.

    Reported as a warning rather than an error: some models legitimately have
    no completion tokens. But if it collapses, the headline claim is hollow.
    """
    if fingerprint.empty:
        return CheckResult("fingerprint_coverage", False, ERROR, "fingerprint mart is empty")
    latest = fingerprint[fingerprint["snapshot_date"] == fingerprint["snapshot_date"].max()]
    classified = latest[latest["archetype"] != "unclassified"]
    share = classified["month_tokens"].sum() / max(latest["month_tokens"].sum(), 1)
    return CheckResult(
        "fingerprint_coverage",
        share >= 0.90,
        WARN,
        f"{len(classified)}/{len(latest)} model-variants classified, "
        f"covering {share:.1%} of monthly tokens",
    )


def check_archetype_stability(stability: pd.DataFrame) -> CheckResult:
    """Success criterion: the classification must hold still between captures."""
    if stability.empty:
        return CheckResult(
            "archetype_stability", True, WARN, "fewer than 2 snapshots; not yet measurable"
        )
    rate = float(stability.sort_values("snapshot_date").iloc[-1]["reassignment_rate"])
    return CheckResult(
        "archetype_stability",
        rate <= 0.05,
        WARN,
        f"{rate:.2%} of models changed archetype since the previous capture (target <=5%)",
    )


# --- runner ----------------------------------------------------------------


def run_all(marts: dict[str, pd.DataFrame], *, now: datetime | None = None) -> list[CheckResult]:
    usage = marts.get("fct_model_usage_snapshot", pd.DataFrame())
    fingerprint = marts.get("mart_model_fingerprint", pd.DataFrame())
    stability = marts.get("mart_archetype_stability", pd.DataFrame())

    if usage.empty:
        return [CheckResult("usage_present", False, ERROR, "fct_model_usage_snapshot is empty")]

    results = [
        check_grain_unique(usage),
        check_keys_not_null(usage),
        check_non_negative(usage),
        check_nested_windows(usage),
        check_coverage(usage),
        check_freshness(usage, now=now),
        check_fingerprint_coverage(fingerprint),
        check_archetype_stability(stability),
    ]
    for r in results:
        log.log(logging.ERROR if r.blocking else logging.INFO, "%s", r)
    return results


def enforce(results: list[CheckResult]) -> None:
    blocking = [r for r in results if r.blocking]
    if blocking:
        raise DataQualityError(blocking)
