# PROOF-REPORT.md — arena-proofs

Reproducible claims audit and conjecture tests over the vendored
zeroclaw-arena experiment JSONs (`data/`). All statistics are hand-rolled
(`src/arena_proofs/stats.py`: pearson, spearman, permutation_p with
n=10000 seeded permutations, ols, mannwhitneyu, logistic_gd) and every
number below is recomputed from the bundled data — nothing is hardcoded.

## Claims audit

| Claim | Verdict | Key recomputed evidence |
| --- | --- | --- |
| Tile score conservation law | **PARTIAL** | std_of_means=0.000964; drift 1.020->1.148 |
| Creative zone: intermediate temperature maximizes performance | **REFUTED** | eval WR range 0.648-0.712; curvature t=+1.35 |
| Post-molt adaptation: transient dip after tile shedding | **UNTESTABLE** | shed-event keys found: 0 |
| Zone inversion: exploration entropy anti-predicts performance | **PARTIAL** | Pearson -0.968 (n=21); Spearman -0.429 p=0.0559; excl-sparse Spearman -0.094 |
| Holographic bound: sqrt(N) random tiles retain full performance | **PARTIAL** | sqrt(N)=40 -> 98.6% of full WR; c_fit=3.2; clusters exponent 0.15 |

#### 1. Tile score conservation law — PARTIAL

Seed-invariance holds (std of 5 seed means = 0.000964), but pos_mean+neg_mean drifts 1.020 -> 1.148 over 1000 games, refuting strict conservation. PARTIAL.

#### 2. Creative zone: intermediate temperature maximizes performance — REFUTED

Eval win rate is flat across T (range 0.648-0.712, spread 0.064); quadratic curvature +0.0126 (t=+1.35) shows no inverted-U. No phi support: REFUTED as stated.

#### 3. Post-molt adaptation: transient dip after tile shedding — UNTESTABLE

No shed-event logging exists in any bundled experiment JSON; the claim cannot be evaluated. UNTESTABLE — see the instrumentation spec in PROOF-REPORT.md.

#### 4. Zone inversion: exploration entropy anti-predicts performance — PARTIAL

Pooled 21 points: Pearson -0.968, Spearman -0.429 (perm p=0.0559). Excluding the sparse-reward outlier: Spearman -0.094 (p=0.712) — the inversion is outlier-driven. PARTIAL.

#### 5. Holographic bound: sqrt(N) random tiles retain full performance — PARTIAL

sqrt(N)=40 subset reaches 98.6% of full win rate (direction OK), but saturation fits c=3.2 (file minimum_95pct=5), far below 40; strategy clusters 7/10/14 grow as N^0.15 (log10 slope 4.25), sublinear but not sqrt(N). PARTIAL.

## Conjectures

### C1 — within-scale entropy/performance collapse

Prediction: |rho| < 0.3 within each scale.

| Scale | n | Spearman rho | permutation p |
| --- | --- | --- | --- |
| 24 | 6 | -0.2571 | 0.6582 |
| 240 | 6 | -0.2000 | 0.7206 |
| 2400 | 6 | -0.3143 | 0.5553 |

mean |rho| = 0.257, max |rho| = 0.314.

**Verdict: PARTIAL** — Per-scale Spearman (sparse excluded): 24: rho=-0.257 (p=0.658), 240: rho=-0.200 (p=0.721), 2400: rho=-0.314 (p=0.555). mean |rho|=0.257, max |rho|=0.314; no scale significant. Verdict: PARTIAL.

### C2 — decay-rate sweet spot for post-switch adaptation

Prediction: inverted-U in log(decay rate) peaking near rate ~= 0.007.

- Logistic fit over 35 with_switch trials (3 adapted,
  at rates [0.005, 0.01, 0.05]):
  beta = (-10.0061, -3.8423, -0.4356),
  converged = True.
- Fitted peak rate = **0.01215** (predicted 0.007;
  |log10 ratio| = 0.239).
- Adaptation lag (window win rates, switch at game 300):
  pre 0.674 (n=525) vs post 0.260
  (n=350); Mann-Whitney U = 182890,
  p = <1e-300.

**Verdict: PARTIAL** — 3/35 trials adapted (rates (0.005, 0.01, 0.05)). Logistic beta=(-10.006, -3.842, -0.436) converged; inverted-U peak rate=0.01215 vs predicted 0.007. Window win rates: pre-switch 0.674 (n=525) vs post-switch 0.260 (n=350), Mann-Whitney U=182890 p=<1e-300. Verdict: PARTIAL.

### C3 — log-gap scaling law

Prediction: gap ~ a + b*log(tiles) with R^2 > 0.85; b_C4 > b_TTT.

| Game | intercept | slope b | se(b) | t(b) | R^2 |
| --- | --- | --- | --- | --- | --- |
| TTT | -0.5079 | 0.0975 | 0.0093 | 10.50 | 0.8596 |
| C4 | -0.4515 | 0.0704 | 0.0052 | 13.58 | 0.9110 |

- ANCOVA interaction (log(tiles) x game): beta = -0.0271,
  t = -2.64 -> b_C4 < b_TTT
  (prediction: b_C4 > b_TTT).
- U-shape cross-check (reflex-evolution-v2 polarization_history):
  confirmed —
  minimum 0.2477 at generation 4,
  rising to 0.7119.

**Verdict: PARTIAL** — gap ~ log(tiles): TTT b=0.0975 R^2=0.860 (t=10.5); C4 b=0.0704 R^2=0.911 (t=13.6). ANCOVA interaction -0.0271 (t=-2.64): b_C4 < b_TTT. U-shape confirmed on polarization_history (min 0.2477 at gen 4, end 0.7119). Verdict: PARTIAL.

## New instrumentation needed

### Post-molt event logging spec (for zeroclaw-arena `TileField`)

The arena never logs *when* tiles are shed, so the post-molt claim is
currently untestable. Required instrumentation:

1. **Shed-event records.** `TileField` must append one record per shed
   event to a `shed_events` list (and into every experiment JSON):
   `{cycle_id, wall_timestamp_ms, tile_id, tile_hash, score_at_shed,
   visits_at_shed, field_size_before, field_size_after, shed_reason}`
   where `shed_reason` is one of {decay, capacity_prune, consolidation}.
2. **Cycle indexing.** Every update cycle gets a monotonically increasing
   `cycle_id` (separate from game id) so shed events can be aligned with
   the win-rate windows already emitted by decay-trials style experiments.
3. **Per-cycle snapshots.** At each shed event, also log the running
   post-switch win rate and `pos_mean`/`neg_mean` so a pre/post-molt
   adaptation dip (predicted: transient win-rate drop then recovery within
   ~100 games) can be measured with a Mann-Whitney window comparison.
4. **Determinism.** Shed events must be reproducible under a fixed seed
   (log the RNG seed per experiment run alongside `seeds` as in
   tile-conservation-results.json).


---
*Generated by `arena_proofs.report.generate_report()` — deterministic; re-run
`python -m arena_proofs` to regenerate.*
