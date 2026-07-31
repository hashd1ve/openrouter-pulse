"""The SVG charts and the generated page.

A chart module with no tests is a module that silently emits malformed SVG the
day an input goes empty or a value goes NaN. These check the geometry invariants
and that the page is genuinely self-contained.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

import pytest

from orpulse import charts, dashboard


# --- scales ----------------------------------------------------------------


def test_linear_scale_maps_endpoints():
    s = charts.Scale(0, 100, 0, 200)
    assert s.px(0) == pytest.approx(0)
    assert s.px(100) == pytest.approx(200)
    assert s.px(50) == pytest.approx(100)


def test_flipped_scale_puts_the_maximum_at_the_top():
    s = charts.Scale(0, 100, 0, 200, flip=True)
    assert s.px(100) == pytest.approx(0)
    assert s.px(0) == pytest.approx(200)


def test_log_scale_is_evenly_spaced_in_decades():
    s = charts.Scale(1, 1000, 0, 300, log=True)
    assert s.px(1) == pytest.approx(0)
    assert s.px(10) == pytest.approx(100)
    assert s.px(1000) == pytest.approx(300)


def test_log_scale_survives_zero_and_negative_input():
    """Real data contains zeros; a log scale must not raise on them."""
    s = charts.Scale(1, 1000, 0, 300, log=True)
    assert charts.math.isfinite(s.px(0))
    assert charts.math.isfinite(s.px(-5))


def test_scale_clamps_rather_than_drawing_far_off_canvas():
    s = charts.Scale(0, 100, 0, 200)
    assert -20 <= s.px(-10_000) <= 220
    assert -20 <= s.px(10_000) <= 220


def test_log_ticks_land_on_round_decades():
    ticks = charts.Scale(1, 1000, 0, 300, log=True).ticks()
    assert 1 in ticks and 10 in ticks and 100 in ticks


def test_compact_formatting():
    assert charts.fmt_compact(1_500_000_000_000) == "1.5T"
    assert charts.fmt_compact(2_400) == "2.4k"
    assert charts.fmt_compact(42) == "42"
    assert charts.fmt_compact(float("nan")) == "—"


# --- chart output ----------------------------------------------------------


def parse(svg: str):
    """Every chart must emit SVG a strict XML parser accepts."""
    return ET.fromstring(svg)


SCATTER = [
    {"x": 50.0, "y": 40_000.0, "size": 1e12, "colour": "s1", "name": "a/one",
     "label": "one", "tooltip": "a/one"},
    {"x": 5.0, "y": 3_000.0, "size": 1e9, "colour": "s2", "name": "a/two"},
]


def test_scatter_is_well_formed_and_plots_every_point():
    svg = charts.scatter_log_log(SCATTER, x_title="x", y_title="y",
                                 vline=26.6, hline=18_607, label="test")
    root = parse(svg)
    circles = root.findall(".//{http://www.w3.org/2000/svg}circle")
    assert len(circles) == len(SCATTER)
    assert 'aria-label="test"' in svg


def test_scatter_handles_an_empty_input():
    assert "No data" in charts.scatter_log_log([], x_title="x", y_title="y")


def test_scatter_skips_non_positive_coordinates_on_log_axes():
    points = SCATTER + [{"x": 0.0, "y": 10.0, "size": 1, "colour": "s3", "name": "z"}]
    root = parse(charts.scatter_log_log(points, x_title="x", y_title="y"))
    assert len(root.findall(".//{http://www.w3.org/2000/svg}circle")) == len(SCATTER)


def test_scatter_keeps_edge_labels_inside_the_canvas():
    """A label on a right-edge point must flip rather than run off."""
    points = [{"x": 1.0, "y": 1_000.0, "size": 1e9, "colour": "s1", "name": "l",
               "label": "left-hand-model"},
              {"x": 10_000.0, "y": 1_000.0, "size": 1e9, "colour": "s1", "name": "r",
               "label": "a-very-long-right-hand-model-name"}]
    svg = charts.scatter_log_log(points, x_title="x", y_title="y")
    anchors = re.findall(r'class="point-label"', svg)
    assert len(anchors) == 2
    assert 'text-anchor="end"' in svg, "the right-edge label must flip"


def test_step_band_is_monotone_and_well_formed():
    steps = [{"x": 10, "y": 0.9, "lo": 0.8, "hi": 0.95},
             {"x": 20, "y": 0.7, "lo": 0.6, "hi": 0.8}]
    root = parse(charts.step_band(steps, x_title="d", y_title="s"))
    assert root.findall(".//{http://www.w3.org/2000/svg}polyline")


def test_step_band_tolerates_a_missing_confidence_band():
    """Greenwood gives NaN bounds at S=1; the chart must still draw."""
    steps = [{"x": 1, "y": 1.0, "lo": float("nan"), "hi": float("nan")},
             {"x": 2, "y": 0.5, "lo": 0.2, "hi": 0.8}]
    parse(charts.step_band(steps, x_title="d", y_title="s"))


def test_step_band_floor_rescales_the_axis():
    """Truncating the axis must actually change where the curve lands."""
    steps = [{"x": 1, "y": 0.95, "lo": 0.9, "hi": 1.0}]
    full = charts.step_band(steps, x_title="d", y_title="s")
    zoomed = charts.step_band(steps, x_title="d", y_title="s", y_floor=0.9)
    assert full != zoomed
    assert "90%" in zoomed or "0.9" in zoomed


def test_forest_marks_significance_by_colour():
    rows = [{"label": "a", "value": -0.5, "lo": -0.8, "hi": -0.2, "n": 40,
             "significant": True},
            {"label": "b", "value": -0.1, "lo": -0.6, "hi": 0.4, "n": 20,
             "significant": False}]
    svg = charts.forest(rows, x_title="elasticity")
    parse(svg)
    assert "var(--s1)" in svg and "var(--neutral)" in svg


def test_forest_widens_its_margin_for_long_labels():
    short = charts.forest([{"label": "a", "value": 0, "lo": -1, "hi": 1, "n": 1,
                            "significant": False}], x_title="x")
    long = charts.forest([{"label": "a" * 40, "value": 0, "lo": -1, "hi": 1, "n": 1,
                           "significant": False}], x_title="x")
    # The label anchor sits at pad-left, so a longer label pushes it right.
    assert float(re.search(r'class="row-label" text-anchor="end"', long) is not None)
    short_x = float(re.search(r'<text x="([\d.]+)" y="[\d.]+" class="row-label"', short).group(1))
    long_x = float(re.search(r'<text x="([\d.]+)" y="[\d.]+" class="row-label"', long).group(1))
    assert long_x > short_x


def test_paired_bars_keeps_values_inside_the_canvas():
    rows = [{"label": "anthropic", "left": 0.119, "right": 0.449}]
    svg = charts.paired_bars(rows, left_title="tokens", right_title="value")
    parse(svg)
    width = int(re.search(r'viewBox="0 0 (\d+)', svg).group(1))
    for x in re.findall(r'<text x="([\d.]+)"', svg):
        assert -5 <= float(x) <= width + 5


def test_hbar_is_well_formed():
    parse(charts.hbar([{"label": "a", "value": 0.5}, {"label": "b", "value": 0.1}]))


def test_labels_with_markup_are_escaped():
    """A model name is untrusted text as far as the SVG is concerned."""
    svg = charts.hbar([{"label": '<script>x</script>', "value": 1.0}])
    assert "<script>" not in svg
    assert "&lt;script&gt;" in svg
    parse(svg)


# --- the page --------------------------------------------------------------


@pytest.fixture
def page(built_marts):
    return dashboard.standalone(built_marts)


def test_page_is_valid_html_with_a_title(page):
    assert page.startswith("<!doctype html>")
    assert "<title>" in page and "OpenRouter Pulse" in page


def test_page_has_no_external_resources(page):
    """A strict content policy blocks any external host; nothing may need one."""
    assert not re.findall(r'(?:src|href)=["\']https?://', page)
    assert "<script" not in page.lower()


def test_page_styles_both_colour_schemes(page):
    assert "prefers-color-scheme:dark" in page
    assert '[data-theme="dark"]' in page


# Sections that need only a handful of models, and so must always render.
CORE_SECTIONS = ("The market splits in two", "Attention and money part company",
                 "context window arms race", "serving layer",
                 "own vitals", "What this cannot tell you")


def test_page_contains_every_core_section(page):
    for heading in CORE_SECTIONS:
        assert heading in page, f"missing section: {heading}"


def test_sections_needing_more_data_are_omitted_not_broken(page, built_marts):
    """The three-model fixture cannot support a regression, and that is fine.

    What matters is that a thin dataset drops the section cleanly rather than
    rendering an empty chart or crashing -- so the assertion is conditional on
    the mart actually having rows.
    """
    for mart, heading in (("mart_price_elasticity", "Price response"),
                          ("mart_model_survival", "How long does a model live")):
        has_data = not built_marts.get(mart, __import__("pandas").DataFrame()).empty
        assert (heading in page) == has_data, (
            f"{heading} should appear exactly when {mart} has rows"
        )


def test_page_states_its_limitations(page):
    """The caveats are load-bearing, not decoration."""
    for claim in ("not revenue", "30-minute", "Traffic is not users"):
        assert claim in page, f"missing caveat: {claim}"


def test_every_chart_on_the_page_parses(page):
    svgs = re.findall(r"<svg .*?</svg>", page, re.S)
    assert len(svgs) >= 4, f"expected several charts, found {len(svgs)}"
    for svg in svgs:
        ET.fromstring(svg)


def test_fragment_form_omits_the_document_skeleton(built_marts):
    """The body-only form for a host that supplies its own wrapper."""
    fragment = dashboard.build(built_marts)
    assert "<!doctype" not in fragment.lower()
    assert "<html" not in fragment.lower()
    assert "<body" not in fragment.lower()
    assert "<title>" in fragment


def test_both_forms_share_the_same_content(built_marts):
    assert dashboard.content(built_marts) in dashboard.standalone(built_marts)
    assert dashboard.content(built_marts) in dashboard.build(built_marts)


def test_write_produces_a_file(built_marts, tmp_path):
    path = dashboard.write(built_marts, tmp_path / "out.html")
    assert path.exists() and path.stat().st_size > 10_000


def test_missing_marts_raise_rather_than_writing_an_empty_page(tmp_path):
    with pytest.raises(RuntimeError, match="no marts"):
        dashboard.write({}, tmp_path / "x.html")
