# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-08-07` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 524 model-variants, 256.20 T
tokens and 16.38 B requests over the trailing 30 days.


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
| **agentic** | 61 | 179.18 T | 69.9% | 52.1 | 46,057 | large contexts, terse output, very large interactions |
| **conversational** | 261 | 68.66 T | 26.8% | 11.0 | 3,848 | moderate context per output token, human-sized interactions |
| **extractive** | 25 | 5.92 T | 2.3% | 42.5 | 8,563 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 103 | 2.30 T | 0.9% | — | 29 | insufficient data to classify |
| **output_heavy** | 74 | 133.11 B | 0.1% | 0.6 | 4,393 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **69.9% of all tokens**
while being 61 of 524 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
26.8%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 235.8 | 873 | 17.04 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 161.3 | 104,634 | 11.04 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 159.9 | 94,941 | 2.27 T | agentic |
| `poolside/laguna-m.1-20260312` | 137.2 | 69,192 | 1.24 T | agentic |
| `xiaomi/mimo-v2.5-20260422` | 116.2 | 67,692 | 34.10 T | agentic |
| `poolside/laguna-xs-2.1-20260625` | 94.8 | 55,506 | 586.44 B | agentic |
| `anthropic/claude-4.8-opus-fast-20260528` | 88.6 | 61,470 | 84.26 B | agentic |
| `stepfun/step-3.7-flash-20260528` | 84.5 | 67,440 | 5.88 T | agentic |
| `anthropic/claude-4.8-opus-20260528` | 81.4 | 76,819 | 5.84 T | agentic |
| `xiaomi/mimo-v2.5-pro-20260422` | 81.2 | 56,778 | 2.55 T | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
235.8 tokens of context per token written, but its interactions
average only 873 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 161.3 tokens of context per token
written, in interactions averaging 104,634 tokens, which
is 120× larger.
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


Across 207 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.93** with a p25–p75 range of 0.73–1.15.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 17 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.43×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `google/gemini-3.6-flash-20260721` | 6.35× | 2.44 T | 17 | agentic |
| `openai/gpt-5.6-luna-pro-20260709` | 4.10× | 703.95 B | 29 | agentic |
| `openai/gpt-5.6-luna-20260709` | 4.05× | 5.14 T | 29 | extractive |
| `z-ai/glm-5v-turbo-20260401` | 3.63× | 34.09 B | 128 | agentic |
| `mistralai/mistral-medium-3.5-20260430` | 3.19× | 36.37 B | 99 | conversational |
| `meta/muse-spark-1.1-20260709` | 3.19× | 155.78 B | 22 | agentic |
| `nousresearch/hermes-4-70b` | 3.06× | 11.63 B | 346 | conversational |
| `openai/gpt-5.6-terra-20260709` | 2.87× | 1.36 T | 29 | agentic |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `ibm-granite/granite-4.0-h-micro` | 0.02× | 50.89 B | 291 | agentic |
| `amazon/nova-2-lite-v1` | 0.09× | 16.94 B | 248 | conversational |
| `openai/o4-mini-2025-04-16` | 0.13× | 53.34 B | 478 | conversational |
| `mistralai/mistral-medium-3` | 0.18× | 4.46 B | 457 | conversational |
| `google/gemma-4-31b-it-20260402` | 0.25× | 23.33 B | 127 | conversational |
| `openai/gpt-4o-2024-05-13` | 0.26× | 3.74 B | 816 | extractive |
| `google/gemma-2-27b-it` | 0.28× | 665.08 M | 755 | conversational |
| `nvidia/nemotron-3-nano-30b-a3b` | 0.29× | 72.67 B | 236 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$150.4 M per month** across
369 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 9.9% | 38.4% | 3.88x |
| `openai` | 8.2% | 17.1% | 2.08x |
| `moonshotai` | 2.5% | 9.2% | 3.69x |
| `z-ai` | 6.4% | 8.0% | 1.25x |
| `google` | 8.3% | 7.1% | 0.86x |
| `deepseek` | 18.8% | 6.2% | 0.33x |
| `xiaomi` | 14.5% | 3.9% | 0.27x |
| `tencent` | 12.4% | 2.9% | 0.23x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**2,361**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **42.5%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.932** by value. Both are extreme; a
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
**8.66%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 8.41% |
| **extractive** | 3.91% |
| **conversational** | 1.92% |
| **output_heavy** | 1.75% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 708 endpoints serving multi-provider models,
**460 are dominated** (65.0%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.2-20260616` | Z.AI | $4.40 | 31 tok/s | Decart | 20 |
| `deepseek/deepseek-v4-flash-20260731` | Phala | $0.40 | 24 tok/s | DeepInfra | 19 |
| `~deepseek/deepseek-v4-flash-latest` | Phala | $0.40 | 24 tok/s | DeepInfra | 19 |
| `deepseek/deepseek-v4-flash-20260731` | Io Net | $0.32 | 24 tok/s | DeepInfra | 17 |
| `~deepseek/deepseek-v4-flash-latest` | Io Net | $0.32 | 24 tok/s | DeepInfra | 17 |
| `deepseek/deepseek-v4-flash-20260731` | AkashML | $0.28 | 26 tok/s | DeepInfra | 16 |
| `~deepseek/deepseek-v4-flash-latest` | AkashML | $0.28 | 26 tok/s | DeepInfra | 16 |
| `z-ai/glm-5.2-20260616` | Fireworks | $4.40 | 36 tok/s | Decart | 16 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-08-06` and `2026-08-07`,
**1.72%** of 408 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.49 | -0.72 to -0.27 | 0.402 | 51 | yes |
| **all** | request weighted | -0.24 | -0.75 to +0.27 | 0.026 | 342 | no |
| **conversational** | request weighted | -0.41 | -1.12 to +0.29 | 0.066 | 233 | no |
| **extractive** | request weighted | -1.25 | -3.07 to +0.57 | 0.206 | 21 | no |
| **output_heavy** | request weighted | +0.06 | -0.19 to +0.31 | 0.007 | 37 | no |
| **agentic** | unweighted | -0.26 | -0.78 to +0.26 | 0.014 | 51 | no |
| **all** | unweighted | -0.58 | -0.85 to -0.31 | 0.044 | 342 | yes |
| **conversational** | unweighted | -0.74 | -1.05 to -0.42 | 0.084 | 233 | yes |
| **extractive** | unweighted | -0.19 | -0.66 to +0.28 | 0.021 | 21 | no |
| **output_heavy** | unweighted | -0.60 | -1.63 to +0.43 | 0.025 | 37 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.26, interval
-0.78 to +0.26, straddling zero). Weighting by requests, the
elasticity is **-0.49** (-0.72 to -0.27) and
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
| ≥2 days silent | 26 | 345 | 96.7% | 90.6% |
| ≥3 days silent | 26 | 345 | 96.7% | 90.6% |
| ≥7 days silent | 26 | 345 | 96.7% | 90.6% |
| ≥14 days silent | 12 | 359 | 98.8% | 96.2% |

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
