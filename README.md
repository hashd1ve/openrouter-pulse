# OpenRouter Pulse

62 of 497 model-variants on OpenRouter carry 70% of all tokens and 85% of the
money. They aren't more popular. They're doing different work.

This derives that from OpenRouter's public data using two ratios nobody
publishes:

```
pc_ratio           = prompt tokens / completion tokens   → context consumed per token produced
tokens_per_request = total tokens / requests             → size of one interaction
```

Weighted by token volume, both are bimodal. The market isn't a continuum of
usage styles; it's two populations that a leaderboard flattens into one.

[Findings](docs/FINDINGS.md) ·
[Dashboard](https://hashd1ve.github.io/openrouter-pulse/dashboard.html) ·
[Methodology](docs/METHODOLOGY.md)

## Results

**Workloads split in two.** Agentic traffic is 62 model-variants, 70% of tokens,
85% of implied value. The classification cuts sit at the minima of the
token-weighted density, so they're measured, not chosen.

**Money and attention diverge between labs.** By tokens, labs sit at an HHI of
1,061. By implied value: 2,501, past the threshold competition authorities call
highly concentrated. The largest lab takes 45% of the value against 17% of the
tokens. Several high-volume open-weight models round to 0%.

**Sticker price misleads by 3×.** Traffic is prompt-heavy and prompt tokens are
cheaper, so the blended cost is a median 0.32× the headline output price.
Comparing models on `$/M output` gets this wrong.

**Context windows go unused.** The median model touches 2.4% of what it
advertises; even the long-context workloads stay under 10%.

**Price response hides in the weighting.** Count models equally and agentic
elasticity is indistinguishable from zero; weight by requests and it is −0.47
(CI −0.67 to −0.26). The models aren't price-sensitive. The volume is.

**The serving layer has arbitrage.** 53–55% of endpoints are Pareto-dominated.
The same model varies 14× in price between providers. Median p99/p50 latency is
6.4×.

**Free tiers substitute.** Where both tiers exist, 81% of tokens never bill, and
free interactions run larger than paid ones. A funnel would look the opposite.

## Running it

```bash
pip install -e ".[dev]"

make ingest     # one snapshot: ~2 min, ~8 MB, 365 requests at 4/s
make build      # staging, SQL marts, statistical marts, quality checks
make report     # docs/FINDINGS.md
make dashboard  # docs/dashboard.html

make test       # 142 tests, no network
make contract   # 10 more against the live API
```

No API key, database, secrets, or plotting library. `git clone && make build`
reproduces the marts and `FINDINGS.md` byte for byte, which is what CI asserts.
The dashboard is excluded: its vitals panel reports how stale the data is right
now, and a page that reports the current time can't be byte-stable without lying
about it.

## One thing to know before reading the numbers

OpenRouter publishes no history. The rankings endpoint looks like a daily time
series, but it returns one row per model holding a trailing aggregate, and its
`date` column is the model's last day with traffic. Grouping by it produces a
clean, false chart. [Methodology §2](docs/METHODOLOGY.md#2-the-trap-that-shaped-the-design)
has the verification.

So `data/raw/` is the only time series this feed has, and a day not captured is
gone. Hence the daily cron and the append-only archive.

## Layout

```
src/orpulse/
  client.py      HTTP: retries, backoff, rate limiting, failure classification
  ingest.py      immutable snapshots and their provenance manifest
  transform.py   raw → staging (Python flattens JSON) → marts (SQL models)
  sql/marts.sql  the dimensional model and set-based marts
  analytics.py   Kaplan-Meier, HC1 OLS, HHI, Gini
  derive.py      statistical marts, written beside the SQL ones
  quality.py     checks that break the build
  report.py      FINDINGS.md
  charts.py      inline SVG, no dependencies
  dashboard.py   the HTML page
data/raw/        immutable snapshots, committed
data/marts/      derived Parquet, committed so the repo runs without ingesting
```

Four decisions and their reasoning are in
[Methodology §14](docs/METHODOLOGY.md#14-design-decisions): why the archive is
append-only, why archetype cuts are frozen instead of re-fitted, why contract
tests live in their own workflow, and why there's no plotting library.

## Limits

[Methodology §12](docs/METHODOLOGY.md#12-what-this-cannot-tell-you) states them
in full. Briefly: implied value is list price × tokens and therefore an upper
bound, not revenue; endpoint percentiles sample 30 minutes, not a day; the
elasticity is cross-sectional and not causal; the survival curve is preliminary
because the feed truncates at ~30 days of silence; four schema fields are
dormant and nothing is built on them; every series here starts at the first
capture.

---

Built against OpenRouter's public API. Not affiliated with OpenRouter.
