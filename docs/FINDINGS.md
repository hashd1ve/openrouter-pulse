# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-10-06` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 654 model-variants, 607.51 T
tokens and 28.27 B requests over the trailing 30 days.


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
| **agentic** | 92 | 489.94 T | 80.6% | 53.6 | 52,790 | large contexts, terse output, very large interactions |
| **conversational** | 304 | 113.65 T | 18.7% | 9.6 | 3,930 | moderate context per output token, human-sized interactions |
| **unclassified** | 134 | 2.66 T | 0.4% | — | 35 | insufficient data to classify |
| **extractive** | 27 | 1.12 T | 0.2% | 50.8 | 5,196 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 97 | 147.08 B | 0.0% | 0.4 | 4,492 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **80.6% of all tokens**
while being 92 of 654 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
18.7%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `upstage/solar-decide-20260928` | 2,090.7 | 4,823 | 6.24 B | extractive |
| `meta-llama/llama-guard-4-12b` | 235.3 | 791 | 8.67 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 206.1 | 132,025 | 20.75 T | agentic |
| `upstage/solar-mini4-20260922` | 145.4 | 52,785 | 547.13 B | agentic |
| `minimax/minimax-m3-20260531` | 136.8 | 78,718 | 788.47 B | agentic |
| `thinkingmachines/inkling-small-20260730` | 125.6 | 57,225 | 507.88 B | agentic |
| `tencent/hy4-preview-20260827` | 113.2 | 115,729 | 48.32 T | agentic |
| `openai/gpt-6-astra-20260903` | 105.8 | 65,008 | 5.07 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 105.6 | 81,121 | 4.64 T | agentic |
| `deepseek/deepseek-v4-flash-20260731` | 105.4 | 98,351 | 1.09 T | agentic |

**Why both axes.** The top of this ranking is `upstage/solar-decide-20260928` at
2,090.7 tokens of context per token written, but its interactions
average only 4,823 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 206.1 tokens of context per token
written, in interactions averaging 132,025 tokens, which
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


Across 254 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.97** with a p25–p75 range of 0.75–1.18.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 19 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **2.00×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `qwen/qwen3.8-27b-20260814` | 5.02× | 292.08 B | 53 | agentic |
| `meta/muse-glimmer-30b-20260810` | 4.58× | 71.99 B | 58 | conversational |
| `deepseek/deepseek-v4.1-flash-20260910` | 4.17× | 5.65 B | 26 | output_heavy |
| `qwen/qwen3-14b-04-28` | 4.15× | 16.56 B | 526 | conversational |
| `stepfun/step-3.7-flash-20260528` | 3.53× | 332.87 B | 131 | conversational |
| `microsoft/phi-4` | 3.34× | 2.87 B | 634 | conversational |
| `inclusionai/ling-3.0-flash-vl-20260910` | 3.31× | 55.46 B | 26 | conversational |
| `qwen/qwen3.8-2.4t-a95b-20260812` | 3.07× | 130.15 B | 55 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `tencent/hy-mt2-1.8b-20260521` | 0.06× | 2.94 B | 47 | conversational |
| `tencent/hy-mt2-7b-20260521` | 0.13× | 2.40 B | 48 | conversational |
| `google/gemini-3.6-flash-20260721` | 0.16× | 11.94 B | 77 | conversational |
| `openai/gpt-5.6-luna-20260709` | 0.17× | 62.64 B | 89 | conversational |
| `google/gemini-3.7-flash-20260813` | 0.19× | 10.15 B | 54 | output_heavy |
| `openai/gpt-5.6-luna-20260709` | 0.19× | 43.27 T | 89 | agentic |
| `amazon/nova-lite-v1` | 0.20× | 18.21 B | 670 | conversational |
| `ibm-granite/granite-4.0-h-micro` | 0.21× | 17.66 B | 351 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$270.7 M per month** across
449 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 3.8% | 30.7% | 7.98x |
| `openai` | 13.8% | 24.7% | 1.80x |
| `tencent` | 10.4% | 15.9% | 1.53x |
| `google` | 5.0% | 6.5% | 1.31x |
| `deepseek` | 23.1% | 6.1% | 0.27x |
| `z-ai` | 12.6% | 3.7% | 0.29x |
| `moonshotai` | 1.3% | 3.2% | 2.49x |
| `xiaomi` | 6.5% | 2.7% | 0.41x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,052**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **51.6%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.932** by value. Both are extreme; a
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
**6.35%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.38% |
| **extractive** | 2.98% |
| **conversational** | 1.61% |
| **output_heavy** | 1.40% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,141 endpoints serving multi-provider models,
**766 are dominated** (67.1%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `~z-ai/glm-flash-latest` | OpenInference | $0.69 | 12 tok/s | DeepInfra | 29 |
| `deepseek/deepseek-v4.1-flash-20260910` | OpenInference | $1.32 | 13 tok/s | Decart | 28 |
| `~deepseek/deepseek-flash-latest` | OpenInference | $1.32 | 13 tok/s | Decart | 28 |
| `z-ai/glm-5.3-flash-20260826` | OpenInference | $0.69 | 12 tok/s | DeepInfra | 28 |
| `~z-ai/glm-flash-latest` | Morph | $0.65 | 13 tok/s | DeepInfra | 27 |
| `z-ai/glm-5.3-20260816` | Z.AI | $4.40 | 40 tok/s | SiliconFlow | 27 |
| `~z-ai/glm-latest` | Z.AI | $4.40 | 40 tok/s | SiliconFlow | 27 |
| `z-ai/glm-5.3-flash-20260826` | DekaLLM | $1.00 | 17 tok/s | Novita | 26 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-10-05` and `2026-10-06`,
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
| **agentic** | request weighted | -0.48 | -0.66 to -0.29 | 0.281 | 79 | yes |
| **all** | request weighted | +0.17 | -0.25 to +0.59 | 0.009 | 417 | no |
| **conversational** | request weighted | +0.53 | -0.00 to +1.05 | 0.081 | 276 | no |
| **extractive** | request weighted | +0.36 | -0.31 to +1.02 | 0.088 | 18 | no |
| **output_heavy** | request weighted | -0.24 | -0.43 to -0.05 | 0.084 | 44 | yes |
| **agentic** | unweighted | -0.46 | -0.80 to -0.12 | 0.081 | 79 | yes |
| **all** | unweighted | -0.40 | -0.66 to -0.14 | 0.023 | 417 | yes |
| **conversational** | unweighted | -0.61 | -0.91 to -0.32 | 0.072 | 276 | yes |
| **extractive** | unweighted | -0.12 | -0.71 to +0.46 | 0.005 | 18 | no |
| **output_heavy** | unweighted | +0.29 | -0.64 to +1.23 | 0.008 | 44 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.46, interval
-0.80 to -0.12, straddling zero). Weighting by requests, the
elasticity is **-0.48** (-0.66 to -0.29) and
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
| ≥2 days silent | 46 | 405 | 91.5% | 89.0% |
| ≥3 days silent | 44 | 407 | 92.1% | 89.6% |
| ≥7 days silent | 43 | 408 | 92.4% | 89.9% |
| ≥14 days silent | 25 | 426 | 95.5% | 94.1% |

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
