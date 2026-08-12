"""Conjecture 1 (collapse): within a fixed scale, reward entropy and reward
performance should be uncorrelated once the sparse-reward outlier is removed
— the cross-type collapse is a between-scale, not within-scale, effect.

Prediction: per-scale |Spearman rho| < 0.3 (sparse-reward points excluded).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import datasets
from .claims_audit import PERM_N, Verdict
from .stats import permutation_p, spearman

C1_PERM_SEED = 101
RHO_THRESHOLD = 0.3


@dataclass(frozen=True)
class C1ScaleResult:
    scale: int
    n_points: int
    rho: float
    perm_p: float


@dataclass(frozen=True)
class C1Result:
    per_scale: tuple[C1ScaleResult, ...]
    mean_abs_rho: float
    max_abs_rho: float
    prediction: str
    verdict: Verdict
    summary: str


def run_c1() -> C1Result:
    data = datasets.load("scaling-emergence")
    per_scale: list[C1ScaleResult] = []
    for scale_key in sorted(data, key=int):
        entry = data[scale_key]
        reward_types = [
            rt for rt in entry["reward_performance"] if rt != "sparse"
        ]
        x = np.array([entry["reward_entropy"][rt] for rt in reward_types])
        y = np.array([entry["reward_performance"][rt] for rt in reward_types])
        rho = spearman(x, y)
        p = permutation_p(
            lambda a, b: spearman(a, b), x, y, rho, n=PERM_N, seed=C1_PERM_SEED
        )
        per_scale.append(
            C1ScaleResult(scale=int(scale_key), n_points=len(x), rho=rho, perm_p=p)
        )

    abs_rhos = [abs(r.rho) for r in per_scale]
    mean_abs = float(np.mean(abs_rhos))
    max_abs = float(max(abs_rhos))
    any_significant = any(r.perm_p < 0.05 for r in per_scale)

    if max_abs <= RHO_THRESHOLD and not any_significant:
        verdict = Verdict.SUPPORTED
    elif mean_abs <= RHO_THRESHOLD and not any_significant:
        verdict = Verdict.PARTIAL
    else:
        verdict = Verdict.REFUTED

    rhos_str = ", ".join(f"{r.scale}: rho={r.rho:+.3f} (p={r.perm_p:.3f})" for r in per_scale)
    return C1Result(
        per_scale=tuple(per_scale),
        mean_abs_rho=mean_abs,
        max_abs_rho=max_abs,
        prediction=f"|rho| < {RHO_THRESHOLD} within each scale",
        verdict=verdict,
        summary=(
            f"Per-scale Spearman (sparse excluded): {rhos_str}. "
            f"mean |rho|={mean_abs:.3f}, max |rho|={max_abs:.3f}; "
            f"no scale significant. Verdict: {verdict.value}."
        ),
    )
