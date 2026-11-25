# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-11-25` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 765 model-variants, 832.65 T
tokens and 42.78 B requests over the trailing 30 days.


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
| **agentic** | 101 | 666.30 T | 80.0% | 57.7 | 51,878 | large contexts, terse output, very large interactions |
| **conversational** | 312 | 115.12 T | 13.8% | 10.1 | 3,854 | moderate context per output token, human-sized interactions |
| **extractive** | 53 | 45.68 T | 5.5% | 59.0 | 4,574 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 176 | 5.25 T | 0.6% | — | 36 | insufficient data to classify |
| **output_heavy** | 123 | 302.69 B | 0.0% | 0.3 | 4,410 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **80.0% of all tokens**
while being 101 of 765 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
13.8%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `scaledown/classify-1-20260928` | 3,626.9 | 9,231 | 20.32 B | extractive |
| `upstage/solar-decide-20260928` | 1,546.7 | 3,526 | 6.31 B | extractive |
| `upstage/solar-decide-flash-20261008` | 1,391.4 | 2,937 | 4.41 B | extractive |
| `microsoft/microsoft-decision-1-20261009` | 863.3 | 2,800 | 129.94 B | extractive |
| `cloudflare/clairic-20261029` | 525.8 | 2,045 | 3.82 B | extractive |
| `perplexity/pplx-decider-flash-v1.2-20261016` | 522.9 | 1,896 | 97.80 B | extractive |
| `perplexity/pplx-decider-v1.2-20261016` | 472.1 | 1,968 | 1.85 T | extractive |
| `inception/mercury-decide-20260930` | 471.3 | 6,700 | 26.18 B | extractive |
| `baseten/bison-1-20261120` | 460.0 | 1,976 | 2.77 B | extractive |
| `inception/mercury-decide-20260930` | 434.5 | 583 | 68.60 B | extractive |

**Why both axes.** The top of this ranking is `scaledown/classify-1-20260928` at
3,626.9 tokens of context per token written, but its interactions
average only 9,231 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `thinkingmachines/inkling-2-small-20261107`: 175.5 tokens of context per token
written, in interactions averaging 176,007 tokens, which
is 19× larger.
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


Across 263 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.96** with a p25–p75 range of 0.68–1.19.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 18 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.94×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `google/gemini-3-flash-preview-20251217` | 17.73× | 317.29 M | 343 | conversational |
| `deepseek/deepseek-v4.1-flash-20261017` | 8.24× | 64.88 B | 39 | output_heavy |
| `scaledown/extract-20260928` | 6.53× | 12.67 B | 43 | conversational |
| `bytedance-seed/seed-2.0-lite-20260309` | 4.76× | 30.07 B | 260 | conversational |
| `thinkingmachines/inkling-small-20260730` | 4.56× | 39.88 B | 118 | conversational |
| `openai/gpt-oss-20b` | 4.01× | 3.49 B | 477 | conversational |
| `deepseek/deepseek-v4.1-flash-20260910` | 3.63× | 21.63 B | 76 | conversational |
| `openai/gpt-4.1-nano-2025-04-14` | 3.30× | 50.71 B | 590 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `google/gemini-3.6-flash-20260721` | 0.04× | 2.24 B | 127 | conversational |
| `upstage/solar-mini4-20260922` | 0.04× | 2.17 T | 63 | agentic |
| `tencent/hy4-preview-20260827` | 0.05× | 4.66 T | 89 | agentic |
| `stepfun/step-5-preview-20261008` | 0.06× | 430.31 B | 48 | extractive |
| `openai/gpt-5.6-luna-20260709` | 0.07× | 56.08 B | 139 | conversational |
| `stepfun/step-3.7-flash-20260528` | 0.08× | 741.46 B | 181 | agentic |
| `ricursiveai/ripple-65b-preview-20261104` | 0.11× | 32.38 B | 21 | conversational |
| `google/gemma-2-27b-it` | 0.18× | 448.62 M | 865 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$429.0 M per month** across
490 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 7.7% | 45.2% | 5.86x |
| `openai` | 10.0% | 18.2% | 1.82x |
| `deepseek` | 43.8% | 13.0% | 0.30x |
| `google` | 4.0% | 8.5% | 2.11x |
| `z-ai` | 9.7% | 2.9% | 0.30x |
| `nvidia` | 4.3% | 2.3% | 0.55x |
| `moonshotai` | 2.8% | 1.9% | 0.68x |
| `tencent` | 4.9% | 1.7% | 0.35x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,090**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **52.3%** of
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
**5.48%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 5.99% |
| **output_heavy** | 1.54% |
| **extractive** | 1.49% |
| **conversational** | 1.45% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,236 endpoints serving multi-provider models,
**875 are dominated** (70.8%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `deepseek/deepseek-v4.1-flash-20261017` | Google | $1.20 | 106 tok/s | Pearl Research | 36 |
| `~deepseek/deepseek-flash-latest` | Google | $1.20 | 106 tok/s | Pearl Research | 36 |
| `z-ai/glm-5.3-20260816` | SambaNova | $4.40 | 45 tok/s | Wafer | 35 |
| `~z-ai/glm-latest` | SambaNova | $4.40 | 45 tok/s | Wafer | 35 |
| `z-ai/glm-5.3-flash-20260826` | Parasail | $0.62 | 28 tok/s | Relace | 35 |
| `~z-ai/glm-flash-latest` | Parasail | $0.62 | 27 tok/s | Relace | 34 |
| `deepseek/deepseek-v4.1-flash-20260910` | Google | $1.20 | 67 tok/s | DeepInfra | 32 |
| `deepseek/deepseek-v4.1-flash-20260910` | Baidu | $1.20 | 67 tok/s | DeepInfra | 32 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-11-20` and `2026-11-25`,
**5.70%** of 579 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.56 | -0.88 to -0.24 | 0.192 | 93 | yes |
| **all** | request weighted | -0.24 | -0.53 to +0.05 | 0.017 | 469 | no |
| **conversational** | request weighted | -0.22 | -0.51 to +0.07 | 0.028 | 291 | no |
| **extractive** | request weighted | -1.18 | -1.60 to -0.77 | 0.421 | 31 | yes |
| **output_heavy** | request weighted | -0.44 | -0.87 to -0.01 | 0.179 | 54 | yes |
| **agentic** | unweighted | -0.33 | -0.67 to +0.02 | 0.038 | 93 | no |
| **all** | unweighted | -0.39 | -0.63 to -0.14 | 0.024 | 469 | yes |
| **conversational** | unweighted | -0.47 | -0.76 to -0.18 | 0.044 | 291 | yes |
| **extractive** | unweighted | -0.39 | -1.33 to +0.55 | 0.017 | 31 | no |
| **output_heavy** | unweighted | -0.44 | -0.94 to +0.07 | 0.047 | 54 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.33, interval
-0.67 to +0.02, straddling zero). Weighting by requests, the
elasticity is **-0.56** (-0.88 to -0.24) and
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
| ≥2 days silent | 73 | 418 | 91.0% | 81.6% |
| ≥3 days silent | 68 | 423 | 92.1% | 82.9% |
| ≥7 days silent | 51 | 440 | 94.9% | 87.0% |
| ≥14 days silent | 36 | 455 | 96.4% | 89.5% |

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
