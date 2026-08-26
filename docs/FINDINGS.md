# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-08-26` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 564 model-variants, 331.68 T
tokens and 18.42 B requests over the trailing 30 days.


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
| **agentic** | 68 | 252.17 T | 76.0% | 51.7 | 48,491 | large contexts, terse output, very large interactions |
| **conversational** | 273 | 75.89 T | 22.9% | 10.0 | 3,778 | moderate context per output token, human-sized interactions |
| **unclassified** | 119 | 2.22 T | 0.7% | — | 28 | insufficient data to classify |
| **extractive** | 28 | 1.26 T | 0.4% | 43.5 | 8,109 | context-heavy but small interactions: classification, extraction, routing |
| **output_heavy** | 76 | 147.12 B | 0.0% | 0.4 | 4,556 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **76.0% of all tokens**
while being 68 of 564 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
22.9%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `meta-llama/llama-guard-4-12b` | 367.5 | 1,311 | 22.41 B | extractive |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 156.1 | 100,806 | 13.41 T | agentic |
| `poolside/laguna-s-2.1-20260720` | 149.6 | 92,927 | 6.46 T | agentic |
| `xiaomi/mimo-v2.5-20260422` | 127.7 | 74,133 | 28.43 T | agentic |
| `poolside/laguna-xs-2.1-20260625` | 125.7 | 56,258 | 674.97 B | agentic |
| `anthropic/claude-opus-5-fast-20260723` | 99.4 | 87,751 | 139.40 B | agentic |
| `nvidia/nemotron-3.5-lightning-20260807` | 98.0 | 73,598 | 1.93 T | agentic |
| `openai/gpt-5.6-terra-20260709` | 86.5 | 36,615 | 3.15 T | agentic |
| `qwen/qwen3-coder-next-2025-02-03` | 84.2 | 26,988 | 97.40 B | agentic |
| `xiaomi/mimo-v2.5-pro-20260422` | 76.8 | 56,160 | 2.28 T | agentic |

**Why both axes.** The top of this ranking is `meta-llama/llama-guard-4-12b` at
367.5 tokens of context per token written, but its interactions
average only 1,311 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `nvidia/nemotron-3-ultra-550b-a55b-20260604`: 156.1 tokens of context per token
written, in interactions averaging 100,806 tokens, which
is 77× larger.
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


Across 217 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.97** with a p25–p75 range of 0.75–1.20.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 17 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **2.00×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-audio-mini` | 8.68× | 2.83 B | 219 | output_heavy |
| `openai/gpt-5-nano-2025-08-07` | 6.27× | 4.56 B | 384 | conversational |
| `openai/gpt-5.6-luna-20260709` | 3.41× | 13.24 B | 48 | output_heavy |
| `google/gemini-3.1-flash-lite-image-20260630` | 3.34× | 7.02 B | 57 | output_heavy |
| `google/gemini-3.7-flash-20260813` | 3.00× | 3.41 T | 13 | agentic |
| `bytedance-seed/seed-2.0-mini-20260224` | 2.98× | 23.46 B | 181 | conversational |
| `openai/gpt-5.6-sol-pro-20260709` | 2.86× | 297.67 B | 48 | agentic |
| `google/gemini-3.7-flash-20260813` | 2.70× | 13.11 B | 13 | conversational |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `openai/gpt-5.2-chat-20251211` | 0.00× | 5.33 B | 259 | conversational |
| `perceptron/perceptron-mk1-20260512` | 0.04× | 6.64 B | 106 | extractive |
| `google/gemma-4-26b-a4b-it-20260403` | 0.08× | 54.73 B | 145 | conversational |
| `thinkingmachines/inkling-small-20260730` | 0.11× | 31.69 B | 27 | conversational |
| `microsoft/phi-4` | 0.18× | 2.57 B | 593 | conversational |
| `meta/muse-glimmer-30b-20260810` | 0.20× | 70.43 B | 17 | conversational |
| `openai/gpt-4o-2024-05-13` | 0.20× | 3.83 B | 835 | extractive |
| `mistralai/mistral-medium-3.5-20260430` | 0.25× | 32.32 B | 118 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$192.5 M per month** across
405 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 6.8% | 45.4% | 6.71x |
| `openai` | 11.0% | 14.4% | 1.31x |
| `moonshotai` | 2.3% | 10.7% | 4.64x |
| `deepseek` | 23.4% | 9.2% | 0.39x |
| `google` | 8.3% | 7.0% | 0.84x |
| `x-ai` | 0.8% | 2.6% | 3.38x |
| `xiaomi` | 9.3% | 2.6% | 0.28x |
| `tencent` | 10.1% | 2.4% | 0.24x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,232**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **53.6%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.940** by value. Both are extreme; a
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
**9.09%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.89% |
| **extractive** | 3.65% |
| **output_heavy** | 2.07% |
| **conversational** | 1.81% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 764 endpoints serving multi-provider models,
**497 are dominated** (65.1%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `z-ai/glm-5.2-20260616` | Crusoe | $4.40 | 27 tok/s | Ambient | 28 |
| `z-ai/glm-5.2-20260616` | Cloudflare | $4.40 | 36 tok/s | Ambient | 24 |
| `z-ai/glm-5.2-20260616` | Z.AI | $4.40 | 38 tok/s | Ambient | 22 |
| `deepseek/deepseek-v4-flash-20260731` | Cloudflare | $1.32 | 41 tok/s | Relace | 17 |
| `~deepseek/deepseek-v4-flash-latest` | Cloudflare | $1.32 | 41 tok/s | Relace | 17 |
| `z-ai/glm-5.2-20260616` | Fireworks | $4.40 | 47 tok/s | DigitalOcean | 16 |
| `moonshotai/kimi-k2.6-20260420` | Baidu | $4.00 | 21 tok/s | StreamLake | 16 |
| `z-ai/glm-5.1-20260406` | Venice | $4.84 | 13 tok/s | GMICloud | 15 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-08-25` and `2026-08-26`,
**0.68%** of 443 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.54 | -0.65 to -0.43 | 0.542 | 54 | yes |
| **all** | request weighted | -0.30 | -0.72 to +0.13 | 0.043 | 372 | no |
| **conversational** | request weighted | -0.25 | -0.90 to +0.40 | 0.027 | 254 | no |
| **extractive** | request weighted | -0.19 | -1.19 to +0.80 | 0.019 | 25 | no |
| **output_heavy** | request weighted | -0.08 | -0.38 to +0.22 | 0.009 | 39 | no |
| **agentic** | unweighted | -0.24 | -0.59 to +0.11 | 0.029 | 54 | no |
| **all** | unweighted | -0.54 | -0.78 to -0.30 | 0.063 | 372 | yes |
| **conversational** | unweighted | -0.65 | -0.88 to -0.42 | 0.105 | 254 | yes |
| **extractive** | unweighted | -0.30 | -0.73 to +0.13 | 0.050 | 25 | no |
| **output_heavy** | unweighted | -1.04 | -1.81 to -0.28 | 0.212 | 39 | yes |

**The reversal in agentic traffic is the result worth the space.** Counting
models equally, price explains nothing (-0.24, interval
-0.59 to +0.11, straddling zero). Weighting by requests, the
elasticity is **-0.54** (-0.65 to -0.43) and
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
| ≥2 days silent | 32 | 377 | 96.4% | 91.1% |
| ≥3 days silent | 19 | 390 | 98.0% | 96.0% |
| ≥7 days silent | 9 | 400 | 98.6% | 98.1% |
| ≥14 days silent | 3 | 406 | 99.4% | 98.9% |

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
