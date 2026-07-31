"""Build a single self-contained HTML page from the marts.

No server, no CDN, no runtime dependency: one file that opens anywhere. That is
worth more than an interactive app for something meant to be sent as a link, and
it means the page can be published as-is under a strict content policy.

Light and dark are one stylesheet apart because every colour is a custom
property. The dark steps are chosen for the dark surface, not flipped from the
light ones.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from . import charts, config, ingest, quality
from .charts import esc, fmt_compact
from .transform import load_marts

log = logging.getLogger(__name__)

ARCHETYPE_COLOUR = {
    "agentic": "s1",
    "conversational": "s2",
    "extractive": "s3",
}
NEUTRAL = "neutral"

STYLE = """
:root{
  color-scheme:light;
  --surface:#fcfcfb; --surface-2:#f4f4f1; --border:#e2e1dc;
  --text:#0b0b0b; --muted:#52514e;
  --s1:#2a78d6; --s2:#eb6834; --s3:#1baf7a; --neutral:#8a8a85;
  /* Status is a separate scale from the categorical one: reusing a series
     hue for "healthy" would make a chart legend read as a state. */
  --ok:#1f7a4d; --warn:#a86a00; --bad:#b3261e;
}
@media (prefers-color-scheme:dark){
  :root:where(:not([data-theme="light"])){
    color-scheme:dark;
    --surface:#1a1a19; --surface-2:#232322; --border:#33332f;
    --text:#ffffff; --muted:#c3c2b7;
    --s1:#3987e5; --s2:#d95926; --s3:#199e70; --neutral:#77776f;
    --ok:#3da06a; --warn:#c98f2a; --bad:#e06b62;
  }
}
:root[data-theme="dark"]{
  color-scheme:dark;
  --surface:#1a1a19; --surface-2:#232322; --border:#33332f;
  --text:#ffffff; --muted:#c3c2b7;
  --s1:#3987e5; --s2:#d95926; --s3:#199e70; --neutral:#77776f;
  --ok:#3da06a; --warn:#c98f2a; --bad:#e06b62;
}
*{box-sizing:border-box}
body{margin:0;background:var(--surface);color:var(--text);
  font:16px/1.6 ui-sans-serif,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  -webkit-font-smoothing:antialiased}
.wrap{max-width:960px;margin:0 auto;padding:56px 22px 96px}
h1{font-size:clamp(30px,5vw,46px);line-height:1.1;letter-spacing:-.022em;margin:0 0 12px}
h2{font-size:clamp(20px,3vw,26px);letter-spacing:-.015em;margin:64px 0 6px}
h3{font-size:16px;margin:34px 0 6px;letter-spacing:-.005em}
p{margin:0 0 14px;max-width:68ch}
.lede{font-size:19px;color:var(--muted);max-width:66ch}
.muted{color:var(--muted)}
small{color:var(--muted);font-size:13.5px}
code{font:13px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;
  background:var(--surface-2);padding:1px 5px;border-radius:4px}
pre{background:var(--surface-2);border:1px solid var(--border);border-radius:10px;
  padding:14px 16px;overflow-x:auto;font:13px/1.6 ui-monospace,Menlo,monospace}
a{color:var(--s1)}
hr{border:0;border-top:1px solid var(--border);margin:56px 0 0}

.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(158px,1fr));
  gap:12px;margin:26px 0 8px}
.tile{background:var(--surface-2);border:1px solid var(--border);
  border-radius:12px;padding:14px 16px}
.tile .v{font-size:27px;font-weight:640;letter-spacing:-.02em;line-height:1.15}
.tile .k{font-size:12.5px;color:var(--muted);margin-top:3px}

figure{margin:22px 0 8px}
figcaption{font-size:13.5px;color:var(--muted);margin-top:10px;max-width:70ch}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
.chart{display:block;width:100%;height:auto;min-width:560px;overflow:visible}
.grid{stroke:var(--muted);stroke-opacity:.14;stroke-width:1}
.cut{stroke:var(--muted);stroke-opacity:.55;stroke-width:1.5;stroke-dasharray:5 4}
.zero{stroke:var(--muted);stroke-opacity:.45;stroke-width:1.5}
.tick{fill:var(--muted);font-size:11.5px}
.axis-title{fill:var(--muted);font-size:12.5px}
.row-label{fill:var(--text);font-size:13px}
.row-value{fill:var(--text);font-size:12.5px;font-variant-numeric:tabular-nums}
.row-value .muted{fill:var(--muted)}
.col-head{fill:var(--muted);font-size:12.5px;letter-spacing:.02em}
.point-label{fill:var(--text);font-size:11.5px;paint-order:stroke;
  stroke:var(--surface);stroke-width:3px;stroke-linejoin:round}
