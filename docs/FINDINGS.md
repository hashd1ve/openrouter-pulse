# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-09-27` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 642 model-variants, 538.07 T
tokens and 24.97 B requests over the trailing 30 days.


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
| **agentic** | 99 | 419.37 T | 77.9% | 53.5 | 51,597 | large contexts, terse output, very large interactions |
| **conversational** | 306 | 115.25 T | 21.4% | 9.4 | 3,701 | moderate context per output token, human-sized interactions |
| **unclassified** | 124 | 2.49 T | 0.5% | — | 27 | insufficient data to classify |
| **extractive** | 16 | 836.81 B | 0.2% | 35.7 | 7,432 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 97 | 122.70 B | 0.0% | 0.5 | 4,421 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **77.9% of all tokens**
while being 99 of 642 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
21.4%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 239.8 | 812 | 9.24 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 206.3 | 130,260 | 18.42 T | agentic |
| `thinkingmachines/inkling-small-20260730` | 124.1 | 57,477 | 485.13 B | agentic |
| `xiaomi/mimo-v2.5-20260422` | 121.5 | 66,102 | 22.45 T | agentic |
| `minimax/minimax-m3-20260531` | 120.8 | 78,290 | 7.66 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 117.4 | 83,035 | 5.19 T | agentic |
| `tencent/hy4-preview-20260827` | 112.4 | 116,396 | 55.71 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 106.8 | 94,546 | 236.38 B | agentic |
| `deepseek/deepseek-v4-flash-20260731` | 105.4 | 98,351 | 1.09 T | agentic |
| `poolside/laguna-xs-2.1-20260625` | 98.9 | 46,737 | 387.66 B | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
239.8 tokens of context per token written, but its interactions
average only 812 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 206.3 tokens of context per token
written, in interactions averaging 130,260 tokens, which
is 160× larger.
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


Across 235 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.76** with a p25–p75 range of 0.53–1.01.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 14 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.28×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `google/gemini-2.5-flash-lite` | 5.12× | 10.85 B | 432 | conversational |
| `z-ai/glm-5.3-flash-20260826` | 5.11× | 8.21 B | 32 | conversational |
| `inclusionai/ling-3.0-flash-vl-20260910` | 4.32× | 15.28 B | 17 | conversational |
| `google/gemini-3.1-flash-lite-20260507` | 3.24× | 9.39 B | 143 | conversational |
| `qwen/qwen3-next-80b-a3b-instruct-2509` | 2.97× | 57.40 B | 381 | conversational |
| `bytedance-seed/seed-2.0-lite-20260309` | 2.83× | 6.70 B | 201 | conversational |
| `nvidia/nemotron-3.5-lightning-20260807` | 2.47× | 210.27 B | 47 | conversational |
| `openai/gpt-5.6-sol-20260709` | 2.36× | 5.51 B | 80 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `anthropic/claude-3-haiku` | 0.01× | 10.97 B | 928 | conversational |
| `tencent/hy-mt2-1.8b-20260521` | 0.05× | 3.02 B | 38 | conversational |
| `tencent/hy-mt2-7b-20260521` | 0.06× | 2.44 B | 39 | conversational |
| `stepfun/step-3.7-flash-20260528` | 0.11× | 778.08 B | 122 | agentic |
| `aion-labs/aion-3.0-20260707` | 0.12× | 37.07 B | 82 | conversational |
| `meta-llama/llama-3.2-1b-instruct` | 0.13× | 1.37 B | 732 | output_heavy |
| `google/gemini-3.7-flash-20260813` | 0.16× | 24.95 B | 45 | conversational |
| `meta/muse-spark-1.2-20260805` | 0.16× | 129.53 B | 53 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$271.7 M per month** across
459 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 4.0% | 31.5% | 7.80x |
| `tencent` | 13.7% | 18.3% | 1.33x |
| `openai` | 15.1% | 17.9% | 1.19x |
| `moonshotai` | 1.5% | 8.4% | 5.54x |
| `z-ai` | 14.8% | 5.7% | 0.39x |
| `google` | 5.7% | 5.3% | 0.94x |
| `deepseek` | 21.4% | 4.0% | 0.19x |
| `x-ai` | 0.5% | 1.8% | 3.82x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,471**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **56.2%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.944** by value. Both are extreme; a
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
**6.31%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.50% |
| **extractive** | 3.60% |
| **conversational** | 1.60% |
| **output_heavy** | 1.40% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,020 endpoints serving multi-provider models,
**702 are dominated** (68.8%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-20260816` | Mistral | $4.84 | 36 tok/s | Baidu | 29 |
| `~z-ai/glm-latest` | Mistral | $4.84 | 36 tok/s | Baidu | 29 |
| `z-ai/glm-5.3-flash-20260826` | Cloudflare | $1.00 | 8 tok/s | InferenceNet | 28 |
| `~z-ai/glm-flash-latest` | Cloudflare | $1.00 | 9 tok/s | InferenceNet | 28 |
| `z-ai/glm-5.3-20260816` | Fireworks | $4.40 | 44 tok/s | Baidu | 27 |
| `~z-ai/glm-latest` | Fireworks | $4.40 | 44 tok/s | Baidu | 27 |
| `z-ai/glm-5.3-flash-20260826` | Morph | $0.70 | 9 tok/s | InferenceNet | 27 |
| `~z-ai/glm-flash-latest` | NextBit | $0.55 | 6 tok/s | InferenceNet | 26 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-09-26` and `2026-09-27`,
**2.90%** of 518 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.52 | -0.74 to -0.29 | 0.264 | 85 | yes |
| **all** | request weighted | -0.23 | -0.59 to +0.13 | 0.017 | 423 | no |
| **conversational** | request weighted | -0.48 | -0.98 to +0.03 | 0.060 | 279 | no |
| **extractive** | request weighted | +0.66 | +0.51 to +0.81 | 0.684 | 14 | yes |
| **output_heavy** | request weighted | -0.14 | -0.47 to +0.20 | 0.027 | 45 | no |
| **agentic** | unweighted | -0.65 | -0.99 to -0.30 | 0.138 | 85 | yes |
| **all** | unweighted | -0.60 | -0.87 to -0.33 | 0.047 | 423 | yes |
| **conversational** | unweighted | -0.76 | -1.10 to -0.43 | 0.085 | 279 | yes |
| **extractive** | unweighted | +0.19 | -0.38 to +0.76 | 0.028 | 14 | no |
| **output_heavy** | unweighted | -0.25 | -1.02 to +0.51 | 0.006 | 45 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.65, interval
-0.99 to -0.30, straddling zero). Weighting by requests, the
elasticity is **-0.52** (-0.74 to -0.29) and
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
| ≥2 days silent | 59 | 401 | 89.1% | 84.2% |
| ≥3 days silent | 46 | 414 | 92.1% | 87.6% |
| ≥7 days silent | 37 | 423 | 93.6% | 89.4% |
| ≥14 days silent | 25 | 435 | 95.1% | 92.3% |

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
