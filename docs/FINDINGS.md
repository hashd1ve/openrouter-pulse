# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-09-21` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 635 model-variants, 513.34 T
tokens and 23.54 B requests over the trailing 30 days.


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
| **agentic** | 88 | 391.13 T | 76.2% | 54.2 | 50,531 | large contexts, terse output, very large interactions |
| **conversational** | 318 | 119.29 T | 23.2% | 9.9 | 3,874 | moderate context per output token, human-sized interactions |
| **unclassified** | 120 | 2.33 T | 0.5% | — | 31 | insufficient data to classify |
| **extractive** | 18 | 450.61 B | 0.1% | 38.4 | 8,186 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 91 | 144.69 B | 0.0% | 0.5 | 4,482 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **76.2% of all tokens**
while being 88 of 635 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
23.2%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 252.7 | 858 | 9.01 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 205.9 | 127,517 | 18.59 T | agentic |
| `xiaomi/mimo-v2.5-20260422` | 130.7 | 71,101 | 29.10 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 121.0 | 82,754 | 5.40 T | agentic |
| `minimax/minimax-m3-20260531` | 119.2 | 76,887 | 8.17 T | agentic |
| `thinkingmachines/inkling-small-20260730` | 117.8 | 56,060 | 430.86 B | agentic |
| `tencent/hy4-preview-20260827` | 112.0 | 116,692 | 47.07 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 107.9 | 94,429 | 247.08 B | agentic |
| `openai/gpt-6-astra-20260903` | 106.9 | 72,276 | 2.61 T | agentic |
| `deepseek/deepseek-v4-flash-20260731` | 105.4 | 98,351 | 1.09 T | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
252.7 tokens of context per token written, but its interactions
average only 858 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 205.9 tokens of context per token
written, in interactions averaging 127,517 tokens, which
is 149× larger.
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


Across 239 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.77** with a p25–p75 range of 0.56–0.96.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 20 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.62×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite-20260507` | 11.76× | 6.70 B | 137 | conversational |
| `tencent/hy-mt2-1.8b-20260521` | 3.67× | 2.84 B | 32 | conversational |
| `tencent/hy-mt2-7b-20260521` | 3.46× | 2.33 B | 33 | conversational |
| `mistralai/voxtral-small-24b-2507` | 3.15× | 2.17 B | 326 | conversational |
| `thinkingmachines/inkling-small-20260730` | 2.18× | 36.60 B | 53 | conversational |
| `meta-llama/llama-3.2-1b-instruct` | 1.91× | 1.82 B | 726 | output_heavy |
| `tencent/hy-mt2-30b-a3b-20260521` | 1.86× | 4.96 B | 32 | conversational |
| `mistralai/mistral-nemo` | 1.85× | 840.97 B | 794 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `google/gemini-3.7-flash-20260813` | 0.05× | 33.53 B | 39 | conversational |
| `meta/muse-spark-1.1-20260709` | 0.06× | 60.10 B | 67 | agentic |
| `stepfun/step-3.7-flash-20260528` | 0.08× | 1.12 T | 116 | agentic |
| `meta/muse-spark-1.2-20260805` | 0.12× | 204.75 B | 47 | conversational |
| `google/gemini-3.6-flash-20260721` | 0.13× | 10.81 B | 62 | conversational |
| `deepseek/deepseek-v4-flash-20260731` | 0.13× | 1.09 T | 52 | agentic |
| `qwen/qwen3-8b-04-28` | 0.14× | 31.87 B | 511 | conversational |
| `mistralai/mistral-small-2603` | 0.18× | 85.02 B | 189 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$240.9 M per month** across
463 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 4.1% | 26.8% | 6.53x |
| `tencent` | 13.3% | 17.8% | 1.34x |
| `openai` | 14.4% | 16.9% | 1.18x |
| `z-ai` | 12.7% | 8.6% | 0.68x |
| `deepseek` | 20.5% | 8.4% | 0.41x |
| `google` | 6.2% | 6.2% | 1.01x |
| `moonshotai` | 1.6% | 5.7% | 3.54x |
| `x-ai` | 0.5% | 2.1% | 4.24x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**2,848**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **49.7%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.939** by value. Both are extreme; a
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
**6.68%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.21% |
| **extractive** | 4.64% |
| **conversational** | 1.71% |
| **output_heavy** | 1.51% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,032 endpoints serving multi-provider models,
**698 are dominated** (67.6%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-flash-20260826` | OpenInference | $0.50 | 13 tok/s | GMICloud | 26 |
| `~z-ai/glm-flash-latest` | OpenInference | $0.50 | 13 tok/s | GMICloud | 26 |
| `z-ai/glm-5.3-flash-20260826` | AtlasCloud | $0.50 | 14 tok/s | GMICloud | 25 |
| `~z-ai/glm-flash-latest` | AtlasCloud | $0.50 | 14 tok/s | GMICloud | 25 |
| `z-ai/glm-5.3-flash-20260826` | Venice | $0.50 | 16 tok/s | GMICloud | 24 |
| `~z-ai/glm-flash-latest` | Venice | $0.50 | 16 tok/s | GMICloud | 24 |
| `z-ai/glm-5.3-20260816` | Cloudflare | $4.40 | 33 tok/s | Io Net | 23 |
| `~z-ai/glm-latest` | Cloudflare | $4.40 | 35 tok/s | Io Net | 23 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-09-20` and `2026-09-21`,
**1.17%** of 515 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.60 | -0.81 to -0.38 | 0.334 | 69 | yes |
| **all** | request weighted | -0.19 | -0.59 to +0.20 | 0.011 | 417 | no |
| **conversational** | request weighted | -0.38 | -0.95 to +0.19 | 0.037 | 287 | no |
| **extractive** | request weighted | +0.68 | +0.12 to +1.24 | 0.327 | 15 | yes |
| **output_heavy** | request weighted | -0.21 | -0.54 to +0.13 | 0.072 | 46 | no |
| **agentic** | unweighted | -0.76 | -1.11 to -0.42 | 0.164 | 69 | yes |
| **all** | unweighted | -0.72 | -0.98 to -0.45 | 0.079 | 417 | yes |
| **conversational** | unweighted | -0.96 | -1.25 to -0.67 | 0.157 | 287 | yes |
| **extractive** | unweighted | -0.16 | -0.56 to +0.23 | 0.018 | 15 | no |
| **output_heavy** | unweighted | -0.43 | -1.14 to +0.27 | 0.039 | 46 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.76, interval
-1.11 to -0.42, straddling zero). Weighting by requests, the
elasticity is **-0.60** (-0.81 to -0.38) and
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
| ≥2 days silent | 80 | 384 | 90.0% | 81.0% |
| ≥3 days silent | 77 | 387 | 90.3% | 82.0% |
| ≥7 days silent | 58 | 406 | 92.9% | 86.2% |
| ≥14 days silent | 50 | 414 | 94.1% | 87.4% |

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