.dot{stroke:var(--surface);stroke-width:2}
.bar{stroke:var(--surface);stroke-width:2}
.ci{stroke-width:2.5;stroke-linecap:round}
.step{fill:none;stroke:var(--s1);stroke-width:2;stroke-linejoin:round}
.band{fill:var(--s1);fill-opacity:.14}
.censor{stroke:var(--s1);stroke-width:1.5;stroke-opacity:.75}
.empty{color:var(--muted);font-style:italic}

.legend{display:flex;flex-wrap:wrap;gap:14px;margin:12px 0 0;
  font-size:13px;color:var(--muted)}
.legend span{display:inline-flex;align-items:center;gap:6px}
.swatch{width:11px;height:11px;border-radius:3px;display:inline-block}

table{border-collapse:collapse;width:100%;font-size:13.5px;min-width:520px}
th,td{text-align:left;padding:7px 12px 7px 0;border-bottom:1px solid var(--border);
  white-space:nowrap}
th{color:var(--muted);font-weight:560;font-size:12.5px}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
details{margin:16px 0}
summary{cursor:pointer;color:var(--muted);font-size:13.5px}
summary:hover{color:var(--text)}

.callout{border-left:3px solid var(--s2);background:var(--surface-2);
  border-radius:0 10px 10px 0;padding:14px 18px;margin:20px 0}
.callout p:last-child{margin-bottom:0}
.checks{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));
  gap:10px;margin:18px 0}
/* State is encoded in the stripe, the pill text and the colour together, never
   in colour alone -- and never in an emoji, which screen readers announce as
   whatever their vendor decided it means. */
.check{background:var(--surface-2);border:1px solid var(--border);
  border-left:3px solid var(--ok);border-radius:0 10px 10px 0;
  padding:11px 14px;font-size:13px}
.check.warn{border-left-color:var(--warn)}
.check.bad{border-left-color:var(--bad)}
.check b{display:block;font-weight:580;margin-bottom:3px;
  font-variant-numeric:tabular-nums}
.pill{display:inline-block;font-size:10.5px;font-weight:640;letter-spacing:.07em;
  text-transform:uppercase;padding:1px 6px;border-radius:4px;margin-right:7px;
  vertical-align:1px;color:var(--surface);background:var(--ok)}
.pill.warn{background:var(--warn)}
.pill.bad{background:var(--bad)}
:focus-visible{outline:2px solid var(--s1);outline-offset:3px;border-radius:3px}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
"""


# --- helpers ---------------------------------------------------------------


def _pct(v, d=1):
    return "—" if v is None or not np.isfinite(v) else f"{v:.{d}%}"


def _tile(value, key):
    return f'<div class="tile"><div class="v">{value}</div><div class="k">{esc(key)}</div></div>'


def _table(df: pd.DataFrame, columns, numeric=()) -> str:
    head = "".join(
        f'<th class="num">{esc(t)}</th>' if k in numeric else f"<th>{esc(t)}</th>"
        for k, t in columns
    )
    rows = []
    for r in df.itertuples():
        cells = []
        for k, _ in columns:
            v = getattr(r, k)
            cls = ' class="num"' if k in numeric else ""
            cells.append(f"<td{cls}>{v}</td>")
        rows.append(f"<tr>{''.join(cells)}</tr>")
    return (f'<div class="scroll"><table><thead><tr>{head}</tr></thead>'
            f"<tbody>{''.join(rows)}</tbody></table></div>")


def _legend(items) -> str:
    return '<div class="legend">' + "".join(
        f'<span><i class="swatch" style="background:var(--{c})"></i>{esc(t)}</span>'
        for c, t in items
    ) + "</div>"


# --- sections --------------------------------------------------------------


def _hero(fp, econ, structure):
    total_tokens = fp["month_tokens"].sum()
    agentic = fp[fp["archetype"] == "agentic"]
    share = agentic["month_tokens"].sum() / total_tokens if total_tokens else 0
    value = econ["implied_gross_value"].sum() if not econ.empty else float("nan")
    agentic_value = (
        econ[econ["archetype"] == "agentic"]["value_share"].sum()
        if not econ.empty else float("nan")
    )
    author_value = structure[
        (structure["measure"] == "implied_value_by_author") & (structure["segment"] == "all")
    ]
    author_tokens = structure[
        (structure["measure"] == "tokens_by_author") & (structure["segment"] == "all")
    ]
    hhi_v = author_value["hhi"].iloc[0] if len(author_value) else float("nan")
    hhi_t = author_tokens["hhi"].iloc[0] if len(author_tokens) else float("nan")

    return f"""
