# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-11-03` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 736 model-variants, 770.84 T
tokens and 37.76 B requests over the trailing 30 days.


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
| **agentic** | 91 | 547.17 T | 71.0% | 59.2 | 57,621 | large contexts, terse output, very large interactions |
| **conversational** | 319 | 168.49 T | 21.9% | 9.8 | 3,918 | moderate context per output token, human-sized interactions |
| **extractive** | 41 | 50.97 T | 6.6% | 45.9 | 4,917 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 171 | 4.01 T | 0.5% | — | 33 | insufficient data to classify |
| **output_heavy** | 114 | 198.28 B | 0.0% | 0.3 | 4,150 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **71.0% of all tokens**
while being 91 of 736 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
21.9%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `upstage/solar-decide-20260928` | 2,162.5 | 4,917 | 19.78 B | extractive |
| `scaledown/classify-1-20260928` | 2,124.4 | 6,816 | 15.96 B | extractive |
| `upstage/solar-decide-flash-20261008` | 1,461.2 | 3,410 | 10.05 B | extractive |
| `perplexity/pplx-decider-flash-v1.2-20261016` | 1,176.7 | 3,283 | 69.35 B | extractive |
| `perplexity/pplx-decider-v1-27b-20261001` | 1,145.1 | 4,599 | 8.96 B | extractive |
| `perplexity/pplx-decider-v1.1-27b-20261006` | 1,141.1 | 3,834 | 257.20 B | extractive |
| `perplexity/pplx-decider-v1.2-20261016` | 504.4 | 1,986 | 545.71 B | extractive |
| `microsoft/microsoft-decision-1-20261009` | 493.2 | 1,447 | 72.04 B | extractive |
| `togethercomputer/tev1-4b-experimental-20260923` | 459.7 | 2,467 | 7.32 B | extractive |
| `inception/mercury-decide-20260930` | 399.7 | 801 | 92.06 B | extractive |

**Why both axes.** The top of this ranking is `upstage/solar-decide-20260928` at
2,162.5 tokens of context per token written, but its interactions
average only 4,917 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `stepfun/step-5-preview-20261008`: 192.7 tokens of context per token
written, in interactions averaging 211,615 tokens, which
is 43× larger.
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
median of **0.92** with a p25–p75 range of 0.65–1.11.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 20 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.58×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-5.6-luna-20260709` | 3.54× | 11.12 T | 117 | extractive |
| `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning-20260428` | 2.98× | 209.61 B | 189 | conversational |
| `stepfun/step-3.7-flash-20260528` | 2.79× | 931.75 B | 159 | agentic |
| `qwen/qwen3-coder-30b-a3b-instruct` | 2.60× | 32.99 B | 460 | conversational |
| `google/gemini-3.8-flash-20260902` | 2.53× | 18.41 B | 62 | output_heavy |
| `openai/gpt-oss-20b` | 2.46× | 3.82 B | 455 | conversational |
| `google/gemini-nano-banana-2.1-20261006` | 2.25× | 7.75 B | 28 | output_heavy |
| `qwen/qwen3.5-9b-20260310` | 2.24× | 293.30 B | 238 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `recursive/flint-v1.0-20261021` | 0.00× | 242.98 B | 13 | agentic |
| `openai/gpt-5-nano-2025-08-07` | 0.00× | 10.26 B | 453 | conversational |
| `google/gemini-3.6-flash-20260721` | 0.02× | 9.00 B | 105 | conversational |
| `google/gemma-2-27b-it` | 0.08× | 861.31 M | 843 | conversational |
| `xiaomi/mimo-v2.5-20260422` | 0.09× | 1.50 T | 195 | agentic |
| `inclusionai/ling-3.0-flash-vl-20260910` | 0.09× | 88.40 B | 54 | conversational |
| `google/gemini-3.7-flash-20260813` | 0.09× | 6.99 B | 82 | output_heavy |
| `nex-agi/nex-n2.5-mini-20260908` | 0.11× | 29.56 B | 56 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$399.2 M per month** across
478 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 7.8% | 42.2% | 5.43x |
| `openai` | 10.0% | 13.7% | 1.37x |
| `tencent` | 6.5% | 8.2% | 1.25x |
| `stepfun` | 4.3% | 7.9% | 1.85x |
| `deepseek` | 32.9% | 7.3% | 0.22x |
| `google` | 3.8% | 5.6% | 1.49x |
| `z-ai` | 11.0% | 3.7% | 0.33x |
| `moonshotai` | 1.8% | 3.0% | 1.71x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,369**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **55.3%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.944** by value. Both are extreme; a
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
**6.71%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 6.95% |
| **conversational** | 1.76% |
| **extractive** | 1.68% |
| **output_heavy** | 0.90% |

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
**881 are dominated** (72.0%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `~deepseek/deepseek-flash-latest` | Phala | $1.20 | 73 tok/s | Particle AI | 33 |
| `deepseek/deepseek-v4.1-flash-20261017` | Phala | $1.20 | 78 tok/s | Particle AI | 32 |
| `z-ai/glm-5.3-flash-20260826` | Near AI | $0.50 | 31 tok/s | Wafer | 30 |
| `~z-ai/glm-flash-latest` | Near AI | $0.50 | 31 tok/s | Wafer | 30 |
| `z-ai/glm-5.3-20260816` | AtlasCloud | $4.40 | 52 tok/s | Baidu | 30 |
| `~z-ai/glm-latest` | AtlasCloud | $4.40 | 52 tok/s | Baidu | 30 |
| `z-ai/glm-5.3-20260816` | Z.AI | $4.40 | 53 tok/s | Baidu | 29 |
| `~z-ai/glm-latest` | Z.AI | $4.40 | 53 tok/s | Baidu | 29 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-11-02` and `2026-11-03`,
**0.89%** of 564 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.64 | -0.85 to -0.42 | 0.451 | 78 | yes |
| **all** | request weighted | -0.39 | -0.82 to +0.04 | 0.055 | 451 | no |
| **conversational** | request weighted | -0.52 | -1.15 to +0.10 | 0.078 | 298 | no |
| **extractive** | request weighted | -1.10 | -1.41 to -0.80 | 0.650 | 22 | yes |
| **output_heavy** | request weighted | -0.07 | -0.39 to +0.25 | 0.008 | 53 | no |
| **agentic** | unweighted | -0.37 | -0.77 to +0.04 | 0.043 | 78 | no |
| **all** | unweighted | -0.79 | -1.09 to -0.49 | 0.070 | 451 | yes |
| **conversational** | unweighted | -0.58 | -0.85 to -0.31 | 0.049 | 298 | yes |
| **extractive** | unweighted | -0.46 | -1.44 to +0.52 | 0.044 | 22 | no |
| **output_heavy** | unweighted | -1.56 | -2.30 to -0.83 | 0.210 | 53 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.37, interval
-0.77 to +0.04, straddling zero). Weighting by requests, the
elasticity is **-0.64** (-0.85 to -0.42) and
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
| ≥2 days silent | 82 | 397 | 94.0% | 85.2% |
| ≥3 days silent | 82 | 397 | 94.0% | 85.2% |
| ≥7 days silent | 61 | 418 | 97.1% | 91.0% |
| ≥14 days silent | 41 | 438 | 97.3% | 93.8% |

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
