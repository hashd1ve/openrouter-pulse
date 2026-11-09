# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-11-09` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 734 model-variants, 802.84 T
tokens and 38.81 B requests over the trailing 30 days.


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
| **agentic** | 98 | 637.74 T | 79.4% | 54.7 | 55,306 | large contexts, terse output, very large interactions |
| **conversational** | 303 | 108.28 T | 13.5% | 10.1 | 3,944 | moderate context per output token, human-sized interactions |
| **extractive** | 41 | 52.40 T | 6.5% | 46.5 | 4,807 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 175 | 4.24 T | 0.5% | — | 37 | insufficient data to classify |
| **output_heavy** | 117 | 177.06 B | 0.0% | 0.4 | 4,419 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **79.4% of all tokens**
while being 98 of 734 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
13.5%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `scaledown/classify-1-20260928` | 2,301.2 | 7,293 | 19.46 B | extractive |
| `upstage/solar-decide-20260928` | 2,151.8 | 4,807 | 16.74 B | extractive |
| `upstage/solar-decide-flash-20261008` | 1,507.4 | 3,612 | 9.19 B | extractive |
| `perplexity/pplx-decider-v1.1-27b-20261006` | 1,278.8 | 3,583 | 222.91 B | extractive |
| `perplexity/pplx-decider-flash-v1.2-20261016` | 1,021.2 | 2,118 | 89.87 B | extractive |
| `microsoft/microsoft-decision-1-20261009` | 584.8 | 1,712 | 104.62 B | extractive |
| `perplexity/pplx-decider-v1.2-20261016` | 513.1 | 1,936 | 890.93 B | extractive |
| `togethercomputer/tev1-4b-experimental-20260923` | 439.4 | 2,262 | 5.96 B | extractive |
| `baseten/mammoth-1-20261021` | 411.2 | 696 | 14.32 B | extractive |
| `inception/mercury-decide-20260930` | 395.0 | 734 | 116.43 B | extractive |

**Why both axes.** The top of this ranking is `scaledown/classify-1-20260928` at
2,301.2 tokens of context per token written, but its interactions
average only 7,293 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `stepfun/step-5-preview-20261008`: 201.2 tokens of context per token
written, in interactions averaging 221,529 tokens, which
is 30× larger.
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