<h1>What the LLM market is actually doing</h1>
<p class="lede">Derived from OpenRouter's public data. Two ratios nobody
publishes separate models that read enormous contexts to emit almost nothing
from models that hold conversations. The first group is a tenth of the catalogue
and most of the market — by volume and by value alike. Where attention and money
<em>do</em> part company is one level up, between the labs.</p>

<div class="tiles">
  {_tile(f"{len(agentic)}<span class='muted' style='font-size:18px'> / {len(fp)}</span>", "agentic model-variants")}
  {_tile(f"{_pct(share, 0)}<span class='muted' style='font-size:18px'> / {_pct(agentic_value, 0)}</span>", "agentic: tokens / value")}
  {_tile("$" + fmt_compact(value), "implied gross value / month")}
  {_tile(f"{hhi_v:,.0f}<span class='muted' style='font-size:18px'> / {hhi_t:,.0f}</span>", "lab HHI: money / tokens")}
</div>
<p><small>The last tile is the headline of section 2: measured by money, the
market is more than twice as concentrated as the token leaderboard suggests.</small></p>
"""


def _workload_plane(fp):
    d = fp.dropna(subset=["pc_ratio", "tokens_per_request"])
    d = d[(d["pc_ratio"] > 0) & (d["tokens_per_request"] > 0) & (d["month_requests"] >= 1e5)]
    biggest = (d.sort_values("month_tokens", ascending=False)
               .groupby(d["archetype"].map(ARCHETYPE_COLOUR).fillna(NEUTRAL))
               .head(1)["model_permaslug"].tolist())
    points = [{
        "x": float(r.pc_ratio), "y": float(r.tokens_per_request),
        "size": float(r.month_tokens or 1),
        "colour": ARCHETYPE_COLOUR.get(r.archetype, NEUTRAL),
        "name": r.model_permaslug,
        "label": r.model_permaslug.split("/")[-1][:24] if r.model_permaslug in biggest else None,
        "tooltip": (f"{r.model_permaslug} · {r.archetype} · P:C {r.pc_ratio:.1f} · "
                    f"{r.tokens_per_request:,.0f} tok/req · {fmt_compact(r.month_tokens)} tokens"),
    } for r in d.itertuples()]

    by_arch = (fp.groupby("archetype")
               .agg(models=("model_permaslug", "size"), tokens=("month_tokens", "sum"),
                    median_pc=("pc_ratio", "median"), median_tpr=("tokens_per_request", "median"))
               .reset_index().sort_values("tokens", ascending=False))
    total = fp["month_tokens"].sum()
    by_arch["share"] = by_arch["tokens"] / total
    tbl = by_arch.assign(
        archetype_=by_arch["archetype"],
        models_=by_arch["models"].map("{:,}".format),
        tokens_=by_arch["tokens"].map(fmt_compact),
        share_=by_arch["share"].map("{:.1%}".format),
        pc_=by_arch["median_pc"].map(lambda v: "—" if pd.isna(v) else f"{v:.1f}"),
        tpr_=by_arch["median_tpr"].map(lambda v: "—" if pd.isna(v) else f"{v:,.0f}"),
    )

    return f"""
<h2>1 · The market splits in two, and volume hides it</h2>
<pre>pc_ratio           = prompt tokens / completion tokens   → context consumed per token produced
tokens_per_request = total tokens / requests             → size of one interaction</pre>
<p>Weighted by token volume, both axes are <strong>bimodal</strong>: modes at a
P:C of 17 and 76, and at 10k and 62k tokens per request. The dashed cuts sit at
the density minima between them, so they are measured rather than chosen.</p>
<figure>
  <div class="scroll">{charts.scatter_log_log(
      points, x_title="Prompt tokens per completion token (log)",
      y_title="Tokens per request (log)",
      vline=config.PC_RATIO_HIGH, hline=config.TPR_HIGH,
      label="Workload plane: P:C ratio against tokens per request")}</div>
  {_legend([("s1", "agentic"), ("s2", "conversational"), ("s3", "extractive"),
            (NEUTRAL, "other / unclassified")])}
  <figcaption>One dot per model-variant above 100k monthly requests; area is
  token volume. Labelled: the largest of each group. Dashed lines are the
  classification cuts.</figcaption>
