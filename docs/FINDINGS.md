# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-10-10` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 695 model-variants, 635.51 T
tokens and 29.68 B requests over the trailing 30 days.


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
| **agentic** | 92 | 517.81 T | 81.5% | 55.0 | 53,457 | large contexts, terse output, very large interactions |
| **conversational** | 315 | 112.11 T | 17.6% | 9.4 | 3,659 | moderate context per output token, human-sized interactions |
| **unclassified** | 147 | 2.80 T | 0.4% | — | 28 | insufficient data to classify |
| **extractive** | 32 | 2.64 T | 0.4% | 52.1 | 5,143 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 109 | 151.95 B | 0.0% | 0.4 | 4,316 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **81.5% of all tokens**
while being 92 of 695 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
17.6%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `upstage/solar-decide-20260928` | 1,967.1 | 4,588 | 8.75 B | extractive |
| `perplexity/pplx-decider-v1-27b-20261001` | 1,155.6 | 4,655 | 9.10 B | extractive |
| `inception/mercury-decide-20260930` | 967.7 | 7,242 | 21.72 B | extractive |
| `perplexity/pplx-decider-v1.1-27b-20261006` | 671.0 | 7,041 | 34.30 B | extractive |
| `togethercomputer/tev1-4b-experimental-20260923` | 527.5 | 2,419 | 3.14 B | extractive |
| `meta-llama/llama-guard-4-12b` | 234.0 | 795 | 8.21 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 207.2 | 132,826 | 22.49 T | agentic |
| `stepfun/step-5-preview-20261008` | 155.3 | 187,247 | 3.22 T | agentic |
| `upstage/solar-mini4-20260922` | 130.7 | 65,333 | 1.15 T | agentic |
| `thinkingmachines/inkling-small-20260730` | 130.5 | 57,899 | 519.83 B | agentic |

**Why both axes.** The top of this ranking is `upstage/solar-decide-20260928` at
1,967.1 tokens of context per token written, but its interactions
average only 4,588 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 207.2 tokens of context per token
written, in interactions averaging 132,826 tokens, which
is 29× larger.
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


Across 253 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.97** with a p25–p75 range of 0.74–1.19.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 18 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.67×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `google/gemini-2.5-flash` | 17.83× | 2.35 B | 480 | conversational |
| `microsoft/phi-4` | 6.16× | 6.46 B | 638 | conversational |
| `google/gemini-3.1-flash-lite-20260507` | 3.28× | 15.07 B | 156 | conversational |
| `meta/muse-spark-1.3-20260902` | 3.27× | 1.52 T | 38 | agentic |
| `qwen/qwen-plus-2025-01-25` | 2.92× | 6.33 B | 616 | conversational |
| `mistralai/ministral-14b-2512` | 2.84× | 13.07 B | 312 | conversational |
| `inclusionai/ling-3.0-flash-vl-20260910` | 2.84× | 97.88 B | 30 | conversational |
| `meta-llama/llama-3.2-1b-instruct` | 2.61× | 953.22 M | 745 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `tencent/hy-mt2-7b-20260521` | 0.03× | 2.29 B | 52 | conversational |
| `tencent/hy-mt2-1.8b-20260521` | 0.03× | 2.73 B | 51 | conversational |
| `perceptron/perceptron-mk1-20260512` | 0.05× | 6.95 B | 151 | extractive |
| `openai/gpt-5.6-sol-20260709` | 0.14× | 4.77 B | 93 | conversational |
| `xiaomi/mimo-v2.5-20260422` | 0.15× | 15.81 T | 171 | agentic |
| `stepfun/step-3.7-flash-20260528` | 0.16× | 299.08 B | 135 | conversational |
| `openai/gpt-6-luna-20260922` | 0.20× | 112.76 B | 18 | conversational |
| `amazon/nova-lite-v1` | 0.24× | 16.32 B | 674 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$301.5 M per month** across
472 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 4.3% | 27.2% | 6.30x |
| `openai` | 13.1% | 22.0% | 1.68x |
| `deepseek` | 25.2% | 13.8% | 0.55x |
| `tencent` | 8.8% | 12.4% | 1.40x |
| `moonshotai` | 1.3% | 5.7% | 4.45x |
| `google` | 4.7% | 4.6% | 0.97x |
| `z-ai` | 12.2% | 4.4% | 0.36x |
| `xiaomi` | 7.0% | 2.8% | 0.40x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,223**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **53.6%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.939** by value. Both are extreme; a
national income distribution above 0.6 is considered severe.


