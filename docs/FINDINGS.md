# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-10-24` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 726 model-variants, 727.70 T
tokens and 35.07 B requests over the trailing 30 days.


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
| **agentic** | 95 | 590.40 T | 81.1% | 53.1 | 51,925 | large contexts, terse output, very large interactions |
| **conversational** | 321 | 115.00 T | 15.8% | 9.0 | 3,916 | moderate context per output token, human-sized interactions |
| **extractive** | 39 | 18.72 T | 2.6% | 41.4 | 5,389 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 158 | 3.39 T | 0.5% | — | 32 | insufficient data to classify |
| **output_heavy** | 113 | 183.45 B | 0.0% | 0.3 | 3,777 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **81.1% of all tokens**
while being 95 of 726 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
15.8%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `upstage/solar-decide-20260928` | 2,158.7 | 4,950 | 21.81 B | extractive |
| `scaledown/classify-1-20260928` | 2,154.5 | 7,418 | 11.61 B | extractive |
| `upstage/solar-decide-flash-20261008` | 1,474.7 | 3,485 | 8.65 B | extractive |
| `perplexity/pplx-decider-v1-27b-20261001` | 1,155.6 | 4,655 | 9.10 B | extractive |
| `perplexity/pplx-decider-v1.1-27b-20261006` | 1,141.1 | 3,834 | 257.20 B | extractive |
| `perplexity/pplx-decider-flash-v1.2-20261016` | 985.6 | 3,089 | 20.39 B | extractive |
| `perplexity/pplx-decider-v1.2-20261016` | 522.0 | 1,981 | 141.61 B | extractive |
| `togethercomputer/tev1-4b-experimental-20260923` | 493.0 | 2,453 | 7.39 B | extractive |
| `inception/mercury-decide-20260930` | 362.3 | 4,463 | 105.77 B | extractive |
| `inception/mercury-decide-20260930` | 347.6 | 1,299 | 44.61 B | extractive |

**Why both axes.** The top of this ranking is `upstage/solar-decide-20260928` at
2,158.7 tokens of context per token written, but its interactions
average only 4,950 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 195.0 tokens of context per token
written, in interactions averaging 134,869 tokens, which
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


Across 261 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.90** with a p25–p75 range of 0.67–1.14.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 20 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **2.19×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-5-nano-2025-08-07` | 10.78× | 11.67 B | 443 | conversational |
| `nex-agi/nex-n2.5-mini-20260908` | 5.95× | 8.17 B | 46 | conversational |
| `openai/gpt-6-sol-20260922` | 3.67× | 6.95 B | 32 | conversational |
| `scaledown/summarize-20260928` | 3.53× | 10.13 B | 11 | extractive |
| `stepfun/step-3.7-flash-20260528` | 3.50× | 331.20 B | 149 | conversational |
| `z-ai/glm-5.3-flash-20260826` | 2.98× | 15.41 B | 59 | conversational |
| `openai/gpt-5.2-20251211` | 2.53× | 187.50 B | 318 | conversational |
| `qwen/qwen3.5-35b-a3b-20260224` | 2.29× | 70.95 B | 241 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `nvidia/nemotron-3-super-120b-a12b-20230311` | 0.00× | 2.06 T | 227 | agentic |
| `inclusionai/ling-3.0-flash-vl-20260910` | 0.03× | 124.46 B | 44 | conversational |
| `xiaomi/mimo-v2.5-20260422` | 0.06× | 3.13 T | 185 | agentic |
| `google/gemma-2-27b-it` | 0.07× | 716.05 M | 833 | conversational |
| `inclusionai/ling-3.1-flash-20261002` | 0.10× | 1.11 T | 22 | conversational |
| `thinkingmachines/inkling-small-20260730` | 0.10× | 41.10 B | 86 | conversational |
| `google/gemini-3.7-flash-20260813` | 0.18× | 8.70 B | 72 | output_heavy |
| `xiaomi/mimo-v2.5-pro-20260422` | 0.19× | 658.44 B | 185 | agentic |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$351.7 M per month** across
485 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 6.7% | 40.8% | 6.11x |
| `openai` | 10.2% | 20.5% | 2.01x |
| `tencent` | 6.3% | 8.5% | 1.35x |
| `stepfun` | 3.2% | 6.4% | 2.01x |
| `deepseek` | 27.8% | 5.0% | 0.18x |
| `google` | 4.1% | 4.2% | 1.02x |
| `z-ai` | 10.4% | 3.6% | 0.35x |
| `xiaomi` | 7.2% | 3.1% | 0.43x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**4,064**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **62.0%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.936** by value. Both are extreme; a
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
**6.54%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.11% |
| **extractive** | 2.12% |
| **conversational** | 1.67% |
| **output_heavy** | 0.37% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,151 endpoints serving multi-provider models,
**813 are dominated** (70.6%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-20260816` | Parasail | $4.40 | 41 tok/s | Wafer | 36 |
| `~z-ai/glm-latest` | Parasail | $4.40 | 41 tok/s | Wafer | 36 |
| `deepseek/deepseek-v4.1-flash-20260910` | Google | $1.20 | 26 tok/s | Decart | 36 |
| `z-ai/glm-5.3-20260816` | AkashML | $4.40 | 46 tok/s | Wafer | 35 |
| `~z-ai/glm-latest` | AkashML | $4.40 | 46 tok/s | Wafer | 35 |
| `z-ai/glm-5.3-20260816` | Morph | $4.40 | 48 tok/s | Wafer | 34 |
| `~z-ai/glm-latest` | Morph | $4.40 | 48 tok/s | Wafer | 34 |
| `z-ai/glm-5.3-20260816` | Fireworks | $4.40 | 51 tok/s | Wafer | 33 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-10-23` and `2026-10-24`,
**1.41%** of 567 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.70 | -0.95 to -0.45 | 0.508 | 81 | yes |
| **all** | request weighted | -0.36 | -0.79 to +0.07 | 0.050 | 444 | no |
| **conversational** | request weighted | -0.39 | -0.85 to +0.07 | 0.074 | 289 | no |
| **extractive** | request weighted | -0.87 | -1.41 to -0.34 | 0.323 | 23 | yes |
| **output_heavy** | request weighted | -0.26 | -0.41 to -0.10 | 0.204 | 51 | yes |
| **agentic** | unweighted | -0.43 | -0.79 to -0.07 | 0.062 | 81 | yes |
| **all** | unweighted | -0.84 | -1.17 to -0.51 | 0.061 | 444 | yes |
| **conversational** | unweighted | -0.82 | -1.15 to -0.49 | 0.075 | 289 | yes |
| **extractive** | unweighted | +0.07 | -0.61 to +0.75 | 0.002 | 23 | no |
| **output_heavy** | unweighted | -1.01 | -1.97 to -0.05 | 0.072 | 51 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.43, interval
-0.79 to -0.07, straddling zero). Weighting by requests, the
elasticity is **-0.70** (-0.95 to -0.45) and
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
| ≥2 days silent | 76 | 410 | 92.3% | 86.4% |
| ≥3 days silent | 71 | 415 | 93.3% | 87.3% |
| ≥7 days silent | 64 | 422 | 93.3% | 87.3% |
| ≥14 days silent | 51 | 435 | 95.5% | 90.4% |

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
