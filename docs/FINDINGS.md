# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-11-06` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 740 model-variants, 796.27 T
tokens and 38.69 B requests over the trailing 30 days.


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
| **agentic** | 94 | 626.52 T | 78.7% | 57.7 | 58,039 | large contexts, terse output, very large interactions |
| **conversational** | 318 | 111.41 T | 14.0% | 9.8 | 3,860 | moderate context per output token, human-sized interactions |
| **extractive** | 43 | 53.99 T | 6.8% | 45.9 | 5,284 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 174 | 4.19 T | 0.5% | — | 34 | insufficient data to classify |
| **output_heavy** | 111 | 174.23 B | 0.0% | 0.3 | 4,406 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **78.7% of all tokens**
while being 94 of 740 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
14.0%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `scaledown/classify-1-20260928` | 2,337.6 | 7,515 | 19.28 B | extractive |
| `upstage/solar-decide-20260928` | 2,074.6 | 4,667 | 18.19 B | extractive |
| `upstage/solar-decide-flash-20261008` | 1,444.2 | 3,170 | 10.89 B | extractive |
| `perplexity/pplx-decider-v1.1-27b-20261006` | 1,141.1 | 3,834 | 257.20 B | extractive |
| `perplexity/pplx-decider-flash-v1.2-20261016` | 1,015.2 | 2,086 | 84.85 B | extractive |
| `microsoft/microsoft-decision-1-20261009` | 569.8 | 1,624 | 91.07 B | extractive |
| `perplexity/pplx-decider-v1.2-20261016` | 516.6 | 2,033 | 741.88 B | extractive |
| `togethercomputer/tev1-4b-experimental-20260923` | 441.9 | 2,424 | 6.76 B | extractive |
| `inception/mercury-decide-20260930` | 401.1 | 751 | 106.44 B | extractive |
| `inception/mercury-decide-20260930` | 378.4 | 4,809 | 145.94 B | extractive |

**Why both axes.** The top of this ranking is `scaledown/classify-1-20260928` at
2,337.6 tokens of context per token written, but its interactions
average only 7,515 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `stepfun/step-5-preview-20261008`: 194.6 tokens of context per token
written, in interactions averaging 215,156 tokens, which
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


Across 261 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.94** with a p25–p75 range of 0.72–1.14.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 17 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.43×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `nvidia/nemotron-3.5-super-vl-20261015` | 4.97× | 954.26 B | 22 | conversational |
| `anthropic/claude-opus-5-20260723` | 4.54× | 497.32 M | 105 | conversational |
| `amazon/nova-2-lite-v1` | 3.03× | 5.66 B | 339 | conversational |
| `bytedance-seed/seed-2.0-lite-20260309` | 2.74× | 21.41 B | 241 | conversational |
| `qwen/qwen3.5-9b-20260310` | 2.60× | 335.64 B | 241 | conversational |
| `thinkingmachines/inkling-20260715` | 2.50× | 51.47 B | 112 | conversational |
| `qwen/qwen3.5-35b-a3b-20260224` | 2.38× | 107.18 B | 254 | conversational |
| `z-ai/glm-5.1-20260406` | 2.21× | 107.32 B | 213 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `nvidia/nemotron-3.5-content-safety-20260604` | 0.00× | 10.17 B | 155 | conversational |
| `google/gemini-3.1-flash-lite-20260507` | 0.05× | 25.59 B | 183 | conversational |
| `stepfun/step-3.7-flash-20260528` | 0.07× | 930.86 B | 162 | agentic |
| `inclusionai/ling-3.0-flash-vl-20260910` | 0.08× | 65.23 B | 57 | conversational |
| `xiaomi/mimo-v2.5-20260422` | 0.09× | 1.13 T | 198 | agentic |
| `tencent/hy4-preview-20260827` | 0.14× | 34.97 T | 70 | agentic |
| `openai/gpt-6-luna-pro-20260922` | 0.17× | 19.33 B | 45 | conversational |
| `xiaomi/mimo-v2.5-pro-20260422` | 0.18× | 389.16 B | 198 | agentic |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$370.3 M per month** across
474 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 8.0% | 30.6% | 3.84x |
| `openai` | 9.9% | 17.7% | 1.79x |
| `deepseek` | 34.4% | 10.2% | 0.30x |
| `stepfun` | 4.6% | 9.4% | 2.06x |
| `tencent` | 6.7% | 9.0% | 1.33x |
| `google` | 3.7% | 5.8% | 1.56x |
| `moonshotai` | 1.9% | 4.2% | 2.14x |
| `z-ai` | 10.9% | 4.0% | 0.37x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**2,642**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **46.2%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.933** by value. Both are extreme; a
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
**6.59%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 6.78% |
| **conversational** | 1.71% |
| **extractive** | 1.65% |
| **output_heavy** | 1.47% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,226 endpoints serving multi-provider models,
**883 are dominated** (72.0%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `~deepseek/deepseek-flash-latest` | Phala | $1.20 | 69 tok/s | Particle AI | 38 |
| `z-ai/glm-5.3-flash-20260826` | Parasail | $0.62 | 21 tok/s | Relace | 38 |
| `~z-ai/glm-flash-latest` | Parasail | $0.62 | 22 tok/s | Relace | 38 |
| `~z-ai/glm-latest` | BaseTen | $4.40 | 38 tok/s | Baidu | 35 |
| `~z-ai/glm-latest` | Parasail | $6.60 | 50 tok/s | Baidu | 35 |
| `z-ai/glm-5.3-flash-20260826` | Mistral | $0.50 | 28 tok/s | Relace | 35 |
| `~z-ai/glm-flash-latest` | Mistral | $0.50 | 28 tok/s | Relace | 35 |
| `z-ai/glm-5.3-20260816` | BaseTen | $4.40 | 38 tok/s | Baidu | 34 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-09-12` and `2026-11-06`,
**0.00%** of 1 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.60 | -0.81 to -0.39 | 0.354 | 82 | yes |
| **all** | request weighted | -0.26 | -0.63 to +0.12 | 0.022 | 449 | no |
| **conversational** | request weighted | -0.19 | -0.56 to +0.17 | 0.017 | 297 | no |
| **extractive** | request weighted | -0.99 | -1.35 to -0.63 | 0.508 | 23 | yes |
| **output_heavy** | request weighted | -0.08 | -0.40 to +0.25 | 0.011 | 47 | no |
| **agentic** | unweighted | -0.51 | -0.89 to -0.14 | 0.078 | 82 | yes |
| **all** | unweighted | -0.69 | -0.97 to -0.41 | 0.067 | 449 | yes |
| **conversational** | unweighted | -0.74 | -1.06 to -0.42 | 0.089 | 297 | yes |
| **extractive** | unweighted | -0.29 | -1.19 to +0.61 | 0.017 | 23 | no |
| **output_heavy** | unweighted | -1.15 | -1.87 to -0.44 | 0.220 | 47 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.51, interval
-0.89 to -0.14, straddling zero). Weighting by requests, the
elasticity is **-0.60** (-0.81 to -0.39) and
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
| ≥2 days silent | 74 | 402 | 94.0% | 86.0% |
| ≥3 days silent | 71 | 405 | 94.6% | 86.5% |
| ≥7 days silent | 54 | 422 | 97.5% | 90.9% |
| ≥14 days silent | 43 | 433 | 97.5% | 93.9% |

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
