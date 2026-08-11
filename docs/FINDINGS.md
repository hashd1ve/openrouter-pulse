# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-08-11` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 528 model-variants, 264.24 T
tokens and 16.57 B requests over the trailing 30 days.


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
| **agentic** | 59 | 193.36 T | 73.2% | 49.8 | 45,682 | large contexts, terse output, very large interactions |
| **conversational** | 267 | 67.60 T | 25.6% | 10.2 | 3,981 | moderate context per output token, human-sized interactions |
| **unclassified** | 103 | 2.30 T | 0.9% | — | 30 | insufficient data to classify |
| **extractive** | 26 | 852.43 B | 0.3% | 42.3 | 8,635 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 73 | 134.88 B | 0.1% | 0.6 | 4,443 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **73.2% of all tokens**
while being 59 of 528 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
25.6%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 268.4 | 995 | 19.38 B | extractive |
| `poolside/laguna-s-2.1-20260720` | 161.1 | 95,117 | 3.26 T | agentic |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 154.7 | 101,556 | 11.09 T | agentic |
| `poolside/laguna-m.1-20260312` | 138.3 | 68,998 | 922.64 B | agentic |
| `xiaomi/mimo-v2.5-20260422` | 117.6 | 68,322 | 33.31 T | agentic |
| `perceptron/perceptron-mk1-20260512` | 112.0 | 9,472 | 11.20 B | extractive |
| `poolside/laguna-xs-2.1-20260625` | 104.9 | 56,477 | 622.66 B | agentic |
| `anthropic/claude-opus-5-fast-20260723` | 97.6 | 86,220 | 95.75 B | agentic |
| `stepfun/step-3.7-flash-20260528` | 87.5 | 68,807 | 5.90 T | agentic |
| `anthropic/claude-4.8-opus-fast-20260528` | 80.5 | 56,868 | 77.66 B | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
268.4 tokens of context per token written, but its interactions
average only 995 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `poolside/laguna-s-2.1-20260720`: 161.1 tokens of context per token
written, in interactions averaging 95,117 tokens, which
is 96× larger.
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


Across 211 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.95** with a p25–p75 range of 0.69–1.16.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 14 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.50×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `inclusionai/ling-3.0-flash-20260723` | 7.87× | 31.71 B | 19 | conversational |
| `nvidia/nemotron-3-nano-30b-a3b` | 3.63× | 88.80 B | 240 | conversational |
| `meta-llama/llama-3.1-70b-instruct` | 3.59× | 37.64 B | 749 | conversational |
| `qwen/qwen-2.5-72b-instruct` | 3.14× | 15.90 B | 691 | conversational |
| `openai/gpt-5.6-luna-20260709` | 3.03× | 7.81 T | 33 | agentic |
| `perceptron/perceptron-mk1-20260512` | 2.98× | 11.20 B | 91 | extractive |
| `tencent/hy3-20260706` | 2.84× | 18.63 T | 36 | agentic |
| `qwen/qwen3-vl-235b-a22b-instruct` | 2.70× | 58.71 B | 322 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `ibm-granite/granite-4.0-h-micro` | 0.09× | 20.66 B | 295 | extractive |
| `openai/o4-mini-2025-04-16` | 0.19× | 40.41 B | 482 | conversational |
| `openai/gpt-4o-2024-05-13` | 0.20× | 3.77 B | 820 | extractive |
| `deepseek/deepseek-v3.1-terminus` | 0.21× | 162.40 B | 323 | conversational |
| `mistralai/mistral-medium-3` | 0.21× | 3.96 B | 461 | conversational |
| `amazon/nova-2-lite-v1` | 0.23× | 14.72 B | 252 | conversational |
| `openai/gpt-5-2025-08-07` | 0.25× | 167.21 B | 369 | conversational |
| `anthropic/claude-4.7-opus-20260416` | 0.29× | 3.83 T | 117 | agentic |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$190.9 M per month** across
380 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 9.0% | 41.6% | 4.62x |
| `openai` | 9.1% | 14.5% | 1.60x |
| `moonshotai` | 2.6% | 8.7% | 3.32x |
| `deepseek` | 20.2% | 7.2% | 0.35x |
| `z-ai` | 6.1% | 6.3% | 1.03x |
| `google` | 8.2% | 6.0% | 0.74x |
| `nvidia` | 5.1% | 3.7% | 0.74x |
| `xiaomi` | 13.7% | 3.0% | 0.22x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**2,752**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **49.1%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.935** by value. Both are extreme; a
national income distribution above 0.6 is considered severe.


