# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-11-26` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 768 model-variants, 845.38 T
tokens and 43.17 B requests over the trailing 30 days.


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
| **agentic** | 104 | 678.45 T | 80.3% | 58.0 | 51,739 | large contexts, terse output, very large interactions |
| **conversational** | 305 | 115.88 T | 13.7% | 10.2 | 4,116 | moderate context per output token, human-sized interactions |
| **extractive** | 52 | 45.41 T | 5.4% | 63.0 | 4,239 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 179 | 5.33 T | 0.6% | — | 34 | insufficient data to classify |
| **output_heavy** | 128 | 316.40 B | 0.0% | 0.3 | 4,380 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **80.3% of all tokens**
while being 104 of 768 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
13.7%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `scaledown/classify-1-20260928` | 4,161.5 | 10,151 | 25.98 B | extractive |
| `upstage/solar-decide-20260928` | 1,552.3 | 3,607 | 6.59 B | extractive |
| `upstage/solar-decide-flash-20261008` | 1,384.8 | 2,905 | 4.36 B | extractive |
| `microsoft/microsoft-decision-1-20261009` | 882.3 | 2,998 | 136.06 B | extractive |
| `perplexity/pplx-decider-flash-v1.2-20261016` | 503.4 | 1,835 | 93.74 B | extractive |
| `cloudflare/clairic-20261029` | 499.1 | 2,074 | 3.92 B | extractive |
| `perplexity/pplx-decider-v1.2-20261016` | 464.4 | 1,967 | 1.88 T | extractive |
| `baseten/bison-1-20261120` | 460.4 | 1,878 | 3.46 B | extractive |
| `baseten/joey-1-20261029` | 446.6 | 509 | 30.96 B | extractive |
| `baseten/mammoth-1-20261021` | 432.4 | 837 | 32.65 B | extractive |

**Why both axes.** The top of this ranking is `scaledown/classify-1-20260928` at
4,161.5 tokens of context per token written, but its interactions
average only 10,151 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `thinkingmachines/inkling-2-small-20261107`: 175.5 tokens of context per token
written, in interactions averaging 176,007 tokens, which
is 17× larger.
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


Across 262 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.94** with a p25–p75 range of 0.62–1.20.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 18 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.82×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `anthropic/claude-4.5-opus-20251124` | 27.27× | 50.13 B | 367 | extractive |
| `bytedance-seed/seed-2.0-lite-20260309` | 6.49× | 41.72 B | 261 | conversational |
| `google/gemini-3-pro-image-20260528` | 6.34× | 5.65 B | 161 | output_heavy |
| `google/gemini-nano-banana-2.1-20261006` | 5.83× | 21.51 B | 51 | output_heavy |
| `scaledown/extract-20260928` | 5.45× | 17.17 B | 44 | conversational |
| `openai/gpt-3.5-turbo-0613` | 5.05× | 678.43 M | 1,036 | conversational |
| `openai/gpt-oss-20b` | 4.39× | 3.92 B | 478 | conversational |
| `qwen/qwen3.5-397b-a17b-20260216` | 4.35× | 99.77 B | 283 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `moonshotai/kimi-k2` | 0.00× | 37.98 B | 503 | agentic |
| `tencent/hy4-preview-20260827` | 0.02× | 4.34 T | 90 | agentic |
| `google/gemini-3.6-flash-20260721` | 0.03× | 2.19 B | 128 | conversational |
| `stepfun/step-5-preview-20261008` | 0.04× | 425.64 B | 49 | extractive |
| `stepfun/step-3.7-flash-20260528` | 0.06× | 687.86 B | 182 | agentic |
| `upstage/solar-mini4-20260922` | 0.08× | 1.97 T | 64 | agentic |
| `ricursiveai/ripple-65b-preview-20261104` | 0.13× | 32.58 B | 22 | conversational |
| `perceptron/perceptron-mk1-20260512` | 0.17× | 974.10 M | 198 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$392.7 M per month** across
490 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 7.6% | 49.6% | 6.49x |
| `openai` | 9.9% | 20.1% | 2.04x |
| `google` | 4.0% | 9.7% | 2.40x |
| `deepseek` | 44.1% | 4.1% | 0.09x |
| `z-ai` | 9.5% | 3.6% | 0.38x |
| `nvidia` | 4.2% | 2.6% | 0.62x |
| `moonshotai` | 2.8% | 2.1% | 0.75x |
| `tencent` | 5.3% | 1.8% | 0.33x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,252**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **54.0%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.939** by value. Both are extreme; a
national income distribution above 0.6 is considered severe.


