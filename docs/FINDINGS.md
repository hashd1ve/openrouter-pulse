# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-09-11` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 630 model-variants, 450.86 T
tokens and 21.66 B requests over the trailing 30 days.


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
| **agentic** | 81 | 347.90 T | 77.2% | 56.9 | 51,748 | large contexts, terse output, very large interactions |
| **conversational** | 306 | 99.67 T | 22.1% | 10.0 | 3,945 | moderate context per output token, human-sized interactions |
| **unclassified** | 125 | 2.17 T | 0.5% | — | 28 | insufficient data to classify |
| **extractive** | 22 | 994.56 B | 0.2% | 36.6 | 8,904 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 96 | 127.54 B | 0.0% | 0.4 | 4,412 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **77.2% of all tokens**
while being 81 of 630 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
22.1%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 343.3 | 1,172 | 13.53 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 187.2 | 116,825 | 17.41 T | agentic |
| `thinkingmachines/inkling-20260715` | 143.6 | 73,339 | 682.49 B | agentic |
| `xiaomi/mimo-v2.5-20260422` | 138.5 | 71,501 | 28.51 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 128.9 | 85,090 | 6.14 T | agentic |
| `minimax/minimax-m3-20260531` | 119.2 | 76,887 | 8.17 T | agentic |
| `thinkingmachines/inkling-small-20260730` | 116.9 | 55,330 | 253.59 B | agentic |
| `tencent/hy4-preview-20260827` | 110.0 | 116,974 | 30.05 T | agentic |
| `poolside/laguna-xs-2.1-20260625` | 108.5 | 51,615 | 507.13 B | agentic |
| `openai/gpt-6-astra-20260903` | 98.2 | 62,042 | 602.61 B | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
343.3 tokens of context per token written, but its interactions
average only 1,172 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 187.2 tokens of context per token
written, in interactions averaging 116,825 tokens, which
is 100× larger.
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


Across 234 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **1.03** with a p25–p75 range of 0.80–1.34.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 21 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.87×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `tencent/hy-mt2-7b-20260521` | 10.80× | 578.03 M | 23 | conversational |
| `ibm-granite/granite-4.0-h-micro` | 10.39× | 15.70 B | 326 | conversational |
| `tencent/hy-mt2-1.8b-20260521` | 9.28× | 735.33 M | 22 | conversational |
| `tencent/hy-mt2-30b-a3b-20260521` | 6.87× | 1.74 B | 22 | conversational |
| `google/gemini-2.5-flash-lite` | 3.20× | 5.48 B | 416 | conversational |
| `dots-studio/dots-3-note-preview-20260813` | 2.84× | 791.37 B | 28 | agentic |
| `qwen/qwen3.5-122b-a10b-20260224` | 2.81× | 52.15 B | 198 | conversational |
| `meta-llama/llama-4-scout-17b-16e-instruct` | 2.73× | 104.44 B | 524 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `meta/muse-spark-1.1-20260709` | 0.09× | 92.11 B | 57 | agentic |
| `meta-llama/llama-3.2-1b-instruct` | 0.11× | 2.33 B | 716 | output_heavy |
| `google/gemini-3.6-flash-20260721` | 0.14× | 3.77 T | 52 | agentic |
| `openai/gpt-4o-2024-05-13` | 0.15× | 788.77 M | 851 | extractive |
| `stepfun/step-3.7-flash-20260528` | 0.15× | 2.17 T | 106 | agentic |
| `openai/gpt-audio-mini` | 0.26× | 4.24 B | 235 | output_heavy |
| `google/gemma-4-26b-a4b-it-20260403` | 0.27× | 22.07 B | 161 | conversational |
| `anthropic/claude-4.7-opus-20260416` | 0.32× | 1.04 T | 148 | agentic |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$261.1 M per month** across
457 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 5.2% | 29.9% | 5.72x |
| `openai` | 13.3% | 14.7% | 1.11x |
| `tencent` | 12.9% | 11.2% | 0.87x |
| `z-ai` | 10.4% | 10.6% | 1.02x |
| `moonshotai` | 1.8% | 8.8% | 4.81x |
| `google` | 7.3% | 7.5% | 1.03x |
| `deepseek` | 19.8% | 7.5% | 0.38x |
| `x-ai` | 0.6% | 2.2% | 3.46x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,258**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **54.3%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.945** by value. Both are extreme; a
national income distribution above 0.6 is considered severe.


### The sticker price is not the price

Traffic is overwhelmingly prompt-heavy, and prompt tokens cost less than
completions. Blended across each model's real token mix, the price actually paid
per token is a median **0.36x** the headline output price, so the
sticker overstates unit cost by about **2.8x**.

Anyone comparing models on `$/M output` is getting this wrong.


## 5. The context window arms race is mostly unused

Dividing mean tokens per request by the advertised context length asks how much
of the window the traffic actually touches. Token-weighted across the market:
**6.86%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.84% |
| **extractive** | 4.59% |
| **conversational** | 1.77% |
| **output_heavy** | 1.56% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 942 endpoints serving multi-provider models,
**627 are dominated** (66.6%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-flash-20260826` | NextBit | $0.50 | 2 tok/s | DeepInfra | 22 |
| `~z-ai/glm-flash-latest` | NextBit | $0.50 | 3 tok/s | DeepInfra | 21 |
| `z-ai/glm-5.3-flash-20260826` | Parasail | $0.50 | 3 tok/s | DeepInfra | 21 |
| `~z-ai/glm-flash-latest` | Parasail | $0.50 | 3 tok/s | DeepInfra | 21 |
| `z-ai/glm-5.3-flash-20260826` | DigitalOcean | $0.50 | 15 tok/s | DeepInfra | 20 |
| `~z-ai/glm-flash-latest` | DigitalOcean | $0.50 | 15 tok/s | DeepInfra | 20 |
| `z-ai/glm-5.2-20260616` | Alibaba | $7.26 | 71 tok/s | DigitalOcean | 17 |
| `z-ai/glm-5.3-20260816` | Z.AI | $4.40 | 36 tok/s | Novita | 17 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-09-10` and `2026-09-11`,
**1.20%** of 502 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.64 | -0.83 to -0.44 | 0.427 | 66 | yes |
| **all** | request weighted | -0.17 | -0.55 to +0.21 | 0.010 | 416 | no |
| **conversational** | request weighted | -0.26 | -0.88 to +0.36 | 0.023 | 281 | no |
| **extractive** | request weighted | +0.59 | +0.22 to +0.97 | 0.267 | 18 | yes |
| **output_heavy** | request weighted | -0.06 | -0.33 to +0.21 | 0.005 | 51 | no |
| **agentic** | unweighted | -0.43 | -0.76 to -0.11 | 0.074 | 66 | yes |
| **all** | unweighted | -0.67 | -0.94 to -0.40 | 0.072 | 416 | yes |
| **conversational** | unweighted | -0.97 | -1.27 to -0.68 | 0.171 | 281 | yes |
| **extractive** | unweighted | -0.14 | -0.54 to +0.26 | 0.014 | 18 | no |
| **output_heavy** | unweighted | -0.09 | -0.82 to +0.65 | 0.002 | 51 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.43, interval
-0.76 to -0.11, straddling zero). Weighting by requests, the
elasticity is **-0.64** (-0.83 to -0.44) and
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
| ≥2 days silent | 71 | 390 | 91.5% | 84.1% |
| ≥3 days silent | 68 | 393 | 91.5% | 84.1% |
| ≥7 days silent | 57 | 404 | 93.9% | 86.3% |
| ≥14 days silent | 41 | 420 | 96.5% | 90.6% |

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
