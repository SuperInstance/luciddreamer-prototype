"""Render PROOF-REPORT.md from the claims audit and conjecture runs."""

from __future__ import annotations

from pathlib import Path

from .c1_collapse import C1Result, run_c1
from .c2_decay_zone import C2Result, format_p, run_c2
from .c3_log_gap import C3Result, run_c3
from .claims_audit import (
    POST_MOLT_INSTRUMENTATION_SPEC,
    ClaimVerdict,
    audit_all,
)

REPORT_PATH = Path(__file__).resolve().parents[2] / "PROOF-REPORT.md"


def _claims_table(verdicts: list[ClaimVerdict]) -> str:
    lines = [
        "| Claim | Verdict | Key recomputed evidence |",
        "| --- | --- | --- |",
    ]
    for v in verdicts:
        e = v.evidence
        if "std_of_means" in e:
            key = (
                f"std_of_means={e['std_of_means']:.6f}; "
                f"drift {e['additive_drift_start']:.3f}->{e['additive_drift_end']:.3f}"
            )
        elif "flat_range" in e:
            key = (
                f"eval WR range {e['eval_wr_min']:.3f}-{e['eval_wr_max']:.3f}; "
                f"curvature t={e['curvature_t']:+.2f}"
            )
        elif "shed_event_keys_found" in e:
            key = f"shed-event keys found: {len(e['shed_event_keys_found'])}"
        elif "pearson_all" in e:
            key = (
                f"Pearson {e['pearson_all']:.3f} (n={e['n_points']}); "
                f"Spearman {e['spearman_all']:.3f} p={e['spearman_perm_p_all']:.4f}; "
                f"excl-sparse Spearman {e['spearman_excl_sparse']:.3f}"
            )
        elif "saturation_c_fit" in e:
            key = (
                f"sqrt(N)={e['sqrt_N']:.0f} -> {e['pct_of_full_at_sqrt_N']:.1f}% "
                f"of full WR; c_fit={e['saturation_c_fit']:.1f}; "
                f"clusters exponent {e['cluster_growth_exponent']:.2f}"
            )
        else:
            key = ""
        lines.append(f"| {v.claim} | **{v.verdict.value}** | {key} |")
    return "\n".join(lines)


def _c1_section(r: C1Result) -> str:
    rows = "\n".join(
        f"| {s.scale} | {s.n_points} | {s.rho:+.4f} | {s.perm_p:.4f} |"
        for s in r.per_scale
    )
    return f"""\
### C1 — within-scale entropy/performance collapse

Prediction: {r.prediction}.

| Scale | n | Spearman rho | permutation p |
| --- | --- | --- | --- |
{rows}

mean |rho| = {r.mean_abs_rho:.3f}, max |rho| = {r.max_abs_rho:.3f}.

**Verdict: {r.verdict.value}** — {r.summary}"""


def _c2_section(r: C2Result) -> str:
    peak = "None (no inverted-U)" if r.peak_rate is None else f"{r.peak_rate:.5f}"
    return f"""\
### C2 — decay-rate sweet spot for post-switch adaptation

Prediction: inverted-U in log(decay rate) peaking near rate ~= {r.predicted_peak}.

- Logistic fit over {r.n_trials} with_switch trials ({r.n_adapted} adapted,
  at rates {list(r.adapted_rates)}):
  beta = ({r.beta[0]:+.4f}, {r.beta[1]:+.4f}, {r.beta[2]:+.4f}),
  converged = {r.logistic_converged}.
- Fitted peak rate = **{peak}** (predicted {r.predicted_peak};
  |log10 ratio| = {r.log10_peak_ratio:.3f}).
- Adaptation lag (window win rates, switch at game 300):
  pre {r.pre_mean_wr:.3f} (n={r.pre_windows}) vs post {r.post_mean_wr:.3f}
  (n={r.post_windows}); Mann-Whitney U = {r.mannwhitney_u:.0f},
  p = {format_p(r.mannwhitney_p)}.

**Verdict: {r.verdict.value}** — {r.summary}"""


def _c3_section(r: C3Result) -> str:
    return f"""\
### C3 — log-gap scaling law

Prediction: gap ~ a + b*log(tiles) with R^2 > {0.85}; b_C4 > b_TTT.

| Game | intercept | slope b | se(b) | t(b) | R^2 |
| --- | --- | --- | --- | --- | --- |
| TTT | {r.ttt.intercept:+.4f} | {r.ttt.slope:.4f} | {r.ttt.slope_se:.4f} | {r.ttt.slope_t:.2f} | {r.ttt.r_squared:.4f} |
| C4 | {r.c4.intercept:+.4f} | {r.c4.slope:.4f} | {r.c4.slope_se:.4f} | {r.c4.slope_t:.2f} | {r.c4.r_squared:.4f} |

- ANCOVA interaction (log(tiles) x game): beta = {r.interaction_beta:+.4f},
  t = {r.interaction_t:+.2f} -> b_C4 {'>' if r.b_c4_greater else '<'} b_TTT
  (prediction: b_C4 > b_TTT).
- U-shape cross-check (reflex-evolution-v2 polarization_history):
  {'confirmed' if r.u_shape_confirmed else 'NOT confirmed'} —
  minimum {r.u_min_value:.4f} at generation {r.u_min_index},
  rising to {r.u_end_value:.4f}.

**Verdict: {r.verdict.value}** — {r.summary}"""


def generate_report(out_path: Path | None = None) -> str:
    """Compute everything and render (and by default write) PROOF-REPORT.md."""
    verdicts = audit_all()
    c1, c2, c3 = run_c1(), run_c2(), run_c3()

    claim_details = "\n\n".join(
        f"#### {i}. {v.claim} — {v.verdict.value}\n\n{v.summary}"
        for i, v in enumerate(verdicts, 1)
    )

    md = f"""\
# PROOF-REPORT.md — arena-proofs

Reproducible claims audit and conjecture tests over the vendored
zeroclaw-arena experiment JSONs (`data/`). All statistics are hand-rolled
(`src/arena_proofs/stats.py`: pearson, spearman, permutation_p with
n=10000 seeded permutations, ols, mannwhitneyu, logistic_gd) and every
number below is recomputed from the bundled data — nothing is hardcoded.

## Claims audit

{_claims_table(verdicts)}

{claim_details}

## Conjectures

{_c1_section(c1)}

{_c2_section(c2)}

{_c3_section(c3)}

## New instrumentation needed

{POST_MOLT_INSTRUMENTATION_SPEC}

---
*Generated by `arena_proofs.report.generate_report()` — deterministic; re-run
`python -m arena_proofs` to regenerate.*
"""
    path = out_path if out_path is not None else REPORT_PATH
    path.write_text(md)
    return md
