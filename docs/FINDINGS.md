# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-08-16` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 559 model-variants, 274.26 T
tokens and 17.09 B requests over the trailing 30 days.


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
| **agentic** | 66 | 203.84 T | 74.3% | 50.8 | 46,863 | large contexts, terse output, very large interactions |
| **conversational** | 274 | 66.60 T | 24.3% | 9.8 | 4,156 | moderate context per output token, human-sized interactions |
| **unclassified** | 112 | 2.28 T | 0.8% | — | 29 | insufficient data to classify |
| **extractive** | 30 | 1.40 T | 0.5% | 36.4 | 7,641 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 77 | 140.39 B | 0.1% | 0.6 | 4,509 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **74.3% of all tokens**
while being 66 of 559 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
24.3%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 327.9 | 1,210 | 22.88 B | extractive |
| `poolside/laguna-s-2.1-20260720` | 159.4 | 94,603 | 4.43 T | agentic |
| `poolside/laguna-m.1-20260312` | 142.5 | 69,033 | 519.54 B | agentic |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 137.8 | 94,000 | 10.11 T | agentic |
| `poolside/laguna-xs-2.1-20260625` | 119.3 | 57,358 | 661.55 B | agentic |
| `xiaomi/mimo-v2.5-20260422` | 117.9 | 68,457 | 29.23 T | agentic |
| `nvidia/nemotron-3.5-lightning-20260807` | 100.7 | 76,278 | 495.51 B | agentic |
| `anthropic/claude-opus-5-fast-20260723` | 99.6 | 87,453 | 116.83 B | agentic |
| `stepfun/step-3.7-flash-20260528` | 88.2 | 69,333 | 6.01 T | agentic |
| `anthropic/claude-4.8-opus-fast-20260528` | 79.1 | 58,144 | 78.60 B | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
327.9 tokens of context per token written, but its interactions
average only 1,210 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `poolside/laguna-s-2.1-20260720`: 159.4 tokens of context per token
written, in interactions averaging 94,603 tokens, which
is 78× larger.
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


Across 211 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.73** with a p25–p75 range of 0.56–0.96.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 13 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.30×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `nex-agi/nex-n2-mini` | 10.18× | 87.08 B | 53 | conversational |
| `qwen/qwen3-vl-32b-instruct` | 3.20× | 93.35 B | 297 | conversational |
| `anthropic/claude-opus-5-20260723` | 2.81× | 4.33 T | 23 | agentic |
| `inclusionai/ling-3.0-flash-20260723` | 2.79× | 106.04 B | 24 | conversational |
| `anthropic/claude-4.8-opus-fast-20260528` | 2.31× | 78.60 B | 81 | agentic |
| `qwen/qwen3.7-max-20260520` | 2.14× | 441.83 B | 87 | conversational |
| `google/gemini-3.1-flash-lite-image-20260630` | 1.98× | 5.16 B | 47 | output_heavy |
| `openai/gpt-5.6-luna-20260709` | 1.70× | 11.48 T | 38 | agentic |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-5.2-chat-20251211` | 0.00× | 8.31 B | 249 | conversational |
| `ibm-granite/granite-4.0-h-micro` | 0.05× | 18.43 B | 300 | extractive |
| `meta/muse-spark-1.1-20260709` | 0.08× | 168.20 B | 31 | agentic |
| `nvidia/nemotron-3-nano-30b-a3b` | 0.15× | 83.98 B | 245 | conversational |
| `openai/o4-mini-2025-04-16` | 0.17× | 24.41 B | 487 | conversational |
| `amazon/nova-2-lite-v1` | 0.17× | 10.33 B | 257 | conversational |
| `deepseek/deepseek-v3.1-terminus` | 0.23× | 141.72 B | 328 | conversational |
| `qwen/qwen3.6-plus-04-02` | 0.24× | 276.63 B | 136 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$163.1 M per month** across
400 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 8.3% | 36.3% | 4.36x |
| `openai` | 10.2% | 16.0% | 1.57x |
| `deepseek` | 22.6% | 12.8% | 0.57x |
| `moonshotai` | 2.9% | 11.8% | 4.14x |
| `google` | 8.6% | 5.7% | 0.66x |
| `z-ai` | 6.0% | 3.6% | 0.59x |
| `xiaomi` | 11.6% | 3.2% | 0.27x |
| `x-ai` | 0.9% | 2.8% | 3.23x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**2,559**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **46.1%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.932** by value. Both are extreme; a
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
**8.01%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.76% |
| **extractive** | 4.87% |
| **output_heavy** | 2.25% |
| **conversational** | 1.87% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 707 endpoints serving multi-provider models,
**460 are dominated** (65.1%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.2-20260616` | Alibaba | $7.26 | 48 tok/s | Baidu | 23 |
| `deepseek/deepseek-v4-flash-20260731` | Cloudflare | $0.28 | 9 tok/s | StreamLake | 21 |
| `~deepseek/deepseek-v4-flash-latest` | Cloudflare | $0.28 | 9 tok/s | StreamLake | 21 |
| `~deepseek/deepseek-v4-flash-latest` | Mancer 2 | $0.50 | 39 tok/s | StreamLake | 20 |
| `~deepseek/deepseek-v4-flash-latest` | Inceptron | $0.28 | 23 tok/s | StreamLake | 19 |
| `deepseek/deepseek-v4-flash-20260731` | Mancer 2 | $0.50 | 38 tok/s | StreamLake | 19 |
| `deepseek/deepseek-v4-flash-20260731` | Inceptron | $0.28 | 25 tok/s | StreamLake | 18 |
| `deepseek/deepseek-v4-flash-20260731` | AkashML | $0.28 | 34 tok/s | StreamLake | 17 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-08-15` and `2026-08-16`,
**1.79%** of 446 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.48 | -0.64 to -0.33 | 0.390 | 57 | yes |
| **all** | request weighted | -0.26 | -0.76 to +0.24 | 0.035 | 369 | no |
| **conversational** | request weighted | -0.45 | -1.18 to +0.28 | 0.092 | 249 | no |
| **extractive** | request weighted | +0.33 | -0.05 to +0.71 | 0.098 | 27 | no |
| **output_heavy** | request weighted | +0.07 | -0.18 to +0.31 | 0.009 | 36 | no |
| **agentic** | unweighted | -0.05 | -0.66 to +0.56 | 0.000 | 57 | no |
| **all** | unweighted | -0.56 | -0.80 to -0.32 | 0.053 | 369 | yes |
| **conversational** | unweighted | -0.84 | -1.10 to -0.59 | 0.133 | 249 | yes |
| **extractive** | unweighted | +0.12 | -0.39 to +0.62 | 0.005 | 27 | no |
| **output_heavy** | unweighted | -0.68 | -1.38 to +0.03 | 0.110 | 36 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.05, interval
-0.66 to +0.56, straddling zero). Weighting by requests, the
elasticity is **-0.48** (-0.64 to -0.33) and
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
| ≥2 days silent | 28 | 374 | 96.3% | 92.4% |
| ≥3 days silent | 26 | 376 | 96.6% | 92.7% |
| ≥7 days silent | 19 | 383 | 97.8% | 94.3% |
| ≥14 days silent | 13 | 389 | 98.9% | 96.1% |

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
