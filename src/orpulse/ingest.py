"""Capture one immutable snapshot of OpenRouter's public state.

Design rules that the rest of the project depends on:

1. ``data/raw/`` is never rewritten by anything downstream. Transformations can
   be re-derived; a snapshot that was not taken is gone forever.
2. The manifest is written **last**. Its absence marks the day as failed, which
   is what makes "no file" and "empty file" mean different things.
3. A partial failure never aborts the sweep, but it is always recorded.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from . import config
from .client import FetchResult, OpenRouterClient, write_gzip_json

log = logging.getLogger(__name__)

MANIFEST_NAME = "_manifest.json"


@dataclass
class RunManifest:
    """The provenance record for one capture.

    Without this, a gap in the series three months from now is indistinguishable
    from a day on which the market genuinely had no traffic.
    """

    snapshot_date: str
    snapshot_ts: str
    started_ts: str
    finished_ts: str | None = None
    duration_seconds: float | None = None
    user_agent: str = config.USER_AGENT
    files: dict[str, int] = field(default_factory=dict)
    requests_ok: int = 0
    requests_failed: int = 0
    bytes_received: int = 0
    failures: list[dict] = field(default_factory=list)
    complete: bool = False

    def record(self, result: FetchResult, label: str | None = None) -> None:
        self.bytes_received += result.bytes_received
        if result.ok:
            self.requests_ok += 1
        else:
            self.requests_failed += 1
            self.failures.append(
                {
                    "label": label or result.path,
                    "path": result.path,
                    "status": result.status,
                    "error": result.error,
                }
            )


def snapshot_dir(snapshot_date: str) -> Path:
    return config.RAW_DIR / snapshot_date


def run(
    client: OpenRouterClient | None = None,
    *,
    now: datetime | None = None,
    sweep_endpoints: bool = True,
    max_models: int | None = None,
) -> RunManifest:
    """Take a full snapshot. Raises if a load-bearing endpoint is unavailable."""
    client = client or OpenRouterClient()
    now = now or datetime.now(timezone.utc)
    snapshot_date = now.date().isoformat()
    out = snapshot_dir(snapshot_date)
    started = time.monotonic()

    manifest = RunManifest(
        snapshot_date=snapshot_date,
        snapshot_ts=now.isoformat(),
        started_ts=now.isoformat(),
    )

    def store(name: str, payload) -> None:
        manifest.files[name] = write_gzip_json(out / f"{name}.json.gz", payload)

    # --- load-bearing endpoints: failure invalidates the run ---------------
    # These raise. A snapshot without the model catalogue or the usage rankings
    # cannot support any downstream analysis, so writing a partial day would be
    # worse than writing nothing.
    log.info("fetching model catalogue")
    models = client.models()
    store("models", models)
    manifest.requests_ok += 1

    for window in config.WINDOWS:
        log.info("fetching usage rankings (window=%s)", window)
        store(f"rankings_models_{window}", client.rankings_models(window))
        manifest.requests_ok += 1

    # --- best-effort endpoints: failure is recorded, not fatal -------------
    apps = client.fetch("/api/frontend/v1/rankings/apps")
    manifest.record(apps, "rankings_apps")
    if apps.ok:
        store("rankings_apps", apps.body)

    providers = client.fetch("/api/v1/providers")
    manifest.record(providers, "providers")
    if providers.ok:
        store("providers", providers.body)

    if sweep_endpoints:
        slugs = [m["canonical_slug"] for m in models.get("data", []) if m.get("canonical_slug")]
        if max_models is not None:
            slugs = slugs[:max_models]
        log.info("sweeping endpoint stats for %d models", len(slugs))
        collected: dict[str, object] = {}
        for i, slug in enumerate(slugs, 1):
            result = client.endpoint_stats(slug)
            manifest.record(result, f"endpoint_stats:{slug}")
            if result.ok:
                collected[slug] = result.body
            if i % 50 == 0:
                log.info("  ... %d/%d", i, len(slugs))
        store("endpoint_stats", collected)

    finished = datetime.now(timezone.utc)
    manifest.finished_ts = finished.isoformat()
    manifest.duration_seconds = round(time.monotonic() - started, 2)
    manifest.complete = True

    # Written last, on purpose: this is the commit point of the snapshot.
    (out / MANIFEST_NAME).write_text(json.dumps(asdict(manifest), indent=2))
    log.info(
        "snapshot %s complete: %d ok, %d failed, %.1f MB in %.0fs",
        snapshot_date,
        manifest.requests_ok,
        manifest.requests_failed,
        manifest.bytes_received / 1e6,
        manifest.duration_seconds,
    )
    return manifest


def list_snapshots() -> list[str]:
    """Dates of snapshots that completed. Incomplete ones are invisible on purpose."""
    if not config.RAW_DIR.exists():
        return []
    dates = []
    for child in sorted(config.RAW_DIR.iterdir()):
        manifest = child / MANIFEST_NAME
        if child.is_dir() and manifest.exists():
            try:
                if json.loads(manifest.read_text()).get("complete"):
                    dates.append(child.name)
            except json.JSONDecodeError:
                log.warning("unreadable manifest in %s; treating as failed", child)
    return dates


def load_manifest(snapshot_date: str) -> dict:
    return json.loads((snapshot_dir(snapshot_date) / MANIFEST_NAME).read_text())
