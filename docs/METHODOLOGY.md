# Methodology

How every number in [FINDINGS.md](FINDINGS.md) is produced, what went wrong on
the way, and what the data can't support.

## 1. Sources

All public and unauthenticated. Two families:

**Documented:** `/api/v1/models`, `/api/v1/models/{author}/{slug}/endpoints`,
`/api/v1/providers`.

**Undocumented:** `/api/frontend/v1/rankings/models`,
`/api/frontend/v1/rankings/apps`, `/api/frontend/v1/stats/endpoint`. These back
openrouter.ai/rankings. They have no contract and can change without notice, so
`tests/test_contract.py` watches them from its own workflow (§14).

Capture runs once a day at 4 requests per second with an identifiable
`User-Agent`. A full sweep is ~365 requests and ~8 MB.

## 2. The trap that shaped the design

The rankings endpoint looks like a daily time series. It has a `date` column and
takes `?view=day|week|month`. Grouping by that column gives a clean chart.

Checking one model across the three views shows why that chart is wrong:

| `view` | prompt tokens | requests |
|---|---|---|
| `day` | 1.09 T | 107 M |
| `week` | 7.08 T | 706 M |
| `month` | 23.95 T | 2,358 M |

The endpoint returns one row per (model, variant) holding a trailing aggregate.
The `date` column is the model's last day with traffic, which is why `view=month`
returns rows dated weeks back for dormant models and 437 rows dated yesterday for
everything else.

Three consequences run through the whole project:

1. No public history exists. Every series here starts at the first capture, which
   makes the snapshot archive the only irreplaceable thing in the repository.
2. The nested windows still allow a trend from a single capture (§4).
3. Staging renames the field to `source_last_activity_date` and keys facts on the
   capture date, so the mistake can't propagate downstream.

A quality check now enforces `day ≤ week ≤ month` on every build. It's a semantic
invariant, not a schema check, and it would have caught this in an afternoon.

## 3. The workload fingerprint

```
pc_ratio           = total_prompt_tokens / total_completion_tokens
tokens_per_request = (total_prompt_tokens + total_completion_tokens) / requests
```

`pc_ratio` measures context consumed per token produced. `tokens_per_request`
measures interaction size. Neither is published; both fall out of fields that
are.

### Where the cuts come from

Fitted once against the 2026-07-31 capture. Both axes are bimodal when density is
weighted by token volume, so the cuts are the minima between modes:

| Axis | Mode 1 | Mode 2 | Trough → cut |
|---|---|---|---|
| `pc_ratio` | 17.1 | 75.9 | **26.6** |
| `tokens_per_request` | 10,457 | 61,734 | **18,607** |

That bimodality is itself the finding: two populations, not a continuum.

A third cut, `pc_ratio < 2` → `output_heavy`, is semantic. No trough exists
there; the region is sparse. Inspecting it showed image-output models
(`seedream`, `gemini-flash-image`, `gpt-image`) rather than text generation,
which is why the label isn't `generative` as originally planned.

### Sensitivity

The headline doesn't hinge on the exact cut:

| `pc_ratio` cut | Agentic models | Share of tokens |
|---|---|---|
| 20 | 57 | 70.8% |
| 25 | 54 | 70.2% |
| **26.6** | 54 | 70.2% |
| 30 | 50 | 68.9% |
| 35 | 45 | 63.3% |
| 40 | 41 | 62.6% |

### Why both axes

The highest `pc_ratio` in the dataset is `meta-llama/llama-guard-4-12b` at 195:1,
a safety classifier. It reads far more than it writes, like an agent, but its
interactions average 726 tokens against `nemotron-3-ultra`'s 103,590. One axis
can't separate them.

## 4. Momentum

```
effective_days = min(30, days since launch)
avg_daily      = month_tokens / effective_days
momentum       = day_tokens / avg_daily
```

Without the age correction the denominator divides by 30 days for a model four
days old. Recent launches then show explosive growth as an arithmetic artefact,
and the analysis "discovers" that new models grow. Measured: for model-variants
under 30 days old, the uncorrected formula inflates momentum by a median 1.36×.

A model is *ratable* only if all three hold:

