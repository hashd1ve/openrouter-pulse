# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-10-09` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 685 model-variants, 626.82 T
tokens and 29.43 B requests over the trailing 30 days.


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
| **agentic** | 90 | 506.99 T | 80.9% | 54.4 | 54,133 | large contexts, terse output, very large interactions |
| **conversational** | 309 | 114.25 T | 18.2% | 9.6 | 3,847 | moderate context per output token, human-sized interactions |
| **unclassified** | 147 | 2.79 T | 0.4% | — | 29 | insufficient data to classify |
| **extractive** | 30 | 2.64 T | 0.4% | 53.8 | 5,152 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 109 | 150.53 B | 0.0% | 0.5 | 3,849 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **80.9% of all tokens**
while being 90 of 685 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
18.2%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `upstage/solar-decide-20260928` | 2,052.7 | 4,925 | 8.34 B | extractive |
| `inception/mercury-decide-20260930` | 1,682.5 | 11,464 | 20.03 B | extractive |
| `perplexity/pplx-decider-v1.1-27b-20261006` | 1,212.5 | 4,338 | 9.13 B | extractive |
| `perplexity/pplx-decider-v1-27b-20261001` | 1,155.6 | 4,655 | 9.10 B | extractive |
| `togethercomputer/tev1-4b-experimental-20260923` | 505.8 | 2,271 | 2.73 B | extractive |
| `meta-llama/llama-guard-4-12b` | 234.0 | 792 | 8.35 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 207.5 | 132,593 | 21.96 T | agentic |
| `stepfun/step-5-preview-20261008` | 150.0 | 189,913 | 632.19 B | agentic |
| `upstage/solar-mini4-20260922` | 131.5 | 62,401 | 986.21 B | agentic |
| `thinkingmachines/inkling-small-20260730` | 129.5 | 57,744 | 519.32 B | agentic |

**Why both axes.** The top of this ranking is `upstage/solar-decide-20260928` at
2,052.7 tokens of context per token written, but its interactions
average only 4,925 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 207.5 tokens of context per token
written, in interactions averaging 132,593 tokens, which
is 27× larger.
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


Across 253 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.99** with a p25–p75 range of 0.75–1.23.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 20 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.76×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `microsoft/phi-4` | 4.35× | 5.18 B | 637 | conversational |
| `inclusionai/ling-3.0-flash-vl-20260910` | 3.43× | 88.61 B | 29 | conversational |
| `x-ai/grok-4.7-20260916` | 2.72× | 1.14 T | 18 | agentic |
| `mistralai/mistral-medium-3.5-20260430` | 2.57× | 21.68 B | 162 | conversational |
| `upstage/solar-mini4-20260922` | 2.48× | 986.21 B | 16 | agentic |
| `ibm-granite/granite-4.2-8b-20260831` | 2.23× | 34.60 B | 39 | conversational |
| `anthropic/claude-opus-5.5-20260921` | 2.19× | 6.34 T | 17 | agentic |
| `openai/gpt-5.6-sol-20260709` | 2.18× | 4.97 B | 92 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `tencent/hy-mt2-7b-20260521` | 0.03× | 2.36 B | 51 | conversational |
| `tencent/hy-mt2-1.8b-20260521` | 0.05× | 2.94 B | 50 | conversational |
| `perceptron/perceptron-mk1-20260512` | 0.07× | 7.09 B | 150 | extractive |
| `google/gemini-3.8-flash-20260902` | 0.14× | 12.84 B | 37 | conversational |
| `xiaomi/mimo-v2.5-20260422` | 0.16× | 16.98 T | 170 | agentic |
| `thinkingmachines/inkling-20260715` | 0.21× | 127.57 B | 84 | agentic |
| `amazon/nova-lite-v1` | 0.22× | 17.24 B | 673 | conversational |
| `mistralai/mistral-large-2512` | 0.23× | 17.05 B | 312 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$284.4 M per month** across
465 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `openai` | 13.2% | 29.2% | 2.21x |
| `anthropic` | 4.2% | 22.7% | 5.45x |
| `tencent` | 9.3% | 13.7% | 1.48x |
| `deepseek` | 24.8% | 6.8% | 0.27x |
| `google` | 4.8% | 6.1% | 1.27x |
| `z-ai` | 12.3% | 6.0% | 0.48x |
| `moonshotai` | 1.3% | 6.0% | 4.64x |
| `xiaomi` | 6.9% | 2.9% | 0.41x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**4,128**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **62.8%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.941** by value. Both are extreme; a
national income distribution above 0.6 is considered severe.