</figure>
<div class="callout"><p><strong>Why one axis is not enough.</strong> The highest
P:C ratio in the whole dataset belongs to a safety classifier, not an agent — it
reads 195 tokens per token written, but its interactions average 726 tokens. A
context-hungry classifier and a coding agent look identical on that axis alone.
Only the conjunction separates them.</p></div>
{_table(tbl, [("archetype_", "Archetype"), ("models_", "Model-variants"),
              ("tokens_", "Tokens (30d)"), ("share_", "Share"),
              ("pc_", "Median P:C"), ("tpr_", "Median tok/req")],
        numeric={"models_", "tokens_", "share_", "pc_", "tpr_"})}
"""


def _economics(econ, structure):
    if econ.empty:
        return ""
    by_author = (econ.groupby("author")
                 .agg(tokens=("month_tokens", "sum"), value=("implied_gross_value", "sum"))
                 .reset_index())
    by_author["token_share"] = by_author["tokens"] / by_author["tokens"].sum()
    by_author["value_share"] = by_author["value"] / by_author["value"].sum()
    top = by_author.nlargest(9, "value_share").sort_values("value_share", ascending=False)
    rows = [{"label": r.author[:18], "left": float(r.token_share),
             "right": float(r.value_share)} for r in top.itertuples()]

    blended = econ["blended_to_sticker_ratio"].median()
    movers = econ.assign(gap=econ["value_rank"] - econ["token_rank"]).nlargest(6, "gap")
    mv = movers.assign(
        m_=movers["model_permaslug"].str.slice(0, 44),
        t_=movers["token_rank"].map("#{:,.0f}".format),
        v_=movers["value_rank"].map("#{:,.0f}".format),
        ts_=movers["token_share"].map("{:.2%}".format),
        vs_=movers["value_share"].map("{:.3%}".format),
    )

    def row(measure, segment="all"):
        s = structure[(structure["measure"] == measure) & (structure["segment"] == segment)]
        return s.iloc[0] if len(s) else None

    t_all, v_all = row("tokens"), row("implied_value")
    conc = pd.DataFrame([
        {"k": "Tokens, by model", "hhi": t_all["hhi"], "gini": t_all["gini"],
         "t1": t_all["top1_share"], "t10": t_all["top10_share"]},
        {"k": "Implied value, by model", "hhi": v_all["hhi"], "gini": v_all["gini"],
         "t1": v_all["top1_share"], "t10": v_all["top10_share"]},
        {"k": "Tokens, by lab", **{c: row("tokens_by_author")[c2] for c, c2 in
         (("hhi", "hhi"), ("gini", "gini"), ("t1", "top1_share"), ("t10", "top10_share"))}},
        {"k": "Implied value, by lab", **{c: row("implied_value_by_author")[c2] for c, c2 in
         (("hhi", "hhi"), ("gini", "gini"), ("t1", "top1_share"), ("t10", "top10_share"))}},
    ])
    ct = conc.assign(k_=conc["k"], hhi_=conc["hhi"].map("{:,.0f}".format),
                     gini_=conc["gini"].map("{:.3f}".format),
                     t1_=conc["t1"].map("{:.1%}".format),
                     t10_=conc["t10"].map("{:.1%}".format))

    return f"""
<h2>2 · Attention and money part company between the labs</h2>
<p>Multiplying each model's tokens by its list price gives the gross value its
traffic represents. It is <em>not</em> revenue — it ignores cache discounts,
batch rates, BYOK and negotiated pricing — so it is an upper bound, and named
<code>implied_gross_value</code> everywhere so nobody forgets.</p>
<figure>
  <div class="scroll">{charts.paired_bars(
      rows, left_title="share of tokens", right_title="share of implied value",
      label="Token share against value share, by lab")}</div>
  <figcaption>The nine labs with the largest share of implied value. Bars are
  mirrored around the label so the gap between the two measures is the thing
  you see first.</figcaption>
</figure>
{_table(ct, [("k_", "Concentration of…"), ("hhi_", "HHI"), ("gini_", "Gini"),
             ("t1_", "Top 1"), ("t10_", "Top 10")],
        numeric={"hhi_", "gini_", "t1_", "t10_"})}
<p>By tokens, the labs look moderately concentrated. By money they cross
<strong>2,500 HHI</strong> — the threshold competition authorities call highly
concentrated — and a single lab takes
<strong>{_pct(row('implied_value_by_author')['top1_share'], 0)}</strong> of it
against {_pct(row('tokens_by_author')['top1_share'], 0)} of the tokens.</p>

