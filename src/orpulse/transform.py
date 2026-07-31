"""raw -> staging -> marts.

The split is deliberate: Python flattens JSON into flat records (something SQL
is bad at), SQL does the modelling (something Python is bad at reviewing).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pandas as pd

from . import config
from .client import read_gzip_json
from .ingest import list_snapshots, snapshot_dir

log = logging.getLogger(__name__)

SQL_DIR = Path(__file__).parent / "sql"


def _f(value) -> float | None:
    """Prices arrive as decimal strings; missing keys are common."""
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _read(snapshot_date: str, name: str):
    path = snapshot_dir(snapshot_date) / f"{name}.json.gz"
    return read_gzip_json(path) if path.exists() else None


# --- staging builders ------------------------------------------------------


def stage_models(snapshot_date: str) -> pd.DataFrame:
    payload = _read(snapshot_date, "models") or {}
    rows = []
    for m in payload.get("data", []):
        pricing = m.get("pricing") or {}
        arch = m.get("architecture") or {}
        top = m.get("top_provider") or {}
        created = m.get("created")
        rows.append(
            {
                "snapshot_date": snapshot_date,
                # canonical_slug is what the rankings feed calls model_permaslug.
                "model_permaslug": m.get("canonical_slug"),
                "model_id": m.get("id"),
                "name": m.get("name"),
                "author": (m.get("id") or "/").split("/")[0],
                "context_length": m.get("context_length"),
                "created_ts": (
                    datetime.fromtimestamp(created, tz=timezone.utc).isoformat()
                    if isinstance(created, (int, float))
                    else None
                ),
                "price_prompt": _f(pricing.get("prompt")),
                "price_completion": _f(pricing.get("completion")),
                "price_cache_read": _f(pricing.get("input_cache_read")),
                "input_modalities": ",".join(arch.get("input_modalities") or []),
                "output_modalities": ",".join(arch.get("output_modalities") or []),
                "tokenizer": arch.get("tokenizer"),
                "is_moderated": top.get("is_moderated"),
                "max_completion_tokens": top.get("max_completion_tokens"),
                "supports_tools": "tools" in (m.get("supported_parameters") or []),
                "supports_reasoning": "reasoning" in (m.get("supported_parameters") or []),
            }
        )
    return pd.DataFrame(rows)


# Present in the schema but zero for every model in the public feed. Ingested
# anyway in case OpenRouter starts populating them; never analysed.
_DORMANT_FIELDS = (
    "total_native_tokens_cached",
    "total_native_tokens_reasoning",
    "total_tool_calls",
    "requests_with_tool_call_errors",
)


def stage_model_usage(snapshot_date: str) -> pd.DataFrame:
    rows = []
    for window in config.WINDOWS:
        payload = _read(snapshot_date, f"rankings_models_{window}")
        if payload is None:
            continue
        for r in payload.get("data", []):
            rows.append(
                {
                    "snapshot_date": snapshot_date,
                    "usage_window": window,
                    "model_permaslug": r.get("model_permaslug"),
                    "variant": r.get("variant"),
                    "prompt_tokens": r.get("total_prompt_tokens") or 0,
                    "completion_tokens": r.get("total_completion_tokens") or 0,
                    "requests": r.get("count") or 0,
                    # NOT a time index: this is the model's last day with traffic.
                    "source_last_activity_date": (r.get("date") or "")[:10] or None,
                    "source_change": r.get("change"),
                    **{f: r.get(f) or 0 for f in _DORMANT_FIELDS},
                }
            )
    return pd.DataFrame(rows)


def stage_endpoint_perf(snapshot_date: str) -> pd.DataFrame:
    payload = _read(snapshot_date, "endpoint_stats") or {}
    rows = []
    for permaslug, body in payload.items():
        for e in (body or {}).get("data", []):
            stats = e.get("stats") or {}
            pricing = e.get("pricing") or {}
            rows.append(
                {
                    "snapshot_date": snapshot_date,
                    "endpoint_id": e.get("id"),
                    "model_permaslug": permaslug,
                    "variant": e.get("variant"),
                    "provider_name": e.get("provider_name"),
                    "provider_display_name": e.get("provider_display_name"),
                    "provider_region": e.get("provider_region"),
                    "quantization": e.get("quantization"),
                    "context_length": e.get("context_length"),
                    "capacity_tpm": e.get("capacity_tpm"),
                    "status": e.get("status"),
                    "is_deranked": e.get("is_deranked"),
                    "is_disabled": e.get("is_disabled"),
                    "supports_tools": e.get("supports_tool_parameters"),
                    "supports_reasoning": e.get("supports_reasoning"),
                    "price_prompt": _f(pricing.get("prompt")),
                    "price_completion": _f(pricing.get("completion")),
                    "p50_throughput": stats.get("p50_throughput"),
                    "p75_throughput": stats.get("p75_throughput"),
                    "p90_throughput": stats.get("p90_throughput"),
                    "p99_throughput": stats.get("p99_throughput"),
                    "p50_latency": stats.get("p50_latency"),
                    "p90_latency": stats.get("p90_latency"),
                    "p99_latency": stats.get("p99_latency"),
                    "stat_request_count": stats.get("request_count"),
                    # Carried with the data on purpose: these percentiles cover a
                    # 30-minute rolling window, not the day. Averaging snapshots
                    # without weighting by request_count would be wrong.
                    "window_minutes": stats.get("window_minutes"),
                }
            )
    return pd.DataFrame(rows)


def stage_apps(snapshot_date: str) -> pd.DataFrame:
    payload = _read(snapshot_date, "rankings_apps") or {}
    rows = []
    for window, entries in (payload.get("data") or {}).items():
        for r in entries or []:
            app = r.get("app") or {}
            rows.append(
                {
                    "snapshot_date": snapshot_date,
                    "usage_window": window,
                    "app_id": r.get("app_id"),
                    "rank": r.get("rank"),
                    "total_tokens": int(r.get("total_tokens") or 0),
                    "total_requests": int(r.get("total_requests") or 0),
                    "app_title": app.get("title") or app.get("name"),
                    "app_origin_url": app.get("origin_url") or app.get("main_url"),
                }
            )
    return pd.DataFrame(rows)


_STAGERS = {
    "stg_models": stage_models,
    "stg_model_usage": stage_model_usage,
    "stg_endpoint_perf": stage_endpoint_perf,
    "stg_apps": stage_apps,
}


def build_staging(snapshot_dates: list[str] | None = None) -> dict[str, pd.DataFrame]:
    """Rebuild staging from every completed snapshot.

    Full rebuild rather than incremental append: the whole raw archive is a few
    hundred MB and reprocessing it takes seconds, so there is no reason to carry
    the complexity and drift risk of incremental state.
    """
    dates = snapshot_dates or list_snapshots()
    if not dates:
        raise RuntimeError("no completed snapshots found; run `make ingest` first")

    out: dict[str, pd.DataFrame] = {}
    for name, fn in _STAGERS.items():
        frames = [fn(d) for d in dates]
        frames = [f for f in frames if not f.empty]
        out[name] = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        log.info("%s: %d rows from %d snapshots", name, len(out[name]), len(dates))

    config.STAGING_DIR.mkdir(parents=True, exist_ok=True)
    for name, df in out.items():
        if not df.empty:
            df.to_parquet(config.STAGING_DIR / f"{name}.parquet", index=False)
    return out


# --- marts -----------------------------------------------------------------


def build_marts(staging: dict[str, pd.DataFrame] | None = None) -> duckdb.DuckDBPyConnection:
    """Run the modelling SQL and persist the marts as Parquet."""
    con = duckdb.connect()
    staging = staging or _load_staging()
    for name, df in staging.items():
        con.register(name, df if not df.empty else _empty_like(name))

    con.execute(f"SET VARIABLE pc_ratio_high = {config.PC_RATIO_HIGH}")
    con.execute(f"SET VARIABLE tpr_high = {config.TPR_HIGH}")
    con.execute(f"SET VARIABLE pc_ratio_output_heavy = {config.PC_RATIO_OUTPUT_HEAVY}")
    con.execute(f"SET VARIABLE min_days_momentum = {config.MIN_DAYS_FOR_MOMENTUM}")
    con.execute(
        f"SET VARIABLE min_month_requests = {config.MIN_MONTH_REQUESTS_FOR_MOMENTUM}"
    )
    con.execute(
        "SET VARIABLE min_endpoint_requests = "
        f"{config.MIN_ENDPOINT_REQUESTS_FOR_COMPARISON}"
    )

    con.execute((SQL_DIR / "marts.sql").read_text())

    config.MARTS_DIR.mkdir(parents=True, exist_ok=True)
    for (table,) in con.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_name LIKE 'dim_%' OR table_name LIKE 'fct_%' OR table_name LIKE 'mart_%'"
    ).fetchall():
        path = config.MARTS_DIR / f"{table}.parquet"
        con.execute(f"COPY {table} TO '{path}' (FORMAT PARQUET)")
        log.info("wrote %s", path.name)
    return con


def _load_staging() -> dict[str, pd.DataFrame]:
    out = {}
    for name in _STAGERS:
        path = config.STAGING_DIR / f"{name}.parquet"
        out[name] = pd.read_parquet(path) if path.exists() else pd.DataFrame()
    return out


def _empty_like(name: str) -> pd.DataFrame:
    """Empty staging tables still need their columns so the marts SQL parses."""
    return pd.DataFrame(columns=_EMPTY_COLUMNS[name])


_EMPTY_COLUMNS = {
    "stg_models": [
        "snapshot_date", "model_permaslug", "model_id", "name", "author",
        "context_length", "created_ts", "price_prompt", "price_completion",
        "price_cache_read", "input_modalities", "output_modalities", "tokenizer",
        "is_moderated", "max_completion_tokens", "supports_tools", "supports_reasoning",
    ],
    "stg_model_usage": [
        "snapshot_date", "usage_window", "model_permaslug", "variant", "prompt_tokens",
        "completion_tokens", "requests", "source_last_activity_date", "source_change",
        *_DORMANT_FIELDS,
    ],
    "stg_endpoint_perf": [
        "snapshot_date", "endpoint_id", "model_permaslug", "variant", "provider_name",
        "provider_display_name", "provider_region", "quantization", "context_length",
        "capacity_tpm", "status", "is_deranked", "is_disabled", "supports_tools",
        "supports_reasoning", "price_prompt", "price_completion", "p50_throughput",
        "p75_throughput", "p90_throughput", "p99_throughput", "p50_latency",
        "p90_latency", "p99_latency", "stat_request_count", "window_minutes",
    ],
    "stg_apps": [
        "snapshot_date", "usage_window", "app_id", "rank", "total_tokens",
        "total_requests", "app_title", "app_origin_url",
    ],
}


def load_marts() -> dict[str, pd.DataFrame]:
    out = {}
    for path in sorted(config.MARTS_DIR.glob("*.parquet")):
        out[path.stem] = pd.read_parquet(path)
    return out