### The sticker price is not the price

Traffic is overwhelmingly prompt-heavy, and prompt tokens cost less than
completions. Blended across each model's real token mix, the price actually paid
per token is a median **0.35x** the headline output price, so the
sticker overstates unit cost by about **2.8x**.

Anyone comparing models on `$/M output` is getting this wrong.


## 5. The context window arms race is mostly unused

Dividing mean tokens per request by the advertised context length asks how much
of the window the traffic actually touches. Token-weighted across the market:
**6.31%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.35% |
| **extractive** | 2.64% |
| **conversational** | 1.61% |
| **output_heavy** | 0.57% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,114 endpoints serving multi-provider models,
**749 are dominated** (67.2%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `~z-ai/glm-latest` | Cloudflare | $4.40 | 41 tok/s | Novita | 30 |
| `z-ai/glm-5.3-20260816` | Cloudflare | $4.40 | 40 tok/s | Novita | 29 |
| `~z-ai/glm-latest` | Z.AI | $4.40 | 48 tok/s | Novita | 29 |
| `deepseek/deepseek-v4.1-flash-20260910` | Alibaba | $1.20 | 33 tok/s | Decart | 28 |
| `~deepseek/deepseek-flash-latest` | Alibaba | $1.20 | 33 tok/s | Decart | 28 |
| `~z-ai/glm-latest` | Fireworks | $4.40 | 49 tok/s | Novita | 27 |
| `z-ai/glm-5.3-20260816` | Z.AI | $4.40 | 48 tok/s | DeepInfra | 27 |
| `z-ai/glm-5.3-20260816` | Fireworks | $4.40 | 49 tok/s | DeepInfra | 26 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-10-08` and `2026-10-09`,
**0.94%** of 534 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.56 | -0.84 to -0.27 | 0.274 | 77 | yes |
| **all** | request weighted | +0.16 | -0.18 to +0.49 | 0.007 | 439 | no |
| **conversational** | request weighted | +0.48 | -0.03 to +0.99 | 0.072 | 286 | no |
| **extractive** | request weighted | +0.73 | +0.28 to +1.18 | 0.470 | 20 | yes |
| **output_heavy** | request weighted | -0.20 | -0.40 to -0.00 | 0.057 | 56 | yes |
| **agentic** | unweighted | -0.57 | -0.92 to -0.22 | 0.116 | 77 | yes |
| **all** | unweighted | -0.81 | -1.12 to -0.50 | 0.064 | 439 | yes |
| **conversational** | unweighted | -0.64 | -0.93 to -0.36 | 0.058 | 286 | yes |
| **extractive** | unweighted | -0.16 | -1.05 to +0.72 | 0.004 | 20 | no |
| **output_heavy** | unweighted | -1.36 | -2.23 to -0.50 | 0.120 | 56 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.57, interval
-0.92 to -0.22, straddling zero). Weighting by requests, the
elasticity is **-0.56** (-0.84 to -0.27) and
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
| ≥2 days silent | 53 | 414 | 93.3% | 87.9% |
| ≥3 days silent | 45 | 422 | 94.0% | 89.7% |
| ≥7 days silent | 29 | 438 | 94.4% | 92.5% |
| ≥14 days silent | 23 | 444 | 94.6% | 93.8% |

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
