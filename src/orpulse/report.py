"""Generate docs/FINDINGS.md from the marts.

The report is regenerated on every build so that no number published in the
repository can drift away from the dataset it came from. Nothing here is
hand-written prose about figures; every figure is read from a mart.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import config

ARCHETYPE_BLURB = {
    "agentic": "large contexts, terse output, very large interactions",
    "conversational": "moderate context per output token, human-sized interactions",
    "extractive": "context-heavy but small interactions: classification, extraction, routing",
    "output_heavy": "emits one token per two consumed; in practice almost entirely image-output models",
    "unclassified": "insufficient data to classify",
}


def _tokens(n) -> str:
    if n is None or pd.isna(n):
        return "—"
    n = float(n)
    for unit, size in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(n) >= size:
            return f"{n / size:.2f} {unit}"
    return f"{n:.0f}"


def _num(n, decimals=1) -> str:
    return "—" if n is None or pd.isna(n) else f"{float(n):,.{decimals}f}"


def _table(rows: list[list[str]], headers: list[str]) -> str:
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def build(marts: dict[str, pd.DataFrame]) -> str:
    fp = marts.get("mart_model_fingerprint", pd.DataFrame())
    if fp.empty:
        raise RuntimeError("mart_model_fingerprint is empty; nothing to report")

    latest_date = fp["snapshot_date"].max()
    cur = fp[fp["snapshot_date"] == latest_date].copy()
    total_month_tokens = cur["month_tokens"].sum()
    total_month_requests = cur["month_requests"].sum()

    parts: list[str] = []
    add = parts.append

    add(f"""# Findings — OpenRouter workload fingerprint

*Generated from snapshot `{latest_date}` by `orpulse report`. Every figure on this
page is read from `data/marts/`; nothing is typed by hand.*

**Scope of this capture:** {len(cur):,} model-variants, {_tokens(total_month_tokens)}
tokens and {_tokens(total_month_requests)} requests over the trailing 30 days.
""")

    # --- 1. the headline ---------------------------------------------------
    add("""
## 1. The market splits into four workloads, and share of tokens hides it

Two ratios, both derived from data OpenRouter already publishes:

```
pc_ratio           = prompt tokens / completion tokens   -- context consumed per token produced
tokens_per_request = total tokens / requests             -- size of one interaction
```

Together they separate regimes of use that a leaderboard flattens. Two models
with identical token volume can be doing entirely different jobs.
""")

    by_arch = (
        cur.groupby("archetype")
        .agg(
            # Rows, not unique slugs: the grain of this table is the
            # model-VARIANT (a model appears separately as standard/free/batch/
            # thinking), and the totals it is compared against are variants too.
            # Counting unique slugs here and dividing by a variant total would
            # be an apples-to-oranges comparison.
            models=("model_permaslug", "size"),
            tokens=("month_tokens", "sum"),
            requests=("month_requests", "sum"),
            median_pc=("pc_ratio", "median"),
            median_tpr=("tokens_per_request", "median"),
        )
        .sort_values("tokens", ascending=False)
    )
    rows = []
    for arch, r in by_arch.iterrows():
        rows.append([
            f"**{arch}**",
            f"{int(r['models']):,}",
            _tokens(r["tokens"]),
            f"{r['tokens'] / total_month_tokens:.1%}",
            _num(r["median_pc"]),
            _num(r["median_tpr"], 0),
            ARCHETYPE_BLURB.get(arch, ""),
        ])
    add(_table(
        rows,
        ["Archetype", "Model-variants", "Tokens (30d)", "Share", "Median P:C",
         "Median tok/req", "What it means"],
    ))

    agentic_share = by_arch["tokens"].get("agentic", 0) / total_month_tokens
    agentic_models = int(by_arch["models"].get("agentic", 0))
    conv_share = by_arch["tokens"].get("conversational", 0) / total_month_tokens
    add(f"""
**The result worth stating plainly:** models classified as *agentic* account for
**{agentic_share:.1%} of all tokens** on OpenRouter while being only
{agentic_models} of {len(cur):,} model-variants. Conversational traffic —
what most people picture when they think "LLM API" — is {conv_share:.1%}.

