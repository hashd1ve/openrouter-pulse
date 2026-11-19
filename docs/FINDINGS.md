# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-11-19` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 784 model-variants, 920.04 T
tokens and 41.68 B requests over the trailing 30 days.


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
| **agentic** | 106 | 742.26 T | 80.7% | 57.2 | 57,679 | large contexts, terse output, very large interactions |
| **conversational** | 314 | 115.08 T | 12.5% | 10.3 | 4,028 | moderate context per output token, human-sized interactions |
| **extractive** | 48 | 57.46 T | 6.2% | 46.9 | 4,880 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 186 | 4.95 T | 0.5% | — | 40 | insufficient data to classify |
| **output_heavy** | 130 | 280.35 B | 0.0% | 0.5 | 4,389 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **80.7% of all tokens**
while being 106 of 784 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
12.5%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `cloudflare/clairic-20261029` | 942,121.6 | 1,291 | 2.12 B | extractive |
| `scaledown/classify-1-20260928` | 2,546.1 | 6,671 | 11.68 B | extractive |
| `upstage/solar-decide-20260928` | 1,965.9 | 4,474 | 9.91 B | extractive |
| `upstage/solar-decide-flash-20261008` | 1,499.5 | 2,970 | 5.16 B | extractive |
| `microsoft/microsoft-decision-1-20261009` | 758.2 | 2,255 | 117.15 B | extractive |
| `perplexity/pplx-decider-flash-v1.2-20261016` | 577.1 | 1,981 | 106.61 B | extractive |
| `perplexity/pplx-decider-v1.2-20261016` | 496.9 | 1,910 | 1.60 T | extractive |
| `inception/mercury-decide-20260930` | 459.5 | 645 | 84.84 B | extractive |
| `inception/mercury-decide-20260930` | 398.9 | 6,368 | 90.75 B | extractive |
| `baseten/mammoth-1-20261021` | 395.5 | 699 | 23.83 B | extractive |

**Why both axes.** The top of this ranking is `cloudflare/clairic-20261029` at
942,121.6 tokens of context per token written, but its interactions
average only 1,291 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `stepfun/step-5-preview-20261008`: 214.3 tokens of context per token
written, in interactions averaging 256,319 tokens, which
is 199× larger.
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
median of **0.98** with a p25–p75 range of 0.74–1.21.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 16 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **2.15×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `moonshotai/kimi-k2` | 10.63× | 22.57 B | 496 | extractive |
| `deepseek/deepseek-v4.1-flash-20261017` | 6.62× | 23.35 B | 33 | output_heavy |
| `particle-ai/particle-1-20261027` | 5.52× | 849.39 B | 22 | agentic |
| `mistralai/mistral-small-2603` | 3.69× | 49.78 B | 248 | conversational |
| `rekaai/reka-edge-2603` | 3.49× | 565.73 M | 244 | conversational |
| `meituan/longcat-2.0-20260720` | 3.21× | 52.15 B | 122 | agentic |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 3.08× | 165.64 B | 168 | conversational |
| `amazon/nova-2-lite-v1` | 2.95× | 13.92 B | 352 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `mistralai/mistral-medium-3.1` | 0.00× | 31.45 B | 463 | conversational |
| `tencent/hy4-preview-20260827` | 0.01× | 20.39 T | 83 | agentic |
| `tencent/hy3-20260706` | 0.02× | 10.16 T | 136 | agentic |
| `openai/gpt-5-nano-2025-08-07` | 0.03× | 9.75 B | 469 | conversational |
| `google/gemini-3.6-flash-20260721` | 0.05× | 4.85 B | 121 | conversational |
| `openai/gpt-6-sol-20260922` | 0.09× | 3.26 B | 58 | conversational |
| `google/gemma-2-27b-it` | 0.10× | 639.72 M | 859 | conversational |
| `stepfun/step-3.7-flash-20260528` | 0.12× | 872.66 B | 175 | agentic |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$344.6 M per month** across
499 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 7.2% | 36.9% | 5.14x |
| `openai` | 9.1% | 16.7% | 1.83x |
| `tencent` | 12.5% | 10.2% | 0.81x |
| `stepfun` | 3.0% | 7.7% | 2.54x |
| `google` | 3.3% | 6.7% | 2.02x |
| `deepseek` | 36.6% | 6.4% | 0.18x |
| `z-ai` | 8.9% | 4.8% | 0.54x |
| `moonshotai` | 2.3% | 2.6% | 1.14x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**2,876**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **50.2%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.933** by value. Both are extreme; a
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
**7.03%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.83% |
| **conversational** | 1.58% |
| **extractive** | 1.54% |
| **output_heavy** | 1.14% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,269 endpoints serving multi-provider models,
**898 are dominated** (70.8%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-flash-20260826` | Near AI | $0.50 | 17 tok/s | Relace | 35 |
| `~z-ai/glm-flash-latest` | Near AI | $0.50 | 16 tok/s | Relace | 35 |
| `z-ai/glm-5.3-flash-20260826` | Parasail | $0.50 | 22 tok/s | Relace | 34 |
| `~z-ai/glm-flash-latest` | Parasail | $0.50 | 21 tok/s | Relace | 34 |
| `deepseek/deepseek-v4.1-flash-20260910` | Google | $1.20 | 77 tok/s | DeepInfra | 33 |
| `~z-ai/glm-flash-latest` | Fireworks | $0.50 | 28 tok/s | Relace | 33 |
| `z-ai/glm-5.3-flash-20260826` | Fireworks | $0.50 | 33 tok/s | Relace | 32 |
| `z-ai/glm-5.3-flash-20260826` | Sail Research | $0.62 | 41 tok/s | Relace | 31 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-11-06` and `2026-11-19`,
**100.00%** of 1 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.79 | -1.10 to -0.48 | 0.515 | 92 | yes |
| **all** | request weighted | -0.47 | -1.01 to +0.08 | 0.066 | 466 | no |
| **conversational** | request weighted | -0.33 | -0.72 to +0.06 | 0.052 | 286 | no |
| **extractive** | request weighted | -0.92 | -1.29 to -0.55 | 0.525 | 27 | yes |
| **output_heavy** | request weighted | -0.24 | -0.48 to -0.00 | 0.114 | 61 | yes |
| **agentic** | unweighted | -0.66 | -1.04 to -0.29 | 0.113 | 92 | yes |
| **all** | unweighted | -0.60 | -0.83 to -0.37 | 0.054 | 466 | yes |
| **conversational** | unweighted | -0.73 | -0.97 to -0.49 | 0.118 | 286 | yes |
| **extractive** | unweighted | -0.02 | -1.13 to +1.10 | 0.000 | 27 | no |
| **output_heavy** | unweighted | -0.51 | -0.97 to -0.04 | 0.056 | 61 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.66, interval
-1.04 to -0.29, straddling zero). Weighting by requests, the
elasticity is **-0.79** (-1.10 to -0.48) and
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
| ≥2 days silent | 80 | 420 | 91.7% | 82.4% |
| ≥3 days silent | 66 | 434 | 94.2% | 85.8% |
| ≥7 days silent | 52 | 448 | 96.3% | 88.2% |
| ≥14 days silent | 38 | 462 | 97.7% | 91.8% |

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
