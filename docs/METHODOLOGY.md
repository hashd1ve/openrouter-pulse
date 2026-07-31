# Methodology

How every number in [FINDINGS.md](FINDINGS.md) is produced, which traps were
found on the way, and what the data cannot support.

---

## 1. Sources

Everything is unauthenticated public data. Two families:

**Documented and stable** — `/api/v1/models`, `/api/v1/models/{author}/{slug}/endpoints`,
`/api/v1/providers`.

**Undocumented** — `/api/frontend/v1/rankings/models`, `/api/frontend/v1/rankings/apps`,
`/api/frontend/v1/stats/endpoint`. These are what openrouter.ai/rankings calls.
They have no contract and can change without notice, which is why
`tests/test_contract.py` exists as a standalone alarm rather than as part of the
normal suite.

Capture is once per day, paced at 4 requests per second, with an identifiable
`User-Agent` carrying a contact address. A full sweep is about 365 requests and
8 MB.

---

## 2. The trap that shaped the whole design

The rankings endpoint looked like a daily time series. It has a `date` column
and accepts `?view=day|week|month`. Grouping by that column produces a clean,
convincing chart.

It is wrong. Checking the same model across the three views:

| `view` | prompt tokens | requests |
|---|---|---|
| `day` | 1.09 T | 107 M |
| `week` | 7.08 T | 706 M |
| `month` | 23.95 T | 2,358 M |

The endpoint returns **one row per (model, variant)** holding a trailing
aggregate. The `date` column is the model's **last day with traffic** — which is
why `view=month` returns rows dated weeks back for models that went dormant, and
437 rows dated yesterday for everything still alive.

Consequences:

1. **No public history exists.** Every time series in this repository starts on
   the day of the first capture. That makes the snapshot archive the project's
   only irreplaceable asset.
2. The nested windows allow a trend to be derived from a single capture (§4).
3. The staging model renames the field to `source_last_activity_date` and uses
   the capture date as the fact's time key, so the mistake cannot be repeated
   downstream by accident.

A data-quality check now enforces `day ≤ week ≤ month` on every build. It is a
*semantic* invariant, not a schema check, and it is the assertion that would
have caught this in an afternoon.

---

## 3. The workload fingerprint

Two ratios computed over the trailing 30-day window:

```
pc_ratio           = total_prompt_tokens / total_completion_tokens
tokens_per_request = (total_prompt_tokens + total_completion_tokens) / requests
```

`pc_ratio` measures how much context a model consumes per token it produces.
`tokens_per_request` measures the size of one interaction. Neither is published;
both fall out of fields that are.

### Why fixed cuts rather than clustering

k-means over two axes with ~400 points produces clusters whose identity drifts
between runs. A cluster that means something different each day is useless in a
time series, and the entire point of the archive is comparability over time. So
the cuts are **fitted once, frozen, and monitored** — `mart_archetype_stability`
measures the share of models that change archetype between consecutive captures,
which is the question that actually matters.

### Where the cuts come from

Fitted against the 2026-07-31 capture. Both axes turned out to be genuinely
bimodal when the density is weighted by token volume, so the cuts are the minima
between the modes, not round numbers:

| Axis | Mode 1 | Mode 2 | Trough → cut |
|---|---|---|---|
| `pc_ratio` | 17.1 | 75.9 | **26.6** |
| `tokens_per_request` | 10,457 | 61,734 | **18,607** |

That bimodality is itself the finding: the market is not a continuum of usage
styles, it is two populations.

The third cut, `pc_ratio < 2` → `output_heavy`, is **semantic, not fitted**.
There is no trough there; the region is simply sparse. Inspecting it showed it
is dominated by image-output models (`seedream`, `gemini-flash-image`,
`gpt-image`), not by text generation — which is why the label is `output_heavy`
rather than the `generative` it was originally going to be called.

### Sensitivity

The headline does not hinge on the exact cut:

| `pc_ratio` cut | Agentic models | Share of tokens |
|---|---|---|
| 20 | 57 | 70.8% |
| 25 | 54 | 70.2% |
| **26.6** | 54 | 70.2% |
| 30 | 50 | 68.9% |
| 35 | 45 | 63.3% |
| 40 | 41 | 62.6% |

### Why both axes are needed

The single highest `pc_ratio` in the dataset is `meta-llama/llama-guard-4-12b`
at 195:1 — a safety classifier, not an agent. It reads far more than it writes,
like an agent does, but its interactions average 726 tokens against
`nemotron-3-ultra`'s 103,590. One axis cannot separate them; their conjunction
can.

