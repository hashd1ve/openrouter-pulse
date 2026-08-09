# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-08-09` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 529 model-variants, 259.71 T
tokens and 16.42 B requests over the trailing 30 days.


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
| **agentic** | 59 | 188.68 T | 72.6% | 50.3 | 46,438 | large contexts, terse output, very large interactions |
| **conversational** | 268 | 67.77 T | 26.1% | 10.1 | 3,980 | moderate context per output token, human-sized interactions |
| **unclassified** | 104 | 2.30 T | 0.9% | — | 30 | insufficient data to classify |
| **extractive** | 25 | 821.19 B | 0.3% | 40.1 | 8,734 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 73 | 134.75 B | 0.1% | 0.5 | 4,410 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **72.6% of all tokens**
while being 59 of 529 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
26.1%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 252.2 | 934 | 18.14 B | extractive |
| `poolside/laguna-s-2.1-20260720` | 161.0 | 95,136 | 2.78 T | agentic |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 160.2 | 104,333 | 11.40 T | agentic |
| `poolside/laguna-m.1-20260312` | 136.6 | 68,924 | 1.08 T | agentic |
| `xiaomi/mimo-v2.5-20260422` | 116.9 | 67,936 | 34.07 T | agentic |
| `poolside/laguna-xs-2.1-20260625` | 99.8 | 56,191 | 605.52 B | agentic |
| `perceptron/perceptron-mk1-20260512` | 97.0 | 8,934 | 10.49 B | extractive |
| `anthropic/claude-opus-5-fast-20260723` | 96.4 | 84,908 | 87.09 B | agentic |
| `stepfun/step-3.7-flash-20260528` | 86.4 | 68,246 | 5.90 T | agentic |
| `anthropic/claude-4.8-opus-fast-20260528` | 83.6 | 57,273 | 79.33 B | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
252.2 tokens of context per token written, but its interactions
average only 934 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `poolside/laguna-s-2.1-20260720`: 161.0 tokens of context per token
written, in interactions averaging 95,136 tokens, which
is 102× larger.
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


Across 205 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.73** with a p25–p75 range of 0.56–0.95.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 11 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.58×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `perceptron/perceptron-mk1-20260512` | 7.04× | 10.49 B | 89 | extractive |
| `qwen/qwen3-30b-a3b-04-28` | 5.11× | 11.88 B | 468 | conversational |
| `nex-agi/nex-n2-mini` | 3.84× | 47.24 B | 46 | conversational |
| `meta-llama/llama-3.1-70b-instruct` | 3.36× | 30.11 B | 747 | conversational |
| `tencent/hy3-20260706` | 2.87× | 15.32 T | 34 | agentic |
| `openai/gpt-5.6-luna-20260709` | 2.76× | 6.50 T | 31 | agentic |
| `openai/gpt-5.6-terra-pro-20260709` | 2.54× | 133.04 B | 31 | agentic |
| `openai/gpt-5.6-luna-pro-20260709` | 2.20× | 853.33 B | 31 | agentic |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `ibm-granite/granite-4.0-h-micro` | 0.02× | 29.43 B | 293 | agentic |
| `openai/gpt-4o-2024-05-13` | 0.02× | 3.75 B | 818 | extractive |
| `amazon/nova-2-lite-v1` | 0.07× | 15.98 B | 250 | conversational |
| `google/gemma-2-27b-it` | 0.08× | 644.55 M | 757 | conversational |
| `openai/o4-mini-2025-04-16` | 0.14× | 44.68 B | 480 | conversational |
| `openai/gpt-5-2025-08-07` | 0.17× | 175.93 B | 367 | conversational |
| `meta/muse-spark-1.1-20260709` | 0.17× | 159.44 B | 24 | agentic |
| `openai/gpt-5.2-20251211` | 0.19× | 361.70 B | 242 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$172.4 M per month** across
378 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 9.3% | 43.1% | 4.62x |
| `openai` | 8.6% | 18.5% | 2.15x |
| `moonshotai` | 2.6% | 8.6% | 3.37x |
| `google` | 8.3% | 6.6% | 0.80x |
| `deepseek` | 19.5% | 6.4% | 0.33x |
| `xiaomi` | 14.3% | 3.4% | 0.24x |
| `tencent` | 12.5% | 2.6% | 0.21x |
| `x-ai` | 0.9% | 2.4% | 2.83x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**2,927**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **49.6%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.936** by value. Both are extreme; a
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
**8.72%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.66% |
| **extractive** | 3.85% |
| **conversational** | 1.93% |
| **output_heavy** | 1.87% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 640 endpoints serving multi-provider models,
**415 are dominated** (64.8%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `deepseek/deepseek-v4-flash-20260731` | Mancer 2 | $0.50 | 32 tok/s | Baidu | 20 |
| `~deepseek/deepseek-v4-flash-latest` | Mancer 2 | $0.50 | 31 tok/s | Baidu | 20 |
| `deepseek/deepseek-v4-flash-20260731` | Phala | $0.40 | 39 tok/s | Baidu | 17 |
| `~deepseek/deepseek-v4-flash-latest` | Phala | $0.40 | 38 tok/s | Baidu | 17 |
| `deepseek/deepseek-v4-flash-20260731` | Venice | $0.35 | 48 tok/s | Baidu | 16 |
| `deepseek/deepseek-v4-flash-20260731` | Io Net | $0.32 | 49 tok/s | Baidu | 15 |
| `~deepseek/deepseek-v4-flash-latest` | Io Net | $0.32 | 43 tok/s | Baidu | 15 |
| `deepseek/deepseek-v4-flash-20260731` | AkashML | $0.28 | 50 tok/s | Baidu | 14 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-08-08` and `2026-08-09`,
**2.37%** of 422 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.45 | -0.63 to -0.26 | 0.401 | 53 | yes |
| **all** | request weighted | -0.18 | -0.54 to +0.18 | 0.015 | 356 | no |
| **conversational** | request weighted | -0.24 | -0.71 to +0.23 | 0.023 | 245 | no |
| **extractive** | request weighted | -0.09 | -1.15 to +0.97 | 0.004 | 21 | no |
| **output_heavy** | request weighted | +0.06 | -0.19 to +0.31 | 0.006 | 37 | no |
| **agentic** | unweighted | -0.23 | -0.69 to +0.22 | 0.016 | 53 | no |
| **all** | unweighted | -0.61 | -0.86 to -0.35 | 0.058 | 356 | yes |
| **conversational** | unweighted | -0.83 | -1.11 to -0.54 | 0.112 | 245 | yes |
| **extractive** | unweighted | -0.25 | -0.86 to +0.36 | 0.015 | 21 | no |
| **output_heavy** | unweighted | -0.76 | -1.38 to -0.15 | 0.106 | 37 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.23, interval
-0.69 to +0.22, straddling zero). Weighting by requests, the
elasticity is **-0.45** (-0.63 to -0.26) and
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
| ≥2 days silent | 23 | 357 | 97.6% | 92.9% |
| ≥3 days silent | 18 | 362 | 98.3% | 94.7% |
| ≥7 days silent | 15 | 365 | 98.9% | 95.3% |
| ≥14 days silent | 12 | 368 | 98.9% | 96.2% |

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
