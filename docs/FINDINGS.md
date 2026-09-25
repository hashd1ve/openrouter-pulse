# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-09-25` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 656 model-variants, 530.01 T
tokens and 24.58 B requests over the trailing 30 days.


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
| **agentic** | 100 | 407.57 T | 76.9% | 53.4 | 51,248 | large contexts, terse output, very large interactions |
| **conversational** | 325 | 119.35 T | 22.5% | 9.2 | 4,123 | moderate context per output token, human-sized interactions |
| **unclassified** | 122 | 2.43 T | 0.5% | — | 27 | insufficient data to classify |
| **extractive** | 17 | 527.28 B | 0.1% | 40.2 | 7,930 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 92 | 131.46 B | 0.0% | 0.4 | 4,524 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **76.9% of all tokens**
while being 100 of 656 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
22.5%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 238.0 | 814 | 9.13 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 206.6 | 128,892 | 17.94 T | agentic |
| `xiaomi/mimo-v2.5-20260422` | 126.0 | 68,475 | 25.59 T | agentic |
| `thinkingmachines/inkling-small-20260730` | 122.9 | 57,461 | 480.36 B | agentic |
| `poolside/laguna-s-2.1-20260720` | 119.0 | 83,058 | 5.28 T | agentic |
| `minimax/minimax-m3-20260531` | 119.0 | 76,823 | 8.10 T | agentic |
| `z-ai/glm-5.3-flashx-20260918` | 113.2 | 83,159 | 213.63 B | agentic |
| `tencent/hy4-preview-20260827` | 112.5 | 116,379 | 54.01 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 106.2 | 95,128 | 246.90 B | agentic |
| `deepseek/deepseek-v4-flash-20260731` | 105.4 | 98,351 | 1.09 T | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
238.0 tokens of context per token written, but its interactions
average only 814 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 206.6 tokens of context per token
written, in interactions averaging 128,892 tokens, which
is 158× larger.
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


Across 237 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.94** with a p25–p75 range of 0.74–1.17.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 18 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.40×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `z-ai/glm-5.3-flash-20260826` | 5.81× | 5.33 B | 30 | output_heavy |
| `inclusionai/ling-3.0-flash-vl-20260910` | 4.12× | 7.54 B | 15 | conversational |
| `qwen/qwen3-next-80b-a3b-instruct-2509` | 3.66× | 47.82 B | 379 | conversational |
| `nvidia/nemotron-3.5-lightning-20260807` | 2.63× | 192.35 B | 45 | conversational |
| `bytedance-seed/seed-2.0-lite-20260309` | 2.09× | 6.06 B | 199 | conversational |
| `mistralai/mistral-medium-3.5-20260430` | 1.93× | 21.78 B | 148 | conversational |
| `anthropic/claude-fable-5.1-20260831` | 1.73× | 1.49 T | 24 | agentic |
| `qwen/qwen3.8-flash-20260826` | 1.72× | 1.32 T | 30 | agentic |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `mistralai/mistral-large-2512` | 0.01× | 25.26 B | 298 | conversational |
| `google/gemini-3.8-flash-20260902` | 0.04× | 12.16 B | 23 | conversational |
| `tencent/hy-mt2-1.8b-20260521` | 0.08× | 3.01 B | 36 | conversational |
| `stepfun/step-3.7-flash-20260528` | 0.10× | 899.37 B | 120 | agentic |
| `meta/muse-spark-1.1-20260709` | 0.11× | 51.55 B | 71 | agentic |
| `aion-labs/aion-3.0-20260707` | 0.14× | 39.44 B | 80 | conversational |
| `meta/muse-spark-1.2-contributor-20260805` | 0.14× | 466.06 B | 35 | conversational |
| `google/gemini-3.7-flash-20260813` | 0.15× | 29.18 B | 43 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$287.9 M per month** across
476 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 4.1% | 26.3% | 6.42x |
| `openai` | 15.0% | 24.9% | 1.66x |
| `tencent` | 13.9% | 16.8% | 1.21x |
| `moonshotai` | 1.5% | 8.0% | 5.17x |
| `z-ai` | 14.8% | 5.5% | 0.37x |
| `deepseek` | 21.3% | 5.4% | 0.25x |
| `google` | 6.0% | 4.4% | 0.74x |
| `qwen` | 1.6% | 1.9% | 1.17x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,074**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **52.7%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.938** by value. Both are extreme; a
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
**6.43%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.60% |
| **extractive** | 4.60% |
| **output_heavy** | 1.75% |
| **conversational** | 1.71% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,104 endpoints serving multi-provider models,
**764 are dominated** (69.2%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-flash-20260826` | Sail Research | $0.60 | 9 tok/s | InferenceNet | 30 |
| `~z-ai/glm-flash-latest` | Sail Research | $0.60 | 9 tok/s | InferenceNet | 30 |
| `z-ai/glm-5.3-flash-20260826` | Sail Research | $0.60 | 11 tok/s | InferenceNet | 29 |
| `~z-ai/glm-flash-latest` | Sail Research | $0.60 | 11 tok/s | InferenceNet | 29 |
| `z-ai/glm-5.3-20260816` | BaseTen | $4.40 | 44 tok/s | Baidu | 28 |
| `z-ai/glm-5.3-flash-20260826` | Io Net | $0.50 | 6 tok/s | InferenceNet | 28 |
| `~z-ai/glm-flash-latest` | Io Net | $0.50 | 6 tok/s | InferenceNet | 28 |
| `~z-ai/glm-latest` | BaseTen | $4.40 | 47 tok/s | Baidu | 27 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-09-24` and `2026-09-25`,
**0.94%** of 533 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.41 | -0.64 to -0.19 | 0.169 | 86 | yes |
| **all** | request weighted | -0.07 | -0.50 to +0.36 | 0.002 | 446 | no |
| **conversational** | request weighted | -0.48 | -0.96 to +0.01 | 0.058 | 303 | no |
| **extractive** | request weighted | +0.71 | +0.49 to +0.94 | 0.608 | 15 | yes |
| **output_heavy** | request weighted | -0.10 | -0.37 to +0.18 | 0.015 | 42 | no |
| **agentic** | unweighted | -0.55 | -0.90 to -0.21 | 0.099 | 86 | yes |
| **all** | unweighted | -0.84 | -1.09 to -0.58 | 0.101 | 446 | yes |
| **conversational** | unweighted | -1.15 | -1.44 to -0.86 | 0.191 | 303 | yes |
| **extractive** | unweighted | -0.08 | -0.81 to +0.65 | 0.001 | 15 | no |
| **output_heavy** | unweighted | -0.17 | -0.71 to +0.36 | 0.013 | 42 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.55, interval
-0.90 to -0.21, straddling zero). Weighting by requests, the
elasticity is **-0.41** (-0.64 to -0.19) and
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
| ≥2 days silent | 80 | 397 | 88.5% | 82.3% |
| ≥3 days silent | 68 | 409 | 90.3% | 84.8% |
| ≥7 days silent | 55 | 422 | 92.5% | 87.7% |
| ≥14 days silent | 45 | 432 | 93.9% | 90.0% |

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
