# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-10-21` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 723 model-variants, 700.46 T
tokens and 33.74 B requests over the trailing 30 days.


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
| **agentic** | 96 | 585.40 T | 83.6% | 54.1 | 53,247 | large contexts, terse output, very large interactions |
| **conversational** | 323 | 106.82 T | 15.2% | 9.4 | 3,857 | moderate context per output token, human-sized interactions |
| **extractive** | 34 | 4.85 T | 0.7% | 49.3 | 5,404 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 154 | 3.23 T | 0.5% | — | 33 | insufficient data to classify |
| **output_heavy** | 116 | 161.86 B | 0.0% | 0.3 | 3,818 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **83.6% of all tokens**
while being 96 of 723 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
15.2%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `upstage/solar-decide-20260928` | 2,207.9 | 5,151 | 20.18 B | extractive |
| `scaledown/classify-1-20260928` | 2,101.7 | 7,608 | 10.38 B | extractive |
| `upstage/solar-decide-flash-20261008` | 1,480.9 | 3,601 | 7.92 B | extractive |
| `perplexity/pplx-decider-v1-27b-20261001` | 1,155.6 | 4,655 | 9.10 B | extractive |
| `perplexity/pplx-decider-v1.1-27b-20261006` | 1,141.1 | 3,834 | 257.20 B | extractive |
| `perplexity/pplx-decider-flash-v1.2-20261016` | 915.2 | 2,953 | 11.53 B | extractive |
| `perplexity/pplx-decider-v1.2-20261016` | 643.5 | 1,995 | 57.51 B | extractive |
| `togethercomputer/tev1-4b-experimental-20260923` | 531.1 | 2,699 | 6.85 B | extractive |
| `inception/mercury-decide-20260930` | 349.9 | 3,962 | 75.00 B | extractive |
| `microsoft/microsoft-decision-1-20261009` | 348.3 | 1,253 | 31.27 B | extractive |

**Why both axes.** The top of this ranking is `upstage/solar-decide-20260928` at
2,207.9 tokens of context per token written, but its interactions
average only 5,151 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 203.2 tokens of context per token
written, in interactions averaging 134,160 tokens, which
is 26× larger.
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


Across 254 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.91** with a p25–p75 range of 0.68–1.15.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 22 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.30×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-5.6-luna-20260709` | 4.16× | 52.04 B | 104 | conversational |
| `google/gemma-2-27b-it` | 4.14× | 662.87 M | 830 | conversational |
| `openai/gpt-6-sol-20260922` | 3.49× | 5.60 B | 29 | conversational |
| `qwen/qwen3-vl-30b-a3b-instruct` | 3.12× | 43.57 B | 380 | conversational |
| `meta-llama/llama-guard-4-12b` | 2.90× | 7.37 B | 539 | extractive |
| `scaledown/summarize-20260928` | 2.73× | 3.47 B | 8 | conversational |
| `openai/gpt-6-luna-pro-20260922` | 2.29× | 23.12 B | 29 | conversational |
| `anthropic/claude-opus-5.5-20260921` | 2.14× | 17.09 T | 29 | agentic |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite-20260507` | 0.00× | 18.80 B | 167 | conversational |
| `perceptron/perceptron-mk1-20260512` | 0.05× | 6.85 B | 162 | extractive |
| `google/gemini-2.5-flash` | 0.08× | 6.38 B | 491 | conversational |
| `inclusionai/ling-3.0-flash-vl-20260910` | 0.09× | 126.64 B | 41 | conversational |
| `tencent/hy-mt2-7b-20260521` | 0.17× | 358.94 M | 63 | conversational |
| `meta/muse-spark-1.3-20260902` | 0.18× | 1.53 T | 49 | agentic |
| `stepfun/step-3.7-flash-20260528` | 0.19× | 282.49 B | 146 | conversational |
| `amazon/nova-lite-v1` | 0.20× | 10.63 B | 685 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$351.1 M per month** across
488 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 6.0% | 34.4% | 5.70x |
| `openai` | 10.5% | 21.6% | 2.05x |
| `tencent` | 6.7% | 8.9% | 1.31x |
| `deepseek` | 27.0% | 8.0% | 0.30x |
| `stepfun` | 3.1% | 6.0% | 1.94x |
| `moonshotai` | 1.3% | 5.7% | 4.34x |
| `google` | 4.3% | 4.2% | 0.98x |
| `xiaomi` | 7.5% | 3.1% | 0.41x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,468**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **55.8%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.943** by value. Both are extreme; a
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
**6.33%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 6.77% |
| **extractive** | 2.39% |
| **conversational** | 1.70% |
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

Of 1,136 endpoints serving multi-provider models,
**771 are dominated** (67.9%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-20260816` | Z.AI | $4.40 | 38 tok/s | Wafer | 34 |
| `z-ai/glm-5.3-20260816` | Cloudflare | $4.40 | 39 tok/s | Wafer | 33 |
| `~z-ai/glm-latest` | Cloudflare | $4.40 | 37 tok/s | Wafer | 33 |
| `z-ai/glm-5.3-20260816` | Alibaba | $8.80 | 49 tok/s | Wafer | 31 |
| `~z-ai/glm-latest` | Z.AI | $4.40 | 38 tok/s | Wafer | 31 |
| `deepseek/deepseek-v4.1-flash-20260910` | Nebius | $1.20 | 50 tok/s | Sail Research | 31 |
| `z-ai/glm-5.3-flash-20260826` | Reka | $2.40 | 30 tok/s | OpenInference | 30 |
| `~z-ai/glm-latest` | Alibaba | $8.80 | 49 tok/s | Wafer | 29 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-10-20` and `2026-10-21`,
**1.41%** of 567 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.67 | -0.90 to -0.43 | 0.545 | 83 | yes |
| **all** | request weighted | -0.29 | -0.78 to +0.19 | 0.035 | 454 | no |
| **conversational** | request weighted | +0.06 | -0.50 to +0.62 | 0.002 | 295 | no |
| **extractive** | request weighted | +0.22 | -0.34 to +0.78 | 0.059 | 20 | no |
| **output_heavy** | request weighted | -0.28 | -0.43 to -0.14 | 0.133 | 56 | yes |
| **agentic** | unweighted | -0.43 | -0.78 to -0.09 | 0.066 | 83 | yes |
| **all** | unweighted | -0.86 | -1.19 to -0.54 | 0.062 | 454 | yes |
| **conversational** | unweighted | -0.78 | -1.11 to -0.44 | 0.067 | 295 | yes |
| **extractive** | unweighted | +0.16 | -0.62 to +0.93 | 0.009 | 20 | no |
| **output_heavy** | unweighted | -0.91 | -1.83 to +0.01 | 0.052 | 56 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.43, interval
-0.78 to -0.09, straddling zero). Weighting by requests, the
elasticity is **-0.67** (-0.90 to -0.43) and
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
| ≥2 days silent | 76 | 413 | 92.1% | 84.6% |
| ≥3 days silent | 72 | 417 | 92.1% | 85.0% |
| ≥7 days silent | 64 | 425 | 93.3% | 87.5% |
| ≥14 days silent | 42 | 447 | 95.2% | 91.8% |

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
