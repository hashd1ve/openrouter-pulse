# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-11-14` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 766 model-variants, 834.30 T
tokens and 40.38 B requests over the trailing 30 days.


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
| **agentic** | 102 | 663.23 T | 79.5% | 58.5 | 60,446 | large contexts, terse output, very large interactions |
| **conversational** | 321 | 113.43 T | 13.6% | 10.1 | 4,086 | moderate context per output token, human-sized interactions |
| **extractive** | 44 | 52.83 T | 6.3% | 45.7 | 4,059 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 180 | 4.64 T | 0.6% | — | 37 | insufficient data to classify |
| **output_heavy** | 119 | 183.57 B | 0.0% | 0.4 | 4,430 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **79.5% of all tokens**
while being 102 of 766 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
13.6%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `scaledown/classify-1-20260928` | 2,369.9 | 7,344 | 16.92 B | extractive |
| `upstage/solar-decide-20260928` | 2,092.2 | 4,506 | 11.72 B | extractive |
| `upstage/solar-decide-flash-20261008` | 1,453.5 | 2,914 | 5.92 B | extractive |
| `perplexity/pplx-decider-v1.1-27b-20261006` | 1,065.0 | 2,090 | 49.19 B | extractive |
| `perplexity/pplx-decider-flash-v1.2-20261016` | 853.8 | 2,007 | 102.09 B | extractive |
| `microsoft/microsoft-decision-1-20261009` | 636.5 | 1,885 | 97.67 B | extractive |
| `inception/mercury-decide-20260930` | 519.9 | 761 | 109.38 B | extractive |
| `perplexity/pplx-decider-v1.2-20261016` | 511.5 | 1,859 | 1.28 T | extractive |
| `inception/mercury-decide-20260930` | 407.9 | 6,192 | 117.67 B | extractive |
| `baseten/mammoth-1-20261021` | 396.6 | 652 | 19.38 B | extractive |

**Why both axes.** The top of this ranking is `scaledown/classify-1-20260928` at
2,369.9 tokens of context per token written, but its interactions
average only 7,344 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `stepfun/step-5-preview-20261008`: 211.6 tokens of context per token
written, in interactions averaging 248,776 tokens, which
is 34× larger.
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


Across 259 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.93** with a p25–p75 range of 0.70–1.13.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 10 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.47×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `google/gemini-3.5-flash-lite-20260721` | 3.27× | 3.38 B | 116 | conversational |
| `mistralai/mistral-large-2512` | 3.04× | 6.61 B | 348 | conversational |
| `meta-llama/llama-3.2-3b-instruct` | 2.67× | 3.33 B | 780 | conversational |
| `qwen/qwen3-14b-04-28` | 2.58× | 12.54 B | 565 | conversational |
| `z-ai/glm-4.6-20251208` | 2.29× | 7.44 B | 341 | conversational |
| `meituan/longcat-2.0-20260720` | 2.22× | 38.87 B | 117 | agentic |
| `nousresearch/hermes-4-405b` | 2.02× | 4.42 B | 445 | conversational |
| `z-ai/glm-5.3-flashx-legal-20261102` | 1.84× | 82.34 B | 12 | agentic |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-5-nano-2025-08-07` | 0.01× | 9.85 B | 464 | conversational |
| `tencent/hy4-preview-20260827` | 0.03× | 26.04 T | 78 | agentic |
| `stepfun/step-3.7-flash-20260528` | 0.05× | 871.19 B | 170 | agentic |
| `anthropic/claude-opus-5-20260723` | 0.08× | 444.95 M | 113 | conversational |
| `openai/gpt-6-sol-20260922` | 0.08× | 4.26 B | 53 | conversational |
| `xiaomi/mimo-v2.5-20260422` | 0.10× | 530.38 B | 206 | agentic |
| `google/gemini-3.6-flash-20260721` | 0.13× | 6.34 B | 116 | conversational |
| `openai/gpt-5.6-luna-20260709` | 0.15× | 65.47 B | 128 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$325.1 M per month** across
490 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 7.8% | 37.5% | 4.80x |
| `openai` | 9.7% | 14.4% | 1.49x |
| `tencent` | 8.0% | 10.8% | 1.35x |
| `deepseek` | 37.2% | 7.6% | 0.20x |
| `stepfun` | 3.0% | 7.3% | 2.43x |
| `google` | 3.5% | 5.3% | 1.52x |
| `z-ai` | 10.1% | 4.3% | 0.43x |
| `moonshotai` | 2.3% | 3.5% | 1.56x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,508**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **56.7%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.943** by value. Both are extreme; a
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
**6.74%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 6.98% |
| **conversational** | 1.75% |
| **extractive** | 1.60% |
| **output_heavy** | 1.50% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,195 endpoints serving multi-provider models,
**839 are dominated** (70.2%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `~deepseek/deepseek-flash-latest` | Near AI | $1.20 | 53 tok/s | Sail Research | 45 |
| `deepseek/deepseek-v4.1-flash-20261017` | Nebius | $1.20 | 79 tok/s | Sail Research | 40 |
| `~deepseek/deepseek-flash-latest` | Nebius | $1.20 | 82 tok/s | Sail Research | 40 |
| `z-ai/glm-5.3-flash-20260826` | AtlasCloud | $0.50 | 22 tok/s | Relace | 35 |
| `~z-ai/glm-flash-latest` | AtlasCloud | $0.50 | 23 tok/s | Relace | 35 |
| `z-ai/glm-5.3-flash-20260826` | Near AI | $0.50 | 34 tok/s | Relace | 34 |
| `~z-ai/glm-flash-latest` | Near AI | $0.50 | 34 tok/s | Relace | 34 |
| `z-ai/glm-5.3-flash-20260826` | Z.AI | $0.50 | 36 tok/s | Relace | 33 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-11-13` and `2026-11-14`,
**1.38%** of 580 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.62 | -0.91 to -0.32 | 0.429 | 88 | yes |
| **all** | request weighted | -0.53 | -0.96 to -0.11 | 0.108 | 455 | yes |
| **conversational** | request weighted | -0.18 | -0.51 to +0.14 | 0.018 | 292 | no |
| **extractive** | request weighted | -0.91 | -1.22 to -0.60 | 0.558 | 23 | yes |
| **output_heavy** | request weighted | -0.04 | -0.37 to +0.30 | 0.002 | 52 | no |
| **agentic** | unweighted | -0.49 | -0.89 to -0.10 | 0.061 | 88 | yes |
| **all** | unweighted | -0.56 | -0.80 to -0.33 | 0.049 | 455 | yes |
| **conversational** | unweighted | -0.61 | -0.86 to -0.35 | 0.076 | 292 | yes |
| **extractive** | unweighted | -0.49 | -1.55 to +0.58 | 0.035 | 23 | no |
| **output_heavy** | unweighted | -0.28 | -0.81 to +0.24 | 0.019 | 52 | no |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.49, interval
-0.89 to -0.10, straddling zero). Weighting by requests, the
elasticity is **-0.62** (-0.91 to -0.32) and
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
| ≥2 days silent | 66 | 425 | 95.2% | 86.5% |
| ≥3 days silent | 63 | 428 | 95.6% | 87.3% |
| ≥7 days silent | 46 | 445 | 97.6% | 91.8% |
| ≥14 days silent | 35 | 456 | 98.6% | 93.7% |

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
