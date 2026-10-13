# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-10-13` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 698 model-variants, 656.11 T
tokens and 30.37 B requests over the trailing 30 days.


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
| **agentic** | 92 | 540.76 T | 82.4% | 54.7 | 52,855 | large contexts, terse output, very large interactions |
| **conversational** | 317 | 109.23 T | 16.6% | 9.1 | 3,780 | moderate context per output token, human-sized interactions |
| **extractive** | 33 | 3.14 T | 0.5% | 49.4 | 5,101 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 148 | 2.83 T | 0.4% | — | 28 | insufficient data to classify |
| **output_heavy** | 108 | 156.43 B | 0.0% | 0.4 | 3,998 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **82.4% of all tokens**
while being 92 of 698 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
16.6%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `upstage/solar-decide-20260928` | 1,832.5 | 4,346 | 10.97 B | extractive |
| `upstage/solar-decide-flash-20261008` | 1,266.7 | 3,100 | 4.47 B | extractive |
| `perplexity/pplx-decider-v1-27b-20261001` | 1,155.6 | 4,655 | 9.10 B | extractive |
| `perplexity/pplx-decider-v1.1-27b-20261006` | 1,148.2 | 6,371 | 138.35 B | extractive |
| `togethercomputer/tev1-4b-experimental-20260923` | 547.5 | 2,922 | 5.06 B | extractive |
| `inception/mercury-decide-20260930` | 351.4 | 2,933 | 32.91 B | extractive |
| `microsoft/microsoft-decision-1-20261009` | 328.4 | 1,181 | 12.61 B | extractive |
| `meta-llama/llama-guard-4-12b` | 234.3 | 800 | 7.93 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 212.1 | 133,736 | 24.30 T | agentic |
| `inception/mercury-decide-20260930` | 208.1 | 790 | 3.57 B | extractive |

**Why both axes.** The top of this ranking is `upstage/solar-decide-20260928` at
1,832.5 tokens of context per token written, but its interactions
average only 4,346 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 212.1 tokens of context per token
written, in interactions averaging 133,736 tokens, which
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


Across 252 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.97** with a p25–p75 range of 0.69–1.17.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 20 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.43×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `google/gemini-2.5-flash` | 11.65× | 4.36 B | 483 | conversational |
| `google/gemma-2-27b-it` | 9.64× | 409.61 M | 822 | conversational |
| `deepseek/deepseek-v4.1-flash-20260910` | 4.57× | 9.02 B | 33 | output_heavy |
| `openai/gpt-6-astra-pro-20260903` | 3.59× | 205.63 B | 39 | agentic |
| `google/gemini-3.1-flash-lite-20260507` | 3.08× | 21.97 B | 159 | conversational |
| `mistralai/mistral-medium-3.5-20260430` | 2.85× | 23.61 B | 166 | conversational |
| `mistralai/mistral-large-4-0-20261006` | 2.53× | 161.72 B | 7 | agentic |
| `perplexity/sonar-pro` | 2.38× | 4.63 B | 585 | output_heavy |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `z-ai/glm-5.3-flash-20260826` | 0.01× | 13.73 B | 48 | conversational |
| `openai/gpt-5.6-sol-20260709` | 0.01× | 4.35 B | 96 | conversational |
| `perceptron/perceptron-mk1-20260512` | 0.03× | 6.93 B | 154 | extractive |
| `tencent/hy-mt2-7b-20260521` | 0.05× | 1.47 B | 55 | conversational |
| `google/gemini-3.6-flash-20260721` | 0.09× | 12.65 B | 84 | conversational |
| `stepfun/step-3.7-flash-20260528` | 0.13× | 288.96 B | 138 | conversational |
| `xiaomi/mimo-v2.5-20260422` | 0.17× | 12.59 T | 174 | agentic |
| `microsoft/phi-4` | 0.20× | 6.23 B | 641 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$293.4 M per month** across
475 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 4.7% | 32.3% | 6.86x |
| `openai` | 12.0% | 20.0% | 1.67x |
| `tencent` | 8.1% | 12.0% | 1.48x |
| `deepseek` | 25.8% | 7.3% | 0.28x |
| `moonshotai` | 1.3% | 6.3% | 4.82x |
| `google` | 4.5% | 4.5% | 1.00x |
| `stepfun` | 1.9% | 4.2% | 2.17x |
| `z-ai` | 12.0% | 4.1% | 0.34x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,009**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **51.1%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.936** by value. Both are extreme; a
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
**6.61%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.17% |
| **extractive** | 2.38% |
| **conversational** | 1.62% |
| **output_heavy** | 0.46% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,114 endpoints serving multi-provider models,
**744 are dominated** (66.8%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-20260816` | Morph | $5.00 | 26 tok/s | Inceptron | 30 |
| `~z-ai/glm-latest` | Morph | $5.00 | 26 tok/s | Inceptron | 30 |
| `z-ai/glm-5.3-flash-20260826` | Morph | $1.00 | 15 tok/s | InferenceNet | 27 |
| `~z-ai/glm-flash-latest` | Morph | $1.00 | 15 tok/s | InferenceNet | 27 |
| `z-ai/glm-5.3-flash-20260826` | OpenInference | $0.90 | 13 tok/s | InferenceNet | 27 |
| `~z-ai/glm-flash-latest` | OpenInference | $0.90 | 13 tok/s | InferenceNet | 27 |
| `z-ai/glm-5.3-20260816` | Z.AI | $4.40 | 44 tok/s | Inceptron | 27 |
| `~z-ai/glm-latest` | Z.AI | $4.40 | 44 tok/s | Inceptron | 27 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-10-12` and `2026-10-13`,
**1.28%** of 548 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.51 | -0.88 to -0.14 | 0.208 | 79 | yes |
| **all** | request weighted | +0.10 | -0.24 to +0.44 | 0.003 | 441 | no |
| **conversational** | request weighted | +0.22 | -0.12 to +0.55 | 0.016 | 288 | no |
| **extractive** | request weighted | +0.44 | -0.11 to +0.99 | 0.217 | 21 | no |
| **output_heavy** | request weighted | -0.22 | -0.40 to -0.04 | 0.091 | 53 | yes |
| **agentic** | unweighted | -0.58 | -0.92 to -0.25 | 0.121 | 79 | yes |
| **all** | unweighted | -1.02 | -1.36 to -0.69 | 0.089 | 441 | yes |
| **conversational** | unweighted | -1.02 | -1.39 to -0.66 | 0.107 | 288 | yes |
| **extractive** | unweighted | +0.10 | -0.62 to +0.83 | 0.004 | 21 | no |
| **output_heavy** | unweighted | -1.34 | -2.21 to -0.48 | 0.125 | 53 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.58, interval
-0.92 to -0.25, straddling zero). Weighting by requests, the
elasticity is **-0.51** (-0.88 to -0.14) and
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
| ≥2 days silent | 72 | 403 | 92.0% | 84.6% |
| ≥3 days silent | 72 | 403 | 92.0% | 84.6% |
| ≥7 days silent | 44 | 431 | 94.1% | 90.5% |
| ≥14 days silent | 28 | 447 | 94.6% | 93.2% |

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
