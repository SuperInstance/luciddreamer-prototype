"""Conjecture 3 (log-gap law): the pos/neg score gap grows linearly in
log(tiles) for both TTT and Connect4, with a steeper slope in the more
complex game (C4).

Tests over the 20 temporal-dynamics snapshots per game:
1. OLS gap ~ a + b * log(tiles) for TTT and C4 (prediction: R^2 > 0.85,
   given correlations 0.927 / 0.955).
2. ANCOVA-style interaction: gap ~ log(tiles) * game; test b_C4 > b_TTT.
3. Shape cross-check against reflex-evolution-v2 ``polarization_history``:
   a U-shape (0.29 -> 0.2477 minimum -> 0.7119) with monotone arms.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import datasets
from .claims_audit import Verdict
from .stats import ols, spearman

R2_THRESHOLD = 0.85


@dataclass(frozen=True)
class C3GameFit:
    game: str
    intercept: float
    slope: float
    slope_se: float
    slope_t: float
    r_squared: float


@dataclass(frozen=True)
class C3Result:
    ttt: C3GameFit
    c4: C3GameFit
    interaction_beta: float
    interaction_t: float
    b_c4_greater: bool
    u_shape_confirmed: bool
    u_min_value: float
    u_min_index: int
    u_end_value: float
    verdict: Verdict
    summary: str


def _fit_game(series: list[dict], game: str) -> C3GameFit:
    log_tiles = np.log([s["tiles"] for s in series])
    gap = np.array([s["gap"] for s in series])
    X = np.column_stack([np.ones(len(gap)), log_tiles])
    fit = ols(X, gap)
    return C3GameFit(
        game=game,
        intercept=fit.beta[0],
        slope=fit.beta[1],
        slope_se=fit.se[1],
        slope_t=fit.t[1],
        r_squared=fit.r_squared,
    )


def run_c3() -> C3Result:
    temporal = datasets.load("temporal-dynamics")
    ttt_fit = _fit_game(temporal["tictactoe"], "TTT")
    c4_fit = _fit_game(temporal["connect4"], "C4")

    # ANCOVA: gap ~ 1 + log(tiles) + game + log(tiles):game  (game: 0=TTT, 1=C4)
    rows = []
    for indicator, series in ((0.0, temporal["tictactoe"]), (1.0, temporal["connect4"])):
        for s in series:
            rows.append((float(np.log(s["tiles"])), indicator, s["gap"]))
    log_tiles = np.array([r[0] for r in rows])
    game = np.array([r[1] for r in rows])
    gap = np.array([r[2] for r in rows])
    X = np.column_stack([np.ones(len(gap)), log_tiles, game, log_tiles * game])
    ancova = ols(X, gap)
    interaction_beta, interaction_t = ancova.beta[3], ancova.t[3]
    b_c4_greater = c4_fit.slope > ttt_fit.slope

    # U-shape cross-check on reflex-evolution-v2 polarization history.
    pol = datasets.load("reflex-evolution-v2")["polarization_history"]
    pol = np.array(pol, dtype=float)
    min_idx = int(np.argmin(pol))
    left_rho = spearman(np.arange(min_idx + 1), pol[: min_idx + 1])
    right_rho = spearman(
        np.arange(len(pol) - min_idx), pol[min_idx:]
    )
    u_confirmed = (
        0 < min_idx < len(pol) - 1 and left_rho < -0.9 and right_rho > 0.9
    )

    fits_ok = ttt_fit.r_squared > R2_THRESHOLD and c4_fit.r_squared > R2_THRESHOLD
    interaction_ok = b_c4_greater and interaction_t > 2.0
    if fits_ok and interaction_ok and u_confirmed:
        verdict = Verdict.SUPPORTED
    elif fits_ok or (interaction_ok and u_confirmed):
        verdict = Verdict.PARTIAL
    else:
        verdict = Verdict.REFUTED

    return C3Result(
        ttt=ttt_fit,
        c4=c4_fit,
        interaction_beta=interaction_beta,
        interaction_t=interaction_t,
        b_c4_greater=b_c4_greater,
        u_shape_confirmed=u_confirmed,
        u_min_value=float(pol[min_idx]),
        u_min_index=min_idx,
        u_end_value=float(pol[-1]),
        verdict=verdict,
        summary=(
            f"gap ~ log(tiles): TTT b={ttt_fit.slope:.4f} R^2={ttt_fit.r_squared:.3f}"
            f" (t={ttt_fit.slope_t:.1f}); C4 b={c4_fit.slope:.4f} "
            f"R^2={c4_fit.r_squared:.3f} (t={c4_fit.slope_t:.1f}). ANCOVA "
            f"interaction {interaction_beta:+.4f} (t={interaction_t:+.2f}): "
            f"b_C4 {'>' if b_c4_greater else '<'} b_TTT. U-shape "
            f"{'confirmed' if u_confirmed else 'NOT confirmed'} on "
            f"polarization_history (min {pol[min_idx]:.4f} at gen {min_idx}, "
            f"end {pol[-1]:.4f}). Verdict: {verdict.value}."
        ),
    )
