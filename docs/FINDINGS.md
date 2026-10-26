# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-10-26` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 716 model-variants, 730.17 T
tokens and 35.69 B requests over the trailing 30 days.


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
| **agentic** | 92 | 546.18 T | 74.8% | 53.1 | 52,880 | large contexts, terse output, very large interactions |
| **conversational** | 319 | 163.33 T | 22.4% | 9.5 | 3,927 | moderate context per output token, human-sized interactions |
| **extractive** | 39 | 16.99 T | 2.3% | 40.7 | 4,990 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 158 | 3.48 T | 0.5% | — | 32 | insufficient data to classify |
| **output_heavy** | 108 | 186.33 B | 0.0% | 0.3 | 4,235 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **74.8% of all tokens**
while being 92 of 716 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
22.4%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `scaledown/classify-1-20260928` | 2,220.8 | 7,472 | 12.40 B | extractive |
| `upstage/solar-decide-20260928` | 2,191.9 | 4,990 | 22.59 B | extractive |
| `upstage/solar-decide-flash-20261008` | 1,495.7 | 3,466 | 9.08 B | extractive |
| `perplexity/pplx-decider-v1-27b-20261001` | 1,155.6 | 4,655 | 9.10 B | extractive |
| `perplexity/pplx-decider-v1.1-27b-20261006` | 1,141.1 | 3,834 | 257.20 B | extractive |
| `perplexity/pplx-decider-flash-v1.2-20261016` | 1,018.0 | 2,722 | 30.45 B | extractive |
| `perplexity/pplx-decider-v1.2-20261016` | 519.6 | 1,955 | 185.67 B | extractive |
| `togethercomputer/tev1-4b-experimental-20260923` | 492.6 | 2,436 | 7.49 B | extractive |
| `inception/mercury-decide-20260930` | 376.0 | 4,606 | 126.05 B | extractive |
| `inception/mercury-decide-20260930` | 351.2 | 1,181 | 48.80 B | extractive |

**Why both axes.** The top of this ranking is `scaledown/classify-1-20260928` at
2,220.8 tokens of context per token written, but its interactions
average only 7,472 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `stepfun/step-5-preview-20261008`: 186.8 tokens of context per token
written, in interactions averaging 200,762 tokens, which
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


Across 262 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.78** with a p25–p75 range of 0.52–0.96.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 21 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **2.14×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `tencent/hy-mt2-1.8b-20260521` | 9.14× | 227.52 M | 67 | output_heavy |
| `z-ai/glm-5.3-flash-20260826` | 8.64× | 21.76 B | 61 | conversational |
| `nex-agi/nex-n2.5-mini-20260908` | 7.63× | 14.81 B | 48 | conversational |
| `google/gemini-3.1-flash-lite-20260507` | 3.70× | 22.45 B | 172 | conversational |
| `stepfun/step-3.7-flash-20260528` | 3.23× | 408.88 B | 151 | conversational |
| `nousresearch/hermes-4-405b` | 3.14× | 3.39 B | 426 | conversational |
| `minimax/minimax-m3.1-flash-20261019` | 3.00× | 789.14 B | 7 | agentic |
| `openai/gpt-6-luna-20260922` | 2.58× | 363.86 B | 34 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `nvidia/nemotron-3-super-120b-a12b-20230311` | 0.00× | 1.97 T | 229 | agentic |
| `openai/gpt-5-nano-2025-08-07` | 0.00× | 10.45 B | 445 | conversational |
| `inclusionai/ling-3.0-flash-vl-20260910` | 0.04× | 118.91 B | 46 | conversational |
| `xiaomi/mimo-v2.5-20260422` | 0.04× | 2.71 T | 187 | agentic |
| `perceptron/perceptron-mk1-20260512` | 0.04× | 6.92 B | 167 | extractive |
| `openai/gpt-5.6-sol-pro-20260709` | 0.10× | 101.45 B | 109 | conversational |
| `inclusionai/ling-3.1-flash-20261002` | 0.11× | 1.12 T | 24 | conversational |
| `google/gemini-3.7-flash-20260813` | 0.13× | 8.22 B | 74 | output_heavy |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$373.6 M per month** across
475 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 6.9% | 40.7% | 5.93x |
| `openai` | 10.1% | 17.6% | 1.75x |
| `tencent` | 6.3% | 8.0% | 1.27x |
| `deepseek` | 28.8% | 7.7% | 0.27x |
| `stepfun` | 3.4% | 6.5% | 1.89x |
| `google` | 4.0% | 5.1% | 1.29x |
| `z-ai` | 10.4% | 3.7% | 0.36x |
| `xiaomi` | 6.9% | 2.9% | 0.41x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,112**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **52.6%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.929** by value. Both are extreme; a
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
**6.53%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.22% |
| **extractive** | 1.90% |
| **conversational** | 1.71% |
| **output_heavy** | 0.68% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,153 endpoints serving multi-provider models,
**799 are dominated** (69.3%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-20260816` | Alibaba | $8.80 | 58 tok/s | Wafer | 32 |
| `deepseek/deepseek-v4.1-flash-20260910` | Google | $1.20 | 56 tok/s | Sail Research | 32 |
| `z-ai/glm-5.3-20260816` | Cloudflare | $4.40 | 29 tok/s | Wafer | 32 |
| `~z-ai/glm-latest` | Cloudflare | $4.40 | 21 tok/s | Wafer | 32 |
| `~z-ai/glm-latest` | Alibaba | $8.80 | 61 tok/s | Wafer | 31 |
| `deepseek/deepseek-v4.1-flash-20260910` | Fireworks | $1.20 | 58 tok/s | Sail Research | 31 |
| `z-ai/glm-5.3-20260816` | Z.AI | $4.40 | 44 tok/s | Wafer | 31 |
| `~z-ai/glm-latest` | Z.AI | $4.40 | 44 tok/s | Wafer | 31 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-10-25` and `2026-10-26`,
**1.08%** of 558 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.39 | -0.60 to -0.18 | 0.118 | 81 | yes |
| **all** | request weighted | -0.05 | -0.46 to +0.36 | 0.001 | 446 | no |
| **conversational** | request weighted | -0.24 | -0.87 to +0.39 | 0.021 | 293 | no |
| **extractive** | request weighted | -0.57 | -1.23 to +0.08 | 0.101 | 23 | no |
| **output_heavy** | request weighted | +0.48 | -0.30 to +1.27 | 0.199 | 49 | no |
| **agentic** | unweighted | -0.31 | -0.66 to +0.04 | 0.033 | 81 | no |
| **all** | unweighted | -0.89 | -1.21 to -0.57 | 0.074 | 446 | yes |
| **conversational** | unweighted | -0.85 | -1.20 to -0.50 | 0.082 | 293 | yes |
| **extractive** | unweighted | +0.06 | -0.60 to +0.72 | 0.001 | 23 | no |
| **output_heavy** | unweighted | -1.49 | -2.30 to -0.67 | 0.154 | 49 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.31, interval
-0.66 to +0.04, straddling zero). Weighting by requests, the
elasticity is **-0.39** (-0.60 to -0.18) and
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
| ≥2 days silent | 75 | 401 | 95.2% | 87.8% |
| ≥3 days silent | 73 | 403 | 95.5% | 88.1% |
| ≥7 days silent | 57 | 419 | 95.7% | 89.7% |
| ≥14 days silent | 41 | 435 | 98.0% | 92.8% |

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
