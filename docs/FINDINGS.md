# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-09-19` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 636 model-variants, 504.21 T
tokens and 23.23 B requests over the trailing 30 days.


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
| **agentic** | 90 | 428.84 T | 85.1% | 51.9 | 49,131 | large contexts, terse output, very large interactions |
| **conversational** | 311 | 72.29 T | 14.3% | 9.9 | 3,811 | moderate context per output token, human-sized interactions |
| **unclassified** | 120 | 2.35 T | 0.5% | — | 32 | insufficient data to classify |
| **extractive** | 18 | 576.36 B | 0.1% | 37.6 | 8,731 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 97 | 157.26 B | 0.0% | 0.6 | 4,392 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **85.1% of all tokens**
while being 90 of 636 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
14.3%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 258.5 | 876 | 9.18 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 201.3 | 125,049 | 18.43 T | agentic |
| `deepseek/deepseek-v4-flash-20260731` | 184.3 | 137,232 | 742.74 B | agentic |
| `xiaomi/mimo-v2.5-20260422` | 133.6 | 72,015 | 30.34 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 123.0 | 83,020 | 5.53 T | agentic |
| `minimax/minimax-m3-20260531` | 119.2 | 76,887 | 8.17 T | agentic |
| `thinkingmachines/inkling-small-20260730` | 116.9 | 55,983 | 396.13 B | agentic |
| `tencent/hy4-preview-20260827` | 111.7 | 116,824 | 43.69 T | agentic |
| `openai/gpt-6-astra-20260903` | 111.6 | 72,966 | 2.36 T | agentic |
| `poolside/laguna-xs-2.1-20260625` | 104.4 | 49,360 | 431.83 B | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
258.5 tokens of context per token written, but its interactions
average only 876 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 201.3 tokens of context per token
written, in interactions averaging 125,049 tokens, which
is 143× larger.
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


Across 240 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.97** with a p25–p75 range of 0.72–1.19.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 21 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.76×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `deepseek/deepseek-v4-flash-20260731` | 30.00× | 742.74 B | 50 | agentic |
| `mistralai/voxtral-small-24b-2507` | 9.46× | 1.68 B | 324 | conversational |
| `tencent/hy-mt2-7b-20260521` | 4.63× | 1.79 B | 31 | conversational |
| `tencent/hy-mt2-1.8b-20260521` | 4.18× | 2.20 B | 30 | conversational |
| `tencent/hy-mt2-30b-a3b-20260521` | 2.71× | 4.19 B | 30 | conversational |
| `dots-studio/dots-3-note-preview-20260813` | 2.14× | 1.49 T | 36 | agentic |
| `z-ai/glm-4.6-20251208` | 2.06× | 10.11 B | 285 | conversational |
| `thinkingmachines/inkling-20260715` | 2.04× | 130.23 B | 64 | agentic |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-3.2-1b-instruct` | 0.06× | 2.03 B | 724 | output_heavy |
| `google/gemini-3.7-flash-20260813` | 0.06× | 34.19 B | 37 | conversational |
| `stepfun/step-3.7-flash-20260528` | 0.07× | 1.25 T | 114 | agentic |
| `meta/muse-spark-1.2-20260805` | 0.09× | 232.74 B | 45 | conversational |
| `google/gemini-3.1-flash-lite-20260507` | 0.10× | 3.30 B | 135 | conversational |
| `bytedance-seed/seed-2.0-mini-20260224` | 0.16× | 42.69 B | 205 | conversational |
| `meta/muse-spark-1.2-contributor-20260805` | 0.16× | 576.95 B | 29 | conversational |
| `meta/muse-spark-1.1-20260709` | 0.18× | 67.58 B | 65 | agentic |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$231.0 M per month** across
464 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 4.3% | 27.6% | 6.42x |
| `openai` | 14.4% | 22.2% | 1.54x |
| `tencent` | 13.1% | 17.4% | 1.32x |
| `google` | 6.3% | 6.1% | 0.95x |
| `moonshotai` | 1.6% | 6.0% | 3.63x |
| `z-ai` | 11.9% | 5.9% | 0.49x |
| `deepseek` | 20.1% | 4.6% | 0.23x |
| `x-ai` | 0.5% | 2.3% | 4.41x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,669**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **58.4%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.938** by value. Both are extreme; a
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
**9.15%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.51% |
| **extractive** | 4.74% |
| **conversational** | 1.63% |
| **output_heavy** | 1.50% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,006 endpoints serving multi-provider models,
**692 are dominated** (68.8%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-flash-20260826` | Near AI | $0.50 | 11 tok/s | DeepInfra | 25 |
| `~z-ai/glm-flash-latest` | Near AI | $0.50 | 11 tok/s | DeepInfra | 25 |
| `z-ai/glm-5.3-flash-20260826` | Venice | $0.50 | 17 tok/s | DeepInfra | 24 |
| `~z-ai/glm-flash-latest` | Venice | $0.50 | 17 tok/s | DeepInfra | 24 |
| `z-ai/glm-5.3-flash-20260826` | Reka | $0.50 | 20 tok/s | Relace | 22 |
| `~z-ai/glm-flash-latest` | Reka | $0.50 | 20 tok/s | Relace | 22 |
| `z-ai/glm-5.3-20260816` | Z.AI | $4.40 | 52 tok/s | InferenceNet | 22 |
| `~z-ai/glm-latest` | Z.AI | $4.40 | 52 tok/s | InferenceNet | 22 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-09-18` and `2026-09-19`,
**1.17%** of 512 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.61 | -0.84 to -0.39 | 0.331 | 69 | yes |
| **all** | request weighted | -0.15 | -0.59 to +0.29 | 0.008 | 415 | no |
| **conversational** | request weighted | -0.39 | -1.13 to +0.34 | 0.063 | 277 | no |
| **extractive** | request weighted | +0.66 | +0.28 to +1.03 | 0.412 | 16 | yes |
| **output_heavy** | request weighted | -0.25 | -0.51 to +0.01 | 0.111 | 53 | no |
| **agentic** | unweighted | -0.49 | -0.91 to -0.07 | 0.064 | 69 | yes |
| **all** | unweighted | -0.69 | -0.94 to -0.43 | 0.078 | 415 | yes |
| **conversational** | unweighted | -0.95 | -1.25 to -0.65 | 0.169 | 277 | yes |
| **extractive** | unweighted | -0.06 | -0.45 to +0.34 | 0.003 | 16 | no |
| **output_heavy** | unweighted | -0.40 | -1.03 to +0.24 | 0.030 | 53 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.49, interval
-0.91 to -0.07, straddling zero). Weighting by requests, the
elasticity is **-0.61** (-0.84 to -0.39) and
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
| ≥2 days silent | 72 | 393 | 91.3% | 83.8% |
| ≥3 days silent | 71 | 394 | 91.5% | 84.0% |
| ≥7 days silent | 58 | 407 | 93.1% | 85.9% |
| ≥14 days silent | 50 | 415 | 94.8% | 87.5% |

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
