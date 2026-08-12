"""End-to-end report generation tests."""

from pathlib import Path

from arena_proofs.report import generate_report


def test_generate_report_end_to_end(tmp_path: Path):
    out = tmp_path / "PROOF-REPORT.md"
    md = generate_report(out_path=out)
    assert out.exists()
    text = out.read_text()
    assert text == md
    # claims table lists all five claims with a verdict
    for claim in (
        "conservation",
        "Creative zone",
        "Post-molt",
        "Zone inversion",
        "Holographic",
    ):
        assert claim in text
    for verdict in ("PARTIAL", "REFUTED", "UNTESTABLE"):
        assert verdict in text
    for section in (
        "Claims audit",
        "C1",
        "C2",
        "C3",
        "New instrumentation needed",
        "cycle_id",
        "TileField",
    ):
        assert section in text
    # spot-check recomputed numbers appear
    assert "0.968" in text  # zone-inversion Pearson
    assert "1.148" in text or "1.147" in text  # conservation drift


def test_report_deterministic(tmp_path: Path):
    a = generate_report(out_path=tmp_path / "a.md")
    b = generate_report(out_path=tmp_path / "b.md")
    assert a == b
