# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-09-24` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 656 model-variants, 526.90 T
tokens and 24.34 B requests over the trailing 30 days.


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
| **agentic** | 97 | 404.19 T | 76.7% | 52.6 | 51,395 | large contexts, terse output, very large interactions |
| **conversational** | 327 | 118.79 T | 22.5% | 9.3 | 4,013 | moderate context per output token, human-sized interactions |
| **unclassified** | 121 | 2.41 T | 0.5% | — | 28 | insufficient data to classify |
| **extractive** | 20 | 1.40 T | 0.3% | 39.8 | 8,310 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 91 | 120.89 B | 0.0% | 0.4 | 4,498 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **76.7% of all tokens**
while being 97 of 656 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
22.5%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 239.2 | 818 | 9.11 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 207.1 | 128,814 | 18.10 T | agentic |
| `z-ai/glm-5.3-flashx-20260918` | 128.6 | 83,720 | 177.72 B | agentic |
| `xiaomi/mimo-v2.5-20260422` | 127.4 | 69,313 | 26.74 T | agentic |
| `thinkingmachines/inkling-small-20260730` | 120.9 | 57,004 | 472.27 B | agentic |
| `minimax/minimax-m3-20260531` | 119.2 | 76,887 | 8.17 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 119.2 | 83,026 | 5.31 T | agentic |
| `tencent/hy4-preview-20260827` | 112.4 | 116,437 | 52.67 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 106.4 | 94,985 | 247.28 B | agentic |
| `deepseek/deepseek-v4-flash-20260731` | 105.4 | 98,351 | 1.09 T | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
239.2 tokens of context per token written, but its interactions
average only 818 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 207.1 tokens of context per token
written, in interactions averaging 128,814 tokens, which
is 157× larger.
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


Across 237 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.96** with a p25–p75 range of 0.76–1.19.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 21 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.36×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `nvidia/nemotron-3.5-lightning-20260807` | 3.50× | 178.59 B | 44 | conversational |
| `qwen/qwen3.7-max-20260520` | 2.93× | 84.32 B | 126 | conversational |
| `moonshotai/kimi-k2-thinking-20251106` | 2.79× | 16.47 B | 322 | conversational |
| `inclusionai/ling-3.0-flash-vl-20260910` | 2.65× | 5.46 B | 14 | conversational |
| `meta/muse-spark-1.3-20260902` | 2.44× | 923.00 B | 22 | agentic |
| `google/gemini-3.1-flash-lite-20260507` | 2.35× | 8.54 B | 140 | conversational |
| `nvidia/nemotron-3-super-120b-a12b-20230311` | 2.12× | 40.66 B | 197 | conversational |
| `openai/gpt-5-nano-2025-08-07` | 2.05× | 529.63 B | 413 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `google/gemini-3.7-flash-20260813` | 0.03× | 31.71 B | 42 | conversational |
| `tencent/hy-mt2-1.8b-20260521` | 0.07× | 3.00 B | 35 | conversational |
| `stepfun/step-3.7-flash-20260528` | 0.09× | 954.49 B | 119 | agentic |
| `meta/muse-spark-1.2-contributor-20260805` | 0.16× | 504.14 B | 34 | conversational |
| `mistralai/voxtral-small-24b-2507` | 0.19× | 2.16 B | 329 | conversational |
| `tencent/hy-mt2-7b-20260521` | 0.21× | 2.41 B | 36 | conversational |
| `mistralai/mistral-small-2603` | 0.23× | 79.46 B | 192 | conversational |
| `meta/muse-spark-1.2-20260805` | 0.29× | 146.07 B | 50 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$267.8 M per month** across
477 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 4.1% | 26.4% | 6.44x |
| `openai` | 14.8% | 21.4% | 1.44x |
| `tencent` | 13.8% | 17.7% | 1.28x |
| `moonshotai` | 1.6% | 8.7% | 5.53x |
| `deepseek` | 21.1% | 5.9% | 0.28x |
| `z-ai` | 14.5% | 5.8% | 0.40x |
| `google` | 6.1% | 4.4% | 0.71x |
| `qwen` | 1.6% | 2.0% | 1.27x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,432**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **56.4%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.943** by value. Both are extreme; a
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
**6.44%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.57% |
| **extractive** | 3.80% |
| **output_heavy** | 1.96% |
| **conversational** | 1.68% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,076 endpoints serving multi-provider models,
**736 are dominated** (68.4%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-20260816` | AtlasCloud | $4.40 | 10 tok/s | Morph | 31 |
| `~z-ai/glm-latest` | AtlasCloud | $4.40 | 10 tok/s | Morph | 31 |
| `z-ai/glm-5.3-20260816` | Cloudflare | $4.40 | 11 tok/s | Morph | 30 |
| `~z-ai/glm-latest` | Cloudflare | $4.40 | 11 tok/s | Morph | 30 |
| `z-ai/glm-5.3-flash-20260826` | SiliconFlow | $0.50 | 13 tok/s | InferenceNet | 26 |
| `~z-ai/glm-flash-latest` | SiliconFlow | $0.50 | 14 tok/s | InferenceNet | 26 |
| `z-ai/glm-5.3-flash-20260826` | OpenInference | $0.50 | 18 tok/s | InferenceNet | 25 |
| `z-ai/glm-5.3-20260816` | Fireworks | $4.40 | 20 tok/s | Morph | 24 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-09-22` and `2026-09-24`,
**3.33%** of 510 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.53 | -0.75 to -0.31 | 0.272 | 85 | yes |
| **all** | request weighted | -0.20 | -0.60 to +0.21 | 0.010 | 445 | no |
| **conversational** | request weighted | -0.34 | -0.87 to +0.19 | 0.026 | 300 | no |
| **extractive** | request weighted | +0.22 | -0.43 to +0.88 | 0.072 | 18 | no |
| **output_heavy** | request weighted | +0.03 | -0.22 to +0.28 | 0.001 | 42 | no |
| **agentic** | unweighted | -0.49 | -0.84 to -0.14 | 0.085 | 85 | yes |
| **all** | unweighted | -0.79 | -1.04 to -0.53 | 0.090 | 445 | yes |
| **conversational** | unweighted | -1.11 | -1.40 to -0.82 | 0.185 | 300 | yes |
| **extractive** | unweighted | -0.05 | -0.92 to +0.83 | 0.000 | 18 | no |
| **output_heavy** | unweighted | -0.11 | -0.65 to +0.43 | 0.005 | 42 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.49, interval
-0.84 to -0.14, straddling zero). Weighting by requests, the
elasticity is **-0.53** (-0.75 to -0.31) and
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
| ≥2 days silent | 72 | 406 | 90.3% | 83.5% |
| ≥3 days silent | 66 | 412 | 91.3% | 84.9% |
| ≥7 days silent | 56 | 422 | 92.5% | 87.7% |
| ≥14 days silent | 47 | 431 | 93.9% | 89.5% |

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
