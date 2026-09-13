# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-09-13` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 631 model-variants, 463.30 T
tokens and 21.96 B requests over the trailing 30 days.


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
| **agentic** | 81 | 387.32 T | 83.6% | 52.6 | 49,450 | large contexts, terse output, very large interactions |
| **conversational** | 310 | 72.69 T | 15.7% | 9.9 | 3,824 | moderate context per output token, human-sized interactions |
| **unclassified** | 124 | 2.23 T | 0.5% | — | 27 | insufficient data to classify |
| **extractive** | 23 | 937.55 B | 0.2% | 37.7 | 8,695 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 93 | 124.41 B | 0.0% | 0.4 | 4,424 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **83.6% of all tokens**
while being 81 of 631 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
15.7%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 310.1 | 1,050 | 11.35 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 195.3 | 119,493 | 18.06 T | agentic |
| `xiaomi/mimo-v2.5-20260422` | 137.1 | 72,061 | 29.70 T | agentic |
| `thinkingmachines/inkling-20260715` | 130.1 | 73,681 | 777.18 B | agentic |
| `poolside/laguna-s-2.1-20260720` | 127.0 | 84,546 | 5.99 T | agentic |
| `minimax/minimax-m3-20260531` | 119.2 | 76,887 | 8.17 T | agentic |
| `thinkingmachines/inkling-small-20260730` | 117.3 | 55,025 | 285.53 B | agentic |
| `tencent/hy4-preview-20260827` | 111.1 | 117,677 | 33.18 T | agentic |
| `poolside/laguna-xs-2.1-20260625` | 107.9 | 51,079 | 489.64 B | agentic |
| `openai/gpt-6-astra-20260903` | 101.7 | 65,797 | 798.77 B | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
310.1 tokens of context per token written, but its interactions
average only 1,050 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 195.3 tokens of context per token
written, in interactions averaging 119,493 tokens, which
is 114× larger.
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


Across 233 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.81** with a p25–p75 range of 0.58–1.03.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 18 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.82×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `tencent/hy-mt2-7b-20260521` | 5.97× | 1.13 B | 25 | conversational |
| `qwen/qwen3-coder-30b-a3b-instruct` | 5.60× | 24.83 B | 409 | conversational |
| `tencent/hy-mt2-1.8b-20260521` | 5.18× | 1.33 B | 24 | conversational |
| `google/gemini-2.5-flash-lite` | 4.63× | 7.13 B | 418 | conversational |
| `tencent/hy-mt2-30b-a3b-20260521` | 4.19× | 2.77 B | 24 | conversational |
| `dots-studio/dots-3-note-preview-20260813` | 2.94× | 973.23 B | 30 | agentic |
| `amazon/nova-2-lite-v1` | 2.78× | 5.52 B | 285 | conversational |
| `openai/gpt-5.6-luna-20260709` | 2.77× | 41.94 T | 66 | agentic |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `stepfun/step-3.7-flash-20260528` | 0.02× | 1.90 T | 108 | agentic |
| `google/gemini-3.7-flash-20260813` | 0.05× | 38.34 B | 31 | conversational |
| `meta/muse-spark-1.2-contributor-20260805` | 0.08× | 562.24 B | 23 | conversational |
| `meta/muse-spark-1.2-20260805` | 0.13× | 284.20 B | 39 | conversational |
| `google/gemini-3.1-flash-lite-20260507` | 0.13× | 3.36 B | 129 | conversational |
| `bytedance-seed/seed-2.0-mini-20260224` | 0.14× | 44.49 B | 199 | conversational |
| `anthropic/claude-4.7-opus-20260416` | 0.16× | 1.01 T | 150 | agentic |
| `bytedance-seed/seed-2.0-lite-20260309` | 0.17× | 5.97 B | 187 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$267.4 M per month** across
459 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 5.0% | 30.4% | 6.12x |
| `openai` | 13.8% | 14.8% | 1.07x |
| `tencent` | 12.8% | 11.9% | 0.93x |
| `z-ai` | 10.7% | 7.9% | 0.74x |
| `moonshotai` | 1.7% | 7.5% | 4.31x |
| `deepseek` | 19.8% | 7.3% | 0.37x |
| `google` | 7.0% | 6.5% | 0.93x |
| `nvidia` | 5.3% | 4.6% | 0.86x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,135**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **53.0%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.943** by value. Both are extreme; a
national income distribution above 0.6 is considered severe.


### The sticker price is not the price

Traffic is overwhelmingly prompt-heavy, and prompt tokens cost less than
completions. Blended across each model's real token mix, the price actually paid
per token is a median **0.36x** the headline output price, so the
sticker overstates unit cost by about **2.8x**.

Anyone comparing models on `$/M output` is getting this wrong.


## 5. The context window arms race is mostly unused

Dividing mean tokens per request by the advertised context length asks how much
of the window the traffic actually touches. Token-weighted across the market:
**8.00%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.57% |
| **extractive** | 4.34% |
| **conversational** | 1.70% |
| **output_heavy** | 1.57% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 888 endpoints serving multi-provider models,
**588 are dominated** (66.2%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-flash-20260826` | NextBit | $0.59 | 2 tok/s | DeepInfra | 23 |
| `~z-ai/glm-flash-latest` | NextBit | $0.59 | 2 tok/s | DeepInfra | 23 |
| `deepseek/deepseek-v4-flash-20260731` | AtlasCloud | $1.32 | 42 tok/s | Relace | 21 |
| `~deepseek/deepseek-v4-flash-latest` | AtlasCloud | $1.32 | 44 tok/s | Relace | 21 |
| `z-ai/glm-5.2-20260616` | Z.AI | $4.40 | 32 tok/s | Baidu | 20 |
| `~z-ai/glm-latest` | SiliconFlow | $4.40 | 31 tok/s | Reka | 20 |
| `z-ai/glm-5.3-flash-20260826` | Venice | $0.50 | 17 tok/s | Relace | 20 |
| `~z-ai/glm-flash-latest` | Venice | $0.50 | 17 tok/s | Relace | 20 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-09-12` and `2026-09-13`,
**0.40%** of 505 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.49 | -0.57 to -0.41 | 0.424 | 69 | yes |
| **all** | request weighted | -0.34 | -0.77 to +0.09 | 0.050 | 429 | no |
| **conversational** | request weighted | -0.37 | -1.12 to +0.39 | 0.057 | 292 | no |
| **extractive** | request weighted | +0.72 | +0.43 to +1.01 | 0.363 | 20 | yes |
| **output_heavy** | request weighted | -0.08 | -0.37 to +0.20 | 0.011 | 48 | no |
| **agentic** | unweighted | -0.43 | -0.76 to -0.11 | 0.076 | 69 | yes |
| **all** | unweighted | -0.66 | -0.92 to -0.40 | 0.072 | 429 | yes |
| **conversational** | unweighted | -0.91 | -1.20 to -0.62 | 0.151 | 292 | yes |
| **extractive** | unweighted | -0.11 | -0.49 to +0.27 | 0.009 | 20 | no |
| **output_heavy** | unweighted | -0.15 | -0.89 to +0.60 | 0.005 | 48 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.43, interval
-0.76 to -0.11, straddling zero). Weighting by requests, the
elasticity is **-0.49** (-0.57 to -0.41) and
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
| ≥2 days silent | 77 | 386 | 90.4% | 82.6% |
| ≥3 days silent | 74 | 389 | 91.0% | 83.6% |
| ≥7 days silent | 58 | 405 | 93.6% | 86.0% |
| ≥14 days silent | 40 | 423 | 96.7% | 90.8% |

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
