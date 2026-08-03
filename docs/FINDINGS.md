# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-08-03` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 504 model-variants, 241.75 T
tokens and 15.93 B requests over the trailing 30 days.


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
| **agentic** | 59 | 167.57 T | 69.3% | 57.7 | 45,743 | large contexts, terse output, very large interactions |
| **conversational** | 253 | 68.48 T | 28.3% | 11.7 | 3,848 | moderate context per output token, human-sized interactions |
| **extractive** | 27 | 3.28 T | 1.4% | 40.3 | 9,330 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 96 | 2.28 T | 0.9% | — | 39 | insufficient data to classify |
| **output_heavy** | 69 | 130.51 B | 0.1% | 0.6 | 4,356 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **69.3% of all tokens**
while being 59 of 504 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
28.3%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 213.8 | 793 | 15.18 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 162.2 | 104,403 | 10.23 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 153.4 | 90,623 | 1.14 T | agentic |
| `poolside/laguna-m.1-20260312` | 142.3 | 70,279 | 1.55 T | agentic |
| `xiaomi/mimo-v2.5-20260422` | 114.0 | 66,943 | 33.31 T | agentic |
| `perceptron/perceptron-mk1-20260512` | 96.2 | 9,330 | 13.44 B | extractive |
| `anthropic/claude-4.8-opus-fast-20260528` | 93.0 | 61,810 | 91.43 B | agentic |
| `poolside/laguna-xs-2.1-20260625` | 84.7 | 53,804 | 565.26 B | agentic |
| `anthropic/claude-4.8-opus-20260528` | 83.1 | 78,980 | 6.49 T | agentic |
| `stepfun/step-3.7-flash-20260528` | 82.2 | 65,764 | 5.95 T | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
213.8 tokens of context per token written, but its interactions
average only 793 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 162.2 tokens of context per token
written, in interactions averaging 104,403 tokens, which
is 132× larger.
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


Across 206 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.70** with a p25–p75 range of 0.49–0.94.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 18 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.67×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-5.6-luna-20260709` | 5.80× | 2.63 T | 25 | extractive |
| `openai/gpt-5.6-luna-pro-20260709` | 3.31× | 376.38 B | 25 | agentic |
| `amazon/nova-micro-v1` | 2.75× | 87.98 B | 606 | conversational |
| `poolside/laguna-s-2.1-20260720` | 2.69× | 1.14 T | 13 | agentic |
| `openai/gpt-5.6-terra-20260709` | 2.19× | 860.52 B | 25 | agentic |
| `inclusionai/ling-2.6-flash-20260421` | 2.16× | 429.98 B | 104 | conversational |
| `tencent/hy3-20260706` | 2.00× | 8.83 T | 28 | agentic |
| `openai/gpt-3.5-turbo` | 1.99× | 5.52 B | 1,163 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `ibm-granite/granite-4.0-h-micro` | 0.01× | 80.03 B | 287 | agentic |
| `perceptron/perceptron-mk1-20260512` | 0.02× | 13.44 B | 83 | extractive |
| `anthropic/claude-4.7-opus-20260416` | 0.05× | 6.18 T | 109 | agentic |
| `google/gemma-2-27b-it` | 0.05× | 643.54 M | 751 | conversational |
| `tencent/hy3-preview-20260421` | 0.06× | 1.11 T | 103 | agentic |
| `openai/gpt-4o-2024-05-13` | 0.08× | 3.56 B | 812 | extractive |
| `openai/o4-mini-2025-04-16` | 0.09× | 79.85 B | 474 | conversational |
| `amazon/nova-2-lite-v1` | 0.16× | 16.87 B | 244 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$234.8 M per month** across
353 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 11.0% | 51.0% | 4.65x |
| `openai` | 7.5% | 14.1% | 1.89x |
| `z-ai` | 6.7% | 8.0% | 1.20x |
| `google` | 8.0% | 5.4% | 0.67x |
| `moonshotai` | 2.4% | 4.9% | 2.08x |
| `deepseek` | 17.6% | 4.4% | 0.25x |
| `nvidia` | 5.2% | 2.8% | 0.54x |
| `xiaomi` | 15.1% | 2.5% | 0.16x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,148**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **52.9%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.940** by value. Both are extreme; a
national income distribution above 0.6 is considered severe.


### The sticker price is not the price

Traffic is overwhelmingly prompt-heavy, and prompt tokens cost less than
completions. Blended across each model's real token mix, the price actually paid
per token is a median **0.32x** the headline output price, so the
sticker overstates unit cost by about **3.1x**.

Anyone comparing models on `$/M output` is getting this wrong.


## 5. The context window arms race is mostly unused

Dividing mean tokens per request by the advertised context length asks how much
of the window the traffic actually touches. Token-weighted across the market:
**8.09%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 8.08% |
| **extractive** | 2.45% |
| **conversational** | 1.88% |
| **output_heavy** | 1.84% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 680 endpoints serving multi-provider models,
**440 are dominated** (64.7%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.2-20260616` | Ambient | $4.40 | 12 tok/s | Decart | 25 |
| `z-ai/glm-5.2-20260616` | Z.AI | $4.40 | 27 tok/s | Decart | 19 |
| `z-ai/glm-5.1-20260406` | Z.AI | $4.40 | 17 tok/s | Baidu | 17 |
| `deepseek/deepseek-v4-flash-20260423` | OpenInference | $0.28 | 12 tok/s | Baidu | 16 |
| `z-ai/glm-5.2-20260616` | DigitalOcean | $4.40 | 36 tok/s | Decart | 15 |
| `deepseek/deepseek-v4-pro-20260423` | CoreWeave | $3.48 | 15 tok/s | DeepSeek | 15 |
| `moonshotai/kimi-k2.6-20260420` | Moonshot AI | $4.00 | 24 tok/s | Baidu | 15 |
| `z-ai/glm-5.1-20260406` | Novita | $4.40 | 19 tok/s | Baidu | 15 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-08-02` and `2026-08-03`,
**0.98%** of 408 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.39 | -0.60 to -0.18 | 0.278 | 50 | yes |
| **all** | request weighted | -0.11 | -0.51 to +0.30 | 0.006 | 331 | no |
| **conversational** | request weighted | -0.20 | -0.73 to +0.32 | 0.019 | 224 | no |
| **extractive** | request weighted | -1.16 | -2.69 to +0.37 | 0.234 | 22 | no |
| **output_heavy** | request weighted | +0.11 | -0.15 to +0.38 | 0.020 | 35 | no |
| **agentic** | unweighted | -0.05 | -0.48 to +0.38 | 0.001 | 50 | no |
| **all** | unweighted | -0.53 | -0.81 to -0.26 | 0.045 | 331 | yes |
| **conversational** | unweighted | -0.65 | -0.98 to -0.32 | 0.074 | 224 | yes |
| **extractive** | unweighted | -0.14 | -0.63 to +0.34 | 0.009 | 22 | no |
| **output_heavy** | unweighted | -1.05 | -1.73 to -0.38 | 0.128 | 35 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.05, interval
-0.48 to +0.38, straddling zero). Weighting by requests, the
elasticity is **-0.39** (-0.60 to -0.18) and
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
| ≥2 days silent | 34 | 321 | 94.7% | 88.0% |
| ≥3 days silent | 34 | 321 | 94.7% | 88.0% |
| ≥7 days silent | 11 | 344 | 98.8% | 96.6% |
| ≥14 days silent | 8 | 347 | 99.7% | 97.5% |

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
