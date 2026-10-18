# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-10-18` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 719 model-variants, 682.93 T
tokens and 32.60 B requests over the trailing 30 days.


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
| **agentic** | 95 | 566.03 T | 82.9% | 53.7 | 54,202 | large contexts, terse output, very large interactions |
| **conversational** | 327 | 109.25 T | 16.0% | 9.2 | 3,884 | moderate context per output token, human-sized interactions |
| **extractive** | 33 | 4.41 T | 0.6% | 45.3 | 4,934 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 151 | 3.07 T | 0.4% | — | 33 | insufficient data to classify |
| **output_heavy** | 113 | 168.03 B | 0.0% | 0.3 | 4,033 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **82.9% of all tokens**
while being 95 of 719 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
16.0%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `upstage/solar-decide-20260928` | 1,958.3 | 4,563 | 15.47 B | extractive |
| `scaledown/classify-1-20260928` | 1,531.3 | 6,070 | 6.52 B | extractive |
| `upstage/solar-decide-flash-20261008` | 1,403.6 | 3,412 | 6.79 B | extractive |
| `perplexity/pplx-decider-v1-27b-20261001` | 1,155.6 | 4,655 | 9.10 B | extractive |
| `perplexity/pplx-decider-v1.1-27b-20261006` | 1,141.1 | 3,834 | 257.20 B | extractive |
| `perplexity/pplx-decider-flash-v1.2-20261016` | 648.8 | 2,191 | 2.88 B | extractive |
| `togethercomputer/tev1-4b-experimental-20260923` | 541.5 | 2,787 | 6.39 B | extractive |
| `inception/mercury-decide-20260930` | 372.9 | 3,180 | 44.83 B | extractive |
| `perplexity/pplx-decider-v1.2-20261016` | 350.3 | 1,556 | 6.37 B | extractive |
| `microsoft/microsoft-decision-1-20261009` | 346.5 | 1,207 | 25.83 B | extractive |

