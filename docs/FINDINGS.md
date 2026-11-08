# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-11-08` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 742 model-variants, 804.53 T
tokens and 38.82 B requests over the trailing 30 days.


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
| **agentic** | 99 | 637.81 T | 79.3% | 55.5 | 55,625 | large contexts, terse output, very large interactions |
| **conversational** | 312 | 109.19 T | 13.6% | 10.0 | 3,888 | moderate context per output token, human-sized interactions |
| **extractive** | 41 | 53.16 T | 6.6% | 46.9 | 4,593 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 176 | 4.20 T | 0.5% | — | 36 | insufficient data to classify |
| **output_heavy** | 114 | 172.19 B | 0.0% | 0.4 | 4,418 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **79.3% of all tokens**
while being 99 of 742 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
13.6%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `scaledown/classify-1-20260928` | 2,310.5 | 7,342 | 19.42 B | extractive |
| `upstage/solar-decide-20260928` | 2,114.1 | 4,663 | 17.07 B | extractive |
| `upstage/solar-decide-flash-20261008` | 1,605.1 | 3,941 | 10.17 B | extractive |
| `perplexity/pplx-decider-v1.1-27b-20261006` | 1,138.6 | 3,818 | 248.07 B | extractive |
| `perplexity/pplx-decider-flash-v1.2-20261016` | 1,031.9 | 2,132 | 89.14 B | extractive |
| `microsoft/microsoft-decision-1-20261009` | 597.3 | 1,710 | 102.89 B | extractive |
| `perplexity/pplx-decider-v1.2-20261016` | 514.6 | 1,942 | 862.94 B | extractive |
| `togethercomputer/tev1-4b-experimental-20260923` | 455.2 | 2,379 | 6.32 B | extractive |
| `baseten/mammoth-1-20261021` | 413.4 | 708 | 13.75 B | extractive |
| `inception/mercury-decide-20260930` | 401.6 | 732 | 115.85 B | extractive |

**Why both axes.** The top of this ranking is `scaledown/classify-1-20260928` at
2,310.5 tokens of context per token written, but its interactions
average only 7,342 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `stepfun/step-5-preview-20261008`: 196.8 tokens of context per token
written, in interactions averaging 217,758 tokens, which
is 30× larger.
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


Across 261 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.75** with a p25–p75 range of 0.53–0.98.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 16 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.30×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `amazon/nova-2-lite-v1` | 7.67× | 8.33 B | 341 | conversational |
| `meta/muse-glimmer-30b-20260810` | 4.82× | 68.73 B | 91 | conversational |
| `openai/gpt-3.5-turbo-0613` | 3.38× | 532.90 M | 1,018 | conversational |
| `qwen/qwen3.5-27b-20260224` | 3.35× | 38.78 B | 256 | conversational |
| `qwen/qwen3-coder-30b-a3b-instruct` | 2.86× | 40.62 B | 465 | conversational |
| `reflection/beam-1.0-501b-a23b-20261016` | 2.08× | 306.15 B | 23 | agentic |
| `moonshotai/kimi-k3.1-pro-20261023` | 2.04× | 6.46 T | 16 | agentic |
| `google/gemma-3-4b-it` | 1.93× | 11.82 B | 605 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-5-nano-2025-08-07` | 0.01× | 10.43 B | 458 | conversational |
| `google/gemini-3.1-flash-lite-20260507` | 0.03× | 25.28 B | 185 | conversational |
| `openai/gpt-6-luna-pro-20260922` | 0.04× | 18.52 B | 47 | conversational |
| `tencent/hy4-preview-20260827` | 0.05× | 32.38 T | 72 | agentic |
| `stepfun/step-3.7-flash-20260528` | 0.05× | 870.68 B | 164 | agentic |
| `xiaomi/mimo-v2.5-20260422` | 0.05× | 946.39 B | 200 | agentic |
| `google/gemini-3.6-flash-20260721` | 0.07× | 7.58 B | 110 | conversational |
| `anthropic/claude-opus-5-20260723` | 0.07× | 456.24 M | 107 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$414.9 M per month** across
475 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 7.9% | 43.1% | 5.47x |
| `openai` | 9.7% | 17.5% | 1.80x |
| `stepfun` | 4.7% | 8.7% | 1.86x |
| `tencent` | 7.1% | 8.1% | 1.14x |
| `moonshotai` | 2.1% | 5.5% | 2.67x |
| `google` | 3.6% | 4.4% | 1.21x |
| `z-ai` | 10.7% | 3.3% | 0.31x |
| `xiaomi` | 4.3% | 2.0% | 0.47x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,264**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **54.4%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.936** by value. Both are extreme; a
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
**6.79%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 6.71% |
| **conversational** | 1.75% |
| **output_heavy** | 1.73% |
| **extractive** | 1.56% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,169 endpoints serving multi-provider models,
**850 are dominated** (72.7%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-flash-20260826` | Near AI | $0.50 | 37 tok/s | Relace | 33 |
| `~z-ai/glm-flash-latest` | Near AI | $0.50 | 38 tok/s | Relace | 33 |
| `z-ai/glm-5.3-20260816` | BaseTen | $4.40 | 55 tok/s | Wafer | 31 |
| `~z-ai/glm-latest` | BaseTen | $4.40 | 53 tok/s | Wafer | 31 |
| `z-ai/glm-5.3-flash-20260826` | Z.AI | $0.50 | 40 tok/s | Relace | 31 |
| `~z-ai/glm-flash-latest` | Z.AI | $0.50 | 40 tok/s | Relace | 31 |
| `z-ai/glm-5.3-flash-20260826` | AtlasCloud | $0.50 | 40 tok/s | Relace | 31 |
| `~z-ai/glm-flash-latest` | AtlasCloud | $0.50 | 40 tok/s | Relace | 31 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-10-25` and `2026-11-08`,
**0.00%** of 1 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.65 | -0.89 to -0.41 | 0.477 | 84 | yes |
| **all** | request weighted | -0.44 | -0.88 to -0.01 | 0.066 | 444 | yes |
| **conversational** | request weighted | -0.25 | -0.60 to +0.11 | 0.026 | 289 | no |
| **extractive** | request weighted | -1.03 | -1.47 to -0.59 | 0.500 | 22 | yes |
| **output_heavy** | request weighted | -0.06 | -0.39 to +0.26 | 0.007 | 49 | no |
| **agentic** | unweighted | -0.42 | -0.86 to +0.01 | 0.050 | 84 | no |
| **all** | unweighted | -0.51 | -0.73 to -0.28 | 0.042 | 444 | yes |
| **conversational** | unweighted | -0.55 | -0.76 to -0.34 | 0.071 | 289 | yes |
| **extractive** | unweighted | -0.07 | -1.11 to +0.97 | 0.001 | 22 | no |
| **output_heavy** | unweighted | -0.38 | -0.98 to +0.21 | 0.025 | 49 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.42, interval
-0.86 to +0.01, straddling zero). Weighting by requests, the
elasticity is **-0.65** (-0.89 to -0.41) and
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
| ≥2 days silent | 75 | 401 | 93.9% | 85.3% |
| ≥3 days silent | 70 | 406 | 94.5% | 86.2% |
| ≥7 days silent | 57 | 419 | 96.2% | 88.7% |
| ≥14 days silent | 36 | 440 | 98.1% | 95.3% |

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
