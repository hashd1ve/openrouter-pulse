# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-10-12` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 695 model-variants, 646.22 T
tokens and 29.91 B requests over the trailing 30 days.


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
| **agentic** | 92 | 531.30 T | 82.2% | 54.0 | 53,213 | large contexts, terse output, very large interactions |
| **conversational** | 313 | 108.93 T | 16.9% | 9.2 | 3,594 | moderate context per output token, human-sized interactions |
| **extractive** | 33 | 3.05 T | 0.5% | 48.5 | 5,172 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 147 | 2.80 T | 0.4% | — | 29 | insufficient data to classify |
| **output_heavy** | 110 | 152.71 B | 0.0% | 0.4 | 4,220 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **82.2% of all tokens**
while being 92 of 695 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
16.9%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `upstage/solar-decide-20260928` | 1,871.8 | 4,353 | 9.78 B | extractive |
| `upstage/solar-decide-flash-20261008` | 1,291.8 | 3,088 | 3.91 B | extractive |
| `perplexity/pplx-decider-v1-27b-20261001` | 1,155.6 | 4,655 | 9.10 B | extractive |
| `perplexity/pplx-decider-v1.1-27b-20261006` | 857.5 | 5,172 | 71.47 B | extractive |
| `togethercomputer/tev1-4b-experimental-20260923` | 562.2 | 3,081 | 4.59 B | extractive |
| `inception/mercury-decide-20260930` | 409.3 | 3,349 | 29.13 B | extractive |
| `microsoft/microsoft-decision-1-20261009` | 325.4 | 1,221 | 8.93 B | extractive |
| `inception/mercury-decide-20260930` | 280.4 | 792 | 2.54 B | extractive |
| `meta-llama/llama-guard-4-12b` | 234.9 | 801 | 8.03 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 210.4 | 133,375 | 23.75 T | agentic |

**Why both axes.** The top of this ranking is `upstage/solar-decide-20260928` at
1,871.8 tokens of context per token written, but its interactions
average only 4,353 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 210.4 tokens of context per token
written, in interactions averaging 133,375 tokens, which
is 31× larger.
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


Across 249 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.77** with a p25–p75 range of 0.56–1.02.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 19 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.50×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-6-astra-pro-20260903` | 4.67× | 198.93 B | 38 | agentic |
| `qwen/qwen3.6-35b-a3b-20260415` | 4.52× | 381.83 B | 168 | conversational |
| `google/gemini-3.1-flash-lite-20260507` | 4.22× | 19.79 B | 158 | conversational |
| `openai/gpt-3.5-turbo` | 3.33× | 2.68 B | 1,233 | conversational |
| `deepseek/deepseek-v4.1-flash-20260910` | 3.05× | 7.65 B | 32 | output_heavy |
| `openai/gpt-4o-mini-2024-07-18` | 2.65× | 49.39 B | 816 | conversational |
| `anthropic/claude-sonnet-5.5-20260928` | 2.31× | 3.22 T | 14 | agentic |
| `meta-llama/llama-3.2-3b-instruct` | 2.05× | 3.59 B | 747 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-5.6-sol-20260709` | 0.00× | 4.51 B | 95 | conversational |
| `tencent/hy-mt2-7b-20260521` | 0.02× | 1.74 B | 54 | conversational |
| `perceptron/perceptron-mk1-20260512` | 0.06× | 6.92 B | 153 | extractive |
| `tencent/hy-mt2-1.8b-20260521` | 0.06× | 2.11 B | 53 | conversational |
| `google/gemini-3.6-flash-20260721` | 0.08× | 13.08 B | 83 | conversational |
| `google/gemini-3.7-flash-20260813` | 0.09× | 8.94 B | 60 | output_heavy |
| `z-ai/glm-5.3-flash-20260826` | 0.09× | 13.84 B | 47 | conversational |
| `microsoft/phi-4` | 0.10× | 6.31 B | 640 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$278.6 M per month** across
472 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `openai` | 12.5% | 29.3% | 2.34x |
| `anthropic` | 4.6% | 24.9% | 5.46x |
| `tencent` | 8.3% | 12.8% | 1.54x |
| `deepseek` | 25.6% | 8.9% | 0.35x |
| `google` | 4.5% | 4.7% | 1.04x |
| `z-ai` | 12.0% | 4.4% | 0.36x |
| `stepfun` | 1.4% | 3.2% | 2.24x |
| `xiaomi` | 7.1% | 3.2% | 0.45x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,199**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **53.0%** of
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
**6.47%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.21% |
| **extractive** | 2.30% |
| **conversational** | 1.59% |
| **output_heavy** | 0.56% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,097 endpoints serving multi-provider models,
**750 are dominated** (68.4%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-20260816` | Morph | $5.00 | 36 tok/s | Baidu | 31 |
| `~z-ai/glm-latest` | Morph | $5.00 | 37 tok/s | Baidu | 30 |
| `z-ai/glm-5.3-flash-20260826` | Morph | $1.00 | 10 tok/s | InferenceNet | 28 |
| `~z-ai/glm-flash-latest` | Morph | $1.00 | 10 tok/s | InferenceNet | 28 |
| `z-ai/glm-5.3-20260816` | AtlasCloud | $4.40 | 32 tok/s | Baidu | 28 |
| `z-ai/glm-5.3-flash-20260826` | OpenInference | $1.20 | 22 tok/s | InferenceNet | 27 |
| `~z-ai/glm-flash-latest` | OpenInference | $1.20 | 22 tok/s | InferenceNet | 27 |
| `~z-ai/glm-latest` | AtlasCloud | $4.40 | 32 tok/s | Baidu | 27 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-10-11` and `2026-10-12`,
**1.28%** of 548 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.48 | -0.82 to -0.15 | 0.152 | 77 | yes |
| **all** | request weighted | +0.23 | -0.01 to +0.48 | 0.016 | 438 | no |
| **conversational** | request weighted | +0.22 | -0.09 to +0.53 | 0.018 | 284 | no |
| **extractive** | request weighted | +0.48 | -0.13 to +1.08 | 0.225 | 21 | no |
| **output_heavy** | request weighted | -0.24 | -0.43 to -0.04 | 0.085 | 56 | yes |
| **agentic** | unweighted | -0.49 | -0.86 to -0.13 | 0.081 | 77 | yes |
| **all** | unweighted | -0.98 | -1.32 to -0.64 | 0.080 | 438 | yes |
| **conversational** | unweighted | -0.96 | -1.33 to -0.58 | 0.094 | 284 | yes |
| **extractive** | unweighted | -0.11 | -0.82 to +0.61 | 0.004 | 21 | no |
| **output_heavy** | unweighted | -1.36 | -2.29 to -0.42 | 0.114 | 56 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.49, interval
-0.86 to -0.13, straddling zero). Weighting by requests, the
elasticity is **-0.48** (-0.82 to -0.15) and
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
| ≥2 days silent | 73 | 401 | 92.0% | 84.0% |
| ≥3 days silent | 73 | 401 | 92.0% | 84.0% |
| ≥7 days silent | 30 | 444 | 94.1% | 92.8% |
| ≥14 days silent | 28 | 446 | 94.6% | 93.2% |

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
