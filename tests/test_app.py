"""The dashboard must actually render.

Streamlit swallows exceptions into the browser, so a running server proves
nothing. AppTest executes the script and surfaces what went wrong.
"""

from __future__ import annotations

from pathlib import Path

import pytest

streamlit = pytest.importorskip("streamlit", reason="app extra not installed")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"


@pytest.fixture
def app(built_marts, monkeypatch):
    """Run the app against the fixture marts rather than the real archive."""
    from orpulse import config, transform

    monkeypatch.setattr(transform, "load_marts", lambda: built_marts)
    # @st.cache_data survives between AppTest runs in one process.
    streamlit.cache_data.clear()
    at = AppTest.from_file(str(APP), default_timeout=60)
    at.run()
    return at


def test_app_renders_without_exceptions(app):
    assert not app.exception, [str(e) for e in app.exception]


def test_headline_metrics_are_present(app):
    labels = [m.label for m in app.metric]
    assert "Agentic share of tokens" in labels
    assert "Tokens (30d)" in labels


def test_charts_are_rendered(app):
    assert len(app.get("arrow_vega_lite_chart")) >= 2, "workload plane and breakdown"


def test_table_view_is_available_for_the_contrast_relief_rule(app):
    """Light-mode aqua sits below 3:1, so a non-colour view must exist."""
    checkboxes = [c.label for c in app.checkbox]
    assert "Show table view" in checkboxes


def test_data_health_panel_reports_checks(app):
    body = " ".join(m.value for m in app.markdown)
    assert "grain_unique" in body
    assert "nested_windows_consistent" in body


def test_missing_marts_shows_an_error_not_a_crash(monkeypatch):
    from orpulse import transform

    monkeypatch.setattr(transform, "load_marts", lambda: {})
    streamlit.cache_data.clear()
    at = AppTest.from_file(str(APP), default_timeout=60)
    at.run()
    assert not at.exception
    assert any("No marts found" in e.value for e in at.error)
