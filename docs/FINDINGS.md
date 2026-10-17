# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-10-17` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 717 model-variants, 684.54 T
tokens and 32.31 B requests over the trailing 30 days.


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
| **agentic** | 96 | 568.35 T | 83.0% | 54.9 | 54,747 | large contexts, terse output, very large interactions |
| **conversational** | 324 | 109.66 T | 16.0% | 9.4 | 3,834 | moderate context per output token, human-sized interactions |
| **extractive** | 32 | 3.31 T | 0.5% | 44.6 | 4,889 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 151 | 3.05 T | 0.4% | — | 34 | insufficient data to classify |
| **output_heavy** | 114 | 167.06 B | 0.0% | 0.3 | 3,924 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **83.0% of all tokens**
while being 96 of 717 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
16.0%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `upstage/solar-decide-20260928` | 1,985.6 | 4,701 | 15.24 B | extractive |
| `upstage/solar-decide-flash-20261008` | 1,411.3 | 3,528 | 6.60 B | extractive |
| `perplexity/pplx-decider-v1.1-27b-20261006` | 1,196.6 | 4,325 | 249.80 B | extractive |
| `perplexity/pplx-decider-v1-27b-20261001` | 1,155.6 | 4,655 | 9.10 B | extractive |
| `togethercomputer/tev1-4b-experimental-20260923` | 549.0 | 2,892 | 6.34 B | extractive |
| `inception/mercury-decide-20260930` | 371.1 | 3,204 | 43.15 B | extractive |
| `microsoft/microsoft-decision-1-20261009` | 346.5 | 1,230 | 24.24 B | extractive |
| `meta-llama/llama-guard-4-12b` | 236.6 | 811 | 7.47 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 212.3 | 134,244 | 25.35 T | agentic |
| `inception/mercury-decide-20260930` | 197.4 | 1,014 | 19.39 B | extractive |

**Why both axes.** The top of this ranking is `upstage/solar-decide-20260928` at
1,985.6 tokens of context per token written, but its interactions
average only 4,701 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 212.3 tokens of context per token
written, in interactions averaging 134,244 tokens, which
is 29× larger.
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


Across 252 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.89** with a p25–p75 range of 0.69–1.09.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 25 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.20×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `qwen/qwen3.6-35b-a3b-20260415` | 10.73× | 1.08 T | 173 | conversational |
| `google/gemma-2-27b-it` | 5.84× | 533.06 M | 826 | conversational |
| `inception/mercury-2-20260304` | 3.59× | 10.66 B | 227 | conversational |
| `bytedance-seed/seed-2.0-mini-20260224` | 3.49× | 18.14 B | 233 | conversational |
| `google/gemini-3.8-flash-20260902` | 2.51× | 12.06 B | 45 | conversational |
| `nvidia/nemotron-3.5-content-safety-20260604` | 2.27× | 10.61 B | 135 | conversational |
| `meta-llama/llama-4-scout-17b-16e-instruct` | 2.21× | 55.43 B | 560 | conversational |
| `openai/gpt-6-sol-20260922` | 2.15× | 4.27 B | 25 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `perceptron/perceptron-mk1-20260512` | 0.03× | 6.84 B | 158 | extractive |
| `tencent/hy-mt2-7b-20260521` | 0.05× | 1.31 B | 59 | conversational |
| `tencent/hy-mt2-1.8b-20260521` | 0.07× | 1.52 B | 58 | conversational |
| `stepfun/step-5-preview-20261008` | 0.08× | 20.29 T | 9 | agentic |
| `openai/gpt-5.6-luna-20260709` | 0.09× | 48.62 B | 100 | conversational |
| `google/gemini-3.7-flash-20260813` | 0.10× | 11.61 B | 65 | output_heavy |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 0.10× | 25.35 T | 135 | agentic |
| `inclusionai/ling-3.0-flash-vl-20260910` | 0.13× | 126.98 B | 37 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$299.3 M per month** across
486 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `openai` | 11.0% | 30.3% | 2.76x |
| `anthropic` | 5.3% | 28.5% | 5.33x |
| `tencent` | 7.4% | 11.2% | 1.51x |
| `stepfun` | 3.1% | 6.9% | 2.23x |
| `google` | 4.4% | 5.1% | 1.17x |
| `xiaomi` | 7.3% | 3.4% | 0.47x |
| `z-ai` | 12.0% | 3.3% | 0.27x |
| `deepseek` | 26.2% | 3.2% | 0.12x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,638**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **58.1%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.937** by value. Both are extreme; a
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
**6.59%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.30% |
| **extractive** | 2.34% |
| **conversational** | 1.65% |
| **output_heavy** | 0.43% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,105 endpoints serving multi-provider models,
**755 are dominated** (68.3%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-20260816` | Relace | $19.90 | 28 tok/s | Sail Research | 42 |
| `~z-ai/glm-latest` | Relace | $19.90 | 28 tok/s | Sail Research | 42 |
| `z-ai/glm-5.3-20260816` | Makora | $4.40 | 27 tok/s | Sail Research | 34 |
| `~z-ai/glm-latest` | Makora | $4.40 | 27 tok/s | Sail Research | 34 |
| `z-ai/glm-5.3-20260816` | Fireworks | $4.40 | 45 tok/s | Sail Research | 32 |
| `~z-ai/glm-latest` | Fireworks | $4.40 | 45 tok/s | Sail Research | 32 |
| `deepseek/deepseek-v4.1-flash-20260910` | Baidu | $1.20 | 66 tok/s | Decart | 30 |
| `z-ai/glm-5.3-20260816` | Cloudflare | $4.40 | 47 tok/s | Sail Research | 30 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-10-15` and `2026-10-17`,
**2.90%** of 551 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.55 | -0.81 to -0.28 | 0.237 | 81 | yes |
| **all** | request weighted | -0.09 | -0.35 to +0.18 | 0.002 | 451 | no |
| **conversational** | request weighted | -0.30 | -0.65 to +0.04 | 0.034 | 294 | no |
| **extractive** | request weighted | +0.57 | -0.01 to +1.15 | 0.265 | 19 | no |
| **output_heavy** | request weighted | -0.25 | -0.43 to -0.07 | 0.109 | 57 | yes |
| **agentic** | unweighted | -0.43 | -0.77 to -0.09 | 0.052 | 81 | yes |
| **all** | unweighted | -0.92 | -1.25 to -0.60 | 0.073 | 451 | yes |
| **conversational** | unweighted | -0.85 | -1.20 to -0.51 | 0.086 | 294 | yes |
| **extractive** | unweighted | +0.36 | -0.23 to +0.96 | 0.070 | 19 | no |
| **output_heavy** | unweighted | -1.13 | -2.00 to -0.26 | 0.080 | 57 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.43, interval
-0.77 to -0.09, straddling zero). Weighting by requests, the
elasticity is **-0.55** (-0.81 to -0.28) and
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
| ≥2 days silent | 75 | 410 | 92.0% | 84.5% |
| ≥3 days silent | 69 | 416 | 92.8% | 86.2% |
| ≥7 days silent | 62 | 423 | 93.9% | 87.3% |
| ≥14 days silent | 23 | 462 | 95.5% | 94.7% |

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
