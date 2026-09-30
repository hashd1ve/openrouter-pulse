# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-09-30` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 649 model-variants, 565.84 T
tokens and 26.13 B requests over the trailing 30 days.


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
| **agentic** | 95 | 441.17 T | 78.0% | 51.4 | 54,429 | large contexts, terse output, very large interactions |
| **conversational** | 310 | 121.77 T | 21.5% | 9.9 | 3,941 | moderate context per output token, human-sized interactions |
| **unclassified** | 126 | 2.57 T | 0.5% | — | 27 | insufficient data to classify |
| **extractive** | 17 | 193.85 B | 0.0% | 39.1 | 4,892 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 101 | 144.59 B | 0.0% | 0.6 | 4,328 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **78.0% of all tokens**
while being 95 of 649 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
21.5%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 240.5 | 808 | 9.34 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 204.4 | 129,598 | 19.04 T | agentic |
| `thinkingmachines/inkling-small-20260730` | 125.2 | 57,216 | 494.43 B | agentic |
| `xiaomi/mimo-v2.5-20260422` | 115.8 | 62,913 | 20.30 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 114.9 | 83,322 | 5.07 T | agentic |
| `minimax/minimax-m3-20260531` | 114.1 | 76,010 | 5.60 T | agentic |
| `tencent/hy4-preview-20260827` | 110.7 | 114,750 | 56.04 T | agentic |
| `upstage/solar-mini4-20260922` | 107.3 | 91,353 | 127.48 B | agentic |
| `deepseek/deepseek-v4-flash-20260731` | 105.4 | 98,351 | 1.09 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 102.6 | 95,484 | 226.71 B | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
240.5 tokens of context per token written, but its interactions
average only 808 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 204.4 tokens of context per token
written, in interactions averaging 129,598 tokens, which
is 160× larger.
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


Across 247 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.94** with a p25–p75 range of 0.72–1.19.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 23 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.50×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `ibm-granite/granite-4.2-8b-20260831` | 3.73× | 13.59 B | 30 | conversational |
| `inclusionai/ling-3.0-flash-vl-20260910` | 3.46× | 27.66 B | 20 | conversational |
| `qwen/qwen3.8-27b-20260814` | 3.16× | 54.44 B | 47 | agentic |
| `qwen/qwen3-next-80b-a3b-instruct-2509` | 2.76× | 67.14 B | 384 | conversational |
| `openai/gpt-5-nano-2025-08-07` | 2.41× | 3.24 B | 419 | conversational |
| `qwen/qwen3.5-397b-a17b-20260216` | 2.25× | 172.64 B | 226 | conversational |
| `z-ai/glm-5.3-flash-20260826` | 2.13× | 10.58 B | 35 | conversational |
| `openai/o4-mini-2025-04-16` | 1.90× | 9.57 B | 532 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `tencent/hy-mt2-1.8b-20260521` | 0.03× | 3.02 B | 41 | conversational |
| `stepfun/step-3.7-flash-20260528` | 0.11× | 614.24 B | 125 | agentic |
| `tencent/hy-mt2-7b-20260521` | 0.11× | 2.42 B | 42 | conversational |
| `mistralai/mistral-large-2512` | 0.13× | 22.90 B | 303 | conversational |
| `google/gemini-3.7-flash-20260813` | 0.19× | 19.28 B | 48 | output_heavy |
| `meta/muse-spark-1.1-20260709` | 0.20× | 34.65 B | 76 | conversational |
| `aion-labs/aion-3.0-20260707` | 0.22× | 33.58 B | 85 | conversational |
| `xiaomi/mimo-v2.5-20260422` | 0.25× | 20.30 T | 161 | agentic |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$249.1 M per month** across
460 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 4.0% | 24.1% | 6.04x |
| `tencent` | 12.9% | 20.0% | 1.55x |
| `openai` | 14.9% | 18.9% | 1.27x |
| `z-ai` | 14.0% | 7.9% | 0.56x |
| `deepseek` | 21.9% | 7.0% | 0.32x |
| `moonshotai` | 1.5% | 7.0% | 4.83x |
| `google` | 5.5% | 5.3% | 0.97x |
| `xiaomi` | 5.6% | 2.2% | 0.40x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,112**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **53.2%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.936** by value. Both are extreme; a
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
**6.54%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.16% |
| **extractive** | 3.64% |
| **conversational** | 1.68% |
| **output_heavy** | 1.06% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,111 endpoints serving multi-provider models,
**750 are dominated** (67.5%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-20260816` | Venice | $4.40 | 38 tok/s | Baidu | 31 |
| `~z-ai/glm-latest` | Venice | $4.40 | 36 tok/s | Baidu | 31 |
| `z-ai/glm-5.3-20260816` | Fireworks | $4.40 | 43 tok/s | Baidu | 30 |
| `~z-ai/glm-latest` | Fireworks | $4.40 | 45 tok/s | Baidu | 27 |
| `z-ai/glm-5.3-20260816` | Z.AI | $4.40 | 45 tok/s | Baidu | 27 |
| `~z-ai/glm-latest` | Z.AI | $4.40 | 45 tok/s | Baidu | 27 |
| `z-ai/glm-5.3-flash-20260826` | Io Net | $0.50 | 10 tok/s | DeepInfra | 26 |
| `~z-ai/glm-flash-latest` | Io Net | $0.50 | 11 tok/s | DeepInfra | 26 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-09-29` and `2026-09-30`,
**1.54%** of 521 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.50 | -0.80 to -0.21 | 0.191 | 82 | yes |
| **all** | request weighted | +0.12 | -0.26 to +0.51 | 0.004 | 434 | no |
| **conversational** | request weighted | +0.15 | -0.56 to +0.86 | 0.007 | 289 | no |
| **output_heavy** | request weighted | -0.12 | -0.44 to +0.21 | 0.016 | 50 | no |
| **agentic** | unweighted | -0.72 | -1.02 to -0.41 | 0.183 | 82 | yes |
| **all** | unweighted | -0.58 | -0.84 to -0.32 | 0.044 | 434 | yes |
| **conversational** | unweighted | -0.60 | -0.91 to -0.30 | 0.067 | 289 | yes |
| **output_heavy** | unweighted | -0.46 | -1.25 to +0.32 | 0.015 | 50 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.72, interval
-1.02 to -0.41, straddling zero). Weighting by requests, the
elasticity is **-0.50** (-0.80 to -0.21) and
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
| ≥2 days silent | 58 | 403 | 89.7% | 85.8% |
| ≥3 days silent | 54 | 407 | 90.0% | 86.5% |
| ≥7 days silent | 40 | 421 | 93.1% | 89.5% |
| ≥14 days silent | 29 | 432 | 94.8% | 92.0% |

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
