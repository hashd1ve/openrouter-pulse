# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-08-20` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 554 model-variants, 288.91 T
tokens and 17.55 B requests over the trailing 30 days.


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
| **agentic** | 61 | 206.60 T | 71.5% | 51.3 | 49,436 | large contexts, terse output, very large interactions |
| **conversational** | 271 | 78.18 T | 27.1% | 9.8 | 4,174 | moderate context per output token, human-sized interactions |
| **unclassified** | 112 | 2.31 T | 0.8% | — | 29 | insufficient data to classify |
| **extractive** | 31 | 1.68 T | 0.6% | 37.2 | 8,205 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 79 | 136.79 B | 0.0% | 0.6 | 4,560 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **71.5% of all tokens**
while being 61 of 554 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
27.1%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 351.8 | 1,278 | 23.29 B | extractive |
| `poolside/laguna-s-2.1-20260720` | 153.4 | 94,246 | 5.41 T | agentic |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 139.7 | 93,631 | 10.82 T | agentic |
| `poolside/laguna-xs-2.1-20260625` | 126.1 | 57,640 | 694.37 B | agentic |
| `poolside/laguna-m.1-20260312` | 124.2 | 59,131 | 157.21 B | agentic |
| `xiaomi/mimo-v2.5-20260422` | 119.6 | 69,771 | 28.83 T | agentic |
| `anthropic/claude-opus-5-fast-20260723` | 99.9 | 88,433 | 130.20 B | agentic |
| `nvidia/nemotron-3.5-lightning-20260807` | 96.9 | 76,175 | 985.54 B | agentic |
| `openai/gpt-5.6-terra-20260709` | 91.2 | 39,808 | 2.78 T | agentic |
| `stepfun/step-3.7-flash-20260528` | 86.3 | 70,381 | 5.99 T | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
351.8 tokens of context per token written, but its interactions
average only 1,278 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `poolside/laguna-s-2.1-20260720`: 153.4 tokens of context per token
written, in interactions averaging 94,246 tokens, which
is 74× larger.
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


Across 219 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **1.00** with a p25–p75 range of 0.72–1.21.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 16 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **2.36×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `amazon/nova-lite-v1` | 2.98× | 10.07 B | 623 | conversational |
| `google/gemini-3.1-pro-preview-20260219` | 2.79× | 829.30 B | 182 | conversational |
| `anthropic/claude-3-haiku` | 2.60× | 11.43 B | 890 | conversational |
| `openai/gpt-5.6-sol-20260709` | 2.49× | 2.81 T | 42 | agentic |
| `z-ai/glm-5v-turbo-20260401` | 2.26× | 72.56 B | 141 | agentic |
| `qwen/qwen3-32b-04-28` | 2.20× | 100.44 B | 479 | conversational |
| `inclusionai/ling-3.0-flash-20260723` | 2.03× | 149.49 B | 28 | conversational |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 2.02× | 10.82 T | 77 | agentic |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-5.2-chat-20251211` | 0.00× | 7.05 B | 253 | conversational |
| `openai/gpt-4o-2024-05-13` | 0.07× | 3.85 B | 829 | extractive |
| `nvidia/nemotron-3-nano-30b-a3b` | 0.16× | 76.79 B | 249 | conversational |
| `google/gemma-3-4b-it` | 0.21× | 25.59 B | 525 | conversational |
| `openai/gpt-5-nano-2025-08-07` | 0.22× | 2.30 B | 378 | conversational |
| `deepseek/deepseek-v3.1-terminus` | 0.25× | 123.25 B | 332 | conversational |
| `google/gemma-2-27b-it` | 0.30× | 643.41 M | 768 | conversational |
| `poolside/laguna-xs-2.1-20260625` | 0.30× | 37.71 B | 49 | extractive |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$201.0 M per month** across
397 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 7.9% | 34.4% | 4.36x |
| `deepseek` | 23.8% | 14.3% | 0.60x |
| `z-ai` | 5.9% | 11.7% | 1.99x |
| `openai` | 11.2% | 11.7% | 1.04x |
| `moonshotai` | 2.7% | 10.1% | 3.72x |
| `google` | 8.9% | 6.2% | 0.69x |
| `xiaomi` | 10.9% | 2.5% | 0.23x |
| `x-ai` | 0.9% | 2.5% | 2.79x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**2,693**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **47.8%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.943** by value. Both are extreme; a
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
**8.26%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.36% |
| **extractive** | 4.50% |
| **output_heavy** | 2.37% |
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

Of 734 endpoints serving multi-provider models,
**479 are dominated** (65.3%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.2-20260616` | Alibaba | $7.26 | 38 tok/s | DigitalOcean | 26 |
| `z-ai/glm-5.2-20260616` | Cloudflare | $4.40 | 18 tok/s | DigitalOcean | 22 |
| `z-ai/glm-5.2-20260616` | Venice | $4.40 | 41 tok/s | DigitalOcean | 21 |
| `z-ai/glm-5.2-20260616` | Z.AI | $4.40 | 43 tok/s | DigitalOcean | 20 |
| `z-ai/glm-5.2-20260616` | Fireworks | $4.40 | 44 tok/s | DigitalOcean | 19 |
| `~deepseek/deepseek-v4-flash-latest` | Ambient | $0.28 | 19 tok/s | Relace | 17 |
| `deepseek/deepseek-v4-flash-20260731` | Ambient | $0.28 | 27 tok/s | Relace | 16 |
| `deepseek/deepseek-v4-flash-20260731` | Mancer 2 | $0.45 | 44 tok/s | Relace | 16 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-08-19` and `2026-08-20`,
**2.71%** of 442 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.48 | -0.66 to -0.31 | 0.354 | 55 | yes |
| **all** | request weighted | -0.13 | -0.57 to +0.31 | 0.008 | 372 | no |
| **conversational** | request weighted | -0.26 | -0.90 to +0.38 | 0.027 | 253 | no |
| **extractive** | request weighted | +0.10 | -0.36 to +0.55 | 0.007 | 27 | no |
| **output_heavy** | request weighted | +0.03 | -0.33 to +0.39 | 0.001 | 37 | no |
| **agentic** | unweighted | -0.21 | -0.54 to +0.12 | 0.022 | 55 | no |
| **all** | unweighted | -0.59 | -0.81 to -0.37 | 0.069 | 372 | yes |
| **conversational** | unweighted | -0.79 | -1.01 to -0.56 | 0.148 | 253 | yes |
| **extractive** | unweighted | -0.35 | -0.71 to +0.02 | 0.029 | 27 | no |
| **output_heavy** | unweighted | -0.65 | -1.23 to -0.08 | 0.079 | 37 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.21, interval
-0.54 to +0.12, straddling zero). Weighting by requests, the
elasticity is **-0.48** (-0.66 to -0.31) and
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
| ≥2 days silent | 22 | 377 | 96.7% | 93.7% |
| ≥3 days silent | 18 | 381 | 97.6% | 94.7% |
| ≥7 days silent | 9 | 390 | 98.3% | 96.8% |
| ≥14 days silent | 6 | 393 | 99.2% | 97.7% |

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