<h3>The sticker price is not the price</h3>
<p>Traffic is overwhelmingly prompt-heavy, and prompt tokens are cheaper than
completions. So the price a buyer actually pays per token, blended across their
real mix, sits at a median of
<strong>{blended:.2f}×</strong> the headline output price — the sticker
overstates the true unit cost by about <strong>{1 / blended:.1f}×</strong>.</p>
{_table(mv, [("m_", "Model"), ("t_", "Rank by tokens"), ("v_", "Rank by value"),
             ("ts_", "Token share"), ("vs_", "Value share")],
        numeric={"t_", "v_", "ts_", "vs_"})}
<figcaption>The models whose standing collapses when ranked by money instead of
volume: high-volume, near-free weights.</figcaption>
"""


def _context(ctx):
    if ctx.empty:
        return ""
    # 'unclassified' is the absence of a classification, not a workload; a bar
    # at 0.00% next to the real ones invites reading it as a finding.
    by_arch = (ctx[ctx["archetype"] != "unclassified"]
               .groupby("archetype")["mean_window_utilisation"]
               .median().dropna().sort_values(ascending=False).reset_index())
    rows = [{"label": r.archetype, "value": float(r.mean_window_utilisation),
             "colour": ARCHETYPE_COLOUR.get(r.archetype, NEUTRAL)}
            for r in by_arch.itertuples()]
    weighted = np.average(
        ctx["mean_window_utilisation"].fillna(0),
        weights=ctx["month_tokens"].clip(lower=0),
    )
    return f"""
<h2>3 · The context window arms race is mostly unused</h2>
<p>Vendors compete hard on advertised context length. Dividing the mean tokens
per request by the advertised window asks how much of it the traffic touches.</p>
<figure>
  <div class="scroll">{charts.hbar(
      rows, value_fmt=lambda v: f"{v:.2%}",
      label="Median share of the advertised context window actually used")}</div>
  <figcaption>Median across models in each group. Token-weighted across the
  whole market: {weighted:.2%}.</figcaption>
</figure>
<p>Even agentic traffic — the workload that exists because of long context —
uses under a tenth of what it is sold. The caveat is real and cuts one way:
tokens per request is a <em>mean</em>, so a model that occasionally fills a
million-token window and usually does not still reads low here. This bounds
typical usage, not peak capability.</p>
"""


def _competition(comp, scoreboard, pp):
    if comp.empty:
        return ""
    multi = comp[comp["n_endpoints"] > 1]
    spread = multi.nlargest(6, "price_spread_ratio")
    st = spread.assign(
        m_=spread["model_permaslug"].str.slice(0, 40),
        n_=spread["n_providers"].map("{:,.0f}".format),
        s_=spread["price_spread_ratio"].map("{:.1f}×".format),
        lo_=(spread["min_price_completion"] * 1e6).map("${:,.2f}".format),
        hi_=(spread["max_price_completion"] * 1e6).map("${:,.2f}".format),
    )
    dominated = pp["is_dominated"].mean() if not pp.empty else float("nan")
    top_prov = scoreboard.nlargest(8, "window_requests") if not scoreboard.empty else pd.DataFrame()
    pt = top_prov.assign(
        p_=top_prov["provider_name"],
        m_=top_prov["n_models"].map("{:,.0f}".format),
        thr_=top_prov["median_throughput"].map(lambda v: "—" if pd.isna(v) else f"{v:,.0f}"),
        jit_=top_prov["jitter_index"].map(lambda v: "—" if pd.isna(v) else f"{v:.1f}×"),
        pp_=top_prov["median_price_percentile"].map(
            lambda v: "—" if pd.isna(v) else f"{v:.0%}"),
    ) if not top_prov.empty else pd.DataFrame()

    return f"""
<h2>4 · The serving layer is where the arbitrage is</h2>
<div class="tiles">
  {_tile(f"{len(multi):,}", "models with >1 provider")}
  {_tile(f"{multi['provider_hhi'].median():,.0f}", "median provider HHI")}
  {_tile(_pct(dominated, 0), "endpoints Pareto-dominated")}
  {_tile(f"{comp['jitter_index'].median():.1f}×", "median p99 / p50 latency")}
