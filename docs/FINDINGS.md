# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-09-05` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 617 model-variants, 406.67 T
tokens and 20.17 B requests over the trailing 30 days.


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
| **agentic** | 76 | 313.59 T | 77.1% | 55.1 | 50,674 | large contexts, terse output, very large interactions |
| **conversational** | 298 | 89.86 T | 22.1% | 10.1 | 3,944 | moderate context per output token, human-sized interactions |
| **unclassified** | 123 | 2.00 T | 0.5% | — | 32 | insufficient data to classify |
| **extractive** | 25 | 1.07 T | 0.3% | 38.4 | 9,068 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 95 | 156.24 B | 0.0% | 0.5 | 4,443 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **77.1% of all tokens**
while being 76 of 617 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
22.1%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 368.3 | 1,296 | 17.85 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 176.5 | 111,086 | 16.20 T | agentic |
| `xiaomi/mimo-v2.5-20260422` | 137.0 | 70,764 | 27.77 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 135.1 | 87,266 | 6.64 T | agentic |
| `thinkingmachines/inkling-20260715` | 127.0 | 69,232 | 363.45 B | agentic |
| `minimax/minimax-m3-20260531` | 118.9 | 77,100 | 6.59 T | agentic |
| `thinkingmachines/inkling-small-20260730` | 116.6 | 53,554 | 147.55 B | agentic |
| `poolside/laguna-xs-2.1-20260625` | 112.2 | 53,120 | 570.06 B | agentic |
| `tencent/hy4-preview-20260827` | 110.1 | 117,730 | 13.93 T | agentic |
| `anthropic/claude-opus-5-fast-20260723` | 98.7 | 86,926 | 96.42 B | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
368.3 tokens of context per token written, but its interactions
average only 1,296 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 176.5 tokens of context per token
written, in interactions averaging 111,086 tokens, which
is 86× larger.
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
median of **0.98** with a p25–p75 range of 0.73–1.29.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 20 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.33×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `minimax/minimax-m2.7-20260318` | 5.00× | 615.36 B | 171 | agentic |
| `google/gemini-3.6-flash-20260721` | 4.99× | 5.66 B | 46 | conversational |
| `tencent/hy-mt2-1.8b-20260521` | 4.39× | 116.76 M | 16 | conversational |
| `minimax/minimax-m3-20260531` | 4.23× | 6.59 T | 97 | agentic |
| `thinkingmachines/inkling-20260715` | 2.99× | 363.45 B | 50 | agentic |
| `thinkingmachines/inkling-small-20260730` | 2.81× | 147.55 B | 37 | agentic |
| `z-ai/glm-5.3-20260816` | 2.64× | 4.06 T | 18 | agentic |
| `openai/gpt-5-nano-2025-08-07` | 2.42× | 258.36 B | 394 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `z-ai/glm-5v-turbo-20260401` | 0.08× | 91.79 B | 157 | agentic |
| `google/gemma-4-26b-a4b-it-20260403` | 0.09× | 34.91 B | 155 | conversational |
| `google/gemini-3.6-flash-20260721` | 0.12× | 5.37 T | 46 | agentic |
| `meta/muse-glimmer-30b-20260810` | 0.19× | 92.40 B | 27 | conversational |
| `anthropic/claude-4.7-opus-20260416` | 0.20× | 1.26 T | 142 | agentic |
| `thinkingmachines/inkling-20260715` | 0.25× | 95.04 B | 50 | agentic |
| `meta/muse-spark-1.1-20260709` | 0.26× | 119.99 B | 51 | agentic |
| `xiaomi/mimo-v2.5-20260422` | 0.26× | 27.77 T | 136 | agentic |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$219.8 M per month** across
449 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 5.7% | 26.9% | 4.75x |
| `openai` | 12.3% | 11.0% | 0.90x |
| `z-ai` | 8.7% | 10.8% | 1.24x |
| `deepseek` | 21.6% | 10.2% | 0.47x |
| `moonshotai` | 2.0% | 10.2% | 5.12x |
| `google` | 7.7% | 8.4% | 1.09x |
| `tencent` | 11.7% | 7.5% | 0.64x |
| `nvidia` | 5.4% | 4.8% | 0.88x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**2,571**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **47.3%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.936** by value. Both are extreme; a
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
**8.65%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.45% |
| **extractive** | 4.51% |
| **conversational** | 1.81% |
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

Of 917 endpoints serving multi-provider models,
**620 are dominated** (67.6%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.2-20260616` | Alibaba | $7.26 | 28 tok/s | StreamLake | 28 |
| `deepseek/deepseek-v4-flash-20260731` | Phala | $1.32 | 36 tok/s | Baidu | 25 |
| `~deepseek/deepseek-v4-flash-latest` | Phala | $1.32 | 36 tok/s | Baidu | 25 |
| `~z-ai/glm-flash-latest` | NextBit | $0.50 | 6 tok/s | GMICloud | 23 |
| `z-ai/glm-5.2-20260616` | Z.AI | $4.40 | 49 tok/s | StreamLake | 22 |
| `z-ai/glm-5.3-flash-20260826` | NextBit | $0.50 | 6 tok/s | GMICloud | 22 |
| `~z-ai/glm-flash-latest` | Reka | $0.50 | 11 tok/s | GMICloud | 22 |
| `z-ai/glm-5.3-flash-20260826` | Reka | $0.50 | 11 tok/s | GMICloud | 21 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-09-04` and `2026-09-05`,
**2.06%** of 485 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.58 | -0.83 to -0.33 | 0.382 | 63 | yes |
| **all** | request weighted | -0.12 | -0.54 to +0.30 | 0.006 | 417 | no |
| **conversational** | request weighted | -0.31 | -0.92 to +0.30 | 0.037 | 281 | no |
| **extractive** | request weighted | +0.65 | +0.32 to +0.97 | 0.306 | 22 | yes |
| **output_heavy** | request weighted | -0.17 | -0.43 to +0.09 | 0.044 | 51 | no |
| **agentic** | unweighted | -0.45 | -0.84 to -0.06 | 0.075 | 63 | yes |
| **all** | unweighted | -0.77 | -1.03 to -0.50 | 0.089 | 417 | yes |
| **conversational** | unweighted | -1.03 | -1.33 to -0.74 | 0.172 | 281 | yes |
| **extractive** | unweighted | -0.02 | -0.38 to +0.34 | 0.000 | 22 | no |
| **output_heavy** | unweighted | -0.57 | -1.30 to +0.16 | 0.059 | 51 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.45, interval
-0.84 to -0.06, straddling zero). Weighting by requests, the
elasticity is **-0.58** (-0.83 to -0.33) and
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
| ≥2 days silent | 71 | 381 | 91.9% | 83.5% |
| ≥3 days silent | 63 | 389 | 92.7% | 85.3% |
| ≥7 days silent | 50 | 402 | 95.0% | 88.7% |
| ≥14 days silent | 10 | 442 | 98.7% | 98.2% |

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
