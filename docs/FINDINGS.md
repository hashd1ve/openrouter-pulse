# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-10-02` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 657 model-variants, 583.15 T
tokens and 26.85 B requests over the trailing 30 days.


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
| **agentic** | 93 | 459.26 T | 78.8% | 54.1 | 52,790 | large contexts, terse output, very large interactions |
| **conversational** | 308 | 120.57 T | 20.7% | 9.9 | 3,842 | moderate context per output token, human-sized interactions |
| **unclassified** | 133 | 2.61 T | 0.4% | — | 31 | insufficient data to classify |
| **extractive** | 23 | 566.37 B | 0.1% | 41.8 | 5,423 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 100 | 141.00 B | 0.0% | 0.5 | 4,476 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **78.8% of all tokens**
while being 93 of 657 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
20.7%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 237.7 | 800 | 9.10 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 204.9 | 130,262 | 19.50 T | agentic |
| `thinkingmachines/inkling-small-20260730` | 125.9 | 57,211 | 499.65 B | agentic |
| `minimax/minimax-m3-20260531` | 124.4 | 76,111 | 4.33 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 111.5 | 82,755 | 4.92 T | agentic |
| `tencent/hy4-preview-20260827` | 111.5 | 115,020 | 55.11 T | agentic |
| `xiaomi/mimo-v2.5-20260422` | 110.2 | 61,553 | 19.56 T | agentic |
| `deepseek/deepseek-v4-flash-20260731` | 105.4 | 98,351 | 1.09 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 103.5 | 96,212 | 227.70 B | agentic |
| `openai/gpt-6-astra-20260903` | 103.0 | 64,068 | 4.46 T | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
237.7 tokens of context per token written, but its interactions
average only 800 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 204.9 tokens of context per token
written, in interactions averaging 130,262 tokens, which
is 163× larger.
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


Across 246 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.95** with a p25–p75 range of 0.71–1.19.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 19 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **2.73×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `perceptron/perceptron-mk1-20260512` | 20.74× | 5.78 B | 143 | extractive |
| `qwen/qwen3.8-27b-20260814` | 7.03× | 90.27 B | 49 | agentic |
| `ibm-granite/granite-4.2-8b-20260831` | 5.73× | 18.35 B | 32 | conversational |
| `openai/gpt-5.3-codex-20260224` | 3.49× | 155.36 B | 220 | agentic |
| `openai/o4-mini-2025-04-16` | 3.22× | 9.78 B | 534 | conversational |
| `openai/gpt-6-astra-20260903` | 2.89× | 4.46 T | 28 | agentic |
| `openai/gpt-3.5-turbo` | 2.42× | 3.00 B | 1,223 | conversational |
| `inclusionai/ling-3.0-flash-vl-20260910` | 2.41× | 35.50 B | 22 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `tencent/hy-mt2-1.8b-20260521` | 0.04× | 3.02 B | 43 | conversational |
| `tencent/hy-mt2-7b-20260521` | 0.09× | 2.43 B | 44 | conversational |
| `stepfun/step-3.7-flash-20260528` | 0.11× | 465.08 B | 127 | agentic |
| `upstage/solar-pro4-20260810` | 0.17× | 6.42 T | 53 | agentic |
| `openai/gpt-6-luna-20260922` | 0.20× | 81.72 B | 10 | conversational |
| `openai/gpt-5.6-luna-20260709` | 0.22× | 49.91 T | 85 | agentic |
| `ibm-granite/granite-4.0-h-micro` | 0.22× | 18.18 B | 347 | conversational |
| `mistralai/mistral-large-2512` | 0.23× | 21.75 B | 305 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$269.2 M per month** across
455 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 4.0% | 21.5% | 5.42x |
| `openai` | 14.7% | 20.7% | 1.41x |
| `tencent` | 12.2% | 18.2% | 1.48x |
| `z-ai` | 13.5% | 11.8% | 0.87x |
| `google` | 5.3% | 6.8% | 1.28x |
| `moonshotai` | 1.4% | 6.4% | 4.55x |
| `deepseek` | 22.1% | 5.4% | 0.24x |
| `xiaomi` | 5.8% | 2.2% | 0.38x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**2,706**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **47.8%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.931** by value. Both are extreme; a
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
**6.32%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.42% |
| **extractive** | 3.32% |
| **conversational** | 1.71% |
| **output_heavy** | 1.22% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,105 endpoints serving multi-provider models,
**758 are dominated** (68.6%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-20260816` | Fireworks | $4.40 | 45 tok/s | Baidu | 30 |
| `~z-ai/glm-latest` | Fireworks | $4.40 | 45 tok/s | Baidu | 30 |
| `z-ai/glm-5.3-flash-20260826` | OpenInference | $0.90 | 17 tok/s | DeepInfra | 30 |
| `~z-ai/glm-flash-latest` | OpenInference | $0.90 | 17 tok/s | DeepInfra | 30 |
| `z-ai/glm-5.3-flash-20260826` | Cloudflare | $1.00 | 23 tok/s | DeepInfra | 29 |
| `~z-ai/glm-flash-latest` | Cloudflare | $1.00 | 23 tok/s | DeepInfra | 29 |
| `deepseek/deepseek-v4.1-flash-20260910` | OpenInference | $1.20 | 8 tok/s | Decart | 28 |
| `~deepseek/deepseek-flash-latest` | OpenInference | $1.20 | 8 tok/s | Decart | 28 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-10-01` and `2026-10-02`,
**1.16%** of 519 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.38 | -0.68 to -0.09 | 0.121 | 82 | yes |
| **all** | request weighted | +0.15 | -0.26 to +0.56 | 0.008 | 425 | no |
| **conversational** | request weighted | +0.01 | -0.76 to +0.79 | 0.000 | 280 | no |
| **extractive** | request weighted | +0.54 | +0.33 to +0.75 | 0.542 | 15 | yes |
| **output_heavy** | request weighted | -0.06 | -0.40 to +0.27 | 0.005 | 48 | no |
| **agentic** | unweighted | -0.61 | -0.91 to -0.30 | 0.127 | 82 | yes |
| **all** | unweighted | -0.55 | -0.82 to -0.28 | 0.039 | 425 | yes |
| **conversational** | unweighted | -0.73 | -1.05 to -0.40 | 0.085 | 280 | yes |
| **extractive** | unweighted | -0.11 | -0.74 to +0.52 | 0.005 | 15 | no |
| **output_heavy** | unweighted | +0.03 | -0.82 to +0.87 | 0.000 | 48 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.61, interval
-0.91 to -0.30, straddling zero). Weighting by requests, the
elasticity is **-0.38** (-0.68 to -0.09) and
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
| ≥2 days silent | 66 | 392 | 89.3% | 83.5% |
| ≥3 days silent | 54 | 404 | 91.6% | 86.9% |
| ≥7 days silent | 44 | 414 | 91.8% | 88.7% |
| ≥14 days silent | 24 | 434 | 96.0% | 93.6% |

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
