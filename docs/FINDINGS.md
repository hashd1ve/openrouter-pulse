# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-11-11` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 749 model-variants, 816.30 T
tokens and 39.56 B requests over the trailing 30 days.


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
| **agentic** | 103 | 649.44 T | 79.6% | 55.7 | 58,440 | large contexts, terse output, very large interactions |
| **conversational** | 308 | 110.43 T | 13.5% | 10.2 | 4,028 | moderate context per output token, human-sized interactions |
| **extractive** | 42 | 51.77 T | 6.3% | 45.4 | 4,818 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 177 | 4.47 T | 0.5% | — | 37 | insufficient data to classify |
| **output_heavy** | 119 | 180.80 B | 0.0% | 0.4 | 4,430 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **79.6% of all tokens**
while being 103 of 749 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
13.5%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `scaledown/classify-1-20260928` | 2,320.5 | 7,290 | 19.97 B | extractive |
| `upstage/solar-decide-20260928` | 2,240.8 | 5,036 | 16.09 B | extractive |
| `upstage/solar-decide-flash-20261008` | 1,582.3 | 3,302 | 7.65 B | extractive |
| `perplexity/pplx-decider-v1.1-27b-20261006` | 1,307.3 | 3,487 | 185.74 B | extractive |
| `perplexity/pplx-decider-flash-v1.2-20261016` | 991.1 | 2,082 | 92.60 B | extractive |
| `microsoft/microsoft-decision-1-20261009` | 585.8 | 1,795 | 102.03 B | extractive |
| `perplexity/pplx-decider-v1.2-20261016` | 511.9 | 1,875 | 1.02 T | extractive |
| `baseten/joey-1-20261029` | 424.2 | 486 | 15.21 B | extractive |
| `togethercomputer/tev1-4b-experimental-20260923` | 411.3 | 1,928 | 4.80 B | extractive |
| `baseten/mammoth-1-20261021` | 401.0 | 664 | 15.82 B | extractive |

**Why both axes.** The top of this ranking is `scaledown/classify-1-20260928` at
2,320.5 tokens of context per token written, but its interactions
average only 7,290 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `stepfun/step-5-preview-20261008`: 206.6 tokens of context per token
written, in interactions averaging 232,057 tokens, which
is 32× larger.
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
median of **0.97** with a p25–p75 range of 0.75–1.18.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 16 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.18×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `amazon/nova-2-lite-v1` | 7.12× | 12.72 B | 344 | conversational |
| `qwen/qwen3.5-27b-20260224` | 5.17× | 51.39 B | 259 | conversational |
| `google/gemma-3-4b-it` | 4.07× | 15.24 B | 608 | conversational |
| `mistralai/mistral-small-2603` | 3.15× | 34.66 B | 240 | conversational |
| `qwen/qwen3.6-27b-20260422` | 2.69× | 52.51 B | 198 | conversational |
| `x-ai/grok-4.7-20260916` | 2.44× | 1.58 T | 51 | agentic |
| `openai/gpt-6.1-sol-20260929` | 2.35× | 12.53 B | 43 | conversational |
| `rekaai/reka-edge-2603` | 2.31× | 357.49 M | 236 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-oss-20b` | 0.00× | 3.71 B | 463 | conversational |
| `openai/gpt-5-nano-2025-08-07` | 0.00× | 10.31 B | 461 | conversational |
| `anthropic/claude-opus-5-20260723` | 0.03× | 428.54 M | 110 | conversational |
| `openai/gpt-6-luna-pro-20260922` | 0.04× | 17.09 B | 50 | conversational |
| `stepfun/step-3.7-flash-20260528` | 0.05× | 870.84 B | 167 | agentic |
| `tencent/hy4-preview-20260827` | 0.05× | 29.19 T | 75 | agentic |
| `google/gemini-3.6-flash-20260721` | 0.05× | 6.67 B | 113 | conversational |
| `z-ai/glm-5.3-flash-20260826` | 0.06× | 34.77 B | 77 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$402.0 M per month** across
481 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 7.8% | 46.3% | 5.93x |
| `openai` | 9.6% | 10.9% | 1.13x |
| `tencent` | 7.6% | 8.6% | 1.12x |
| `stepfun` | 3.9% | 7.6% | 1.94x |
| `moonshotai` | 2.2% | 5.5% | 2.47x |
| `google` | 3.5% | 4.9% | 1.39x |
| `deepseek` | 35.7% | 4.5% | 0.13x |
| `z-ai` | 10.4% | 3.8% | 0.37x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,375**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **55.7%** of
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
**6.88%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 6.98% |
| **conversational** | 1.74% |
| **extractive** | 1.58% |
| **output_heavy** | 1.52% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,222 endpoints serving multi-provider models,
**867 are dominated** (70.9%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-flash-20260826` | Parasail | $0.62 | 25 tok/s | Relace | 40 |
| `~z-ai/glm-flash-latest` | Parasail | $0.62 | 25 tok/s | Relace | 40 |
| `z-ai/glm-5.3-flash-20260826` | Parasail | $0.50 | 17 tok/s | Relace | 38 |
| `~z-ai/glm-flash-latest` | Parasail | $0.50 | 16 tok/s | Relace | 38 |
| `z-ai/glm-5.3-flash-20260826` | Near AI | $0.50 | 30 tok/s | Morph | 36 |
| `~z-ai/glm-flash-latest` | Near AI | $0.50 | 29 tok/s | Morph | 36 |
| `~z-ai/glm-flash-latest` | Z.AI | $0.50 | 34 tok/s | Morph | 34 |
| `z-ai/glm-5.3-flash-20260826` | Z.AI | $0.50 | 34 tok/s | Morph | 33 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-11-09` and `2026-11-11`,
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
| **agentic** | request weighted | -0.52 | -0.78 to -0.27 | 0.381 | 87 | yes |
| **all** | request weighted | -0.46 | -0.83 to -0.09 | 0.085 | 447 | yes |
| **conversational** | request weighted | -0.32 | -0.76 to +0.11 | 0.050 | 283 | no |
| **extractive** | request weighted | -1.29 | -1.68 to -0.90 | 0.571 | 24 | yes |
| **output_heavy** | request weighted | -0.11 | -0.40 to +0.18 | 0.014 | 53 | no |
| **agentic** | unweighted | -0.44 | -0.83 to -0.05 | 0.055 | 87 | yes |
| **all** | unweighted | -0.47 | -0.70 to -0.24 | 0.032 | 447 | yes |
| **conversational** | unweighted | -0.58 | -0.80 to -0.35 | 0.072 | 283 | yes |
| **extractive** | unweighted | +0.11 | -0.95 to +1.17 | 0.001 | 24 | no |
| **output_heavy** | unweighted | -0.06 | -0.63 to +0.52 | 0.000 | 53 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.44, interval
-0.83 to -0.05, straddling zero). Weighting by requests, the
elasticity is **-0.52** (-0.78 to -0.27) and
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
| ≥2 days silent | 69 | 412 | 93.6% | 85.9% |
| ≥3 days silent | 66 | 415 | 94.1% | 86.3% |
| ≥7 days silent | 52 | 430 | 95.6% | 89.5% |
| ≥14 days silent | 32 | 450 | 98.4% | 94.9% |

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
