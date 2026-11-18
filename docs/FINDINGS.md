# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-11-18` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 784 model-variants, 888.04 T
tokens and 41.17 B requests over the trailing 30 days.


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
| **agentic** | 104 | 711.54 T | 80.1% | 58.1 | 56,675 | large contexts, terse output, very large interactions |
| **conversational** | 319 | 114.83 T | 12.9% | 10.0 | 4,013 | moderate context per output token, human-sized interactions |
| **extractive** | 49 | 56.54 T | 6.4% | 43.8 | 4,774 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 187 | 4.86 T | 0.5% | — | 41 | insufficient data to classify |
| **output_heavy** | 125 | 269.12 B | 0.0% | 0.4 | 4,407 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **80.1% of all tokens**
while being 104 of 784 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
12.9%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `scaledown/classify-1-20260928` | 2,914.1 | 7,645 | 13.61 B | extractive |
| `upstage/solar-decide-20260928` | 2,160.5 | 4,774 | 10.92 B | extractive |
| `upstage/solar-decide-flash-20261008` | 1,526.2 | 3,037 | 5.26 B | extractive |
| `microsoft/microsoft-decision-1-20261009` | 751.2 | 2,243 | 117.51 B | extractive |
| `perplexity/pplx-decider-flash-v1.2-20261016` | 593.7 | 2,030 | 108.71 B | extractive |
| `perplexity/pplx-decider-v1.2-20261016` | 508.5 | 1,917 | 1.54 T | extractive |
| `inception/mercury-decide-20260930` | 465.4 | 659 | 87.56 B | extractive |
| `inception/mercury-decide-20260930` | 399.2 | 6,331 | 104.12 B | extractive |
| `baseten/mammoth-1-20261021` | 393.6 | 686 | 22.92 B | extractive |
| `togethercomputer/tev1-4b-experimental-20260923` | 374.0 | 1,817 | 3.44 B | extractive |

**Why both axes.** The top of this ranking is `scaledown/classify-1-20260928` at
2,914.1 tokens of context per token written, but its interactions
average only 7,645 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `stepfun/step-5-preview-20261008`: 214.3 tokens of context per token
written, in interactions averaging 256,444 tokens, which
is 34× larger.
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


Across 266 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **1.02** with a p25–p75 range of 0.81–1.23.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 15 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **2.14×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `moonshotai/kimi-k2` | 14.46× | 14.80 B | 495 | conversational |
| `deepseek/deepseek-v4.1-flash-20261017` | 10.56× | 18.19 B | 32 | output_heavy |
| `meta/muse-glimmer-30b-20260810` | 6.51× | 97.00 B | 101 | conversational |
| `particle-ai/particle-1-20261027` | 5.70× | 636.33 B | 21 | agentic |
| `meituan/longcat-2.0-20260720` | 4.59× | 47.20 B | 121 | agentic |
| `nvidia/nemotron-3-nano-30b-a3b` | 4.35× | 31.55 B | 339 | conversational |
| `thinkingmachines/inkling-2-small-20261107` | 3.77× | 386.53 B | 9 | agentic |
| `openai/gpt-5-nano-2025-08-07` | 3.44× | 195.73 B | 468 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `tencent/hy4-preview-20260827` | 0.01× | 21.75 T | 82 | agentic |
| `tencent/hy3-20260706` | 0.01× | 10.66 T | 135 | agentic |
| `openai/gpt-5-nano-2025-08-07` | 0.04× | 9.74 B | 468 | conversational |
| `stepfun/step-3.7-flash-20260528` | 0.05× | 871.09 B | 174 | agentic |
| `openai/gpt-oss-20b` | 0.09× | 2.87 B | 470 | conversational |
| `google/gemini-3.6-flash-20260721` | 0.12× | 4.97 B | 120 | conversational |
| `thinkingmachines/inkling-small-20260730` | 0.13× | 48.88 B | 111 | conversational |
| `openai/gpt-6-sol-20260922` | 0.14× | 3.29 B | 57 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$432.9 M per month** across
499 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 7.4% | 44.2% | 5.96x |
| `openai` | 9.3% | 16.1% | 1.73x |
| `tencent` | 10.3% | 8.1% | 0.78x |
| `stepfun` | 3.1% | 6.0% | 1.95x |
| `deepseek` | 37.3% | 5.4% | 0.14x |
| `moonshotai` | 2.3% | 5.3% | 2.29x |
| `google` | 3.4% | 4.7% | 1.40x |
| `z-ai` | 9.3% | 3.9% | 0.42x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**2,915**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **50.3%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.940** by value. Both are extreme; a
national income distribution above 0.6 is considered severe.


