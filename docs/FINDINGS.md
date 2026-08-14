# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-08-14` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 553 model-variants, 272.31 T
tokens and 17.05 B requests over the trailing 30 days.


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
| **agentic** | 65 | 201.17 T | 73.9% | 52.0 | 47,859 | large contexts, terse output, very large interactions |
| **conversational** | 268 | 67.30 T | 24.7% | 9.9 | 4,066 | moderate context per output token, human-sized interactions |
| **unclassified** | 111 | 2.30 T | 0.8% | — | 26 | insufficient data to classify |
| **extractive** | 30 | 1.39 T | 0.5% | 38.6 | 8,983 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 79 | 144.00 B | 0.1% | 0.6 | 4,487 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **73.9% of all tokens**
while being 65 of 553 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
24.7%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 302.8 | 1,118 | 21.60 B | extractive |
| `poolside/laguna-s-2.1-20260720` | 160.5 | 94,769 | 3.95 T | agentic |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 140.2 | 96,076 | 10.25 T | agentic |
| `poolside/laguna-m.1-20260312` | 139.9 | 69,024 | 687.23 B | agentic |
| `xiaomi/mimo-v2.5-20260422` | 118.5 | 68,491 | 31.09 T | agentic |
| `poolside/laguna-xs-2.1-20260625` | 115.1 | 57,168 | 647.14 B | agentic |
| `nvidia/nemotron-3.5-lightning-20260807` | 104.8 | 75,440 | 255.18 B | agentic |
| `anthropic/claude-opus-5-fast-20260723` | 98.8 | 86,437 | 109.95 B | agentic |
| `perceptron/perceptron-mk1-20260512` | 96.2 | 9,005 | 9.78 B | extractive |
| `stepfun/step-3.7-flash-20260528` | 87.9 | 69,193 | 5.99 T | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
302.8 tokens of context per token written, but its interactions
average only 1,118 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `poolside/laguna-s-2.1-20260720`: 160.5 tokens of context per token
written, in interactions averaging 94,769 tokens, which
is 85× larger.
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


Across 213 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.97** with a p25–p75 range of 0.76–1.18.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 16 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.40×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-4-scout-17b-16e-instruct` | 5.82× | 91.16 B | 496 | extractive |
| `inclusionai/ling-3.0-flash-20260723` | 4.76× | 79.80 B | 22 | conversational |
| `google/gemini-3.6-flash-20260721` | 3.04× | 4.14 T | 24 | agentic |
| `poolside/laguna-xs-2.1-20260625` | 2.84× | 37.90 B | 43 | conversational |
| `qwen/qwen3.6-35b-a3b-20260415` | 2.42× | 436.06 B | 109 | conversational |
| `openai/gpt-5.6-luna-20260709` | 2.33× | 10.18 T | 36 | agentic |
| `z-ai/glm-5v-turbo-20260401` | 2.24× | 53.89 B | 135 | agentic |
| `qwen/qwen3.5-plus-20260216` | 2.23× | 26.21 B | 179 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-5.2-chat-20251211` | 0.00× | 9.06 B | 247 | conversational |
| `openai/gpt-4o-2024-05-13` | 0.04× | 3.83 B | 823 | extractive |
| `perceptron/perceptron-mk1-20260512` | 0.19× | 9.78 B | 94 | extractive |
| `nvidia/nemotron-3-nano-30b-a3b` | 0.19× | 88.20 B | 243 | conversational |
| `meta/muse-spark-1.1-20260709` | 0.19× | 173.33 B | 29 | agentic |
| `ibm-granite/granite-4.0-h-micro` | 0.19× | 18.69 B | 298 | extractive |
| `amazon/nova-2-lite-v1` | 0.21× | 11.74 B | 255 | conversational |
| `deepseek/deepseek-v3.1-terminus` | 0.24× | 150.76 B | 326 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$196.0 M per month** across
395 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 8.5% | 36.3% | 4.24x |
| `openai` | 9.8% | 14.2% | 1.45x |
| `deepseek` | 21.7% | 11.5% | 0.53x |
| `moonshotai` | 2.8% | 9.5% | 3.42x |
| `google` | 8.5% | 7.2% | 0.86x |
| `z-ai` | 6.0% | 6.2% | 1.03x |
| `nvidia` | 4.7% | 3.3% | 0.70x |
| `xiaomi` | 12.4% | 2.8% | 0.22x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**2,221**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **42.1%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.929** by value. Both are extreme; a
national income distribution above 0.6 is considered severe.


