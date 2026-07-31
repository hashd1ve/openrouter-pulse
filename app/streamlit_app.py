"""Exploration dashboard over the marts.

Chart decisions worth knowing about:

* The headline scatter is an all-pairs form, so the categorical palette caps at
  three hues. There are four archetypes, so the two residual ones (0.9% of
  tokens between them) fold into a neutral "other" rather than seating a fourth
  hue that would fail colourblind separation.
* Palette validated with the dataviz validator in both modes. Light mode warns
  on aqua contrast (2.74:1), so the relief rule applies: direct labels on the
  chart and a table view of the same data are both present, never colour alone.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from orpulse import config, ingest, quality, transform  # noqa: E402

st.set_page_config(page_title="OpenRouter Pulse", page_icon="◐", layout="wide")

# --- palette ---------------------------------------------------------------
# Validated categorical slots 1-3 plus a neutral for the folded tail.
LIGHT = {"surface": "#fcfcfb", "text": "#0b0b0b", "muted": "#52514e",
         "s1": "#2a78d6", "s2": "#eb6834", "s3": "#1baf7a", "other": "#8a8a85"}
DARK = {"surface": "#1a1a19", "text": "#ffffff", "muted": "#c3c2b7",
        "s1": "#3987e5", "s2": "#d95926", "s3": "#199e70", "other": "#77776f"}

ARCHETYPE_ORDER = ["agentic", "conversational", "extractive", "other"]


def theme() -> dict:
    try:
        return DARK if st.context.theme.type == "dark" else LIGHT
    except Exception:
        return LIGHT


C = theme()
SCALE = alt.Scale(
    domain=ARCHETYPE_ORDER, range=[C["s1"], C["s2"], C["s3"], C["other"]]
)


def axis(title: str, **kw):
    return alt.Axis(
        title=title, grid=True, gridColor=C["muted"], gridOpacity=0.15,
        domainColor=C["muted"], domainOpacity=0.4, tickColor=C["muted"],
        labelColor=C["muted"], titleColor=C["muted"], **kw
    )


def style(chart: alt.Chart) -> alt.Chart:
    return chart.configure_view(strokeWidth=0).configure_legend(
        labelColor=C["text"], titleColor=C["muted"], symbolStrokeWidth=0
    ).properties(background="transparent")


# --- data ------------------------------------------------------------------


@st.cache_data(show_spinner="Loading marts…")
def load():
    marts = transform.load_marts()
    if not marts:
        return None
    return marts


marts = load()
if not marts or "mart_model_fingerprint" not in marts:
    st.error("No marts found. Run `make ingest && make build` first.")
    st.stop()

fp_all = marts["mart_model_fingerprint"]
snapshots = sorted(fp_all["snapshot_date"].unique())

st.title("OpenRouter Pulse")
st.caption(
    "What kind of work the LLM market is actually doing, derived from "
    "OpenRouter's public data. One capture per day; the archive is the only "
    "time series that exists for this feed."
)

with st.sidebar:
    st.subheader("Capture")
    chosen = st.selectbox("Snapshot", snapshots, index=len(snapshots) - 1)
    st.caption(f"{len(snapshots)} snapshot(s) in the archive")
    st.subheader("Filters")
    min_requests = st.select_slider(
        "Minimum monthly requests",
        options=[0, 10_000, 100_000, 1_000_000, 10_000_000],
        value=100_000,
        format_func=lambda v: f"{v:,}",
        help="Ratios below ~100k requests are noise rather than signal.",
    )
    show_table = st.checkbox("Show table view", value=False)

fp = fp_all[fp_all["snapshot_date"] == chosen].copy()
fp["archetype_plot"] = fp["archetype"].where(
    fp["archetype"].isin(["agentic", "conversational", "extractive"]), "other"
)
view = fp[fp["month_requests"].fillna(0) >= min_requests].copy()
plot = view.dropna(subset=["pc_ratio", "tokens_per_request"])
plot = plot[(plot["pc_ratio"] > 0) & (plot["tokens_per_request"] > 0)]

# --- headline --------------------------------------------------------------

total_tokens = fp["month_tokens"].sum()
agentic = fp[fp["archetype"] == "agentic"]
share = agentic["month_tokens"].sum() / total_tokens if total_tokens else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Agentic share of tokens", f"{share:.1%}",
          help="Share of trailing-30-day tokens from models classified as agentic.")
c2.metric("Agentic model-variants", f"{len(agentic)} / {len(fp)}")
c3.metric("Tokens (30d)", f"{total_tokens / 1e12:.1f} T")
c4.metric("Requests (30d)", f"{fp['month_requests'].sum() / 1e9:.2f} B")

st.markdown(
    f"**{len(agentic)} of {len(fp)} model-variants carry {share:.0%} of all tokens.** "
    "They are not more popular — they consume vastly more per call."
)

# --- the money chart -------------------------------------------------------

st.subheader("The workload plane")
st.caption(
    "Each point is one model-variant. Horizontal: context consumed per token "
    "produced. Vertical: size of a single interaction. Both axes log. Dashed "
    "lines are the classification cuts, placed at the minima of the "
    "token-weighted density — the distribution is genuinely bimodal on both axes."
)

base = alt.Chart(plot)
points = base.mark_circle(size=90, opacity=0.75, stroke=C["surface"], strokeWidth=2).encode(
    x=alt.X("pc_ratio:Q", scale=alt.Scale(type="log"),
            axis=axis("Prompt tokens per completion token (log)")),
    y=alt.Y("tokens_per_request:Q", scale=alt.Scale(type="log"),
            axis=axis("Tokens per request (log)")),
    size=alt.Size("month_tokens:Q", scale=alt.Scale(type="log", range=[40, 900]),
                  legend=alt.Legend(title="Tokens (30d)", format=".2s")),
    color=alt.Color("archetype_plot:N", scale=SCALE,
                    legend=alt.Legend(title="Archetype"), sort=ARCHETYPE_ORDER),
    tooltip=[
        alt.Tooltip("model_permaslug:N", title="Model"),
        alt.Tooltip("archetype:N", title="Archetype"),
        alt.Tooltip("pc_ratio:Q", title="P:C ratio", format=".1f"),
        alt.Tooltip("tokens_per_request:Q", title="Tokens/request", format=",.0f"),
        alt.Tooltip("month_tokens:Q", title="Tokens (30d)", format=",.0f"),
        alt.Tooltip("momentum:Q", title="Momentum", format=".2f"),
    ],
)

# Direct labels: identity never rests on colour alone. The largest model of
# each archetype rather than the largest overall -- the top 8 by volume all sit
# in the same corner and their labels collide into an unreadable pile.
labelled = (
    plot.sort_values("month_tokens", ascending=False)
    .groupby("archetype_plot", as_index=False)
    .head(1)
    .assign(short_name=lambda d: d["model_permaslug"].str.split("/").str[-1].str.slice(0, 24))
)
labels = alt.Chart(labelled).mark_text(
    align="left", dx=10, dy=-6, fontSize=11, color=C["text"]
).encode(
    x=alt.X("pc_ratio:Q", scale=alt.Scale(type="log")),
    y=alt.Y("tokens_per_request:Q", scale=alt.Scale(type="log")),
    text=alt.Text("short_name:N"),
)

rule_x = alt.Chart(pd.DataFrame({"v": [config.PC_RATIO_HIGH]})).mark_rule(
    strokeDash=[5, 4], color=C["muted"], opacity=0.6).encode(x="v:Q")
rule_y = alt.Chart(pd.DataFrame({"v": [config.TPR_HIGH]})).mark_rule(
    strokeDash=[5, 4], color=C["muted"], opacity=0.6).encode(y="v:Q")

st.altair_chart(
    style((points + labels + rule_x + rule_y).properties(height=520).interactive()),
    use_container_width=True,
)

# --- archetype breakdown ---------------------------------------------------

st.subheader("Where the tokens are")
by_arch = (
    fp.groupby("archetype")
    .agg(models=("model_permaslug", "size"),
         tokens=("month_tokens", "sum"),
         median_pc=("pc_ratio", "median"),
         median_tpr=("tokens_per_request", "median"))
    .reset_index()
    .sort_values("tokens", ascending=False)
)
by_arch["share"] = by_arch["tokens"] / total_tokens
by_arch["archetype_plot"] = by_arch["archetype"].where(
    by_arch["archetype"].isin(["agentic", "conversational", "extractive"]), "other")

bars = alt.Chart(by_arch).mark_bar(cornerRadiusEnd=4, height=22).encode(
    x=alt.X("share:Q", axis=axis("Share of trailing-30-day tokens", format="%")),
    y=alt.Y("archetype:N", sort="-x", axis=axis(None)),
    color=alt.Color("archetype_plot:N", scale=SCALE, legend=None, sort=ARCHETYPE_ORDER),
    tooltip=[alt.Tooltip("archetype:N"), alt.Tooltip("models:Q"),
             alt.Tooltip("share:Q", format=".1%"),
             alt.Tooltip("tokens:Q", format=",.0f")],
)
bar_labels = alt.Chart(by_arch).mark_text(align="left", dx=6, fontSize=12, color=C["text"]).encode(
    x="share:Q", y=alt.Y("archetype:N", sort="-x"), text=alt.Text("share:Q", format=".1%")
)
st.altair_chart(style((bars + bar_labels).properties(height=180)), use_container_width=True)

st.dataframe(
    by_arch[["archetype", "models", "tokens", "share", "median_pc", "median_tpr"]],
    column_config={
        "tokens": st.column_config.NumberColumn("Tokens (30d)", format="%.3g"),
        "share": st.column_config.NumberColumn("Share", format="%.1f%%"),
        "median_pc": st.column_config.NumberColumn("Median P:C", format="%.1f"),
        "median_tpr": st.column_config.NumberColumn("Median tok/req", format="%.0f"),
    },
    hide_index=True, width='stretch',
)

# --- momentum --------------------------------------------------------------

st.subheader("Momentum")
st.caption(
    "Last day's rate against the 30-day average, with the denominator corrected "
    "for how long the model has actually existed. Models younger than "
    f"{config.MIN_DAYS_FOR_MOMENTUM} days, below "
    f"{config.MIN_MONTH_REQUESTS_FOR_MOMENTUM:,} monthly requests, or of unknown "
    "launch date are excluded rather than given a meaningless number."
)
ratable = view[view["is_ratable"] & view["momentum"].notna()].copy()
if ratable.empty:
    st.info("No ratable models at this filter setting.")
else:
    cols = ["model_permaslug", "archetype", "momentum", "month_tokens",
            "days_since_launch", "pc_ratio", "tokens_per_request"]
    a, b = st.columns(2)
    a.markdown("**Accelerating**")
    a.dataframe(ratable.nlargest(10, "momentum")[cols], hide_index=True,
                width='stretch')
    b.markdown("**Fading**")
    b.dataframe(ratable.nsmallest(10, "momentum")[cols], hide_index=True,
                width='stretch')

# --- endpoints -------------------------------------------------------------

pp = marts.get("mart_endpoint_price_perf", pd.DataFrame())
if not pp.empty:
    st.subheader("Provider endpoints: cost against speed")
    st.caption(
        "An endpoint is dominated when another endpoint for the same model is "
        "both cheaper per completion token and faster at the median. "
        "Percentiles come from a 30-minute rolling window, so one capture is a "
        "sample of half an hour — suggestive, not conclusive."
    )
    dom = pp.copy()
    dom["status"] = dom["is_dominated"].map({True: "dominated", False: "on the frontier"})
    scatter = alt.Chart(dom[dom["price_completion"] > 0]).mark_circle(
        size=70, opacity=0.7, stroke=C["surface"], strokeWidth=2
    ).encode(
        x=alt.X("price_completion:Q", scale=alt.Scale(type="log"),
                axis=axis("$ per completion token (log)")),
        y=alt.Y("p50_throughput:Q", axis=axis("p50 throughput (tokens/s)")),
        color=alt.Color("status:N",
                        scale=alt.Scale(domain=["on the frontier", "dominated"],
                                        range=[C["s1"], C["other"]]),
                        legend=alt.Legend(title=None)),
        tooltip=[alt.Tooltip("model_permaslug:N", title="Model"),
                 alt.Tooltip("provider_name:N", title="Provider"),
                 alt.Tooltip("price_completion:Q", title="$/token", format=".3g"),
                 alt.Tooltip("p50_throughput:Q", title="p50 tok/s"),
                 alt.Tooltip("stat_request_count:Q", title="Requests in window", format=",")],
    ).properties(height=380)
    st.altair_chart(style(scatter.interactive()), use_container_width=True)
    st.metric("Endpoints dominated", f"{dom['is_dominated'].mean():.1%}",
              help=f"{int(dom['is_dominated'].sum())} of {len(dom)} compared endpoints")

# --- data health -----------------------------------------------------------

st.subheader("Data health")
st.caption(
    "The pipeline's own vital signs. A dashboard that cannot tell you whether "
    "its data is current is a liability."
)
results = quality.run_all(marts)
hc = st.columns(min(len(results), 4))
for i, r in enumerate(results):
    icon = "✅" if r.passed else ("❌" if r.severity == quality.ERROR else "⚠️")
    hc[i % len(hc)].markdown(f"{icon} **{r.name}**  \n<small>{r.detail}</small>",
                             unsafe_allow_html=True)

with st.expander("Capture manifests"):
    rows = []
    for d in ingest.list_snapshots():
        try:
            m = ingest.load_manifest(d)
        except (OSError, json.JSONDecodeError):
            continue
        rows.append({
            "snapshot": d, "requests ok": m["requests_ok"],
            "failed": m["requests_failed"], "MB": round(m["bytes_received"] / 1e6, 1),
            "seconds": m.get("duration_seconds"),
        })
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, width='stretch')
        st.caption(
            "Every gap in the series has a cause recorded here. Without this, a "
            "missing day is indistinguishable from a day with no traffic."
        )

if show_table:
    st.subheader("Table view")
    st.caption("The same data as the charts above, for anyone who cannot rely on colour.")
    st.dataframe(
        view[["model_permaslug", "archetype", "pc_ratio", "tokens_per_request",
              "month_tokens", "month_requests", "momentum", "days_since_launch"]]
        .sort_values("month_tokens", ascending=False),
        hide_index=True, width='stretch',
    )
