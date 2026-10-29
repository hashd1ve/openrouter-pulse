# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-10-29` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 729 model-variants, 748.53 T
tokens and 36.79 B requests over the trailing 30 days.


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
| **agentic** | 93 | 531.19 T | 71.0% | 54.1 | 53,174 | large contexts, terse output, very large interactions |
| **conversational** | 323 | 168.01 T | 22.4% | 9.5 | 4,026 | moderate context per output token, human-sized interactions |
| **extractive** | 39 | 45.46 T | 6.1% | 43.9 | 4,867 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 167 | 3.70 T | 0.5% | — | 36 | insufficient data to classify |
| **output_heavy** | 107 | 170.90 B | 0.0% | 0.3 | 4,334 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **71.0% of all tokens**
while being 93 of 729 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
22.4%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `upstage/solar-decide-20260928` | 2,200.2 | 4,929 | 23.17 B | extractive |
| `scaledown/classify-1-20260928` | 2,183.5 | 7,140 | 13.42 B | extractive |
| `upstage/solar-decide-flash-20261008` | 1,490.6 | 3,444 | 9.55 B | extractive |
| `perplexity/pplx-decider-v1-27b-20261001` | 1,155.6 | 4,655 | 9.10 B | extractive |
| `perplexity/pplx-decider-v1.1-27b-20261006` | 1,141.1 | 3,834 | 257.20 B | extractive |
| `perplexity/pplx-decider-flash-v1.2-20261016` | 1,091.6 | 2,851 | 46.47 B | extractive |
| `togethercomputer/tev1-4b-experimental-20260923` | 490.0 | 2,408 | 7.81 B | extractive |
| `perplexity/pplx-decider-v1.2-20261016` | 489.6 | 1,918 | 308.72 B | extractive |
| `inception/mercury-decide-20260930` | 389.6 | 4,867 | 152.23 B | extractive |
| `inception/mercury-decide-20260930` | 384.9 | 964 | 67.98 B | extractive |

**Why both axes.** The top of this ranking is `upstage/solar-decide-20260928` at
2,200.2 tokens of context per token written, but its interactions
average only 4,929 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `stepfun/step-5-preview-20261008`: 189.2 tokens of context per token
written, in interactions averaging 205,135 tokens, which
is 42× larger.
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
median of **0.95** with a p25–p75 range of 0.71–1.21.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 19 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.88×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `nex-agi/nex-n2.5-mini-20260908` | 4.79× | 26.44 B | 51 | conversational |
| `stepfun/step-3.7-flash-20260528` | 3.75× | 601.62 B | 154 | agentic |
| `google/gemma-3-4b-it` | 3.66× | 5.42 B | 595 | conversational |
| `deepseek/deepseek-v4.1-flash-20260910` | 3.14× | 28.70 B | 49 | conversational |
| `minimax/minimax-m3.1-flash-20261019` | 2.80× | 3.21 T | 10 | agentic |
| `google/gemini-nano-banana-2.1-20261006` | 2.39× | 5.01 B | 23 | output_heavy |
| `qwen/qwen3-30b-a3b-04-28` | 2.11× | 9.38 B | 549 | conversational |
| `google/gemini-3.1-flash-lite-20260507` | 2.07× | 21.54 B | 175 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-5-nano-2025-08-07` | 0.01× | 9.95 B | 448 | conversational |
| `inclusionai/ling-3.0-flash-vl-20260910` | 0.03× | 107.77 B | 49 | conversational |
| `inclusionai/ling-3.1-flash-20261002` | 0.07× | 1.13 T | 27 | conversational |
| `xiaomi/mimo-v2.5-20260422` | 0.08× | 2.24 T | 190 | agentic |
| `perceptron/perceptron-mk1-20260512` | 0.10× | 6.89 B | 170 | extractive |
| `xiaomi/mimo-v2.5-pro-20260422` | 0.12× | 552.57 B | 190 | agentic |
| `openai/gpt-6-sol-20260922` | 0.18× | 6.85 B | 37 | conversational |
| `xiaomi/mimo-v2.6-pro-ultraspeed-20260921` | 0.19× | 412.98 B | 38 | agentic |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$376.4 M per month** across
477 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 7.3% | 44.4% | 6.06x |
| `openai` | 9.8% | 15.5% | 1.58x |
| `tencent` | 6.3% | 8.2% | 1.29x |
| `stepfun` | 3.7% | 7.1% | 1.91x |
| `deepseek` | 30.2% | 6.7% | 0.22x |
| `z-ai` | 10.8% | 3.7% | 0.35x |
| `google` | 3.9% | 3.5% | 0.88x |
| `xiaomi` | 6.4% | 2.9% | 0.46x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,036**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **52.0%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.934** by value. Both are extreme; a
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
**6.52%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 6.57% |
| **extractive** | 1.81% |
| **conversational** | 1.79% |
| **output_heavy** | 0.70% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,223 endpoints serving multi-provider models,
**867 are dominated** (70.9%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-20260816` | Amazon Bedrock | $5.28 | 17 tok/s | Baidu | 42 |
| `~z-ai/glm-latest` | Amazon Bedrock | $5.28 | 18 tok/s | Baidu | 42 |
| `~z-ai/glm-latest` | Cloudflare | $4.40 | 34 tok/s | Baidu | 40 |
| `z-ai/glm-5.3-20260816` | BaseTen | $6.60 | 50 tok/s | Baidu | 40 |
| `z-ai/glm-5.3-20260816` | Nebius | $4.40 | 28 tok/s | Baidu | 40 |
| `z-ai/glm-5.3-20260816` | Cloudflare | $4.40 | 34 tok/s | Baidu | 39 |
| `~z-ai/glm-latest` | AkashML | $4.40 | 48 tok/s | Baidu | 38 |
| `z-ai/glm-5.3-20260816` | AkashML | $4.40 | 48 tok/s | Baidu | 36 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-10-28` and `2026-10-29`,
**1.97%** of 559 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.65 | -0.92 to -0.38 | 0.469 | 84 | yes |
| **all** | request weighted | -0.48 | -0.88 to -0.08 | 0.098 | 446 | yes |
| **conversational** | request weighted | -0.69 | -1.31 to -0.08 | 0.181 | 294 | yes |
| **extractive** | request weighted | -1.15 | -1.60 to -0.70 | 0.632 | 21 | yes |
| **output_heavy** | request weighted | -0.18 | -0.47 to +0.11 | 0.075 | 47 | no |
| **agentic** | unweighted | -0.32 | -0.69 to +0.05 | 0.032 | 84 | no |
| **all** | unweighted | -0.88 | -1.18 to -0.57 | 0.079 | 446 | yes |
| **conversational** | unweighted | -0.73 | -1.03 to -0.42 | 0.069 | 294 | yes |
| **extractive** | unweighted | -0.46 | -1.43 to +0.50 | 0.042 | 21 | no |
| **output_heavy** | unweighted | -1.56 | -2.41 to -0.71 | 0.165 | 47 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.32, interval
-0.69 to +0.05, straddling zero). Weighting by requests, the
elasticity is **-0.65** (-0.92 to -0.38) and
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
| ≥2 days silent | 71 | 407 | 96.1% | 88.3% |
| ≥3 days silent | 66 | 412 | 96.7% | 90.0% |
| ≥7 days silent | 47 | 431 | 96.7% | 92.7% |
| ≥14 days silent | 39 | 439 | 96.9% | 92.9% |

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
