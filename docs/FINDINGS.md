# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-09-28` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 640 model-variants, 543.48 T
tokens and 25.19 B requests over the trailing 30 days.


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
| **agentic** | 98 | 426.04 T | 78.4% | 52.9 | 52,870 | large contexts, terse output, very large interactions |
| **conversational** | 302 | 114.34 T | 21.0% | 9.6 | 3,813 | moderate context per output token, human-sized interactions |
| **unclassified** | 124 | 2.47 T | 0.5% | — | 27 | insufficient data to classify |
| **extractive** | 18 | 488.99 B | 0.1% | 35.9 | 5,971 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 98 | 144.75 B | 0.0% | 0.5 | 4,417 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **78.4% of all tokens**
while being 98 of 640 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
21.0%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 241.0 | 810 | 9.29 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 205.5 | 130,442 | 18.68 T | agentic |
| `thinkingmachines/inkling-small-20260730` | 124.2 | 57,374 | 487.83 B | agentic |
| `minimax/minimax-m3-20260531` | 119.6 | 77,424 | 7.05 T | agentic |
| `xiaomi/mimo-v2.5-20260422` | 119.2 | 64,372 | 21.03 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 116.1 | 83,128 | 5.15 T | agentic |
| `tencent/hy4-preview-20260827` | 112.3 | 116,294 | 56.35 T | agentic |
| `deepseek/deepseek-v4-flash-20260731` | 105.4 | 98,351 | 1.09 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 104.4 | 93,426 | 231.17 B | agentic |
| `openai/gpt-6-astra-20260903` | 98.8 | 63,040 | 3.65 T | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
241.0 tokens of context per token written, but its interactions
average only 810 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 205.5 tokens of context per token
written, in interactions averaging 130,442 tokens, which
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


Across 241 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.76** with a p25–p75 range of 0.52–1.01.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 17 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.25×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite-20260507` | 5.17× | 11.16 B | 144 | conversational |
| `bytedance-seed/seed-2.0-lite-20260309` | 3.67× | 7.49 B | 202 | conversational |
| `inclusionai/ling-3.0-flash-vl-20260910` | 3.46× | 18.92 B | 18 | conversational |
| `qwen/qwen3.8-27b-20260814` | 3.16× | 44.03 B | 45 | agentic |
| `z-ai/glm-5.3-flash-20260826` | 2.91× | 9.10 B | 33 | conversational |
| `inclusionai/ling-3.0-flash-fin-20260827` | 2.58× | 10.32 B | 32 | conversational |
| `cohere/command-r7b-12-2024` | 2.04× | 1.25 B | 653 | conversational |
| `meta-llama/llama-3.3-70b-instruct` | 1.98× | 148.21 B | 661 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `tencent/hy-mt2-7b-20260521` | 0.08× | 2.44 B | 40 | conversational |
| `meta/muse-spark-1.1-20260709` | 0.08× | 44.07 B | 74 | conversational |
| `qwen/qwen-plus-2025-07-28` | 0.08× | 3.19 B | 385 | conversational |
| `openai/gpt-5.6-sol-20260709` | 0.08× | 5.52 B | 81 | conversational |
| `tencent/hy-mt2-1.8b-20260521` | 0.09× | 3.02 B | 39 | conversational |
| `stepfun/step-3.7-flash-20260528` | 0.11× | 719.48 B | 123 | agentic |
| `google/gemini-3.6-flash-20260721` | 0.11× | 11.71 B | 69 | conversational |
| `thinkingmachines/inkling-20260715` | 0.12× | 149.49 B | 73 | agentic |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$269.8 M per month** across
457 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 4.0% | 25.6% | 6.44x |
| `openai` | 14.9% | 20.0% | 1.34x |
| `tencent` | 13.6% | 18.6% | 1.37x |
| `z-ai` | 14.5% | 10.0% | 0.68x |
| `moonshotai` | 1.5% | 8.3% | 5.57x |
| `deepseek` | 21.6% | 4.5% | 0.21x |
| `google` | 5.6% | 3.9% | 0.70x |
| `qwen` | 1.6% | 2.0% | 1.22x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,266**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **54.3%** of
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
**6.24%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.44% |
| **extractive** | 3.59% |
| **conversational** | 1.65% |
| **output_heavy** | 1.38% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,117 endpoints serving multi-provider models,
**775 are dominated** (69.4%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-20260816` | Alibaba | $8.80 | 23 tok/s | Reka | 34 |
| `~z-ai/glm-latest` | Alibaba | $8.80 | 23 tok/s | Reka | 34 |
| `z-ai/glm-5.3-20260816` | Cloudflare | $4.40 | 20 tok/s | Reka | 34 |
| `~z-ai/glm-latest` | Cloudflare | $4.40 | 22 tok/s | Reka | 32 |
| `z-ai/glm-5.3-20260816` | BaseTen | $4.40 | 30 tok/s | Reka | 30 |
| `~z-ai/glm-latest` | BaseTen | $4.40 | 30 tok/s | Reka | 30 |
| `z-ai/glm-5.3-20260816` | AtlasCloud | $4.40 | 32 tok/s | Reka | 29 |
| `~z-ai/glm-latest` | AtlasCloud | $4.40 | 30 tok/s | Reka | 29 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-09-27` and `2026-09-28`,
**1.55%** of 516 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.49 | -0.73 to -0.26 | 0.239 | 85 | yes |
| **all** | request weighted | -0.18 | -0.56 to +0.21 | 0.009 | 422 | no |
| **conversational** | request weighted | -0.39 | -0.87 to +0.10 | 0.035 | 274 | no |
| **extractive** | request weighted | +0.73 | +0.39 to +1.07 | 0.527 | 16 | yes |
| **output_heavy** | request weighted | -0.17 | -0.53 to +0.19 | 0.032 | 47 | no |
| **agentic** | unweighted | -0.66 | -1.01 to -0.32 | 0.150 | 85 | yes |
| **all** | unweighted | -0.61 | -0.87 to -0.34 | 0.049 | 422 | yes |
| **conversational** | unweighted | -0.63 | -0.95 to -0.32 | 0.070 | 274 | yes |
| **extractive** | unweighted | -0.33 | -1.05 to +0.38 | 0.050 | 16 | no |
| **output_heavy** | unweighted | -0.45 | -1.23 to +0.32 | 0.015 | 47 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.66, interval
-1.01 to -0.32, straddling zero). Weighting by requests, the
elasticity is **-0.49** (-0.73 to -0.26) and
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
| ≥2 days silent | 56 | 402 | 89.7% | 85.2% |
| ≥3 days silent | 55 | 403 | 89.7% | 85.2% |
| ≥7 days silent | 38 | 420 | 93.5% | 89.3% |
| ≥14 days silent | 23 | 435 | 95.4% | 93.2% |

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
