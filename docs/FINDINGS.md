# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-08-02` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 505 model-variants, 241.51 T
tokens and 15.92 B requests over the trailing 30 days.


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
| **agentic** | 60 | 167.64 T | 69.4% | 56.6 | 45,558 | large contexts, terse output, very large interactions |
| **conversational** | 254 | 68.67 T | 28.4% | 11.7 | 3,730 | moderate context per output token, human-sized interactions |
| **extractive** | 27 | 2.81 T | 1.2% | 36.5 | 9,277 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 95 | 2.26 T | 0.9% | — | 39 | insufficient data to classify |
| **output_heavy** | 69 | 131.15 B | 0.1% | 0.6 | 4,343 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **69.4% of all tokens**
while being 60 of 505 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
28.4%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 207.7 | 770 | 14.78 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 161.7 | 104,086 | 10.04 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 148.1 | 88,089 | 903.03 B | agentic |
| `poolside/laguna-m.1-20260312` | 143.2 | 70,476 | 1.63 T | agentic |
| `xiaomi/mimo-v2.5-20260422` | 114.0 | 66,912 | 33.37 T | agentic |
| `perceptron/perceptron-mk1-20260512` | 96.2 | 9,277 | 13.45 B | extractive |
| `anthropic/claude-4.8-opus-fast-20260528` | 92.1 | 62,465 | 96.43 B | agentic |
| `anthropic/claude-4.8-opus-20260528` | 83.5 | 79,149 | 6.75 T | agentic |
| `stepfun/step-3.7-flash-20260528` | 81.7 | 65,484 | 6.01 T | agentic |
| `poolside/laguna-xs-2.1-20260625` | 80.4 | 53,221 | 562.87 B | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
207.7 tokens of context per token written, but its interactions
average only 770 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 161.7 tokens of context per token
written, in interactions averaging 104,086 tokens, which
is 135× larger.
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


Across 205 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.72** with a p25–p75 range of 0.53–0.99.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 17 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.76×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-5.6-luna-20260709` | 6.65× | 2.02 T | 24 | extractive |
| `google/gemini-3.1-flash-image-20260528` | 4.60× | 13.25 B | 45 | output_heavy |
| `openai/gpt-5.6-luna-pro-20260709` | 4.47× | 326.54 B | 24 | agentic |
| `mistralai/mistral-medium-3.5-20260430` | 3.88× | 29.74 B | 94 | extractive |
| `amazon/nova-micro-v1` | 3.51× | 81.69 B | 605 | conversational |
| `poolside/laguna-s-2.1-20260720` | 2.81× | 903.03 B | 12 | agentic |
| `inclusionai/ling-2.6-flash-20260421` | 2.79× | 404.90 B | 103 | conversational |
| `openai/gpt-5.6-terra-20260709` | 2.40× | 785.16 B | 24 | agentic |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `ibm-granite/granite-4.0-h-micro` | 0.02× | 80.03 B | 286 | agentic |
| `perceptron/perceptron-mk1-20260512` | 0.03× | 13.45 B | 82 | extractive |
| `tencent/hy3-preview-20260421` | 0.04× | 1.50 T | 102 | agentic |
| `anthropic/claude-4.7-opus-20260416` | 0.05× | 6.55 T | 108 | agentic |
| `openai/o4-mini-2025-04-16` | 0.09× | 88.68 B | 473 | conversational |
| `amazon/nova-2-lite-v1` | 0.09× | 17.06 B | 243 | conversational |
| `openai/gpt-3.5-turbo` | 0.14× | 5.27 B | 1,162 | conversational |
| `google/gemma-4-31b-it-20260402` | 0.14× | 40.35 B | 122 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$225.6 M per month** across
353 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 11.3% | 54.6% | 4.84x |
| `openai` | 7.3% | 15.0% | 2.06x |
| `google` | 8.1% | 5.7% | 0.71x |
| `moonshotai` | 2.3% | 4.9% | 2.11x |
| `deepseek` | 17.4% | 4.6% | 0.26x |
| `nvidia` | 5.1% | 2.8% | 0.54x |
| `z-ai` | 6.8% | 2.7% | 0.40x |
| `xiaomi` | 15.1% | 2.6% | 0.17x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,455**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **55.9%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.939** by value. Both are extreme; a
national income distribution above 0.6 is considered severe.


### The sticker price is not the price

Traffic is overwhelmingly prompt-heavy, and prompt tokens cost less than
completions. Blended across each model's real token mix, the price actually paid
per token is a median **0.32x** the headline output price, so the
sticker overstates unit cost by about **3.1x**.

Anyone comparing models on `$/M output` is getting this wrong.


## 5. The context window arms race is mostly unused

Dividing mean tokens per request by the advertised context length asks how much
of the window the traffic actually touches. Token-weighted across the market:
**8.19%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 8.09% |
| **extractive** | 2.73% |
| **conversational** | 1.88% |
| **output_heavy** | 1.84% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 619 endpoints serving multi-provider models,
**380 are dominated** (61.4%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `deepseek/deepseek-v4-pro-20260423` | CoreWeave | $3.48 | 4 tok/s | DeepSeek | 17 |
| `deepseek/deepseek-v4-flash-20260423` | OpenInference | $0.28 | 14 tok/s | StreamLake | 17 |
| `z-ai/glm-5.2-20260616` | Fireworks | $4.40 | 40 tok/s | Novita | 15 |
| `deepseek/deepseek-v4-flash-20260423` | Ionstream | $0.28 | 27 tok/s | StreamLake | 15 |
| `deepseek/deepseek-v4-pro-20260423` | Cloudflare | $3.48 | 40 tok/s | DeepSeek | 14 |
| `z-ai/glm-5.2-20260616` | Ambient | $4.40 | 42 tok/s | Novita | 13 |
| `deepseek/deepseek-v4-flash-20260423` | Mancer 2 | $0.50 | 35 tok/s | Baidu | 12 |
| `moonshotai/kimi-k2.6-20260420` | StreamLake | $3.60 | 7 tok/s | Baidu | 11 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-08-01` and `2026-08-02`,
**1.46%** of 410 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.45 | -0.64 to -0.27 | 0.387 | 49 | yes |
| **all** | request weighted | -0.13 | -0.52 to +0.27 | 0.009 | 329 | no |
| **conversational** | request weighted | -0.20 | -0.70 to +0.31 | 0.018 | 224 | no |
| **extractive** | request weighted | -0.97 | -2.44 to +0.49 | 0.203 | 21 | no |
| **output_heavy** | request weighted | +0.11 | -0.16 to +0.38 | 0.019 | 35 | no |
| **agentic** | unweighted | -0.02 | -0.52 to +0.47 | 0.000 | 49 | no |
| **all** | unweighted | -0.53 | -0.81 to -0.25 | 0.045 | 329 | yes |
| **conversational** | unweighted | -0.67 | -1.01 to -0.34 | 0.078 | 224 | yes |
| **extractive** | unweighted | -0.13 | -0.62 to +0.37 | 0.007 | 21 | no |
| **output_heavy** | unweighted | -1.04 | -1.71 to -0.36 | 0.124 | 35 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.02, interval
-0.52 to +0.47, straddling zero). Weighting by requests, the
elasticity is **-0.45** (-0.64 to -0.27) and
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
| ≥2 days silent | 35 | 320 | 94.4% | 87.6% |
| ≥3 days silent | 34 | 321 | 94.4% | 88.1% |
| ≥7 days silent | 11 | 344 | 98.8% | 96.6% |
| ≥14 days silent | 6 | 349 | 100.0% | 97.8% |

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
