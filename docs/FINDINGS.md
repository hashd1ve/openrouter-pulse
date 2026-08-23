# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-08-23` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 560 model-variants, 302.87 T
tokens and 17.83 B requests over the trailing 30 days.


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
| **agentic** | 67 | 222.29 T | 73.4% | 51.3 | 47,141 | large contexts, terse output, very large interactions |
| **conversational** | 274 | 76.78 T | 25.4% | 10.1 | 3,771 | moderate context per output token, human-sized interactions |
| **unclassified** | 115 | 2.30 T | 0.8% | — | 28 | insufficient data to classify |
| **extractive** | 26 | 1.37 T | 0.5% | 44.5 | 7,860 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 78 | 137.80 B | 0.0% | 0.5 | 4,585 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **73.4% of all tokens**
while being 67 of 560 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
25.4%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 362.6 | 1,306 | 22.91 B | extractive |
| `poolside/laguna-s-2.1-20260720` | 152.7 | 93,865 | 5.96 T | agentic |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 147.9 | 97,298 | 12.14 T | agentic |
| `poolside/laguna-xs-2.1-20260625` | 127.6 | 56,989 | 691.62 B | agentic |
| `xiaomi/mimo-v2.5-20260422` | 124.0 | 71,993 | 28.56 T | agentic |
| `poolside/laguna-m.1-20260312` | 123.7 | 55,551 | 73.16 B | agentic |
| `anthropic/claude-opus-5-fast-20260723` | 102.1 | 90,020 | 143.72 B | agentic |
| `nvidia/nemotron-3.5-lightning-20260807` | 98.1 | 75,021 | 1.42 T | agentic |
| `openai/gpt-5.6-terra-20260709` | 91.1 | 39,696 | 2.95 T | agentic |
| `qwen/qwen3-coder-next-2025-02-03` | 81.3 | 26,365 | 94.56 B | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
362.6 tokens of context per token written, but its interactions
average only 1,306 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `poolside/laguna-s-2.1-20260720`: 152.7 tokens of context per token
written, in interactions averaging 93,865 tokens, which
is 72× larger.
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
median of **0.73** with a p25–p75 range of 0.54–0.96.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 16 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **2.50×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-5.6-luna-20260709` | 23.02× | 5.83 B | 45 | output_heavy |
| `bytedance-seed/seed-2.0-mini-20260224` | 3.38× | 19.24 B | 178 | conversational |
| `openai/gpt-5-nano-2025-08-07` | 2.60× | 2.60 B | 381 | conversational |
| `mistralai/mistral-small-24b-instruct-2501` | 2.58× | 28.79 B | 570 | conversational |
| `google/gemma-3n-e4b-it` | 2.53× | 7.31 B | 460 | conversational |
| `inclusionai/ling-3.0-flash-20260723` | 1.85× | 184.13 B | 31 | conversational |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 1.82× | 12.14 T | 80 | agentic |
| `qwen/qwen3-max` | 1.61× | 10.79 B | 334 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-4o-2024-05-13` | 0.01× | 3.84 B | 832 | extractive |
| `openai/gpt-oss-20b` | 0.02× | 39.66 B | 383 | conversational |
| `google/gemma-4-26b-a4b-it-20260403` | 0.08× | 60.14 B | 142 | conversational |
| `google/gemini-3.6-flash-20260721` | 0.10× | 6.18 T | 33 | agentic |
| `perceptron/perceptron-mk1-20260512` | 0.15× | 6.84 B | 103 | extractive |
| `nvidia/nemotron-3.5-lightning-20260807` | 0.17× | 106.19 B | 12 | agentic |
| `qwen/qwen3.7-max-20260520` | 0.21× | 396.08 B | 94 | agentic |
| `amazon/nova-2-lite-v1` | 0.21× | 6.80 B | 264 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$194.4 M per month** across
403 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 7.2% | 43.7% | 6.05x |
| `moonshotai` | 2.5% | 10.3% | 4.10x |
| `openai` | 11.2% | 9.6% | 0.86x |
| `z-ai` | 5.5% | 8.5% | 1.54x |
| `google` | 8.6% | 6.2% | 0.72x |
| `deepseek` | 24.2% | 5.8% | 0.24x |
| `nvidia` | 5.3% | 4.0% | 0.76x |
| `xiaomi` | 10.3% | 2.6% | 0.25x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,088**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **53.2%** of
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
**8.70%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.42% |
| **extractive** | 3.99% |
| **output_heavy** | 2.55% |
| **conversational** | 1.81% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 718 endpoints serving multi-provider models,
**460 are dominated** (64.1%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `deepseek/deepseek-v4-flash-20260731` | AtlasCloud | $1.32 | 54 tok/s | Relace | 20 |
| `z-ai/glm-5.2-20260616` | Fireworks | $4.40 | 52 tok/s | Baidu | 19 |
| `z-ai/glm-5.2-20260616` | Venice | $4.40 | 54 tok/s | Baidu | 18 |
| `moonshotai/kimi-k2.6-20260420` | Moonshot AI | $4.00 | 27 tok/s | Baidu | 15 |
| `z-ai/glm-5.1-20260406` | Z.AI | $4.40 | 23 tok/s | Baidu | 14 |
| `~deepseek/deepseek-v4-flash-latest` | Together | $0.28 | 36 tok/s | Relace | 14 |
| `google/gemma-4-31b-it-20260402` | SambaNova | $1.15 | 18 tok/s | DeepInfra | 14 |
| `z-ai/glm-5.2-20260616` | GMICloud | $4.40 | 57 tok/s | DigitalOcean | 14 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-08-22` and `2026-08-23`,
**2.25%** of 444 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.52 | -0.65 to -0.39 | 0.435 | 55 | yes |
| **all** | request weighted | -0.28 | -0.74 to +0.18 | 0.040 | 374 | no |
| **conversational** | request weighted | -0.54 | -1.24 to +0.17 | 0.122 | 256 | no |
| **extractive** | request weighted | +0.23 | -0.66 to +1.12 | 0.021 | 23 | no |
| **output_heavy** | request weighted | -0.03 | -0.41 to +0.34 | 0.001 | 40 | no |
| **agentic** | unweighted | -0.26 | -0.65 to +0.13 | 0.026 | 55 | no |
| **all** | unweighted | -0.49 | -0.74 to -0.24 | 0.047 | 374 | yes |
| **conversational** | unweighted | -0.71 | -0.97 to -0.45 | 0.111 | 256 | yes |
| **extractive** | unweighted | -0.07 | -0.42 to +0.27 | 0.003 | 23 | no |
| **output_heavy** | unweighted | -0.44 | -1.33 to +0.45 | 0.041 | 40 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.26, interval
-0.65 to +0.13, straddling zero). Weighting by requests, the
elasticity is **-0.52** (-0.65 to -0.39) and
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
| ≥2 days silent | 24 | 382 | 97.6% | 94.7% |
| ≥3 days silent | 16 | 390 | 98.2% | 96.7% |
| ≥7 days silent | 6 | 400 | 98.8% | 97.9% |
| ≥14 days silent | 3 | 403 | 99.7% | 98.8% |

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
