# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-10-11` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 695 model-variants, 640.35 T
tokens and 29.78 B requests over the trailing 30 days.


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
| **agentic** | 91 | 524.04 T | 81.8% | 54.4 | 53,342 | large contexts, terse output, very large interactions |
| **conversational** | 314 | 110.74 T | 17.3% | 9.2 | 3,618 | moderate context per output token, human-sized interactions |
| **unclassified** | 147 | 2.79 T | 0.4% | — | 28 | insufficient data to classify |
| **extractive** | 31 | 2.61 T | 0.4% | 56.1 | 5,004 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 112 | 158.93 B | 0.0% | 0.4 | 4,349 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **81.8% of all tokens**
while being 91 of 695 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
17.3%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `upstage/solar-decide-20260928` | 1,921.8 | 4,339 | 9.21 B | extractive |
| `upstage/solar-decide-flash-20261008` | 1,197.9 | 2,184 | 2.44 B | extractive |
| `perplexity/pplx-decider-v1-27b-20261001` | 1,155.6 | 4,655 | 9.10 B | extractive |
| `perplexity/pplx-decider-v1.1-27b-20261006` | 747.7 | 5,301 | 51.19 B | extractive |
| `inception/mercury-decide-20260930` | 619.8 | 4,811 | 24.47 B | extractive |
| `togethercomputer/tev1-4b-experimental-20260923` | 539.2 | 2,535 | 3.47 B | extractive |
| `microsoft/microsoft-decision-1-20261009` | 345.9 | 1,137 | 4.73 B | extractive |
| `inception/mercury-decide-20260930` | 317.4 | 1,001 | 1.88 B | extractive |
| `meta-llama/llama-guard-4-12b` | 234.2 | 797 | 8.09 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 208.7 | 133,042 | 23.05 T | agentic |

**Why both axes.** The top of this ranking is `upstage/solar-decide-20260928` at
1,921.8 tokens of context per token written, but its interactions
average only 4,339 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 208.7 tokens of context per token
written, in interactions averaging 133,042 tokens, which
is 31× larger.
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


Across 248 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.77** with a p25–p75 range of 0.55–1.04.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 18 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.58×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `qwen/qwen3.6-35b-a3b-20260415` | 3.70× | 335.21 B | 167 | conversational |
| `google/gemini-3.1-flash-lite-20260507` | 3.54× | 17.05 B | 157 | conversational |
| `google/gemini-2.5-flash` | 2.89× | 2.60 B | 481 | conversational |
| `google/gemini-3.8-flash-20260902` | 2.65× | 12.33 B | 39 | conversational |
| `amazon/nova-2-lite-v1` | 2.65× | 5.35 B | 313 | conversational |
| `z-ai/glm-5.3-prime-20260921` | 2.27× | 135.99 B | 18 | agentic |
| `anthropic/claude-sonnet-5.5-20260928` | 2.07× | 2.69 T | 13 | agentic |
| `meta-llama/llama-3.2-1b-instruct` | 2.02× | 1.01 B | 746 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `tencent/hy-mt2-7b-20260521` | 0.01× | 2.02 B | 53 | conversational |
| `tencent/hy-mt2-1.8b-20260521` | 0.03× | 2.42 B | 52 | conversational |
| `openai/gpt-5.6-sol-20260709` | 0.04× | 4.62 B | 94 | conversational |
| `thinkingmachines/inkling-20260715` | 0.12× | 120.11 B | 86 | agentic |
| `xiaomi/mimo-v2.5-20260422` | 0.13× | 14.59 T | 172 | agentic |
| `stepfun/step-3.7-flash-20260528` | 0.13× | 289.71 B | 136 | conversational |
| `perceptron/perceptron-mk1-20260512` | 0.17× | 6.96 B | 152 | extractive |
| `meta/muse-glimmer-30b-20260810` | 0.17× | 87.58 B | 63 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$302.5 M per month** across
472 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 4.4% | 27.4% | 6.18x |
| `openai` | 12.8% | 20.6% | 1.61x |
| `deepseek` | 25.4% | 13.0% | 0.51x |
| `tencent` | 8.6% | 12.0% | 1.40x |
| `google` | 4.6% | 6.1% | 1.31x |
| `moonshotai` | 1.3% | 5.8% | 4.53x |
| `z-ai` | 12.1% | 4.4% | 0.36x |
| `xiaomi` | 7.0% | 2.8% | 0.40x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**4,107**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **62.1%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.945** by value. Both are extreme; a
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
**6.43%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.59% |
| **extractive** | 2.37% |
| **conversational** | 1.59% |
| **output_heavy** | 0.64% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,015 endpoints serving multi-provider models,
**693 are dominated** (68.3%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `deepseek/deepseek-v4.1-flash-20260910` | Wafer | $1.60 | 24 tok/s | Baidu | 29 |
| `~deepseek/deepseek-flash-latest` | Wafer | $1.60 | 23 tok/s | Baidu | 29 |
| `z-ai/glm-5.3-flash-20260826` | Morph | $0.75 | 23 tok/s | InferenceNet | 28 |
| `~z-ai/glm-flash-latest` | Morph | $0.75 | 23 tok/s | InferenceNet | 28 |
| `z-ai/glm-5.3-20260816` | Fireworks | $4.40 | 50 tok/s | Baidu | 26 |
| `~z-ai/glm-latest` | Fireworks | $4.40 | 49 tok/s | Baidu | 26 |
| `z-ai/glm-5.3-20260816` | AtlasCloud | $4.40 | 52 tok/s | Baidu | 25 |
| `~z-ai/glm-latest` | AtlasCloud | $4.40 | 53 tok/s | Baidu | 25 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-10-10` and `2026-10-11`,
**2.01%** of 548 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.36 | -0.62 to -0.10 | 0.113 | 77 | yes |
| **all** | request weighted | +0.22 | -0.04 to +0.49 | 0.015 | 439 | no |
| **conversational** | request weighted | +0.25 | -0.08 to +0.58 | 0.020 | 284 | no |
| **extractive** | request weighted | +0.50 | -0.01 to +1.02 | 0.307 | 19 | no |
| **output_heavy** | request weighted | -0.26 | -0.44 to -0.08 | 0.090 | 59 | yes |
| **agentic** | unweighted | -0.45 | -0.79 to -0.10 | 0.072 | 77 | yes |
| **all** | unweighted | -0.99 | -1.34 to -0.65 | 0.081 | 439 | yes |
| **conversational** | unweighted | -1.00 | -1.38 to -0.61 | 0.104 | 284 | yes |
| **extractive** | unweighted | +0.23 | -0.45 to +0.91 | 0.016 | 19 | no |
| **output_heavy** | unweighted | -1.27 | -2.24 to -0.30 | 0.095 | 59 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.45, interval
-0.79 to -0.10, straddling zero). Weighting by requests, the
elasticity is **-0.36** (-0.62 to -0.10) and
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
| ≥2 days silent | 78 | 396 | 91.1% | 82.7% |
| ≥3 days silent | 55 | 419 | 93.2% | 88.4% |
| ≥7 days silent | 28 | 446 | 94.6% | 93.2% |
| ≥14 days silent | 24 | 450 | 94.8% | 93.9% |

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
