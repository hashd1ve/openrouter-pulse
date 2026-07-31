# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-07-31` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 497 model-variants, 240.10 T
tokens and 15.87 B requests over the trailing 30 days.


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
| **agentic** | 62 | 167.17 T | 69.6% | 55.5 | 45,780 | large contexts, terse output, very large interactions |
| **conversational** | 249 | 68.65 T | 28.6% | 11.8 | 3,578 | moderate context per output token, human-sized interactions |
| **unclassified** | 89 | 2.19 T | 0.9% | — | 39 | insufficient data to classify |
| **extractive** | 27 | 1.94 T | 0.8% | 34.2 | 8,924 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 70 | 138.05 B | 0.1% | 0.6 | 4,345 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **69.6% of all tokens**
while being 62 of 497 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
28.6%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 195.3 | 726 | 14.08 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 162.7 | 103,590 | 9.68 T | agentic |
| `poolside/laguna-m.1-20260312` | 142.4 | 69,730 | 1.82 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 127.6 | 78,633 | 445.54 B | agentic |
| `xiaomi/mimo-v2.5-20260422` | 113.9 | 66,781 | 33.26 T | agentic |
| `perceptron/perceptron-mk1-20260512` | 98.8 | 9,328 | 13.85 B | extractive |
| `anthropic/claude-4.8-opus-fast-20260528` | 96.3 | 66,711 | 112.37 B | agentic |
| `anthropic/claude-4.8-opus-20260528` | 84.5 | 80,368 | 7.39 T | agentic |
| `qwen/qwen3-coder-480b-a35b-07-25` | 81.0 | 20,956 | 103.83 B | agentic |
| `anthropic/claude-4.7-opus-20260416` | 80.7 | 64,223 | 7.17 T | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
195.3 tokens of context per token written, but its interactions
average only 726 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 162.7 tokens of context per token
written, in interactions averaging 103,590 tokens, which
is 143× larger.
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
median of **0.97** with a p25–p75 range of 0.70–1.19.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 19 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.36×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `moonshotai/kimi-k2-thinking-20251106` | 9.67× | 18.18 B | 267 | conversational |
| `openai/gpt-4o-2024-05-13` | 8.71× | 3.52 B | 809 | extractive |
| `openai/gpt-5.6-terra-20260709` | 3.73× | 598.67 B | 22 | agentic |
| `nex-agi/nex-n2-mini` | 3.52× | 32.31 B | 37 | conversational |
| `amazon/nova-micro-v1` | 3.28× | 67.04 B | 603 | conversational |
| `inclusionai/ling-2.6-flash-20260421` | 3.15× | 344.67 B | 101 | conversational |
| `openai/gpt-5.6-luna-pro-20260709` | 3.11× | 149.43 B | 22 | agentic |
| `poolside/laguna-s-2.1-20260720` | 2.68× | 445.54 B | 10 | agentic |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-5.1-chat-20251113` | 0.00× | 7.93 B | 260 | conversational |
| `ibm-granite/granite-4.0-h-micro` | 0.01× | 80.04 B | 284 | agentic |
| `tencent/hy3-preview-20260421` | 0.05× | 2.43 T | 100 | agentic |
| `openai/o4-mini-2025-04-16` | 0.12× | 93.82 B | 471 | conversational |
| `google/gemma-4-31b-it-20260402` | 0.13× | 49.80 B | 120 | conversational |
| `amazon/nova-2-lite-v1` | 0.15× | 18.65 B | 241 | conversational |
| `mistralai/ministral-14b-2512` | 0.18× | 21.90 B | 241 | conversational |
| `perceptron/perceptron-mk1-20260512` | 0.19× | 13.85 B | 80 | extractive |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$167.3 M per month** across
351 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 11.9% | 44.9% | 3.77x |
| `openai` | 6.9% | 15.7% | 2.27x |
| `z-ai` | 6.9% | 10.9% | 1.58x |
| `moonshotai` | 2.2% | 6.1% | 2.79x |
| `deepseek` | 17.2% | 6.1% | 0.35x |
| `google` | 8.1% | 4.5% | 0.56x |
| `xiaomi` | 15.2% | 3.5% | 0.23x |
| `tencent` | 12.2% | 2.3% | 0.19x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**2,501**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **44.9%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.933** by value. Both are extreme; a
national income distribution above 0.6 is considered severe.


### The sticker price is not the price

Traffic is overwhelmingly prompt-heavy, and prompt tokens cost less than
completions. Blended across each model's real token mix, the price actually paid
per token is a median **0.32x** the headline output price, so the
sticker overstates unit cost by about **3.1x**.

Anyone comparing models on `$/M output` is getting this wrong.


## 5. The context window arms race is mostly unused

Dividing mean tokens per request by the advertised context length asks how much
of the window the traffic actually touches. Token-weighted across the market:
**7.98%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 8.73% |
| **conversational** | 1.90% |
| **output_heavy** | 1.87% |
| **extractive** | 1.68% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 666 endpoints serving multi-provider models,
**417 are dominated** (62.6%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.2-20260616` | DigitalOcean | $4.40 | 18 tok/s | Decart | 25 |
| `z-ai/glm-5.2-20260616` | Phala | $4.40 | 29 tok/s | Decart | 24 |
| `z-ai/glm-5.2-20260616` | Ambient | $4.40 | 31 tok/s | Decart | 23 |
| `z-ai/glm-5.2-20260616` | Venice | $4.40 | 36 tok/s | Decart | 20 |
| `moonshotai/kimi-k2.6-20260420` | Moonshot AI | $4.00 | 21 tok/s | DigitalOcean | 19 |
| `deepseek/deepseek-v4-flash-20260423` | Ambient | $0.28 | 11 tok/s | DeepInfra | 17 |
| `deepseek/deepseek-v4-flash-20260423` | Mancer 2 | $0.50 | 13 tok/s | DeepInfra | 17 |
| `deepseek/deepseek-v4-pro-20260423` | CoreWeave | $3.48 | 7 tok/s | DeepSeek | 16 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


> Not yet measurable: it needs two completed snapshots and this is the first.
> The metric is built and will populate on the next capture.


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.47 | -0.67 to -0.26 | 0.367 | 48 | yes |
| **all** | request weighted | -0.12 | -0.51 to +0.27 | 0.007 | 323 | no |
| **conversational** | request weighted | -0.22 | -0.70 to +0.25 | 0.020 | 219 | no |
| **extractive** | request weighted | -0.26 | -1.31 to +0.79 | 0.034 | 20 | no |
| **output_heavy** | request weighted | +0.10 | -0.17 to +0.36 | 0.015 | 36 | no |
| **agentic** | unweighted | -0.08 | -0.62 to +0.47 | 0.002 | 48 | no |
| **all** | unweighted | -0.49 | -0.75 to -0.23 | 0.036 | 323 | yes |
| **conversational** | unweighted | -0.69 | -1.01 to -0.36 | 0.078 | 219 | yes |
| **extractive** | unweighted | -0.04 | -0.52 to +0.44 | 0.001 | 20 | no |
| **output_heavy** | unweighted | -0.67 | -1.19 to -0.14 | 0.047 | 36 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.08, interval
-0.62 to +0.47, straddling zero). Weighting by requests, the
elasticity is **-0.47** (-0.67 to -0.26) and
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
| ≥2 days silent | 33 | 320 | 94.4% | 88.5% |
| ≥3 days silent | 15 | 338 | 98.1% | 94.6% |
| ≥7 days silent | 11 | 342 | 98.8% | 96.6% |
| ≥14 days silent | 1 | 352 | 100.0% | 99.2% |

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
