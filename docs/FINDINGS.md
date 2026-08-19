# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-08-19` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 557 model-variants, 285.23 T
tokens and 17.41 B requests over the trailing 30 days.


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
| **agentic** | 64 | 202.63 T | 71.0% | 51.0 | 47,110 | large contexts, terse output, very large interactions |
| **conversational** | 274 | 78.97 T | 27.7% | 9.9 | 4,188 | moderate context per output token, human-sized interactions |
| **unclassified** | 113 | 2.31 T | 0.8% | — | 31 | insufficient data to classify |
| **extractive** | 28 | 1.17 T | 0.4% | 37.8 | 7,941 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 78 | 143.32 B | 0.1% | 0.6 | 4,574 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **71.0% of all tokens**
while being 64 of 557 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
27.7%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 347.5 | 1,267 | 23.15 B | extractive |
| `poolside/laguna-s-2.1-20260720` | 153.6 | 94,292 | 5.14 T | agentic |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 137.2 | 92,280 | 10.35 T | agentic |
| `poolside/laguna-m.1-20260312` | 136.2 | 64,517 | 250.99 B | agentic |
| `poolside/laguna-xs-2.1-20260625` | 124.4 | 57,564 | 687.16 B | agentic |
| `xiaomi/mimo-v2.5-20260422` | 118.5 | 69,189 | 28.98 T | agentic |
| `anthropic/claude-opus-5-fast-20260723` | 99.3 | 87,660 | 125.77 B | agentic |
| `nvidia/nemotron-3.5-lightning-20260807` | 97.1 | 76,326 | 856.46 B | agentic |
| `openai/gpt-5.6-terra-20260709` | 88.9 | 38,952 | 2.68 T | agentic |
| `stepfun/step-3.7-flash-20260528` | 87.2 | 70,112 | 6.04 T | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
347.5 tokens of context per token written, but its interactions
average only 1,267 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `poolside/laguna-s-2.1-20260720`: 153.6 tokens of context per token
written, in interactions averaging 94,292 tokens, which
is 74× larger.
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


