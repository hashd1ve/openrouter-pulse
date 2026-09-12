# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-09-12` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 631 model-variants, 457.38 T
tokens and 21.85 B requests over the trailing 30 days.


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
| **agentic** | 81 | 380.66 T | 83.2% | 52.0 | 50,711 | large contexts, terse output, very large interactions |
| **conversational** | 311 | 73.41 T | 16.1% | 10.0 | 3,887 | moderate context per output token, human-sized interactions |
| **unclassified** | 124 | 2.20 T | 0.5% | — | 28 | insufficient data to classify |
| **extractive** | 22 | 972.73 B | 0.2% | 38.6 | 8,909 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 93 | 126.17 B | 0.0% | 0.4 | 4,424 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **83.2% of all tokens**
while being 81 of 631 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
16.1%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 326.8 | 1,112 | 12.44 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 188.7 | 118,080 | 17.61 T | agentic |
| `xiaomi/mimo-v2.5-20260422` | 137.6 | 71,788 | 29.21 T | agentic |
| `thinkingmachines/inkling-20260715` | 137.2 | 73,401 | 726.89 B | agentic |
| `poolside/laguna-s-2.1-20260720` | 128.0 | 84,788 | 6.07 T | agentic |
| `minimax/minimax-m3-20260531` | 119.2 | 76,887 | 8.17 T | agentic |
| `thinkingmachines/inkling-small-20260730` | 116.8 | 55,121 | 269.93 B | agentic |
| `tencent/hy4-preview-20260827` | 110.3 | 117,260 | 31.68 T | agentic |
| `poolside/laguna-xs-2.1-20260625` | 107.9 | 51,305 | 498.22 B | agentic |
| `openai/gpt-6-astra-20260903` | 100.2 | 64,013 | 715.94 B | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
326.8 tokens of context per token written, but its interactions
average only 1,112 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 188.7 tokens of context per token
written, in interactions averaging 118,080 tokens, which
is 106× larger.
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


Across 234 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.93** with a p25–p75 range of 0.77–1.17.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 20 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.82×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `tencent/hy-mt2-7b-20260521` | 7.93× | 863.32 M | 24 | conversational |
| `tencent/hy-mt2-1.8b-20260521` | 6.84× | 1.05 B | 23 | conversational |
| `tencent/hy-mt2-30b-a3b-20260521` | 5.49× | 2.28 B | 23 | conversational |
| `openai/gpt-3.5-turbo` | 5.48× | 2.62 B | 1,203 | conversational |
| `anthropic/claude-4.5-sonnet-20250929` | 3.72× | 368.06 B | 348 | conversational |
| `meta-llama/llama-4-scout-17b-16e-instruct` | 3.04× | 103.24 B | 525 | conversational |
| `openai/gpt-4o-mini-2024-07-18` | 3.03× | 34.06 B | 786 | conversational |
| `z-ai/glm-4.6-20251208` | 2.89× | 7.17 B | 278 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `stepfun/step-3.7-flash-20260528` | 0.03× | 2.04 T | 107 | agentic |
| `z-ai/glm-5v-turbo-20260401` | 0.08× | 70.59 B | 164 | agentic |
| `meta-llama/llama-3.2-1b-instruct` | 0.12× | 2.22 B | 717 | output_heavy |
| `bytedance-seed/seed-2.0-mini-20260224` | 0.13× | 44.62 B | 198 | conversational |
| `google/gemini-3.6-flash-20260721` | 0.21× | 3.42 T | 53 | agentic |
| `openai/gpt-4o-2024-05-13` | 0.22× | 784.71 M | 852 | extractive |
| `google/gemma-3-4b-it` | 0.22× | 8.81 B | 548 | conversational |
| `meta/muse-spark-1.2-contributor-20260805` | 0.23× | 560.28 B | 22 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$232.8 M per month** across
459 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 5.1% | 28.6% | 5.59x |
| `openai` | 13.3% | 15.8% | 1.18x |
| `tencent` | 12.9% | 13.1% | 1.02x |
| `moonshotai` | 1.8% | 9.8% | 5.48x |
| `z-ai` | 10.6% | 9.6% | 0.90x |
| `google` | 7.1% | 6.5% | 0.91x |
| `deepseek` | 19.9% | 5.8% | 0.29x |
| `x-ai` | 0.6% | 2.6% | 3.99x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,177**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **53.4%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.943** by value. Both are extreme; a
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
**7.07%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.61% |
| **extractive** | 4.54% |
| **conversational** | 1.73% |
| **output_heavy** | 1.58% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 943 endpoints serving multi-provider models,
**624 are dominated** (66.2%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-flash-20260826` | Sail Research | $0.50 | 10 tok/s | DeepInfra | 24 |
| `~z-ai/glm-flash-latest` | Sail Research | $0.50 | 10 tok/s | DeepInfra | 24 |
| `z-ai/glm-5.3-flash-20260826` | Near AI | $0.50 | 13 tok/s | DeepInfra | 23 |
| `~z-ai/glm-flash-latest` | Near AI | $0.50 | 15 tok/s | DeepInfra | 23 |
| `z-ai/glm-5.3-flash-20260826` | DigitalOcean | $0.50 | 16 tok/s | DeepInfra | 22 |
| `deepseek/deepseek-v4-flash-20260731` | Phala | $1.32 | 35 tok/s | Relace | 22 |
| `~deepseek/deepseek-v4-flash-latest` | Phala | $1.32 | 35 tok/s | Relace | 22 |
| `~z-ai/glm-flash-latest` | Venice | $0.50 | 17 tok/s | DeepInfra | 22 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-09-11` and `2026-09-12`,
**1.39%** of 505 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.52 | -0.61 to -0.44 | 0.482 | 65 | yes |
| **all** | request weighted | -0.37 | -0.82 to +0.08 | 0.055 | 419 | no |
| **conversational** | request weighted | -0.33 | -1.06 to +0.39 | 0.042 | 288 | no |
| **extractive** | request weighted | +0.68 | +0.39 to +0.96 | 0.343 | 19 | yes |
| **output_heavy** | request weighted | -0.06 | -0.34 to +0.23 | 0.005 | 47 | no |
| **agentic** | unweighted | -0.50 | -0.83 to -0.18 | 0.109 | 65 | yes |
| **all** | unweighted | -0.69 | -0.95 to -0.42 | 0.079 | 419 | yes |
| **conversational** | unweighted | -0.99 | -1.27 to -0.71 | 0.182 | 288 | yes |
| **extractive** | unweighted | -0.08 | -0.47 to +0.30 | 0.005 | 19 | no |
| **output_heavy** | unweighted | -0.04 | -0.86 to +0.79 | 0.000 | 47 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.50, interval
-0.83 to -0.18, straddling zero). Weighting by requests, the
elasticity is **-0.52** (-0.61 to -0.44) and
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
| ≥2 days silent | 79 | 384 | 90.1% | 82.3% |
| ≥3 days silent | 71 | 392 | 91.5% | 84.1% |
| ≥7 days silent | 58 | 405 | 93.7% | 86.1% |
| ≥14 days silent | 42 | 421 | 96.2% | 90.4% |

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
