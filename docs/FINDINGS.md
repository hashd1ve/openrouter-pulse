# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-08-24` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 559 model-variants, 309.35 T
tokens and 17.87 B requests over the trailing 30 days.


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
| **agentic** | 67 | 229.64 T | 74.2% | 51.4 | 47,161 | large contexts, terse output, very large interactions |
| **conversational** | 272 | 75.94 T | 24.5% | 10.2 | 3,762 | moderate context per output token, human-sized interactions |
| **unclassified** | 116 | 2.26 T | 0.7% | — | 27 | insufficient data to classify |
| **extractive** | 27 | 1.37 T | 0.4% | 43.3 | 7,527 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 77 | 140.28 B | 0.0% | 0.4 | 4,571 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **74.2% of all tokens**
while being 67 of 559 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
24.5%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 365.2 | 1,309 | 22.41 B | extractive |
| `poolside/laguna-s-2.1-20260720` | 151.9 | 93,589 | 6.12 T | agentic |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 150.9 | 98,735 | 12.55 T | agentic |
| `poolside/laguna-xs-2.1-20260625` | 126.8 | 56,778 | 690.33 B | agentic |
| `xiaomi/mimo-v2.5-20260422` | 125.5 | 72,784 | 28.40 T | agentic |
| `anthropic/claude-opus-5-fast-20260723` | 102.5 | 89,731 | 144.12 B | agentic |
| `nvidia/nemotron-3.5-lightning-20260807` | 98.5 | 74,776 | 1.57 T | agentic |
| `openai/gpt-5.6-terra-20260709` | 89.7 | 38,701 | 2.99 T | agentic |
| `qwen/qwen3-coder-next-2025-02-03` | 79.9 | 26,395 | 92.91 B | agentic |
| `stepfun/step-3.7-flash-20260528` | 77.9 | 68,659 | 4.84 T | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
365.2 tokens of context per token written, but its interactions
average only 1,309 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `poolside/laguna-s-2.1-20260720`: 151.9 tokens of context per token
written, in interactions averaging 93,589 tokens, which
is 71× larger.
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


Across 221 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.75** with a p25–p75 range of 0.58–0.95.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 16 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **2.31×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-5.6-luna-20260709` | 10.28× | 9.69 B | 46 | output_heavy |
| `openai/gpt-audio-mini` | 5.15× | 1.27 B | 217 | conversational |
| `bytedance-seed/seed-2.0-mini-20260224` | 3.22× | 20.40 B | 179 | conversational |
| `google/gemini-3.7-flash-20260813` | 2.74× | 9.47 B | 11 | conversational |
| `mistralai/mistral-small-24b-instruct-2501` | 2.72× | 30.34 B | 571 | conversational |
| `openai/gpt-5.5-20260423` | 2.53× | 1.04 T | 122 | agentic |
| `mistralai/mistral-large-2512` | 2.20× | 38.24 B | 266 | conversational |
| `openai/gpt-5-nano-2025-08-07` | 2.11× | 2.80 B | 382 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-5.2-chat-20251211` | 0.00× | 5.89 B | 257 | conversational |
| `meta-llama/llama-3.2-1b-instruct` | 0.04× | 2.42 B | 698 | output_heavy |
| `perceptron/perceptron-mk1-20260512` | 0.05× | 6.66 B | 104 | extractive |
| `google/gemma-4-26b-a4b-it-20260403` | 0.08× | 58.57 B | 143 | conversational |
| `nvidia/nemotron-3-nano-30b-a3b` | 0.12× | 62.71 B | 253 | conversational |
| `qwen/qwen3.5-plus-20260216` | 0.17× | 25.31 B | 189 | conversational |
| `thinkingmachines/inkling-small-20260730` | 0.17× | 31.37 B | 25 | conversational |
| `nvidia/nemotron-3.5-lightning-20260807` | 0.17× | 107.62 B | 13 | agentic |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$159.4 M per month** across
403 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 7.0% | 37.5% | 5.36x |
| `openai` | 11.1% | 13.6% | 1.22x |
| `moonshotai` | 2.4% | 12.6% | 5.16x |
| `deepseek` | 24.0% | 9.5% | 0.40x |
| `google` | 8.5% | 6.2% | 0.73x |
| `nvidia` | 5.4% | 5.0% | 0.92x |
| `xiaomi` | 10.0% | 3.1% | 0.31x |
| `x-ai` | 0.8% | 3.1% | 3.79x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,147**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **53.1%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.940** by value. Both are extreme; a
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
**8.99%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.66% |
| **extractive** | 3.81% |
| **output_heavy** | 2.37% |
| **conversational** | 1.84% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 738 endpoints serving multi-provider models,
**486 are dominated** (65.9%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.2-20260616` | Fireworks | $4.40 | 38 tok/s | Ambient | 20 |
| `z-ai/glm-5.2-20260616` | GMICloud | $4.40 | 40 tok/s | Ambient | 19 |
| `z-ai/glm-5.2-20260616` | Baidu | $4.40 | 41 tok/s | Ambient | 18 |
| `deepseek/deepseek-v4-flash-20260731` | Cloudflare | $1.32 | 41 tok/s | Decart | 17 |
| `~deepseek/deepseek-v4-flash-latest` | Cloudflare | $1.32 | 40 tok/s | Decart | 17 |
| `z-ai/glm-5.2-20260616` | Cloudflare | $6.60 | 51 tok/s | Ambient | 16 |
| `z-ai/glm-5.2-20260616` | Z.AI | $4.40 | 42 tok/s | Ambient | 16 |
| `moonshotai/kimi-k2.6-20260420` | Phala | $4.60 | 18 tok/s | Decart | 16 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-08-23` and `2026-08-24`,
**0.68%** of 442 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.61 | -0.79 to -0.44 | 0.464 | 53 | yes |
| **all** | request weighted | -0.28 | -0.75 to +0.19 | 0.037 | 364 | no |
| **conversational** | request weighted | -0.46 | -1.17 to +0.24 | 0.093 | 247 | no |
| **extractive** | request weighted | -0.21 | -1.24 to +0.82 | 0.020 | 24 | no |
| **output_heavy** | request weighted | -0.06 | -0.44 to +0.32 | 0.004 | 40 | no |
| **agentic** | unweighted | -0.28 | -0.63 to +0.06 | 0.038 | 53 | no |
| **all** | unweighted | -0.51 | -0.78 to -0.25 | 0.050 | 364 | yes |
| **conversational** | unweighted | -0.65 | -0.93 to -0.36 | 0.088 | 247 | yes |
| **extractive** | unweighted | -0.29 | -0.70 to +0.13 | 0.052 | 24 | no |
| **output_heavy** | unweighted | -0.69 | -1.53 to +0.15 | 0.096 | 40 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.28, interval
-0.63 to +0.06, straddling zero). Weighting by requests, the
elasticity is **-0.61** (-0.79 to -0.44) and
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
| ≥2 days silent | 26 | 381 | 96.9% | 94.5% |
| ≥3 days silent | 23 | 384 | 97.6% | 95.2% |
| ≥7 days silent | 7 | 400 | 98.5% | 97.6% |
| ≥14 days silent | 4 | 403 | 99.4% | 98.4% |

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
