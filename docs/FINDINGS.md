# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-10-08` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 684 model-variants, 621.41 T
tokens and 28.99 B requests over the trailing 30 days.


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
| **agentic** | 89 | 502.19 T | 80.8% | 52.9 | 54,135 | large contexts, terse output, very large interactions |
| **conversational** | 310 | 113.55 T | 18.3% | 9.7 | 4,038 | moderate context per output token, human-sized interactions |
| **unclassified** | 147 | 2.76 T | 0.4% | — | 30 | insufficient data to classify |
| **extractive** | 29 | 2.76 T | 0.4% | 50.9 | 5,380 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 109 | 151.25 B | 0.0% | 0.5 | 3,879 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **80.8% of all tokens**
while being 89 of 684 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
18.3%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `upstage/solar-decide-20260928` | 2,149.1 | 5,107 | 7.66 B | extractive |
| `inception/mercury-decide-20260930` | 1,362.3 | 9,007 | 12.05 B | extractive |
| `perplexity/pplx-decider-v1-27b-20261001` | 1,155.6 | 4,655 | 9.10 B | extractive |
| `togethercomputer/tev1-4b-experimental-20260923` | 557.6 | 2,266 | 2.56 B | extractive |
| `meta-llama/llama-guard-4-12b` | 233.6 | 790 | 8.47 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 207.2 | 132,204 | 21.47 T | agentic |
| `upstage/solar-mini4-20260922` | 137.2 | 59,299 | 833.18 B | agentic |
| `thinkingmachines/inkling-small-20260730` | 129.4 | 57,635 | 518.12 B | agentic |
| `tencent/hy4-preview-20260827` | 113.1 | 115,587 | 45.83 T | agentic |
| `deepseek/deepseek-v4-flash-20260731` | 105.4 | 98,351 | 1.09 T | agentic |

**Why both axes.** The top of this ranking is `upstage/solar-decide-20260928` at
2,149.1 tokens of context per token written, but its interactions
average only 5,107 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 207.2 tokens of context per token
written, in interactions averaging 132,204 tokens, which
is 26× larger.
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
median of **0.98** with a p25–p75 range of 0.75–1.25.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 18 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.82×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `ibm-granite/granite-4.2-8b-20260831` | 4.34× | 32.23 B | 38 | conversational |
| `stepfun/step-3.7-flash-20260528` | 4.25× | 330.36 B | 133 | conversational |
| `meta/muse-glimmer-30b-20260810` | 4.24× | 91.53 B | 60 | conversational |
| `inclusionai/ling-3.0-flash-vl-20260910` | 3.88× | 78.13 B | 28 | conversational |
| `upstage/solar-mini4-20260922` | 2.99× | 833.18 B | 15 | agentic |
| `qwen/qwen3.8-2.4t-a95b-20260812` | 2.89× | 157.24 B | 57 | conversational |
| `anthropic/claude-opus-5.5-20260921` | 2.56× | 5.53 T | 16 | agentic |
| `deepseek/deepseek-v4.1-flash-20260910` | 2.48× | 84.98 T | 28 | agentic |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite-20260507` | 0.02× | 13.05 B | 154 | conversational |
| `google/gemini-3.7-flash-20260813` | 0.02× | 11.85 B | 56 | output_heavy |
| `perceptron/perceptron-mk1-20260512` | 0.04× | 7.33 B | 149 | extractive |
| `tencent/hy-mt2-1.8b-20260521` | 0.06× | 2.96 B | 49 | conversational |
| `tencent/hy-mt2-7b-20260521` | 0.12× | 2.38 B | 50 | conversational |
| `openai/gpt-6-luna-20260922` | 0.15× | 109.21 B | 16 | conversational |
| `xiaomi/mimo-v2.5-20260422` | 0.16× | 18.28 T | 169 | agentic |
| `openai/gpt-5-nano-2025-08-07` | 0.19× | 3.54 B | 427 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$252.6 M per month** across
465 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 4.0% | 30.0% | 7.46x |
| `openai` | 13.3% | 25.5% | 1.91x |
| `tencent` | 9.7% | 16.1% | 1.66x |
| `deepseek` | 24.3% | 5.3% | 0.22x |
| `z-ai` | 12.4% | 5.3% | 0.43x |
| `google` | 4.9% | 4.7% | 0.97x |
| `xiaomi` | 6.9% | 3.1% | 0.45x |
| `moonshotai` | 1.3% | 2.4% | 1.88x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,690**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **58.7%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.935** by value. Both are extreme; a
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
**6.23%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.67% |
| **extractive** | 3.23% |
| **conversational** | 1.60% |
| **output_heavy** | 0.64% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,114 endpoints serving multi-provider models,
**754 are dominated** (67.7%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-20260816` | Cloudflare | $4.40 | 24 tok/s | Novita | 35 |
| `~z-ai/glm-latest` | Cloudflare | $4.40 | 24 tok/s | Novita | 35 |
| `z-ai/glm-5.3-20260816` | Together | $4.40 | 25 tok/s | Novita | 33 |
| `~z-ai/glm-latest` | Together | $4.40 | 25 tok/s | Novita | 33 |
| `z-ai/glm-5.3-flash-20260826` | OpenInference | $3.67 | 14 tok/s | DeepInfra | 32 |
| `~z-ai/glm-flash-latest` | OpenInference | $3.67 | 14 tok/s | DeepInfra | 32 |
| `z-ai/glm-5.3-20260816` | Io Net | $4.40 | 28 tok/s | Decart | 29 |
| `~z-ai/glm-latest` | Io Net | $4.40 | 28 tok/s | Novita | 29 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-10-07` and `2026-10-08`,
**0.94%** of 534 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.42 | -0.64 to -0.19 | 0.143 | 79 | yes |
| **all** | request weighted | +0.33 | +0.06 to +0.60 | 0.031 | 438 | yes |
| **conversational** | request weighted | +0.48 | -0.07 to +1.03 | 0.070 | 285 | no |
| **extractive** | request weighted | +0.86 | +0.21 to +1.50 | 0.413 | 18 | yes |
| **output_heavy** | request weighted | -0.25 | -0.44 to -0.05 | 0.072 | 56 | yes |
| **agentic** | unweighted | -0.51 | -0.84 to -0.18 | 0.098 | 79 | yes |
| **all** | unweighted | -0.74 | -1.05 to -0.43 | 0.055 | 438 | yes |
| **conversational** | unweighted | -0.58 | -0.86 to -0.30 | 0.052 | 285 | yes |
| **extractive** | unweighted | -0.10 | -0.80 to +0.59 | 0.004 | 18 | no |
| **output_heavy** | unweighted | -1.12 | -2.04 to -0.20 | 0.079 | 56 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.51, interval
-0.84 to -0.18, straddling zero). Weighting by requests, the
elasticity is **-0.42** (-0.64 to -0.19) and
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
| ≥2 days silent | 54 | 413 | 92.0% | 87.4% |
| ≥3 days silent | 34 | 433 | 93.2% | 91.3% |
| ≥7 days silent | 32 | 435 | 93.6% | 91.7% |
| ≥14 days silent | 16 | 451 | 96.5% | 95.6% |

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
