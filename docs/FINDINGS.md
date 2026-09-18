# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-09-18` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 635 model-variants, 496.81 T
tokens and 23.04 B requests over the trailing 30 days.


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
| **agentic** | 88 | 420.90 T | 84.7% | 52.1 | 49,880 | large contexts, terse output, very large interactions |
| **conversational** | 311 | 72.83 T | 14.7% | 9.9 | 3,824 | moderate context per output token, human-sized interactions |
| **unclassified** | 122 | 2.32 T | 0.5% | — | 26 | insufficient data to classify |
| **extractive** | 19 | 600.88 B | 0.1% | 36.0 | 8,758 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 95 | 147.69 B | 0.0% | 0.5 | 4,413 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **84.7% of all tokens**
while being 88 of 635 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
14.7%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 261.5 | 886 | 9.18 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 199.0 | 123,963 | 18.35 T | agentic |
| `xiaomi/mimo-v2.5-20260422` | 134.7 | 72,386 | 30.58 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 124.3 | 83,364 | 5.63 T | agentic |
| `minimax/minimax-m3-20260531` | 119.2 | 76,887 | 8.17 T | agentic |
| `thinkingmachines/inkling-small-20260730` | 118.1 | 55,985 | 377.23 B | agentic |
| `tencent/hy4-preview-20260827` | 111.5 | 116,998 | 41.66 T | agentic |
| `openai/gpt-6-astra-20260903` | 106.2 | 69,798 | 2.12 T | agentic |
| `poolside/laguna-xs-2.1-20260625` | 104.7 | 49,626 | 441.77 B | agentic |
| `thinkingmachines/inkling-20260715` | 101.5 | 73,169 | 1.04 T | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
261.5 tokens of context per token written, but its interactions
average only 886 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 199.0 tokens of context per token
written, in interactions averaging 123,963 tokens, which
is 140× larger.
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
median of **0.98** with a p25–p75 range of 0.78–1.24.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 23 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.88×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `mistralai/voxtral-small-24b-2507` | 13.24× | 1.17 B | 323 | conversational |
| `openai/gpt-6-astra-20260903` | 5.48× | 2.12 T | 14 | agentic |
| `thinkingmachines/inkling-20260715` | 3.59× | 125.11 B | 63 | agentic |
| `z-ai/glm-4.6-20251208` | 3.48× | 9.65 B | 284 | conversational |
| `tencent/hy-mt2-1.8b-20260521` | 3.36× | 1.89 B | 29 | conversational |
| `tencent/hy-mt2-30b-a3b-20260521` | 3.23× | 3.81 B | 29 | conversational |
| `moonshotai/kimi-k2-thinking-20251106` | 3.12× | 15.34 B | 316 | conversational |
| `tencent/hy-mt2-7b-20260521` | 2.91× | 1.51 B | 30 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `google/gemini-3.7-flash-20260813` | 0.03× | 34.63 B | 36 | conversational |
| `stepfun/step-3.7-flash-20260528` | 0.06× | 1.32 T | 113 | agentic |
| `meta-llama/llama-3.2-1b-instruct` | 0.11× | 2.14 B | 723 | output_heavy |
| `meta/muse-spark-1.1-20260709` | 0.13× | 73.31 B | 64 | agentic |
| `meta/muse-spark-1.2-contributor-20260805` | 0.13× | 573.69 B | 28 | conversational |
| `z-ai/glm-5v-turbo-20260401` | 0.14× | 50.83 B | 170 | agentic |
| `bytedance-seed/seed-2.0-mini-20260224` | 0.16× | 42.85 B | 204 | conversational |
| `meta/muse-spark-1.2-20260805` | 0.16× | 239.21 B | 44 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$254.1 M per month** across
462 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 4.4% | 32.0% | 7.31x |
| `openai` | 14.5% | 17.1% | 1.18x |
| `tencent` | 13.0% | 15.2% | 1.17x |
| `deepseek` | 19.9% | 9.6% | 0.48x |
| `moonshotai` | 1.7% | 6.6% | 3.95x |
| `google` | 6.4% | 5.9% | 0.91x |
| `z-ai` | 11.7% | 4.3% | 0.37x |
| `x-ai` | 0.5% | 2.1% | 3.95x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**2,683**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **46.4%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.937** by value. Both are extreme; a
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
**9.13%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.38% |
| **extractive** | 5.35% |
| **conversational** | 1.67% |
| **output_heavy** | 1.50% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,017 endpoints serving multi-provider models,
**706 are dominated** (69.4%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-20260816` | AtlasCloud | $4.40 | 25 tok/s | Phala | 24 |
| `~z-ai/glm-latest` | AtlasCloud | $4.40 | 24 tok/s | Phala | 23 |
| `z-ai/glm-5.3-20260816` | Cloudflare | $4.40 | 31 tok/s | Phala | 22 |
| `z-ai/glm-5.2-20260616` | Baidu | $4.40 | 40 tok/s | DeepInfra | 21 |
| `~z-ai/glm-latest` | Cloudflare | $4.40 | 31 tok/s | Phala | 21 |
| `deepseek/deepseek-v4-flash-20260731` | Alibaba | $1.06 | 10 tok/s | Relace | 21 |
| `~deepseek/deepseek-v4-flash-latest` | Alibaba | $1.06 | 10 tok/s | Relace | 21 |
| `z-ai/glm-5.3-flash-20260826` | DigitalOcean | $0.50 | 19 tok/s | InferenceNet | 20 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-09-17` and `2026-09-18`,
**0.98%** of 510 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.52 | -0.74 to -0.29 | 0.252 | 73 | yes |
| **all** | request weighted | -0.03 | -0.48 to +0.43 | 0.000 | 419 | no |
| **conversational** | request weighted | -0.19 | -0.86 to +0.47 | 0.013 | 281 | no |
| **extractive** | request weighted | +0.70 | +0.30 to +1.10 | 0.430 | 16 | yes |
| **output_heavy** | request weighted | -0.21 | -0.53 to +0.10 | 0.080 | 49 | no |
| **agentic** | unweighted | -0.52 | -0.89 to -0.14 | 0.073 | 73 | yes |
| **all** | unweighted | -0.70 | -0.96 to -0.44 | 0.082 | 419 | yes |
| **conversational** | unweighted | -0.96 | -1.25 to -0.67 | 0.179 | 281 | yes |
| **extractive** | unweighted | -0.01 | -0.36 to +0.35 | 0.000 | 16 | no |
| **output_heavy** | unweighted | -0.25 | -0.97 to +0.47 | 0.012 | 49 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.52, interval
-0.89 to -0.14, straddling zero). Weighting by requests, the
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
| ≥2 days silent | 84 | 381 | 90.2% | 81.8% |
| ≥3 days silent | 73 | 392 | 91.7% | 84.0% |
| ≥7 days silent | 61 | 404 | 93.1% | 86.1% |
| ≥14 days silent | 52 | 413 | 95.0% | 87.8% |

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
