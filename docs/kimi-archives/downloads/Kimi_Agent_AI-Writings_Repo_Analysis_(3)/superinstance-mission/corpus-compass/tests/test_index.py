"""Index building: schema, incremental behavior, persona/series mapping."""

import os
import sqlite3
import time
from pathlib import Path

import pytest

from corpus_compass.embeddings import HashEmbedder
from corpus_compass.index import (
    build_index,
    persona_for_path,
    series_for_path,
    title_from_body,
)


def test_build_index_full(corpus_dir, db_path):
    stats = build_index(corpus_dir, db_path)
    assert stats.total_files == 10
    assert stats.indexed == 10
    assert stats.skipped == 0
    assert stats.embedded == 0

    conn = sqlite3.connect(str(db_path))
    rows = conn.execute(
        "SELECT path, title, series, directory, persona FROM pieces"
    ).fetchall()
    assert len(rows) == 10
    by_path = {r[0]: r for r in rows}

    assert by_path["wesley-stream/03-the-ensign-counts.md"][4] == "wesley"
    assert by_path["qwen-stream/01-lantern-on-the-water.md"][4] == "qwen"
    assert by_path["ensemble/deepseek-tide-tables.md"][4] == "deepseek"
    assert by_path["ensemble/hermes-six-voices.md"][4] == "hermes"
    assert by_path["model-portraits/deepseek-v3-barnacles.md"][4] == "deepseek"
    assert by_path["fetch-riffs/glm-guardrail-riff.md"][4] == "glm"
    assert by_path["essays/the-anchor-chain.md"][4] is None

    # series: leading NN- prefix else directory name else None
    assert by_path["00-the-tide-remembers.md"][2] == "00"
    assert by_path["wesley-stream/03-the-ensign-counts.md"][2] == "03"
    assert by_path["essays/the-anchor-chain.md"][2] == "essays"

    # title comes from the first H1
    assert by_path["00-the-tide-remembers.md"][1] == "The Tide Remembers"
    conn.close()


def test_incremental_reindex_skips_unchanged(tmp_corpus, db_path):
    stats1 = build_index(tmp_corpus, db_path)
    assert stats1.indexed == 10

    stats2 = build_index(tmp_corpus, db_path)
    assert stats2.indexed == 0
    assert stats2.skipped == 10

    # touch one file: mtime changes -> exactly one re-indexed
    target = tmp_corpus / "essays" / "the-anchor-chain.md"
    target.write_text(target.read_text() + "\nOne more link in the chain.\n")
    stats3 = build_index(tmp_corpus, db_path)
    assert stats3.indexed == 1
    assert stats3.skipped == 9

    conn = sqlite3.connect(str(db_path))
    body = conn.execute(
        "SELECT body FROM pieces WHERE path = 'essays/the-anchor-chain.md'"
    ).fetchone()[0]
    assert "One more link" in body
    # FTS stays content-synced after update
    fts_hits = conn.execute(
        "SELECT COUNT(*) FROM pieces_fts WHERE pieces_fts MATCH '\"link\"'"
    ).fetchone()[0]
    assert fts_hits == 1
    conn.close()


def test_deleted_file_removed_from_index(tmp_corpus, db_path):
    build_index(tmp_corpus, db_path)
    (tmp_corpus / "essays" / "ballast-and-buoyancy.md").unlink()
    stats = build_index(tmp_corpus, db_path)
    assert stats.total_files == 9
    conn = sqlite3.connect(str(db_path))
    n = conn.execute("SELECT COUNT(*) FROM pieces").fetchone()[0]
    assert n == 9
    hits = conn.execute(
        "SELECT COUNT(*) FROM pieces_fts WHERE pieces_fts MATCH 'ballast'"
    ).fetchone()[0]
    assert hits == 0
    conn.close()


def test_embeddings_table_only_with_embedder(corpus_dir, db_path, tmp_path):
    build_index(corpus_dir, db_path)
    conn = sqlite3.connect(str(db_path))
    assert conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0] == 0
    conn.close()

    db2 = tmp_path / "with_embed.db"
    stats = build_index(corpus_dir, db2, embeddings=HashEmbedder(dim=64))
    assert stats.embedded == 10
    conn = sqlite3.connect(str(db2))
    rows = conn.execute("SELECT piece_id, vector FROM embeddings").fetchall()
    assert len(rows) == 10
    assert all(len(blob) == 64 * 4 for _, blob in rows)  # float32
    conn.close()


def test_persona_mapping_table():
    assert persona_for_path(Path("wesley-stream/01-x.md")) == "wesley"
    assert persona_for_path(Path("deep/wesley-stream/x.md")) == "wesley"
    assert persona_for_path(Path("qwen-stream/01-x.md")) == "qwen"
    assert persona_for_path(Path("ensemble/deepseek-foo.md")) == "deepseek"
    assert persona_for_path(Path("ensemble/CLAUDE-synth.md")) == "claude"
    assert persona_for_path(Path("model-portraits/deepseek-v3-x.md")) == "deepseek"
    assert persona_for_path(Path("model-portraits/2026-05-21-four-models.md")) == "four"
    assert persona_for_path(Path("fetch-riffs/glm-riff.md")) == "glm"
    assert persona_for_path(Path("essays/plain.md")) is None
    assert persona_for_path(Path("loose.md")) is None


def test_series_mapping():
    assert series_for_path(Path("538-what-the-current-knows.md")) == "538"
    assert series_for_path(Path("essays/plain.md")) == "essays"
    assert series_for_path(Path("plain.md")) is None


def test_title_fallbacks():
    assert title_from_body("# Heading\n\nbody", "stem") == "Heading"
    assert title_from_body("no heading here\nsecond line", "stem") == "no heading here"
    assert title_from_body("\n\n", "the-stem") == "the-stem"
