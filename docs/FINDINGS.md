# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-10-15` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 704 model-variants, 673.85 T
tokens and 31.28 B requests over the trailing 30 days.


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
| **agentic** | 92 | 557.72 T | 82.8% | 54.3 | 54,543 | large contexts, terse output, very large interactions |
| **conversational** | 322 | 109.82 T | 16.3% | 9.3 | 3,816 | moderate context per output token, human-sized interactions |
| **extractive** | 32 | 3.20 T | 0.5% | 43.8 | 4,972 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 151 | 2.95 T | 0.4% | — | 30 | insufficient data to classify |
| **output_heavy** | 107 | 163.78 B | 0.0% | 0.4 | 4,316 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **82.8% of all tokens**
while being 92 of 704 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
16.3%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `upstage/solar-decide-20260928` | 2,021.8 | 4,761 | 14.56 B | extractive |
| `upstage/solar-decide-flash-20261008` | 1,459.2 | 3,548 | 5.93 B | extractive |
| `perplexity/pplx-decider-v1.1-27b-20261006` | 1,160.7 | 4,776 | 208.01 B | extractive |
| `perplexity/pplx-decider-v1-27b-20261001` | 1,155.6 | 4,655 | 9.10 B | extractive |
| `togethercomputer/tev1-4b-experimental-20260923` | 568.6 | 3,008 | 6.05 B | extractive |
| `microsoft/microsoft-decision-1-20261009` | 339.4 | 1,240 | 19.82 B | extractive |
| `inception/mercury-decide-20260930` | 337.8 | 2,816 | 34.57 B | extractive |
| `meta-llama/llama-guard-4-12b` | 234.1 | 801 | 7.68 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 213.5 | 134,218 | 25.49 T | agentic |
| `stepfun/step-5-preview-20261008` | 183.3 | 195,450 | 18.79 T | agentic |

**Why both axes.** The top of this ranking is `upstage/solar-decide-20260928` at
2,021.8 tokens of context per token written, but its interactions
average only 4,761 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 213.5 tokens of context per token
written, in interactions averaging 134,218 tokens, which
is 28× larger.
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
median of **0.92** with a p25–p75 range of 0.70–1.20.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 24 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.30×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `qwen/qwen3.6-35b-a3b-20260415` | 7.23× | 540.26 B | 171 | conversational |
| `google/gemini-2.5-flash` | 7.07× | 5.49 B | 485 | conversational |
| `qwen/qwen3.8-2.4t-a95b-20260812` | 3.63× | 199.18 B | 64 | conversational |
| `z-ai/glm-4.5-air` | 3.52× | 46.81 B | 447 | conversational |
| `openai/gpt-5.4-mini-20260317` | 3.45× | 534.33 B | 212 | conversational |
| `anthropic/claude-sonnet-5.5-20260928` | 2.71× | 5.62 B | 17 | conversational |
| `nvidia/nemotron-3-super-120b-a12b-20230311` | 2.55× | 1.96 T | 218 | agentic |
| `google/gemini-3.7-flash-20260813` | 2.46× | 11.83 B | 63 | output_heavy |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite-20260507` | 0.00× | 21.96 B | 161 | conversational |
| `openai/gpt-5.6-sol-20260709` | 0.00× | 4.14 B | 98 | conversational |
| `perceptron/perceptron-mk1-20260512` | 0.03× | 6.91 B | 156 | extractive |
| `google/gemma-2-27b-it` | 0.08× | 438.08 M | 824 | conversational |
| `tencent/hy-mt2-1.8b-20260521` | 0.12× | 1.60 B | 56 | conversational |
| `stepfun/step-3.7-flash-20260528` | 0.16× | 287.72 B | 140 | conversational |
| `openai/gpt-6-sol-20260922` | 0.22× | 3.86 B | 23 | conversational |
| `xiaomi/mimo-v2.5-20260422` | 0.22× | 10.61 T | 176 | agentic |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$281.8 M per month** across
479 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 5.0% | 31.5% | 6.24x |
| `openai` | 11.2% | 21.7% | 1.94x |
| `tencent` | 7.8% | 12.2% | 1.57x |
| `stepfun` | 2.9% | 6.8% | 2.33x |
| `google` | 4.5% | 5.7% | 1.28x |
| `deepseek` | 25.9% | 5.0% | 0.19x |
| `z-ai` | 12.0% | 4.8% | 0.40x |
| `xiaomi` | 7.2% | 3.4% | 0.48x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,993**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **61.0%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.945** by value. Both are extreme; a
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
**6.66%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.19% |
| **extractive** | 1.97% |
| **conversational** | 1.64% |
| **output_heavy** | 0.47% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,112 endpoints serving multi-provider models,
**755 are dominated** (67.9%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-20260816` | Alibaba | $8.80 | 28 tok/s | Inceptron | 40 |
| `~z-ai/glm-latest` | Alibaba | $8.80 | 26 tok/s | Inceptron | 39 |
| `z-ai/glm-5.3-20260816` | Venice | $4.40 | 28 tok/s | Inceptron | 31 |
| `z-ai/glm-5.3-flash-20260826` | Morph | $1.00 | 19 tok/s | StreamLake | 31 |
| `~z-ai/glm-flash-latest` | Morph | $1.00 | 20 tok/s | StreamLake | 31 |
| `z-ai/glm-5.3-flash-20260826` | OpenInference | $0.90 | 10 tok/s | StreamLake | 31 |
| `~z-ai/glm-flash-latest` | OpenInference | $0.90 | 11 tok/s | StreamLake | 31 |
| `~z-ai/glm-latest` | Venice | $4.40 | 31 tok/s | Inceptron | 30 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-10-14` and `2026-10-15`,
**1.27%** of 552 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.48 | -0.73 to -0.23 | 0.190 | 77 | yes |
| **all** | request weighted | +0.02 | -0.23 to +0.26 | 0.000 | 444 | no |
| **conversational** | request weighted | -0.10 | -0.50 to +0.29 | 0.004 | 294 | no |
| **extractive** | request weighted | +0.60 | +0.09 to +1.12 | 0.385 | 20 | yes |
| **output_heavy** | request weighted | -0.24 | -0.43 to -0.05 | 0.101 | 53 | yes |
| **agentic** | unweighted | -0.57 | -0.90 to -0.23 | 0.107 | 77 | yes |
| **all** | unweighted | -1.01 | -1.35 to -0.68 | 0.088 | 444 | yes |
| **conversational** | unweighted | -1.06 | -1.42 to -0.70 | 0.124 | 294 | yes |
| **extractive** | unweighted | +0.35 | -0.38 to +1.08 | 0.033 | 20 | no |
| **output_heavy** | unweighted | -1.26 | -2.13 to -0.39 | 0.106 | 53 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.57, interval
-0.90 to -0.23, straddling zero). Weighting by requests, the
elasticity is **-0.48** (-0.73 to -0.23) and
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
| ≥2 days silent | 77 | 404 | 91.2% | 83.4% |
| ≥3 days silent | 71 | 410 | 92.0% | 84.7% |
| ≥7 days silent | 54 | 427 | 93.3% | 88.5% |
| ≥14 days silent | 28 | 453 | 94.6% | 93.3% |

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