### The sticker price is not the price

Traffic is overwhelmingly prompt-heavy, and prompt tokens cost less than
completions. Blended across each model's real token mix, the price actually paid
per token is a median **0.33x** the headline output price, so the
sticker overstates unit cost by about **3.0x**.

Anyone comparing models on `$/M output` is getting this wrong.


## 5. The context window arms race is mostly unused

Dividing mean tokens per request by the advertised context length asks how much
of the window the traffic actually touches. Token-weighted across the market:
**5.51%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 6.03% |
| **conversational** | 1.49% |
| **extractive** | 1.46% |
| **output_heavy** | 1.16% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,219 endpoints serving multi-provider models,
**856 are dominated** (70.2%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `~deepseek/deepseek-flash-latest` | Reka | $1.20 | 59 tok/s | DeepInfra | 44 |
| `deepseek/deepseek-v4.1-flash-20261017` | Reka | $1.20 | 61 tok/s | DeepInfra | 43 |
| `z-ai/glm-5.3-20260816` | Amazon Bedrock | $5.28 | 43 tok/s | Wafer | 35 |
| `~z-ai/glm-latest` | Amazon Bedrock | $5.28 | 43 tok/s | Wafer | 35 |
| `z-ai/glm-5.3-flash-20260826` | Parasail | $0.62 | 21 tok/s | Relace | 35 |
| `~z-ai/glm-flash-latest` | Parasail | $0.62 | 21 tok/s | Relace | 35 |
| `z-ai/glm-5.3-flash-20260826` | Near AI | $0.50 | 26 tok/s | Relace | 33 |
| `~z-ai/glm-flash-latest` | Near AI | $0.50 | 26 tok/s | Relace | 33 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-11-20` and `2026-11-26`,
**0.00%** of 1 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.70 | -1.09 to -0.32 | 0.381 | 96 | yes |
| **all** | request weighted | -0.49 | -0.95 to -0.02 | 0.076 | 469 | yes |
| **conversational** | request weighted | -0.23 | -0.52 to +0.07 | 0.029 | 285 | no |
| **extractive** | request weighted | -1.12 | -1.58 to -0.66 | 0.382 | 29 | yes |
| **output_heavy** | request weighted | -0.54 | -0.90 to -0.18 | 0.342 | 59 | yes |
| **agentic** | unweighted | -0.22 | -0.57 to +0.12 | 0.018 | 96 | no |
| **all** | unweighted | -0.44 | -0.67 to -0.22 | 0.031 | 469 | yes |
| **conversational** | unweighted | -0.60 | -0.83 to -0.38 | 0.090 | 285 | yes |
| **extractive** | unweighted | -0.45 | -1.46 to +0.57 | 0.021 | 29 | no |
| **output_heavy** | unweighted | +0.05 | -0.71 to +0.81 | 0.000 | 59 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.22, interval
-0.57 to +0.12, straddling zero). Weighting by requests, the
elasticity is **-0.70** (-1.09 to -0.32) and
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
| ≥2 days silent | 71 | 421 | 91.0% | 82.6% |
| ≥3 days silent | 65 | 427 | 91.6% | 83.4% |
| ≥7 days silent | 50 | 442 | 94.4% | 87.6% |
| ≥14 days silent | 32 | 460 | 96.4% | 90.4% |

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
