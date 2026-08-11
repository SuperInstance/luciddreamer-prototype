"""Known-answer and determinism tests for the hand-rolled stats."""

import math

import numpy as np
import pytest

from arena_proofs.stats import (
    logistic_gd,
    mannwhitneyu,
    ols,
    pearson,
    permutation_p,
    spearman,
)


class TestPearson:
    def test_identical_series(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert pearson(x, x) == pytest.approx(1.0)

    def test_perfect_negative(self):
        x = [1.0, 2.0, 3.0, 4.0]
        y = [4.0, 3.0, 2.0, 1.0]
        assert pearson(x, y) == pytest.approx(-1.0)

    def test_known_value(self):
        # Hand-computed: corr([1,2,3],[1,2,4]) = 0.5*sqrt(3)... compute exactly:
        # cov = ( (-1)(-1) + 0 + (1)(1) ) = 2; sx = sqrt(2), sy = sqrt(2) -> wait:
        # y = [1,2,4], mean 7/3; deviations -4/3, -1/3, 5/3; cov = (-1)(-4/3)+0+(1)(5/3)=3
        # sx = sqrt(2); sy = sqrt(16/9+1/9+25/9)=sqrt(42/9)=sqrt(42)/3
        expected = 3.0 / (math.sqrt(2.0) * math.sqrt(42.0) / 3.0)
        assert pearson([1, 2, 3], [1, 2, 4]) == pytest.approx(expected)

    def test_uncorrelated(self):
        assert pearson([1, -1, 1, -1], [1, 1, -1, -1]) == pytest.approx(0.0)


class TestSpearman:
    def test_identical_series(self):
        x = [3.0, 1.0, 2.0, 5.0, 4.0]
        assert spearman(x, x) == pytest.approx(1.0)

    def test_monotone_nonlinear_is_one(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [math.exp(v) for v in x]
        assert spearman(x, y) == pytest.approx(1.0)

    def test_average_ranks_for_ties(self):
        # [1,2,2,3] -> ranks [1, 2.5, 2.5, 4]; correlate with [1,2,3,4]
        x = [1.0, 2.0, 2.0, 3.0]
        y = [1.0, 2.0, 3.0, 4.0]
        # ranks x: 1, 2.5, 2.5, 4 ; pearson with 1..4:
        rx = np.array([1.0, 2.5, 2.5, 4.0])
        ry = np.array([1.0, 2.0, 3.0, 4.0])
        expected = np.corrcoef(rx, ry)[0, 1]
        assert spearman(x, y) == pytest.approx(expected)

    def test_reversed(self):
        x = [1.0, 2.0, 3.0, 4.0]
        assert spearman(x, x[::-1]) == pytest.approx(-1.0)


class TestPermutationP:
    def test_deterministic_same_seed(self):
        rng = np.random.default_rng(0)
        x, y = rng.normal(size=20), rng.normal(size=20)
        obs = pearson(x, y)
        p1 = permutation_p(lambda a, b: pearson(a, b), x, y, obs, n=2000, seed=42)
        p2 = permutation_p(lambda a, b: pearson(a, b), x, y, obs, n=2000, seed=42)
        assert p1 == p2

    def test_strong_correlation_small_p(self):
        x = np.arange(30.0)
        y = x + np.linspace(0, 0.01, 30)  # nearly perfect
        obs = pearson(x, y)
        p = permutation_p(lambda a, b: pearson(a, b), x, y, obs, n=5000, seed=1)
        assert p < 0.01

    def test_noise_large_p(self):
        rng = np.random.default_rng(7)
        x, y = rng.normal(size=40), rng.normal(size=40)
        obs = pearson(x, y)
        p = permutation_p(lambda a, b: pearson(a, b), x, y, obs, n=5000, seed=2)
        assert p > 0.2

    def test_p_bounded(self):
        x = [1.0, 2.0, 3.0]
        y = [1.0, 2.0, 3.0]
        p = permutation_p(lambda a, b: pearson(a, b), x, y, 1.0, n=100, seed=3)
        assert 0.0 < p <= 1.0


class TestOLS:
    def test_recovers_known_slope_intercept(self):
        x = np.linspace(0, 10, 50)
        y = 3.0 + 2.5 * x
        fit = ols(np.column_stack([np.ones(50), x]), y)
        assert fit.beta[0] == pytest.approx(3.0, abs=1e-8)
        assert fit.beta[1] == pytest.approx(2.5, abs=1e-8)
        assert fit.r_squared == pytest.approx(1.0)

    def test_noisy_known_answer(self):
        rng = np.random.default_rng(5)
        x = rng.normal(size=200)
        y = 1.0 - 2.0 * x + rng.normal(scale=0.5, size=200)
        fit = ols(np.column_stack([np.ones(200), x]), y)
        assert fit.beta[0] == pytest.approx(1.0, abs=0.15)
        assert fit.beta[1] == pytest.approx(-2.0, abs=0.15)
        assert 0.8 < fit.r_squared < 1.0
        # t-stat for a strong slope should be huge
        assert abs(fit.t[1]) > 10.0

    def test_multivariate(self):
        rng = np.random.default_rng(11)
        x1 = rng.normal(size=100)
        x2 = rng.normal(size=100)
        y = 0.5 + 1.0 * x1 - 3.0 * x2
        fit = ols(np.column_stack([np.ones(100), x1, x2]), y)
        assert fit.beta == pytest.approx((0.5, 1.0, -3.0), abs=1e-6)

    def test_deterministic(self):
        x = np.linspace(0, 1, 20)
        y = np.sin(x)
        f1 = ols(np.column_stack([np.ones(20), x]), y)
        f2 = ols(np.column_stack([np.ones(20), x]), y)
        assert f1 == f2


class TestMannWhitney:
    def test_identical_samples_high_p(self):
        x = list(range(20))
        u, p = mannwhitneyu(x, x)
        assert p > 0.9

    def test_identical_small_samples_no_inflated_significance(self):
        # Regression: with |u1 - mu| < 0.5 the continuity correction used to
        # go negative and inflate significance. Identical n=3 samples must
        # give p ≈ 1.0.
        x = [1.0, 2.0, 3.0]
        u, p = mannwhitneyu(x, x)
        assert u == pytest.approx(4.5)
        assert p > 0.9

    def test_separated_samples_low_p(self):
        x = [float(v) for v in range(10)]
        y = [float(v) for v in range(100, 110)]
        u, p = mannwhitneyu(x, y)
        assert u == pytest.approx(0.0)
        assert p < 0.001

    def test_known_u(self):
        # x = [1,2], y = [3,4]: ranks 1,2,3,4 -> R1 = 3 -> U1 = 3 - 3 = 0
        u, _ = mannwhitneyu([1.0, 2.0], [3.0, 4.0])
        assert u == pytest.approx(0.0)
        u2, _ = mannwhitneyu([3.0, 4.0], [1.0, 2.0])
        assert u2 == pytest.approx(4.0)

    def test_deterministic(self):
        rng = np.random.default_rng(9)
        x, y = rng.normal(size=30), rng.normal(size=25)
        assert mannwhitneyu(x, y) == mannwhitneyu(x, y)


class TestLogisticGD:
    def test_recovers_separable_direction(self):
        rng = np.random.default_rng(13)
        x = rng.normal(size=300)
        y = (x + rng.normal(scale=0.3, size=300) > 0).astype(float)
        X = np.column_stack([np.ones(300), x])
        fit = logistic_gd(X, y, lr=0.5, iters=50000)
        assert fit.beta[1] > 2.0  # strongly positive coefficient
        # fitted model classifies training data well
        z = X @ np.array(fit.beta)
        pred = (1.0 / (1.0 + np.exp(-z))) > 0.5
        assert (pred == y.astype(bool)).mean() > 0.85

    def test_quadratic_peak(self):
        # True model: logit = -(z)^2 -> peak at x=0.
        x = np.linspace(-3, 3, 200)
        rng = np.random.default_rng(17)
        p = np.exp(-(x**2)) / (1 + np.exp(-(x**2)))
        y = (rng.uniform(size=200) < p).astype(float)
        X = np.column_stack([np.ones(200), x, x**2])
        fit = logistic_gd(X, y, lr=0.5, iters=200000)
        b1, b2 = fit.beta[1], fit.beta[2]
        assert b2 < 0
        peak = -b1 / (2 * b2)
        assert peak == pytest.approx(0.0, abs=0.5)

    def test_deterministic(self):
        rng = np.random.default_rng(19)
        X = np.column_stack([np.ones(50), rng.normal(size=50)])
        y = (rng.uniform(size=50) < 0.5).astype(float)
        f1 = logistic_gd(X, y, lr=0.3, iters=5000)
        f2 = logistic_gd(X, y, lr=0.3, iters=5000)
        assert f1 == f2
