"""Conjecture 2 (decay sweet spot): adaptation after an opponent switch is
maximal at an intermediate memory-decay rate — an inverted-U in log(rate).

Two tests over the 35 ``with_switch`` decay trials:
1. Logistic regression of adapted (0/1) on [1, log rate, (log rate)^2];
   the fitted peak rate is compared against the prediction peak ~= 0.007.
2. Mann-Whitney U on per-20-game window win rates pre- vs post-game-300
   (the opponent switch) — the adaptation lag.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from . import datasets
from .claims_audit import Verdict
from .stats import logistic_gd, mannwhitneyu

PREDICTED_PEAK = 0.007
SWITCH_GAME = 300
# log(0) is undefined; the zero-decay condition is mapped to half the
# smallest positive rate (0.001 / 2) on the log scale.
ZERO_RATE_EPS = 0.0005


def format_p(p: float) -> str:
    """Readable p-value; guards against erf underflow to exactly 0.0."""
    if p <= 0.0:
        return "<1e-300"
    return f"{p:.3g}"


@dataclass(frozen=True)
class C2Result:
    n_trials: int
    n_adapted: int
    adapted_rates: tuple[float, ...]
    beta: tuple[float, float, float]
    logistic_converged: bool
    peak_rate: float | None
    predicted_peak: float
    log10_peak_ratio: float | None
    pre_windows: int
    post_windows: int
    pre_mean_wr: float
    post_mean_wr: float
    mannwhitney_u: float
    mannwhitney_p: float
    verdict: Verdict
    summary: str


def run_c2() -> C2Result:
    trials = datasets.decay_with_switch_trials()
    log_rates, adapted = [], []
    pre_wr, post_wr = [], []
    for trial in trials:
        rate = trial["decay_rate"]
        lr = math.log(rate if rate > 0 else ZERO_RATE_EPS)
        log_rates.append(lr)
        adapted.append(1.0 if trial["adaptation_game"] is not None else 0.0)
        for game, wr in trial["windows"]:
            if game < SWITCH_GAME:
                pre_wr.append(wr)
            elif game > SWITCH_GAME:
                post_wr.append(wr)

    X = np.column_stack(
        [np.ones(len(log_rates)), np.array(log_rates), np.array(log_rates) ** 2]
    )
    y = np.array(adapted)
    fit = logistic_gd(X, y, lr=0.5, iters=300000)
    b0, b1, b2 = fit.beta
    peak = math.exp(-b1 / (2.0 * b2)) if b2 < 0 else None
    log10_ratio = (
        abs(math.log10(peak / PREDICTED_PEAK)) if peak is not None else None
    )

    u, p_mw = mannwhitneyu(pre_wr, post_wr)

    adapted_rates = tuple(
        sorted({t["decay_rate"] for t in trials if t["adaptation_game"] is not None})
    )

    inverted_u = b2 < 0 and peak is not None and 0.0005 <= peak <= 0.2
    if inverted_u and log10_ratio is not None and log10_ratio <= math.log10(1.5):
        verdict = Verdict.SUPPORTED
    elif inverted_u and log10_ratio is not None and log10_ratio <= math.log10(3.0):
        verdict = Verdict.PARTIAL
    else:
        verdict = Verdict.REFUTED

    return C2Result(
        n_trials=len(trials),
        n_adapted=int(y.sum()),
        adapted_rates=adapted_rates,
        beta=(b0, b1, b2),
        logistic_converged=fit.converged,
        peak_rate=peak,
        predicted_peak=PREDICTED_PEAK,
        log10_peak_ratio=log10_ratio,
        pre_windows=len(pre_wr),
        post_windows=len(post_wr),
        pre_mean_wr=float(np.mean(pre_wr)),
        post_mean_wr=float(np.mean(post_wr)),
        mannwhitney_u=u,
        mannwhitney_p=p_mw,
        verdict=verdict,
        summary=(
            f"{int(y.sum())}/{len(trials)} trials adapted (rates "
            f"{adapted_rates}). Logistic beta=({b0:+.3f}, {b1:+.3f}, {b2:+.3f})"
            f"{' converged' if fit.converged else ' (not fully converged)'}; "
            f"inverted-U peak rate={peak if peak is None else round(peak, 5)} "
            f"vs predicted {PREDICTED_PEAK}. Window win rates: pre-switch "
            f"{np.mean(pre_wr):.3f} (n={len(pre_wr)}) vs post-switch "
            f"{np.mean(post_wr):.3f} (n={len(post_wr)}), Mann-Whitney "
            f"U={u:.0f} p={format_p(p_mw)}. Verdict: {verdict.value}."
        ),
    )
