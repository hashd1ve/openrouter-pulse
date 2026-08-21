# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-08-21` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 558 model-variants, 292.67 T
tokens and 17.68 B requests over the trailing 30 days.


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
| **agentic** | 63 | 210.69 T | 72.0% | 49.5 | 46,954 | large contexts, terse output, very large interactions |
| **conversational** | 274 | 77.85 T | 26.6% | 9.8 | 3,980 | moderate context per output token, human-sized interactions |
| **unclassified** | 112 | 2.31 T | 0.8% | — | 29 | insufficient data to classify |
| **extractive** | 30 | 1.68 T | 0.6% | 35.8 | 8,418 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 79 | 132.20 B | 0.0% | 0.6 | 4,565 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **72.0% of all tokens**
while being 63 of 558 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
26.6%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 355.8 | 1,289 | 23.25 B | extractive |
| `poolside/laguna-s-2.1-20260720` | 152.9 | 94,139 | 5.63 T | agentic |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 143.2 | 95,460 | 11.34 T | agentic |
| `poolside/laguna-xs-2.1-20260625` | 127.5 | 57,546 | 698.73 B | agentic |
| `xiaomi/mimo-v2.5-20260422` | 121.0 | 70,535 | 28.59 T | agentic |
| `poolside/laguna-m.1-20260312` | 120.0 | 55,942 | 112.11 B | agentic |
| `anthropic/claude-opus-5-fast-20260723` | 101.3 | 89,637 | 135.85 B | agentic |
| `nvidia/nemotron-3.5-lightning-20260807` | 96.6 | 75,975 | 1.11 T | agentic |
| `openai/gpt-5.6-terra-20260709` | 91.6 | 39,859 | 2.86 T | agentic |
| `stepfun/step-3.7-flash-20260528` | 84.9 | 70,392 | 5.75 T | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
355.8 tokens of context per token written, but its interactions
average only 1,289 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `poolside/laguna-s-2.1-20260720`: 152.9 tokens of context per token
written, in interactions averaging 94,139 tokens, which
is 73× larger.
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


Across 223 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.95** with a p25–p75 range of 0.74–1.15.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 18 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **2.61×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-5.6-sol-20260709` | 2.29× | 2.96 T | 43 | agentic |
| `z-ai/glm-5v-turbo-20260401` | 2.26× | 78.01 B | 142 | agentic |
| `qwen/qwen3.8-27b-20260814` | 2.17× | 90.76 B | 7 | conversational |
| `inclusionai/ling-3.0-flash-20260723` | 2.14× | 161.40 B | 29 | conversational |
| `meta-llama/llama-3.2-1b-instruct` | 2.13× | 2.36 B | 695 | output_heavy |
| `meta/muse-spark-1.2-20260805` | 1.98× | 186.29 B | 16 | agentic |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 1.94× | 11.34 T | 78 | agentic |
| `openai/gpt-4.1-nano-2025-04-14` | 1.72× | 118.38 B | 494 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-5.2-chat-20251211` | 0.00× | 6.73 B | 254 | conversational |
| `openai/gpt-4o-2024-05-13` | 0.08× | 3.84 B | 830 | extractive |
| `google/gemma-3-4b-it` | 0.20× | 24.07 B | 526 | conversational |
| `google/gemma-2-27b-it` | 0.20× | 618.71 M | 769 | conversational |
| `nvidia/nemotron-3-nano-30b-a3b` | 0.22× | 74.49 B | 250 | conversational |
| `deepseek/deepseek-v3.1-terminus` | 0.27× | 118.24 B | 333 | conversational |
| `mistralai/mistral-medium-3.5-20260430` | 0.28× | 37.59 B | 113 | conversational |
| `amazon/nova-2-lite-v1` | 0.30× | 7.82 B | 262 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$208.7 M per month** across
401 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 7.7% | 34.6% | 4.49x |
| `deepseek` | 24.1% | 13.7% | 0.57x |
| `openai` | 11.3% | 12.6% | 1.11x |
| `moonshotai` | 2.7% | 9.7% | 3.64x |
| `z-ai` | 5.8% | 8.0% | 1.37x |
| `google` | 8.9% | 6.6% | 0.75x |
| `nvidia` | 5.1% | 3.4% | 0.67x |
| `xiaomi` | 10.7% | 2.4% | 0.23x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**2,644**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **47.8%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.939** by value. Both are extreme; a
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
**8.41%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.32% |
| **extractive** | 4.08% |
| **output_heavy** | 2.82% |
| **conversational** | 1.88% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 730 endpoints serving multi-provider models,
**485 are dominated** (66.4%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.2-20260616` | Cloudflare | $4.40 | 34 tok/s | DigitalOcean | 22 |
| `z-ai/glm-5.2-20260616` | Venice | $4.40 | 41 tok/s | DigitalOcean | 21 |
| `z-ai/glm-5.2-20260616` | Fireworks | $4.40 | 47 tok/s | DigitalOcean | 18 |
| `deepseek/deepseek-v4-flash-20260731` | Cloudflare | $1.32 | 57 tok/s | Relace | 16 |
| `z-ai/glm-5.1-20260406` | Z.AI | $4.40 | 19 tok/s | GMICloud | 15 |
| `z-ai/glm-5.2-20260616` | Baidu | $4.40 | 53 tok/s | DigitalOcean | 15 |
| `~deepseek/deepseek-v4-flash-latest` | Cloudflare | $1.32 | 56 tok/s | Relace | 15 |
| `~deepseek/deepseek-v4-flash-latest` | Alibaba | $1.21 | 51 tok/s | Relace | 15 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-08-20` and `2026-08-21`,
**1.13%** of 441 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.51 | -0.67 to -0.36 | 0.389 | 56 | yes |
| **all** | request weighted | -0.13 | -0.57 to +0.30 | 0.009 | 376 | no |
| **conversational** | request weighted | -0.25 | -0.89 to +0.38 | 0.029 | 256 | no |
| **extractive** | request weighted | +0.09 | -0.37 to +0.56 | 0.006 | 26 | no |
| **output_heavy** | request weighted | +0.01 | -0.39 to +0.41 | 0.000 | 38 | no |
| **agentic** | unweighted | -0.27 | -0.58 to +0.05 | 0.029 | 56 | no |
| **all** | unweighted | -0.50 | -0.76 to -0.25 | 0.047 | 376 | yes |
| **conversational** | unweighted | -0.68 | -0.95 to -0.40 | 0.096 | 256 | yes |
| **extractive** | unweighted | -0.28 | -0.60 to +0.04 | 0.056 | 26 | no |
| **output_heavy** | unweighted | -0.54 | -1.30 to +0.23 | 0.060 | 38 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.27, interval
-0.58 to +0.05, straddling zero). Weighting by requests, the
elasticity is **-0.51** (-0.67 to -0.36) and
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
| ≥2 days silent | 16 | 387 | 97.3% | 95.8% |
| ≥3 days silent | 11 | 392 | 97.6% | 96.1% |
| ≥7 days silent | 8 | 395 | 98.6% | 97.1% |
| ≥14 days silent | 5 | 398 | 99.5% | 97.9% |

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
