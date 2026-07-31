"""Contract tests against the live OpenRouter API.

These are excluded from the default run (`-m 'not contract'`) and live in their
own CI job on purpose. The `/api/frontend/*` endpoints this project depends on
are undocumented and can change without notice; when that happens this suite
must go red **without** turning the whole repository red, or it would simply get
disabled and the alarm would be lost.

Run with: `make contract`
"""

from __future__ import annotations

import pytest

from orpulse import config
from orpulse.client import OpenRouterClient

pytestmark = pytest.mark.contract


@pytest.fixture(scope="module")
def client():
    return OpenRouterClient()


@pytest.fixture(scope="module")
def rankings(client):
    return {w: client.rankings_models(w) for w in config.WINDOWS}


# --- documented surface ----------------------------------------------------


def test_models_endpoint_shape(client):
    body = client.models()
    assert isinstance(body.get("data"), list) and body["data"]
    m = body["data"][0]
    for key in ("id", "canonical_slug", "context_length", "pricing", "created"):
        assert key in m, f"/api/v1/models lost the `{key}` field"
    assert isinstance(m["created"], (int, float)), "created must stay a unix timestamp"
    assert "prompt" in m["pricing"] and "completion" in m["pricing"]


def test_canonical_slug_joins_to_the_rankings_feed(client, rankings):
    """The single join key the whole model depends on."""
    slugs = {m["canonical_slug"] for m in client.models()["data"]}
    permaslugs = {r["model_permaslug"] for r in rankings["month"]["data"]}
    overlap = slugs & permaslugs
    assert len(overlap) > 100, (
        f"canonical_slug no longer joins to model_permaslug: only {len(overlap)} matches"
    )


# --- undocumented surface --------------------------------------------------


def test_rankings_fields_still_present(rankings):
    r = rankings["month"]["data"][0]
    for key in ("model_permaslug", "variant", "total_prompt_tokens",
                "total_completion_tokens", "count", "date"):
        assert key in r, f"rankings/models lost the `{key}` field"


def test_rankings_grain_is_model_and_variant(rankings):
    """One row per (model, variant) -- not per day."""
    rows = rankings["month"]["data"]
    keys = [(r["model_permaslug"], r["variant"]) for r in rows]
    assert len(keys) == len(set(keys)), "the grain of rankings/models changed"


def test_rankings_is_not_a_daily_time_series(rankings):
    """`view=day` must return a single trailing aggregate, not a series.

    If this ever fails, OpenRouter started publishing real history and the whole
    snapshot pipeline can be simplified. That is a change worth being told about.
    """
    dates = {r["date"][:10] for r in rankings["day"]["data"]}
    assert len(dates) <= 3, (
        f"view=day now spans {len(dates)} dates; the feed may have become a series"
    )


def test_windows_are_nested_and_cumulative(rankings):
    """The semantic invariant the pipeline's headline check relies on."""
    def totals(window):
        return {
            (r["model_permaslug"], r["variant"]):
                (r["total_prompt_tokens"] or 0) + (r["total_completion_tokens"] or 0)
            for r in rankings[window]["data"]
        }

    day, week, month = totals("day"), totals("week"), totals("month")
    shared = set(day) & set(week) & set(month)
    assert len(shared) > 50, "too few models in common to verify nesting"

    violations = [k for k in shared if not (day[k] <= week[k] * 1.01 <= month[k] * 1.02)]
    assert not violations, (
        f"{len(violations)} models violate day<=week<=month; "
        f"window semantics changed (e.g. {violations[:3]})"
    )


def test_endpoint_stats_shape(client, rankings):
    slug = max(
        rankings["month"]["data"], key=lambda r: r["total_prompt_tokens"] or 0
    )["model_permaslug"]
    result = client.endpoint_stats(slug)
    assert result.ok, f"endpoint stats unavailable for {slug}: {result.error}"
    endpoints = result.body["data"]
    assert endpoints
    e = endpoints[0]
    for key in ("id", "provider_name", "pricing", "stats"):
        assert key in e, f"stats/endpoint lost the `{key}` field"
    for key in ("p50_throughput", "p50_latency", "request_count", "window_minutes"):
        assert key in e["stats"], f"stats lost the `{key}` percentile"


def test_endpoint_stats_window_is_still_thirty_minutes(client, rankings):
    """Every caveat in the report is written around this number."""
    slug = rankings["month"]["data"][0]["model_permaslug"]
    result = client.endpoint_stats(slug)
    if not result.ok or not result.body.get("data"):
        pytest.skip(f"no endpoint data for {slug}")
    windows = {
        e["stats"]["window_minutes"]
        for e in result.body["data"]
        if e.get("stats", {}).get("window_minutes") is not None
    }
    assert windows == {30}, f"sampling window changed to {windows}; update the caveats"


def test_apps_ranking_shape(client):
    body = client.fetch("/api/frontend/v1/rankings/apps")
    assert body.ok, f"rankings/apps unavailable: {body.error}"
    data = body.body["data"]
    assert set(data) >= {"day", "week", "month"}
    r = data["month"][0]
    for key in ("app_id", "total_tokens", "total_requests", "rank", "app"):
        assert key in r, f"rankings/apps lost the `{key}` field"


# --- dormant fields --------------------------------------------------------


def test_dormant_fields_are_still_dormant(rankings):
    """These are zero for every model today, so nothing is built on them.

    A failure here is *good news*: it means OpenRouter started publishing cache,
    reasoning and tool-call telemetry, and there is new analysis to build.
    """
    from orpulse.transform import _DORMANT_FIELDS

    awake = {
        f for f in _DORMANT_FIELDS
        for r in rankings["month"]["data"]
        if (r.get(f) or 0) > 0
    }
    assert not awake, (
        f"fields {sorted(awake)} now carry data -- new analysis is possible, "
        "and docs/METHODOLOGY.md needs updating"
    )
