# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-10-19` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 718 model-variants, 682.74 T
tokens and 32.82 B requests over the trailing 30 days.


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
| **agentic** | 94 | 565.77 T | 82.9% | 53.6 | 54,373 | large contexts, terse output, very large interactions |
| **conversational** | 327 | 109.28 T | 16.0% | 9.4 | 3,875 | moderate context per output token, human-sized interactions |
| **extractive** | 33 | 4.42 T | 0.6% | 40.9 | 4,990 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 152 | 3.10 T | 0.5% | — | 33 | insufficient data to classify |
| **output_heavy** | 112 | 168.11 B | 0.0% | 0.3 | 3,878 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **82.9% of all tokens**
while being 94 of 718 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
16.0%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `upstage/solar-decide-20260928` | 2,014.9 | 4,633 | 16.42 B | extractive |
| `scaledown/classify-1-20260928` | 1,727.7 | 6,340 | 7.81 B | extractive |
| `upstage/solar-decide-flash-20261008` | 1,478.5 | 3,557 | 7.47 B | extractive |
| `perplexity/pplx-decider-v1-27b-20261001` | 1,155.6 | 4,655 | 9.10 B | extractive |
| `perplexity/pplx-decider-v1.1-27b-20261006` | 1,141.1 | 3,834 | 257.20 B | extractive |
| `perplexity/pplx-decider-flash-v1.2-20261016` | 739.8 | 2,491 | 5.58 B | extractive |
| `togethercomputer/tev1-4b-experimental-20260923` | 536.5 | 2,752 | 6.55 B | extractive |
| `inception/mercury-decide-20260930` | 370.1 | 3,244 | 48.10 B | extractive |
| `microsoft/microsoft-decision-1-20261009` | 342.1 | 1,226 | 27.73 B | extractive |
| `perplexity/pplx-decider-v1.2-20261016` | 332.7 | 1,304 | 15.07 B | extractive |

**Why both axes.** The top of this ranking is `upstage/solar-decide-20260928` at
2,014.9 tokens of context per token written, but its interactions
average only 4,633 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 208.8 tokens of context per token
written, in interactions averaging 134,245 tokens, which
is 29× larger.
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
median of **0.72** with a p25–p75 range of 0.52–0.96.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 25 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.15×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-5.6-sol-20260709` | 7.74× | 5.33 B | 102 | conversational |
| `openai/gpt-6-luna-20260922` | 4.71× | 253.04 B | 27 | conversational |
| `meituan/longcat-2.0-20260720` | 2.74× | 38.43 B | 91 | agentic |
| `google/gemma-2-27b-it` | 2.23× | 523.77 M | 828 | conversational |
| `bytedance-seed/seed-1.6-flash-20250625` | 2.04× | 13.98 B | 300 | conversational |
| `z-ai/glm-5.3-prime-20260921` | 1.88× | 222.26 B | 26 | agentic |
| `meta-llama/llama-3.1-70b-instruct` | 1.77× | 7.04 B | 818 | conversational |
| `openai/gpt-5.5-20260423` | 1.65× | 242.03 B | 178 | extractive |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite-20260507` | 0.00× | 22.33 B | 165 | conversational |
| `stepfun/step-5-preview-20261008` | 0.00× | 20.30 T | 11 | agentic |
| `google/gemini-3.7-flash-20260813` | 0.03× | 11.53 B | 67 | output_heavy |
| `perceptron/perceptron-mk1-20260512` | 0.04× | 6.83 B | 160 | extractive |
| `tencent/hy-mt2-1.8b-20260521` | 0.05× | 995.70 M | 60 | conversational |
| `inclusionai/ling-3.0-flash-vl-20260910` | 0.10× | 126.92 B | 39 | conversational |
| `tencent/hy-mt2-7b-20260521` | 0.10× | 892.65 M | 61 | conversational |
| `google/gemini-2.5-flash` | 0.11× | 6.56 B | 489 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$281.8 M per month** across
487 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 5.6% | 31.5% | 5.58x |
| `openai` | 10.7% | 21.9% | 2.05x |
| `tencent` | 7.0% | 11.2% | 1.60x |
| `stepfun` | 3.1% | 7.3% | 2.36x |
| `google` | 4.3% | 6.8% | 1.58x |
| `deepseek` | 26.7% | 5.6% | 0.21x |
| `xiaomi` | 7.5% | 3.8% | 0.51x |
| `z-ai` | 11.8% | 3.5% | 0.30x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,067**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **51.8%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.936** by value. Both are extreme; a
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
**6.46%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.10% |
| **extractive** | 2.92% |
| **conversational** | 1.65% |
| **output_heavy** | 0.36% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,140 endpoints serving multi-provider models,
**769 are dominated** (67.5%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-20260816` | Morph | $6.00 | 12 tok/s | Wafer | 35 |
| `~z-ai/glm-latest` | Morph | $6.00 | 12 tok/s | Wafer | 35 |
| `z-ai/glm-5.3-20260816` | Cloudflare | $4.40 | 30 tok/s | Wafer | 33 |
| `~z-ai/glm-latest` | Cloudflare | $4.40 | 30 tok/s | Wafer | 33 |
| `z-ai/glm-5.3-20260816` | Mistral | $4.84 | 45 tok/s | Wafer | 30 |
| `z-ai/glm-5.3-20260816` | AtlasCloud | $4.40 | 41 tok/s | Wafer | 30 |
| `~z-ai/glm-latest` | AtlasCloud | $4.40 | 41 tok/s | Wafer | 30 |
| `~z-ai/glm-latest` | Mistral | $4.40 | 44 tok/s | Wafer | 29 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-10-18` and `2026-10-19`,
**1.06%** of 566 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.63 | -0.81 to -0.46 | 0.599 | 80 | yes |
| **all** | request weighted | -0.50 | -0.94 to -0.06 | 0.106 | 452 | yes |
| **conversational** | request weighted | -0.43 | -0.87 to +0.01 | 0.079 | 299 | no |
| **extractive** | request weighted | +0.27 | -0.31 to +0.85 | 0.071 | 19 | no |
| **output_heavy** | request weighted | -0.22 | -0.35 to -0.09 | 0.140 | 54 | yes |
| **agentic** | unweighted | -0.44 | -0.80 to -0.08 | 0.052 | 80 | yes |
| **all** | unweighted | -0.90 | -1.22 to -0.58 | 0.070 | 452 | yes |
| **conversational** | unweighted | -0.79 | -1.13 to -0.45 | 0.070 | 299 | yes |
| **extractive** | unweighted | +0.30 | -0.30 to +0.89 | 0.045 | 19 | no |
| **output_heavy** | unweighted | -1.23 | -2.06 to -0.41 | 0.103 | 54 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.44, interval
-0.80 to -0.08, straddling zero). Weighting by requests, the
elasticity is **-0.63** (-0.81 to -0.46) and
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
| ≥2 days silent | 75 | 413 | 91.9% | 84.0% |
| ≥3 days silent | 75 | 413 | 91.9% | 84.0% |
| ≥7 days silent | 61 | 427 | 94.1% | 87.5% |
| ≥14 days silent | 24 | 464 | 95.3% | 94.5% |

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
