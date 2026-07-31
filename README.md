# OpenRouter Pulse

**62 of 497 model-variants on OpenRouter carry 70% of all tokens — not because
they are more popular, but because they are doing a different kind of work.**

This repository derives that from OpenRouter's public data, using two ratios
nobody publishes:

```
pc_ratio           = prompt tokens / completion tokens   -- context consumed per token produced
tokens_per_request = total tokens / requests             -- size of one interaction
```

Both axes turn out to be **genuinely bimodal** when weighted by token volume.
The market is not a continuum of usage styles; it is two populations that a
leaderboard flattens into one.

📊 **[Findings](docs/FINDINGS.md)** · 🔬 **[Methodology](docs/METHODOLOGY.md)** ·
📐 **[Design](docs/superpowers/specs/2026-07-31-openrouter-workload-fingerprint-design.md)**

---

## What is here

| | |
|---|---|
| **Ingestion** | Daily immutable snapshots with a per-run provenance manifest, retry/backoff, and partial-failure tolerance |
| **Modelling** | DuckDB + Parquet: SCD-2 dimensions, snapshot facts, analytical marts — all in reviewable SQL |
| **Validation** | Six quality checks that break the build, including a semantic invariant on the API's own window nesting |
| **Analysis** | Workload archetypes, age-corrected momentum, Pareto-dominated provider endpoints |
| **Tests** | 73 tests at three levels: unit (frozen fixtures), contract (live API, isolated), quality (on the marts) |
| **Dashboard** | Streamlit, with a colourblind-validated palette and a table view for the contrast-relief case |
| **CI** | Daily capture, test suite, and an independent upstream-contract alarm |

## Quick start

```bash
pip install -e ".[app,dev]"

make ingest    # capture one snapshot (~2 min, ~8 MB, 365 requests at 4/s)
make build     # rebuild staging + marts from raw, run quality checks
make report    # regenerate docs/FINDINGS.md from the marts
make app       # open the dashboard

make test      # unit + mart + dashboard tests, no network
make contract  # verify the upstream API still matches expectations
```

No API key, no database, no secrets. `git clone && make build` reproduces every
published figure from the committed snapshots.

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

**Contract tests are isolated on purpose.** This project reads undocumented
endpoints. If those assertions lived in the normal suite, an upstream change
would redden every pull request for reasons no contributor could fix, and the
tests would get disabled. Alone, a red run there means exactly one thing.

**Scraping is polite.** One capture per day, 4 requests per second, identifiable
`User-Agent` with a contact address.

---

## Repository layout

```
src/orpulse/
  client.py      HTTP: retries, backoff with jitter, rate limiting, failure classification
  ingest.py      immutable snapshots + provenance manifest
  transform.py   raw -> staging (Python flattens JSON) -> marts (SQL models)
  sql/marts.sql  the dimensional model
  quality.py     checks that break the build
  report.py      regenerates FINDINGS.md from the marts
app/             Streamlit dashboard
tests/           unit · contract · quality · dashboard
data/raw/        immutable snapshots (committed: the irreplaceable artefact)
data/marts/      derived Parquet (committed: makes the repo runnable without ingesting)
```

## Limitations

Stated in full in [METHODOLOGY.md](docs/METHODOLOGY.md#7-what-this-cannot-tell-you).
The short version: traffic is not users, endpoint percentiles are a 30-minute
sample rather than a daily aggregate, four schema fields are dormant and nothing
is built on them, and every time series here begins on the day of the first
capture.

---

*Built against OpenRouter's public API. Not affiliated with OpenRouter.*
