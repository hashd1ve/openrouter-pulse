# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-08-31` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 597 model-variants, 365.06 T
tokens and 18.95 B requests over the trailing 30 days.


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
| **agentic** | 73 | 284.56 T | 77.9% | 52.2 | 50,235 | large contexts, terse output, very large interactions |
| **conversational** | 284 | 77.30 T | 21.2% | 10.3 | 3,884 | moderate context per output token, human-sized interactions |
| **unclassified** | 121 | 1.95 T | 0.5% | — | 28 | insufficient data to classify |
| **extractive** | 27 | 1.10 T | 0.3% | 37.2 | 7,464 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 92 | 146.14 B | 0.0% | 0.4 | 4,470 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **77.9% of all tokens**
while being 73 of 597 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
21.2%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 370.6 | 1,328 | 20.24 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 168.1 | 107,028 | 15.30 T | agentic |
| `tencent/hy4-preview-20260827` | 155.7 | 152,984 | 3.07 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 141.7 | 90,626 | 6.93 T | agentic |
| `thinkingmachines/inkling-20260715` | 139.7 | 68,797 | 202.45 B | agentic |
| `xiaomi/mimo-v2.5-20260422` | 133.8 | 77,417 | 29.44 T | agentic |
| `minimax/minimax-m3-20260531` | 132.1 | 78,869 | 2.57 T | agentic |
| `poolside/laguna-xs-2.1-20260625` | 117.1 | 54,768 | 614.55 B | agentic |
| `thinkingmachines/inkling-small-20260730` | 104.6 | 49,548 | 81.25 B | agentic |
| `anthropic/claude-opus-5-fast-20260723` | 101.5 | 89,880 | 112.04 B | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
370.6 tokens of context per token written, but its interactions
average only 1,328 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 168.1 tokens of context per token
written, in interactions averaging 107,028 tokens, which
is 81× larger.
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


Across 220 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.76** with a p25–p75 range of 0.57–1.04.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 17 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.58×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `minimax/minimax-m2.7-20260318` | 9.55× | 205.24 B | 166 | agentic |
| `minimax/minimax-m3-20260531` | 8.76× | 2.57 T | 92 | agentic |
| `qwen/qwen3-8b-04-28` | 5.40× | 22.10 B | 490 | conversational |
| `ibm-granite/granite-4.0-h-micro` | 4.59× | 3.74 B | 315 | conversational |
| `thinkingmachines/inkling-20260715` | 4.29× | 202.45 B | 45 | agentic |
| `thinkingmachines/inkling-small-20260730` | 4.26× | 81.25 B | 32 | agentic |
| `amazon/nova-2-lite-v1` | 3.35× | 4.47 B | 272 | conversational |
| `thinkingmachines/inkling-20260715` | 2.52× | 75.37 B | 45 | agentic |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `google/gemma-4-26b-a4b-it-20260403` | 0.09× | 44.59 B | 150 | conversational |
| `google/gemini-3.6-flash-20260721` | 0.10× | 6.22 T | 41 | agentic |
| `anthropic/claude-4.7-opus-20260416` | 0.12× | 1.33 T | 137 | agentic |
| `google/gemini-3.6-flash-20260721` | 0.14× | 2.64 B | 41 | conversational |
| `nex-agi/nex-n2-mini` | 0.15× | 94.70 B | 68 | conversational |
| `z-ai/glm-5v-turbo-20260401` | 0.16× | 102.03 B | 152 | agentic |
| `qwen/qwen3.7-max-20260520` | 0.17× | 284.32 B | 102 | agentic |
| `nvidia/nemotron-3-nano-30b-a3b` | 0.18× | 48.73 B | 260 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$216.3 M per month** across
433 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 6.0% | 34.7% | 5.79x |
| `openai` | 11.7% | 15.6% | 1.33x |
| `z-ai` | 6.6% | 10.5% | 1.60x |
| `moonshotai` | 2.1% | 9.5% | 4.59x |
| `deepseek` | 22.9% | 8.4% | 0.37x |
| `google` | 8.1% | 6.2% | 0.77x |
| `nvidia` | 5.6% | 3.8% | 0.69x |
| `tencent` | 10.3% | 3.4% | 0.33x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**2,218**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **40.7%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.932** by value. Both are extreme; a
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
**9.37%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.37% |
| **extractive** | 2.53% |
| **output_heavy** | 1.90% |
| **conversational** | 1.84% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 819 endpoints serving multi-provider models,
**540 are dominated** (65.9%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.2-20260616` | Mistral | $4.40 | 35 tok/s | Baidu | 24 |
| `deepseek/deepseek-v4-flash-20260731` | Phala | $1.32 | 28 tok/s | AkashML | 23 |
| `~deepseek/deepseek-v4-flash-latest` | Phala | $1.32 | 28 tok/s | AkashML | 23 |
| `z-ai/glm-5.3-flash-20260826` | Io Net | $0.50 | 10 tok/s | Relace | 19 |
| `z-ai/glm-5.2-20260616` | Fireworks | $4.40 | 46 tok/s | Baidu | 18 |
| `z-ai/glm-5.3-flash-20260826` | Parasail | $0.50 | 21 tok/s | Relace | 17 |
| `z-ai/glm-5.3-flash-20260826` | Phala | $0.50 | 24 tok/s | Relace | 16 |
| `z-ai/glm-5.2-20260616` | Z.AI | $4.40 | 48 tok/s | Baidu | 16 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-08-29` and `2026-08-31`,
**2.95%** of 474 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.56 | -0.70 to -0.43 | 0.472 | 58 | yes |
| **all** | request weighted | -0.22 | -0.67 to +0.23 | 0.021 | 398 | no |
| **conversational** | request weighted | -0.31 | -0.96 to +0.34 | 0.040 | 267 | no |
| **extractive** | request weighted | -0.20 | -1.22 to +0.81 | 0.020 | 23 | no |
| **output_heavy** | request weighted | +0.01 | -0.26 to +0.29 | 0.000 | 50 | no |
| **agentic** | unweighted | -0.19 | -0.60 to +0.22 | 0.012 | 58 | no |
| **all** | unweighted | -0.70 | -0.98 to -0.42 | 0.075 | 398 | yes |
| **conversational** | unweighted | -1.02 | -1.31 to -0.73 | 0.198 | 267 | yes |
| **extractive** | unweighted | -0.29 | -0.67 to +0.09 | 0.051 | 23 | no |
| **output_heavy** | unweighted | -0.09 | -1.04 to +0.86 | 0.001 | 50 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.19, interval
-0.60 to +0.22, straddling zero). Weighting by requests, the
elasticity is **-0.56** (-0.70 to -0.43) and
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
| ≥2 days silent | 70 | 366 | 91.9% | 84.5% |
| ≥3 days silent | 65 | 371 | 92.6% | 85.5% |
| ≥7 days silent | 18 | 418 | 97.7% | 94.5% |
| ≥14 days silent | 5 | 431 | 98.6% | 98.6% |

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