| Condition | Reason |
|---|---|
| Launch date known | 144 model-variants (mostly embedding models absent from `/api/v1/models`) have no `created`. Defaulting them to 30 days publishes an uncorrected number as a corrected one. They're 1.75% of tokens. |
| At least 7 days old | Below that the 30-day window is mostly empty. |
| At least 1 M monthly requests | Below that the ratio is noise. The unfiltered extremes (0.00× and 12.07×) are all residual-traffic models. |

Everything else reports "not ratable" instead of a number.

Across 233 ratable model-variants: median 0.97, p25–p75 0.73–1.20. A median near
1.0 is what a market neither collapsing nor exploding looks like, which is a weak
sanity check on the construction.

## 5. Provider endpoints

An endpoint is *dominated* when another serving the same model is both cheaper
per completion token and faster at the median, and strictly better on at least
one axis. Result: 53–55% of compared endpoints.

Two constraints:

**The percentiles sample 30 minutes.** `window_minutes` is 30 in every response,
so a daily capture measures half an hour. The column travels with the data and
the marts never average across snapshots without weighting by
`stat_request_count`. A single capture indicates where to look and settles
nothing.

**Low-volume endpoints are excluded.** The p10 of `stat_request_count` is 45
requests. Endpoints below 100 are dropped. The headline is insensitive: 53–55%
for any floor between 0 and 1,000.

## 6. Dormant fields

`total_native_tokens_cached`, `total_native_tokens_reasoning`,
`total_tool_calls` and `requests_with_tool_call_errors` appear in every rankings
response and are zero for all 446 models. They're ingested so the archive already
holds them if that changes, and no analysis rests on them. A contract test
asserts they're still dormant; that test failing is good news.

## 7. Implied gross value

```
implied_gross_value = prompt_tokens × price_prompt + completion_tokens × price_completion
```

This isn't revenue, and the column name says so. It uses headline prices and
ignores prompt-cache discounts, batch pricing, BYOK traffic, negotiated rates and
OpenRouter's margin. It's an upper bound on the economic weight of a model's
traffic. Calling it `revenue` anywhere would invite readers to forget that.

Models without a published price are excluded, not zeroed. An unknown price
isn't zero, and 144 of 497 model-variants would otherwise drag the total down
silently.

### Blended versus sticker

Traffic is prompt-heavy and prompt tokens cost less than completions, so the
price actually paid per token sits well below the headline output price:

```
blended_price_per_token  = implied_gross_value / total_tokens
blended_to_sticker_ratio = blended_price_per_token / price_completion
```

Median 0.32, so the sticker overstates unit cost by about 3.1×. It varies by
model because the P:C mix does.

## 8. Concentration

Three measures, each hiding something the others show:

- **HHI** on the 0–10,000 scale competition authorities use. Above 2,500 is
  conventionally "highly concentrated".
- **Gini**, insensitive to how mass splits among leaders, sensitive to the tail.
- **Top-N share**, which a non-specialist reads correctly.

Each is computed over four bases: tokens by model, value by model, tokens by lab,
value by lab. The choice of base *is* the finding. By tokens the labs look
moderately concentrated at HHI ≈ 1,061; by money they cross 2,500. A single
number would hide that.

## 9. Context-window utilisation

```
mean_window_utilisation = tokens_per_request / context_length
```

`tokens_per_request` is a mean over the month, so a model whose median request is
small but which occasionally fills a million-token window still reads low. The
metric bounds typical usage, not peak capability, and is named accordingly.

## 10. Price elasticity

Log tokens on log price with HC1 heteroskedasticity-robust standard errors. Token
volume spans nine orders of magnitude; classical errors would claim confidence
the data can't support.

Two weightings answer different questions. Unweighted treats every model as one
observation. Request-weighted follows the traffic.

### A statistical bug that had to be fixed

Weighted least squares scales both sides by √w. The R² falling out of that fit is
computed on the scaled response, whose total sum of squares is dominated by the
spread of the weights, and it came out at 0.99 for every segment. Recomputed on
the original scale against the weighted mean:

```
R²_w = 1 − Σ w(y − ŷ)² / Σ w(y − ȳ_w)²
```

The same regressions then report 0.007 to 0.367.
`tests/test_analytics.py::test_weighted_r_squared_is_not_inflated_by_the_weights`
asserts that deliberately noisy input can't produce a high weighted R².

