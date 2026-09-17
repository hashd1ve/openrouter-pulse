# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-09-17` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 632 model-variants, 489.56 T
tokens and 22.84 B requests over the trailing 30 days.


## 1. The market splits into four workloads, and share of tokens hides it

Two ratios, both derived from data OpenRouter already publishes:

```
pc_ratio           = prompt tokens / completion tokens   -- context consumed per token produced
tokens_per_request = total tokens / requests             -- size of one interaction
```

Together they separate regimes of use that a leaderboard flattens. Two models
with identical token volume can be doing entirely different jobs.

| Archetype | Model-variants | Tokens (30d) | Share | Median P:C | Median tok/req | What it means |
|---|---|---|---|---|---|---|
| **agentic** | 86 | 413.06 T | 84.4% | 53.8 | 50,037 | large contexts, terse output, very large interactions |
| **conversational** | 310 | 73.21 T | 15.0% | 9.9 | 3,748 | moderate context per output token, human-sized interactions |
| **unclassified** | 122 | 2.31 T | 0.5% | — | 28 | insufficient data to classify |
| **extractive** | 20 | 853.40 B | 0.2% | 35.6 | 8,673 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 94 | 122.30 B | 0.0% | 0.5 | 4,400 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **84.4% of all tokens**
while being 86 of 632 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
15.0%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 267.3 | 905 | 9.27 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 197.0 | 122,640 | 18.20 T | agentic |
| `xiaomi/mimo-v2.5-20260422` | 135.2 | 72,606 | 30.78 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 125.1 | 83,649 | 5.71 T | agentic |
| `minimax/minimax-m3-20260531` | 119.2 | 76,887 | 8.17 T | agentic |
| `thinkingmachines/inkling-small-20260730` | 118.7 | 55,999 | 358.79 B | agentic |
| `tencent/hy4-preview-20260827` | 111.3 | 117,116 | 39.68 T | agentic |
| `thinkingmachines/inkling-20260715` | 110.0 | 73,749 | 984.99 B | agentic |
| `poolside/laguna-xs-2.1-20260625` | 105.5 | 49,843 | 451.14 B | agentic |
| `openai/gpt-6-astra-20260903` | 103.9 | 70,077 | 1.29 T | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
267.3 tokens of context per token written, but its interactions
average only 905 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 197.0 tokens of context per token
written, in interactions averaging 122,640 tokens, which
is 135× larger.
That shape belongs to a model sitting inside a loop, re-reading a large
accumulated state every turn, not to a classifier answering a short question.


## 3. Momentum, and why the age correction is not optional

There is no public time series: the rankings feed returns one aggregate row per
model over a trailing window, not a daily history. But because the 1-, 7- and
30-day windows are nested, a trend can be derived from a single capture:

```
effective_days = min(30, days since the model launched)
momentum       = tokens in the last day / (tokens in the last 30 days / effective_days)
```

Dividing by 30 for a model four days old inflates every recent launch by
arithmetic alone, and the analysis then "discovers" that new models grow.


