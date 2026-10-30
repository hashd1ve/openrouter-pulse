# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-10-30` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 734 model-variants, 756.70 T
tokens and 37.11 B requests over the trailing 30 days.


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
| **agentic** | 94 | 570.04 T | 75.3% | 55.4 | 53,761 | large contexts, terse output, very large interactions |
| **conversational** | 322 | 169.04 T | 22.3% | 9.3 | 3,972 | moderate context per output token, human-sized interactions |
| **extractive** | 40 | 13.69 T | 1.8% | 47.9 | 4,761 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 170 | 3.76 T | 0.5% | — | 33 | insufficient data to classify |
| **output_heavy** | 108 | 173.26 B | 0.0% | 0.3 | 4,388 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **75.3% of all tokens**
while being 94 of 734 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
22.3%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `upstage/solar-decide-20260928` | 2,207.9 | 4,913 | 22.66 B | extractive |
| `scaledown/classify-1-20260928` | 2,176.6 | 7,166 | 13.70 B | extractive |
| `upstage/solar-decide-flash-20261008` | 1,488.6 | 3,449 | 9.64 B | extractive |
| `perplexity/pplx-decider-flash-v1.2-20261016` | 1,197.6 | 3,375 | 59.68 B | extractive |
| `perplexity/pplx-decider-v1-27b-20261001` | 1,155.6 | 4,655 | 9.10 B | extractive |
| `perplexity/pplx-decider-v1.1-27b-20261006` | 1,141.1 | 3,834 | 257.20 B | extractive |
| `togethercomputer/tev1-4b-experimental-20260923` | 488.1 | 2,380 | 7.83 B | extractive |
| `perplexity/pplx-decider-v1.2-20261016` | 467.6 | 2,009 | 366.55 B | extractive |
| `inception/mercury-decide-20260930` | 396.3 | 937 | 74.26 B | extractive |
| `inception/mercury-decide-20260930` | 389.6 | 4,867 | 152.23 B | extractive |

**Why both axes.** The top of this ranking is `upstage/solar-decide-20260928` at
2,207.9 tokens of context per token written, but its interactions
average only 4,913 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `stepfun/step-5-preview-20261008`: 190.2 tokens of context per token
written, in interactions averaging 206,939 tokens, which
is 42× larger.
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


Across 262 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.92** with a p25–p75 range of 0.71–1.18.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 20 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.88×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-3.5-turbo-0613` | 7.25× | 407.94 M | 1,009 | conversational |
| `nex-agi/nex-n2.5-mini-20260908` | 4.21× | 30.70 B | 52 | conversational |
| `google/gemini-3.8-flash-20260902` | 4.14× | 13.62 B | 58 | conversational |
| `openai/gpt-5.6-luna-20260709` | 4.10× | 57.25 B | 113 | conversational |
| `google/gemma-3-4b-it` | 3.81× | 6.03 B | 596 | conversational |
| `openai/gpt-6.1-sol-20260929` | 3.40× | 10.00 T | 31 | agentic |
| `stepfun/step-3.7-flash-20260528` | 3.27× | 672.85 B | 155 | agentic |
| `bytedance-seed/seed-2.0-lite-20260309` | 3.26× | 18.52 B | 234 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `google/gemini-3.6-flash-20260721` | 0.01× | 11.92 B | 101 | conversational |
| `inclusionai/ling-3.0-flash-vl-20260910` | 0.03× | 103.08 B | 50 | conversational |
| `openai/gpt-6-sol-20260922` | 0.04× | 6.61 B | 38 | conversational |
| `xiaomi/mimo-v2.5-20260422` | 0.07× | 2.07 T | 191 | agentic |
| `inclusionai/ling-3.1-flash-20261002` | 0.10× | 1.14 T | 28 | conversational |
| `xiaomi/mimo-v2.5-pro-20260422` | 0.13× | 538.40 B | 191 | agentic |
| `thinkingmachines/inkling-20260715` | 0.16× | 60.48 B | 105 | conversational |
| `z-ai/glm-5.3-flash-20260826` | 0.20× | 22.87 B | 65 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$386.1 M per month** across
477 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 7.5% | 42.0% | 5.61x |
| `openai` | 10.0% | 17.6% | 1.76x |
| `tencent` | 6.3% | 8.1% | 1.27x |
| `stepfun` | 3.9% | 7.3% | 1.88x |
| `deepseek` | 30.7% | 6.7% | 0.22x |
| `google` | 3.9% | 3.9% | 1.01x |
| `z-ai` | 10.8% | 3.8% | 0.35x |
| `xiaomi` | 6.2% | 2.8% | 0.45x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,572**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **57.5%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.943** by value. Both are extreme; a
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
**6.55%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 6.45% |
| **extractive** | 2.35% |
| **conversational** | 1.72% |
| **output_heavy** | 0.81% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,186 endpoints serving multi-provider models,
**839 are dominated** (70.7%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-20260816` | Cloudflare | $4.40 | 31 tok/s | Baidu | 37 |
| `~z-ai/glm-latest` | Cloudflare | $4.40 | 29 tok/s | Baidu | 37 |
| `deepseek/deepseek-v4.1-flash-20260910` | Google | $1.20 | 42 tok/s | Decart | 34 |
| `z-ai/glm-5.3-flash-20260826` | Near AI | $0.50 | 21 tok/s | OpenInference | 33 |
| `~z-ai/glm-flash-latest` | Near AI | $0.50 | 22 tok/s | OpenInference | 33 |
| `z-ai/glm-5.3-flash-20260826` | Parasail | $0.50 | 26 tok/s | OpenInference | 32 |
| `~z-ai/glm-flash-latest` | Parasail | $0.50 | 26 tok/s | OpenInference | 32 |
| `z-ai/glm-5.3-flash-20260826` | SiliconFlow | $0.50 | 34 tok/s | OpenInference | 31 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-10-29` and `2026-10-30`,
**1.07%** of 562 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.62 | -0.87 to -0.37 | 0.480 | 80 | yes |
| **all** | request weighted | -0.46 | -0.90 to -0.03 | 0.082 | 440 | yes |
| **conversational** | request weighted | -0.59 | -1.18 to +0.01 | 0.105 | 292 | no |
| **extractive** | request weighted | -0.81 | -1.27 to -0.36 | 0.334 | 21 | yes |
| **output_heavy** | request weighted | -0.26 | -0.46 to -0.06 | 0.123 | 47 | yes |
| **agentic** | unweighted | -0.45 | -0.85 to -0.04 | 0.057 | 80 | yes |
| **all** | unweighted | -0.83 | -1.15 to -0.50 | 0.069 | 440 | yes |
| **conversational** | unweighted | -0.76 | -1.10 to -0.43 | 0.073 | 292 | yes |
| **extractive** | unweighted | -0.16 | -0.93 to +0.60 | 0.006 | 21 | no |
| **output_heavy** | unweighted | -1.47 | -2.32 to -0.62 | 0.158 | 47 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.45, interval
-0.85 to -0.04, straddling zero). Weighting by requests, the
elasticity is **-0.62** (-0.87 to -0.37) and
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
| ≥2 days silent | 67 | 411 | 96.7% | 89.2% |
| ≥3 days silent | 66 | 412 | 96.7% | 89.7% |
| ≥7 days silent | 57 | 421 | 96.7% | 91.7% |
| ≥14 days silent | 39 | 439 | 96.9% | 92.9% |

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
