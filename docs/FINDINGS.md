# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-11-16` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 767 model-variants, 839.81 T
tokens and 40.10 B requests over the trailing 30 days.


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
| **agentic** | 97 | 666.46 T | 79.4% | 60.2 | 60,104 | large contexts, terse output, very large interactions |
| **conversational** | 315 | 113.56 T | 13.5% | 10.0 | 4,213 | moderate context per output token, human-sized interactions |
| **extractive** | 48 | 54.86 T | 6.5% | 44.3 | 4,960 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 182 | 4.68 T | 0.6% | — | 42 | insufficient data to classify |
| **output_heavy** | 125 | 252.00 B | 0.0% | 0.4 | 4,430 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **79.4% of all tokens**
while being 97 of 767 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
13.5%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `scaledown/classify-1-20260928` | 2,591.6 | 7,544 | 15.51 B | extractive |
| `upstage/solar-decide-20260928` | 2,190.8 | 4,678 | 11.66 B | extractive |
| `upstage/solar-decide-flash-20261008` | 1,620.0 | 3,097 | 5.77 B | extractive |
| `perplexity/pplx-decider-flash-v1.2-20261016` | 824.6 | 1,994 | 105.19 B | extractive |
| `microsoft/microsoft-decision-1-20261009` | 786.5 | 2,212 | 116.77 B | extractive |
| `perplexity/pplx-decider-v1.2-20261016` | 515.7 | 1,911 | 1.41 T | extractive |
| `inception/mercury-decide-20260930` | 493.1 | 701 | 98.01 B | extractive |
| `perplexity/pplx-decider-v1.1-27b-20261006` | 444.1 | 793 | 7.40 B | extractive |
| `inception/mercury-decide-20260930` | 397.4 | 6,127 | 109.05 B | extractive |
| `baseten/mammoth-1-20261021` | 391.3 | 658 | 20.73 B | extractive |

**Why both axes.** The top of this ranking is `scaledown/classify-1-20260928` at
2,591.6 tokens of context per token written, but its interactions
average only 7,544 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `stepfun/step-5-preview-20261008`: 214.1 tokens of context per token
written, in interactions averaging 256,508 tokens, which
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


Across 262 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.75** with a p25–p75 range of 0.57–0.99.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 13 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **2.14×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `deepseek/deepseek-v4.1-flash-20261017` | 9.49× | 10.91 B | 30 | output_heavy |
| `particle-ai/particle-1-20261027` | 8.84× | 365.75 B | 19 | agentic |
| `nvidia/nemotron-3-nano-30b-a3b` | 4.44× | 27.64 B | 337 | conversational |
| `nvidia/nemotron-3-super-120b-a12b-20230311` | 3.10× | 48.89 B | 250 | conversational |
| `mistralai/ministral-14b-2512` | 3.00× | 12.38 B | 349 | conversational |
| `meta-llama/llama-3.2-1b-instruct` | 2.68× | 754.83 M | 782 | conversational |
| `minimax/minimax-m2.7-20260318` | 2.39× | 86.69 B | 243 | conversational |
| `qwen/qwen3-30b-a3b-04-28` | 2.23× | 11.61 B | 567 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-5-nano-2025-08-07` | 0.01× | 9.76 B | 466 | conversational |
| `tencent/hy4-preview-20260827` | 0.01× | 23.47 T | 80 | agentic |
| `openai/gpt-5.6-luna-20260709` | 0.02× | 67.66 B | 130 | conversational |
| `z-ai/glm-5.3-flash-20260826` | 0.05× | 41.41 B | 82 | conversational |
| `stepfun/step-3.7-flash-20260528` | 0.07× | 871.07 B | 172 | agentic |
| `openai/gpt-oss-20b` | 0.09× | 2.78 B | 468 | conversational |
| `openai/gpt-6-sol-20260922` | 0.13× | 3.89 B | 55 | conversational |
| `anthropic/claude-opus-5-20260723` | 0.15× | 396.41 M | 115 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$430.2 M per month** across
489 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 7.6% | 44.4% | 5.81x |
| `openai` | 9.6% | 14.9% | 1.56x |
| `tencent` | 8.1% | 8.1% | 1.00x |
| `moonshotai` | 2.3% | 6.1% | 2.62x |
| `google` | 3.4% | 5.8% | 1.71x |
| `deepseek` | 37.9% | 5.7% | 0.15x |
| `stepfun` | 3.0% | 5.5% | 1.85x |
| `z-ai` | 9.8% | 3.1% | 0.32x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,041**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **52.0%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.937** by value. Both are extreme; a
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
**6.72%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 6.83% |
| **extractive** | 1.74% |
| **conversational** | 1.69% |
| **output_heavy** | 1.30% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,256 endpoints serving multi-provider models,
**893 are dominated** (71.1%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-flash-20260826` | Sail Research | $0.62 | 29 tok/s | Relace | 37 |
| `~z-ai/glm-flash-latest` | Sail Research | $0.62 | 29 tok/s | Relace | 37 |
| `z-ai/glm-5.3-flash-20260826` | AtlasCloud | $0.50 | 32 tok/s | Relace | 35 |
| `~z-ai/glm-flash-latest` | AtlasCloud | $0.50 | 32 tok/s | Relace | 35 |
| `~deepseek/deepseek-flash-latest` | Nebius | $1.20 | 74 tok/s | Ionstream | 35 |
| `deepseek/deepseek-v4.1-flash-20261017` | Nebius | $1.20 | 83 tok/s | Ionstream | 33 |
| `z-ai/glm-5.3-flash-20260826` | Near AI | $0.50 | 34 tok/s | Relace | 32 |
| `~z-ai/glm-flash-latest` | Near AI | $0.50 | 34 tok/s | Relace | 32 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-11-15` and `2026-11-16`,
**1.54%** of 585 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.62 | -0.94 to -0.31 | 0.348 | 81 | yes |
| **all** | request weighted | -0.34 | -0.71 to +0.03 | 0.038 | 452 | no |
| **conversational** | request weighted | -0.29 | -0.68 to +0.09 | 0.049 | 285 | no |
| **extractive** | request weighted | -1.00 | -1.32 to -0.69 | 0.550 | 28 | yes |
| **output_heavy** | request weighted | -0.20 | -0.46 to +0.05 | 0.100 | 58 | no |
| **agentic** | unweighted | -0.55 | -0.93 to -0.18 | 0.100 | 81 | yes |
| **all** | unweighted | -0.54 | -0.78 to -0.30 | 0.045 | 452 | yes |
| **conversational** | unweighted | -0.67 | -0.93 to -0.40 | 0.091 | 285 | yes |
| **extractive** | unweighted | +0.16 | -0.64 to +0.96 | 0.004 | 28 | no |
| **output_heavy** | unweighted | -0.50 | -0.99 to -0.01 | 0.052 | 58 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.55, interval
-0.93 to -0.18, straddling zero). Weighting by requests, the
elasticity is **-0.62** (-0.94 to -0.31) and
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
| ≥2 days silent | 76 | 414 | 92.3% | 83.8% |
| ≥3 days silent | 72 | 418 | 93.2% | 84.6% |
| ≥7 days silent | 50 | 440 | 97.0% | 90.4% |
| ≥14 days silent | 36 | 454 | 98.6% | 93.7% |

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