### What the estimate isn't

Not causal. It's a cross-section of different models at different prices, not one
model at several prices, so it absorbs everything that makes cheap models cheap:
smaller, weaker, newer. A steep slope fits "buyers chase cheap tokens" as well as
"cheap models are built for bulk work".

Differences *between* archetypes carry more than any single coefficient, and the
headline result is one of those: agentic elasticity is indistinguishable from
zero unweighted and clearly negative request-weighted. Agentic models aren't
price-sensitive; agentic volume is.

## 11. Survival analysis

Kaplan-Meier product-limit estimator with right-censoring and Greenwood variance.
The confidence band uses the log-log transform, which keeps the interval inside
[0, 1]; the plain Greenwood interval routinely produces bounds above 1 near the
tail.

Implemented directly rather than imported, and verified: it reproduces the
published survival curve of the Freireich leukemia trial (6-MP arm) to within
5×10⁻⁴ at every event time and recovers its published median of 23 weeks.

### Why the application is preliminary

Death has to be inferred from `source_last_activity_date`, and two biases pull
against each other:

1. **Right truncation.** A model silent for more than ~30 days leaves the monthly
   window entirely, so long-dead models are absent from the sample. Every subject
   is conditioned on recent presence, biasing survival up. The tell is in the
   sensitivity table: at a 14-day threshold there's essentially one event, and at
   30 days none. That's a property of the feed, not the market.
2. **Resurrection.** At a 2-day threshold, a model that had a quiet Tuesday is
   booked as dead, biasing survival down.

Their relative sizes are unknown, so the curve is published as a demonstration of
method with the sensitivity across thresholds shown instead of a single number.

The fix costs only time. Once the archive holds several weeks of captures, death
is observed (present on day N, absent on day N+k) instead of inferred from a
truncated field. The estimator doesn't change; its input stops being biased.

## 12. What this cannot tell you

- **Traffic isn't users.** One agentic application can outproduce a million chat
  sessions. Nothing here measures adoption, revenue or satisfaction.
- **Model-variants aren't models.** The same model appears under `standard`,
  `free`, `batch` and `thinking`; they're counted separately because they behave
  differently.
- **Archetypes are inferred from aggregate shape**, not from observing what
  applications do. A model split evenly between agents and chat lands in between
  and is labelled by whichever dominates.
- **Boundary models will flip** between captures. `mart_archetype_stability`
  measures how often, rather than assuming it away.
- **A capture is a point in time.** OpenRouter may revise figures retroactively.
  Detecting that is possible from the archive but out of scope for now.

## 13. Reproducing any figure

```bash
make build      # staging, SQL marts, statistical marts, quality checks
make report     # docs/FINDINGS.md
make dashboard  # docs/dashboard.html
```

Every published number is read from `data/marts/*.parquet`, derived from
`data/raw/` by committed SQL. Nothing in `FINDINGS.md` is typed by hand, and CI
fails if the committed report drifts from what the data produces.

## 14. Design decisions

**The archive is append-only.** `data/raw/` is never rewritten. Transformations
can be re-derived; a snapshot not taken is gone. If the modelling changes,
staging and marts rebuild from raw without touching the network.

**The manifest is the commit point.** It's written last, and its absence marks a
day as failed. That's what makes "no file" and "empty file" mean different
things. Without it, a gap in the series three months from now is
indistinguishable from a day with no traffic.

**Archetype cuts are frozen, not re-fitted.** k-means over two axes with ~400
points yields clusters whose identity drifts between runs, and a cluster that
means something different each day is useless in a time series. The cuts are
fitted once against the observed density minima and their stability is measured.

**SQL models sets; Python runs estimators.** Set-based work belongs in reviewable
SQL. Survival with censoring and robust regression don't, so they live in
`analytics.py` and are written out as marts beside the rest.

**Contract tests get their own workflow.** This reads undocumented endpoints. If
those assertions lived in the normal suite, an upstream change would redden every
pull request for reasons no contributor could fix, and they'd get disabled.
Isolated, a red run there means one thing.

**No plotting library.** The dashboard is one HTML file with inline SVG. It opens
anywhere, survives a strict content-security policy, and has no runtime
dependency to rot.