Across 261 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.70** with a p25–p75 range of 0.51–0.98.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 16 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.25×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `thinkingmachines/inkling-small-20260730` | 3.96× | 40.71 B | 102 | conversational |
| `qwen/qwen3.5-27b-20260224` | 2.85× | 40.41 B | 257 | conversational |
| `google/gemma-3-4b-it` | 2.43× | 12.74 B | 606 | conversational |
| `amazon/nova-2-lite-v1` | 2.42× | 8.87 B | 342 | conversational |
| `nvidia/nemotron-3-nano-30b-a3b` | 2.28× | 21.80 B | 330 | conversational |
| `perceptron/perceptron-mk1-20260512` | 2.27× | 1.11 B | 181 | conversational |
| `thinkingmachines/inkling-20260715` | 2.09× | 53.16 B | 115 | conversational |
| `moonshotai/kimi-k3.1-pro-20261023` | 1.93× | 7.29 T | 17 | agentic |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-5-nano-2025-08-07` | 0.00× | 10.39 B | 459 | conversational |
| `anthropic/claude-opus-5-20260723` | 0.02× | 427.52 M | 108 | conversational |
| `google/gemini-3.6-flash-20260721` | 0.02× | 7.00 B | 111 | conversational |
| `tencent/hy4-preview-20260827` | 0.05× | 31.16 T | 73 | agentic |
| `stepfun/step-3.7-flash-20260528` | 0.05× | 870.46 B | 165 | agentic |
| `inception/mercury-2.5-20260908` | 0.06× | 115.62 B | 62 | conversational |
| `xiaomi/mimo-v2.5-20260422` | 0.07× | 866.80 B | 201 | agentic |
| `inclusionai/ling-3.0-flash-vl-20260910` | 0.09× | 35.04 B | 60 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$317.8 M per month** across
468 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 7.8% | 35.1% | 4.48x |
| `openai` | 9.6% | 14.3% | 1.49x |
| `stepfun` | 4.5% | 10.9% | 2.42x |
| `tencent` | 7.3% | 9.6% | 1.32x |
| `moonshotai` | 2.1% | 6.2% | 2.90x |
| `google` | 3.6% | 5.4% | 1.52x |
| `z-ai` | 10.5% | 4.9% | 0.47x |
| `deepseek` | 35.0% | 4.3% | 0.12x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**2,890**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **49.9%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.940** by value. Both are extreme; a
national income distribution above 0.6 is considered severe.


### The sticker price is not the price

Traffic is overwhelmingly prompt-heavy, and prompt tokens cost less than
completions. Blended across each model's real token mix, the price actually paid
per token is a median **0.34x** the headline output price, so the
sticker overstates unit cost by about **3.0x**.

Anyone comparing models on `$/M output` is getting this wrong.


## 5. The context window arms race is mostly unused

Dividing mean tokens per request by the advertised context length asks how much
of the window the traffic actually touches. Token-weighted across the market:
**6.94%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 6.84% |
| **conversational** | 1.78% |
| **extractive** | 1.56% |
| **output_heavy** | 1.34% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,238 endpoints serving multi-provider models,
**878 are dominated** (70.9%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `~deepseek/deepseek-flash-latest` | Mistral | $1.20 | 39 tok/s | DeepInfra | 43 |
| `~deepseek/deepseek-flash-latest` | Phala | $1.20 | 52 tok/s | DeepInfra | 42 |
| `deepseek/deepseek-v4.1-flash-20261017` | Mistral | $1.20 | 44 tok/s | DeepInfra | 42 |
| `z-ai/glm-5.3-flash-20260826` | AtlasCloud | $0.50 | 13 tok/s | Relace | 36 |
| `~z-ai/glm-flash-latest` | AtlasCloud | $0.50 | 13 tok/s | Relace | 36 |
| `z-ai/glm-5.3-flash-20260826` | Sail Research | $0.62 | 37 tok/s | Relace | 35 |
| `~z-ai/glm-flash-latest` | Sail Research | $0.62 | 37 tok/s | Relace | 35 |
| `z-ai/glm-5.3-flash-20260826` | Near AI | $0.50 | 25 tok/s | Relace | 35 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-10-22` and `2026-11-09`,
**100.00%** of 1 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.54 | -0.79 to -0.29 | 0.346 | 84 | yes |
| **all** | request weighted | -0.38 | -0.78 to +0.02 | 0.052 | 437 | no |
| **conversational** | request weighted | -0.34 | -0.79 to +0.10 | 0.054 | 279 | no |
| **extractive** | request weighted | -1.13 | -1.41 to -0.85 | 0.562 | 22 | yes |
| **output_heavy** | request weighted | -0.05 | -0.36 to +0.27 | 0.004 | 52 | no |
| **agentic** | unweighted | -0.42 | -0.84 to +0.00 | 0.053 | 84 | no |
| **all** | unweighted | -0.50 | -0.72 to -0.27 | 0.039 | 437 | yes |
| **conversational** | unweighted | -0.57 | -0.77 to -0.36 | 0.070 | 279 | yes |
| **extractive** | unweighted | -0.16 | -1.18 to +0.86 | 0.004 | 22 | no |
| **output_heavy** | unweighted | -0.24 | -0.74 to +0.26 | 0.012 | 52 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.42, interval
-0.84 to +0.00, straddling zero). Weighting by requests, the
elasticity is **-0.54** (-0.79 to -0.29) and
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
| ≥2 days silent | 61 | 408 | 94.7% | 87.7% |
| ≥3 days silent | 60 | 409 | 95.0% | 87.9% |
| ≥7 days silent | 48 | 421 | 96.5% | 90.3% |
| ≥14 days silent | 30 | 439 | 98.4% | 95.8% |

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