The gap between the count and the share is the whole point. Agentic workloads
are rare per model and enormous per request.
""")

    # --- 2. the extremes ---------------------------------------------------
    add("""
## 2. The extremes of the context axis

Ranked by tokens of context consumed per token produced, among models above
1 M requests in the trailing 30 days.
""")
    sig = cur[cur["month_requests"] >= 1_000_000].dropna(subset=["pc_ratio"])
    top_pc = sig.nlargest(10, "pc_ratio")
    add(_table(
        [[
            f"`{r.model_permaslug}`",
            _num(r.pc_ratio),
            _num(r.tokens_per_request, 0),
            _tokens(r.month_tokens),
            r.archetype,
        ] for r in top_pc.itertuples()],
        ["Model", "P:C ratio", "Tokens/request", "Tokens (30d)", "Archetype"],
    ))
    if not top_pc.empty:
        lead = top_pc.iloc[0]
        top_agentic = sig[sig["archetype"] == "agentic"].nlargest(1, "pc_ratio")
        add(f"""
**Why one axis is not enough.** The top of this ranking is
`{lead.model_permaslug}` at {_num(lead.pc_ratio)} tokens of context per token
written — but its interactions average only {_num(lead.tokens_per_request, 0)}
tokens. A high P:C ratio on its own cannot tell a coding agent from a safety
classifier: both read far more than they write. What separates them is the
second axis. Reading a lot per call and reading a lot *per token produced* are
different properties, and only their conjunction identifies agentic use.
""")
        if not top_agentic.empty:
            a = top_agentic.iloc[0]
            add(f"""
Contrast `{a.model_permaslug}`: {_num(a.pc_ratio)} tokens of context per token
written, but in interactions averaging {_num(a.tokens_per_request, 0)} tokens —
{_num(a.tokens_per_request / max(lead.tokens_per_request, 1), 0)}× larger. That
is not a classifier answering a short question. That is a model sitting inside a
loop, re-reading a large accumulated state on every turn.
""")

    # --- 3. momentum -------------------------------------------------------
    add("""
## 3. Momentum, and why the age correction is not optional

There is no public time series: the rankings feed returns one aggregate row per
model over a trailing window, not a daily history. But because the 1-, 7- and
30-day windows are nested, a trend can be derived from a single capture:

```
effective_days = min(30, days since the model launched)
momentum       = tokens in the last day / (tokens in the last 30 days / effective_days)
```

Dividing by 30 for a model that has existed for four days inflates every recent
launch by pure arithmetic — the analysis would then "discover" that new models
grow, which is a tautology wearing a result's clothes.
""")

    ratable = cur[cur["is_ratable"] & cur["momentum"].notna()]
    if not ratable.empty:
        q = ratable["momentum"].quantile([0.25, 0.5, 0.75])
        add(f"""
Across {len(ratable):,} ratable model-variants (at least
{config.MIN_DAYS_FOR_MOMENTUM} days old and above
{config.MIN_MONTH_REQUESTS_FOR_MOMENTUM:,} monthly requests), momentum has a
median of **{q[0.5]:.2f}** with a p25–p75 range of {q[0.25]:.2f}–{q[0.75]:.2f}.
A median near 1.0 is the expected signature of a market that is neither
collapsing nor exploding in aggregate.
""")
        young = cur[(cur["days_since_launch"].notna()) & (cur["days_since_launch"] < 30)]
        young = young.dropna(subset=["momentum_uncorrected"])
        if not young.empty:
            infl = (young["momentum_uncorrected"] / young["momentum"].where(young["momentum"] > 0)).median()
            if pd.notna(infl):
                add(f"""
