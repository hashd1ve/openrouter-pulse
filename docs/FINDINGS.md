# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-08-27` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 573 model-variants, 341.33 T
tokens and 18.61 B requests over the trailing 30 days.


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
| **agentic** | 68 | 262.46 T | 76.9% | 51.8 | 50,523 | large contexts, terse output, very large interactions |
| **conversational** | 273 | 75.96 T | 22.3% | 10.0 | 3,725 | moderate context per output token, human-sized interactions |
| **unclassified** | 121 | 2.17 T | 0.6% | — | 31 | insufficient data to classify |
| **extractive** | 30 | 592.79 B | 0.2% | 41.9 | 8,324 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 81 | 148.20 B | 0.0% | 0.4 | 4,520 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **76.9% of all tokens**
while being 68 of 573 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
22.3%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 369.9 | 1,321 | 21.89 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 158.2 | 101,992 | 13.78 T | agentic |
| `thinkingmachines/inkling-20260715` | 157.1 | 57,065 | 72.98 B | agentic |
| `poolside/laguna-s-2.1-20260720` | 148.4 | 92,587 | 6.63 T | agentic |
| `xiaomi/mimo-v2.5-20260422` | 128.6 | 74,885 | 28.36 T | agentic |
| `poolside/laguna-xs-2.1-20260625` | 124.1 | 56,024 | 664.14 B | agentic |
| `minimax/minimax-m3-20260531` | 109.6 | 63,260 | 195.71 B | agentic |
| `anthropic/claude-opus-5-fast-20260723` | 97.4 | 86,294 | 136.08 B | agentic |
| `nvidia/nemotron-3.5-lightning-20260807` | 97.0 | 72,861 | 2.07 T | agentic |
| `z-ai/glm-5.3-flash-20260826` | 87.1 | 68,425 | 360.76 B | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
369.9 tokens of context per token written, but its interactions
average only 1,321 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 158.2 tokens of context per token
written, in interactions averaging 101,992 tokens, which
is 77× larger.
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


Across 217 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.97** with a p25–p75 range of 0.76–1.19.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 18 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.94×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `minimax/minimax-m3-20260531` | 19.28× | 195.71 B | 88 | agentic |
| `openai/gpt-audio-mini` | 9.39× | 4.09 B | 220 | output_heavy |
| `thinkingmachines/inkling-20260715` | 8.50× | 72.98 B | 41 | agentic |
| `ibm-granite/granite-4.0-h-micro` | 5.90× | 1.75 B | 311 | conversational |
| `venice/uncensored` | 3.85× | 3.62 B | 414 | conversational |
| `google/gemini-3.7-flash-20260813` | 3.60× | 4.59 T | 14 | agentic |
| `qwen/qwen3.5-397b-a17b-20260216` | 3.29× | 125.95 B | 192 | conversational |
| `bytedance-seed/seed-2.0-mini-20260224` | 2.83× | 25.58 B | 182 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `google/gemma-4-26b-a4b-it-20260403` | 0.09× | 52.44 B | 146 | conversational |
| `google/gemini-3.6-flash-20260721` | 0.10× | 6.33 T | 37 | agentic |
| `openai/gpt-4o-2024-05-13` | 0.17× | 3.81 B | 836 | extractive |
| `meta/muse-glimmer-30b-20260810` | 0.19× | 71.20 B | 18 | conversational |
| `nvidia/nemotron-3-nano-30b-a3b` | 0.29× | 51.62 B | 256 | conversational |
| `meta/muse-spark-1.2-20260805` | 0.31× | 270.23 B | 22 | agentic |
| `microsoft/phi-4` | 0.31× | 2.56 B | 594 | conversational |
| `meta-llama/llama-3.1-70b-instruct` | 0.32× | 34.61 B | 765 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$187.4 M per month** across
407 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 6.6% | 36.8% | 5.57x |
| `openai` | 11.0% | 13.3% | 1.21x |
| `z-ai` | 5.3% | 11.5% | 2.17x |
| `moonshotai` | 2.3% | 11.1% | 4.92x |
| `deepseek` | 23.3% | 9.1% | 0.39x |
| `google` | 8.4% | 6.5% | 0.77x |
| `x-ai` | 0.8% | 2.7% | 3.58x |
| `xiaomi` | 9.0% | 2.7% | 0.29x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**2,930**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **50.4%** of
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
**8.32%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.13% |
| **extractive** | 3.81% |
| **output_heavy** | 2.07% |
| **conversational** | 1.80% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 804 endpoints serving multi-provider models,
**526 are dominated** (65.4%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.2-20260616` | BaseTen | $6.60 | 21 tok/s | Baidu | 31 |
| `z-ai/glm-5.2-20260616` | BaseTen | $4.40 | 36 tok/s | Baidu | 21 |
| `z-ai/glm-5.2-20260616` | Venice | $4.40 | 44 tok/s | Baidu | 18 |
| `~deepseek/deepseek-v4-flash-latest` | AtlasCloud | $1.32 | 40 tok/s | Relace | 17 |
| `~deepseek/deepseek-v4-flash-latest` | StreamLake | $0.66 | 36 tok/s | Relace | 17 |
| `moonshotai/kimi-k2.6-20260420` | Phala | $4.60 | 23 tok/s | Decart | 16 |
| `z-ai/glm-5.2-20260616` | Sail Research | $3.15 | 7 tok/s | Baidu | 15 |
| `deepseek/deepseek-v4-flash-20260731` | StreamLake | $0.66 | 36 tok/s | Relace | 15 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-08-26` and `2026-08-27`,
**1.35%** of 445 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.52 | -0.63 to -0.41 | 0.537 | 59 | yes |
| **all** | request weighted | -0.29 | -0.71 to +0.13 | 0.042 | 379 | no |
| **conversational** | request weighted | -0.32 | -0.97 to +0.32 | 0.044 | 255 | no |
| **extractive** | request weighted | +0.21 | -0.28 to +0.70 | 0.041 | 26 | no |
| **output_heavy** | request weighted | -0.09 | -0.38 to +0.20 | 0.011 | 39 | no |
| **agentic** | unweighted | -0.21 | -0.57 to +0.15 | 0.019 | 59 | no |
| **all** | unweighted | -0.55 | -0.78 to -0.32 | 0.066 | 379 | yes |
| **conversational** | unweighted | -0.71 | -0.93 to -0.48 | 0.118 | 255 | yes |
| **extractive** | unweighted | -0.22 | -0.46 to +0.02 | 0.049 | 26 | no |
| **output_heavy** | unweighted | -0.96 | -1.73 to -0.19 | 0.189 | 39 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.21, interval
-0.57 to +0.15, straddling zero). Weighting by requests, the
elasticity is **-0.52** (-0.63 to -0.41) and
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
| ≥2 days silent | 35 | 376 | 96.6% | 89.8% |
| ≥3 days silent | 28 | 383 | 97.3% | 92.0% |
| ≥7 days silent | 13 | 398 | 98.6% | 98.1% |
| ≥14 days silent | 5 | 406 | 98.9% | 98.4% |

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
