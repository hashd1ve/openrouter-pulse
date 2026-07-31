"""Statistical estimators.

SQL models sets; it does not do survival analysis or robust regression. These
are the estimators the marts need, implemented directly rather than pulled in
from lifelines/statsmodels: they are short, the assumptions matter more than the
code, and every one is verified in `tests/test_analytics.py` against a case with
a known closed-form answer.

Everything here is pure: arrays in, arrays out, no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

# Normal quantile for a 95% two-sided interval. Hardcoded to avoid a scipy
# dependency for a single constant.
Z_95 = 1.959963984540054


# --- concentration ---------------------------------------------------------


def herfindahl(values: np.ndarray) -> float:
    """HHI on a 0–10,000 scale, the convention competition authorities use.

    10,000 is a pure monopoly; below 1,500 is normally called unconcentrated.
    Negative values are rejected rather than silently clipped: a negative share
    means the caller passed the wrong column.
    """
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]
    if v.size == 0:
        return float("nan")
    if (v < 0).any():
        raise ValueError("HHI is undefined for negative values")
    total = v.sum()
    if total <= 0:
        return float("nan")
    shares = v / total
    return float((shares**2).sum() * 10_000)


def gini(values: np.ndarray) -> float:
    """Gini coefficient. 0 = perfectly even, →1 = one holder takes everything.

    Uses the sorted-rank form, which is exact and O(n log n):
        G = (2 * Σ i·x_i) / (n · Σ x_i) - (n + 1) / n
    """
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]
    if v.size == 0:
        return float("nan")
    if (v < 0).any():
        raise ValueError("Gini is undefined for negative values")
    n = v.size
    total = v.sum()
    if total <= 0:
        return float("nan")
    v = np.sort(v)
    index = np.arange(1, n + 1)
    return float((2 * (index * v).sum()) / (n * total) - (n + 1) / n)


def top_n_share(values: np.ndarray, n: int) -> float:
    """Share of the total held by the largest n."""
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]
    total = v.sum()
    if v.size == 0 or total <= 0:
        return float("nan")
    return float(np.sort(v)[::-1][:n].sum() / total)


# --- survival --------------------------------------------------------------


@dataclass
class KaplanMeier:
    """Survival curve with right-censoring.

    `time`      distinct times at which something happened
    `at_risk`   how many subjects were still being observed just before
    `events`    how many failed at that time
    `survival`  S(t), the probability of surviving beyond t
    `ci_low` / `ci_high`  95% band via the log-log transform, which keeps the
                interval inside [0, 1] — the plain Greenwood interval does not,
                and at the tail it routinely produces bounds above 1.
    """

    time: np.ndarray
    at_risk: np.ndarray
    events: np.ndarray
    censored: np.ndarray
    survival: np.ndarray
    ci_low: np.ndarray
    ci_high: np.ndarray
    n_subjects: int = 0
    n_events: int = 0

    def quantile(self, p: float = 0.5) -> float:
        """Smallest t with S(t) <= 1-p. NaN if the curve never gets there.

        Returning NaN rather than the last observed time is deliberate: if the
        curve never drops to 50%, the median survival is *not reached*, and
        reporting the study's end date instead would understate it badly.
        """
        target = 1.0 - p
        below = np.nonzero(self.survival <= target)[0]
        return float(self.time[below[0]]) if below.size else float("nan")

    def at(self, t: float) -> float:
        """S(t) via the step function (last value at or before t)."""
        prior = np.nonzero(self.time <= t)[0]
        return float(self.survival[prior[-1]]) if prior.size else 1.0


def kaplan_meier(durations, observed) -> KaplanMeier:
    """Product-limit estimator with Greenwood variance.

    `durations`  time from entry to event, or to censoring
    `observed`   True if the event was seen, False if the subject was still
                 alive when observation stopped

    Censoring is what makes this necessary. Most models in the dataset are still
    running: their lifetime is only known to be *at least* their current age.
    Dropping them would bias the curve towards short lives; treating their age
    as a lifetime would bias it the other way. The product-limit estimator uses
    exactly the information each subject carries and no more.
    """
    d = np.asarray(durations, dtype=float)
    e = np.asarray(observed, dtype=bool)
    keep = np.isfinite(d) & (d >= 0)
    d, e = d[keep], e[keep]
    n = d.size
    if n == 0:
        empty = np.array([])
        return KaplanMeier(empty, empty, empty, empty, empty, empty, empty, 0, 0)

    times = np.unique(d)
    at_risk, events, censored = [], [], []
    for t in times:
        at_risk.append(int((d >= t).sum()))
        events.append(int(((d == t) & e).sum()))
        censored.append(int(((d == t) & ~e).sum()))
    at_risk = np.array(at_risk, dtype=float)
    events = np.array(events, dtype=float)
    censored = np.array(censored, dtype=int)

    survival = np.cumprod(1.0 - np.divide(
        events, at_risk, out=np.zeros_like(events), where=at_risk > 0
    ))

    # Greenwood's formula for Var(log S(t)).
    denom = at_risk * (at_risk - events)
    terms = np.divide(events, denom, out=np.zeros_like(events), where=denom > 0)
    cum = np.cumsum(terms)

    # Log-log interval: keeps the band inside [0, 1] at both ends.
    with np.errstate(divide="ignore", invalid="ignore"):
        log_s = np.log(survival)
        se = np.sqrt(cum) / np.abs(log_s)
        factor = np.exp(Z_95 * se)
        ci_low = survival ** factor
        ci_high = survival ** (1.0 / factor)
    for arr in (ci_low, ci_high):
        arr[~np.isfinite(arr)] = np.nan
    # S = 1 carries no uncertainty; S = 0 is absorbing.
    ci_low[survival >= 1.0] = 1.0
    ci_high[survival >= 1.0] = 1.0
    ci_low[survival <= 0.0] = 0.0

    return KaplanMeier(
        time=times, at_risk=at_risk, events=events, censored=censored,
        survival=survival, ci_low=ci_low, ci_high=ci_high,
        n_subjects=n, n_events=int(e.sum()),
    )


# --- regression ------------------------------------------------------------


@dataclass
class OLSResult:
    """Least squares with heteroskedasticity-robust standard errors."""

    names: list[str]
    coef: np.ndarray
    se: np.ndarray
    t: np.ndarray
    ci_low: np.ndarray
    ci_high: np.ndarray
    r_squared: float
    n: int

    def summary(self) -> dict[str, dict[str, float]]:
        return {
            name: {
                "coef": float(self.coef[i]), "se": float(self.se[i]),
                "t": float(self.t[i]), "ci_low": float(self.ci_low[i]),
                "ci_high": float(self.ci_high[i]),
            }
            for i, name in enumerate(self.names)
        }


def ols(X: np.ndarray, y: np.ndarray, names: list[str] | None = None) -> OLSResult:
    """OLS with HC1 robust covariance.

    Robust rather than classical standard errors because the residuals here are
    wildly heteroskedastic: token volume spans nine orders of magnitude, and
    classical errors would report confidence the data does not support.

    `X` must already contain an intercept column if one is wanted.
    """
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    if X.ndim == 1:
        X = X[:, None]
    n, k = X.shape
    if n <= k:
        raise ValueError(f"need more observations than parameters (n={n}, k={k})")

    xtx_inv = np.linalg.pinv(X.T @ X)
    beta = xtx_inv @ X.T @ y
    resid = y - X @ beta

    # HC1: the sandwich, with the small-sample n/(n-k) correction.
    meat = (X * (resid**2)[:, None]).T @ X
    cov = xtx_inv @ meat @ xtx_inv * (n / (n - k))
    se = np.sqrt(np.diag(cov))

    ss_res = (resid**2).sum()
    ss_tot = ((y - y.mean()) ** 2).sum()
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")

    with np.errstate(divide="ignore", invalid="ignore"):
        t = beta / se
    return OLSResult(
        names=names or [f"x{i}" for i in range(k)],
        coef=beta, se=se, t=t,
        ci_low=beta - Z_95 * se, ci_high=beta + Z_95 * se,
        r_squared=float(r2), n=n,
    )


def log_log_elasticity(price, quantity, weights=None) -> OLSResult | None:
    """Elasticity of demand: the slope of log(quantity) on log(price).

    A coefficient of -1.3 reads as "a 1% higher price is associated with 1.3%
    fewer tokens". Association, not causation — this is a cross-section of
    different models, not the same model at different prices, so the estimate is
    confounded by quality. It bounds the story; it does not tell it.
    """
    p = np.asarray(price, dtype=float)
    q = np.asarray(quantity, dtype=float)
    keep = np.isfinite(p) & np.isfinite(q) & (p > 0) & (q > 0)
    if weights is not None:
        w = np.asarray(weights, dtype=float)
        keep &= np.isfinite(w) & (w > 0)
    if keep.sum() < 10:
        return None

    lp, lq = np.log(p[keep]), np.log(q[keep])
    X = np.column_stack([np.ones(lp.size), lp])
    if weights is None:
        return ols(X, lq, names=["intercept", "log_price"])

    # Weighted least squares by the square root of the weight, so the fit
    # follows where the traffic actually is rather than treating a model with
    # 300 requests as equal to one with 300 billion tokens.
    ww = w[keep]
    rw = np.sqrt(ww)
    result = ols(X * rw[:, None], lq * rw, names=["intercept", "log_price"])

    # The R-squared that ols() returned is computed on the sqrt-weighted
    # response, whose total sum of squares is dominated by the weights rather
    # than by the relationship. It comes out near 1.0 for any weighting and
    # means nothing. Recompute it on the original scale against the WEIGHTED
    # mean, which is the quantity the weighted fit is actually explaining.
    fitted = X @ result.coef
    resid = lq - fitted
    wmean = np.average(lq, weights=ww)
    ss_res = float((ww * resid**2).sum())
    ss_tot = float((ww * (lq - wmean) ** 2).sum())
    result.r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return result
