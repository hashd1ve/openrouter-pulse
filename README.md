# OpenRouter Pulse

**62 of 497 model-variants on OpenRouter carry 70% of all tokens and 85% of the
money.** They are not more popular — they are doing a different kind of work,
and it is worth measuring which.

This repository derives that from OpenRouter's public data, using two ratios
nobody publishes:

```
pc_ratio           = prompt tokens / completion tokens   -- context consumed per token produced
tokens_per_request = total tokens / requests             -- size of one interaction
```

Both axes turn out to be **genuinely bimodal** when weighted by token volume.
The market is not a continuum of usage styles; it is two populations that a
leaderboard flattens into one.

📊 **[Findings](docs/FINDINGS.md)** · 🖥 **[Dashboard](docs/dashboard.html)** ·
🔬 **[Methodology](docs/METHODOLOGY.md)** ·
📐 **[Design](docs/superpowers/specs/2026-07-31-openrouter-workload-fingerprint-design.md)**

---

## What it found

| | |
|---|---|
| **Workloads split in two** | Agentic traffic is 62 of 497 model-variants, 70% of tokens and 85% of implied value. The cuts sit at the density minima between two modes — measured, not chosen. |
| **Money ≠ attention, at the lab level** | By tokens, labs sit at an HHI of 1,061. By implied value: **2,501**, past the threshold competition authorities call highly concentrated. One lab takes 45% of the value against 17% of the tokens, while several high-volume open-weight models round to 0% of it. |
| **The sticker price is not the price** | Traffic is prompt-heavy and prompt tokens are cheaper, so the blended cost is a median **0.32×** the headline output price. Anyone comparing models on `$/M output` is off by ~3×. |
| **The context arms race is unused** | Median model touches **2.4%** of its advertised window. Even agentic traffic — the workload that exists *because* of long context — uses under a tenth. |
| **Price response hides in the weighting** | Agentic elasticity is indistinguishable from zero counting models equally, and **−0.47 (CI −0.67 to −0.26)** weighted by requests. Agentic *models* are not price-sensitive; agentic *volume* is. |
| **Serving-layer arbitrage** | 53–55% of endpoints are Pareto-dominated. The same model varies **14×** in price between providers. Median p99/p50 latency is 6.4×. |
| **Free tiers substitute, not funnel** | Where both tiers exist, 81% of tokens never bill — and free interactions are *larger* than paid ones. |

## What is here

| | |
|---|---|
| **Ingestion** | Daily immutable snapshots with a per-run provenance manifest, retry/backoff with jitter, partial-failure tolerance |
| **Modelling** | DuckDB + Parquet: SCD-2 dimensions, snapshot facts, 13 marts — all in reviewable SQL |
| **Statistics** | Kaplan-Meier with censoring and Greenwood variance, OLS with HC1 robust errors, HHI/Gini — hand-rolled and verified against published results |
| **Validation** | Six quality checks that break the build, including a semantic invariant on the API's own window nesting |
| **Tests** | 152 across five levels: unit, marts, statistics, charts/page, and live-API contract (isolated) |
| **Dashboard** | One self-contained HTML file — no server, no CDN, no JavaScript. Inline SVG, colourblind-validated palette, light and dark |
| **CI** | Daily capture, test suite, and an independent upstream-contract alarm |

## Quick start

```bash
pip install -e ".[dev]"

make ingest     # capture one snapshot (~2 min, ~8 MB, 365 requests at 4/s)
make build      # staging + SQL marts + statistical marts, with quality checks
make report     # regenerate docs/FINDINGS.md
make dashboard  # regenerate docs/dashboard.html

make test       # 142 tests, no network (plus 10 contract tests)
make contract   # verify the upstream API still matches expectations
```

No API key, no database, no secrets, no plotting library. `git clone && make
build` reproduces every published figure from the committed snapshots — the
marts and `FINDINGS.md` byte for byte, which is what CI asserts. The dashboard
is deliberately excluded from that check: its vitals panel reports how stale the
data is *right now*, and a page that reports the current time cannot be
byte-stable without lying about it.

---

## The one thing worth knowing before you read the numbers

