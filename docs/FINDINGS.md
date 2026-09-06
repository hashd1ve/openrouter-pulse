# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-09-06` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 617 model-variants, 411.02 T
tokens and 20.26 B requests over the trailing 30 days.


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
| **agentic** | 74 | 317.11 T | 77.2% | 57.6 | 50,919 | large contexts, terse output, very large interactions |
| **conversational** | 298 | 90.67 T | 22.1% | 10.1 | 3,969 | moderate context per output token, human-sized interactions |
| **unclassified** | 123 | 2.01 T | 0.5% | — | 32 | insufficient data to classify |
| **extractive** | 26 | 1.08 T | 0.3% | 36.4 | 8,849 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 96 | 155.51 B | 0.0% | 0.5 | 4,418 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **77.2% of all tokens**
while being 74 of 617 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
22.1%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 368.6 | 1,294 | 17.20 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 178.5 | 112,158 | 16.38 T | agentic |
| `xiaomi/mimo-v2.5-20260422` | 137.1 | 70,582 | 27.10 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 133.8 | 86,781 | 6.53 T | agentic |
| `thinkingmachines/inkling-20260715` | 130.2 | 69,836 | 401.79 B | agentic |
| `minimax/minimax-m3-20260531` | 117.6 | 76,696 | 7.38 T | agentic |
| `thinkingmachines/inkling-small-20260730` | 117.4 | 53,840 | 160.20 B | agentic |
| `poolside/laguna-xs-2.1-20260625` | 111.3 | 52,815 | 560.84 B | agentic |
| `tencent/hy4-preview-20260827` | 109.9 | 117,557 | 15.97 T | agentic |
| `anthropic/claude-opus-5-fast-20260723` | 98.4 | 87,287 | 90.34 B | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
368.6 tokens of context per token written, but its interactions
average only 1,294 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 178.5 tokens of context per token
written, in interactions averaging 112,158 tokens, which
is 87× larger.
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


Across 226 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.79** with a p25–p75 range of 0.53–1.01.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 20 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.28×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `tencent/hy-mt2-1.8b-20260521` | 5.80× | 177.26 M | 17 | conversational |
| `minimax/minimax-m2.7-20260318` | 4.77× | 731.81 B | 172 | agentic |
| `minimax/minimax-m3-20260531` | 3.21× | 7.38 T | 98 | agentic |
| `google/gemini-2.5-flash-lite` | 3.12× | 4.27 B | 411 | conversational |
| `z-ai/glm-5.2-20260616` | 3.02× | 54.43 B | 82 | conversational |
| `openai/gpt-5-nano-2025-08-07` | 2.93× | 277.36 B | 395 | conversational |
| `thinkingmachines/inkling-20260715` | 2.86× | 401.79 B | 51 | agentic |
| `ibm-granite/granite-4.0-h-micro` | 2.49× | 5.11 B | 321 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `google/gemma-4-26b-a4b-it-20260403` | 0.09× | 32.93 B | 156 | conversational |
| `anthropic/claude-4.7-opus-20260416` | 0.11× | 1.21 T | 143 | agentic |
| `google/gemini-3.6-flash-20260721` | 0.12× | 4.48 T | 47 | agentic |
| `meta-llama/llama-3.1-70b-instruct` | 0.14× | 32.35 B | 775 | conversational |
| `xiaomi/mimo-v2.5-20260422` | 0.14× | 27.10 T | 137 | agentic |
| `meta/muse-spark-1.1-20260709` | 0.20× | 98.07 B | 52 | agentic |
| `meta/muse-spark-1.2-20260805` | 0.20× | 349.12 B | 32 | agentic |
| `qwen/qwen3.5-397b-a17b-20260216` | 0.20× | 134.83 B | 202 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$201.5 M per month** across
449 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 5.6% | 37.2% | 6.64x |
| `openai` | 12.5% | 11.4% | 0.91x |
| `moonshotai` | 2.0% | 11.2% | 5.67x |
| `tencent` | 11.9% | 9.0% | 0.75x |
| `deepseek` | 21.4% | 7.9% | 0.37x |
| `google` | 7.5% | 7.1% | 0.95x |
| `z-ai` | 9.0% | 4.9% | 0.55x |
| `x-ai` | 0.7% | 2.8% | 4.04x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,840**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **59.9%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.945** by value. Both are extreme; a
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
**7.47%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.28% |
| **extractive** | 4.51% |
| **conversational** | 1.80% |
| **output_heavy** | 1.42% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 875 endpoints serving multi-provider models,
**597 are dominated** (68.2%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.2-20260616` | Alibaba | $7.26 | 34 tok/s | StreamLake | 23 |
| `z-ai/glm-5.2-20260616` | Z.AI | $4.40 | 46 tok/s | StreamLake | 22 |
| `z-ai/glm-5.3-20260816` | DigitalOcean | $4.40 | 20 tok/s | Decart | 21 |
| `~z-ai/glm-latest` | DigitalOcean | $4.40 | 21 tok/s | Decart | 21 |
| `z-ai/glm-5.3-flash-20260826` | NextBit | $0.50 | 6 tok/s | GMICloud | 21 |
| `~z-ai/glm-flash-latest` | NextBit | $0.50 | 6 tok/s | GMICloud | 21 |
| `z-ai/glm-5.3-20260816` | SiliconFlow | $4.40 | 26 tok/s | Decart | 20 |
| `~z-ai/glm-latest` | SiliconFlow | $4.40 | 25 tok/s | Decart | 20 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-09-05` and `2026-09-06`,
**1.42%** of 493 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.55 | -0.67 to -0.44 | 0.483 | 63 | yes |
| **all** | request weighted | -0.35 | -0.79 to +0.09 | 0.052 | 417 | no |
| **conversational** | request weighted | -0.30 | -0.89 to +0.29 | 0.037 | 280 | no |
| **extractive** | request weighted | +0.57 | +0.27 to +0.88 | 0.214 | 23 | yes |
| **output_heavy** | request weighted | -0.20 | -0.47 to +0.06 | 0.067 | 51 | no |
| **agentic** | unweighted | -0.35 | -0.68 to -0.02 | 0.060 | 63 | yes |
| **all** | unweighted | -0.71 | -0.97 to -0.45 | 0.084 | 417 | yes |
| **conversational** | unweighted | -1.01 | -1.30 to -0.72 | 0.179 | 280 | yes |
| **extractive** | unweighted | -0.19 | -0.54 to +0.16 | 0.029 | 23 | no |
| **output_heavy** | unweighted | -0.21 | -0.94 to +0.52 | 0.009 | 51 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.35, interval
-0.68 to -0.02, straddling zero). Weighting by requests, the
elasticity is **-0.55** (-0.67 to -0.44) and
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
| ≥2 days silent | 74 | 378 | 91.6% | 82.7% |
| ≥3 days silent | 69 | 383 | 92.4% | 83.9% |
| ≥7 days silent | 50 | 402 | 94.9% | 88.6% |
| ≥14 days silent | 9 | 443 | 98.9% | 98.4% |

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
