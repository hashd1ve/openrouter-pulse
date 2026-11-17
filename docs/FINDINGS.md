# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-11-17` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 766 model-variants, 853.81 T
tokens and 40.46 B requests over the trailing 30 days.


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
| **agentic** | 100 | 679.35 T | 79.6% | 58.2 | 59,678 | large contexts, terse output, very large interactions |
| **conversational** | 316 | 113.96 T | 13.3% | 10.0 | 4,009 | moderate context per output token, human-sized interactions |
| **extractive** | 47 | 55.49 T | 6.5% | 41.7 | 5,090 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 180 | 4.75 T | 0.6% | — | 42 | insufficient data to classify |
| **output_heavy** | 123 | 257.05 B | 0.0% | 0.4 | 4,424 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **79.6% of all tokens**
while being 100 of 766 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
13.3%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `scaledown/classify-1-20260928` | 2,975.7 | 7,586 | 14.48 B | extractive |
| `upstage/solar-decide-20260928` | 2,231.8 | 4,833 | 11.53 B | extractive |
| `upstage/solar-decide-flash-20261008` | 1,634.8 | 3,173 | 5.65 B | extractive |
| `microsoft/microsoft-decision-1-20261009` | 738.9 | 2,247 | 118.26 B | extractive |
| `perplexity/pplx-decider-flash-v1.2-20261016` | 681.1 | 2,031 | 108.12 B | extractive |
| `perplexity/pplx-decider-v1.2-20261016` | 511.4 | 1,924 | 1.47 T | extractive |
| `inception/mercury-decide-20260930` | 469.2 | 667 | 88.99 B | extractive |
| `inception/mercury-decide-20260930` | 397.0 | 6,253 | 107.39 B | extractive |
| `baseten/mammoth-1-20261021` | 393.2 | 667 | 21.90 B | extractive |
| `togethercomputer/tev1-4b-experimental-20260923` | 376.6 | 1,834 | 3.53 B | extractive |

**Why both axes.** The top of this ranking is `scaledown/classify-1-20260928` at
2,975.7 tokens of context per token written, but its interactions
average only 7,586 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `stepfun/step-5-preview-20261008`: 214.4 tokens of context per token
written, in interactions averaging 256,765 tokens, which
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
median of **1.00** with a p25–p75 range of 0.74–1.22.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 15 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **2.31×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `tencent/hy-mt2-1.8b-20260521` | 8.67× | 272.21 M | 89 | conversational |
| `tencent/hy-mt2-7b-20260521` | 8.02× | 293.14 M | 90 | conversational |
| `qwen/qwen3-14b-04-28` | 5.84× | 14.85 B | 568 | conversational |
| `particle-ai/particle-1-20261027` | 4.22× | 463.69 B | 20 | agentic |
| `moonshotai/kimi-k2` | 3.14× | 7.86 B | 494 | conversational |
| `mistralai/ministral-8b-2512` | 3.10× | 21.69 B | 350 | conversational |
| `meta/muse-glimmer-30b-20260810` | 2.86× | 77.12 B | 100 | conversational |
| `openai/gpt-oss-20b` | 2.84× | 2.91 B | 469 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `google/gemini-3.6-flash-20260721` | 0.01× | 4.99 B | 119 | conversational |
| `tencent/hy3-20260706` | 0.02× | 10.97 T | 134 | agentic |
| `tencent/hy4-preview-20260827` | 0.02× | 22.59 T | 81 | agentic |
| `openai/gpt-5-nano-2025-08-07` | 0.02× | 9.75 B | 467 | conversational |
| `thinkingmachines/inkling-small-20260730` | 0.04× | 49.83 B | 110 | conversational |
| `stepfun/step-3.7-flash-20260528` | 0.07× | 871.30 B | 173 | agentic |
| `openai/gpt-6-sol-20260922` | 0.09× | 3.52 B | 56 | conversational |
| `deepseek/deepseek-v4.1-flash-20260910` | 0.16× | 28.47 B | 68 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$358.4 M per month** across
491 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 7.6% | 34.0% | 4.46x |
| `openai` | 9.5% | 17.4% | 1.82x |
| `deepseek` | 38.0% | 10.4% | 0.27x |
| `tencent` | 8.2% | 9.6% | 1.18x |
| `stepfun` | 3.1% | 6.9% | 2.26x |
| `moonshotai` | 2.3% | 6.1% | 2.58x |
| `google` | 3.4% | 6.0% | 1.76x |
| `z-ai` | 9.6% | 2.5% | 0.26x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**2,772**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **48.7%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.937** by value. Both are extreme; a
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
**6.72%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 6.92% |
| **extractive** | 1.73% |
| **conversational** | 1.63% |
| **output_heavy** | 1.21% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,288 endpoints serving multi-provider models,
**905 are dominated** (70.3%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `deepseek/deepseek-v4.1-flash-20261017` | Near AI | $1.20 | 38 tok/s | Sail Research | 46 |
| `~deepseek/deepseek-flash-latest` | Near AI | $1.20 | 41 tok/s | Sail Research | 45 |
| `z-ai/glm-5.3-flash-20260826` | Near AI | $0.50 | 23 tok/s | Relace | 35 |
| `~z-ai/glm-flash-latest` | Near AI | $0.50 | 23 tok/s | Relace | 34 |
| `z-ai/glm-5.3-flash-20260826` | AtlasCloud | $0.50 | 29 tok/s | Relace | 34 |
| `~z-ai/glm-flash-latest` | Sail Research | $0.62 | 38 tok/s | Relace | 33 |
| `~z-ai/glm-flash-latest` | AtlasCloud | $0.50 | 34 tok/s | Relace | 33 |
| `z-ai/glm-5.3-flash-20260826` | Sail Research | $0.62 | 48 tok/s | Relace | 31 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-11-16` and `2026-11-17`,
**0.51%** of 584 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.37 | -0.65 to -0.08 | 0.142 | 84 | yes |
| **all** | request weighted | -0.22 | -0.59 to +0.16 | 0.016 | 452 | no |
| **conversational** | request weighted | -0.28 | -0.66 to +0.10 | 0.041 | 285 | no |
| **extractive** | request weighted | -1.06 | -1.40 to -0.72 | 0.610 | 27 | yes |
| **output_heavy** | request weighted | -0.30 | -0.46 to -0.15 | 0.196 | 56 | yes |
| **agentic** | unweighted | -0.55 | -0.90 to -0.20 | 0.099 | 84 | yes |
| **all** | unweighted | -0.56 | -0.80 to -0.32 | 0.047 | 452 | yes |
| **conversational** | unweighted | -0.64 | -0.90 to -0.38 | 0.082 | 285 | yes |
| **extractive** | unweighted | +0.02 | -0.98 to +1.03 | 0.000 | 27 | no |
| **output_heavy** | unweighted | -0.56 | -1.09 to -0.03 | 0.061 | 56 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.55, interval
-0.90 to -0.20, straddling zero). Weighting by requests, the
elasticity is **-0.37** (-0.65 to -0.08) and
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
| ≥2 days silent | 81 | 411 | 92.2% | 83.3% |
| ≥3 days silent | 73 | 419 | 93.0% | 84.4% |
| ≥7 days silent | 52 | 440 | 96.8% | 90.2% |
| ≥14 days silent | 36 | 456 | 98.6% | 93.7% |

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
