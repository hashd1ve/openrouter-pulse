"""Estimators verified against closed-form or published results.

Hand-rolled statistics are only worth trusting if they reproduce a case whose
answer is known independently. The Kaplan-Meier test uses the Freireich
leukemia trial (6-MP arm), whose survival curve is published in every survival
analysis textbook.
"""

from __future__ import annotations

import numpy as np
import pytest

from orpulse.analytics import (
    gini,
    herfindahl,
    kaplan_meier,
    log_log_elasticity,
    ols,
    top_n_share,
)


# --- concentration ---------------------------------------------------------


def test_hhi_of_a_monopoly_is_ten_thousand():
    assert herfindahl([100]) == pytest.approx(10_000)


def test_hhi_of_four_equal_shares():
    # Four holders at 25% each: 4 * 0.25^2 * 10000 = 2500
    assert herfindahl([1, 1, 1, 1]) == pytest.approx(2_500)


def test_hhi_is_scale_invariant():
    assert herfindahl([2, 3, 5]) == pytest.approx(herfindahl([200, 300, 500]))


def test_hhi_rejects_negative_values():
    with pytest.raises(ValueError):
        herfindahl([1, -1])


def test_gini_of_perfect_equality_is_zero():
    assert gini([5, 5, 5, 5]) == pytest.approx(0.0, abs=1e-12)


def test_gini_of_perfect_inequality():
    # One holder takes everything: G = (n-1)/n
    assert gini([0, 0, 0, 1]) == pytest.approx(0.75)


def test_gini_is_scale_invariant():
    assert gini([1, 2, 3, 4]) == pytest.approx(gini([10, 20, 30, 40]))


def test_top_n_share():
    assert top_n_share([1, 2, 3, 4], 2) == pytest.approx(7 / 10)


def test_empty_input_is_nan_not_a_crash():
    assert np.isnan(herfindahl([]))
    assert np.isnan(gini([]))


# --- Kaplan-Meier ----------------------------------------------------------

# Freireich et al. (1963), 6-MP arm, n=21. "+" marks a censored observation.
FREIREICH_TIMES = [6, 6, 6, 6, 7, 9, 10, 10, 11, 13, 16, 17, 19,
                   20, 22, 23, 25, 32, 32, 34, 35]
FREIREICH_EVENTS = [True, True, True, False, True, False, True, False, False,
                    True, True, False, False, False, True, True, False, False,
                    False, False, False]


@pytest.fixture
def freireich():
    return kaplan_meier(FREIREICH_TIMES, FREIREICH_EVENTS)


def test_kaplan_meier_reproduces_the_published_curve(freireich):
    """The canonical published values for this dataset."""
    expected = {6: 0.857, 7: 0.807, 10: 0.753, 13: 0.690,
                16: 0.627, 22: 0.538, 23: 0.448}
    for t, s in expected.items():
        assert freireich.at(t) == pytest.approx(s, abs=5e-4), f"S({t})"


def test_kaplan_meier_counts_subjects_and_events(freireich):
    assert freireich.n_subjects == 21
    assert freireich.n_events == 9


def test_kaplan_meier_median_matches_the_published_value(freireich):
    assert freireich.quantile(0.5) == pytest.approx(23)


def test_censored_observations_hold_the_curve_flat(freireich):
    """A censoring at t=9 must not drop S; only events drop it."""
    assert freireich.at(9) == pytest.approx(freireich.at(7), abs=1e-12)


def test_censoring_is_not_the_same_as_an_event():
    """Treating censored subjects as dead would understate survival badly."""
    censored = kaplan_meier([1, 2, 3], [True, False, False])
    as_events = kaplan_meier([1, 2, 3], [True, True, True])
    assert censored.at(3) > as_events.at(3)
    assert as_events.at(3) == pytest.approx(0.0)


def test_all_events_gives_the_empirical_survival_function():
    km = kaplan_meier([1, 2, 3, 4, 5], [True] * 5)
    assert km.survival == pytest.approx([0.8, 0.6, 0.4, 0.2, 0.0])


def test_confidence_band_stays_inside_zero_and_one(freireich):
    """The log-log transform is used precisely to guarantee this."""
    valid = np.isfinite(freireich.ci_low) & np.isfinite(freireich.ci_high)
    assert (freireich.ci_low[valid] >= 0).all()
    assert (freireich.ci_high[valid] <= 1).all()
    assert (freireich.ci_low[valid] <= freireich.survival[valid] + 1e-12).all()
    assert (freireich.ci_high[valid] >= freireich.survival[valid] - 1e-12).all()