Across 217 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **1.00** with a p25–p75 range of 0.76–1.23.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 18 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.54×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `thinkingmachines/inkling-small-20260730` | 6.39× | 27.17 B | 20 | conversational |
| `google/gemma-3-12b-it` | 3.27× | 98.35 B | 524 | conversational |
| `qwen/qwen3-vl-30b-a3b-instruct` | 2.90× | 44.01 B | 317 | conversational |
| `thinkingmachines/inkling-20260715` | 2.61× | 74.93 B | 33 | conversational |
| `bytedance-seed/seed-2.0-lite-20260309` | 2.52× | 7.38 B | 162 | conversational |
| `meta/muse-spark-1.1-20260709` | 2.45× | 164.16 B | 34 | agentic |
| `nex-agi/nex-n2-mini` | 2.33× | 96.56 B | 56 | conversational |
| `openai/gpt-5.6-luna-pro-20260709` | 2.26× | 1.67 T | 41 | agentic |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-5.2-chat-20251211` | 0.00× | 7.39 B | 252 | conversational |
| `openai/gpt-4o-2024-05-13` | 0.09× | 3.86 B | 828 | extractive |
| `openai/gpt-5-nano-2025-08-07` | 0.12× | 2.29 B | 377 | conversational |
| `google/gemma-2-27b-it` | 0.23× | 683.34 M | 767 | conversational |
| `deepseek/deepseek-v3.1-terminus` | 0.24× | 127.96 B | 331 | conversational |
| `mistralai/mistral-medium-3` | 0.24× | 2.61 B | 469 | conversational |
| `nvidia/nemotron-3.5-lightning-20260807` | 0.29× | 75.57 B | 8 | agentic |
| `nvidia/nemotron-3-nano-30b-a3b` | 0.36× | 79.03 B | 248 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$195.9 M per month** across
399 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 8.0% | 38.0% | 4.72x |
| `deepseek` | 23.5% | 13.0% | 0.55x |
| `moonshotai` | 2.7% | 10.3% | 3.74x |
| `openai` | 11.0% | 9.9% | 0.90x |
| `z-ai` | 5.9% | 8.3% | 1.41x |
| `google` | 8.9% | 5.6% | 0.63x |
| `nvidia` | 4.8% | 3.4% | 0.70x |
| `xiaomi` | 11.1% | 2.6% | 0.24x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,007**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **52.2%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.943** by value. Both are extreme; a
national income distribution above 0.6 is considered severe.


### The sticker price is not the price

Traffic is overwhelmingly prompt-heavy, and prompt tokens cost less than
completions. Blended across each model's real token mix, the price actually paid
per token is a median **0.34x** the headline output price, so the
sticker overstates unit cost by about **2.9x**.

Anyone comparing models on `$/M output` is getting this wrong.


## 5. The context window arms race is mostly unused

Dividing mean tokens per request by the advertised context length asks how much
of the window the traffic actually touches. Token-weighted across the market:
**8.79%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.63% |
| **extractive** | 4.13% |
| **output_heavy** | 2.35% |
| **conversational** | 1.89% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 732 endpoints serving multi-provider models,
**485 are dominated** (66.3%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.2-20260616` | Z.AI | $4.40 | 29 tok/s | Ambient | 21 |
| `z-ai/glm-5.2-20260616` | Venice | $4.40 | 29 tok/s | Ambient | 21 |
| `z-ai/glm-5.2-20260616` | Cloudflare | $4.40 | 35 tok/s | Ambient | 19 |
| `z-ai/glm-5.2-20260616` | Fireworks | $4.40 | 35 tok/s | Ambient | 19 |
| `z-ai/glm-5.2-20260616` | Alibaba | $7.26 | 42 tok/s | Ambient | 18 |
| `deepseek/deepseek-v4-flash-20260731` | Inceptron | $0.28 | 17 tok/s | Decart | 18 |
| `~deepseek/deepseek-v4-flash-latest` | Inceptron | $0.28 | 17 tok/s | Decart | 18 |
| `deepseek/deepseek-v4-flash-20260731` | Mancer 2 | $0.45 | 30 tok/s | Decart | 17 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-08-18` and `2026-08-19`,
**1.35%** of 443 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.52 | -0.68 to -0.36 | 0.410 | 56 | yes |
| **all** | request weighted | -0.17 | -0.65 to +0.31 | 0.014 | 371 | no |
| **conversational** | request weighted | -0.25 | -0.95 to +0.45 | 0.028 | 254 | no |
| **extractive** | request weighted | +0.41 | -0.30 to +1.13 | 0.101 | 24 | no |
| **output_heavy** | request weighted | -0.02 | -0.31 to +0.28 | 0.001 | 37 | no |
| **agentic** | unweighted | -0.29 | -0.78 to +0.19 | 0.022 | 56 | no |
| **all** | unweighted | -0.53 | -0.76 to -0.31 | 0.053 | 371 | yes |
| **conversational** | unweighted | -0.74 | -0.97 to -0.50 | 0.113 | 254 | yes |
| **extractive** | unweighted | -0.34 | -0.70 to +0.03 | 0.071 | 24 | no |
| **output_heavy** | unweighted | -0.66 | -1.42 to +0.10 | 0.076 | 37 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.29, interval
-0.78 to +0.19, straddling zero). Weighting by requests, the
elasticity is **-0.52** (-0.68 to -0.36) and
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
| ≥2 days silent | 24 | 377 | 96.1% | 93.2% |
| ≥3 days silent | 18 | 383 | 97.4% | 95.4% |
| ≥7 days silent | 9 | 392 | 98.6% | 97.0% |
| ≥14 days silent | 7 | 394 | 99.2% | 97.7% |

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