**Why both axes.** The top of this ranking is `upstage/solar-decide-20260928` at
1,958.3 tokens of context per token written, but its interactions
average only 4,563 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 211.4 tokens of context per token
written, in interactions averaging 134,097 tokens, which
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
median of **0.74** with a p25–p75 range of 0.52–1.01.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 24 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.18×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-6-luna-20260922` | 5.75× | 208.87 B | 26 | conversational |
| `inception/mercury-2-20260304` | 5.17× | 12.48 B | 228 | conversational |
| `qwen/qwen3.6-35b-a3b-20260415` | 3.42× | 1.21 T | 174 | extractive |
| `deepseek/deepseek-v4.1-flash-20260910` | 3.26× | 12.44 B | 38 | output_heavy |
| `xiaomi/mimo-v2.6-pro-ultraspeed-20260921` | 3.05× | 405.94 B | 27 | agentic |
| `microsoft/phi-4` | 2.70× | 6.87 B | 646 | conversational |
| `openai/gpt-6-sol-20260922` | 2.09× | 4.64 B | 26 | conversational |
| `qwen/qwen-2.5-72b-instruct` | 1.84× | 11.41 B | 759 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `google/gemini-3.7-flash-20260813` | 0.00× | 11.57 B | 66 | output_heavy |
| `google/gemini-3.1-flash-lite-20260507` | 0.00× | 22.34 B | 164 | conversational |
| `google/gemini-2.5-flash` | 0.00× | 6.54 B | 488 | conversational |
| `stepfun/step-5-preview-20261008` | 0.00× | 20.30 T | 10 | agentic |
| `google/gemini-3.8-flash-20260902` | 0.03× | 11.73 B | 46 | conversational |
| `tencent/hy-mt2-7b-20260521` | 0.04× | 1.17 B | 60 | conversational |
| `perceptron/perceptron-mk1-20260512` | 0.04× | 6.83 B | 159 | extractive |
| `tencent/hy-mt2-1.8b-20260521` | 0.05× | 1.30 B | 59 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$330.5 M per month** across
488 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 5.5% | 38.0% | 6.92x |
| `openai` | 10.8% | 23.6% | 2.18x |
| `tencent` | 7.2% | 9.9% | 1.37x |
| `stepfun` | 3.1% | 6.2% | 2.01x |
| `deepseek` | 26.5% | 4.6% | 0.17x |
| `google` | 4.4% | 3.9% | 0.90x |
| `xiaomi` | 7.4% | 3.2% | 0.43x |
| `z-ai` | 11.9% | 3.1% | 0.26x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,546**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **56.8%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.940** by value. Both are extreme; a
national income distribution above 0.6 is considered severe.


### The sticker price is not the price

Traffic is overwhelmingly prompt-heavy, and prompt tokens cost less than
completions. Blended across each model's real token mix, the price actually paid
per token is a median **0.35x** the headline output price, so the
sticker overstates unit cost by about **2.8x**.

Anyone comparing models on `$/M output` is getting this wrong.


## 5. The context window arms race is mostly unused

Dividing mean tokens per request by the advertised context length asks how much
of the window the traffic actually touches. Token-weighted across the market:
**6.44%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.25% |
| **extractive** | 2.92% |
| **conversational** | 1.65% |
| **output_heavy** | 0.41% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,050 endpoints serving multi-provider models,
**701 are dominated** (66.8%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-20260816` | Cloudflare | $4.40 | 28 tok/s | Sail Research | 30 |
| `~z-ai/glm-latest` | Cloudflare | $4.40 | 28 tok/s | Sail Research | 30 |
| `z-ai/glm-5.3-20260816` | AtlasCloud | $4.40 | 45 tok/s | Sail Research | 29 |
| `~z-ai/glm-latest` | AtlasCloud | $4.40 | 44 tok/s | Sail Research | 29 |
| `z-ai/glm-5.3-flash-20260826` | Near AI | $0.50 | 15 tok/s | OpenInference | 28 |
| `~z-ai/glm-flash-latest` | Near AI | $0.50 | 15 tok/s | OpenInference | 28 |
| `z-ai/glm-5.3-flash-20260826` | Reka | $1.60 | 44 tok/s | OpenInference | 28 |
| `~z-ai/glm-flash-latest` | Reka | $1.60 | 42 tok/s | OpenInference | 28 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-10-17` and `2026-10-18`,
**1.95%** of 565 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.63 | -0.88 to -0.38 | 0.461 | 86 | yes |
| **all** | request weighted | -0.36 | -0.81 to +0.09 | 0.046 | 457 | no |
| **conversational** | request weighted | -0.19 | -0.52 to +0.13 | 0.013 | 297 | no |
| **extractive** | request weighted | +0.33 | -0.32 to +0.99 | 0.089 | 19 | no |
| **output_heavy** | request weighted | -0.23 | -0.37 to -0.09 | 0.127 | 55 | yes |
| **agentic** | unweighted | -0.35 | -0.66 to -0.03 | 0.041 | 86 | yes |
| **all** | unweighted | -0.95 | -1.27 to -0.64 | 0.080 | 457 | yes |
| **conversational** | unweighted | -0.87 | -1.19 to -0.54 | 0.085 | 297 | yes |
| **extractive** | unweighted | +0.26 | -0.35 to +0.86 | 0.033 | 19 | no |
| **output_heavy** | unweighted | -1.27 | -2.09 to -0.44 | 0.110 | 55 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.35, interval
-0.66 to -0.03, straddling zero). Weighting by requests, the
elasticity is **-0.63** (-0.88 to -0.38) and
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
| ≥2 days silent | 82 | 406 | 90.7% | 82.5% |
| ≥3 days silent | 73 | 415 | 92.2% | 85.2% |
| ≥7 days silent | 61 | 427 | 94.1% | 87.5% |
| ≥14 days silent | 22 | 466 | 95.8% | 94.9% |

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
