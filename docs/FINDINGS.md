# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-09-10` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 626 model-variants, 442.61 T
tokens and 21.37 B requests over the trailing 30 days.


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
| **agentic** | 78 | 341.49 T | 77.2% | 53.8 | 51,671 | large contexts, terse output, very large interactions |
| **conversational** | 302 | 97.84 T | 22.1% | 10.1 | 3,901 | moderate context per output token, human-sized interactions |
| **unclassified** | 124 | 2.13 T | 0.5% | — | 36 | insufficient data to classify |
| **extractive** | 23 | 1.03 T | 0.2% | 36.1 | 8,685 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 99 | 129.08 B | 0.0% | 0.5 | 4,386 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **77.2% of all tokens**
while being 78 of 626 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
22.1%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 348.6 | 1,197 | 14.22 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 185.8 | 115,946 | 17.11 T | agentic |
| `thinkingmachines/inkling-20260715` | 145.6 | 73,052 | 625.55 B | agentic |
| `xiaomi/mimo-v2.5-20260422` | 138.2 | 71,264 | 27.94 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 129.5 | 85,347 | 6.18 T | agentic |
| `minimax/minimax-m3-20260531` | 119.2 | 76,887 | 8.17 T | agentic |
| `thinkingmachines/inkling-small-20260730` | 116.2 | 55,181 | 233.39 B | agentic |
| `tencent/hy4-preview-20260827` | 110.4 | 116,967 | 27.72 T | agentic |
| `openai/gpt-6-astra-20260903` | 110.4 | 66,997 | 471.24 B | agentic |
| `poolside/laguna-xs-2.1-20260625` | 108.6 | 51,872 | 517.62 B | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
348.6 tokens of context per token written, but its interactions
average only 1,197 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 185.8 tokens of context per token
written, in interactions averaging 115,946 tokens, which
is 97× larger.
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


Across 232 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **1.04** with a p25–p75 range of 0.80–1.34.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 22 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.46×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `ibm-granite/granite-4.0-h-micro` | 14.63× | 10.32 B | 325 | conversational |
| `tencent/hy-mt2-1.8b-20260521` | 10.52× | 425.05 M | 21 | conversational |
| `tencent/hy-mt2-7b-20260521` | 5.26× | 306.55 M | 22 | conversational |
| `dots-studio/dots-3-note-preview-20260813` | 3.22× | 711.12 B | 27 | agentic |
| `thinkingmachines/inkling-20260715` | 2.81× | 625.55 B | 55 | agentic |
| `z-ai/glm-4.5-air` | 2.78× | 18.53 B | 412 | conversational |
| `tencent/hy-mt2-30b-a3b-20260521` | 2.75× | 1.20 B | 21 | conversational |
| `qwen/qwen3.5-35b-a3b-20260224` | 2.65× | 113.21 B | 197 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-3.2-1b-instruct` | 0.04× | 2.49 B | 715 | output_heavy |
| `meta/muse-spark-1.1-20260709` | 0.14× | 94.61 B | 56 | agentic |
| `openai/gpt-4o-2024-05-13` | 0.14× | 863.72 M | 850 | extractive |
| `google/gemini-3.6-flash-20260721` | 0.16× | 3.93 T | 51 | agentic |
| `google/gemini-3.7-flash-20260813` | 0.21× | 37.07 B | 28 | conversational |
| `stepfun/step-3.7-flash-20260528` | 0.23× | 2.33 T | 105 | agentic |
| `google/gemma-4-26b-a4b-it-20260403` | 0.25× | 24.29 B | 160 | conversational |
| `z-ai/glm-5v-turbo-20260401` | 0.25× | 78.18 B | 162 | agentic |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$247.5 M per month** across
454 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 5.3% | 24.2% | 4.54x |
| `openai` | 13.1% | 14.8% | 1.14x |
| `tencent` | 12.8% | 11.1% | 0.87x |
| `z-ai` | 10.2% | 11.0% | 1.08x |
| `moonshotai` | 1.9% | 9.3% | 4.99x |
| `google` | 7.3% | 8.3% | 1.13x |
| `deepseek` | 20.0% | 6.8% | 0.34x |
| `nvidia` | 5.3% | 4.7% | 0.88x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**2,392**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **44.4%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.937** by value. Both are extreme; a
national income distribution above 0.6 is considered severe.


### The sticker price is not the price

Traffic is overwhelmingly prompt-heavy, and prompt tokens cost less than
completions. Blended across each model's real token mix, the price actually paid
per token is a median **0.36x** the headline output price, so the
sticker overstates unit cost by about **2.8x**.

Anyone comparing models on `$/M output` is getting this wrong.


## 5. The context window arms race is mostly unused

Dividing mean tokens per request by the advertised context length asks how much
of the window the traffic actually touches. Token-weighted across the market:
**8.15%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.90% |
| **extractive** | 4.19% |
| **conversational** | 1.80% |
| **output_heavy** | 1.54% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 937 endpoints serving multi-provider models,
**588 are dominated** (62.8%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `~z-ai/glm-latest` | Phala | $4.40 | 25 tok/s | StreamLake | 23 |
| `z-ai/glm-5.3-20260816` | Phala | $4.40 | 25 tok/s | StreamLake | 21 |
| `z-ai/glm-5.3-flash-20260826` | DigitalOcean | $0.50 | 21 tok/s | Relace | 20 |
| `~z-ai/glm-flash-latest` | DigitalOcean | $0.50 | 21 tok/s | Relace | 20 |
| `z-ai/glm-5.2-20260616` | Z.AI | $4.40 | 25 tok/s | DeepInfra | 20 |
| `~z-ai/glm-latest` | SiliconFlow | $4.40 | 30 tok/s | StreamLake | 20 |
| `~z-ai/glm-latest` | Z.AI | $4.40 | 30 tok/s | StreamLake | 20 |
| `z-ai/glm-5.3-20260816` | SiliconFlow | $4.40 | 30 tok/s | StreamLake | 19 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-09-09` and `2026-09-10`,
**1.80%** of 499 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.48 | -0.67 to -0.28 | 0.309 | 66 | yes |
| **all** | request weighted | -0.15 | -0.59 to +0.30 | 0.009 | 421 | no |
| **conversational** | request weighted | -0.24 | -0.81 to +0.32 | 0.023 | 283 | no |
| **extractive** | request weighted | +0.64 | +0.27 to +1.00 | 0.281 | 19 | yes |
| **output_heavy** | request weighted | -0.06 | -0.34 to +0.21 | 0.005 | 53 | no |
| **agentic** | unweighted | -0.33 | -0.65 to -0.01 | 0.047 | 66 | yes |
| **all** | unweighted | -0.65 | -0.92 to -0.39 | 0.068 | 421 | yes |
| **conversational** | unweighted | -0.90 | -1.20 to -0.60 | 0.148 | 283 | yes |
| **extractive** | unweighted | -0.19 | -0.62 to +0.25 | 0.023 | 19 | no |
| **output_heavy** | unweighted | +0.02 | -0.77 to +0.80 | 0.000 | 53 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.33, interval
-0.65 to -0.01, straddling zero). Weighting by requests, the
elasticity is **-0.48** (-0.67 to -0.28) and
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
| ≥2 days silent | 75 | 383 | 90.4% | 82.2% |
| ≥3 days silent | 68 | 390 | 91.9% | 83.6% |
| ≥7 days silent | 61 | 397 | 93.6% | 85.1% |
| ≥14 days silent | 40 | 418 | 96.6% | 91.1% |

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
