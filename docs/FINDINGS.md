# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-11-07` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 740 model-variants, 802.41 T
tokens and 38.95 B requests over the trailing 30 days.


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
| **agentic** | 98 | 634.08 T | 79.0% | 56.1 | 55,407 | large contexts, terse output, very large interactions |
| **conversational** | 314 | 110.16 T | 13.7% | 10.0 | 3,882 | moderate context per output token, human-sized interactions |
| **extractive** | 40 | 53.77 T | 6.7% | 50.2 | 4,642 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 175 | 4.22 T | 0.5% | — | 37 | insufficient data to classify |
| **output_heavy** | 113 | 175.54 B | 0.0% | 0.4 | 4,418 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **79.0% of all tokens**
while being 98 of 740 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
13.7%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `scaledown/classify-1-20260928` | 2,320.8 | 7,406 | 19.37 B | extractive |
| `upstage/solar-decide-20260928` | 2,066.6 | 4,585 | 17.57 B | extractive |
| `upstage/solar-decide-flash-20261008` | 1,443.1 | 3,164 | 10.95 B | extractive |
| `perplexity/pplx-decider-v1.1-27b-20261006` | 1,140.7 | 3,836 | 256.13 B | extractive |
| `perplexity/pplx-decider-flash-v1.2-20261016` | 1,026.1 | 2,115 | 87.47 B | extractive |
| `microsoft/microsoft-decision-1-20261009` | 612.8 | 1,714 | 100.71 B | extractive |
| `perplexity/pplx-decider-v1.2-20261016` | 514.5 | 1,990 | 816.65 B | extractive |
| `togethercomputer/tev1-4b-experimental-20260923` | 444.0 | 2,398 | 6.43 B | extractive |
| `inception/mercury-decide-20260930` | 402.5 | 745 | 111.58 B | extractive |
| `baseten/mammoth-1-20261021` | 389.5 | 649 | 11.52 B | extractive |

**Why both axes.** The top of this ranking is `scaledown/classify-1-20260928` at
2,320.8 tokens of context per token written, but its interactions
average only 7,406 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `stepfun/step-5-preview-20261008`: 195.2 tokens of context per token
written, in interactions averaging 216,278 tokens, which
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


Across 261 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.87** with a p25–p75 range of 0.68–1.10.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 16 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.36×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-5.1-codex-mini-20251113` | 5.08× | 7.33 B | 359 | conversational |
| `nvidia/nemotron-3.5-super-vl-20261015` | 5.00× | 1.22 T | 23 | agentic |
| `amazon/nova-2-lite-v1` | 4.67× | 6.35 B | 340 | conversational |
| `reflection/beam-1.0-501b-a23b-20261016` | 2.80× | 278.50 B | 22 | agentic |
| `openai/gpt-3.5-turbo-0613` | 2.56× | 477.48 M | 1,017 | conversational |
| `meta/muse-glimmer-30b-20260810` | 2.47× | 58.59 B | 90 | conversational |
| `bytedance-seed/seed-2.0-lite-20260309` | 2.40× | 22.61 B | 242 | conversational |
| `minimax/minimax-m2.5-20260211` | 2.29× | 45.93 B | 268 | agentic |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-5-nano-2025-08-07` | 0.01× | 10.48 B | 457 | conversational |
| `tencent/hy4-preview-20260827` | 0.02× | 33.62 T | 71 | agentic |
| `anthropic/claude-opus-5-20260723` | 0.04× | 487.71 M | 106 | conversational |
| `stepfun/step-3.7-flash-20260528` | 0.06× | 885.78 B | 163 | agentic |
| `google/gemma-2-27b-it` | 0.07× | 1.05 B | 847 | conversational |
| `xiaomi/mimo-v2.5-20260422` | 0.07× | 1.03 T | 199 | agentic |
| `inclusionai/ling-3.0-flash-vl-20260910` | 0.08× | 54.55 B | 58 | conversational |
| `deepseek/deepseek-v4.1-flash-20260910` | 0.09× | 32.18 B | 58 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$416.6 M per month** across
474 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 8.0% | 41.4% | 5.20x |
| `openai` | 9.8% | 13.9% | 1.41x |
| `deepseek` | 34.4% | 9.0% | 0.26x |
| `stepfun` | 4.7% | 8.6% | 1.85x |
| `tencent` | 6.9% | 8.0% | 1.16x |
| `moonshotai` | 2.0% | 4.0% | 1.99x |
| `z-ai` | 10.8% | 3.6% | 0.33x |
| `google` | 3.6% | 3.4% | 0.92x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,774**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **59.4%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.942** by value. Both are extreme; a
national income distribution above 0.6 is considered severe.


