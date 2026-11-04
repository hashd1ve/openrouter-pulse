# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-11-04` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 741 model-variants, 781.65 T
tokens and 38.26 B requests over the trailing 30 days.


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
| **agentic** | 93 | 554.39 T | 70.9% | 59.7 | 58,160 | large contexts, terse output, very large interactions |
| **conversational** | 320 | 171.43 T | 21.9% | 9.8 | 3,881 | moderate context per output token, human-sized interactions |
| **extractive** | 41 | 51.56 T | 6.6% | 45.8 | 4,788 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 173 | 4.08 T | 0.5% | — | 35 | insufficient data to classify |
| **output_heavy** | 114 | 190.48 B | 0.0% | 0.3 | 4,349 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **70.9% of all tokens**
while being 93 of 741 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
21.9%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `scaledown/classify-1-20260928` | 2,426.7 | 7,666 | 18.69 B | extractive |
| `upstage/solar-decide-20260928` | 2,101.4 | 4,756 | 19.29 B | extractive |
| `upstage/solar-decide-flash-20261008` | 1,456.6 | 3,382 | 10.15 B | extractive |
| `perplexity/pplx-decider-v1.1-27b-20261006` | 1,141.1 | 3,834 | 257.20 B | extractive |
| `perplexity/pplx-decider-v1-27b-20261001` | 1,092.3 | 4,542 | 7.75 B | extractive |
| `perplexity/pplx-decider-flash-v1.2-20261016` | 1,043.9 | 2,282 | 76.75 B | extractive |
| `perplexity/pplx-decider-v1.2-20261016` | 493.5 | 1,945 | 587.73 B | extractive |
| `microsoft/microsoft-decision-1-20261009` | 488.9 | 1,439 | 73.63 B | extractive |
| `togethercomputer/tev1-4b-experimental-20260923` | 452.5 | 2,404 | 7.34 B | extractive |
| `inception/mercury-decide-20260930` | 400.4 | 785 | 96.96 B | extractive |

