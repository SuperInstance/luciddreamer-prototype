"""
Offline tests for peer_consult.embeddings.

HashEmbedder only — no network, no Ollama. SHA-256 token hashing makes every
value here deterministic across machines.
"""

import math

import pytest

from peer_consult.embeddings import HashEmbedder, Zone, classify_zone, delta


class TestHashEmbedder:
    def test_deterministic(self):
        emb = HashEmbedder()
        text = "the tide comes in twice a day"
        assert emb.embed([text]) == emb.embed([text])
        assert HashEmbedder().embed([text]) == HashEmbedder(dim=256).embed([text])

    def test_l2_normalized(self):
        (vec,) = HashEmbedder().embed(["alpha bravo charlie delta echo"])
        assert math.sqrt(sum(x * x for x in vec)) == pytest.approx(1.0)

    def test_dim_respected(self):
        assert len(HashEmbedder(dim=64).embed(["hello world"])[0]) == 64

    def test_empty_text_is_zero_vector(self):
        (vec,) = HashEmbedder().embed(["!!! ---"])
        assert all(x == 0.0 for x in vec)

    def test_rejects_nonpositive_dim(self):
        with pytest.raises(ValueError):
            HashEmbedder(dim=0)


class TestDelta:
    def test_identical_texts_zero_delta(self):
        emb = HashEmbedder()
        (a,), (b,) = emb.embed(["same words here"]), emb.embed(["same words here"])
        assert delta(a, b) == pytest.approx(0.0)

    def test_disjoint_vocab_near_one(self):
        emb = HashEmbedder()
        a_text = " ".join(f"answord{i:02d}" for i in range(30))
        b_text = " ".join(f"critword{i:02d}" for i in range(30))
        (a, b) = emb.embed([a_text, b_text])
        d = delta(a, b)
        assert d > 0.80  # hash collisions may shave it below 1.0, never below CHAOTIC

    def test_zero_vector_is_maximally_distant(self):
        assert delta([0.0, 0.0], [1.0, 0.0]) == 1.0

    def test_known_cosine(self):
        # orthogonal unit vectors → Δ = 1; identical unit vectors → Δ = 0
        assert delta([1.0, 0.0], [0.0, 1.0]) == pytest.approx(1.0)
        assert delta([0.6, 0.8], [0.6, 0.8]) == pytest.approx(0.0)


class TestClassifyZone:
    @pytest.mark.parametrize("d,expected", [
        (0.0, Zone.STALE),
        (0.199, Zone.STALE),
        (0.20, Zone.TRANSITIONAL_LOW),
        (0.399, Zone.TRANSITIONAL_LOW),
        (0.40, Zone.CREATIVE),
        (0.60, Zone.CREATIVE),
        (0.600001, Zone.TRANSITIONAL_HIGH),
        (0.80, Zone.TRANSITIONAL_HIGH),
        (0.800001, Zone.CHAOTIC),
        (1.0, Zone.CHAOTIC),
    ])
    def test_bands(self, d, expected):
        assert classify_zone(d) is expected