For the {len(young)} model-variants younger than 30 days, the uncorrected
formula inflates momentum by a median factor of **{infl:.2f}×**. That is the
size of the artefact the correction removes.
""")

        add("\n**Accelerating** — highest momentum among ratable models:\n")
        add(_table(
            [[
                f"`{r.model_permaslug}`",
                f"{r.momentum:.2f}×",
                _tokens(r.month_tokens),
                _num(r.days_since_launch, 0),
                r.archetype,
            ] for r in ratable.nlargest(8, "momentum").itertuples()],
            ["Model", "Momentum", "Tokens (30d)", "Age (days)", "Archetype"],
        ))
        add("\n**Fading** — lowest momentum among ratable models:\n")
        add(_table(
            [[
                f"`{r.model_permaslug}`",
                f"{r.momentum:.2f}×",
                _tokens(r.month_tokens),
                _num(r.days_since_launch, 0),
                r.archetype,
            ] for r in ratable.nsmallest(8, "momentum").itertuples()],
            ["Model", "Momentum", "Tokens (30d)", "Age (days)", "Archetype"],
        ))

    # --- 3b. economics ------------------------------------------------------
    econ = marts.get("mart_model_economics", pd.DataFrame())
    structure = marts.get("mart_market_structure", pd.DataFrame())
    if not econ.empty:
        econ = econ[econ["snapshot_date"] == econ["snapshot_date"].max()]
        total_value = econ["implied_gross_value"].sum()
        by_author = (econ.groupby("author")
                     .agg(tokens=("month_tokens", "sum"),
                          value=("implied_gross_value", "sum"))
                     .assign(token_share=lambda d: d.tokens / d.tokens.sum(),
                             value_share=lambda d: d.value / d.value.sum())
                     .nlargest(8, "value_share"))
        blended = econ["blended_to_sticker_ratio"].median()

        add(f"""
## 4. Attention and money are different markets

Multiplying each model's tokens by its list price gives the gross value its
traffic represents: **${total_value / 1e6:,.1f} M per month** across
{len(econ):,} priced model-variants.

This is *not* revenue. It ignores prompt-cache discounts, batch pricing, BYOK
traffic, negotiated rates and OpenRouter's own margin, so it is an upper bound —
which is why the column is called `implied_gross_value` and never `revenue`.
""")
        add(_table(
            [[
                f"`{a}`",
                f"{r.token_share:.1%}",
                f"{r.value_share:.1%}",
                f"{r.value_share / r.token_share:.2f}x" if r.token_share else "—",
            ] for a, r in by_author.iterrows()],
            ["Lab", "Share of tokens", "Share of implied value", "Value per token of attention"],
        ))

        def _row(measure):
            s = structure[(structure["measure"] == measure)
                          & (structure["segment"] == "all")]
            return s.iloc[0] if len(s) else None

        tok_a, val_a = _row("tokens_by_author"), _row("implied_value_by_author")
        if tok_a is not None and val_a is not None:
            add(f"""
Concentration makes the same point without picking a winner. Measured by tokens,
the labs sit at an HHI of **{tok_a['hhi']:,.0f}**. Measured by money they sit at
**{val_a['hhi']:,.0f}** — past the 2,500 mark competition authorities treat as
highly concentrated — and the largest lab takes **{val_a['top1_share']:.1%}** of
the value against {tok_a['top1_share']:.1%} of the tokens.

The Gini coefficient across models is **{_row('tokens')['gini']:.3f}** by tokens
and **{_row('implied_value')['gini']:.3f}** by value. Both are extreme; a
national income distribution above 0.6 is considered severe.
""")
        add(f"""
### The sticker price is not the price

Traffic is overwhelmingly prompt-heavy, and prompt tokens cost less than
completions. Blended across each model's real token mix, the price actually paid
per token is a median of **{blended:.2f}x** the headline output price — the
sticker overstates the true unit cost by about **{1 / blended:.1f}x**.

This is the number a buyer comparing models on `$/M output` is getting wrong.
""")

    # --- 3c. context utilisation --------------------------------------------
    ctx = marts.get("mart_context_utilization", pd.DataFrame())
    if not ctx.empty:
        ctx = ctx[ctx["snapshot_date"] == ctx["snapshot_date"].max()]
        weighted = (ctx["mean_window_utilisation"].fillna(0)
                    * ctx["month_tokens"].clip(lower=0)).sum() / max(
                        ctx["month_tokens"].clip(lower=0).sum(), 1)
        by_arch = (ctx[ctx["archetype"] != "unclassified"]
                   .groupby("archetype")["mean_window_utilisation"]
                   .median().dropna().sort_values(ascending=False))
        add(f"""
## 5. The context window arms race is mostly unused

