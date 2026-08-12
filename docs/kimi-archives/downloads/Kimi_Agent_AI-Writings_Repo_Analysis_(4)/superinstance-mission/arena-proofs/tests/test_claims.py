"""Smoke + stability tests on the claims audit (bundled offline data)."""

import pytest

from arena_proofs.claims_audit import (
    ClaimVerdict,
    Verdict,
    audit_all,
    check_conservation,
    check_creative_zone,
    check_holographic,
    check_post_molt,
    check_zone_inversion,
)


def test_audit_returns_five_typed_verdicts():
    verdicts = audit_all()
    assert len(verdicts) == 5
    for v in verdicts:
        assert isinstance(v, ClaimVerdict)
        assert isinstance(v.verdict, Verdict)
        assert v.summary


def test_verdicts_are_stable():
    expected = {
        "conservation": Verdict.PARTIAL,
        "creative": Verdict.REFUTED,
        "post-molt": Verdict.UNTESTABLE,
        "inversion": Verdict.PARTIAL,
        "holographic": Verdict.PARTIAL,
    }
    for v in audit_all():
        for key, want in expected.items():
            if key in v.claim.lower():
                assert v.verdict is want, f"{v.claim}: {v.verdict} != {want}"


def test_conservation_numbers():
    v = check_conservation()
    e = v.evidence
    assert e["std_of_means"] == pytest.approx(0.00096, abs=0.0002)
    assert e["seed_invariant"] is True
    assert e["additive_drift_start"] == pytest.approx(1.020, abs=0.005)
    assert e["additive_drift_end"] == pytest.approx(1.148, abs=0.005)
    assert e["strict_form_conserved"] is False


def test_creative_zone_flat():
    v = check_creative_zone()
    e = v.evidence
    assert e["eval_wr_min"] == pytest.approx(0.648, abs=0.005)
    assert e["eval_wr_max"] == pytest.approx(0.712, abs=0.005)
    assert e["flat_range"] < 0.10
    assert e["has_inverted_u"] is False


def test_post_molt_untestable_with_spec():
    v = check_post_molt()
    assert v.verdict is Verdict.UNTESTABLE
    assert v.evidence["shed_event_keys_found"] == []
    spec = v.evidence["instrumentation_spec"]
    assert "cycle_id" in spec and "TileField" in spec and "shed" in spec


def test_zone_inversion_outlier_driven():
    v = check_zone_inversion()
    e = v.evidence
    assert e["n_points"] == 21
    assert e["pearson_all"] == pytest.approx(-0.968, abs=0.005)
    assert e["spearman_all"] == pytest.approx(-0.429, abs=0.005)
    assert e["spearman_perm_p_all"] == pytest.approx(0.053, abs=0.01)
    # dropping the sparse-reward outlier destroys the rank correlation
    assert abs(e["spearman_excl_sparse"]) < 0.15
    assert e["outlier_driven"] is True


def test_holographic_direction_not_magnitude():
    v = check_holographic()
    e = v.evidence
    assert e["sqrt_N"] == pytest.approx(40.0)
    assert e["pct_of_full_at_sqrt_N"] >= 95.0
    assert e["direction_supported"] is True
    assert e["minimum_95pct_file"] == 5.0
    assert e["saturation_c_fit"] < 10.0  # fitted c is ~3, not ~40
    assert e["strategy_clusters"] == [7.0, 10.0, 14.0]
    assert 0.0 < e["cluster_growth_exponent"] < 0.5  # sublinear, not sqrt(N)
