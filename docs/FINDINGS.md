# Findings — OpenRouter workload fingerprint

*Generated from snapshot `2026-11-20` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** 782 model-variants, 945.28 T
tokens and 41.95 B requests over the trailing 30 days.


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
| **agentic** | 104 | 766.80 T | 81.1% | 59.1 | 57,105 | large contexts, terse output, very large interactions |
| **conversational** | 318 | 115.30 T | 12.2% | 10.2 | 4,109 | moderate context per output token, human-sized interactions |
| **extractive** | 47 | 57.87 T | 6.1% | 48.6 | 4,829 | context-heavy but small interactions: classification, extraction, routing |
| **unclassified** | 187 | 5.02 T | 0.5% | — | 39 | insufficient data to classify |
| **output_heavy** | 126 | 292.97 B | 0.0% | 0.4 | 4,387 | emits one token per two consumed; in practice almost entirely image-output models |

Models classified as *agentic* account for **81.1% of all tokens**
while being 104 of 782 model-variants. Conversational
traffic, which is what most people picture when they think "LLM API", is
12.2%.

The gap between the count and the share is what the fingerprint is for. Agentic
workloads are rare per model and enormous per request.


## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.

| Model | P:C ratio | Tokens/request | Tokens (30d) | Archetype |
|---|---|---|---|---|
| `scaledown/classify-1-20260928` | 2,501.1 | 6,601 | 11.50 B | extractive |
| `upstage/solar-decide-20260928` | 1,719.7 | 3,819 | 8.22 B | extractive |
| `upstage/solar-decide-flash-20261008` | 1,468.9 | 2,920 | 5.32 B | extractive |
| `cloudflare/clairic-20261029` | 1,441.6 | 1,473 | 2.52 B | extractive |
| `microsoft/microsoft-decision-1-20261009` | 748.3 | 2,249 | 116.08 B | extractive |
| `perplexity/pplx-decider-flash-v1.2-20261016` | 562.9 | 1,949 | 105.32 B | extractive |
| `perplexity/pplx-decider-v1.2-20261016` | 490.9 | 1,925 | 1.66 T | extractive |
| `inception/mercury-decide-20260930` | 451.9 | 630 | 81.79 B | extractive |
| `inception/mercury-decide-20260930` | 437.6 | 6,254 | 77.23 B | extractive |
| `baseten/mammoth-1-20261021` | 388.6 | 713 | 24.97 B | extractive |

**Why both axes.** The top of this ranking is `scaledown/classify-1-20260928` at
2,501.1 tokens of context per token written, but its interactions
average only 6,601 tokens. A high P:C ratio alone
cannot tell a coding agent from a safety classifier; both read far more than they
write. Reading a lot per call and reading a lot per token produced are different
properties, and only their conjunction identifies agentic use.


Contrast `stepfun/step-5-preview-20261008`: 214.2 tokens of context per token
written, in interactions averaging 256,253 tokens, which
is 39× larger.
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


Across 270 ratable model-variants (at least
7 days old and above
1,000,000 monthly requests), momentum has a
median of **0.94** with a p25–p75 range of 0.70–1.15.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.


For the 18 model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median **2.01×**. That is the size of the
artefact the correction removes.


**Accelerating** — highest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `deepseek/deepseek-v4.1-flash-20261017` | 9.64× | 34.40 B | 34 | output_heavy |
| `amazon/nova-2-lite-v1` | 8.51× | 18.97 B | 353 | conversational |
| `moonshotai/kimi-k2` | 8.11× | 30.60 B | 497 | extractive |
| `mistralai/mistral-small-2603` | 5.06× | 58.99 B | 249 | conversational |
| `anthropic/claude-opus-5.5-20260921` | 4.88× | 15.00 B | 59 | conversational |
| `rekaai/reka-edge-2603` | 3.00× | 625.24 M | 245 | conversational |
| `nvidia/nemotron-3-ultra-550b-a55b-20260604` | 2.88× | 176.90 B | 169 | conversational |
| `thinkingmachines/inkling-2-small-20261107` | 2.68× | 692.03 B | 11 | agentic |

**Fading** — lowest momentum among ratable models:

| Model | Momentum | Tokens (30d) | Age (days) | Archetype |
|---|---|---|---|---|
| `mistralai/mistral-medium-3.1` | 0.00× | 30.89 B | 464 | conversational |
| `openai/gpt-oss-20b` | 0.01× | 2.76 B | 472 | conversational |
| `tencent/hy3-20260706` | 0.02× | 9.65 T | 137 | agentic |
| `tencent/hy4-preview-20260827` | 0.03× | 19.02 T | 84 | agentic |
| `openai/gpt-5-nano-2025-08-07` | 0.04× | 9.76 B | 470 | conversational |
| `stepfun/step-3.7-flash-20260528` | 0.06× | 872.54 B | 176 | agentic |
| `google/gemma-2-27b-it` | 0.10× | 550.01 M | 860 | conversational |
| `openai/gpt-6.1-sol-20260929` | 0.11× | 11.92 B | 52 | conversational |

## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **$494.6 M per month** across
496 priced model-variants.

