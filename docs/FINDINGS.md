# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-09-03` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 608 model-variants, 390.62 T
tokens and 19.73 B requests over the trailing 30 days.


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
| **agentic** | 75 | 301.98 T | 77.3% | 51.7 | 52,565 | large contexts, terse output, very large interactions |
| **conversational** | 293 | 84.13 T | 21.5% | 10.1 | 3,915 | moderate context per output token, human-sized interactions |
| **extractive** | 27 | 2.39 T | 0.6% | 39.6 | 8,550 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 123 | 1.96 T | 0.5% | — | 31 | insufficient data to classify |
| **output_heavy** | 90 | 147.32 B | 0.0% | 0.5 | 4,456 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **77.3% of all tokens**
while being 75 of 608 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
21.5%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 367.6 | 1,303 | 18.82 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 172.3 | 109,083 | 15.83 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 137.5 | 88,742 | 6.83 T | agentic |
| `xiaomi/mimo-v2.5-20260422` | 136.7 | 75,119 | 29.05 T | agentic |
| `thinkingmachines/inkling-20260715` | 122.8 | 68,822 | 296.52 B | agentic |
| `minimax/minimax-m3-20260531` | 115.9 | 77,706 | 4.74 T | agentic |
| `tencent/hy4-preview-20260827` | 114.9 | 122,399 | 7.99 T | agentic |
| `poolside/laguna-xs-2.1-20260625` | 114.7 | 54,042 | 590.73 B | agentic |
| `thinkingmachines/inkling-small-20260730` | 112.9 | 52,565 | 120.89 B | agentic |
| `anthropic/claude-opus-5-fast-20260723` | 98.9 | 87,329 | 105.36 B | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
367.6 tokens of context per token written, but its interactions
average only 1,303 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 172.3 tokens of context per token
written, in interactions averaging 109,083 tokens, which
is 84× larger.
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


Across 226 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **1.04** with a p25–p75 range of 0.75–1.24.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 19 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.43×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `minimax/minimax-m2.7-20260318` | 6.67× | 422.47 B | 169 | agentic |
| `google/gemini-3.1-flash-lite-20260507` | 5.77× | 3.19 B | 119 | conversational |
| `minimax/minimax-m3-20260531` | 5.72× | 4.74 T | 95 | agentic |
| `google/gemini-3.6-flash-20260721` | 4.77× | 4.71 B | 44 | conversational |
| `openai/gpt-5.6-luna-20260709` | 3.96× | 17.79 B | 56 | output_heavy |
| `bytedance-seed/seed-2.0-lite-20260309` | 3.57× | 6.88 B | 177 | conversational |
| `thinkingmachines/inkling-small-20260730` | 3.42× | 120.89 B | 35 | agentic |
| `openai/gpt-5-nano-2025-08-07` | 3.17× | 223.84 B | 392 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `google/gemma-4-26b-a4b-it-20260403` | 0.10× | 38.82 B | 153 | conversational |
| `google/gemini-3.6-flash-20260721` | 0.11× | 6.12 T | 44 | agentic |
| `z-ai/glm-5v-turbo-20260401` | 0.12× | 99.67 B | 155 | agentic |
| `meta-llama/llama-3.2-1b-instruct` | 0.26× | 2.98 B | 708 | output_heavy |
| `qwen/qwen3.7-max-20260520` | 0.34× | 271.54 B | 105 | conversational |
| `meta/muse-glimmer-30b-20260810` | 0.35× | 90.89 B | 25 | conversational |
| `meta-llama/llama-3.1-70b-instruct` | 0.35× | 33.13 B | 772 | conversational |
| `anthropic/claude-4.7-opus-20260416` | 0.36× | 1.32 T | 140 | agentic |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$191.1 M per month** across
442 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 5.8% | 34.5% | 5.96x |
| `moonshotai` | 2.0% | 11.3% | 5.59x |
| `deepseek` | 22.1% | 10.8% | 0.49x |
| `openai` | 12.3% | 10.5% | 0.86x |
| `google` | 7.9% | 8.7% | 1.09x |
| `tencent` | 10.8% | 6.0% | 0.55x |
| `nvidia` | 5.5% | 5.3% | 0.97x |
| `z-ai` | 7.9% | 3.6% | 0.46x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,546**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **57.4%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.944** by value. Both are extreme; a
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
**9.21%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.41% |
| **extractive** | 3.39% |
| **output_heavy** | 1.84% |
| **conversational** | 1.80% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 930 endpoints serving multi-provider models,
**612 are dominated** (65.8%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.2-20260616` | Z.AI | $4.40 | 40 tok/s | DeepInfra | 23 |
| `z-ai/glm-5.3-flash-20260826` | Io Net | $0.50 | 10 tok/s | Novita | 22 |
| `~z-ai/glm-flash-latest` | Io Net | $0.50 | 10 tok/s | Novita | 22 |
| `z-ai/glm-5.3-flash-20260826` | Sail Research | $0.50 | 12 tok/s | Novita | 20 |
| `~z-ai/glm-flash-latest` | Sail Research | $0.50 | 12 tok/s | Novita | 20 |
| `z-ai/glm-5.2-20260616` | Mistral | $4.40 | 48 tok/s | DeepInfra | 19 |
| `z-ai/glm-5.3-20260816` | Phala | $4.40 | 30 tok/s | Decart | 19 |
| `~z-ai/glm-latest` | Phala | $4.40 | 30 tok/s | Decart | 19 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-09-02` and `2026-09-03`,
**1.88%** of 480 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.68 | -0.79 to -0.57 | 0.624 | 59 | yes |
| **all** | request weighted | -0.30 | -0.73 to +0.13 | 0.035 | 404 | no |
| **conversational** | request weighted | -0.28 | -0.92 to +0.36 | 0.031 | 273 | no |
| **extractive** | request weighted | -0.65 | -1.17 to -0.14 | 0.396 | 24 | yes |
| **output_heavy** | request weighted | -0.07 | -0.38 to +0.23 | 0.008 | 48 | no |
| **agentic** | unweighted | -0.18 | -0.60 to +0.23 | 0.014 | 59 | no |
| **all** | unweighted | -0.73 | -0.99 to -0.46 | 0.084 | 404 | yes |
| **conversational** | unweighted | -1.01 | -1.31 to -0.71 | 0.174 | 273 | yes |
| **extractive** | unweighted | -0.55 | -1.11 to +0.00 | 0.105 | 24 | no |
| **output_heavy** | unweighted | -0.35 | -1.09 to +0.39 | 0.025 | 48 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.18, interval
-0.60 to +0.23, straddling zero). Weighting by requests, the
elasticity is **-0.68** (-0.79 to -0.57) and
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
| ≥2 days silent | 71 | 374 | 91.1% | 83.7% |
| ≥3 days silent | 61 | 384 | 93.1% | 86.0% |
| ≥7 days silent | 48 | 397 | 95.3% | 89.8% |
| ≥14 days silent | 8 | 437 | 98.6% | 98.6% |

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
