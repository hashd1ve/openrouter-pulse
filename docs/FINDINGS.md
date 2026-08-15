# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-08-15` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 558 model-variants, 274.31 T
tokens and 17.12 B requests over the trailing 30 days.


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
| **agentic** | 64 | 203.32 T | 74.1% | 50.7 | 46,570 | large contexts, terse output, very large interactions |
| **conversational** | 270 | 67.15 T | 24.5% | 10.0 | 4,119 | moderate context per output token, human-sized interactions |
| **unclassified** | 112 | 2.30 T | 0.8% | — | 29 | insufficient data to classify |
| **extractive** | 32 | 1.40 T | 0.5% | 40.5 | 8,629 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 80 | 144.17 B | 0.1% | 0.6 | 4,489 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **74.1% of all tokens**
while being 64 of 558 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
24.5%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 317.0 | 1,172 | 22.46 B | extractive |
| `poolside/laguna-s-2.1-20260720` | 160.0 | 94,603 | 4.19 T | agentic |
| `poolside/laguna-m.1-20260312` | 140.1 | 69,027 | 606.36 B | agentic |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 138.6 | 94,785 | 10.16 T | agentic |
| `xiaomi/mimo-v2.5-20260422` | 118.3 | 68,473 | 30.17 T | agentic |
| `poolside/laguna-xs-2.1-20260625` | 116.8 | 57,272 | 654.66 B | agentic |
| `nvidia/nemotron-3.5-lightning-20260807` | 101.3 | 75,851 | 373.47 B | agentic |
| `anthropic/claude-opus-5-fast-20260723` | 98.9 | 86,664 | 113.44 B | agentic |
| `perceptron/perceptron-mk1-20260512` | 92.2 | 8,836 | 9.42 B | extractive |
| `stepfun/step-3.7-flash-20260528` | 87.8 | 69,171 | 6.01 T | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
317.0 tokens of context per token written, but its interactions
average only 1,172 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `poolside/laguna-s-2.1-20260720`: 160.0 tokens of context per token
written, in interactions averaging 94,603 tokens, which
is 81× larger.
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