### The sticker price is not the price

Traffic is overwhelmingly prompt-heavy, and prompt tokens cost less than
completions. Blended across each model's real token mix, the price actually paid
per token is a median **0.33x** the headline output price, so the
sticker overstates unit cost by about **3.0x**.

Anyone comparing models on `$/M output` is getting this wrong.


## 5. The context window arms race is mostly unused

Dividing mean tokens per request by the advertised context length asks how much
of the window the traffic actually touches. Token-weighted across the market:
**8.62%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 8.28% |
| **extractive** | 5.05% |
| **output_heavy** | 2.10% |
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

Of 750 endpoints serving multi-provider models,
**482 are dominated** (64.3%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.2-20260616` | Alibaba | $7.26 | 32 tok/s | GMICloud | 24 |
| `z-ai/glm-5.2-20260616` | Z.AI | $4.40 | 28 tok/s | GMICloud | 22 |
| `deepseek/deepseek-v4-flash-20260731` | AkashML | $0.28 | 25 tok/s | Decart | 19 |
| `~deepseek/deepseek-v4-flash-latest` | AkashML | $0.28 | 25 tok/s | Decart | 19 |
| `deepseek/deepseek-v4-flash-20260731` | Mancer 2 | $0.50 | 29 tok/s | Decart | 19 |
| `~deepseek/deepseek-v4-flash-latest` | Mancer 2 | $0.50 | 31 tok/s | Decart | 19 |
| `deepseek/deepseek-v4-flash-20260731` | Ambient | $0.28 | 27 tok/s | Decart | 18 |
| `~deepseek/deepseek-v4-flash-latest` | Ambient | $0.28 | 26 tok/s | Decart | 18 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-08-13` and `2026-08-14`,
**2.52%** of 436 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.43 | -0.59 to -0.28 | 0.364 | 58 | yes |
| **all** | request weighted | -0.11 | -0.48 to +0.26 | 0.006 | 367 | no |
| **conversational** | request weighted | -0.20 | -0.67 to +0.27 | 0.017 | 243 | no |
| **extractive** | request weighted | +0.33 | -0.03 to +0.69 | 0.101 | 27 | no |
| **output_heavy** | request weighted | +0.04 | -0.21 to +0.29 | 0.003 | 39 | no |
| **agentic** | unweighted | -0.14 | -0.63 to +0.35 | 0.004 | 58 | no |
| **all** | unweighted | -0.54 | -0.77 to -0.30 | 0.047 | 367 | yes |
| **conversational** | unweighted | -0.87 | -1.14 to -0.60 | 0.127 | 243 | yes |
| **extractive** | unweighted | +0.27 | -0.33 to +0.88 | 0.031 | 27 | no |
| **output_heavy** | unweighted | -0.45 | -0.99 to +0.08 | 0.054 | 39 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.14, interval
-0.63 to +0.35, straddling zero). Weighting by requests, the
elasticity is **-0.43** (-0.59 to -0.28) and
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
| ≥2 days silent | 25 | 372 | 96.7% | 92.7% |
| ≥3 days silent | 22 | 375 | 97.1% | 93.6% |
| ≥7 days silent | 16 | 381 | 98.3% | 95.5% |
| ≥14 days silent | 13 | 384 | 98.9% | 96.1% |

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
