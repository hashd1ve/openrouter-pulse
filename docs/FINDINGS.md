# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-09-07` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 617 model-variants, 414.92 T
tokens and 20.43 B requests over the trailing 30 days.


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
| **agentic** | 74 | 320.09 T | 77.1% | 56.0 | 50,903 | large contexts, terse output, very large interactions |
| **conversational** | 300 | 91.63 T | 22.1% | 9.9 | 3,933 | moderate context per output token, human-sized interactions |
| **unclassified** | 123 | 2.00 T | 0.5% | — | 31 | insufficient data to classify |
| **extractive** | 27 | 1.06 T | 0.3% | 35.2 | 8,583 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 93 | 126.59 B | 0.0% | 0.5 | 4,396 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **77.1% of all tokens**
while being 74 of 617 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
22.1%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 366.6 | 1,282 | 16.51 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 180.2 | 113,189 | 16.54 T | agentic |
| `xiaomi/mimo-v2.5-20260422` | 137.3 | 70,465 | 26.48 T | agentic |
| `thinkingmachines/inkling-20260715` | 136.7 | 70,711 | 448.95 B | agentic |
| `poolside/laguna-s-2.1-20260720` | 132.7 | 86,492 | 6.42 T | agentic |
| `openai/gpt-6-astra-20260903` | 117.7 | 75,043 | 137.89 B | agentic |
| `thinkingmachines/inkling-small-20260730` | 117.6 | 54,293 | 176.03 B | agentic |
| `minimax/minimax-m3-20260531` | 117.6 | 76,546 | 7.59 T | agentic |
| `poolside/laguna-xs-2.1-20260625` | 110.4 | 52,503 | 549.71 B | agentic |
| `tencent/hy4-preview-20260827` | 109.8 | 117,347 | 17.74 T | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
366.6 tokens of context per token written, but its interactions
average only 1,282 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 180.2 tokens of context per token
written, in interactions averaging 113,189 tokens, which
is 88× larger.
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


Across 229 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.77** with a p25–p75 range of 0.52–1.02.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 22 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.25×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `minimax/minimax-m2.7-20260318` | 5.34× | 890.40 B | 173 | agentic |
| `qwen/qwen3.5-35b-a3b-20260224` | 4.18× | 92.61 B | 194 | conversational |
| `tencent/hy-mt2-30b-a3b-20260521` | 3.91× | 758.32 M | 18 | conversational |
| `thinkingmachines/inkling-20260715` | 3.15× | 448.95 B | 52 | agentic |
| `openai/gpt-5-nano-2025-08-07` | 2.75× | 298.83 B | 396 | conversational |
| `thinkingmachines/inkling-small-20260730` | 2.70× | 176.03 B | 39 | agentic |
| `openai/gpt-5.6-luna-20260709` | 2.62× | 21.30 B | 60 | conversational |
| `amazon/nova-2-lite-v1` | 2.59× | 4.12 B | 279 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-3.2-1b-instruct` | 0.03× | 2.85 B | 712 | output_heavy |
| `z-ai/glm-5v-turbo-20260401` | 0.05× | 84.69 B | 159 | agentic |
| `google/gemini-3.7-flash-20260813` | 0.11× | 34.45 B | 25 | conversational |
| `google/gemma-4-26b-a4b-it-20260403` | 0.12× | 30.93 B | 157 | conversational |
| `google/gemini-3.6-flash-20260721` | 0.12× | 4.07 T | 48 | agentic |
| `bytedance-seed/seed-2.0-lite-20260309` | 0.12× | 6.68 B | 181 | conversational |
| `xiaomi/mimo-v2.5-20260422` | 0.14× | 26.48 T | 138 | agentic |
| `thinkingmachines/inkling-small-20260730` | 0.16× | 38.89 B | 39 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$240.8 M per month** across
449 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 5.5% | 28.6% | 5.16x |
| `openai` | 12.7% | 14.9% | 1.17x |
| `z-ai` | 9.3% | 10.3% | 1.11x |
| `deepseek` | 21.1% | 9.4% | 0.44x |
| `moonshotai` | 1.9% | 9.3% | 4.80x |
| `tencent` | 12.0% | 8.1% | 0.67x |
| `google` | 7.4% | 5.5% | 0.74x |
| `nvidia` | 5.5% | 4.6% | 0.84x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,065**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **52.8%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.942** by value. Both are extreme; a
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
**8.63%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.56% |
| **extractive** | 4.50% |
| **output_heavy** | 1.79% |
| **conversational** | 1.78% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 929 endpoints serving multi-provider models,
**618 are dominated** (66.5%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.2-20260616` | Alibaba | $7.26 | 31 tok/s | DeepInfra | 25 |
| `z-ai/glm-5.3-flash-20260826` | Io Net | $0.50 | 10 tok/s | Relace | 22 |
| `~z-ai/glm-flash-latest` | Io Net | $0.50 | 10 tok/s | Relace | 22 |
| `z-ai/glm-5.3-flash-20260826` | DigitalOcean | $0.50 | 13 tok/s | Relace | 21 |
| `~z-ai/glm-flash-latest` | DigitalOcean | $0.50 | 13 tok/s | Relace | 21 |
| `z-ai/glm-5.2-20260616` | Z.AI | $4.40 | 42 tok/s | StreamLake | 21 |
| `z-ai/glm-5.3-20260816` | Sail Research | $4.40 | 21 tok/s | Decart | 21 |
| `~z-ai/glm-latest` | Sail Research | $4.40 | 21 tok/s | Decart | 21 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-09-06` and `2026-09-07`,
**1.62%** of 494 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.54 | -0.78 to -0.29 | 0.329 | 65 | yes |
| **all** | request weighted | -0.12 | -0.54 to +0.31 | 0.005 | 418 | no |
| **conversational** | request weighted | -0.25 | -0.85 to +0.35 | 0.025 | 281 | no |
| **extractive** | request weighted | +0.67 | +0.33 to +1.01 | 0.323 | 23 | yes |
| **output_heavy** | request weighted | -0.04 | -0.27 to +0.19 | 0.002 | 49 | no |
| **agentic** | unweighted | -0.32 | -0.64 to +0.01 | 0.046 | 65 | no |
| **all** | unweighted | -0.69 | -0.95 to -0.43 | 0.079 | 418 | yes |
| **conversational** | unweighted | -0.99 | -1.28 to -0.71 | 0.177 | 281 | yes |
| **extractive** | unweighted | -0.14 | -0.54 to +0.26 | 0.014 | 23 | no |
| **output_heavy** | unweighted | -0.16 | -0.91 to +0.59 | 0.006 | 49 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.32, interval
-0.64 to +0.01, straddling zero). Weighting by requests, the
elasticity is **-0.54** (-0.78 to -0.29) and
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
| ≥2 days silent | 75 | 377 | 91.2% | 82.4% |
| ≥3 days silent | 71 | 381 | 92.1% | 83.2% |
| ≥7 days silent | 55 | 397 | 94.1% | 87.4% |
| ≥14 days silent | 17 | 435 | 98.0% | 94.8% |

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
