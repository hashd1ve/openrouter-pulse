# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-10-25` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 726 model-variants, 729.25 T
tokens and 35.36 B requests over the trailing 30 days.


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
| **agentic** | 92 | 543.49 T | 74.5% | 53.5 | 53,116 | large contexts, terse output, very large interactions |
| **conversational** | 327 | 164.36 T | 22.5% | 9.2 | 3,945 | moderate context per output token, human-sized interactions |
| **extractive** | 37 | 17.75 T | 2.4% | 41.8 | 4,947 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 158 | 3.47 T | 0.5% | — | 32 | insufficient data to classify |
| **output_heavy** | 112 | 185.65 B | 0.0% | 0.3 | 3,809 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **74.5% of all tokens**
while being 92 of 726 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
22.5%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `upstage/solar-decide-20260928` | 2,159.7 | 4,947 | 22.01 B | extractive |
| `scaledown/classify-1-20260928` | 2,135.9 | 7,296 | 11.78 B | extractive |
| `upstage/solar-decide-flash-20261008` | 1,482.5 | 3,491 | 8.79 B | extractive |
| `perplexity/pplx-decider-v1-27b-20261001` | 1,155.6 | 4,655 | 9.10 B | extractive |
| `perplexity/pplx-decider-v1.1-27b-20261006` | 1,141.1 | 3,834 | 257.20 B | extractive |
| `perplexity/pplx-decider-flash-v1.2-20261016` | 1,059.7 | 2,770 | 27.66 B | extractive |
| `perplexity/pplx-decider-v1.2-20261016` | 518.1 | 1,974 | 162.80 B | extractive |
| `togethercomputer/tev1-4b-experimental-20260923` | 493.6 | 2,448 | 7.44 B | extractive |
| `inception/mercury-decide-20260930` | 365.6 | 4,487 | 115.21 B | extractive |
| `inception/mercury-decide-20260930` | 348.0 | 1,262 | 46.25 B | extractive |

**Why both axes.** The top of this ranking is `upstage/solar-decide-20260928` at
2,159.7 tokens of context per token written, but its interactions
average only 4,947 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 189.3 tokens of context per token
written, in interactions averaging 134,370 tokens, which
is 27× larger.
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


Across 259 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.73** with a p25–p75 range of 0.52–0.97.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 20 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **2.04×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `nex-agi/nex-n2.5-mini-20260908` | 7.95× | 11.05 B | 47 | conversational |
| `deepseek/deepseek-v4.1-flash-20260910` | 5.07× | 23.34 B | 45 | output_heavy |
| `z-ai/glm-5.3-flash-20260826` | 4.59× | 16.98 B | 60 | conversational |
| `stepfun/step-3.7-flash-20260528` | 3.19× | 367.46 B | 150 | conversational |
| `anthropic/claude-haiku-5.5-20261007` | 3.13× | 72.47 B | 18 | conversational |
| `qwen/qwen-2.5-7b-instruct` | 2.76× | 17.99 B | 739 | conversational |
| `google/gemini-3.1-flash-lite-20260507` | 2.33× | 19.88 B | 171 | conversational |
| `scaledown/summarize-20260928` | 2.05× | 12.21 B | 12 | extractive |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `nvidia/nemotron-3-super-120b-a12b-20230311` | 0.00× | 2.01 T | 228 | agentic |
| `openai/gpt-5-nano-2025-08-07` | 0.01× | 10.77 B | 444 | conversational |
| `xiaomi/mimo-v2.5-20260422` | 0.03× | 2.89 T | 186 | agentic |
| `perceptron/perceptron-mk1-20260512` | 0.04× | 7.00 B | 166 | extractive |
| `inclusionai/ling-3.0-flash-vl-20260910` | 0.06× | 122.63 B | 45 | conversational |
| `openai/gpt-6-sol-20260922` | 0.08× | 6.91 B | 33 | conversational |
| `inclusionai/ling-3.1-flash-20261002` | 0.09× | 1.12 T | 23 | conversational |
| `openai/gpt-5.6-sol-pro-20260709` | 0.09× | 104.82 B | 108 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$356.7 M per month** across
485 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 6.8% | 37.4% | 5.51x |
| `openai` | 10.1% | 21.1% | 2.08x |
| `tencent` | 6.2% | 8.3% | 1.33x |
| `stepfun` | 3.3% | 6.6% | 1.98x |
| `moonshotai` | 1.4% | 6.2% | 4.46x |
| `deepseek` | 28.3% | 5.0% | 0.18x |
| `google` | 4.0% | 3.7% | 0.91x |
| `xiaomi` | 7.1% | 3.1% | 0.43x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,338**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **55.1%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.932** by value. Both are extreme; a
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
**6.49%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.12% |
| **extractive** | 1.95% |
| **conversational** | 1.72% |
| **output_heavy** | 0.38% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,097 endpoints serving multi-provider models,
**749 are dominated** (68.3%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-20260816` | Alibaba | $8.80 | 55 tok/s | Wafer | 34 |
| `~z-ai/glm-latest` | Alibaba | $8.80 | 54 tok/s | Wafer | 34 |
| `~z-ai/glm-latest` | Morph | $4.40 | 42 tok/s | Wafer | 34 |
| `z-ai/glm-5.3-20260816` | Morph | $4.40 | 41 tok/s | Wafer | 33 |
| `z-ai/glm-5.3-flash-20260826` | Near AI | $0.50 | 13 tok/s | OpenInference | 32 |
| `~z-ai/glm-flash-latest` | Near AI | $0.50 | 13 tok/s | OpenInference | 32 |
| `deepseek/deepseek-v4.1-flash-20261017` | SiliconFlow | $1.20 | 25 tok/s | Sail Research | 32 |
| `~deepseek/deepseek-flash-latest` | SiliconFlow | $1.20 | 24 tok/s | Sail Research | 32 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-10-24` and `2026-10-25`,
**1.41%** of 568 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.62 | -0.94 to -0.30 | 0.438 | 81 | yes |
| **all** | request weighted | -0.50 | -0.94 to -0.07 | 0.097 | 452 | yes |
| **conversational** | request weighted | -0.63 | -1.18 to -0.07 | 0.126 | 299 | yes |
| **extractive** | request weighted | -0.98 | -1.49 to -0.46 | 0.360 | 21 | yes |
| **output_heavy** | request weighted | -0.32 | -0.44 to -0.21 | 0.289 | 51 | yes |
| **agentic** | unweighted | -0.47 | -0.81 to -0.12 | 0.079 | 81 | yes |
| **all** | unweighted | -0.89 | -1.23 to -0.56 | 0.068 | 452 | yes |
| **conversational** | unweighted | -0.85 | -1.18 to -0.52 | 0.078 | 299 | yes |
| **extractive** | unweighted | -0.00 | -0.71 to +0.70 | 0.000 | 21 | no |
| **output_heavy** | unweighted | -1.02 | -2.06 to +0.02 | 0.067 | 51 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.47, interval
-0.81 to -0.12, straddling zero). Weighting by requests, the
elasticity is **-0.62** (-0.94 to -0.30) and
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
| ≥2 days silent | 85 | 401 | 92.6% | 85.4% |
| ≥3 days silent | 74 | 412 | 92.6% | 86.7% |
| ≥7 days silent | 64 | 422 | 93.3% | 87.4% |
| ≥14 days silent | 51 | 435 | 95.5% | 90.4% |

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