Across 212 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.92** with a p25–p75 range of 0.74–1.13.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 13 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.36×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `nex-agi/nex-n2-mini` | 6.05× | 58.41 B | 52 | conversational |
| `inclusionai/ling-3.0-flash-20260723` | 3.41× | 93.69 B | 23 | conversational |
| `google/gemini-3.6-flash-20260721` | 2.75× | 4.65 T | 25 | agentic |
| `z-ai/glm-5v-turbo-20260401` | 2.29× | 56.88 B | 136 | agentic |
| `qwen/qwen3.5-plus-20260216` | 2.21× | 27.78 B | 180 | conversational |
| `google/gemma-3-27b-it` | 2.15× | 239.03 B | 521 | conversational |
| `meta-llama/llama-4-scout-17b-16e-instruct` | 2.10× | 95.76 B | 497 | extractive |
| `openai/gpt-5.6-luna-pro-20260709` | 2.10× | 1.36 T | 37 | agentic |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-5.2-chat-20251211` | 0.00× | 8.69 B | 248 | conversational |
| `ibm-granite/granite-4.0-h-micro` | 0.07× | 18.43 B | 299 | extractive |
| `perceptron/perceptron-mk1-20260512` | 0.14× | 9.42 B | 95 | extractive |
| `nvidia/nemotron-3-nano-30b-a3b` | 0.14× | 86.01 B | 244 | conversational |
| `meta/muse-spark-1.1-20260709` | 0.15× | 174.22 B | 30 | agentic |
| `openai/gpt-4o-2024-05-13` | 0.22× | 3.85 B | 824 | extractive |
| `amazon/nova-2-lite-v1` | 0.22× | 10.92 B | 256 | conversational |
| `google/gemma-2-27b-it` | 0.23× | 698.46 M | 763 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$179.2 M per month** across
399 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 8.4% | 39.8% | 4.74x |
| `openai` | 10.0% | 12.7% | 1.27x |
| `deepseek` | 22.1% | 11.7% | 0.53x |
| `moonshotai` | 2.8% | 10.6% | 3.77x |
| `z-ai` | 6.1% | 6.7% | 1.10x |
| `google` | 8.6% | 4.6% | 0.53x |
| `xiaomi` | 12.0% | 3.0% | 0.25x |
| `tencent` | 12.3% | 2.6% | 0.21x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**2,462**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **44.7%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.934** by value. Both are extreme; a
national income distribution above 0.6 is considered severe.


### The sticker price is not the price

Traffic is overwhelmingly prompt-heavy, and prompt tokens cost less than
completions. Blended across each model's real token mix, the price actually paid
per token is a median **0.34x** the headline output price, so the
sticker overstates unit cost by about **3.0x**.

Anyone comparing models on `$/M output` is getting this wrong.


## 5. The context window arms race is mostly unused

Dividing mean tokens per request by the advertised context length asks how much
of the window the traffic actually touches. Token-weighted across the market:
**8.78%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 8.15% |
| **extractive** | 5.00% |
| **output_heavy** | 2.00% |
| **conversational** | 1.91% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 699 endpoints serving multi-provider models,
**458 are dominated** (65.5%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `deepseek/deepseek-v4-flash-20260731` | Mancer 2 | $0.50 | 23 tok/s | StreamLake | 25 |
| `~deepseek/deepseek-v4-flash-latest` | Mancer 2 | $0.50 | 23 tok/s | StreamLake | 25 |
| `z-ai/glm-5.2-20260616` | Z.AI | $4.40 | 30 tok/s | Baidu | 23 |
| `z-ai/glm-5.2-20260616` | Alibaba | $7.26 | 45 tok/s | Baidu | 22 |
| `deepseek/deepseek-v4-flash-20260731` | Ambient | $0.28 | 33 tok/s | StreamLake | 20 |
| `~deepseek/deepseek-v4-flash-latest` | Ambient | $0.28 | 33 tok/s | StreamLake | 20 |
| `deepseek/deepseek-v4-flash-20260731` | AkashML | $0.28 | 40 tok/s | StreamLake | 18 |
| `~deepseek/deepseek-v4-flash-latest` | AkashML | $0.28 | 40 tok/s | StreamLake | 18 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-08-14` and `2026-08-15`,
**1.81%** of 442 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.44 | -0.60 to -0.29 | 0.356 | 57 | yes |
| **all** | request weighted | -0.24 | -0.75 to +0.28 | 0.027 | 369 | no |
| **conversational** | request weighted | -0.49 | -1.26 to +0.27 | 0.093 | 245 | no |
| **extractive** | request weighted | +0.13 | -0.38 to +0.64 | 0.012 | 27 | no |
| **output_heavy** | request weighted | +0.04 | -0.20 to +0.29 | 0.003 | 40 | no |
| **agentic** | unweighted | -0.20 | -0.68 to +0.27 | 0.009 | 57 | no |
| **all** | unweighted | -0.58 | -0.82 to -0.34 | 0.055 | 369 | yes |
| **conversational** | unweighted | -0.79 | -1.04 to -0.54 | 0.109 | 245 | yes |
| **extractive** | unweighted | +0.05 | -0.45 to +0.55 | 0.001 | 27 | no |
| **output_heavy** | unweighted | -0.90 | -1.60 to -0.21 | 0.148 | 40 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.20, interval
-0.68 to +0.27, straddling zero). Weighting by requests, the
elasticity is **-0.44** (-0.60 to -0.29) and
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
| ≥2 days silent | 30 | 371 | 95.5% | 91.6% |
| ≥3 days silent | 24 | 377 | 97.0% | 93.1% |
| ≥7 days silent | 16 | 385 | 98.6% | 95.8% |
| ≥14 days silent | 13 | 388 | 98.9% | 96.1% |

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