</div>
<p>Where more than one provider serves the same model, the median HHI is still
above 5,000 — competition exists on paper more than in traffic. And the price of
the identical model varies by up to an order of magnitude.</p>
{_table(st, [("m_", "Model"), ("n_", "Providers"), ("s_", "Price spread"),
             ("lo_", "Cheapest /M out"), ("hi_", "Dearest /M out")],
        numeric={"n_", "s_", "lo_", "hi_"})}
<p>An endpoint is <em>dominated</em> when another serving the same model is both
cheaper and faster at the median. The jitter index — p99 over p50 latency —
measures consistency rather than speed: a provider can be quick on average and
still miss deadlines.</p>
{_table(pt, [("p_", "Provider"), ("m_", "Models"), ("thr_", "Median tok/s"),
             ("jit_", "Jitter"), ("pp_", "Price percentile")],
        numeric={"m_", "thr_", "jit_", "pp_"}) if not pt.empty else ""}
<figcaption>Busiest providers by requests observed in the sampling window. Price
percentile is their typical standing among everyone serving the same model:
0% is cheapest.</figcaption>
<div class="callout"><p><strong>Caveat that constrains all of section 4.</strong>
These percentiles come from a 30-minute rolling window, so a daily capture
samples half an hour, not the day. The dominance share is stable at 53–55% for
any volume floor between 0 and 1,000 requests, which is reassuring — but a
single capture indicates where to look, it does not settle anything.</p></div>
"""


def _elasticity(el):
    if el.empty:
        return ""
    rows = []
    for r in el.sort_values(["weighting", "segment"]).itertuples():
        rows.append({
            "label": f"{r.segment} · {'weighted' if r.weighting == 'request_weighted' else 'unweighted'}",
            "value": float(r.elasticity), "lo": float(r.ci_low), "hi": float(r.ci_high),
            "n": int(r.n), "significant": bool(r.significant_at_95),
        })
    agentic = el[(el["segment"] == "agentic") & (el["weighting"] == "request_weighted")]
    a = agentic.iloc[0] if len(agentic) else None

    return f"""
<h2>5 · Price response, and where it hides</h2>
<p>Regressing log tokens on log price, with heteroskedasticity-robust standard
errors. Two weightings: unweighted treats every model as one observation;
request-weighted follows where the traffic actually is.</p>
<figure>
  <div class="scroll">{charts.forest(
      rows, x_title="elasticity (Δ log tokens / Δ log price), 95% CI",
      label="Price elasticity by archetype and weighting")}</div>
  {_legend([("s1", "significant at 95%"), (NEUTRAL, "not distinguishable from zero")])}
  <figcaption>Point estimate with its 95% interval. Coloured where the interval
  excludes zero.</figcaption>
</figure>
{f'''<p>The interesting result is the reversal in agentic traffic. Counting
models equally, price explains nothing. Weighting by requests, the elasticity is
<strong>{a.elasticity:+.2f}</strong> ({a.ci_low:+.2f} to {a.ci_high:+.2f}) and
clears zero comfortably. Agentic <em>models</em> are not price-sensitive; agentic
<em>volume</em> is. That is the signature of a small number of very large
consumers optimising unit cost hard.</p>''' if a is not None else ""}
<div class="callout"><p><strong>This is not a causal elasticity.</strong> It is a
cross-section of different models at different prices, not one model observed at
several prices, so it absorbs everything that makes cheap models cheap — smaller,
weaker, newer. A steep slope is as consistent with "buyers chase cheap tokens" as
with "cheap models are the ones built for bulk work". The comparison
<em>between</em> archetypes carries more than any single coefficient.</p></div>
"""


def _survival(curve, sens):
    if curve.empty:
        return ""
    steps = [{"x": float(r.day), "y": float(r.survival),
              "lo": float(r.ci_low), "hi": float(r.ci_high)}
             for r in curve.itertuples()]
    # Truncate the axis just below the confidence band so the trajectory is
    # visible, and say so in the caption. Capped at 0.9 so the reader always
    # keeps at least a tenth of the full scale for context.
    depth = min([s["lo"] for s in steps if np.isfinite(s["lo"])] +
                [s["y"] for s in steps])
    y_floor = min(0.9, np.floor(depth * 20) / 20)
    censors = [{"x": float(r.day), "y": float(r.survival)}
               for r in curve.itertuples() if r.censored > 0]
    s = sens.assign(
        th_=sens["threshold_days"].map("≥{:,.0f} days silent".format),
        ev_=sens["n_events"].map("{:,.0f}".format),
        ce_=sens["n_censored"].map("{:,.0f}".format),
        s180_=sens["survival_at_180d"].map("{:.1%}".format),
        s365_=sens["survival_at_365d"].map("{:.1%}".format),
    )
    return f"""
