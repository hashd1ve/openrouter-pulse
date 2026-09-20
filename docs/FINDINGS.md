# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-09-20` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 636 model-variants, 509.90 T
tokens and 23.35 B requests over the trailing 30 days.


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
| **agentic** | 91 | 435.45 T | 85.4% | 53.2 | 49,088 | large contexts, terse output, very large interactions |
| **conversational** | 313 | 71.41 T | 14.0% | 9.6 | 3,842 | moderate context per output token, human-sized interactions |
| **unclassified** | 120 | 2.34 T | 0.5% | — | 31 | insufficient data to classify |
| **extractive** | 20 | 556.06 B | 0.1% | 37.7 | 8,300 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 92 | 145.96 B | 0.0% | 0.6 | 4,447 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **85.4% of all tokens**
while being 91 of 636 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
14.0%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 255.2 | 867 | 9.11 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 203.5 | 126,074 | 18.49 T | agentic |
| `xiaomi/mimo-v2.5-20260422` | 132.3 | 71,593 | 29.95 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 122.0 | 82,836 | 5.46 T | agentic |
| `minimax/minimax-m3-20260531` | 119.2 | 76,887 | 8.17 T | agentic |
| `thinkingmachines/inkling-small-20260730` | 116.8 | 55,983 | 411.91 B | agentic |
| `tencent/hy4-preview-20260827` | 111.9 | 116,837 | 45.10 T | agentic |
| `deepseek/deepseek-v4-flash-20260731` | 111.6 | 102,637 | 1.08 T | agentic |
| `openai/gpt-6-astra-20260903` | 111.1 | 73,451 | 2.50 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 105.3 | 92,829 | 246.69 B | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
255.2 tokens of context per token written, but its interactions
average only 867 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 203.5 tokens of context per token
written, in interactions averaging 126,074 tokens, which
is 145× larger.
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


Across 238 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.76** with a p25–p75 range of 0.55–0.96.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 19 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.67×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `deepseek/deepseek-v4-flash-20260731` | 9.44× | 1.08 T | 51 | agentic |
| `google/gemini-3.1-flash-lite-20260507` | 6.69× | 4.20 B | 136 | conversational |
| `mistralai/voxtral-small-24b-2507` | 4.74× | 1.97 B | 325 | conversational |
| `tencent/hy-mt2-7b-20260521` | 3.91× | 2.06 B | 32 | conversational |
| `tencent/hy-mt2-1.8b-20260521` | 3.67× | 2.50 B | 31 | conversational |
| `thinkingmachines/inkling-small-20260730` | 3.25× | 34.61 B | 52 | conversational |
| `tencent/hy-mt2-30b-a3b-20260521` | 3.10× | 4.66 B | 31 | conversational |
| `openai/gpt-5.6-sol-20260709` | 3.09× | 5.42 B | 73 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `meta/muse-spark-1.1-20260709` | 0.06× | 63.48 B | 66 | agentic |
| `stepfun/step-3.7-flash-20260528` | 0.08× | 1.19 T | 115 | agentic |
| `meta/muse-spark-1.2-20260805` | 0.17× | 210.90 B | 46 | conversational |
| `z-ai/glm-5v-turbo-20260401` | 0.20× | 40.07 B | 172 | agentic |
| `meta/muse-spark-1.2-contributor-20260805` | 0.21× | 581.04 B | 30 | conversational |
| `bytedance-seed/seed-2.0-mini-20260224` | 0.21× | 42.71 B | 206 | conversational |
| `mistralai/mistral-small-2603` | 0.21× | 86.70 B | 188 | conversational |
| `meta-llama/llama-3.1-8b-instruct` | 0.22× | 340.79 B | 789 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$208.8 M per month** across
464 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 4.2% | 23.7% | 5.67x |
| `tencent` | 13.1% | 19.7% | 1.51x |
| `openai` | 14.3% | 18.5% | 1.29x |
| `deepseek` | 20.4% | 7.8% | 0.38x |
| `moonshotai` | 1.6% | 6.6% | 4.06x |
| `z-ai` | 12.3% | 6.3% | 0.51x |
| `google` | 6.2% | 5.8% | 0.93x |
| `x-ai` | 0.5% | 2.5% | 4.93x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,568**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **57.5%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.934** by value. Both are extreme; a
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
**8.78%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.57% |
| **extractive** | 4.63% |
| **conversational** | 1.71% |
| **output_heavy** | 1.51% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 970 endpoints serving multi-provider models,
**667 are dominated** (68.8%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-flash-20260826` | Phala | $0.50 | 3 tok/s | GMICloud | 27 |
| `~z-ai/glm-flash-latest` | Phala | $0.50 | 2 tok/s | GMICloud | 27 |
| `z-ai/glm-5.3-flash-20260826` | NextBit | $0.60 | 5 tok/s | GMICloud | 26 |
| `~z-ai/glm-flash-latest` | NextBit | $0.60 | 5 tok/s | GMICloud | 26 |
| `z-ai/glm-5.3-flash-20260826` | Near AI | $0.50 | 4 tok/s | GMICloud | 26 |
| `~z-ai/glm-flash-latest` | Near AI | $0.50 | 4 tok/s | GMICloud | 26 |
| `~z-ai/glm-flash-latest` | Reka | $0.50 | 7 tok/s | GMICloud | 25 |
| `z-ai/glm-5.3-flash-20260826` | Reka | $0.50 | 7 tok/s | GMICloud | 24 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-09-19` and `2026-09-20`,
**2.13%** of 516 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.63 | -0.84 to -0.42 | 0.336 | 75 | yes |
| **all** | request weighted | -0.21 | -0.58 to +0.16 | 0.014 | 427 | no |
| **conversational** | request weighted | -0.46 | -1.13 to +0.21 | 0.092 | 287 | no |
| **extractive** | request weighted | +0.57 | +0.13 to +1.00 | 0.263 | 17 | yes |
| **output_heavy** | request weighted | -0.21 | -0.54 to +0.11 | 0.075 | 48 | no |
| **agentic** | unweighted | -0.62 | -0.97 to -0.28 | 0.112 | 75 | yes |
| **all** | unweighted | -0.77 | -1.03 to -0.51 | 0.096 | 427 | yes |
| **conversational** | unweighted | -0.98 | -1.28 to -0.69 | 0.171 | 287 | yes |
| **extractive** | unweighted | -0.05 | -0.39 to +0.28 | 0.002 | 17 | no |
| **output_heavy** | unweighted | -0.50 | -1.19 to +0.20 | 0.050 | 48 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.62, interval
-0.97 to -0.28, straddling zero). Weighting by requests, the
elasticity is **-0.63** (-0.84 to -0.42) and
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
| ≥2 days silent | 79 | 386 | 90.3% | 81.3% |
| ≥3 days silent | 71 | 394 | 91.3% | 83.9% |
| ≥7 days silent | 57 | 408 | 93.1% | 86.0% |
| ≥14 days silent | 49 | 416 | 94.8% | 87.5% |

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
