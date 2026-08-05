# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-08-05` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 506 model-variants, 249.36 T
tokens and 16.24 B requests over the trailing 30 days.


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
| **agentic** | 62 | 173.08 T | 69.4% | 53.2 | 45,397 | large contexts, terse output, very large interactions |
| **conversational** | 254 | 69.43 T | 27.8% | 11.4 | 3,875 | moderate context per output token, human-sized interactions |
| **extractive** | 25 | 4.42 T | 1.8% | 39.9 | 8,559 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 97 | 2.31 T | 0.9% | — | 35 | insufficient data to classify |
| **output_heavy** | 68 | 132.99 B | 0.1% | 0.6 | 4,385 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **69.4% of all tokens**
while being 62 of 506 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
27.8%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 223.3 | 829 | 16.04 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 162.1 | 104,381 | 10.60 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 160.3 | 93,831 | 1.71 T | agentic |
| `poolside/laguna-m.1-20260312` | 139.4 | 69,606 | 1.39 T | agentic |
| `xiaomi/mimo-v2.5-20260422` | 114.6 | 67,148 | 33.76 T | agentic |
| `anthropic/claude-4.8-opus-fast-20260528` | 91.6 | 62,128 | 88.48 B | agentic |
| `poolside/laguna-xs-2.1-20260625` | 90.5 | 54,834 | 575.68 B | agentic |
| `qwen/qwen3-coder-next-2025-02-03` | 84.6 | 25,612 | 98.04 B | agentic |
| `anthropic/claude-4.8-opus-20260528` | 83.0 | 78,083 | 6.27 T | agentic |
| `stepfun/step-3.7-flash-20260528` | 82.9 | 66,326 | 5.93 T | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
223.3 tokens of context per token written, but its interactions
average only 829 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 162.1 tokens of context per token
written, in interactions averaging 104,381 tokens, which
is 126× larger.
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


Across 207 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.92** with a p25–p75 range of 0.74–1.18.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 17 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.50×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `z-ai/glm-5v-turbo-20260401` | 5.01× | 26.67 B | 126 | agentic |
| `z-ai/glm-4.5-air` | 4.93× | 41.59 B | 376 | conversational |
| `openai/gpt-5.6-luna-20260709` | 4.30× | 3.79 T | 27 | extractive |
| `openai/gpt-5.6-luna-pro-20260709` | 3.88× | 508.45 B | 27 | agentic |
| `amazon/nova-micro-v1` | 3.08× | 103.71 B | 608 | conversational |
| `openai/gpt-5.6-terra-20260709` | 2.91× | 1.08 T | 27 | agentic |
| `amazon/nova-2-lite-v1` | 2.89× | 17.75 B | 246 | conversational |
| `qwen/qwen3.5-plus-20260216` | 2.79× | 24.96 B | 170 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `ibm-granite/granite-4.0-h-micro` | 0.01× | 72.76 B | 289 | agentic |
| `anthropic/claude-4.7-opus-20260416` | 0.15× | 5.60 T | 111 | agentic |
| `openai/o4-mini-2025-04-16` | 0.17× | 68.94 B | 476 | conversational |
| `google/gemma-4-31b-it-20260402` | 0.25× | 29.36 B | 125 | conversational |
| `openai/gpt-5.1-codex-mini-20251113` | 0.27× | 15.91 B | 265 | conversational |
| `poolside/laguna-xs-2.1-20260625` | 0.27× | 39.82 B | 34 | conversational |
| `qwen/qwen3.7-max-20260520` | 0.32× | 537.89 B | 76 | conversational |
| `openai/gpt-5.5-20260423` | 0.32× | 2.09 T | 103 | agentic |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$229.0 M per month** across
354 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 10.5% | 51.5% | 4.89x |
| `openai` | 7.8% | 14.6% | 1.86x |
| `z-ai` | 6.6% | 5.6% | 0.86x |
| `google` | 7.9% | 5.6% | 0.71x |
| `moonshotai` | 2.4% | 5.5% | 2.27x |
| `deepseek` | 18.2% | 4.7% | 0.26x |
| `nvidia` | 5.2% | 2.9% | 0.56x |
| `xiaomi` | 14.8% | 2.6% | 0.17x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,291**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **54.4%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.940** by value. Both are extreme; a
national income distribution above 0.6 is considered severe.


### The sticker price is not the price

Traffic is overwhelmingly prompt-heavy, and prompt tokens cost less than
completions. Blended across each model's real token mix, the price actually paid
per token is a median **0.33x** the headline output price, so the
sticker overstates unit cost by about **3.1x**.

Anyone comparing models on `$/M output` is getting this wrong.


## 5. The context window arms race is mostly unused

Dividing mean tokens per request by the advertised context length asks how much
of the window the traffic actually touches. Token-weighted across the market:
**8.45%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 8.52% |
| **conversational** | 1.93% |
| **output_heavy** | 1.84% |
| **extractive** | 1.77% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 697 endpoints serving multi-provider models,
**445 are dominated** (63.8%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.2-20260616` | Z.AI | $4.40 | 20 tok/s | Decart | 25 |
| `z-ai/glm-5.2-20260616` | Ambient | $4.40 | 30 tok/s | Decart | 19 |
| `moonshotai/kimi-k2.6-20260420` | Phala | $4.60 | 19 tok/s | Baidu | 19 |
| `deepseek/deepseek-v4-flash-20260423` | OpenInference | $0.28 | 5 tok/s | DigitalOcean | 17 |
| `moonshotai/kimi-k2.6-20260420` | Moonshot AI | $4.00 | 21 tok/s | Baidu | 17 |
| `deepseek/deepseek-v4-flash-20260423` | Mancer 2 | $0.50 | 21 tok/s | StreamLake | 16 |
| `~deepseek/deepseek-v4-flash-latest` | Phala | $0.40 | 27 tok/s | DeepInfra | 16 |
| `deepseek/deepseek-v4-flash-20260731` | Io Net | $0.32 | 13 tok/s | DeepInfra | 16 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-08-04` and `2026-08-05`,
**0.73%** of 409 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.44 | -0.63 to -0.25 | 0.363 | 50 | yes |
| **all** | request weighted | -0.13 | -0.55 to +0.29 | 0.009 | 326 | no |
| **conversational** | request weighted | -0.21 | -0.75 to +0.33 | 0.020 | 222 | no |
| **extractive** | request weighted | -1.25 | -2.84 to +0.34 | 0.242 | 21 | no |
| **output_heavy** | request weighted | +0.04 | -0.21 to +0.29 | 0.003 | 33 | no |
| **agentic** | unweighted | -0.05 | -0.56 to +0.45 | 0.001 | 50 | no |
| **all** | unweighted | -0.51 | -0.79 to -0.23 | 0.041 | 326 | yes |
| **conversational** | unweighted | -0.64 | -0.98 to -0.31 | 0.072 | 222 | yes |
| **extractive** | unweighted | -0.17 | -0.67 to +0.33 | 0.012 | 21 | no |
| **output_heavy** | unweighted | -1.11 | -1.81 to -0.41 | 0.130 | 33 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.05, interval
-0.56 to +0.45, straddling zero). Weighting by requests, the
elasticity is **-0.44** (-0.63 to -0.25) and
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
| ≥2 days silent | 34 | 322 | 94.7% | 88.0% |
| ≥3 days silent | 34 | 322 | 94.7% | 88.0% |
| ≥7 days silent | 32 | 324 | 94.7% | 89.0% |
| ≥14 days silent | 10 | 346 | 99.1% | 97.0% |

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
