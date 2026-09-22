# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-09-22` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 638 model-variants, 520.10 T
tokens and 23.81 B requests over the trailing 30 days.


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
| **agentic** | 89 | 397.75 T | 76.5% | 53.0 | 50,267 | large contexts, terse output, very large interactions |
| **conversational** | 322 | 119.42 T | 23.0% | 10.0 | 3,938 | moderate context per output token, human-sized interactions |
| **unclassified** | 120 | 2.36 T | 0.5% | — | 31 | insufficient data to classify |
| **extractive** | 19 | 445.32 B | 0.1% | 38.3 | 8,912 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 88 | 121.46 B | 0.0% | 0.5 | 4,480 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **76.5% of all tokens**
while being 89 of 638 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
23.0%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 247.2 | 843 | 9.05 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 207.6 | 128,555 | 18.60 T | agentic |
| `xiaomi/mimo-v2.5-20260422` | 129.6 | 70,716 | 28.69 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 120.3 | 82,837 | 5.37 T | agentic |
| `minimax/minimax-m3-20260531` | 119.2 | 76,887 | 8.17 T | agentic |
| `thinkingmachines/inkling-small-20260730` | 117.8 | 56,230 | 446.33 B | agentic |
| `tencent/hy4-preview-20260827` | 112.1 | 116,559 | 48.96 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 107.9 | 94,727 | 249.20 B | agentic |
| `deepseek/deepseek-v4-flash-20260731` | 105.4 | 98,351 | 1.09 T | agentic |
| `poolside/laguna-xs-2.1-20260625` | 102.6 | 48,782 | 411.21 B | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
247.2 tokens of context per token written, but its interactions
average only 843 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 207.6 tokens of context per token
written, in interactions averaging 128,555 tokens, which
is 152× larger.
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


Across 238 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.96** with a p25–p75 range of 0.74–1.17.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 20 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.54×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite-20260507` | 5.56× | 8.22 B | 138 | conversational |
| `qwen/qwen3.5-35b-a3b-20260224` | 4.27× | 131.15 B | 209 | conversational |
| `arcee-ai/trinity-large-thinking` | 2.61× | 4.92 B | 174 | conversational |
| `z-ai/glm-5.3-flash-20260826` | 2.41× | 48.88 T | 27 | agentic |
| `z-ai/glm-4.5-air` | 2.18× | 23.84 B | 424 | conversational |
| `deepseek/deepseek-chat-v3-0324` | 1.98× | 140.48 B | 547 | conversational |
| `openai/gpt-5-nano-2025-08-07` | 1.91× | 466.33 B | 411 | conversational |
| `google/gemini-2.5-flash-lite` | 1.89× | 8.93 B | 427 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `google/gemini-3.7-flash-20260813` | 0.04× | 32.77 B | 40 | conversational |
| `meta/muse-spark-1.1-20260709` | 0.06× | 57.32 B | 68 | agentic |
| `stepfun/step-3.7-flash-20260528` | 0.08× | 1.07 T | 117 | agentic |
| `google/gemini-3.6-flash-20260721` | 0.14× | 10.86 B | 63 | conversational |
| `meta/muse-spark-1.2-contributor-20260805` | 0.17× | 575.43 B | 32 | conversational |
| `z-ai/glm-5v-turbo-20260401` | 0.20× | 33.57 B | 174 | agentic |
| `meta/muse-spark-1.2-20260805` | 0.20× | 195.87 B | 48 | conversational |
| `mistralai/mistral-small-2603` | 0.20× | 83.46 B | 190 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$262.2 M per month** across
466 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `openai` | 14.4% | 25.0% | 1.73x |
| `anthropic` | 4.1% | 21.4% | 5.24x |
| `tencent` | 13.4% | 16.9% | 1.26x |
| `moonshotai` | 1.6% | 8.8% | 5.58x |
| `z-ai` | 13.5% | 7.3% | 0.54x |
| `deepseek` | 20.6% | 7.0% | 0.34x |
| `google` | 6.2% | 4.4% | 0.71x |
| `qwen` | 1.5% | 2.0% | 1.31x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**2,895**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **50.1%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.941** by value. Both are extreme; a
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
**6.81%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.34% |
| **extractive** | 5.44% |
| **conversational** | 1.77% |
| **output_heavy** | 1.58% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,037 endpoints serving multi-provider models,
**713 are dominated** (68.8%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-20260816` | Cloudflare | $4.40 | 0 tok/s | Morph | 29 |
| `~z-ai/glm-latest` | Cloudflare | $4.40 | 0 tok/s | Morph | 29 |
| `z-ai/glm-5.3-flash-20260826` | OpenInference | $0.50 | 3 tok/s | GMICloud | 29 |
| `~z-ai/glm-flash-latest` | OpenInference | $0.50 | 3 tok/s | GMICloud | 29 |
| `z-ai/glm-5.3-20260816` | Z.AI | $4.40 | 27 tok/s | Morph | 27 |
| `~z-ai/glm-latest` | Z.AI | $4.40 | 27 tok/s | Morph | 27 |
| `z-ai/glm-5.3-flash-20260826` | DigitalOcean | $0.50 | 11 tok/s | GMICloud | 25 |
| `~z-ai/glm-flash-latest` | DigitalOcean | $0.50 | 11 tok/s | GMICloud | 25 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-09-21` and `2026-09-22`,
**0.78%** of 514 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.57 | -0.79 to -0.35 | 0.308 | 74 | yes |
| **all** | request weighted | -0.02 | -0.39 to +0.35 | 0.000 | 431 | no |
| **conversational** | request weighted | -0.08 | -0.68 to +0.52 | 0.001 | 297 | no |
| **extractive** | request weighted | +0.67 | +0.12 to +1.23 | 0.327 | 16 | yes |
| **output_heavy** | request weighted | -0.01 | -0.27 to +0.25 | 0.000 | 44 | no |
| **agentic** | unweighted | -0.54 | -0.95 to -0.13 | 0.086 | 74 | yes |
| **all** | unweighted | -0.73 | -0.98 to -0.47 | 0.083 | 431 | yes |
| **conversational** | unweighted | -0.97 | -1.26 to -0.69 | 0.164 | 297 | yes |
| **extractive** | unweighted | -0.11 | -0.58 to +0.37 | 0.007 | 16 | no |
| **output_heavy** | unweighted | -0.35 | -1.01 to +0.30 | 0.024 | 44 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.54, interval
-0.95 to -0.13, straddling zero). Weighting by requests, the
elasticity is **-0.57** (-0.79 to -0.35) and
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
| ≥2 days silent | 71 | 396 | 91.5% | 83.2% |
| ≥3 days silent | 69 | 398 | 91.8% | 83.4% |
| ≥7 days silent | 65 | 402 | 91.9% | 84.9% |
| ≥14 days silent | 54 | 413 | 93.1% | 86.4% |

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
