"""Central configuration. No secrets: every endpoint used here is public.

Thresholds are derived in docs/METHODOLOGY.md; the comments here say what a
value is, not why it was chosen.
"""

from __future__ import annotations

import os
from pathlib import Path

BASE_URL = "https://openrouter.ai"

# The frontend endpoints are undocumented. Scraping them anonymously would be
# rude, so the UA carries a URL that reaches the issue tracker.
USER_AGENT = os.environ.get(
    "ORPULSE_USER_AGENT",
    "orpulse/0.1 (+https://github.com/hashd1ve/openrouter-pulse; "
    "public-data research; one capture per day)",
)

# A full sweep is ~365 requests, so 4/s takes ~90s.
REQUESTS_PER_SECOND = float(os.environ.get("ORPULSE_RPS", "4"))
MAX_RETRIES = int(os.environ.get("ORPULSE_MAX_RETRIES", "4"))
TIMEOUT_SECONDS = float(os.environ.get("ORPULSE_TIMEOUT", "30"))

# Each window returns one row per (model, variant) over a trailing period.
# It is not a daily series -- see METHODOLOGY §2.
WINDOWS = ("day", "week", "month")
WINDOW_DAYS = {"day": 1, "week": 7, "month": 30}

_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("ORPULSE_DATA_DIR", _ROOT / "data"))
RAW_DIR = DATA_DIR / "raw"
STAGING_DIR = DATA_DIR / "staging"
MARTS_DIR = DATA_DIR / "marts"
DOCS_DIR = Path(os.environ.get("ORPULSE_DOCS_DIR", _ROOT / "docs"))

# --- Archetype cuts --------------------------------------------------------
# Fitted once against the 2026-07-31 capture and frozen so labels stay
# comparable across snapshots. Density minima, not round numbers.

PC_RATIO_HIGH = 26.6            # trough between modes at 17.1 and 75.9
TPR_HIGH = 18_607.0             # trough between modes at 10,457 and 61,734
PC_RATIO_OUTPUT_HEAVY = 2.0     # semantic cut; no trough, the region is sparse

# --- Reporting floors ------------------------------------------------------
# Below these, the ratios are noise and the metric reports nothing.

MIN_DAYS_FOR_MOMENTUM = 7
MIN_MONTH_REQUESTS_FOR_MOMENTUM = 1_000_000
MIN_ENDPOINT_REQUESTS_FOR_COMPARISON = 100   # p10 of the 30-min window is ~45

# --- Quality-check limits --------------------------------------------------

COVERAGE_TOLERANCE = 0.20       # model-count drift that means a partial failure
MAX_STALENESS_HOURS = 48        # older than this means the cron is dead
