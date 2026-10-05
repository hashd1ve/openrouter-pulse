# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-10-05` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 654 model-variants, 596.98 T
tokens and 27.70 B requests over the trailing 30 days.


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
| **agentic** | 92 | 478.14 T | 80.1% | 53.9 | 52,762 | large contexts, terse output, very large interactions |
| **conversational** | 305 | 115.02 T | 19.3% | 9.7 | 4,036 | moderate context per output token, human-sized interactions |
| **unclassified** | 134 | 2.63 T | 0.4% | — | 37 | insufficient data to classify |
| **extractive** | 25 | 1.04 T | 0.2% | 42.1 | 5,159 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 98 | 145.84 B | 0.0% | 0.5 | 4,455 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **80.1% of all tokens**
while being 92 of 654 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
19.3%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `upstage/solar-decide-20260928` | 2,145.4 | 5,093 | 5.60 B | extractive |
| `meta-llama/llama-guard-4-12b` | 236.2 | 793 | 8.74 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 206.8 | 131,806 | 20.45 T | agentic |
| `upstage/solar-mini4-20260922` | 147.7 | 55,833 | 481.30 B | agentic |
| `thinkingmachines/inkling-small-20260730` | 125.1 | 57,109 | 503.52 B | agentic |
| `minimax/minimax-m3-20260531` | 120.5 | 76,008 | 1.58 T | agentic |
| `tencent/hy4-preview-20260827` | 113.0 | 115,764 | 49.29 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 107.1 | 81,796 | 4.70 T | agentic |
| `openai/gpt-6-astra-20260903` | 106.1 | 65,290 | 5.05 T | agentic |
| `xiaomi/mimo-v2.5-20260422` | 105.8 | 69,501 | 18.91 T | agentic |

**Why both axes.** The top of this ranking is `upstage/solar-decide-20260928` at
2,145.4 tokens of context per token written, but its interactions
average only 5,093 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 206.8 tokens of context per token
written, in interactions averaging 131,806 tokens, which
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


Across 251 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.74** with a p25–p75 range of 0.53–0.96.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 17 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **2.14×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `qwen/qwen3.8-27b-20260814` | 7.93× | 243.17 B | 52 | agentic |
| `openai/gpt-5.3-codex-20260224` | 4.80× | 228.72 B | 223 | agentic |
| `upstage/solar-mini4-20260922` | 3.37× | 481.30 B | 12 | agentic |
| `stepfun/step-3.7-flash-20260528` | 3.20× | 337.54 B | 130 | conversational |
| `thinkingmachines/inkling-small-20260730` | 3.06× | 33.84 B | 67 | conversational |
| `qwen/qwen3.8-2.4t-a95b-20260812` | 2.99× | 121.28 B | 54 | conversational |
| `deepseek/deepseek-v4.1-flash-20260910` | 2.71× | 4.74 B | 25 | output_heavy |
| `inclusionai/ling-3.0-flash-vl-20260910` | 2.65× | 48.40 B | 25 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `tencent/hy-mt2-1.8b-20260521` | 0.05× | 3.00 B | 46 | conversational |
| `google/gemini-3.8-flash-20260902` | 0.07× | 12.88 B | 33 | conversational |
| `google/gemini-3.1-flash-lite-20260507` | 0.09× | 11.32 B | 151 | conversational |
| `openai/gpt-5.6-sol-20260709` | 0.11× | 4.57 B | 88 | conversational |
| `qwen/qwen-plus-2025-07-28` | 0.11× | 2.67 B | 392 | conversational |
| `upstage/solar-pro4-20260810` | 0.11× | 6.04 T | 56 | agentic |
| `google/gemini-3.7-flash-20260813` | 0.11× | 10.66 B | 53 | output_heavy |
| `ibm-granite/granite-4.0-h-micro` | 0.12× | 17.96 B | 350 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$263.6 M per month** across
450 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `openai` | 14.1% | 23.3% | 1.66x |
| `anthropic` | 3.8% | 23.0% | 5.98x |
| `tencent` | 10.7% | 16.6% | 1.54x |
| `deepseek` | 22.6% | 10.9% | 0.48x |
| `moonshotai` | 1.3% | 6.4% | 4.88x |
| `z-ai` | 12.8% | 5.8% | 0.45x |
| `google` | 5.0% | 4.6% | 0.92x |
| `xiaomi` | 6.4% | 2.6% | 0.41x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,627**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **58.1%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.938** by value. Both are extreme; a
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
**6.38%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.20% |
| **extractive** | 2.97% |
| **conversational** | 1.65% |
| **output_heavy** | 1.28% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,107 endpoints serving multi-provider models,
**755 are dominated** (68.2%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `~z-ai/glm-flash-latest` | Sail Research | $0.60 | 13 tok/s | DeepInfra | 27 |
| `~deepseek/deepseek-flash-latest` | DekaLLM | $2.40 | 32 tok/s | Decart | 27 |
| `z-ai/glm-5.3-flash-20260826` | Sail Research | $0.60 | 16 tok/s | DeepInfra | 26 |
| `deepseek/deepseek-v4.1-flash-20260910` | DekaLLM | $2.40 | 42 tok/s | Decart | 26 |
| `z-ai/glm-5.3-20260816` | Venice | $4.40 | 35 tok/s | SiliconFlow | 26 |
| `~z-ai/glm-latest` | Venice | $4.40 | 37 tok/s | SiliconFlow | 26 |
| `z-ai/glm-5.3-flash-20260826` | OpenInference | $0.65 | 17 tok/s | DeepInfra | 25 |
| `~z-ai/glm-flash-latest` | OpenInference | $0.65 | 17 tok/s | DeepInfra | 24 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-10-04` and `2026-10-05`,
**0.38%** of 520 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.44 | -0.67 to -0.21 | 0.172 | 79 | yes |
| **all** | request weighted | +0.36 | +0.08 to +0.65 | 0.036 | 415 | yes |
| **conversational** | request weighted | +0.55 | +0.00 to +1.10 | 0.084 | 274 | yes |
| **extractive** | request weighted | +0.46 | -0.36 to +1.27 | 0.109 | 16 | no |
| **output_heavy** | request weighted | -0.11 | -0.48 to +0.25 | 0.017 | 46 | no |
| **agentic** | unweighted | -0.52 | -0.84 to -0.20 | 0.093 | 79 | yes |
| **all** | unweighted | -0.40 | -0.66 to -0.15 | 0.024 | 415 | yes |
| **conversational** | unweighted | -0.62 | -0.90 to -0.34 | 0.078 | 274 | yes |
| **extractive** | unweighted | -0.15 | -0.67 to +0.38 | 0.007 | 16 | no |
| **output_heavy** | unweighted | +0.41 | -0.59 to +1.42 | 0.015 | 46 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.52, interval
-0.84 to -0.20, straddling zero). Weighting by requests, the
elasticity is **-0.44** (-0.67 to -0.21) and
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
| ≥2 days silent | 46 | 406 | 91.8% | 89.3% |
| ≥3 days silent | 44 | 408 | 92.1% | 89.6% |
| ≥7 days silent | 43 | 409 | 92.1% | 90.2% |
| ≥14 days silent | 23 | 429 | 95.8% | 94.4% |

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