def test_median_is_nan_when_the_curve_never_reaches_it():
    """Reporting the last observed time instead would understate survival."""
    km = kaplan_meier([1, 2, 3], [True, False, False])
    assert np.isnan(km.quantile(0.5))


def test_empty_survival_input():
    km = kaplan_meier([], [])
    assert km.n_subjects == 0
    assert km.at(10) == 1.0


# --- OLS -------------------------------------------------------------------


def test_ols_recovers_an_exact_linear_relationship():
    x = np.arange(10.0)
    y = 2.0 + 3.0 * x
    X = np.column_stack([np.ones(10), x])
    result = ols(X, y, ["intercept", "x"])
    assert result.coef == pytest.approx([2.0, 3.0])
    assert result.r_squared == pytest.approx(1.0)


def test_ols_hc1_matches_the_formula_computed_by_hand():
    rng = np.random.default_rng(0)
    x = rng.normal(size=40)
    y = 1.0 + 2.0 * x + rng.normal(size=40) * (1 + np.abs(x))  # heteroskedastic
    X = np.column_stack([np.ones(40), x])

    result = ols(X, y)

    n, k = X.shape
    xtx_inv = np.linalg.pinv(X.T @ X)
    beta = xtx_inv @ X.T @ y
    e = y - X @ beta
    cov = xtx_inv @ ((X * (e**2)[:, None]).T @ X) @ xtx_inv * (n / (n - k))
    assert result.se == pytest.approx(np.sqrt(np.diag(cov)))


def test_ols_refuses_an_underdetermined_system():
    with pytest.raises(ValueError):
        ols(np.ones((2, 3)), np.ones(2))


def test_confidence_interval_brackets_the_coefficient():
    rng = np.random.default_rng(1)
    x = rng.normal(size=100)
    y = 1.0 + 2.0 * x + rng.normal(size=100) * 0.1
    result = ols(np.column_stack([np.ones(100), x]), y, ["intercept", "slope"])
    lo, hi = result.ci_low[1], result.ci_high[1]
    assert lo < result.coef[1] < hi
    assert lo < 2.0 < hi


# --- elasticity ------------------------------------------------------------


def test_elasticity_recovers_a_known_exponent():
    """q = 100 * p^-1.5 must come back as a slope of -1.5."""
    p = np.linspace(1, 20, 60)
    q = 100 * p ** (-1.5)
    result = log_log_elasticity(p, q)
    assert result.coef[1] == pytest.approx(-1.5, abs=1e-9)


def test_elasticity_ignores_non_positive_and_missing_values():
    p = np.array([1.0, 2.0, 0.0, -1.0, np.nan] + list(np.linspace(3, 20, 20)))
    q = 100 * np.where(p > 0, p, 1.0) ** (-1.5)
    result = log_log_elasticity(p, q)
    assert result is not None
    assert result.n == 22


def test_elasticity_returns_none_when_there_is_too_little_data():
    assert log_log_elasticity([1, 2, 3], [3, 2, 1]) is None


def test_weighting_moves_the_fit_towards_the_heavy_observations():
    """A high-volume outlier should pull a weighted fit and not an unweighted one."""
    p = np.linspace(1, 20, 40)
    q = 100 * p ** (-1.5)
    q[-1] *= 50                      # one huge, expensive outlier
    w = np.ones(40)
    w[-1] = 10_000                   # carrying almost all the volume

    unweighted = log_log_elasticity(p, q)
    weighted = log_log_elasticity(p, q, weights=w)
    assert weighted.coef[1] > unweighted.coef[1]


def test_weighted_r_squared_is_not_inflated_by_the_weights():
    """WLS on sqrt-weighted data reports R^2 near 1 for any weighting.

    That number describes the spread of the weights, not the fit, so it must be
    recomputed on the original scale against the weighted mean.
    """
    rng = np.random.default_rng(7)
    p = np.exp(rng.normal(size=200))
    q = 100 * p ** (-1.2) * np.exp(rng.normal(size=200) * 1.5)  # very noisy
    w = np.exp(rng.normal(size=200) * 4)                        # wildly unequal

    result = log_log_elasticity(p, q, weights=w)
    assert result.r_squared < 0.9, (
        f"R^2 of {result.r_squared:.3f} on deliberately noisy data means the "
        "weights are being counted as explained variance"
    )
    assert 0.0 <= result.r_squared <= 1.0


def test_weighted_r_squared_is_high_when_the_fit_really_is_good():
    p = np.linspace(1, 20, 100)
    q = 100 * p ** (-1.5)
    w = np.linspace(1, 1000, 100)
    assert log_log_elasticity(p, q, weights=w).r_squared == pytest.approx(1.0, abs=1e-9)
