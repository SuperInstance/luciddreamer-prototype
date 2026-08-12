"""
Offline tests for the peer-consult CLI — --mock mode only.
"""

from peer_consult.cli import _parse_model_map, main


class TestMockMode:
    def test_mock_run_prints_verdict(self, capsys):
        rc = main(["intent_parse", "summarize the tide log", "--mock"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "verdict:" in out
        assert "primary:  SEED_MINI" in out
        assert "critic:   GLM_5_2" in out
        assert "swmidi (24 bytes)" in out

    def test_mock_mode_is_deterministic(self, capsys):
        main(["voice", "narrate the fog", "--mock"])
        first = capsys.readouterr().out
        main(["voice", "narrate the fog", "--mock"])
        second = capsys.readouterr().out
        assert first == second


class TestModelMapParsing:
    def test_pairs(self):
        assert _parse_model_map(["primary=granite3.1:2b", "SEED_MINI=qwen:0.5b"]) == {
            "primary": "granite3.1:2b",
            "SEED_MINI": "qwen:0.5b",
        }

    def test_bad_pair_exits(self):
        import pytest
        with pytest.raises(SystemExit):
            _parse_model_map(["no-equals-sign"])
