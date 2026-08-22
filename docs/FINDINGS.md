# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-08-22` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 563 model-variants, 297.54 T
tokens and 17.76 B requests over the trailing 30 days.


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
| **agentic** | 66 | 216.24 T | 72.7% | 50.3 | 47,899 | large contexts, terse output, very large interactions |
| **conversational** | 272 | 77.18 T | 25.9% | 9.9 | 3,821 | moderate context per output token, human-sized interactions |
| **unclassified** | 114 | 2.31 T | 0.8% | — | 29 | insufficient data to classify |
| **extractive** | 32 | 1.69 T | 0.6% | 38.7 | 8,422 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 79 | 132.62 B | 0.0% | 0.5 | 4,564 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **72.7% of all tokens**
while being 66 of 563 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
25.9%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 359.1 | 1,297 | 23.18 B | extractive |
| `poolside/laguna-s-2.1-20260720` | 152.7 | 94,075 | 5.81 T | agentic |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 145.7 | 96,456 | 11.76 T | agentic |
| `poolside/laguna-xs-2.1-20260625` | 128.0 | 57,280 | 695.87 B | agentic |
| `xiaomi/mimo-v2.5-20260422` | 122.6 | 71,318 | 28.76 T | agentic |
| `poolside/laguna-m.1-20260312` | 121.2 | 55,373 | 90.98 B | agentic |
| `anthropic/claude-opus-5-fast-20260723` | 101.9 | 89,968 | 141.52 B | agentic |
| `nvidia/nemotron-3.5-lightning-20260807` | 97.9 | 75,417 | 1.27 T | agentic |
| `openai/gpt-5.6-terra-20260709` | 90.9 | 39,769 | 2.92 T | agentic |
| `qwen/qwen3-coder-next-2025-02-03` | 82.0 | 26,279 | 95.92 B | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
359.1 tokens of context per token written, but its interactions
average only 1,297 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `poolside/laguna-s-2.1-20260720`: 152.7 tokens of context per token
written, in interactions averaging 94,075 tokens, which
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


Across 224 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.93** with a p25–p75 range of 0.69–1.12.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 18 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **2.61×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `anthropic/claude-4.5-opus-20251124` | 3.05× | 75.03 B | 271 | conversational |
| `mistralai/mistral-large-2512` | 2.72× | 36.49 B | 264 | conversational |
| `bytedance-seed/seed-2.0-mini-20260224` | 2.61× | 17.41 B | 177 | conversational |
| `meta-llama/llama-3.2-1b-instruct` | 2.24× | 2.45 B | 696 | output_heavy |
| `inclusionai/ling-3.0-flash-20260723` | 2.02× | 173.08 B | 30 | conversational |
| `openai/gpt-5.6-sol-20260709` | 1.99× | 3.07 T | 44 | agentic |
| `qwen/qwen3.8-27b-20260814` | 1.91× | 119.21 B | 8 | conversational |
| `mistralai/voxtral-small-24b-2507` | 1.84× | 542.87 M | 296 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-5.2-chat-20251211` | 0.00× | 6.45 B | 255 | conversational |
| `google/gemma-4-26b-a4b-it-20260403` | 0.08× | 61.58 B | 141 | conversational |
| `google/gemma-2-27b-it` | 0.10× | 573.81 M | 770 | conversational |
| `mistralai/mistral-large` | 0.11× | 4.50 B | 908 | conversational |
| `google/gemma-3-4b-it` | 0.20× | 21.08 B | 527 | conversational |
| `perceptron/perceptron-mk1-20260512` | 0.24× | 6.83 B | 102 | extractive |
| `qwen/qwen3.7-max-20260520` | 0.25× | 402.39 B | 93 | agentic |
| `deepseek/deepseek-v3.1-terminus` | 0.30× | 113.91 B | 334 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$187.8 M per month** across
404 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 7.5% | 40.3% | 5.38x |
| `openai` | 11.3% | 13.5% | 1.19x |
| `moonshotai` | 2.6% | 10.6% | 4.09x |
| `z-ai` | 5.7% | 8.8% | 1.55x |
| `google` | 8.8% | 7.5% | 0.85x |
| `deepseek` | 24.2% | 6.7% | 0.28x |
| `xiaomi` | 10.5% | 2.7% | 0.26x |
| `x-ai` | 0.9% | 2.7% | 3.08x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**2,487**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **44.9%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.933** by value. Both are extreme; a
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
**8.02%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 6.96% |
| **extractive** | 4.37% |
| **output_heavy** | 2.25% |
| **conversational** | 1.83% |

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
**496 are dominated** (67.9%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.2-20260616` | Crusoe | $4.40 | 42 tok/s | StreamLake | 22 |
| `deepseek/deepseek-v4-flash-20260731` | AtlasCloud | $1.32 | 52 tok/s | Baidu | 19 |
| `z-ai/glm-5.2-20260616` | Venice | $4.40 | 47 tok/s | Baidu | 18 |
| `z-ai/glm-5.2-20260616` | Fireworks | $4.40 | 48 tok/s | Baidu | 17 |
| `~deepseek/deepseek-v4-flash-latest` | AtlasCloud | $1.32 | 58 tok/s | Baidu | 17 |
| `z-ai/glm-5.2-20260616` | Cloudflare | $4.40 | 52 tok/s | Baidu | 16 |
| `z-ai/glm-5.2-20260616` | Fireworks | $6.60 | 54 tok/s | Baidu | 16 |
| `deepseek/deepseek-v4-flash-20260731` | Nebius | $0.28 | 21 tok/s | Decart | 15 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-08-21` and `2026-08-22`,
**2.02%** of 445 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.52 | -0.66 to -0.38 | 0.432 | 57 | yes |
| **all** | request weighted | -0.24 | -0.71 to +0.22 | 0.030 | 372 | no |
| **conversational** | request weighted | -0.34 | -1.04 to +0.35 | 0.053 | 248 | no |
| **extractive** | request weighted | +0.11 | -0.48 to +0.70 | 0.007 | 28 | no |
| **output_heavy** | request weighted | -0.05 | -0.46 to +0.36 | 0.003 | 39 | no |
| **agentic** | unweighted | -0.10 | -0.54 to +0.34 | 0.004 | 57 | no |
| **all** | unweighted | -0.51 | -0.76 to -0.27 | 0.051 | 372 | yes |
| **conversational** | unweighted | -0.66 | -0.93 to -0.38 | 0.092 | 248 | yes |
| **extractive** | unweighted | -0.36 | -0.66 to -0.05 | 0.085 | 28 | yes |
| **output_heavy** | unweighted | -0.66 | -1.25 to -0.07 | 0.094 | 39 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.10, interval
-0.54 to +0.34, straddling zero). Weighting by requests, the
elasticity is **-0.52** (-0.66 to -0.38) and
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
| ≥2 days silent | 20 | 386 | 97.4% | 95.4% |
| ≥3 days silent | 12 | 394 | 98.3% | 96.8% |
| ≥7 days silent | 7 | 399 | 98.8% | 97.3% |
| ≥14 days silent | 4 | 402 | 99.7% | 98.2% |

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
