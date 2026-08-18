# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-08-18` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 559 model-variants, 280.27 T
tokens and 17.21 B requests over the trailing 30 days.


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
| **agentic** | 64 | 198.05 T | 70.7% | 50.0 | 47,187 | large contexts, terse output, very large interactions |
| **conversational** | 272 | 78.37 T | 28.0% | 9.9 | 4,151 | moderate context per output token, human-sized interactions |
| **unclassified** | 112 | 2.28 T | 0.8% | — | 29 | insufficient data to classify |
| **extractive** | 31 | 1.44 T | 0.5% | 35.9 | 8,406 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 80 | 139.40 B | 0.0% | 0.5 | 4,590 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **70.7% of all tokens**
while being 64 of 559 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
28.0%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 340.5 | 1,247 | 23.12 B | extractive |
| `poolside/laguna-s-2.1-20260720` | 154.9 | 94,373 | 4.89 T | agentic |
| `poolside/laguna-m.1-20260312` | 142.1 | 67,016 | 336.77 B | agentic |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 137.4 | 92,988 | 10.28 T | agentic |
| `poolside/laguna-xs-2.1-20260625` | 122.8 | 57,597 | 678.31 B | agentic |
| `xiaomi/mimo-v2.5-20260422` | 118.1 | 68,818 | 29.01 T | agentic |
| `anthropic/claude-opus-5-fast-20260723` | 99.7 | 87,844 | 122.66 B | agentic |
| `nvidia/nemotron-3.5-lightning-20260807` | 97.5 | 76,367 | 723.74 B | agentic |
| `stepfun/step-3.7-flash-20260528` | 87.8 | 69,866 | 6.04 T | agentic |
| `openai/gpt-5.6-terra-20260709` | 81.7 | 36,034 | 2.56 T | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
340.5 tokens of context per token written, but its interactions
average only 1,247 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `poolside/laguna-s-2.1-20260720`: 154.9 tokens of context per token
written, in interactions averaging 94,373 tokens, which
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


Across 217 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.96** with a p25–p75 range of 0.74–1.20.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 16 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.47×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `google/gemma-3-12b-it` | 3.81× | 89.13 B | 523 | conversational |
| `bytedance-seed/seed-2.0-mini-20260224` | 3.51× | 16.54 B | 173 | conversational |
| `qwen/qwen3-max` | 3.19× | 10.20 B | 329 | conversational |
| `qwen/qwen3-vl-30b-a3b-instruct` | 3.07× | 40.34 B | 316 | conversational |
| `qwen/qwen3.5-plus-20260216` | 3.03× | 30.01 B | 183 | conversational |
| `google/gemini-3.6-flash-20260721` | 2.61× | 5.82 T | 28 | agentic |
| `qwen/qwen3.5-397b-a17b-20260216` | 2.51× | 114.72 B | 183 | conversational |
| `openai/gpt-5.6-luna-20260709` | 2.39× | 13.11 T | 40 | agentic |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-5.2-chat-20251211` | 0.00× | 7.74 B | 251 | conversational |
| `ibm-granite/granite-4.0-h-micro` | 0.09× | 12.85 B | 302 | extractive |
| `nvidia/nemotron-3-nano-30b-a3b` | 0.11× | 80.58 B | 247 | conversational |
| `nvidia/nemotron-3.5-lightning-20260807` | 0.13× | 72.79 B | 7 | agentic |
| `amazon/nova-2-lite-v1` | 0.22× | 9.45 B | 259 | conversational |
| `cohere/command-r7b-12-2024` | 0.23× | 2.51 B | 612 | conversational |
| `deepseek/deepseek-v3.1-terminus` | 0.23× | 132.56 B | 330 | conversational |
| `openai/gpt-4o-2024-05-13` | 0.25× | 3.85 B | 827 | extractive |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$174.6 M per month** across
402 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 8.1% | 42.3% | 5.22x |
| `deepseek` | 23.2% | 14.4% | 0.62x |
| `openai` | 10.7% | 12.4% | 1.17x |
| `moonshotai` | 2.8% | 11.5% | 4.10x |
| `google` | 8.9% | 5.8% | 0.65x |
| `xiaomi` | 11.3% | 2.9% | 0.26x |
| `x-ai` | 0.9% | 2.7% | 3.10x |
| `tencent` | 11.4% | 2.5% | 0.22x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,134**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **52.2%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.942** by value. Both are extreme; a
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
**9.71%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.78% |
| **extractive** | 4.95% |
| **output_heavy** | 2.32% |
| **conversational** | 1.87% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 745 endpoints serving multi-provider models,
**490 are dominated** (65.8%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.2-20260616` | Z.AI | $4.40 | 24 tok/s | StreamLake | 25 |
| `z-ai/glm-5.2-20260616` | Cloudflare | $4.40 | 35 tok/s | StreamLake | 21 |
| `z-ai/glm-5.2-20260616` | Ambient | $4.40 | 35 tok/s | StreamLake | 21 |
| `deepseek/deepseek-v4-flash-20260731` | Mancer 2 | $0.45 | 23 tok/s | StreamLake | 21 |
| `z-ai/glm-5.2-20260616` | Alibaba | $7.26 | 41 tok/s | StreamLake | 20 |
| `~deepseek/deepseek-v4-flash-latest` | Inceptron | $0.28 | 7 tok/s | StreamLake | 20 |
| `~deepseek/deepseek-v4-flash-latest` | Mancer 2 | $0.45 | 22 tok/s | StreamLake | 20 |
| `moonshotai/kimi-k2.6-20260420` | Phala | $4.60 | 17 tok/s | StreamLake | 19 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-08-17` and `2026-08-18`,
**2.46%** of 447 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.54 | -0.70 to -0.39 | 0.467 | 55 | yes |
| **all** | request weighted | -0.22 | -0.66 to +0.23 | 0.024 | 370 | no |
| **conversational** | request weighted | -0.26 | -0.91 to +0.39 | 0.031 | 251 | no |
| **extractive** | request weighted | +0.34 | -0.08 to +0.76 | 0.096 | 26 | no |
| **output_heavy** | request weighted | -0.02 | -0.32 to +0.28 | 0.001 | 38 | no |
| **agentic** | unweighted | -0.18 | -0.70 to +0.34 | 0.006 | 55 | no |
| **all** | unweighted | -0.53 | -0.76 to -0.30 | 0.051 | 370 | yes |
| **conversational** | unweighted | -0.78 | -1.01 to -0.55 | 0.132 | 251 | yes |
| **extractive** | unweighted | -0.10 | -0.55 to +0.35 | 0.004 | 26 | no |
| **output_heavy** | unweighted | -0.29 | -1.27 to +0.69 | 0.012 | 38 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.18, interval
-0.70 to +0.34, straddling zero). Weighting by requests, the
elasticity is **-0.54** (-0.70 to -0.39) and
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
| ≥2 days silent | 27 | 377 | 97.1% | 93.2% |
| ≥3 days silent | 21 | 383 | 97.1% | 93.2% |
| ≥7 days silent | 15 | 389 | 98.6% | 95.1% |
| ≥14 days silent | 12 | 392 | 99.2% | 96.4% |

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