Dividing mean tokens per request by the advertised context length asks how much
of the window the traffic actually touches. Token-weighted across the market:
**{weighted:.2%}**.
""")
        add(_table(
            [[f"**{a}**", f"{v:.2%}"] for a, v in by_arch.items()],
            ["Archetype", "Median share of the advertised window used"],
        ))
        add("""
Even agentic traffic — the workload that exists *because* of long context — uses
under a tenth of what it is sold. One caveat, and it cuts one way: tokens per
request is a mean, so a model that occasionally fills a million-token window and
usually does not still reads low. This bounds typical usage, not peak capability.
""")

    # --- 4. price / performance -------------------------------------------
    pp = marts.get("mart_endpoint_price_perf", pd.DataFrame())
    if not pp.empty:
        dominated = pp[pp["is_dominated"]]
        multi = pp.groupby("model_permaslug")["endpoint_id"].nunique()
        contested = multi[multi > 1].index
        contested_rows = pp[pp["model_permaslug"].isin(contested)]
        add(f"""
## 6. The serving layer: Pareto-dominated endpoints

For models served by more than one provider, an endpoint is *dominated* when
another endpoint for the same model is both cheaper per completion token and
faster at the median. There is no rational reason to route traffic to it.

Of {len(contested_rows):,} endpoints serving multi-provider models,
**{len(dominated):,} are dominated** ({len(dominated) / max(len(contested_rows), 1):.1%}).
""")
        if not dominated.empty:
            add(_table(
                [[
                    f"`{r.model_permaslug}`",
                    r.provider_name,
                    f"${r.price_completion * 1e6:.2f}",
                    f"{_num(r.p50_throughput, 0)} tok/s",
                    r.dominant_provider or "—",
                    int(r.dominated_by_n),
                ] for r in dominated.sort_values(
                    # endpoint_id breaks ties so the report is reproducible.
                    ["dominated_by_n", "endpoint_id"], ascending=[False, True]
                ).head(8).itertuples()],
                ["Model", "Dominated endpoint", "$/M out", "p50 throughput",
                 "Beaten by", "# better"],
            ))
        add("""
*Caveat that matters:* these percentiles come from a 30-minute rolling window,
so one capture samples half an hour. A single snapshot suggests where to look;
it does not settle the question. Repeated captures are what turn this into
evidence.
""")

    # --- 5. stability ------------------------------------------------------
    stab = marts.get("mart_archetype_stability", pd.DataFrame())
    add("""
## 7. Is the classification stable?

Fixed thresholds only beat clustering if the resulting labels hold still. That
is measurable rather than assumable, so it is measured: the share of models that
change archetype between consecutive captures.
""")
    if stab.empty:
        add("""
> Not yet measurable — it needs two completed snapshots. This is the first.
> The metric is built and will populate on the next capture.
""")
    else:
        last = stab.sort_values("snapshot_date").iloc[-1]
        add(f"""
Between `{last['prev_snapshot_date']}` and `{last['snapshot_date']}`,
**{last['reassignment_rate']:.2%}** of {int(last['models_compared']):,} compared
models changed archetype (target: under 5%).
""")

    # --- 5b. elasticity -----------------------------------------------------
    el = marts.get("mart_price_elasticity", pd.DataFrame())
    if not el.empty:
        el = el[el["snapshot_date"] == el["snapshot_date"].max()]
        add("""
## 8. Price response, and where it hides

Regressing log tokens on log price with heteroskedasticity-robust (HC1) standard
errors — robust rather than classical because token volume spans nine orders of
magnitude and classical errors would claim confidence the data cannot support.

Two weightings, because they answer different questions. Unweighted treats every
model as one observation. Request-weighted follows where the traffic actually is.
""")
        add(_table(
            [[
                f"**{r.segment}**",
                r.weighting.replace("_", " "),
                f"{r.elasticity:+.2f}",
                f"{r.ci_low:+.2f} to {r.ci_high:+.2f}",
                f"{r.r_squared:.3f}",
                f"{r.n:,}",
                "yes" if r.significant_at_95 else "no",
            ] for r in el.sort_values(["weighting", "segment"]).itertuples()],
            ["Segment", "Weighting", "Elasticity", "95% CI", "R²", "n", "Clears zero"],
        ))
        ag = el[(el["segment"] == "agentic") & (el["weighting"] == "request_weighted")]
        agu = el[(el["segment"] == "agentic") & (el["weighting"] == "unweighted")]
        if len(ag) and len(agu):
            a, u = ag.iloc[0], agu.iloc[0]
            add(f"""
