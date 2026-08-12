"""Hand-rolled statistics for arena-proofs.

No scipy. Everything is deterministic: permutation tests take an explicit
``seed`` and drive a ``numpy.random.Generator``. All functions are pure.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np

ArrayLike = Sequence[float] | np.ndarray


def _as_float_array(v: ArrayLike) -> np.ndarray:
    a = np.asarray(v, dtype=float)
    if a.ndim != 1:
        raise ValueError("expected a 1-D array")
    return a


def _average_ranks(v: np.ndarray) -> np.ndarray:
    """Ranks 1..n with ties assigned the average of their span."""
    order = np.argsort(v, kind="stable")
    ranks = np.empty(len(v), dtype=float)
    i = 0
    while i < len(v):
        j = i
        while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
            j += 1
        ranks[order[i : j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return ranks


def pearson(x: ArrayLike, y: ArrayLike) -> float:
    """Pearson product-moment correlation coefficient."""
    xa, ya = _as_float_array(x), _as_float_array(y)
    if len(xa) != len(ya):
        raise ValueError("x and y must have equal length")
    if len(xa) < 2:
        raise ValueError("need at least 2 points")
    xc, yc = xa - xa.mean(), ya - ya.mean()
    denom = math.sqrt(float(xc @ xc) * float(yc @ yc))
    if denom == 0.0:
        raise ValueError("zero variance in input")
    return float(xc @ yc / denom)


def spearman(x: ArrayLike, y: ArrayLike) -> float:
    """Spearman rank correlation (average ranks for ties)."""
    xa, ya = _as_float_array(x), _as_float_array(y)
    if len(xa) != len(ya):
        raise ValueError("x and y must have equal length")
    return pearson(_average_ranks(xa), _average_ranks(ya))


def permutation_p(
    stat_fn: Callable[[np.ndarray, np.ndarray], float],
    x: ArrayLike,
    y: ArrayLike,
    observed: float,
    n: int = 10000,
    seed: int = 0,
) -> float:
    """Two-sided permutation p-value for |stat| >= |observed|.

    ``stat_fn(x_perm, y)`` is evaluated on ``n`` seeded permutations of ``x``.
    Uses the (+1) adjusted estimator (count + 1) / (n + 1).
    """
    xa, ya = _as_float_array(x), _as_float_array(y)
    rng = np.random.default_rng(seed)
    threshold = abs(observed) - 1e-12
    count = 0
    for _ in range(n):
        stat = stat_fn(rng.permutation(xa), ya)
        if abs(stat) >= threshold:
            count += 1
    return (count + 1) / (n + 1)


@dataclass(frozen=True)
class OLSResult:
    beta: tuple[float, ...]
    se: tuple[float, ...]
    t: tuple[float, ...]
    r_squared: float
    n: int
    df_resid: int


def ols(X: ArrayLike, y: ArrayLike) -> OLSResult:
    """Ordinary least squares via the normal equations.

    ``X`` is an (n, k) design matrix (include a column of ones for an
    intercept), ``y`` length n. Returns beta, standard errors, t-stats, R^2.
    """
    Xa = np.atleast_2d(np.asarray(X, dtype=float))
    ya = _as_float_array(y)
    if Xa.shape[0] != len(ya):
        raise ValueError("X rows must match len(y)")
    n, k = Xa.shape
    if n <= k:
        raise ValueError("need more observations than parameters")
    XtX = Xa.T @ Xa
    XtX_inv = np.linalg.inv(XtX)
    beta = XtX_inv @ (Xa.T @ ya)
    resid = ya - Xa @ beta
    df = n - k
    s2 = float(resid @ resid) / df
    se = np.sqrt(s2 * np.diag(XtX_inv))
    with np.errstate(divide="ignore", invalid="ignore"):
        t = np.where(se > 0, beta / se, np.nan)
    ss_tot = float(((ya - ya.mean()) ** 2).sum())
    r2 = 1.0 - float(resid @ resid) / ss_tot if ss_tot > 0 else float("nan")
    return OLSResult(
        beta=tuple(float(b) for b in beta),
        se=tuple(float(s) for s in se),
        t=tuple(float(v) for v in t),
        r_squared=float(r2),
        n=n,
        df_resid=df,
    )


def _norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def mannwhitneyu(x: ArrayLike, y: ArrayLike) -> tuple[float, float]:
    """Mann-Whitney U test (normal approximation, continuity correction).

    Returns (U, p_two_sided). Ranks are averaged over ties; no tie-variance
    correction beyond average ranks is applied.
    """
    xa, ya = _as_float_array(x), _as_float_array(y)
    n1, n2 = len(xa), len(ya)
    if n1 == 0 or n2 == 0:
        raise ValueError("both samples must be non-empty")
    pooled = np.concatenate([xa, ya])
    ranks = _average_ranks(pooled)
    r1 = float(ranks[:n1].sum())
    u1 = r1 - n1 * (n1 + 1) / 2.0
    mu = n1 * n2 / 2.0
    sigma = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12.0)
    # continuity correction toward the mean; clamp at 0 so that
    # |u1 - mu| < 0.5 does not go negative and inflate significance
    diff = max(0.0, abs(u1 - mu) - 0.5)
    z = -abs(diff) / sigma
    p = 2.0 * _norm_cdf(z)
    return u1, float(p)


@dataclass(frozen=True)
class LogisticResult:
    beta: tuple[float, ...]
    converged: bool
    iterations: int
    final_grad_norm: float


def logistic_gd(
    X: ArrayLike,
    y: ArrayLike,
    lr: float = 0.5,
    iters: int = 200000,
    tol: float = 1e-9,
) -> LogisticResult:
    """Logistic regression by full-batch gradient descent on the NLL.

    ``X`` is an (n, k) design matrix (include a ones column), ``y`` is 0/1.
    Feature columns are standardised internally for conditioning and the
    coefficients are mapped back to the raw scale before returning, so the
    caller can interpret ``beta`` directly on ``X``. Deterministic.
    """
    Xa = np.atleast_2d(np.asarray(X, dtype=float))
    ya = _as_float_array(y)
    if Xa.shape[0] != len(ya):
        raise ValueError("X rows must match len(y)")
    n, k = Xa.shape

    # Standardise every non-constant column for conditioning; constant
    # columns (by convention a single intercept column of ones) pass through.
    mu = Xa.mean(axis=0)
    sd = Xa.std(axis=0)
    const_cols = sd == 0.0
    Z = Xa.copy()
    Z[:, ~const_cols] = (Xa[:, ~const_cols] - mu[~const_cols]) / sd[~const_cols]

    b = np.zeros(k)
    grad = np.full(k, np.inf)
    converged = False
    it_done = 0
    for it in range(1, iters + 1):
        z = np.clip(Z @ b, -500.0, 500.0)
        p = 1.0 / (1.0 + np.exp(-z))
        grad = Z.T @ (p - ya) / n
        b -= lr * grad
        it_done = it
        if float(np.abs(grad).max()) < tol:
            converged = True
            break
    final_grad = float(np.abs(grad).max())

    # Map coefficients back to the raw X scale: X@beta == Z@b.
    beta_raw = b.copy()
    beta_raw[~const_cols] = b[~const_cols] / sd[~const_cols]
    offset = float((b[~const_cols] * mu[~const_cols] / sd[~const_cols]).sum())
    const_idx = np.flatnonzero(const_cols)
    if len(const_idx) > 0:
        beta_raw[const_idx[0]] -= offset
    return LogisticResult(
        beta=tuple(float(v) for v in beta_raw),
        converged=converged,
        iterations=it_done,
        final_grad_norm=final_grad,
    )
