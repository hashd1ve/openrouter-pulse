"""Central configuration. No secrets: every endpoint used here is public."""

from __future__ import annotations

import os
from pathlib import Path

BASE_URL = "https://openrouter.ai"

# Identifiable, contactable User-Agent. These frontend endpoints are undocumented;
# scraping them anonymously and aggressively is both rude and indefensible.
USER_AGENT = os.environ.get(
    "ORPULSE_USER_AGENT",
    "orpulse/0.1 (public-data research project; contact: https://github.com/hashd1ve/openrouter-pulse)",
)

# Conservative pacing. A full endpoint sweep is ~365 requests; at 4/s that is
# ~90s, which is plenty fast for a once-a-day job and gentle on the host.
REQUESTS_PER_SECOND = float(os.environ.get("ORPULSE_RPS", "4"))
MAX_RETRIES = int(os.environ.get("ORPULSE_MAX_RETRIES", "4"))
TIMEOUT_SECONDS = float(os.environ.get("ORPULSE_TIMEOUT", "30"))

# Usage windows exposed by the rankings endpoint. Each returns ONE row per
# (model, variant) aggregated over a trailing window -- not a daily series.
WINDOWS = ("day", "week", "month")

# Nominal length in days of each trailing window, used to convert a window
# aggregate into an average daily rate.
WINDOW_DAYS = {"day": 1, "week": 7, "month": 30}

_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("ORPULSE_DATA_DIR", _ROOT / "data"))
RAW_DIR = DATA_DIR / "raw"
STAGING_DIR = DATA_DIR / "staging"
MARTS_DIR = DATA_DIR / "marts"
DOCS_DIR = Path(os.environ.get("ORPULSE_DOCS_DIR", _ROOT / "docs"))

# --- Analytical thresholds -------------------------------------------------
# Fitted ONCE against the 2026-07-31 snapshot, then frozen. Re-fitting on every
# capture would destroy comparability over time, which is the entire reason for
# preferring declared cuts to clustering. Stability is monitored instead, by
# mart_archetype_stability. See docs/METHODOLOGY.md for the derivation.
#
# Both axes turned out to be genuinely bimodal when weighted by token volume,
# so these are the minima between the two modes, not round numbers:
#   pc_ratio           modes at 17.1 and 75.9  -> trough at 26.6
#   tokens_per_request modes at 10,457 and 61,734 -> trough at 18,607

# pc_ratio: prompt tokens consumed per completion token produced.
PC_RATIO_HIGH = 26.6
# tokens_per_request: size of a single interaction.
TPR_HIGH = 18_607.0
# Below this, a model emits one token for every two it reads. Empirically this
# band is dominated by image-output models rather than by text generation, so it
# is labelled `output_heavy` rather than `generative`. This cut is semantic, not
# fitted: there is no density trough here, the region is simply sparse.
PC_RATIO_OUTPUT_HEAVY = 2.0

# A model must have lived this long for its month-window average to mean anything.
MIN_DAYS_FOR_MOMENTUM = 7
# Below this request count the ratios are noise, not signal.
MIN_MONTH_REQUESTS_FOR_MOMENTUM = 1_000_000

# Endpoint throughput comes from a 30-minute rolling window whose p10 is only
# ~45 requests. Endpoints below this floor are excluded from the dominance
# comparison because their percentiles are noise. The headline is insensitive to
# the exact value (53-55% dominated for any floor from 0 to 1000), which is
# reported rather than hidden.
MIN_ENDPOINT_REQUESTS_FOR_COMPARISON = 100

# Coverage check: a snapshot whose model count deviates more than this from the
# previous one indicates a silent partial failure.
COVERAGE_TOLERANCE = 0.20
# A dataset staler than this means the cron is dead.
MAX_STALENESS_HOURS = 48