<h2>6 · How long does a model live? (preliminary)</h2>
<p>Kaplan-Meier with right-censoring. Most models are still running, so their
lifetime is only known to be <em>at least</em> their current age — dropping them
would bias the curve towards short lives, and counting their age as a lifetime
would bias it the other way. The product-limit estimator uses exactly what each
subject carries.</p>
<figure>
  <div class="scroll">{charts.step_band(
      steps, x_title="days since the model launched", y_title="still active",
      censor_marks=censors, y_floor=y_floor,
      label="Kaplan-Meier survival curve for model lifetime")}</div>
  <figcaption><strong>The vertical axis starts at {y_floor:.0%}, not zero</strong>
  — the curve never falls below {depth:.1%}, and on a full scale it would be a
  flat line against nine-tenths of empty space. Step function with its 95% band
  via the log-log transform, which keeps the interval inside 0–100%. Ticks mark
  censoring.</figcaption>
</figure>
{_table(s, [("th_", "Death defined as"), ("ev_", "Events"), ("ce_", "Censored"),
            ("s180_", "Alive at 180d"), ("s365_", "Alive at 365d")],
        numeric={"ev_", "ce_", "s180_", "s365_"})}
<div class="callout"><p><strong>Why this is labelled preliminary.</strong> Death
is inferred from the last day with traffic, and two biases pull against each
other. A model silent for more than about 30 days leaves the monthly window
entirely, so long-dead models are absent and survival is biased <em>up</em> —
the giveaway is in the table above, where a 14-day threshold finds almost no
events at all, which is a property of the feed and not of the market. Meanwhile a
2-day threshold books a model that merely had a quiet Tuesday as dead, biasing
<em>down</em>. Their relative sizes are unknown.</p>
<p>What fixes it costs nothing but time: once the archive holds several weeks of
captures, death is <em>observed</em> — present on day N, absent on day N+k —
rather than inferred from a truncated field. The estimator does not change; its
input stops being biased. This is the clearest case in the project of a metric
that only a growing archive can make real.</p></div>
"""


def _variants(var):
    if var.empty:
        return ""
    free = var[var["free_token_share"] > 0]
    if free.empty:
        return ""
    return f"""
<h2>7 · Free tiers are substitutes, not funnels</h2>
<div class="tiles">
  {_tile(f"{len(free):,}", "models with a free variant")}
  {_tile(_pct(free['free_token_share'].median(), 0), "median tokens that never bill")}
  {_tile(f"{free['free_to_paid_intensity'].median():.2f}×", "free vs paid interaction size")}
</div>
<p>For models shipping both tiers, the free variant carries a median
{_pct(free['free_token_share'].median(), 0)} of the tokens — and its
interactions are <em>larger</em> than the paid tier's, not smaller. A funnel
would look the opposite: small free trials graduating into heavy paid usage.
This looks like substitution.</p>
"""


def _health(marts):
    results = quality.run_all(marts)
    def card(r):
        if r.passed:
            cls, word = "", "pass"
        elif r.severity == quality.ERROR:
            cls, word = "bad", "fail"
        else:
            cls, word = "warn", "warn"
        return (f'<div class="check {cls}">'
                f'<b><span class="pill {cls}">{word}</span>{esc(r.name)}</b>'
                f'<span class="muted">{esc(r.detail)}</span></div>')

    cards = "".join(card(r) for r in results)
    rows = []
    for d in ingest.list_snapshots():
        try:
            m = ingest.load_manifest(d)
        except (OSError, ValueError):
            continue
        rows.append(f"<tr><td>{esc(d)}</td><td class='num'>{m['requests_ok']}</td>"
                    f"<td class='num'>{m['requests_failed']}</td>"
                    f"<td class='num'>{m['bytes_received'] / 1e6:.1f} MB</td>"
                    f"<td class='num'>{m.get('duration_seconds', 0):.0f}s</td></tr>")
    return f"""
<h2>8 · The pipeline's own vitals</h2>
<p>A dashboard that cannot say whether its data is current is a liability.</p>
<div class="checks">{cards}</div>
<details><summary>Capture manifests — every gap in the series has a recorded cause</summary>
<div class="scroll"><table><thead><tr><th>Snapshot</th><th class="num">Requests OK</th>
<th class="num">Failed</th><th class="num">Volume</th><th class="num">Duration</th>
</tr></thead><tbody>{''.join(rows)}</tbody></table></div></details>
"""


def _limits():
    return """
