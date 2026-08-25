# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-08-25` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 561 model-variants, 320.40 T
tokens and 18.14 B requests over the trailing 30 days.


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
| **agentic** | 67 | 240.89 T | 75.2% | 51.1 | 47,105 | large contexts, terse output, very large interactions |
| **conversational** | 274 | 75.80 T | 23.7% | 10.0 | 3,754 | moderate context per output token, human-sized interactions |
| **unclassified** | 118 | 2.23 T | 0.7% | — | 26 | insufficient data to classify |
| **extractive** | 27 | 1.35 T | 0.4% | 43.9 | 7,648 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 75 | 143.33 B | 0.0% | 0.4 | 4,585 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **75.2% of all tokens**
while being 67 of 561 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
23.7%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 367.4 | 1,312 | 22.45 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 153.9 | 99,863 | 13.02 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 151.0 | 93,246 | 6.31 T | agentic |
| `xiaomi/mimo-v2.5-20260422` | 127.0 | 73,540 | 28.55 T | agentic |
| `poolside/laguna-xs-2.1-20260625` | 126.6 | 56,447 | 684.76 B | agentic |
| `anthropic/claude-opus-5-fast-20260723` | 101.7 | 89,388 | 142.32 B | agentic |
| `nvidia/nemotron-3.5-lightning-20260807` | 98.6 | 74,208 | 1.75 T | agentic |
| `openai/gpt-5.6-terra-20260709` | 87.8 | 37,555 | 3.07 T | agentic |
| `qwen/qwen3-coder-next-2025-02-03` | 81.4 | 26,537 | 94.47 B | agentic |
| `xiaomi/mimo-v2.5-pro-20260422` | 77.3 | 56,348 | 2.27 T | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
367.4 tokens of context per token written, but its interactions
average only 1,312 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 153.9 tokens of context per token
written, in interactions averaging 99,863 tokens, which
is 76× larger.
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


Across 222 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.95** with a p25–p75 range of 0.71–1.18.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 18 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **2.14×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-audio-mini` | 11.71× | 2.03 B | 218 | output_heavy |
| `openai/gpt-5-nano-2025-08-07` | 6.70× | 3.60 B | 383 | conversational |
| `openai/gpt-5.6-luna-20260709` | 5.22× | 11.74 B | 47 | output_heavy |
| `anthropic/claude-4.5-opus-20251124` | 5.00× | 84.33 B | 274 | agentic |
| `bytedance-seed/seed-2.0-mini-20260224` | 3.96× | 21.64 B | 180 | conversational |
| `meta/muse-spark-1.2-20260805` | 3.50× | 256.84 B | 20 | agentic |
| `mistralai/mistral-small-24b-instruct-2501` | 2.58× | 32.03 B | 572 | conversational |
| `qwen/qwen3-max` | 2.35× | 11.92 B | 336 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-5.2-chat-20251211` | 0.00× | 5.72 B | 258 | conversational |
| `perceptron/perceptron-mk1-20260512` | 0.07× | 6.66 B | 105 | extractive |
| `google/gemma-4-26b-a4b-it-20260403` | 0.08× | 56.91 B | 144 | conversational |
| `thinkingmachines/inkling-small-20260730` | 0.15× | 31.55 B | 26 | conversational |
| `inclusionai/ling-2.6-1t-20260423` | 0.19× | 13.48 B | 124 | conversational |
| `meta/muse-glimmer-30b-20260810` | 0.21× | 69.61 B | 16 | conversational |
| `nvidia/nemotron-3-nano-30b-a3b` | 0.21× | 57.81 B | 254 | conversational |
| `mistralai/mistral-large` | 0.22× | 4.04 B | 911 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$209.6 M per month** across
403 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 6.9% | 39.4% | 5.71x |
| `openai` | 11.0% | 12.2% | 1.11x |
| `z-ai` | 5.3% | 9.7% | 1.85x |
| `moonshotai` | 2.4% | 9.7% | 4.11x |
| `deepseek` | 23.7% | 9.3% | 0.39x |
| `google` | 8.3% | 5.7% | 0.68x |
| `nvidia` | 5.4% | 3.9% | 0.73x |
| `xiaomi` | 9.7% | 2.4% | 0.25x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**2,611**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **47.3%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.934** by value. Both are extreme; a
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
**8.17%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.00% |
| **extractive** | 3.57% |
| **output_heavy** | 2.14% |
| **conversational** | 1.81% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 786 endpoints serving multi-provider models,
**519 are dominated** (66.0%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.2-20260616` | Z.AI | $4.40 | 41 tok/s | Ambient | 24 |
| `z-ai/glm-5.2-20260616` | Fireworks | $4.40 | 44 tok/s | Ambient | 23 |
| `z-ai/glm-5.2-20260616` | Baidu | $4.40 | 54 tok/s | Ambient | 18 |
| `z-ai/glm-5.2-20260616` | Cloudflare | $4.40 | 56 tok/s | Ambient | 16 |
| `moonshotai/kimi-k2.6-20260420` | Baidu | $4.00 | 16 tok/s | Decart | 16 |
| `moonshotai/kimi-k2.6-20260420` | Phala | $4.60 | 18 tok/s | Decart | 16 |
| `google/gemma-4-31b-it-20260402` | SambaNova | $1.15 | 12 tok/s | DeepInfra | 15 |
| `z-ai/glm-5.1-20260406` | Z.AI | $4.40 | 19 tok/s | GMICloud | 14 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-08-24` and `2026-08-25`,
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
| **agentic** | request weighted | -0.53 | -0.71 to -0.36 | 0.417 | 55 | yes |
| **all** | request weighted | -0.14 | -0.59 to +0.31 | 0.009 | 370 | no |
| **conversational** | request weighted | -0.31 | -0.99 to +0.37 | 0.034 | 253 | no |
| **extractive** | request weighted | +0.21 | -0.72 to +1.14 | 0.017 | 24 | no |
| **output_heavy** | request weighted | -0.02 | -0.34 to +0.29 | 0.001 | 38 | no |
| **agentic** | unweighted | -0.17 | -0.51 to +0.18 | 0.015 | 55 | no |
| **all** | unweighted | -0.50 | -0.75 to -0.26 | 0.052 | 370 | yes |
| **conversational** | unweighted | -0.69 | -0.94 to -0.44 | 0.108 | 253 | yes |
| **extractive** | unweighted | -0.19 | -0.53 to +0.14 | 0.022 | 24 | no |
| **output_heavy** | unweighted | -0.82 | -1.57 to -0.07 | 0.137 | 38 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.17, interval
-0.51 to +0.18, straddling zero). Weighting by requests, the
elasticity is **-0.53** (-0.71 to -0.36) and
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
| ≥2 days silent | 20 | 387 | 97.6% | 95.6% |
| ≥3 days silent | 17 | 390 | 98.3% | 96.8% |
| ≥7 days silent | 6 | 401 | 98.5% | 98.1% |
| ≥14 days silent | 3 | 404 | 99.4% | 98.9% |

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