---

## 4. Momentum

```
effective_days = min(30, days since the model launched)
avg_daily      = month_tokens / effective_days
momentum       = day_tokens / avg_daily
```

### The age correction is not optional

Without it the denominator divides by 30 days for a model that has existed for
four. Every recent launch then shows explosive growth as a pure artefact, and
the analysis "discovers" that new models grow — a tautology wearing a result's
clothes.

Measured: for model-variants younger than 30 days, the uncorrected formula
inflates momentum by a median factor of **1.36×**.

### Exclusions, and why they are exclusions rather than estimates

A model is *ratable* only if all three hold:

| Condition | Reason |
|---|---|
| Launch date is **known** | 144 model-variants (mostly embedding models, absent from `/api/v1/models`) have no `created`. Defaulting them to 30 days would publish an uncorrected number as if it were corrected. They are 1.75% of tokens. |
| At least 7 days old | Below that the 30-day window is mostly empty and the ratio is meaningless. |
| At least 1 M monthly requests | Below that the ratio is noise. The extremes of the unfiltered list (0.00× and 12.07×) are all residual-traffic models. |

Everything else is reported as "not ratable" rather than given a number.

Observed distribution across 233 ratable model-variants: median **0.97**,
p25–p75 **0.73–1.20**. A median near 1.0 is what a market neither collapsing nor
exploding should look like, which is a weak but real sanity check on the whole
construction.

---

## 5. Provider endpoints (secondary)

An endpoint is *dominated* when another endpoint for the same model is both
cheaper per completion token and faster at the median, and strictly better on at
least one axis. Result: **53–55% of compared endpoints are dominated.**

Two caveats that constrain how far this can be pushed:

**The percentiles are a 30-minute sample.** `window_minutes` is 30 in every
response. A daily capture measures half an hour of that day, not the day. The
column travels with the data, and the mart never averages across snapshots
without weighting by `stat_request_count`. A single capture indicates where to
look; it does not settle anything.

**Low-volume endpoints are excluded.** The p10 of `stat_request_count` is 45
requests — percentiles over that are noise. Endpoints below 100 requests in the
window are dropped. The headline is insensitive to this: the dominated share is
53–55% for any floor between 0 and 1,000.

---

## 6. Fields that exist but are empty

`total_native_tokens_cached`, `total_native_tokens_reasoning`,
`total_tool_calls` and `requests_with_tool_call_errors` are present in every
rankings response and are **zero for all 446 models**. They are ingested anyway,
so that the archive already contains them if OpenRouter starts populating them.

No analysis rests on them. `test_contract.py` asserts they are still dormant;
that test failing is good news, not a regression.

---

## 7. Implied gross value

```
implied_gross_value = prompt_tokens × price_prompt + completion_tokens × price_completion
```

**It is not revenue, and the column name says so.** It uses each model's
headline price and therefore ignores prompt-cache discounts, batch pricing, BYOK
traffic, negotiated rates and OpenRouter's own margin. It is an upper bound on
the economic weight of a model's traffic. Calling it `revenue` anywhere would
have invited every downstream reader to forget that, so it is called
`implied_gross_value` in the SQL, in the Parquet, and in the report.

Models without a published price are **excluded, not zeroed**: an unknown price
is not a price of zero, and 144 of 497 model-variants would otherwise silently
drag the total down.

### The blended-versus-sticker ratio

Traffic is overwhelmingly prompt-heavy, and prompt tokens cost less than
completions. So the price a buyer actually pays per token, blended across their
real mix, sits well below the headline output price:

```
blended_price_per_token   = implied_gross_value / total_tokens
blended_to_sticker_ratio  = blended_price_per_token / price_completion
```

Median observed: **0.32**, i.e. the sticker overstates the true unit cost by
about 3.1×. This is the number a buyer comparing models on `$/M output` is
getting wrong, and it varies by model precisely because the P:C mix does.

## 8. Concentration

Three measures, because each hides something the others show:

- **HHI**, on the 0–10,000 scale competition authorities use. Above 2,500 is
  conventionally "highly concentrated".
- **Gini**, which is insensitive to how the mass is split among the leaders but
  sensitive to the long tail.
- **Top-N share**, which is the one a non-specialist reads correctly.

Each is computed over four different bases — tokens by model, value by model,
tokens by lab, value by lab — because *the choice of base is the finding*. By
tokens the labs look moderately concentrated (HHI ≈ 1,061); by money they cross
2,500. A single concentration number would have hidden exactly the thing worth
reporting.

## 9. Context-window utilisation

