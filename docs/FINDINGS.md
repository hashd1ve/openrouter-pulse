# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-11-05` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 742 model-variants, 788.46 T
tokens and 38.45 B requests over the trailing 30 days.


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
| **agentic** | 94 | 618.95 T | 78.5% | 59.7 | 58,066 | large contexts, terse output, very large interactions |
| **conversational** | 320 | 113.36 T | 14.4% | 9.8 | 3,843 | moderate context per output token, human-sized interactions |
| **extractive** | 40 | 51.84 T | 6.6% | 51.1 | 4,968 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 173 | 4.13 T | 0.5% | — | 35 | insufficient data to classify |
| **output_heavy** | 115 | 173.78 B | 0.0% | 0.3 | 4,149 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **78.5% of all tokens**
while being 94 of 742 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
14.4%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `scaledown/classify-1-20260928` | 2,393.8 | 7,550 | 18.83 B | extractive |
| `upstage/solar-decide-20260928` | 2,108.5 | 4,789 | 18.73 B | extractive |
| `upstage/solar-decide-flash-20261008` | 1,430.7 | 3,151 | 10.55 B | extractive |
| `perplexity/pplx-decider-v1.1-27b-20261006` | 1,141.1 | 3,834 | 257.20 B | extractive |
| `perplexity/pplx-decider-v1-27b-20261001` | 1,096.5 | 5,147 | 6.36 B | extractive |
| `perplexity/pplx-decider-flash-v1.2-20261016` | 1,009.2 | 2,063 | 81.71 B | extractive |
| `microsoft/microsoft-decision-1-20261009` | 529.7 | 1,534 | 82.35 B | extractive |
| `perplexity/pplx-decider-v1.2-20261016` | 497.1 | 1,960 | 651.03 B | extractive |
| `togethercomputer/tev1-4b-experimental-20260923` | 453.2 | 2,498 | 7.12 B | extractive |
| `inception/mercury-decide-20260930` | 401.3 | 766 | 101.94 B | extractive |

**Why both axes.** The top of this ranking is `scaledown/classify-1-20260928` at
2,393.8 tokens of context per token written, but its interactions
average only 7,550 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `stepfun/step-5-preview-20261008`: 194.0 tokens of context per token
written, in interactions averaging 213,959 tokens, which
is 28× larger.
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


Across 260 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.91** with a p25–p75 range of 0.72–1.15.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 19 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.43×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `nvidia/nemotron-3.5-super-vl-20261015` | 5.71× | 738.89 B | 21 | conversational |
| `openai/gpt-6.1-sol-20260929` | 5.30× | 11.66 B | 37 | conversational |
| `google/gemma-2-27b-it` | 4.75× | 1.03 B | 845 | conversational |
| `meta-llama/llama-guard-4-12b` | 3.34× | 8.38 B | 554 | extractive |
| `qwen/qwen3-coder-30b-a3b-instruct` | 2.25× | 37.13 B | 462 | conversational |
| `moonshotai/kimi-k3-20260715` | 2.22× | 9.04 T | 112 | agentic |
| `google/gemini-3.8-flash-20260902` | 2.07× | 20.72 B | 64 | conversational |
| `google/gemma-3-4b-it` | 1.95× | 10.38 B | 602 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-6-luna-pro-20260922` | 0.03× | 20.57 B | 44 | conversational |
| `tencent/hy4-preview-20260827` | 0.06× | 36.04 T | 69 | agentic |
| `google/gemini-3.7-flash-20260813` | 0.06× | 6.93 B | 84 | output_heavy |
| `google/gemini-3.1-flash-lite-20260507` | 0.08× | 26.70 B | 182 | conversational |
| `inclusionai/ling-3.0-flash-vl-20260910` | 0.09× | 76.89 B | 56 | conversational |
| `xiaomi/mimo-v2.5-20260422` | 0.09× | 1.24 T | 197 | agentic |
| `xiaomi/mimo-v2.5-pro-20260422` | 0.14× | 414.26 B | 197 | agentic |
| `nex-agi/nex-n2.5-mini-20260908` | 0.21× | 29.45 B | 58 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$354.8 M per month** across
481 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 8.0% | 30.3% | 3.80x |
| `openai` | 10.0% | 16.9% | 1.69x |
| `stepfun` | 4.5% | 9.5% | 2.12x |
| `tencent` | 6.6% | 9.3% | 1.41x |
| `deepseek` | 34.2% | 9.0% | 0.26x |
| `z-ai` | 11.0% | 6.0% | 0.54x |
| `google` | 3.7% | 5.0% | 1.33x |
| `moonshotai` | 1.9% | 4.1% | 2.13x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,561**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **57.1%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.945** by value. Both are extreme; a
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
**6.76%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.56% |
| **conversational** | 1.72% |
| **extractive** | 1.61% |
| **output_heavy** | 0.96% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,256 endpoints serving multi-provider models,
**902 are dominated** (71.8%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `deepseek/deepseek-v4.1-flash-20261017` | Mistral | $1.20 | 33 tok/s | DeepInfra | 40 |
| `~deepseek/deepseek-flash-latest` | Mistral | $1.20 | 33 tok/s | DeepInfra | 40 |
| `z-ai/glm-5.3-20260816` | Parasail | $6.60 | 41 tok/s | Baidu | 38 |
| `~z-ai/glm-latest` | Parasail | $6.60 | 41 tok/s | Baidu | 38 |
| `z-ai/glm-5.3-flash-20260826` | AtlasCloud | $0.50 | 27 tok/s | Relace | 36 |
| `~z-ai/glm-flash-latest` | AtlasCloud | $0.50 | 27 tok/s | Relace | 36 |
| `~z-ai/glm-flash-latest` | Sail Research | $0.62 | 33 tok/s | Relace | 35 |
| `z-ai/glm-5.3-flash-20260826` | Parasail | $0.62 | 32 tok/s | Relace | 35 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-11-04` and `2026-11-05`,
**0.88%** of 566 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.75 | -1.02 to -0.47 | 0.377 | 83 | yes |
| **all** | request weighted | -0.09 | -0.38 to +0.21 | 0.002 | 458 | no |
| **conversational** | request weighted | -0.20 | -0.61 to +0.20 | 0.017 | 300 | no |
| **extractive** | request weighted | -1.18 | -1.58 to -0.77 | 0.490 | 21 | yes |
| **output_heavy** | request weighted | -0.17 | -0.43 to +0.09 | 0.042 | 54 | no |
| **agentic** | unweighted | -0.42 | -0.81 to -0.03 | 0.052 | 83 | yes |
| **all** | unweighted | -0.82 | -1.12 to -0.53 | 0.073 | 458 | yes |
| **conversational** | unweighted | -0.69 | -0.95 to -0.43 | 0.067 | 300 | yes |
| **extractive** | unweighted | -0.45 | -1.42 to +0.51 | 0.043 | 21 | no |
| **output_heavy** | unweighted | -1.49 | -2.22 to -0.77 | 0.193 | 54 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.42, interval
-0.81 to -0.03, straddling zero). Weighting by requests, the
elasticity is **-0.75** (-1.02 to -0.47) and
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
| ≥2 days silent | 81 | 401 | 94.4% | 85.6% |
| ≥3 days silent | 77 | 405 | 95.4% | 86.6% |
| ≥7 days silent | 62 | 420 | 97.6% | 90.5% |
| ≥14 days silent | 42 | 440 | 97.6% | 94.1% |

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
