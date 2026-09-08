# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-09-08` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 617 model-variants, 425.20 T
tokens and 20.74 B requests over the trailing 30 days.


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
| **agentic** | 77 | 328.44 T | 77.2% | 55.5 | 50,566 | large contexts, terse output, very large interactions |
| **conversational** | 298 | 93.56 T | 22.0% | 10.0 | 3,887 | moderate context per output token, human-sized interactions |
| **unclassified** | 123 | 2.03 T | 0.5% | — | 32 | insufficient data to classify |
| **extractive** | 25 | 1.05 T | 0.2% | 37.8 | 8,622 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 94 | 127.28 B | 0.0% | 0.4 | 4,447 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **77.2% of all tokens**
while being 77 of 617 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
22.0%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 362.3 | 1,258 | 15.77 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 182.3 | 114,263 | 16.77 T | agentic |
| `thinkingmachines/inkling-20260715` | 142.3 | 71,809 | 499.19 B | agentic |
| `xiaomi/mimo-v2.5-20260422` | 137.7 | 70,671 | 26.58 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 131.6 | 86,096 | 6.34 T | agentic |
| `openai/gpt-6-astra-20260903` | 119.2 | 73,030 | 225.17 B | agentic |
| `minimax/minimax-m3-20260531` | 119.2 | 76,887 | 8.17 T | agentic |
| `thinkingmachines/inkling-small-20260730` | 115.4 | 54,717 | 192.80 B | agentic |
| `tencent/hy4-preview-20260827` | 110.0 | 116,954 | 21.06 T | agentic |
| `poolside/laguna-xs-2.1-20260625` | 109.7 | 52,263 | 539.00 B | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
362.3 tokens of context per token written, but its interactions
average only 1,258 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 182.3 tokens of context per token
written, in interactions averaging 114,263 tokens, which
is 91× larger.
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


Across 231 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.95** with a p25–p75 range of 0.71–1.16.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 22 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.31×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `tencent/hy-mt2-30b-a3b-20260521` | 3.85× | 950.75 M | 19 | conversational |
| `minimax/minimax-m2.7-20260318` | 3.38× | 1.00 T | 174 | agentic |
| `thinkingmachines/inkling-20260715` | 3.02× | 499.19 B | 53 | agentic |
| `openai/gpt-5-nano-2025-08-07` | 2.94× | 325.68 B | 397 | conversational |
| `openai/gpt-5.2-20251211` | 2.91× | 117.45 B | 272 | conversational |
| `dots-studio/dots-3-note-preview-20260813` | 2.77× | 530.96 B | 25 | agentic |
| `nousresearch/hermes-3-llama-3.1-70b` | 2.67× | 2.24 B | 751 | conversational |
| `thinkingmachines/inkling-small-20260730` | 2.61× | 192.80 B | 40 | agentic |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-3.2-1b-instruct` | 0.06× | 2.70 B | 713 | output_heavy |
| `openai/gpt-4o-2024-05-13` | 0.09× | 889.07 M | 848 | extractive |
| `google/gemini-3.6-flash-20260721` | 0.16× | 4.01 T | 49 | agentic |
| `meta/muse-spark-1.2-20260805` | 0.17× | 330.58 B | 34 | agentic |
| `nvidia/nemotron-3.5-lightning-20260807` | 0.17× | 192.07 B | 28 | conversational |
| `google/gemma-4-26b-a4b-it-20260403` | 0.19× | 28.74 B | 158 | conversational |
| `google/gemini-3.6-flash-20260721` | 0.20× | 6.05 B | 49 | conversational |
| `z-ai/glm-5v-turbo-20260401` | 0.22× | 83.00 B | 160 | agentic |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$235.7 M per month** across
449 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 5.5% | 27.9% | 5.08x |
| `openai` | 13.0% | 15.1% | 1.17x |
| `z-ai` | 9.6% | 11.0% | 1.14x |
| `moonshotai` | 1.9% | 9.6% | 5.03x |
| `deepseek` | 20.7% | 9.6% | 0.46x |
| `tencent` | 12.3% | 9.4% | 0.77x |
| `google` | 7.3% | 7.3% | 1.00x |
| `x-ai` | 0.7% | 2.4% | 3.64x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**2,387**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **43.8%** of
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
**7.47%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.48% |
| **extractive** | 4.34% |
| **conversational** | 1.74% |
| **output_heavy** | 1.63% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 925 endpoints serving multi-provider models,
**607 are dominated** (65.6%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-flash-20260826` | Sail Research | $0.50 | 14 tok/s | Relace | 23 |
| `~z-ai/glm-flash-latest` | Sail Research | $0.50 | 14 tok/s | Relace | 23 |
| `z-ai/glm-5.3-20260816` | Inceptron | $4.40 | 15 tok/s | GMICloud | 23 |
| `~z-ai/glm-latest` | Inceptron | $4.40 | 15 tok/s | GMICloud | 23 |
| `z-ai/glm-5.2-20260616` | Alibaba | $7.26 | 55 tok/s | Novita | 22 |
| `z-ai/glm-5.3-flash-20260826` | Io Net | $0.50 | 17 tok/s | Relace | 22 |
| `~z-ai/glm-flash-latest` | Io Net | $0.50 | 17 tok/s | Relace | 22 |
| `z-ai/glm-5.2-20260616` | Z.AI | $4.40 | 35 tok/s | DeepInfra | 21 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-09-07` and `2026-09-08`,
**1.42%** of 494 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.59 | -0.81 to -0.38 | 0.419 | 64 | yes |
| **all** | request weighted | -0.19 | -0.56 to +0.18 | 0.014 | 419 | no |
| **conversational** | request weighted | -0.29 | -0.85 to +0.26 | 0.035 | 283 | no |
| **extractive** | request weighted | +0.56 | +0.09 to +1.03 | 0.179 | 22 | yes |
| **output_heavy** | request weighted | -0.03 | -0.28 to +0.21 | 0.001 | 50 | no |
| **agentic** | unweighted | -0.48 | -0.82 to -0.15 | 0.089 | 64 | yes |
| **all** | unweighted | -0.68 | -0.94 to -0.41 | 0.073 | 419 | yes |
| **conversational** | unweighted | -0.98 | -1.27 to -0.69 | 0.173 | 283 | yes |
| **extractive** | unweighted | -0.13 | -0.48 to +0.23 | 0.011 | 22 | no |
| **output_heavy** | unweighted | -0.13 | -0.88 to +0.62 | 0.003 | 50 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.48, interval
-0.82 to -0.15, straddling zero). Weighting by requests, the
elasticity is **-0.59** (-0.81 to -0.38) and
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
| ≥2 days silent | 72 | 380 | 91.3% | 83.0% |
| ≥3 days silent | 69 | 383 | 92.1% | 83.7% |
| ≥7 days silent | 59 | 393 | 93.2% | 86.3% |
| ≥14 days silent | 19 | 433 | 98.0% | 94.2% |

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
