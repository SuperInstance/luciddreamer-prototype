"""FTS5 BM25 search + cosine vibe_search."""

import pytest

from corpus_compass.embeddings import HashEmbedder
from corpus_compass.index import build_index
from corpus_compass.search import search, vibe_search


@pytest.fixture()
def indexed_db(corpus_dir, db_path):
    build_index(corpus_dir, db_path)
    return db_path


@pytest.fixture()
def embedded_db(corpus_dir, tmp_path):
    db = tmp_path / "embedded.db"
    build_index(corpus_dir, db, embeddings=HashEmbedder(dim=128))
    return db


def test_search_ranking_sanity(indexed_db):
    results = search(indexed_db, "anchor", k=5)
    assert results, "expected hits for 'anchor'"
    # both essays mention anchors; the anchor-chain essay is anchor-saturated
    assert results[0].path == "essays/the-anchor-chain.md"
    assert results[0].title == "The Anchor Chain"
    paths = [r.path for r in results]
    assert "essays/ballast-and-buoyancy.md" in paths


def test_search_scores_positive_and_ordered(indexed_db):
    results = search(indexed_db, "tide", k=10)
    assert len(results) >= 3
    scores = [r.score for r in results]
    assert all(s > 0 for s in scores)
    assert scores == sorted(scores, reverse=True)


def test_search_snippet_marks_match(indexed_db):
    results = search(indexed_db, "lantern", k=3)
    assert results
    assert ">>>" in results[0].snippet and "<<<" in results[0].snippet
    assert results[0].path == "qwen-stream/01-lantern-on-the-water.md"
    assert results[0].persona == "qwen"


def test_search_multiword_or(indexed_db):
    results = search(indexed_db, "barnacles guardrail", k=10)
    paths = {r.path for r in results}
    assert "model-portraits/deepseek-v3-barnacles.md" in paths
    assert "fetch-riffs/glm-guardrail-riff.md" in paths


def test_search_no_tokens_returns_empty(indexed_db):
    assert search(indexed_db, "!!! ---", k=5) == []


def test_search_no_match_returns_empty(indexed_db):
    assert search(indexed_db, "zyxwvut", k=5) == []


def test_vibe_search_finds_similar(embedded_db):
    embedder = HashEmbedder(dim=128)
    results = vibe_search(
        embedded_db,
        # query in the document's own vocabulary (HashEmbedder has no stemming)
        "anchor chain iron promise harbor return",
        k=3,
        embedder=embedder,
    )
    assert results
    assert results[0].path == "essays/the-anchor-chain.md"
    assert all(isinstance(r.score, float) for r in results)
    assert results[0].score >= results[-1].score


def test_vibe_search_respects_k(embedded_db):
    embedder = HashEmbedder(dim=128)
    results = vibe_search(embedded_db, "tide", k=4, embedder=embedder)
    assert len(results) == 4


def test_vibe_search_requires_embedder(embedded_db):
    with pytest.raises(ValueError):
        vibe_search(embedded_db, "tide", k=4, embedder=None)


def test_vibe_search_empty_without_embeddings(indexed_db):
    embedder = HashEmbedder(dim=128)
    assert vibe_search(indexed_db, "tide", k=4, embedder=embedder) == []


def test_hash_embedder_deterministic():
    h1 = HashEmbedder(dim=64)
    h2 = HashEmbedder(dim=64)
    assert h1.embed(["the tide remembers"]) == h2.embed(["the tide remembers"])
