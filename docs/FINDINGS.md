# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-08-29` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 595 model-variants, 355.16 T
tokens and 18.85 B requests over the trailing 30 days.


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
| **agentic** | 68 | 274.92 T | 77.4% | 52.4 | 51,887 | large contexts, terse output, very large interactions |
| **conversational** | 287 | 76.81 T | 21.6% | 10.0 | 3,820 | moderate context per output token, human-sized interactions |
| **unclassified** | 121 | 2.07 T | 0.6% | — | 28 | insufficient data to classify |
| **extractive** | 29 | 1.21 T | 0.3% | 36.3 | 7,420 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 90 | 157.78 B | 0.0% | 0.5 | 4,452 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **77.4% of all tokens**
while being 68 of 595 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
21.6%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 370.5 | 1,327 | 21.14 B | extractive |
| `thinkingmachines/inkling-20260715` | 166.6 | 67,264 | 144.99 B | agentic |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 164.2 | 104,691 | 14.65 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 146.4 | 91,937 | 6.93 T | agentic |
| `tencent/hy4-preview-20260827` | 142.4 | 138,908 | 363.79 B | agentic |
| `xiaomi/mimo-v2.5-20260422` | 131.5 | 76,432 | 29.83 T | agentic |
| `poolside/laguna-xs-2.1-20260625` | 120.4 | 55,442 | 641.52 B | agentic |
| `minimax/minimax-m3-20260531` | 116.6 | 73,658 | 1.12 T | agentic |
| `thinkingmachines/inkling-small-20260730` | 96.8 | 46,881 | 58.15 B | agentic |
| `nvidia/nemotron-3.5-lightning-20260807` | 95.7 | 72,091 | 2.16 T | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
370.5 tokens of context per token written, but its interactions
average only 1,327 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `thinkingmachines/inkling-20260715`: 166.6 tokens of context per token
written, in interactions averaging 67,264 tokens, which
is 51× larger.
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


Across 222 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.93** with a p25–p75 range of 0.70–1.17.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 18 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.76×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `minimax/minimax-m2.7-20260318` | 16.94× | 80.79 B | 164 | agentic |
| `minimax/minimax-m3-20260531` | 16.26× | 1.12 T | 90 | agentic |
| `thinkingmachines/inkling-20260715` | 7.32× | 144.99 B | 43 | agentic |
| `thinkingmachines/inkling-small-20260730` | 5.91× | 58.15 B | 30 | agentic |
| `ibm-granite/granite-4.0-h-micro` | 5.59× | 2.65 B | 313 | conversational |
| `google/gemini-3.7-flash-20260813` | 2.88× | 21.79 B | 16 | conversational |
| `bytedance-seed/seed-2.0-mini-20260224` | 2.69× | 29.83 B | 184 | conversational |
| `openai/gpt-oss-20b` | 2.52× | 773.13 B | 389 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `nvidia/nemotron-3.5-lightning-20260807` | 0.00× | 2.16 T | 18 | agentic |
| `google/gemini-3.6-flash-20260721` | 0.02× | 2.62 B | 39 | conversational |
| `google/gemma-4-26b-a4b-it-20260403` | 0.08× | 48.06 B | 148 | conversational |
| `anthropic/claude-4.7-opus-20260416` | 0.20× | 1.41 T | 135 | agentic |
| `openai/gpt-audio-mini` | 0.23× | 4.12 B | 222 | output_heavy |
| `mistralai/mistral-large-2512` | 0.24× | 38.37 B | 271 | conversational |
| `nvidia/nemotron-3-nano-30b-a3b` | 0.25× | 49.85 B | 258 | conversational |
| `mistralai/mistral-large` | 0.26× | 2.94 B | 915 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$210.9 M per month** across
431 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 6.3% | 41.7% | 6.60x |
| `openai` | 11.5% | 16.1% | 1.39x |
| `moonshotai` | 2.2% | 9.8% | 4.56x |
| `deepseek` | 23.1% | 8.2% | 0.35x |
| `google` | 8.3% | 8.2% | 0.98x |
| `nvidia` | 5.5% | 3.8% | 0.69x |
| `x-ai` | 0.7% | 2.5% | 3.33x |
| `xiaomi` | 9.1% | 2.4% | 0.27x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,266**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **53.6%** of
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
**10.06%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.71% |
| **extractive** | 2.79% |
| **output_heavy** | 1.93% |
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

Of 847 endpoints serving multi-provider models,
**569 are dominated** (67.2%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `~deepseek/deepseek-v4-flash-latest` | Reka | $0.66 | 22 tok/s | Baidu | 21 |
| `z-ai/glm-5.2-20260616` | Alibaba | $7.26 | 44 tok/s | StreamLake | 21 |
| `z-ai/glm-5.3-flash-20260826` | Morph | $0.50 | 7 tok/s | Relace | 20 |
| `z-ai/glm-5.3-flash-20260826` | Parasail | $0.50 | 11 tok/s | Relace | 19 |
| `~deepseek/deepseek-v4-flash-latest` | AtlasCloud | $1.32 | 48 tok/s | Baidu | 18 |
| `z-ai/glm-5.3-flash-20260826` | Phala | $0.50 | 20 tok/s | Relace | 18 |
| `deepseek/deepseek-v4-flash-20260731` | SiliconFlow | $0.66 | 30 tok/s | Baidu | 18 |
| `~deepseek/deepseek-v4-flash-latest` | Phala | $0.66 | 40 tok/s | Baidu | 17 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-08-28` and `2026-08-29`,
**0.87%** of 460 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.60 | -0.76 to -0.45 | 0.478 | 57 | yes |
| **all** | request weighted | -0.20 | -0.62 to +0.23 | 0.018 | 400 | no |
| **conversational** | request weighted | -0.34 | -0.99 to +0.31 | 0.047 | 269 | no |
| **extractive** | request weighted | -0.22 | -1.23 to +0.79 | 0.023 | 25 | no |
| **output_heavy** | request weighted | -0.11 | -0.37 to +0.14 | 0.019 | 49 | no |
| **agentic** | unweighted | -0.25 | -0.61 to +0.10 | 0.028 | 57 | no |
| **all** | unweighted | -0.61 | -0.92 to -0.30 | 0.049 | 400 | yes |
| **conversational** | unweighted | -1.02 | -1.33 to -0.71 | 0.161 | 269 | yes |
| **extractive** | unweighted | -0.31 | -0.71 to +0.09 | 0.058 | 25 | no |
| **output_heavy** | unweighted | +0.63 | -0.65 to +1.91 | 0.038 | 49 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.25, interval
-0.61 to +0.10, straddling zero). Weighting by requests, the
elasticity is **-0.60** (-0.76 to -0.45) and
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
| ≥2 days silent | 53 | 382 | 94.1% | 88.2% |
| ≥3 days silent | 23 | 412 | 97.2% | 92.9% |
| ≥7 days silent | 11 | 424 | 98.6% | 97.7% |
| ≥14 days silent | 5 | 430 | 98.9% | 98.5% |

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