### The sticker price is not the price

Traffic is overwhelmingly prompt-heavy, and prompt tokens cost less than
completions. Blended across each model's real token mix, the price actually paid
per token is a median **0.34x** the headline output price, so the
sticker overstates unit cost by about **3.0x**.

Anyone comparing models on `$/M output` is getting this wrong.


## 5. The context window arms race is mostly unused

Dividing mean tokens per request by the advertised context length asks how much
of the window the traffic actually touches. Token-weighted across the market:
**6.84%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 6.74% |
| **conversational** | 1.76% |
| **output_heavy** | 1.76% |
| **extractive** | 1.58% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,192 endpoints serving multi-provider models,
**867 are dominated** (72.7%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.3-flash-20260826` | Near AI | $0.50 | 27 tok/s | Relace | 33 |
| `~z-ai/glm-flash-latest` | Near AI | $0.50 | 27 tok/s | Relace | 33 |
| `z-ai/glm-5.3-flash-20260826` | AtlasCloud | $0.50 | 30 tok/s | Relace | 32 |
| `~z-ai/glm-flash-latest` | AtlasCloud | $0.50 | 30 tok/s | Relace | 32 |
| `deepseek/deepseek-v4.1-flash-20261017` | PrimeIntellect | $1.20 | 117 tok/s | Particle AI | 30 |
| `~deepseek/deepseek-flash-latest` | PrimeIntellect | $1.20 | 117 tok/s | Particle AI | 30 |
| `deepseek/deepseek-v4.1-flash-20261017` | Mistral | $1.20 | 120 tok/s | Particle AI | 29 |
| `~deepseek/deepseek-flash-latest` | Mistral | $1.20 | 120 tok/s | Particle AI | 29 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-10-25` and `2026-11-07`,
**25.00%** of 4 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.56 | -0.78 to -0.35 | 0.307 | 87 | yes |
| **all** | request weighted | -0.25 | -0.62 to +0.12 | 0.021 | 449 | no |
| **conversational** | request weighted | -0.26 | -0.59 to +0.06 | 0.033 | 293 | no |
| **extractive** | request weighted | -1.13 | -1.50 to -0.77 | 0.578 | 21 | yes |
| **output_heavy** | request weighted | -0.03 | -0.35 to +0.28 | 0.003 | 48 | no |
| **agentic** | unweighted | -0.43 | -0.81 to -0.04 | 0.052 | 87 | yes |
| **all** | unweighted | -0.55 | -0.77 to -0.33 | 0.045 | 449 | yes |
| **conversational** | unweighted | -0.58 | -0.80 to -0.37 | 0.069 | 293 | yes |
| **extractive** | unweighted | -0.26 | -1.18 to +0.66 | 0.012 | 21 | no |
| **output_heavy** | unweighted | -0.55 | -1.20 to +0.11 | 0.043 | 48 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.43, interval
-0.81 to -0.04, straddling zero). Weighting by requests, the
elasticity is **-0.56** (-0.78 to -0.35) and
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
| ≥2 days silent | 72 | 403 | 94.3% | 86.0% |
| ≥3 days silent | 67 | 408 | 94.6% | 87.2% |
| ≥7 days silent | 59 | 416 | 96.0% | 88.5% |
| ≥14 days silent | 38 | 437 | 97.9% | 95.1% |

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
