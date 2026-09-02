# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-09-02` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 602 model-variants, 381.27 T
tokens and 19.49 B requests over the trailing 30 days.


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
| **agentic** | 72 | 294.70 T | 77.3% | 50.9 | 51,693 | large contexts, terse output, very large interactions |
| **conversational** | 288 | 81.48 T | 21.4% | 10.1 | 3,810 | moderate context per output token, human-sized interactions |
| **extractive** | 30 | 2.99 T | 0.8% | 35.6 | 8,531 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 122 | 1.96 T | 0.5% | — | 27 | insufficient data to classify |
| **output_heavy** | 90 | 146.73 B | 0.0% | 0.5 | 4,478 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **77.3% of all tokens**
while being 72 of 602 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
21.4%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 367.0 | 1,306 | 19.32 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 170.4 | 108,091 | 15.61 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 139.0 | 89,424 | 6.90 T | agentic |
| `xiaomi/mimo-v2.5-20260422` | 135.9 | 78,390 | 29.32 T | agentic |
| `thinkingmachines/inkling-20260715` | 124.7 | 68,730 | 265.74 B | agentic |
| `tencent/hy4-preview-20260827` | 123.2 | 129,500 | 5.72 T | agentic |
| `poolside/laguna-xs-2.1-20260625` | 115.4 | 54,319 | 598.23 B | agentic |
| `minimax/minimax-m3-20260531` | 113.8 | 77,781 | 3.84 T | agentic |
| `thinkingmachines/inkling-small-20260730` | 110.7 | 51,490 | 107.12 B | agentic |
| `anthropic/claude-opus-5-fast-20260723` | 99.4 | 87,756 | 111.05 B | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
367.0 tokens of context per token written, but its interactions
average only 1,306 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 170.4 tokens of context per token
written, in interactions averaging 108,091 tokens, which
is 83× larger.
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
median of **1.03** with a p25–p75 range of 0.75–1.29.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 18 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.46×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `minimax/minimax-m2.7-20260318` | 6.92× | 328.56 B | 168 | agentic |
| `google/gemini-3.6-flash-20260721` | 6.52× | 3.96 B | 43 | conversational |
| `minimax/minimax-m3-20260531` | 6.39× | 3.84 T | 94 | agentic |
| `thinkingmachines/inkling-small-20260730` | 3.68× | 107.12 B | 34 | agentic |
| `thinkingmachines/inkling-20260715` | 3.64× | 265.74 B | 47 | agentic |
| `ibm-granite/granite-4.1-8b-20260429` | 3.36× | 11.91 B | 125 | conversational |
| `qwen/qwen3.6-27b-20260422` | 2.97× | 120.37 B | 128 | conversational |
| `z-ai/glm-5.2-20260616` | 2.90× | 39.31 B | 78 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `google/gemma-4-26b-a4b-it-20260403` | 0.10× | 40.74 B | 152 | conversational |
| `google/gemini-3.6-flash-20260721` | 0.16× | 6.16 T | 43 | agentic |
| `z-ai/glm-5v-turbo-20260401` | 0.20× | 102.50 B | 154 | agentic |
| `anthropic/claude-4.7-opus-20260416` | 0.21× | 1.33 T | 139 | agentic |
| `meta/muse-glimmer-30b-20260810` | 0.27× | 89.62 B | 24 | conversational |
| `meta-llama/llama-3.1-70b-instruct` | 0.28× | 33.84 B | 771 | conversational |
| `anthropic/claude-4.8-opus-fast-20260528` | 0.29× | 59.11 B | 98 | agentic |
| `nvidia/nemotron-3-nano-30b-a3b` | 0.30× | 48.57 B | 262 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$206.5 M per month** across
437 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 5.9% | 45.3% | 7.67x |
| `openai` | 11.9% | 12.1% | 1.01x |
| `moonshotai` | 2.0% | 10.2% | 5.03x |
| `deepseek` | 22.5% | 10.0% | 0.44x |
| `google` | 8.0% | 4.7% | 0.59x |
| `tencent` | 10.6% | 4.6% | 0.44x |
| `z-ai` | 7.5% | 2.9% | 0.39x |
| `x-ai` | 0.7% | 2.6% | 3.67x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,680**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **58.6%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.942** by value. Both are extreme; a
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
**8.51%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.50% |
| **extractive** | 3.87% |
| **output_heavy** | 1.87% |
| **conversational** | 1.77% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 900 endpoints serving multi-provider models,
**596 are dominated** (66.2%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.2-20260616` | Alibaba | $7.26 | 33 tok/s | DeepInfra | 26 |
| `z-ai/glm-5.2-20260616` | Mistral | $4.40 | 28 tok/s | DeepInfra | 24 |
| `deepseek/deepseek-v4-flash-20260731` | Phala | $1.32 | 34 tok/s | Relace | 23 |
| `~deepseek/deepseek-v4-flash-latest` | Phala | $1.32 | 34 tok/s | Relace | 23 |
| `z-ai/glm-5.3-flash-20260826` | NextBit | $0.50 | 17 tok/s | Z.AI | 20 |
| `~z-ai/glm-flash-latest` | NextBit | $0.50 | 17 tok/s | Z.AI | 19 |
| `deepseek/deepseek-v4-flash-20260731` | NextBit | $1.20 | 35 tok/s | Relace | 19 |
| `~deepseek/deepseek-v4-flash-latest` | NextBit | $1.20 | 35 tok/s | Relace | 19 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-09-01` and `2026-09-02`,
**1.05%** of 477 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.65 | -0.77 to -0.53 | 0.559 | 58 | yes |
| **all** | request weighted | -0.22 | -0.66 to +0.22 | 0.020 | 401 | no |
| **conversational** | request weighted | -0.29 | -0.89 to +0.32 | 0.031 | 270 | no |
| **extractive** | request weighted | -0.45 | -0.88 to -0.02 | 0.207 | 26 | yes |
| **output_heavy** | request weighted | +0.00 | -0.26 to +0.26 | 0.000 | 47 | no |
| **agentic** | unweighted | -0.34 | -0.76 to +0.07 | 0.046 | 58 | no |
| **all** | unweighted | -0.71 | -0.99 to -0.44 | 0.079 | 401 | yes |
| **conversational** | unweighted | -1.08 | -1.38 to -0.79 | 0.191 | 270 | yes |
| **extractive** | unweighted | -0.44 | -0.93 to +0.05 | 0.136 | 26 | no |
| **output_heavy** | unweighted | -0.24 | -0.99 to +0.51 | 0.013 | 47 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.34, interval
-0.76 to +0.07, straddling zero). Weighting by requests, the
elasticity is **-0.65** (-0.77 to -0.53) and
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
| ≥2 days silent | 62 | 378 | 93.1% | 85.6% |
| ≥3 days silent | 54 | 386 | 94.2% | 87.9% |
| ≥7 days silent | 22 | 418 | 97.2% | 93.5% |
| ≥14 days silent | 8 | 432 | 98.6% | 98.6% |

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
