# arena-proofs

Reproducible proofs & claims audit over the zeroclaw-arena experiment JSONs.
numpy allowed; **no scipy/pandas** — all statistics are hand-rolled and
deterministic (`src/arena_proofs/stats.py`): `pearson`, `spearman` (average
ranks), `permutation_p` (10 000 seeded permutations), `ols` (beta/se/t/R²),
`mannwhitneyu` (normal approx + continuity correction), `logistic_gd`
(gradient descent with internal standardisation, returns beta + converged).

## Layout

- `src/arena_proofs/stats.py` — hand-rolled statistics.
- `src/arena_proofs/datasets.py` — typed loaders over `data/` (vendored,
  committed; tests run fully offline).
- `src/arena_proofs/claims_audit.py` — five claim checks
  (`check_conservation`, `check_creative_zone`, `check_post_molt`,
  `check_zone_inversion`, `check_holographic`) returning `ClaimVerdict`
  with verdicts in {SUPPORTED, PARTIAL, REFUTED, UNTESTABLE}.
- `src/arena_proofs/c1_collapse.py`, `c2_decay_zone.py`, `c3_log_gap.py` —
  conjectures C1/C2/C3.
- `src/arena_proofs/report.py` — `generate_report()` renders
  `PROOF-REPORT.md` (claims table, conjecture numbers, post-molt
  instrumentation spec).
- `scripts/fetch_data.sh` — re-vendor the JSONs from the arena repo
  (`ZARENA_DIR`, default `/mnt/agents/repos/zeroclaw-arena`).
- `data/` — committed copies of the experiment JSONs.

## Use

```bash
pip install -e .
python -m pytest -q          # 42 tests, offline
python -m arena_proofs       # regenerate PROOF-REPORT.md
make report                  # same, via Makefile
make data                    # re-vendor data from $ZARENA_DIR
```

## Headline results (recomputed from `data/`)

| Item | Verdict | Key numbers |
| --- | --- | --- |
| Conservation law | PARTIAL | std_of_means = 0.000964 (supports); pos+neg mean drift 1.020→1.148 (refutes strict) |
| Creative zone | REFUTED | eval WR flat 0.648–0.712 across T=0.01–5.0, no inverted-U |
| Post-molt adaptation | UNTESTABLE | no shed-event logging anywhere; instrumentation spec in PROOF-REPORT.md |
| Zone inversion | PARTIAL | Pearson −0.968, Spearman −0.429 (p≈0.055) on 21 pooled points; outlier-driven by the sparse-reward point |
| Holographic bound | PARTIAL | √N=40 → 98.6% of full WR (direction OK); saturation c≈3.2 ≪ 40; clusters 7/10/14 ~ N^0.15 |
| C1 collapse | PARTIAL | per-scale Spearman −0.257/−0.200/−0.314, all p>0.55 |
| C2 decay sweet spot | PARTIAL | logistic inverted-U peak 0.012 vs predicted 0.007; pre/post-300 MW p≈0 |
| C3 log-gap law | PARTIAL | R² 0.860/0.911 (both >0.85); but b_C4 < b_TTT (t=−2.64); U-shape confirmed |

## Run on the boat

The boat has 24 cores, Ollama at `localhost:11434`, and
`DEEPINFRA_API_KEY`/`DEEPSEEK_API_KEY` in the environment — none of which
this package needs: arena-proofs is pure CPU + numpy over the vendored
JSONs. On the boat:

```bash
git clone <mission-repo> && cd superinstance-mission/arena-proofs
python3 -m venv .venv && . .venv/bin/activate
pip install -e . && python -m pytest -q
python -m arena_proofs   # writes PROOF-REPORT.md
```

To refresh the data from a local zeroclaw-arena checkout:
`ZARENA_DIR=/path/to/zeroclaw-arena make data` (then commit the changed
`data/*.json`).