### The sticker price is not the price

Traffic is overwhelmingly prompt-heavy, and prompt tokens cost less than
completions. Blended across each model's real token mix, the price actually paid
per token is a median **0.33x** the headline output price, so the
sticker overstates unit cost by about **3.0x**.

Anyone comparing models on `$/M output` is getting this wrong.


## 5. The context window arms race is mostly unused

Dividing mean tokens per request by the advertised context length asks how much
of the window the traffic actually touches. Token-weighted across the market:
**6.91%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.38% |
| **extractive** | 1.70% |
| **conversational** | 1.65% |
| **output_heavy** | 1.26% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,276 endpoints serving multi-provider models,
**905 are dominated** (70.9%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `deepseek/deepseek-v4.1-flash-20261017` | Morph | $2.40 | 28 tok/s | Sail Research | 46 |
| `~deepseek/deepseek-flash-latest` | Morph | $2.40 | 31 tok/s | Sail Research | 46 |
| `deepseek/deepseek-v4.1-flash-20261017` | Venice | $1.20 | 94 tok/s | Sail Research | 35 |
| `deepseek/deepseek-v4.1-flash-20260910` | Google | $1.20 | 49 tok/s | Baidu | 34 |
| `z-ai/glm-5.3-flash-20260826` | Near AI | $0.50 | 12 tok/s | Relace | 34 |
| `~z-ai/glm-flash-latest` | Near AI | $0.50 | 12 tok/s | Relace | 34 |
| `~deepseek/deepseek-flash-latest` | Venice | $1.20 | 102 tok/s | Sail Research | 33 |
| `~z-ai/glm-latest` | Morph | $5.05 | 52 tok/s | Wafer | 32 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-11-17` and `2026-11-18`,
**1.71%** of 586 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.61 | -0.94 to -0.29 | 0.235 | 88 | yes |
| **all** | request weighted | -0.24 | -0.54 to +0.07 | 0.017 | 460 | no |
| **conversational** | request weighted | -0.26 | -0.62 to +0.10 | 0.036 | 288 | no |
| **extractive** | request weighted | -0.83 | -1.16 to -0.50 | 0.593 | 28 | yes |
| **output_heavy** | request weighted | -0.10 | -0.41 to +0.21 | 0.017 | 56 | no |
| **agentic** | unweighted | -0.59 | -0.99 to -0.19 | 0.092 | 88 | yes |
| **all** | unweighted | -0.61 | -0.85 to -0.38 | 0.056 | 460 | yes |
| **conversational** | unweighted | -0.71 | -0.96 to -0.47 | 0.108 | 288 | yes |
| **extractive** | unweighted | -0.42 | -1.62 to +0.78 | 0.015 | 28 | no |
| **output_heavy** | unweighted | -0.49 | -0.98 to +0.00 | 0.051 | 56 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.59, interval
-0.99 to -0.19, straddling zero). Weighting by requests, the
elasticity is **-0.61** (-0.94 to -0.29) and
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
| ≥2 days silent | 71 | 429 | 94.0% | 85.6% |
| ≥3 days silent | 70 | 430 | 94.0% | 85.6% |
| ≥7 days silent | 55 | 445 | 96.3% | 88.8% |
| ≥14 days silent | 37 | 463 | 98.0% | 93.2% |

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