<h2>What this cannot tell you</h2>
<p>Stating the limits is part of the result.</p>
<ul>
<li><strong>No public history exists.</strong> The rankings feed returns trailing
aggregates, and its <code>date</code> column is the model's last day with
traffic, not a time index. Grouping by it produces a convincing and entirely
false chart. Every series here starts on the day of the first capture.</li>
<li><strong>Implied value is not revenue.</strong> List price × tokens, ignoring
cache discounts, batch pricing, BYOK and negotiated rates. An upper bound.</li>
<li><strong>Endpoint percentiles are a 30-minute sample</strong>, not a daily
aggregate.</li>
<li><strong>Four schema fields are dormant</strong> — cache, reasoning and
tool-call counters are present but zero for every model. Nothing is built on
them; a contract test watches for them waking up.</li>
<li><strong>Traffic is not users.</strong> One agentic application can outproduce
a million chat sessions. Nothing here measures adoption or satisfaction.</li>
<li><strong>Archetype cuts are frozen, not re-fitted.</strong> Boundary models
will flip between captures; that is measured rather than assumed away.</li>
</ul>
"""


# --- entry point -----------------------------------------------------------


TITLE = "OpenRouter Pulse — what the LLM market is actually doing"
DESCRIPTION = ("What the LLM market is actually doing, derived from OpenRouter's "
               "public data.")


def content(marts: dict[str, pd.DataFrame]) -> str:
    """The page body: everything between the wrapper and the data."""
    fp_all = marts["mart_model_fingerprint"]
    snapshot = fp_all["snapshot_date"].max()
    fp = fp_all[fp_all["snapshot_date"] == snapshot]

    def latest(name):
        df = marts.get(name, pd.DataFrame())
        if df.empty or "snapshot_date" not in df.columns:
            return df
        return df[df["snapshot_date"] == df["snapshot_date"].max()]

    econ = latest("mart_model_economics")
    structure = latest("mart_market_structure")
    body = "".join([
        _hero(fp, econ, structure),
        _workload_plane(fp),
        _economics(econ, structure),
        _context(latest("mart_context_utilization")),
        _competition(latest("mart_provider_competition"),
                     latest("mart_provider_scoreboard"),
                     latest("mart_endpoint_price_perf")),
        _elasticity(latest("mart_price_elasticity")),
        _survival(latest("mart_model_survival"), latest("mart_survival_sensitivity")),
        _variants(latest("mart_variant_economics")),
        _health(marts),
        _limits(),
        f"""<hr><p><small>Snapshot <code>{esc(snapshot)}</code>. Every figure on
this page is read from <code>data/marts/</code> — none is typed by hand, and the
page is regenerated from the data on every build. Method and derivations in
METHODOLOGY.md.<br>Built against OpenRouter's public API by an independent
analyst. Not affiliated with OpenRouter.</small></p>""",
    ])
    return f"<div class='wrap'>{body}</div>"


def build(marts: dict[str, pd.DataFrame]) -> str:
    """Body-only form: title, styles and content, no document skeleton.

    This is what a host that supplies its own `<!doctype>`/`<head>`/`<body>`
    wrapper needs. `standalone()` is the same content in a real document.
    Generating one and hand-editing the other would guarantee they drift, so
    both come from `content()`.
    """
    return f"<title>{esc(TITLE)}</title><style>{STYLE}</style>{content(marts)}"


def standalone(marts: dict[str, pd.DataFrame]) -> str:
    """A complete document, for opening from disk or serving as a static file."""
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<meta name="description" content="{esc(DESCRIPTION)}">'
        f"<title>{esc(TITLE)}</title><style>{STYLE}</style></head>"
        f"<body>{content(marts)}</body></html>"
    )


def write(marts: dict[str, pd.DataFrame] | None = None, path: Path | None = None) -> Path:
    marts = marts if marts is not None else load_marts()
    if "mart_model_fingerprint" not in marts:
        raise RuntimeError("no marts found; run `make build` first")
    path = path or (config.DOCS_DIR / "dashboard.html")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(standalone(marts))
    return path


def write_fragment(marts: dict[str, pd.DataFrame] | None = None,
                   path: Path | None = None) -> Path:
    """The body-only form, for a host that wraps it in its own skeleton."""
    marts = marts if marts is not None else load_marts()
    path = path or (config.DOCS_DIR / "dashboard.fragment.html")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build(marts))
    return path