Across 241 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.96** with a p25–p75 range of 0.77–1.24.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 24 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **2.00×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-5.6-luna-20260709` | 10.71× | 53.16 B | 70 | conversational |
| `moonshotai/kimi-k2-thinking-20251106` | 4.27× | 14.11 B | 315 | conversational |
| `nvidia/nemotron-3-nano-30b-a3b` | 3.62× | 23.27 B | 277 | conversational |
| `z-ai/glm-4.6-20251208` | 3.41× | 8.74 B | 283 | conversational |
| `google/gemma-3-4b-it` | 2.65× | 7.18 B | 553 | conversational |
| `mistralai/ministral-14b-2512` | 2.52× | 14.81 B | 289 | conversational |
| `openai/gpt-4.1-mini-2025-04-14` | 2.40× | 356.43 B | 521 | conversational |
| `openai/gpt-6-astra-20260903` | 2.22× | 1.29 T | 13 | agentic |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite-20260507` | 0.04× | 3.28 B | 133 | conversational |
| `stepfun/step-3.7-flash-20260528` | 0.05× | 1.43 T | 112 | agentic |
| `google/gemini-3.7-flash-20260813` | 0.11× | 36.73 B | 35 | conversational |
| `meta/muse-spark-1.2-contributor-20260805` | 0.12× | 570.94 B | 27 | conversational |
| `meta-llama/llama-3.2-1b-instruct` | 0.15× | 2.18 B | 722 | output_heavy |
| `z-ai/glm-5v-turbo-20260401` | 0.18× | 54.83 B | 169 | agentic |
| `meta/muse-spark-1.1-20260709` | 0.20× | 86.40 B | 63 | agentic |
| `bytedance-seed/seed-2.0-mini-20260224` | 0.24× | 43.03 B | 203 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$292.5 M per month** across
460 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 4.4% | 29.1% | 6.54x |
| `openai` | 14.5% | 17.1% | 1.18x |
| `tencent` | 13.0% | 12.6% | 0.97x |
| `z-ai` | 11.4% | 8.9% | 0.78x |
| `moonshotai` | 1.7% | 7.9% | 4.70x |
| `deepseek` | 19.9% | 7.4% | 0.37x |
| `google` | 6.5% | 4.4% | 0.67x |
| `nvidia` | 5.0% | 4.1% | 0.83x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**2,823**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **49.4%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.945** by value. Both are extreme; a
national income distribution above 0.6 is considered severe.


### The sticker price is not the price

Traffic is overwhelmingly prompt-heavy, and prompt tokens cost less than
completions. Blended across each model's real token mix, the price actually paid
per token is a median **0.35x** the headline output price, so the
sticker overstates unit cost by about **2.9x**.

Anyone comparing models on `$/M output` is getting this wrong.


## 5. The context window arms race is mostly unused

Dividing mean tokens per request by the advertised context length asks how much
of the window the traffic actually touches. Token-weighted across the market:
**8.15%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.38% |
| **extractive** | 4.71% |
| **conversational** | 1.62% |
| **output_heavy** | 1.49% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,016 endpoints serving multi-provider models,
**693 are dominated** (68.2%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-20260816` | BaseTen | $6.60 | 6 tok/s | Phala | 28 |
| `~z-ai/glm-latest` | BaseTen | $6.60 | 6 tok/s | Phala | 28 |
| `z-ai/glm-5.3-20260816` | BaseTen | $6.60 | 7 tok/s | Phala | 27 |
| `~z-ai/glm-latest` | BaseTen | $6.60 | 7 tok/s | Phala | 27 |
| `deepseek/deepseek-v4-flash-20260731` | AtlasCloud | $1.32 | 16 tok/s | Relace | 25 |
| `~deepseek/deepseek-v4-flash-latest` | AtlasCloud | $1.32 | 16 tok/s | Relace | 25 |
| `z-ai/glm-5.3-flash-20260826` | NextBit | $0.68 | 3 tok/s | DeepInfra | 25 |
| `~z-ai/glm-flash-latest` | NextBit | $0.68 | 3 tok/s | DeepInfra | 25 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-09-16` and `2026-09-17`,
**1.18%** of 509 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.44 | -0.58 to -0.31 | 0.314 | 73 | yes |
| **all** | request weighted | -0.16 | -0.66 to +0.34 | 0.009 | 428 | no |
| **conversational** | request weighted | -0.21 | -0.87 to +0.45 | 0.015 | 287 | no |
| **extractive** | request weighted | +0.71 | +0.46 to +0.97 | 0.409 | 17 | yes |
| **output_heavy** | request weighted | -0.05 | -0.32 to +0.23 | 0.003 | 51 | no |
| **agentic** | unweighted | -0.44 | -0.82 to -0.06 | 0.058 | 73 | yes |
| **all** | unweighted | -0.66 | -0.91 to -0.40 | 0.071 | 428 | yes |
| **conversational** | unweighted | -0.94 | -1.22 to -0.65 | 0.172 | 287 | yes |
| **extractive** | unweighted | -0.05 | -0.44 to +0.34 | 0.002 | 17 | no |
| **output_heavy** | unweighted | -0.10 | -0.87 to +0.68 | 0.002 | 51 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.44, interval
-0.82 to -0.06, straddling zero). Weighting by requests, the
elasticity is **-0.44** (-0.58 to -0.31) and
clears zero comfortably.

