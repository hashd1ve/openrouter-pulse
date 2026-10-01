# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-10-01` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 652 model-variants, 575.90 T
tokens and 26.54 B requests over the trailing 30 days.


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
| **agentic** | 95 | 451.53 T | 78.4% | 55.4 | 54,371 | large contexts, terse output, very large interactions |
| **conversational** | 308 | 121.37 T | 21.1% | 10.0 | 3,802 | moderate context per output token, human-sized interactions |
| **unclassified** | 129 | 2.59 T | 0.5% | — | 27 | insufficient data to classify |
| **extractive** | 22 | 261.30 B | 0.0% | 45.5 | 5,287 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 98 | 141.81 B | 0.0% | 0.5 | 4,418 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **78.4% of all tokens**
while being 95 of 652 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
21.1%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 239.2 | 805 | 9.20 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 203.7 | 129,737 | 19.23 T | agentic |
| `thinkingmachines/inkling-small-20260730` | 125.7 | 57,162 | 497.09 B | agentic |
| `minimax/minimax-m3-20260531` | 124.0 | 76,104 | 5.15 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 113.4 | 83,154 | 5.00 T | agentic |
| `xiaomi/mimo-v2.5-20260422` | 112.9 | 62,143 | 19.91 T | agentic |
| `tencent/hy4-preview-20260827` | 110.9 | 114,708 | 56.15 T | agentic |
| `deepseek/deepseek-v4-flash-20260731` | 105.4 | 98,351 | 1.09 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 103.2 | 95,549 | 227.86 B | agentic |
| `upstage/solar-mini4-20260922` | 100.4 | 90,441 | 136.50 B | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
239.2 tokens of context per token written, but its interactions
average only 805 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 203.7 tokens of context per token
written, in interactions averaging 129,737 tokens, which
is 161× larger.
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
median of **0.93** with a p25–p75 range of 0.68–1.16.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 22 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.87×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `qwen/qwen3.8-27b-20260814` | 6.36× | 69.10 B | 48 | agentic |
| `ibm-granite/granite-4.2-8b-20260831` | 4.13× | 15.70 B | 31 | conversational |
| `inclusionai/ling-3.0-flash-vl-20260910` | 2.62× | 31.61 B | 21 | conversational |
| `inclusionai/ling-3.0-flash-fin-20260827` | 2.47× | 12.07 B | 35 | conversational |
| `qwen/qwen3-next-80b-a3b-instruct-2509` | 2.34× | 69.80 B | 385 | extractive |
| `qwen/qwen3.5-27b-20260224` | 2.12× | 64.22 B | 218 | conversational |
| `google/gemini-2.5-flash-lite` | 2.10× | 12.45 B | 436 | conversational |
| `openai/gpt-3.5-turbo` | 2.04× | 2.83 B | 1,222 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `google/gemini-3.6-flash-20260721` | 0.00× | 11.84 B | 72 | conversational |
| `google/gemini-3.1-flash-lite-20260507` | 0.00× | 12.51 B | 147 | conversational |
| `tencent/hy-mt2-1.8b-20260521` | 0.08× | 3.02 B | 42 | conversational |
| `stepfun/step-3.7-flash-20260528` | 0.11× | 547.14 B | 126 | agentic |
| `tencent/hy-mt2-7b-20260521` | 0.14× | 2.43 B | 43 | conversational |
| `google/gemini-3.8-flash-20260902` | 0.17× | 13.76 B | 29 | conversational |
| `mistralai/mistral-large-2512` | 0.18× | 22.38 B | 304 | conversational |
| `mistralai/voxtral-small-24b-2507` | 0.20× | 2.06 B | 336 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$269.6 M per month** across
456 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `openai` | 14.8% | 24.4% | 1.65x |
| `anthropic` | 4.0% | 24.2% | 6.08x |
| `tencent` | 12.6% | 18.5% | 1.47x |
| `google` | 5.4% | 6.9% | 1.28x |
| `moonshotai` | 1.4% | 6.4% | 4.49x |
| `z-ai` | 13.7% | 6.4% | 0.46x |
| `deepseek` | 22.0% | 3.9% | 0.18x |
| `xiaomi` | 5.7% | 2.1% | 0.38x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,476**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **56.2%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.940** by value. Both are extreme; a
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
**6.51%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.26% |
| **extractive** | 3.04% |
| **conversational** | 1.72% |
| **output_heavy** | 1.10% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,103 endpoints serving multi-provider models,
**745 are dominated** (67.5%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-20260816` | Venice | $4.40 | 36 tok/s | Baidu | 29 |
| `~z-ai/glm-latest` | Venice | $4.40 | 36 tok/s | Baidu | 29 |
| `z-ai/glm-5.3-flash-20260826` | Cloudflare | $1.00 | 21 tok/s | DeepInfra | 28 |
| `~z-ai/glm-flash-latest` | Cloudflare | $1.00 | 21 tok/s | DeepInfra | 28 |
| `z-ai/glm-5.3-20260816` | Fireworks | $4.40 | 48 tok/s | Baidu | 26 |
| `~z-ai/glm-latest` | Fireworks | $4.40 | 48 tok/s | Baidu | 26 |
| `z-ai/glm-5.3-flash-20260826` | Sail Research | $0.60 | 20 tok/s | DeepInfra | 26 |
| `~z-ai/glm-flash-latest` | Sail Research | $0.60 | 20 tok/s | DeepInfra | 26 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-09-30` and `2026-10-01`,
**1.93%** of 519 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.42 | -0.69 to -0.15 | 0.137 | 83 | yes |
| **all** | request weighted | +0.18 | -0.24 to +0.60 | 0.011 | 428 | no |
| **conversational** | request weighted | +0.03 | -0.75 to +0.81 | 0.000 | 281 | no |
| **extractive** | request weighted | +0.26 | -0.38 to +0.90 | 0.078 | 15 | no |
| **output_heavy** | request weighted | -0.06 | -0.39 to +0.28 | 0.004 | 49 | no |
| **agentic** | unweighted | -0.68 | -1.00 to -0.36 | 0.159 | 83 | yes |
| **all** | unweighted | -0.56 | -0.83 to -0.28 | 0.040 | 428 | yes |
| **conversational** | unweighted | -0.74 | -1.09 to -0.39 | 0.092 | 281 | yes |
| **extractive** | unweighted | -0.31 | -0.91 to +0.28 | 0.026 | 15 | no |
| **output_heavy** | unweighted | +0.11 | -0.77 to +0.98 | 0.001 | 49 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.68, interval
-1.00 to -0.36, straddling zero). Weighting by requests, the
elasticity is **-0.42** (-0.69 to -0.15) and
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
| ≥2 days silent | 56 | 401 | 91.1% | 86.4% |
| ≥3 days silent | 52 | 405 | 91.1% | 87.4% |
| ≥7 days silent | 36 | 421 | 93.9% | 90.7% |
| ≥14 days silent | 26 | 431 | 95.4% | 93.0% |

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