### The sticker price is not the price

Traffic is overwhelmingly prompt-heavy, and prompt tokens cost less than
completions. Blended across each model's real token mix, the price actually paid
per token is a median **0.34x** the headline output price, so the
sticker overstates unit cost by about **2.9x**.

Anyone comparing models on `$/M output` is getting this wrong.


## 5. The context window arms race is mostly unused

Dividing mean tokens per request by the advertised context length asks how much
of the window the traffic actually touches. Token-weighted across the market:
**8.67%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.27% |
| **extractive** | 3.63% |
| **output_heavy** | 2.00% |
| **conversational** | 1.86% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 698 endpoints serving multi-provider models,
**457 are dominated** (65.5%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.2-20260616` | Venice | $4.40 | 21 tok/s | Decart | 21 |
| `z-ai/glm-5.2-20260616` | BaseTen | $4.40 | 26 tok/s | Decart | 20 |
| `~deepseek/deepseek-v4-flash-latest` | Ambient | $0.28 | 8 tok/s | Decart | 19 |
| `deepseek/deepseek-v4-flash-20260731` | Ambient | $0.28 | 8 tok/s | Decart | 18 |
| `deepseek/deepseek-v4-flash-20260731` | Ionstream | $0.42 | 32 tok/s | Decart | 16 |
| `~deepseek/deepseek-v4-flash-latest` | Ionstream | $0.42 | 33 tok/s | Decart | 16 |
| `deepseek/deepseek-v4-flash-20260731` | AkashML | $0.28 | 15 tok/s | Decart | 16 |
| `~deepseek/deepseek-v4-flash-latest` | AkashML | $0.28 | 15 tok/s | Decart | 16 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-08-10` and `2026-08-11`,
**0.71%** of 423 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.40 | -0.59 to -0.22 | 0.330 | 55 | yes |
| **all** | request weighted | -0.10 | -0.50 to +0.30 | 0.005 | 360 | no |
| **conversational** | request weighted | -0.19 | -0.72 to +0.35 | 0.013 | 247 | no |
| **extractive** | request weighted | -0.09 | -1.18 to +0.99 | 0.004 | 22 | no |
| **output_heavy** | request weighted | +0.05 | -0.20 to +0.30 | 0.004 | 36 | no |
| **agentic** | unweighted | -0.23 | -0.68 to +0.23 | 0.013 | 55 | no |
| **all** | unweighted | -0.59 | -0.83 to -0.35 | 0.055 | 360 | yes |
| **conversational** | unweighted | -0.87 | -1.14 to -0.60 | 0.121 | 247 | yes |
| **extractive** | unweighted | -0.52 | -1.24 to +0.19 | 0.058 | 22 | no |
| **output_heavy** | unweighted | -0.44 | -1.00 to +0.11 | 0.078 | 36 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.23, interval
-0.68 to +0.23, straddling zero). Weighting by requests, the
elasticity is **-0.40** (-0.59 to -0.22) and
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
| ≥2 days silent | 33 | 349 | 95.5% | 90.7% |
| ≥3 days silent | 24 | 358 | 97.3% | 93.2% |
| ≥7 days silent | 15 | 367 | 98.9% | 95.3% |
| ≥14 days silent | 12 | 370 | 98.9% | 96.3% |

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