This is an upper bound, not revenue: it ignores prompt-cache discounts, batch
pricing, BYOK traffic, negotiated rates and OpenRouter's own margin. The column
is called `implied_gross_value` and never `revenue` for that reason.

| Lab | Share of tokens | Share of implied value | Value per token of attention |
|---|---|---|---|
| `anthropic` | 7.0% | 40.8% | 5.85x |
| `openai` | 9.0% | 16.1% | 1.80x |
| `deepseek` | 36.0% | 13.7% | 0.38x |
| `tencent` | 14.6% | 7.1% | 0.49x |
| `google` | 3.3% | 6.2% | 1.91x |
| `stepfun` | 2.9% | 5.3% | 1.82x |
| `nvidia` | 3.7% | 2.1% | 0.57x |
| `moonshotai` | 2.3% | 1.6% | 0.71x |

Concentration makes the same point without naming a winner. Measured by tokens,
the labs sit at an HHI of **1,061**. Measured by money they sit at
**3,200**, past the 2,500 mark competition authorities treat as
highly concentrated, and the largest lab takes **53.5%** of
the value against 17.2% of the tokens.

The Gini coefficient across models is **0.935** by tokens
and **0.940** by value. Both are extreme; a
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
**7.48%**.

| Archetype | Median share of the advertised window used |
|---|---|
| **agentic** | 7.19% |
| **conversational** | 1.61% |
| **extractive** | 1.54% |
| **output_heavy** | 1.04% |

The pattern holds even where it should not: models bought for their long context
still leave nine tenths of it idle.

Tokens per request is a mean, so a model that fills a million-token window
occasionally and stays small usually will read low here. The number bounds
typical usage; peak capability is a separate question this cannot answer.


## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of 1,291 endpoints serving multi-provider models,
**908 are dominated** (70.3%).

| Model | Dominated endpoint | $/M out | p50 throughput | Beaten by | # better |
|---|---|---|---|---|---|
| `deepseek/deepseek-v4.1-flash-20261017` | Reka | $1.20 | 42 tok/s | DeepInfra | 45 |
| `~deepseek/deepseek-flash-latest` | Reka | $1.20 | 42 tok/s | DeepInfra | 45 |
| `z-ai/glm-5.3-flash-20260826` | DekaLLM | $0.50 | 24 tok/s | Relace | 34 |
| `~z-ai/glm-flash-latest` | DekaLLM | $0.50 | 24 tok/s | Relace | 34 |
| `z-ai/glm-5.3-flash-20260826` | Sail Research | $0.62 | 35 tok/s | Relace | 32 |
| `~z-ai/glm-flash-latest` | Sail Research | $0.62 | 35 tok/s | Relace | 32 |
| `deepseek/deepseek-v4.1-flash-20261017` | AtlasCloud | $0.78 | 84 tok/s | Particle AI | 30 |
| `~deepseek/deepseek-flash-latest` | AtlasCloud | $0.78 | 84 tok/s | Particle AI | 30 |

*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.


## 7. Is the classification stable?

Fixed thresholds only beat clustering if the labels hold still, which is
measurable, so it is measured: the share of models changing archetype between
consecutive captures.


Between `2026-11-19` and `2026-11-20`,
**0.84%** of 595 compared
models changed archetype (target: under 5%).


## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors. Token volume spans nine orders of magnitude, so classical errors would
claim confidence the data cannot support.

Two weightings, because they answer different questions. One model, one vote;
or one request, one vote.

| Segment | Weighting | Elasticity | 95% CI | R² | n | Clears zero |
|---|---|---|---|---|---|---|
| **agentic** | request weighted | -0.36 | -0.60 to -0.12 | 0.136 | 96 | yes |
| **all** | request weighted | -0.21 | -0.54 to +0.13 | 0.016 | 475 | no |
| **conversational** | request weighted | -0.21 | -0.52 to +0.11 | 0.024 | 296 | no |
| **extractive** | request weighted | -0.97 | -1.35 to -0.59 | 0.598 | 26 | yes |
| **output_heavy** | request weighted | -0.28 | -0.53 to -0.04 | 0.109 | 57 | yes |
| **agentic** | unweighted | -0.45 | -0.79 to -0.11 | 0.069 | 96 | yes |
| **all** | unweighted | -0.56 | -0.78 to -0.34 | 0.052 | 475 | yes |
| **conversational** | unweighted | -0.70 | -0.93 to -0.47 | 0.115 | 296 | yes |
| **extractive** | unweighted | -0.18 | -1.32 to +0.95 | 0.003 | 26 | no |
| **output_heavy** | unweighted | -0.45 | -0.93 to +0.04 | 0.043 | 57 | no |

**Agentic traffic, both ways.** Counting models equally, the elasticity is
-0.45 (-0.79 to -0.11); weighting by requests it is
**-0.36** (-0.60 to -0.12). The reversal this section
looks for, models indifferent to price while their volume is not, needs the first
interval to straddle zero and the second to clear it. In this capture
both clear zero.


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
| ≥2 days silent | 72 | 426 | 93.6% | 84.7% |
| ≥3 days silent | 68 | 430 | 93.8% | 84.9% |
| ≥7 days silent | 57 | 441 | 94.8% | 86.7% |
| ≥14 days silent | 36 | 462 | 97.6% | 91.7% |

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