Agentic *models* are not price-sensitive. Agentic *volume* is. That is what a
small number of very large consumers optimising unit cost looks like, and it is
invisible to any analysis treating each model as one data point.

**Read this as association, not cause.** Nothing here observes one model at two
prices; it compares models that differ in price and in everything else, quality
included. Either story fits a steep slope: buyers hunting cheap tokens, or cheap
models being the ones built for bulk work. What survives that ambiguity is the
*contrast* between archetypes, which is why the table reports segments rather
than one number.


## 9. How long does a model live? (preliminary)

Kaplan-Meier with right-censoring. Most models are still running, so their
lifetime is known only to be *at least* their current age. Dropping them biases
the curve towards short lives; counting their age as a lifetime biases it the
other way. The implementation reproduces the published curve for the Freireich
leukemia trial, which is what `tests/test_analytics.py` asserts.

| Death defined as | Events | Censored | Alive at 180d | Alive at 365d |
|---|---|---|---|---|
| ≥2 days silent | 74 | 389 | 91.7% | 83.5% |
| ≥3 days silent | 63 | 400 | 92.9% | 85.8% |
| ≥7 days silent | 61 | 402 | 93.1% | 86.0% |
| ≥14 days silent | 51 | 412 | 95.3% | 88.1% |

**Why this is preliminary.** Death is inferred from the last day with traffic,
and two biases pull against each other. A model silent for more than about 30
days leaves the monthly window entirely, so long-dead models are absent and
survival is biased *up*. The tell is in the table: a 14-day threshold finds
almost no events, which is a property of the feed rather than the market.
Meanwhile a 2-day threshold books a model that had a quiet Tuesday as dead,
biasing *down*. Their relative magnitudes are unknown.

The fix costs only time. Once the archive holds several weeks of captures, death
is *observed*, present on day N and absent on day N+k, instead of inferred from a
truncated field. The estimator does not change; its input stops being biased.


## 10. What this cannot tell you

The limits are part of the result.

- **No daily history exists publicly.** The rankings feed returns trailing
  aggregates, and its `date` field is the model's last day with traffic, not a
  time index. Every time series in this repository begins the day the first
  snapshot was taken.
- **Four schema fields are dormant.** `total_native_tokens_cached`,
  `total_native_tokens_reasoning`, `total_tool_calls` and
  `requests_with_tool_call_errors` are present but zero for every model. They
  are ingested in case that changes; no conclusion rests on them.
- **Endpoint performance is a 30-minute sample**, not a daily aggregate.
- **Archetype cuts are declared, not discovered.** P:C at
  26.6 and 2.0, tokens per
  request at 18,607. They are chosen from the observed
  distribution and held fixed so labels stay comparable over time. Models near a
  boundary will flip; that is what section 5 measures.
- **Traffic is not users.** One agentic application can generate more tokens
  than a million chat sessions. Nothing here measures adoption.

---

*Pipeline: `orpulse ingest` → `orpulse build` → `orpulse report`.
Sources and methodology in [METHODOLOGY.md](METHODOLOGY.md).*

<!-- This file is a pure function of the marts: same data in, byte-identical
     file out. No wall-clock timestamp: CI asserts that the committed report
     matches what the committed data produces, and a clock would break that
     check. -->