```
mean_window_utilisation = tokens_per_request / context_length
```

The asymmetry matters: `tokens_per_request` is a **mean over the month**, so a
model whose median request is small but which occasionally fills a million-token
window still reads low. The metric bounds *typical* usage, not peak capability,
and the column is named `mean_window_utilisation` rather than `window_usage` for
that reason.

## 10. Price elasticity

Log tokens regressed on log price with **HC1 heteroskedasticity-robust** standard
errors. Robust rather than classical because token volume spans nine orders of
magnitude; classical errors would report confidence the data cannot support.

Two weightings are reported side by side because they answer different questions:
unweighted treats every model as one observation; request-weighted follows where
the traffic actually is.

### A statistical trap that had to be fixed

Weighted least squares here is done by scaling both sides by √w. The R² that
falls out of that fit is computed on the *scaled* response, whose total sum of
squares is dominated by the spread of the weights rather than by the
relationship — it came out at 0.99 for every segment, which is meaningless. It
is recomputed on the original scale against the **weighted mean**:

```
R²_w = 1 − Σ w(y − ŷ)² / Σ w(y − ȳ_w)²
```

After the fix the same regressions report 0.007 to 0.367, which is what the data
actually supports. `tests/test_analytics.py` asserts that deliberately noisy
input cannot produce a high weighted R².

### What the estimate is not

**Not causal.** It is a cross-section of different models at different prices,
not one model observed at several prices, so it absorbs everything that makes
cheap models cheap — smaller, weaker, newer. A steep slope is as consistent with
"buyers chase cheap tokens" as with "cheap models are the ones built for bulk
work". The differences *between* archetypes carry more than any single
coefficient, and the headline result is one of those differences: agentic
elasticity is indistinguishable from zero unweighted and clearly negative
request-weighted. Agentic models are not price-sensitive; agentic volume is.

## 11. Survival analysis

Kaplan-Meier product-limit estimator with right-censoring and Greenwood
variance; the confidence band uses the **log-log transform**, which keeps the
interval inside [0, 1] where the plain Greenwood interval routinely produces
bounds above 1 near the tail.

Implemented directly rather than imported. The verification is the point: the
implementation reproduces the published survival curve of the Freireich
leukemia trial (6-MP arm) to within 5 × 10⁻⁴ at every event time, and recovers
its published median of 23 weeks.

### Why the application is preliminary even though the estimator is not

Death has to be *inferred* from `source_last_activity_date`, and two biases pull
in opposite directions:

1. **Right truncation.** A model silent for more than ~30 days leaves the
   monthly window entirely, so long-dead models are absent from the sample
   altogether. Every subject is conditioned on recent presence, biasing survival
   **up**. The tell is in the sensitivity table: at a 14-day threshold there is
   essentially one event, and at 30 days none — a property of the feed, not of
   the market.
2. **Resurrection.** At a 2-day threshold, a model that merely had a quiet
   Tuesday is booked as dead, biasing survival **down**.

Their relative magnitudes are unknown, so the curve is published as a
demonstration of method rather than as a finding, with the sensitivity across
thresholds shown rather than a single number.

**What fixes it costs nothing but time.** Once the archive holds several weeks
of captures, death is *observed* — present on day N, absent on day N+k — instead
of inferred from a truncated field. The estimator does not change; its input
stops being biased.

## 12. What this cannot tell you

- **Traffic is not users.** One agentic application can outproduce a million
  chat sessions. Nothing here measures adoption, revenue, or satisfaction.
- **Model-variants are not models.** The same model appears under `standard`,
  `free`, `batch` and `thinking` variants; they are counted separately because
  they behave differently.
- **The archetype is inferred from aggregate shape**, not from observing what
  applications actually do. A model whose traffic is evenly split between agents
  and chat lands somewhere in between and is labelled by whichever dominates.
- **Boundary models will flip** between captures. That is measured, not assumed
  away — see `mart_archetype_stability`.
- **A capture is a point in time.** OpenRouter may revise figures retroactively;
  detecting that is possible from the archive but deliberately out of scope for
  now.

---

## 13. Reproducing any figure

```bash
make build      # rebuilds staging + SQL marts + statistical marts, runs quality checks
make report     # regenerates FINDINGS.md from the marts
make dashboard  # regenerates the self-contained HTML dashboard from the same marts
```

Every published number is read from `data/marts/*.parquet`, which are derived
from `data/raw/` by committed SQL. Nothing in `FINDINGS.md` is typed by hand,
and CI fails if the committed report drifts from what the data produces.
