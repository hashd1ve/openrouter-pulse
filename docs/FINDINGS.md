# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-10-04` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 655 model-variants, 592.47 T
tokens and 27.51 B requests over the trailing 30 days.


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
| **agentic** | 93 | 471.75 T | 79.6% | 54.4 | 53,117 | large contexts, terse output, very large interactions |
| **conversational** | 305 | 116.90 T | 19.7% | 9.9 | 4,094 | moderate context per output token, human-sized interactions |
| **unclassified** | 134 | 2.62 T | 0.4% | — | 37 | insufficient data to classify |
| **extractive** | 24 | 1.06 T | 0.2% | 41.5 | 5,112 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 99 | 147.48 B | 0.0% | 0.5 | 4,495 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **79.6% of all tokens**
while being 93 of 655 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
19.7%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 237.1 | 796 | 8.88 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 205.8 | 131,100 | 20.06 T | agentic |
| `upstage/solar-mini4-20260922` | 132.2 | 60,015 | 346.16 B | agentic |
| `thinkingmachines/inkling-small-20260730` | 125.3 | 57,037 | 501.77 B | agentic |
| `minimax/minimax-m3-20260531` | 120.7 | 75,486 | 2.51 T | agentic |
| `tencent/hy4-preview-20260827` | 112.6 | 115,739 | 51.28 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 108.5 | 81,982 | 4.77 T | agentic |
| `xiaomi/mimo-v2.5-20260422` | 106.7 | 66,557 | 19.04 T | agentic |
| `openai/gpt-6-astra-20260903` | 106.3 | 65,765 | 4.97 T | agentic |
| `deepseek/deepseek-v4-flash-20260731` | 105.4 | 98,351 | 1.09 T | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
237.1 tokens of context per token written, but its interactions
average only 796 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 205.8 tokens of context per token
written, in interactions averaging 131,100 tokens, which
is 165× larger.
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
median of **0.74** with a p25–p75 range of 0.51–1.00.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 15 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **2.31×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `qwen/qwen3.8-27b-20260814` | 10.64× | 178.89 B | 51 | agentic |
| `openai/gpt-5.3-codex-20260224` | 6.20× | 196.64 B | 222 | agentic |
| `amazon/nova-2-lite-v1` | 4.97× | 5.52 B | 306 | conversational |
| `upstage/solar-mini4-20260922` | 4.36× | 346.16 B | 11 | agentic |
| `ibm-granite/granite-4.2-8b-20260831` | 3.09× | 22.64 B | 34 | conversational |
| `stepfun/step-3.7-flash-20260528` | 2.93× | 358.09 B | 129 | conversational |
| `bytedance-seed/seed-2.0-lite-20260309` | 2.87× | 7.89 B | 208 | conversational |
| `inclusionai/ling-3.0-flash-vl-20260910` | 2.15× | 43.26 B | 24 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `tencent/hy-mt2-1.8b-20260521` | 0.06× | 3.03 B | 45 | conversational |
| `openai/gpt-5-nano-2025-08-07` | 0.07× | 3.52 B | 423 | conversational |
| `upstage/solar-pro4-20260810` | 0.11× | 6.18 T | 55 | agentic |
| `tencent/hy-mt2-7b-20260521` | 0.11× | 2.42 B | 46 | conversational |
| `openai/gpt-5.6-luna-20260709` | 0.13× | 46.16 T | 87 | agentic |
| `openai/gpt-5.6-sol-20260709` | 0.13× | 4.61 B | 87 | conversational |
| `openai/gpt-5.6-terra-pro-20260709` | 0.19× | 71.18 B | 87 | agentic |
| `xiaomi/mimo-v2.5-20260422` | 0.20× | 19.04 T | 165 | agentic |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$279.2 M per month** across
451 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 3.9% | 29.3% | 7.50x |
| `openai` | 14.2% | 21.1% | 1.48x |
| `tencent` | 11.2% | 16.3% | 1.45x |
| `z-ai` | 13.1% | 9.3% | 0.71x |
| `google` | 5.1% | 6.3% | 1.23x |
| `deepseek` | 22.5% | 6.2% | 0.28x |
| `moonshotai` | 1.3% | 2.6% | 1.94x |
| `xiaomi` | 6.2% | 2.3% | 0.38x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**4,280**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **64.1%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.943** by value. Both are extreme; a
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
**6.46%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.25% |
| **extractive** | 2.99% |
| **conversational** | 1.69% |
| **output_heavy** | 1.31% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,062 endpoints serving multi-provider models,
**741 are dominated** (69.8%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-flash-20260826` | OpenInference | $0.65 | 14 tok/s | DeepInfra | 31 |
| `~z-ai/glm-flash-latest` | OpenInference | $0.65 | 14 tok/s | DeepInfra | 31 |
| `deepseek/deepseek-v4.1-flash-20260910` | DekaLLM | $2.40 | 30 tok/s | Decart | 28 |
| `~deepseek/deepseek-flash-latest` | DekaLLM | $2.40 | 30 tok/s | Decart | 28 |
| `z-ai/glm-5.3-20260816` | AtlasCloud | $4.40 | 48 tok/s | SiliconFlow | 28 |
| `~z-ai/glm-latest` | AtlasCloud | $4.40 | 48 tok/s | SiliconFlow | 28 |
| `z-ai/glm-5.3-20260816` | Fireworks | $4.40 | 53 tok/s | SiliconFlow | 27 |
| `~z-ai/glm-latest` | Fireworks | $4.40 | 53 tok/s | SiliconFlow | 27 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-10-03` and `2026-10-04`,
**0.58%** of 520 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.46 | -0.67 to -0.25 | 0.236 | 80 | yes |
| **all** | request weighted | +0.25 | -0.18 to +0.67 | 0.018 | 423 | no |
| **conversational** | request weighted | +0.57 | +0.00 to +1.14 | 0.089 | 280 | yes |
| **extractive** | request weighted | +0.08 | -0.64 to +0.80 | 0.004 | 16 | no |
| **output_heavy** | request weighted | -0.06 | -0.40 to +0.28 | 0.005 | 47 | no |
| **agentic** | unweighted | -0.56 | -0.87 to -0.24 | 0.112 | 80 | yes |
| **all** | unweighted | -0.39 | -0.65 to -0.13 | 0.022 | 423 | yes |
| **conversational** | unweighted | -0.58 | -0.88 to -0.28 | 0.068 | 280 | yes |
| **extractive** | unweighted | -0.30 | -0.93 to +0.33 | 0.033 | 16 | no |
| **output_heavy** | unweighted | +0.33 | -0.51 to +1.18 | 0.011 | 47 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.56, interval
-0.87 to -0.24, straddling zero). Weighting by requests, the
elasticity is **-0.46** (-0.67 to -0.25) and
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
| ≥2 days silent | 56 | 397 | 90.1% | 86.3% |
| ≥3 days silent | 55 | 398 | 90.1% | 86.8% |
| ≥7 days silent | 40 | 413 | 92.0% | 90.6% |
| ≥14 days silent | 21 | 432 | 96.0% | 94.9% |

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
