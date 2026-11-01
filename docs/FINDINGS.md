# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-11-01` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 736 model-variants, 763.76 T
tokens and 37.46 B requests over the trailing 30 days.


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
| **agentic** | 94 | 544.07 T | 71.2% | 57.7 | 55,689 | large contexts, terse output, very large interactions |
| **conversational** | 319 | 167.61 T | 21.9% | 9.4 | 3,874 | moderate context per output token, human-sized interactions |
| **extractive** | 40 | 47.96 T | 6.3% | 48.5 | 4,763 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 172 | 3.91 T | 0.5% | — | 34 | insufficient data to classify |
| **output_heavy** | 111 | 207.33 B | 0.0% | 0.3 | 4,242 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **71.2% of all tokens**
while being 94 of 736 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
21.9%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `upstage/solar-decide-20260928` | 2,137.3 | 4,676 | 20.28 B | extractive |
| `scaledown/classify-1-20260928` | 2,117.7 | 6,991 | 14.15 B | extractive |
| `upstage/solar-decide-flash-20261008` | 1,479.4 | 3,461 | 9.88 B | extractive |
| `perplexity/pplx-decider-flash-v1.2-20261016` | 1,196.2 | 3,272 | 63.64 B | extractive |
| `perplexity/pplx-decider-v1-27b-20261001` | 1,155.6 | 4,655 | 9.10 B | extractive |
| `perplexity/pplx-decider-v1.1-27b-20261006` | 1,141.1 | 3,834 | 257.20 B | extractive |
| `perplexity/pplx-decider-v1.2-20261016` | 499.3 | 2,055 | 460.63 B | extractive |
| `togethercomputer/tev1-4b-experimental-20260923` | 474.2 | 2,308 | 7.60 B | extractive |
| `microsoft/microsoft-decision-1-20261009` | 470.2 | 1,396 | 66.11 B | extractive |
| `baseten/joey-1-20261029` | 464.4 | 664 | 2.21 B | extractive |

**Why both axes.** The top of this ranking is `upstage/solar-decide-20260928` at
2,137.3 tokens of context per token written, but its interactions
average only 4,676 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `stepfun/step-5-preview-20261008`: 191.5 tokens of context per token
written, in interactions averaging 209,385 tokens, which
is 45× larger.
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


Across 260 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.70** with a p25–p75 range of 0.49–0.91.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 19 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.67×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `z-ai/glm-5.3-flash-20260826` | 6.49× | 32.33 B | 67 | conversational |
| `mistralai/mistral-medium-3.1` | 5.30× | 28.86 B | 445 | conversational |
| `google/gemma-3-4b-it` | 3.94× | 8.23 B | 598 | conversational |
| `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning-20260428` | 3.47× | 175.62 B | 187 | conversational |
| `openai/gpt-5.6-luna-20260709` | 3.39× | 9.76 T | 115 | extractive |
| `stepfun/step-3.7-flash-20260528` | 2.74× | 815.15 B | 157 | agentic |
| `qwen/qwen3.5-9b-20260310` | 2.10× | 265.44 B | 236 | conversational |
| `openai/gpt-oss-120b` | 2.05× | 2.45 B | 453 | output_heavy |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `recursive/flint-v1.0-20261021` | 0.00× | 242.98 B | 11 | agentic |
| `openai/gpt-5-nano-2025-08-07` | 0.01× | 10.35 B | 451 | conversational |
| `google/gemini-3.6-flash-20260721` | 0.06× | 11.39 B | 103 | conversational |
| `xiaomi/mimo-v2.5-20260422` | 0.07× | 1.76 T | 193 | agentic |
| `inclusionai/ling-3.0-flash-vl-20260910` | 0.08× | 95.67 B | 52 | conversational |
| `xiaomi/mimo-v2.5-pro-20260422` | 0.09× | 501.52 B | 193 | agentic |
| `nex-agi/nex-n2.5-mini-20260908` | 0.09× | 31.92 B | 54 | conversational |
| `openai/gpt-6-sol-20260922` | 0.11× | 4.97 B | 40 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$405.8 M per month** across
477 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 7.6% | 43.2% | 5.66x |
| `openai` | 9.9% | 15.2% | 1.53x |
| `tencent` | 6.4% | 7.9% | 1.23x |
| `stepfun` | 4.1% | 7.4% | 1.80x |
| `deepseek` | 31.8% | 7.0% | 0.22x |
| `google` | 3.8% | 5.4% | 1.42x |
| `z-ai` | 10.9% | 3.3% | 0.30x |
| `xiaomi` | 5.8% | 2.5% | 0.44x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,342**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **54.7%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.946** by value. Both are extreme; a
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
**6.58%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 6.60% |
| **extractive** | 1.87% |
| **conversational** | 1.74% |
| **output_heavy** | 0.70% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,121 endpoints serving multi-provider models,
**777 are dominated** (69.3%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `deepseek/deepseek-v4.1-flash-20261017` | Near AI | $1.20 | 40 tok/s | Sail Research | 37 |
| `~deepseek/deepseek-flash-latest` | Near AI | $1.20 | 40 tok/s | Sail Research | 37 |
| `z-ai/glm-5.3-flash-20260826` | Sail Research | $0.75 | 34 tok/s | Relace | 33 |
| `~z-ai/glm-flash-latest` | Sail Research | $0.75 | 34 tok/s | Relace | 33 |
| `~z-ai/glm-flash-latest` | Near AI | $0.50 | 28 tok/s | Relace | 33 |
| `z-ai/glm-5.3-flash-20260826` | PrimeIntellect | $0.50 | 21 tok/s | Relace | 33 |
| `z-ai/glm-5.3-flash-20260826` | Near AI | $0.50 | 24 tok/s | Relace | 32 |
| `~z-ai/glm-flash-latest` | PrimeIntellect | $0.50 | 32 tok/s | Relace | 32 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-10-31` and `2026-11-01`,
**0.89%** of 563 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.73 | -1.10 to -0.36 | 0.382 | 79 | yes |
| **all** | request weighted | -0.26 | -0.63 to +0.10 | 0.029 | 450 | no |
| **conversational** | request weighted | -0.61 | -1.23 to +0.01 | 0.143 | 299 | no |
| **extractive** | request weighted | -1.04 | -1.36 to -0.73 | 0.551 | 21 | yes |
| **output_heavy** | request weighted | -0.24 | -0.64 to +0.16 | 0.110 | 51 | no |
| **agentic** | unweighted | -0.46 | -0.84 to -0.08 | 0.060 | 79 | yes |
| **all** | unweighted | -0.75 | -1.04 to -0.46 | 0.064 | 450 | yes |
| **conversational** | unweighted | -0.64 | -0.90 to -0.38 | 0.062 | 299 | yes |
| **extractive** | unweighted | -0.48 | -1.36 to +0.40 | 0.047 | 21 | no |
| **output_heavy** | unweighted | -1.48 | -2.20 to -0.77 | 0.193 | 51 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.46, interval
-0.84 to -0.08, straddling zero). Weighting by requests, the
elasticity is **-0.73** (-1.10 to -0.36) and
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
| ≥2 days silent | 71 | 407 | 96.0% | 88.7% |
| ≥3 days silent | 67 | 411 | 96.5% | 89.5% |
| ≥7 days silent | 54 | 424 | 97.1% | 92.6% |
| ≥14 days silent | 36 | 442 | 97.3% | 93.8% |

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