### The sticker price is not the price

Traffic is overwhelmingly prompt-heavy, and prompt tokens cost less than
completions. Blended across each model's real token mix, the price actually paid
per token is a median **0.35x** the headline output price, so the
sticker overstates unit cost by about **2.8x**.

Anyone comparing models on `$/M output` is getting this wrong.


## 5. The context window arms race is mostly unused

Dividing mean tokens per request by the advertised context length asks how much
of the window the traffic actually touches. Token-weighted across the market:
**6.35%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.30% |
| **extractive** | 2.33% |
| **conversational** | 1.58% |
| **output_heavy** | 0.63% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,075 endpoints serving multi-provider models,
**740 are dominated** (68.8%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-20260816` | Morph | $6.00 | 18 tok/s | Inceptron | 31 |
| `~z-ai/glm-latest` | Morph | $6.00 | 18 tok/s | Inceptron | 31 |
| `z-ai/glm-5.3-flash-20260826` | Fireworks | $0.75 | 12 tok/s | StreamLake | 30 |
| `~z-ai/glm-flash-latest` | Fireworks | $0.75 | 9 tok/s | StreamLake | 30 |
| `z-ai/glm-5.3-20260816` | Cloudflare | $4.40 | 36 tok/s | Inceptron | 27 |
| `~z-ai/glm-latest` | Cloudflare | $4.40 | 36 tok/s | Inceptron | 27 |
| `deepseek/deepseek-v4.1-flash-20260910` | Alibaba | $1.20 | 59 tok/s | Decart | 25 |
| `~deepseek/deepseek-flash-latest` | Alibaba | $1.20 | 59 tok/s | Decart | 25 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-10-09` and `2026-10-10`,
**1.67%** of 538 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.40 | -0.66 to -0.14 | 0.119 | 76 | yes |
| **all** | request weighted | +0.41 | +0.12 to +0.70 | 0.046 | 444 | yes |
| **conversational** | request weighted | +0.50 | +0.00 to +1.00 | 0.078 | 293 | yes |
| **extractive** | request weighted | +0.66 | +0.17 to +1.16 | 0.422 | 19 | yes |
| **output_heavy** | request weighted | -0.27 | -0.46 to -0.09 | 0.103 | 56 | yes |
| **agentic** | unweighted | -0.52 | -0.94 to -0.09 | 0.079 | 76 | yes |
| **all** | unweighted | -0.99 | -1.33 to -0.65 | 0.080 | 444 | yes |
| **conversational** | unweighted | -0.94 | -1.32 to -0.57 | 0.093 | 293 | yes |
| **extractive** | unweighted | -0.22 | -1.62 to +1.18 | 0.006 | 19 | no |
| **output_heavy** | unweighted | -1.37 | -2.25 to -0.48 | 0.118 | 56 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.52, interval
-0.94 to -0.09, straddling zero). Weighting by requests, the
elasticity is **-0.40** (-0.66 to -0.14) and
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
| ≥2 days silent | 55 | 419 | 93.2% | 88.4% |
| ≥3 days silent | 52 | 422 | 93.4% | 88.6% |
| ≥7 days silent | 28 | 446 | 94.5% | 93.2% |
| ≥14 days silent | 24 | 450 | 94.8% | 93.9% |

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
