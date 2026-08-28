# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-08-28` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 582 model-variants, 348.24 T
tokens and 18.75 B requests over the trailing 30 days.


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
| **agentic** | 67 | 268.53 T | 77.1% | 52.3 | 50,061 | large contexts, terse output, very large interactions |
| **conversational** | 283 | 76.95 T | 22.1% | 10.0 | 3,810 | moderate context per output token, human-sized interactions |
| **unclassified** | 122 | 2.09 T | 0.6% | — | 29 | insufficient data to classify |
| **extractive** | 28 | 515.97 B | 0.1% | 38.0 | 7,941 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 82 | 158.40 B | 0.0% | 0.5 | 4,557 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **77.1% of all tokens**
while being 67 of 582 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
22.1%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 370.1 | 1,323 | 21.61 B | extractive |
| `thinkingmachines/inkling-20260715` | 170.4 | 63,772 | 109.60 B | agentic |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 161.4 | 103,407 | 14.26 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 147.8 | 92,297 | 6.80 T | agentic |
| `xiaomi/mimo-v2.5-20260422` | 130.1 | 75,807 | 28.98 T | agentic |
| `poolside/laguna-xs-2.1-20260625` | 122.5 | 55,739 | 652.49 B | agentic |
| `minimax/minimax-m3-20260531` | 99.4 | 60,625 | 511.48 B | agentic |
| `anthropic/claude-opus-5-fast-20260723` | 96.2 | 84,994 | 133.55 B | agentic |
| `nvidia/nemotron-3.5-lightning-20260807` | 95.7 | 72,095 | 2.16 T | agentic |
| `qwen/qwen3-coder-next-2025-02-03` | 88.9 | 28,278 | 101.71 B | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
370.1 tokens of context per token written, but its interactions
average only 1,323 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `thinkingmachines/inkling-20260715`: 170.4 tokens of context per token
written, in interactions averaging 63,772 tokens, which
is 48× larger.
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
median of **1.01** with a p25–p75 range of 0.79–1.37.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 20 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **1.82×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `minimax/minimax-m3-20260531` | 18.52× | 511.48 B | 89 | agentic |
| `minimax/minimax-m2.7-20260318` | 14.86× | 35.16 B | 163 | agentic |
| `thinkingmachines/inkling-20260715` | 10.02× | 109.60 B | 42 | agentic |
| `thinkingmachines/inkling-small-20260730` | 8.77× | 46.70 B | 29 | agentic |
| `ibm-granite/granite-4.0-h-micro` | 6.85× | 2.19 B | 312 | conversational |
| `google/gemini-3.6-flash-20260721` | 4.46× | 2.62 B | 38 | conversational |
| `google/gemini-3.7-flash-20260813` | 3.36× | 17.87 B | 15 | conversational |
| `perplexity/sonar-pro` | 3.17× | 4.86 B | 539 | output_heavy |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-5.2-chat-20251211` | 0.00× | 3.98 B | 261 | conversational |
| `google/gemma-4-26b-a4b-it-20260403` | 0.08× | 50.05 B | 147 | conversational |
| `google/gemini-3.6-flash-20260721` | 0.12× | 6.32 T | 38 | agentic |
| `anthropic/claude-4.7-opus-20260416` | 0.27× | 1.43 T | 134 | agentic |
| `nvidia/nemotron-3-nano-30b-a3b` | 0.31× | 50.16 B | 257 | conversational |
| `amazon/nova-micro-v1` | 0.36× | 250.72 B | 631 | conversational |
| `meta-llama/llama-guard-4-12b` | 0.37× | 21.61 B | 485 | extractive |
| `openai/gpt-5.5-20260423` | 0.39× | 1.03 T | 126 | agentic |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$170.5 M per month** across
417 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 6.5% | 35.2% | 5.43x |
| `openai` | 11.3% | 19.3% | 1.72x |
| `moonshotai` | 2.2% | 12.2% | 5.51x |
| `google` | 8.4% | 9.1% | 1.09x |
| `deepseek` | 23.2% | 9.0% | 0.39x |
| `x-ai` | 0.8% | 3.0% | 4.03x |
| `xiaomi` | 9.0% | 3.0% | 0.33x |
| `qwen` | 1.6% | 2.3% | 1.46x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**2,687**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **46.6%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.931** by value. Both are extreme; a
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
**8.36%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.17% |
| **extractive** | 3.41% |
| **output_heavy** | 2.04% |
| **conversational** | 1.89% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 809 endpoints serving multi-provider models,
**535 are dominated** (66.1%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.2-20260616` | Cloudflare | $4.40 | 43 tok/s | Baidu | 19 |
| `z-ai/glm-5.2-20260616` | Fireworks | $4.40 | 43 tok/s | Baidu | 19 |
| `deepseek/deepseek-v4-flash-20260731` | Phala | $0.66 | 36 tok/s | Baidu | 19 |
| `~deepseek/deepseek-v4-flash-latest` | Phala | $0.66 | 36 tok/s | Baidu | 19 |
| `z-ai/glm-5.2-20260616` | Alibaba | $7.26 | 60 tok/s | Baidu | 18 |
| `z-ai/glm-5.2-20260616` | Z.AI | $4.40 | 50 tok/s | Baidu | 17 |
| `moonshotai/kimi-k3-20260715` | Morph | $22.50 | 13 tok/s | Makora | 16 |
| `z-ai/glm-5.2-20260616` | Venice | $4.40 | 53 tok/s | Baidu | 16 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-08-27` and `2026-08-28`,
**1.56%** of 450 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.56 | -0.67 to -0.44 | 0.517 | 57 | yes |
| **all** | request weighted | -0.30 | -0.75 to +0.14 | 0.044 | 384 | no |
| **conversational** | request weighted | -0.27 | -0.90 to +0.36 | 0.033 | 263 | no |
| **extractive** | request weighted | +0.38 | -0.07 to +0.82 | 0.150 | 24 | no |
| **output_heavy** | request weighted | -0.14 | -0.40 to +0.13 | 0.029 | 40 | no |
| **agentic** | unweighted | -0.34 | -0.66 to -0.01 | 0.056 | 57 | yes |
| **all** | unweighted | -0.83 | -1.09 to -0.58 | 0.135 | 384 | yes |
| **conversational** | unweighted | -1.05 | -1.34 to -0.76 | 0.225 | 263 | yes |
| **extractive** | unweighted | -0.13 | -0.42 to +0.16 | 0.013 | 24 | no |
| **output_heavy** | unweighted | -0.99 | -1.65 to -0.34 | 0.225 | 40 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.34, interval
-0.66 to -0.01, straddling zero). Weighting by requests, the
elasticity is **-0.56** (-0.67 to -0.44) and
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
| ≥2 days silent | 26 | 395 | 97.1% | 91.4% |
| ≥3 days silent | 24 | 397 | 97.6% | 91.9% |
| ≥7 days silent | 11 | 410 | 98.6% | 97.2% |
| ≥14 days silent | 5 | 416 | 98.9% | 98.4% |

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
