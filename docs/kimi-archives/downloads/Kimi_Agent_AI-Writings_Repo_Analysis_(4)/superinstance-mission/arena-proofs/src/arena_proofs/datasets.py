"""Typed loaders over the vendored zeroclaw-arena experiment JSONs.

All data lives in ``data/`` at the package root (copied from
``$ZARENA_DIR`` by ``scripts/fetch_data.sh`` and committed, so tests run
offline). Schemas below were verified against the actual files in
/mnt/agents/repos/zeroclaw-arena.
"""

from __future__ import annotations

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

#: Canonical dataset names -> bundled file names.
FILES = {
    "scaling-emergence": "scaling-emergence-results.json",
    "decay": "decay-results.json",
    "min-exposure": "min-exposure-results.json",
    "tile-capacity": "tile-capacity-results.json",
    "temperature-sweep": "temperature-sweep-results.json",
    "temporal-dynamics": "temporal-dynamics-results.json",
    "reflex-evolution-v2": "reflex-evolution-v2-results.json",
    "tile-conservation": "tile-conservation-results.json",
    "holographic-bound": "holographic-bound-results.json",
    "entropy-production": "entropy-production-results.json",
}


def load(name: str) -> dict:
    """Load a vendored experiment JSON by canonical name.

    Schemas (verified against the arena repo):

    - ``scaling-emergence``: keys "24"/"240"/"2400" (env counts). Each has
      ``reward_performance``/``reward_entropy`` dicts over 7 reward types
      {binary, marginal, progressive, sparse, adversarial, cooperative,
      noisy} (7 x 3 = 21 points), plus ``strategy_clusters`` (7/10/14) and
      ``complexity_performance`` {low, mid, high}.
    - ``decay``: ``decay_rates`` [0, .001, .005, .01, .02, .05, .1];
      ``conditions.with_switch[rate]`` = 5 trials (35 total) with
      ``pre_switch_winrate``/``post_switch_winrate``/``adaptation_game``/
      ``adaptation_speed``/``tile_churn_rate`` and ``windows`` = 25
      [game, win_rate] pairs (games 10..490; opponent switches at game 300).
      ``conditions.without_switch`` mirrors it.
    - ``temporal-dynamics``: ``tictactoe``/``connect4``, each 20 snapshots
      with ``game``, ``tiles``, ``gap``, ``entropy``, ``pos_mean``,
      ``neg_mean``, ``pos_std``, ``neg_std``.
    - ``reflex-evolution-v2``: ``polarization_history`` (21 floats,
      U-shaped 0.29 -> 0.2477 -> 0.7119), ``entropy_history``,
      ``score_history`` (21 dicts of strategy scores).
    - ``tile-conservation``: 5 seeds; ``run_summaries`` with
      ``score_distribution`` {mean, std, ...}; ``verdict.std_of_means``.
    - ``holographic-bound``: ``N``=1614, ``sqrt_N``=40, ``full_win_rate``,
      ``minimum_95pct``=5, ``subset_results`` = 8 rows {subset_size,
      avg_win_rate, pct_of_full_wr, trials}.
    - ``temperature-sweep``: ``results`` = 12 rows {temperature,
      train_win_rate, eval_win_rate_at_train_T, eval_win_rate_at_greedy_T,
      score_entropy, ...} for T in 0.01..5.0.
    - ``tile-capacity``: ``TTT``/``Connect4`` with ``full_tiles`` and
      ``prune_by_visits``/``prune_by_score`` lists.
    - ``min-exposure``: ``diverse``/``memorize`` with ``checkpoints``
      (20 rows {training_games, num_tiles, evaluation.win_rate}) and
      ``milestones``.
    - ``entropy-production``: ``ttt``/``c4``/``holdem`` each with 20
      ``snapshots`` ({n_tiles, shannon_entropy, score_mean, score_std,
      avg_tile_entropy, ...}) and an ``analysis`` summary.
    """
    if name not in FILES:
        raise KeyError(f"unknown dataset {name!r}; known: {sorted(FILES)}")
    path = DATA_DIR / FILES[name]
    with path.open() as fh:
        return json.load(fh)


def decay_with_switch_trials(data: dict | None = None) -> list[dict]:
    """Flatten decay ``conditions.with_switch`` to 35 trial dicts.

    Each returned trial gains a float ``decay_rate`` field.
    """
    data = data if data is not None else load("decay")
    trials = []
    for rate in data["decay_rates"]:
        for trial in data["conditions"]["with_switch"][str(rate)]:
            trials.append({**trial, "decay_rate": float(rate)})
    return trials


def scaling_reward_points(
    data: dict | None = None, *, exclude_sparse: bool = False
) -> list[dict]:
    """Flatten scaling-emergence to 21 (or 18) {scale, reward_type,
    reward_entropy, reward_performance} points."""
    data = data if data is not None else load("scaling-emergence")
    points = []
    for scale, entry in data.items():
        for reward_type, perf in entry["reward_performance"].items():
            if exclude_sparse and reward_type == "sparse":
                continue
            points.append(
                {
                    "scale": int(scale),
                    "reward_type": reward_type,
                    "reward_entropy": entry["reward_entropy"][reward_type],
                    "reward_performance": perf,
                }
            )
    return points