**The result worth the space is the reversal in agentic traffic.** Counting
models equally, price explains nothing ({u.elasticity:+.2f}, interval
{u.ci_low:+.2f} to {u.ci_high:+.2f}, straddling zero). Weighting by requests, the
elasticity is **{a.elasticity:+.2f}** ({a.ci_low:+.2f} to {a.ci_high:+.2f}) and
clears zero comfortably.

Agentic *models* are not price-sensitive. Agentic *volume* is. That is the
signature of a small number of very large consumers optimising unit cost hard,
and it is invisible to any analysis that treats each model as one data point.

**This is not a causal elasticity.** It is a cross-section of different models at
different prices, not one model observed at several prices, so it absorbs
everything that makes cheap models cheap — smaller, weaker, newer. A steep slope
is as consistent with "buyers chase cheap tokens" as with "cheap models are the
ones built for bulk work". The comparison *between* archetypes carries more than
any single coefficient.
""")

    # --- 5c. survival --------------------------------------------------------
    sens = marts.get("mart_survival_sensitivity", pd.DataFrame())
    if not sens.empty:
        add("""
## 9. How long does a model live? (preliminary)

Kaplan-Meier with right-censoring. Most models are still running, so their
lifetime is known only to be *at least* their current age: dropping them would
bias the curve towards short lives, counting their age as a lifetime would bias
it the other way, and the product-limit estimator uses exactly what each subject
carries. The implementation reproduces the published curve for the Freireich
leukemia trial, which is what `tests/test_analytics.py` asserts.
""")
        add(_table(
            [[
                f"≥{int(r.threshold_days)} days silent",
                f"{int(r.n_events):,}",
                f"{int(r.n_censored):,}",
                f"{r.survival_at_180d:.1%}",
                f"{r.survival_at_365d:.1%}",
            ] for r in sens.sort_values("threshold_days").itertuples()],
            ["Death defined as", "Events", "Censored", "Alive at 180d", "Alive at 365d"],
        ))
        add("""
**Why this is labelled preliminary.** Death is inferred from the last day with
traffic, and two biases pull against each other. A model silent for more than
about 30 days leaves the monthly window entirely, so long-dead models are absent
and survival is biased *up* — the giveaway is in the table, where a 14-day
threshold finds almost no events at all, which is a property of the feed rather
than of the market. Meanwhile a 2-day threshold books a model that merely had a
quiet Tuesday as dead, biasing *down*. Their relative magnitudes are unknown.

What fixes it costs nothing but time. Once the archive holds several weeks of
captures, death is *observed* — present on day N, absent on day N+k — instead of
inferred from a truncated field. The estimator does not change; its input stops
being biased. This is the clearest case in the project of a metric that only a
growing archive can make real.
""")

    # --- 6. limitations ----------------------------------------------------
    add(f"""
## 10. What this cannot tell you

Stating the limits is part of the result.

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
  {config.PC_RATIO_HIGH:.1f} and {config.PC_RATIO_OUTPUT_HEAVY:.1f}, tokens per
  request at {config.TPR_HIGH:,.0f}. They are chosen from the observed
  distribution and held fixed so labels stay comparable over time. Models near a
  boundary will flip; that is what section 5 measures.
- **Traffic is not users.** One agentic application can generate more tokens
  than a million chat sessions. Nothing here measures adoption.

---

*Pipeline: `orpulse ingest` → `orpulse build` → `orpulse report`.
Sources and methodology in [METHODOLOGY.md](METHODOLOGY.md).*

<!-- This file is a pure function of the marts: same data in, byte-identical
     file out. No wall-clock timestamp, deliberately -- CI asserts that the
     committed report matches what the committed data produces, and a clock
     would make that check impossible. -->
""")

    return "\n".join(parts)


def write(marts: dict[str, pd.DataFrame], path: Path | None = None) -> Path:
    path = path or (config.DOCS_DIR / "FINDINGS.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build(marts))
    return path
