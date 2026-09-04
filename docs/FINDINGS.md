# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-09-04` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 609 model-variants, 399.19 T
tokens and 19.96 B requests over the trailing 30 days.


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
| **agentic** | 73 | 308.12 T | 77.2% | 51.6 | 52,679 | large contexts, terse output, very large interactions |
| **conversational** | 296 | 85.70 T | 21.5% | 10.1 | 3,932 | moderate context per output token, human-sized interactions |
| **extractive** | 27 | 3.24 T | 0.8% | 39.4 | 8,832 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 124 | 1.98 T | 0.5% | — | 32 | insufficient data to classify |
| **output_heavy** | 89 | 146.91 B | 0.0% | 0.4 | 4,454 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **77.2% of all tokens**
while being 73 of 609 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
21.5%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 368.7 | 1,301 | 18.38 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 174.4 | 110,058 | 16.02 T | agentic |
| `xiaomi/mimo-v2.5-20260422` | 137.0 | 73,268 | 28.39 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 135.7 | 87,953 | 6.72 T | agentic |
| `thinkingmachines/inkling-20260715` | 125.9 | 68,894 | 327.20 B | agentic |
| `minimax/minimax-m3-20260531` | 118.6 | 77,524 | 5.66 T | agentic |
| `thinkingmachines/inkling-small-20260730` | 114.7 | 53,119 | 133.72 B | agentic |
| `poolside/laguna-xs-2.1-20260625` | 113.5 | 53,573 | 580.27 B | agentic |
| `tencent/hy4-preview-20260827` | 111.0 | 118,274 | 10.97 T | agentic |
| `anthropic/claude-opus-5-fast-20260723` | 99.2 | 87,319 | 101.88 B | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
368.7 tokens of context per token written, but its interactions
average only 1,301 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 174.4 tokens of context per token
written, in interactions averaging 110,058 tokens, which
is 85× larger.
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


Across 227 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **1.02** with a p25–p75 range of 0.73–1.25.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 19 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.36×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `qwen/qwen-plus-2025-07-28` | 5.58× | 2.17 B | 361 | conversational |
| `minimax/minimax-m2.7-20260318` | 5.29× | 512.84 B | 170 | agentic |
| `minimax/minimax-m3-20260531` | 4.86× | 5.66 T | 96 | agentic |
| `google/gemini-2.5-flash-lite` | 4.56× | 3.60 B | 409 | conversational |
| `openai/gpt-5-nano-2025-08-07` | 3.41× | 244.31 B | 393 | conversational |
| `thinkingmachines/inkling-20260715` | 3.39× | 96.39 B | 49 | agentic |
| `thinkingmachines/inkling-small-20260730` | 2.88× | 133.72 B | 36 | agentic |
| `thinkingmachines/inkling-20260715` | 2.81× | 327.20 B | 49 | agentic |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `google/gemini-3.6-flash-20260721` | 0.10× | 4.72 B | 45 | conversational |
| `google/gemma-4-26b-a4b-it-20260403` | 0.12× | 36.86 B | 154 | conversational |
| `google/gemini-3.6-flash-20260721` | 0.13× | 6.09 T | 45 | agentic |
| `meta/muse-glimmer-30b-20260810` | 0.24× | 91.75 B | 26 | conversational |
| `anthropic/claude-4.7-opus-20260416` | 0.26× | 1.30 T | 141 | agentic |
| `z-ai/glm-5v-turbo-20260401` | 0.28× | 96.13 B | 156 | agentic |
| `meta-llama/llama-3.1-70b-instruct` | 0.31× | 32.90 B | 773 | conversational |
| `tencent/hy3-preview-20260421` | 0.33× | 79.49 B | 135 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$203.0 M per month** across
442 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 5.7% | 30.7% | 5.37x |
| `openai` | 12.3% | 12.3% | 1.00x |
| `z-ai` | 8.3% | 11.2% | 1.36x |
| `moonshotai` | 2.0% | 10.9% | 5.40x |
| `deepseek` | 21.8% | 9.8% | 0.45x |
| `google` | 7.9% | 9.2% | 1.15x |
| `tencent` | 11.3% | 6.9% | 0.61x |
| `x-ai` | 0.7% | 2.7% | 3.92x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**2,865**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **49.8%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.942** by value. Both are extreme; a
national income distribution above 0.6 is considered severe.


### The sticker price is not the price

Traffic is overwhelmingly prompt-heavy, and prompt tokens cost less than
completions. Blended across each model's real token mix, the price actually paid
per token is a median **0.35x** the headline output price, so the
sticker overstates unit cost by about **2.8x**.

Anyone comparing models on `$/M output` is getting this wrong.


## 5. The context window arms race is mostly unused

Dividing mean tokens per request by the advertised context length asks how much
of the window the traffic actually touches. Token-weighted across the market:
**7.21%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.19% |
| **extractive** | 4.68% |
| **conversational** | 1.79% |
| **output_heavy** | 1.60% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 924 endpoints serving multi-provider models,
**605 are dominated** (65.5%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.2-20260616` | Alibaba | $7.26 | 31 tok/s | DeepInfra | 28 |
| `z-ai/glm-5.2-20260616` | BaseTen | $6.60 | 32 tok/s | DeepInfra | 27 |
| `deepseek/deepseek-v4-flash-20260731` | AtlasCloud | $1.32 | 24 tok/s | Relace | 25 |
| `~deepseek/deepseek-v4-flash-latest` | AtlasCloud | $1.32 | 24 tok/s | Relace | 25 |
| `deepseek/deepseek-v4-flash-20260731` | Phala | $1.32 | 26 tok/s | Relace | 23 |
| `~deepseek/deepseek-v4-flash-latest` | Phala | $1.32 | 26 tok/s | Relace | 23 |
| `z-ai/glm-5.3-flash-20260826` | Io Net | $0.50 | 14 tok/s | GMICloud | 22 |
| `~z-ai/glm-flash-latest` | Io Net | $0.50 | 14 tok/s | GMICloud | 22 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-09-03` and `2026-09-04`,
**1.65%** of 485 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.61 | -0.71 to -0.52 | 0.563 | 59 | yes |
| **all** | request weighted | -0.19 | -0.65 to +0.26 | 0.016 | 407 | no |
| **conversational** | request weighted | -0.25 | -0.87 to +0.37 | 0.025 | 277 | no |
| **extractive** | request weighted | -0.47 | -0.83 to -0.11 | 0.290 | 24 | yes |
| **output_heavy** | request weighted | -0.12 | -0.43 to +0.18 | 0.022 | 47 | no |
| **agentic** | unweighted | -0.21 | -0.61 to +0.20 | 0.017 | 59 | no |
| **all** | unweighted | -0.70 | -0.96 to -0.43 | 0.077 | 407 | yes |
| **conversational** | unweighted | -1.00 | -1.29 to -0.70 | 0.172 | 277 | yes |
| **extractive** | unweighted | -0.31 | -0.89 to +0.28 | 0.028 | 24 | no |
| **output_heavy** | unweighted | -0.28 | -1.08 to +0.52 | 0.016 | 47 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.21, interval
-0.61 to +0.20, straddling zero). Weighting by requests, the
elasticity is **-0.61** (-0.71 to -0.52) and
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
| ≥2 days silent | 63 | 382 | 92.7% | 85.3% |
| ≥3 days silent | 62 | 383 | 92.7% | 85.7% |
| ≥7 days silent | 49 | 396 | 95.3% | 88.9% |
| ≥14 days silent | 9 | 436 | 98.7% | 98.2% |

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