**Why both axes.** The top of this ranking is `scaledown/classify-1-20260928` at
2,426.7 tokens of context per token written, but its interactions
average only 7,666 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `stepfun/step-5-preview-20261008`: 193.4 tokens of context per token
written, in interactions averaging 212,820 tokens, which
is 28× larger.
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
median of **0.95** with a p25–p75 range of 0.77–1.20.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 21 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.50×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-6.1-sol-20260929` | 5.64× | 9.60 B | 36 | conversational |
| `qwen/qwen3-32b-04-28` | 3.33× | 65.10 B | 555 | conversational |
| `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning-20260428` | 2.91× | 227.97 B | 190 | conversational |
| `qwen/qwen3-coder-30b-a3b-instruct` | 2.84× | 35.30 B | 461 | conversational |
| `qwen/qwen-plus-2025-01-25` | 2.69× | 6.89 B | 641 | conversational |
| `nvidia/nemotron-3.5-super-vl-20261015` | 2.66× | 538.11 B | 20 | conversational |
| `anthropic/claude-4.8-opus-20260528` | 2.51× | 867.37 B | 161 | agentic |
| `qwen/qwen3.8-flash-20260826` | 2.17× | 2.69 T | 70 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `recursive/flint-v1.0-20261021` | 0.00× | 242.98 B | 14 | agentic |
| `openai/gpt-5-nano-2025-08-07` | 0.00× | 10.24 B | 454 | conversational |
| `xiaomi/mimo-v2.5-20260422` | 0.06× | 1.38 T | 196 | agentic |
| `google/gemini-3.7-flash-20260813` | 0.13× | 6.98 B | 83 | output_heavy |
| `xiaomi/mimo-v2.5-pro-20260422` | 0.13× | 439.89 B | 196 | agentic |
| `openai/gpt-6-sol-20260922` | 0.15× | 4.32 B | 43 | conversational |
| `inclusionai/ling-3.0-flash-vl-20260910` | 0.17× | 83.73 B | 55 | conversational |
| `inclusionai/ling-3.1-flash-20261002` | 0.17× | 1.00 T | 33 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$425.5 M per month** across
481 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 7.9% | 41.8% | 5.32x |
| `openai` | 10.0% | 16.0% | 1.60x |
| `tencent` | 6.6% | 7.8% | 1.19x |
| `stepfun` | 4.4% | 7.7% | 1.76x |
| `deepseek` | 33.7% | 7.2% | 0.21x |
| `google` | 3.8% | 4.4% | 1.18x |
| `z-ai` | 11.1% | 3.5% | 0.31x |
| `moonshotai` | 1.8% | 3.1% | 1.71x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,271**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **54.3%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.944** by value. Both are extreme; a
national income distribution above 0.6 is considered severe.


### The sticker price is not the price

Traffic is overwhelmingly prompt-heavy, and prompt tokens cost less than
completions. Blended across each model's real token mix, the price actually paid
per token is a median **0.34x** the headline output price, so the
sticker overstates unit cost by about **3.0x**.

Anyone comparing models on `$/M output` is getting this wrong.


## 5. The context window arms race is mostly unused

Dividing mean tokens per request by the advertised context length asks how much
of the window the traffic actually touches. Token-weighted across the market:
**6.52%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 6.84% |
| **conversational** | 1.72% |
| **extractive** | 1.65% |
| **output_heavy** | 0.97% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,214 endpoints serving multi-provider models,
**871 are dominated** (71.7%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `deepseek/deepseek-v4.1-flash-20261017` | Crusoe | $1.20 | 29 tok/s | Sail Research | 42 |
| `~deepseek/deepseek-flash-latest` | Crusoe | $1.20 | 29 tok/s | Sail Research | 42 |
| `deepseek/deepseek-v4.1-flash-20261017` | Phala | $1.20 | 72 tok/s | Sail Research | 37 |
| `~deepseek/deepseek-flash-latest` | Phala | $1.20 | 71 tok/s | Sail Research | 37 |
| `deepseek/deepseek-v4.1-flash-20260910` | Crusoe | $1.20 | 44 tok/s | Sail Research | 37 |
| `z-ai/glm-5.3-flash-20260826` | Parasail | $0.50 | 23 tok/s | Relace | 36 |
| `~z-ai/glm-flash-latest` | Parasail | $0.50 | 25 tok/s | Relace | 36 |
| `z-ai/glm-5.3-flash-20260826` | Near AI | $0.50 | 32 tok/s | Relace | 34 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-11-03` and `2026-11-04`,
**1.06%** of 565 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.63 | -0.82 to -0.43 | 0.446 | 80 | yes |
| **all** | request weighted | -0.37 | -0.81 to +0.07 | 0.049 | 453 | no |
| **conversational** | request weighted | -0.55 | -1.20 to +0.09 | 0.087 | 297 | no |
| **extractive** | request weighted | -1.51 | -2.00 to -1.03 | 0.587 | 22 | yes |
| **output_heavy** | request weighted | -0.14 | -0.41 to +0.12 | 0.028 | 54 | no |
| **agentic** | unweighted | -0.46 | -0.84 to -0.07 | 0.061 | 80 | yes |
| **all** | unweighted | -0.82 | -1.12 to -0.52 | 0.070 | 453 | yes |
| **conversational** | unweighted | -0.69 | -0.96 to -0.43 | 0.066 | 297 | yes |
| **extractive** | unweighted | -0.41 | -1.30 to +0.48 | 0.031 | 22 | no |
| **output_heavy** | unweighted | -1.60 | -2.41 to -0.79 | 0.191 | 54 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.46, interval
-0.84 to -0.07, straddling zero). Weighting by requests, the
elasticity is **-0.63** (-0.82 to -0.43) and
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
| ≥2 days silent | 81 | 401 | 94.8% | 86.0% |
| ≥3 days silent | 79 | 403 | 94.8% | 86.0% |
| ≥7 days silent | 62 | 420 | 97.1% | 90.5% |
| ≥14 days silent | 43 | 439 | 97.3% | 93.9% |

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
