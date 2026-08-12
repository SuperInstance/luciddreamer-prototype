"""Tests for conjectures C1-C3 over the bundled data."""

import pytest

from arena_proofs.c1_collapse import run_c1
from arena_proofs.c2_decay_zone import run_c2
from arena_proofs.c3_log_gap import run_c3
from arena_proofs.claims_audit import Verdict


class TestC1:
    def test_three_scales_six_points_each(self):
        r = run_c1()
        assert len(r.per_scale) == 3
        assert [s.scale for s in r.per_scale] == [24, 240, 2400]
        assert all(s.n_points == 6 for s in r.per_scale)

    def test_no_significant_within_scale_correlation(self):
        r = run_c1()
        for s in r.per_scale:
            assert abs(s.rho) < 0.5
            assert s.perm_p > 0.05
        # prediction |rho| < 0.3: met on average, max marginally over
        assert r.mean_abs_rho < 0.3
        assert r.verdict in (Verdict.SUPPORTED, Verdict.PARTIAL)

    def test_determinism(self):
        r1, r2 = run_c1(), run_c1()
        assert r1 == r2


class TestC2:
    def test_logistic_inverted_u_peak(self):
        r = run_c2()
        assert r.n_trials == 35
        assert r.n_adapted == 3
        assert r.adapted_rates == (0.005, 0.01, 0.05)
        assert r.beta[2] < 0  # inverted-U
        assert r.peak_rate is not None
        # same order of magnitude as the predicted 0.007
        assert 0.002 < r.peak_rate < 0.03

    def test_mannwhitney_adaptation_lag(self):
        r = run_c2()
        assert r.pre_windows == 35 * 15
        assert r.post_windows == 35 * 10
        assert r.pre_mean_wr > r.post_mean_wr  # switch hurts
        assert r.mannwhitney_p < 0.001

    def test_determinism(self):
        r1, r2 = run_c2(), run_c2()
        assert r1 == r2


class TestC3:
    def test_log_gap_fits(self):
        r = run_c3()
        assert r.ttt.r_squared > 0.85
        assert r.c4.r_squared > 0.85
        assert r.ttt.slope > 0 and r.c4.slope > 0

    def test_interaction_direction_recomputed(self):
        r = run_c3()
        # Recomputed from data: C4 slope is actually shallower than TTT.
        assert r.b_c4_greater is False
        assert r.interaction_beta < 0
        assert abs(r.interaction_t) > 2.0

    def test_u_shape_cross_check(self):
        r = run_c3()
        assert r.u_shape_confirmed is True
        assert r.u_min_value == pytest.approx(0.2477, abs=1e-4)
        assert r.u_min_index == 4
        assert r.u_end_value == pytest.approx(0.7119, abs=1e-4)

    def test_determinism(self):
        r1, r2 = run_c3(), run_c3()
        assert r1 == r2