**OpenRouter publishes no history.** The rankings endpoint looks like a daily
time series — it has a `date` column and a `view=day|week|month` parameter — but
it returns *one row per model holding a trailing aggregate*, and the `date` is
the model's last day with traffic, not a time index.

Verified across the three views for a single model:

| `view` | prompt tokens | requests |
|---|---|---|
| `day` | 1.09 T | 107 M |
| `week` | 7.08 T | 706 M |
| `month` | 23.95 T | 2,358 M |

Grouping by `date` produces a convincing and entirely false chart.

Two things follow. First, `data/raw/` is the only time series that exists for
this feed, so a day not captured is a day lost permanently — hence the daily
cron and the append-only archive. Second, because the windows are *nested*, a
trend can still be derived from a single capture, which is what the momentum
metric does.

A quality check now enforces `day ≤ week ≤ month` on every build. It is a
semantic invariant rather than a schema check, and it is precisely the assertion
that catches this class of misreading.

---

## Design notes

**Raw is never rewritten.** Transformations can be re-derived; a snapshot not
taken is gone. If the modelling changes, staging and marts rebuild from `raw`
without touching the network.

**The manifest is the commit point.** It is written last, and its absence marks
a day as failed. This is what makes "no file" and "empty file" mean different
things — without it, a gap in the series three months from now is
indistinguishable from a day with no traffic.

**Thresholds are declared, not clustered.** k-means over two axes with ~400
points yields clusters whose identity drifts between runs, and a cluster that
means something different each day is useless in a time series. The cuts are
fitted once against the observed density minima, frozen, and their stability is
*measured* rather than assumed — see `mart_archetype_stability`.

**SQL for sets, Python for estimators.** Set-based modelling belongs in
reviewable SQL. Survival with censoring and robust regression do not, so they
live in `analytics.py` and are materialised as marts alongside the rest — a
consumer cannot tell which engine produced which table.

**Statistics are verified, not trusted.** The Kaplan-Meier implementation
reproduces the published curve of the Freireich leukemia trial to 5×10⁻⁴ at
every event time. The robust covariance is checked against the HC1 formula
computed independently in the test.

**Contract tests are isolated on purpose.** This project reads undocumented
endpoints. If those assertions lived in the normal suite, an upstream change
would redden every pull request for reasons no contributor could fix, and the
tests would get disabled. Alone, a red run there means exactly one thing.

**No plotting library.** The dashboard is one HTML file with inline SVG: it
opens anywhere, survives a strict content-security policy, and has no runtime
dependency to rot.

**Scraping is polite.** One capture per day, 4 requests per second, identifiable
`User-Agent` with a contact address.

---

## Repository layout

```
src/orpulse/
  client.py      HTTP: retries, backoff with jitter, rate limiting, failure classification
  ingest.py      immutable snapshots + provenance manifest
  transform.py   raw -> staging (Python flattens JSON) -> marts (SQL models)
  sql/marts.sql  the dimensional model and the set-based marts
  analytics.py   Kaplan-Meier, HC1 OLS, HHI, Gini — verified estimators
  derive.py      statistical marts, materialised beside the SQL ones
  quality.py     checks that break the build
  report.py      regenerates FINDINGS.md from the marts
  charts.py      inline SVG, no dependencies
  dashboard.py   the self-contained HTML page
tests/           unit · marts · statistics · charts/page · contract
data/raw/        immutable snapshots (committed: the irreplaceable artefact)
data/marts/      derived Parquet (committed: makes the repo runnable without ingesting)
```

## Limitations

Stated in full in [METHODOLOGY.md](docs/METHODOLOGY.md#12-what-this-cannot-tell-you).
The short version: implied value is list price × tokens and therefore an upper
bound, not revenue; endpoint percentiles are a 30-minute sample rather than a
daily aggregate; the elasticity is a cross-section and not causal; the survival
curve is preliminary because the feed truncates at ~30 days of silence; four
schema fields are dormant and nothing is built on them; and every time series
here begins on the day of the first capture.

---

*Built against OpenRouter's public API. Not affiliated with OpenRouter.*
