# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-10-07` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 672 model-variants, 615.34 T
tokens and 28.67 B requests over the trailing 30 days.


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
| **agentic** | 93 | 497.51 T | 80.9% | 53.6 | 52,596 | large contexts, terse output, very large interactions |
| **conversational** | 307 | 113.84 T | 18.5% | 9.6 | 3,874 | moderate context per output token, human-sized interactions |
| **unclassified** | 136 | 2.71 T | 0.4% | — | 35 | insufficient data to classify |
| **extractive** | 26 | 1.12 T | 0.2% | 53.1 | 5,304 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 110 | 153.48 B | 0.0% | 0.5 | 4,070 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **80.9% of all tokens**
while being 93 of 672 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
18.5%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `upstage/solar-decide-20260928` | 2,127.4 | 4,890 | 6.90 B | extractive |
| `perplexity/pplx-decider-v1-27b-20261001` | 1,386.5 | 4,316 | 5.49 B | extractive |
| `meta-llama/llama-guard-4-12b` | 233.9 | 790 | 8.58 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 206.8 | 132,207 | 21.08 T | agentic |
| `minimax/minimax-m3-20260531` | 145.0 | 81,613 | 583.31 B | agentic |
| `upstage/solar-mini4-20260922` | 140.2 | 54,726 | 667.26 B | agentic |
| `thinkingmachines/inkling-small-20260730` | 126.9 | 57,424 | 513.14 B | agentic |
| `tencent/hy4-preview-20260827` | 113.2 | 115,650 | 47.78 T | agentic |
| `deepseek/deepseek-v4-flash-20260731` | 105.4 | 98,351 | 1.09 T | agentic |
| `openai/gpt-6-astra-20260903` | 105.2 | 64,712 | 5.08 T | agentic |

**Why both axes.** The top of this ranking is `upstage/solar-decide-20260928` at
2,127.4 tokens of context per token written, but its interactions
average only 4,890 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 206.8 tokens of context per token
written, in interactions averaging 132,207 tokens, which
is 27× larger.
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


Across 252 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **1.02** with a p25–p75 range of 0.79–1.29.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 18 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.88×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `microsoft/phi-4` | 11.69× | 4.45 B | 635 | conversational |
| `bytedance-seed/seed-2.0-lite-20260309` | 6.14× | 10.31 B | 211 | conversational |
| `google/gemini-3.7-flash-20260813` | 5.81× | 12.40 B | 55 | output_heavy |
| `inclusionai/ling-3.0-flash-vl-20260910` | 4.75× | 67.29 B | 27 | conversational |
| `stepfun/step-3.7-flash-20260528` | 4.25× | 333.96 B | 132 | conversational |
| `qwen/qwen3.8-2.4t-a95b-20260812` | 3.96× | 145.81 B | 56 | conversational |
| `meta/muse-glimmer-30b-20260810` | 3.62× | 79.42 B | 59 | conversational |
| `google/gemini-3.1-flash-lite-20260507` | 2.66× | 13.10 B | 153 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `tencent/hy-mt2-7b-20260521` | 0.02× | 2.39 B | 49 | conversational |
| `perceptron/perceptron-mk1-20260512` | 0.05× | 7.38 B | 148 | extractive |
| `openai/gpt-5-nano-2025-08-07` | 0.15× | 3.53 B | 426 | conversational |
| `tencent/hy-mt2-1.8b-20260521` | 0.15× | 2.95 B | 48 | conversational |
| `xiaomi/mimo-v2.5-20260422` | 0.19× | 18.92 T | 168 | agentic |
| `openai/gpt-5.6-luna-20260709` | 0.19× | 41.34 T | 90 | agentic |
| `mistralai/voxtral-small-24b-2507` | 0.24× | 2.07 B | 342 | conversational |
| `openai/gpt-6-astra-pro-20260903` | 0.26× | 252.67 B | 33 | agentic |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$282.6 M per month** across
465 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `openai` | 13.6% | 29.8% | 2.19x |
| `anthropic` | 3.9% | 28.0% | 7.12x |
| `tencent` | 10.2% | 15.0% | 1.48x |
| `google` | 4.9% | 6.4% | 1.29x |
| `deepseek` | 23.5% | 6.3% | 0.27x |
| `z-ai` | 12.5% | 3.3% | 0.27x |
| `xiaomi` | 6.8% | 2.7% | 0.40x |
| `moonshotai` | 1.3% | 2.2% | 1.75x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,745**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **58.8%** of
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
**6.34%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.32% |
| **extractive** | 3.29% |
| **conversational** | 1.59% |
| **output_heavy** | 0.78% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,116 endpoints serving multi-provider models,
**763 are dominated** (68.4%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-20260816` | Reka | $6.00 | 18 tok/s | Novita | 29 |
| `~z-ai/glm-latest` | Reka | $6.00 | 19 tok/s | Novita | 29 |
| `z-ai/glm-5.3-flash-20260826` | OpenInference | $0.69 | 13 tok/s | DeepInfra | 28 |
| `~z-ai/glm-flash-latest` | OpenInference | $0.69 | 13 tok/s | DeepInfra | 28 |
| `deepseek/deepseek-v4.1-flash-20260910` | DekaLLM | $2.40 | 23 tok/s | Decart | 27 |
| `~deepseek/deepseek-flash-latest` | DekaLLM | $2.40 | 23 tok/s | Decart | 27 |
| `z-ai/glm-5.3-flash-20260826` | Sail Research | $0.60 | 13 tok/s | DeepInfra | 26 |
| `~z-ai/glm-flash-latest` | Sail Research | $0.60 | 13 tok/s | DeepInfra | 26 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-09-26` and `2026-10-07`,
**81.82%** of 11 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.54 | -0.72 to -0.37 | 0.364 | 78 | yes |
| **all** | request weighted | +0.08 | -0.30 to +0.47 | 0.002 | 429 | no |
| **conversational** | request weighted | +0.47 | -0.06 to +0.99 | 0.069 | 277 | no |
| **extractive** | request weighted | +0.36 | -0.30 to +1.02 | 0.089 | 17 | no |
| **output_heavy** | request weighted | -0.20 | -0.40 to +0.00 | 0.053 | 57 | no |
| **agentic** | unweighted | -0.49 | -0.83 to -0.15 | 0.090 | 78 | yes |
| **all** | unweighted | -0.70 | -1.02 to -0.39 | 0.052 | 429 | yes |
| **conversational** | unweighted | -0.60 | -0.88 to -0.33 | 0.058 | 277 | yes |
| **extractive** | unweighted | -0.19 | -0.84 to +0.47 | 0.015 | 17 | no |
| **output_heavy** | unweighted | -1.12 | -2.01 to -0.24 | 0.083 | 57 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.49, interval
-0.83 to -0.15, straddling zero). Weighting by requests, the
elasticity is **-0.54** (-0.72 to -0.37) and
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
| ≥2 days silent | 36 | 431 | 92.6% | 90.7% |
| ≥3 days silent | 34 | 433 | 93.0% | 91.1% |
| ≥7 days silent | 34 | 433 | 93.0% | 91.1% |
| ≥14 days silent | 18 | 449 | 95.8% | 95.0% |

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
