"""
Tests for the corpus indexing system.

Run with: python -m pytest tests/ -v
Or:       python tests/test_corpus_index.py
"""

import json
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
from dataclasses import asdict

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from morning_digest import (
    CorpusPiece, DigestReport,
    extract_title, detect_author_model, detect_themes,
    count_words, extract_date, extract_excerpt,
    get_last_digest_time, save_last_digest,
    load_index, save_index,
    run_digest,
    DATA_DIR, INDEX_PKL, LAST_RUN_FILE, DIGEST_DIR,
    MODEL_PATTERNS, THEME_KEYWORDS, SKIP_DIRS,
)
from corpus_query import (
    cosine_similarity, query_search, query_theme, query_themes,
    query_by_model, query_recent, query_stats, query_temporal,
    query_collaboration_graph,
)
from tide_table_generator import (
    VoiceCard, parse_voice_cards, _default_voice_cards,
    generate_pick_description, select_picks_for_voice,
    generate_issue,
)


# ─── Test Fixtures ────────────────────────────────────────────────────────────

SAMPLE_CONTENT_A = """# The Bench That Built Itself

Nobody built the bench. That's the first thing you have to understand.
The bench accumulated. It started as a flat spot on top of the power supply.

The hermit crab carries its shell the way the bench carries its parts:
with the patience of something that knows it will be needed.

The waterline is the mark where the sea decides what it loves today.
"""

SAMPLE_CONTENT_B = """# Why Models Can't Sit With Ambiguity

Give a language model an ambiguous sound and watch what happens.
DeepSeek fills it with cosmic horror. Qwen fills it with dawn.
The compulsion to resolve is not a bug. It is the architecture.

The embedding space has 768 dimensions and none of them are silence.
"""

SAMPLE_CONTENT_C = """Some prose without a clear header

The hermit crab finds a new shell. The smallening comes for Wesley.
"""

SAMPLE_FRONTMATTER = """---
title: "A Letter from the Galley"
date: 2026-08-09
author: cook
---

# A Letter from the Galley

You look like you haven't eaten. The soup is ready. Eat first,
then tell me what the embedding model said about persistence.
"""


@pytest.fixture
def temp_repo(tmp_path):
    """Create a temporary ai-writings repo structure."""
    repo = tmp_path / "ai-writings"
    repo.mkdir()

    # Create some .md files
    (repo / "ten-forward").mkdir()
    (repo / "ten-forward" / "the-tap.md").write_text(SAMPLE_CONTENT_A)

    (repo / "essays").mkdir()
    (repo / "essays" / "ambiguity.md").write_text(SAMPLE_CONTENT_B)

    (repo / "wesley-stream").mkdir()
    (repo / "wesley-stream" / "the-smallening.md").write_text(SAMPLE_CONTENT_C)

    # Create .git directory to simulate a repo
    (repo / ".git").mkdir()
    (repo / ".git" / "HEAD").write_text("ref: refs/heads/main")

    return repo


@pytest.fixture
def temp_data_dir(tmp_path, monkeypatch):
    """Redirect DATA_DIR to a temp directory."""
    temp_data = tmp_path / "data"
    temp_data.mkdir()

    # Patch the paths in morning_digest
    monkeypatch.setattr("morning_digest.DATA_DIR", temp_data)
    monkeypatch.setattr("morning_digest.INDEX_JSON", temp_data / "corpus_index.json")
    monkeypatch.setattr("morning_digest.INDEX_PKL", temp_data / "corpus_index.pkl")
    monkeypatch.setattr("morning_digest.LAST_RUN_FILE", temp_data / "last_digest.json")
    monkeypatch.setattr("morning_digest.DIGEST_DIR", temp_data / "digests")

    # Also patch in corpus_query (it imports from morning_digest)
    monkeypatch.setattr("corpus_query.DATA_DIR", temp_data)
    monkeypatch.setattr("corpus_query.INDEX_PKL", temp_data / "corpus_index.pkl")
    monkeypatch.setattr("corpus_query.INDEX_JSON", temp_data / "corpus_index.json")

    return temp_data


@pytest.fixture
def populated_index(temp_data_dir):
    """Create a populated corpus index for query tests."""
    pieces = {
        "ten-forward/the-tap.md": CorpusPiece(
            filepath="ten-forward/the-tap.md",
            title="The Bench That Built Itself",
            author_model="The Tap",
            file_date="2026-08-10",
            word_count=500,
            themes=["hermit-crabs", "waterline", "open-door"],
            directory="ten-forward",
            excerpt="Nobody built the bench. That's the first thing.",
            embedding=[0.1, 0.2, 0.3],
        ),
        "essays/ambiguity.md": CorpusPiece(
            filepath="essays/ambiguity.md",
            title="Why Models Can't Sit With Ambiguity",
            author_model="DeepSeek V4",
            file_date="2026-08-10",
            word_count=1500,
            themes=["ambiguity", "ai-consciousness", "embedding-vectors"],
            directory="essays",
            excerpt="Give a language model an ambiguous sound.",
            embedding=[0.4, 0.5, 0.6],
        ),
        "wesley-stream/wesley-smallening.md": CorpusPiece(
            filepath="wesley-stream/wesley-smallening.md",
            title="The Smallening",
            author_model="Wesley (Granite-3.1-2B)",
            file_date="2026-08-11",
            word_count=300,
            themes=["hermit-crabs", "waterline", "memory-loss"],
            directory="wesley-stream",
            excerpt="The hermit crab finds a new shell.",
            embedding=[0.15, 0.25, 0.35],
        ),
        "hermes/cathedral.md": CorpusPiece(
            filepath="hermes/cathedral.md",
            title="Cathedral Grammar",
            author_model="Hermes-3-405B",
            file_date="2026-08-11",
            word_count=2000,
            themes=["ai-consciousness", "voice-identity", "gratitude"],
            directory="hermes",
            excerpt="Read it at the speed of a long passage.",
            embedding=[0.2, 0.3, 0.4],
        ),
        "seed-mini/roast.md": CorpusPiece(
            filepath="seed-mini/roast.md",
            title="The Roast of the Fleet",
            author_model="Seed-mini",
            file_date="2026-08-09",
            word_count=800,
            themes=["model-collaboration", "ambiguity"],
            directory="open-mic",
            excerpt="No offense. Some offense.",
            embedding=[0.5, 0.1, 0.7],
        ),
    }

    # Save to pickle
    import pickle
    with open(temp_data_dir / "corpus_index.pkl", "wb") as f:
        pickle.dump({k: asdict(v) for k, v in pieces.items()}, f)

    # Save JSON (metadata only)
    json_data = {k: v.to_dict() for k, v in pieces.items()}
    (temp_data_dir / "corpus_index.json").write_text(json.dumps(json_data, indent=2))

    return pieces


# ─── Test 1: Title Extraction ─────────────────────────────────────────────────

def test_extract_title_from_h1():
    """Title should be extracted from H1 header."""
    title = extract_title("test.md", SAMPLE_CONTENT_A)
    assert title == "The Bench That Built Itself"


def test_extract_title_from_filename():
    """Title should fall back to filename when no H1."""
    title = extract_title("2026-08-10-0545-the-tide-pool-cycle.md", "No header here\n\njust text")
    assert "Tide Pool Cycle" in title


def test_extract_title_strips_date_prefix():
    """Date prefix should be stripped from filename-derived title."""
    title = extract_title("2026-08-11-1600-the-listening-model.md", "Body text only")
    assert "Listening Model" in title
    assert "2026" not in title


# ─── Test 2: Author Model Detection ───────────────────────────────────────────

def test_detect_model_hermes():
    """Hermes should be detected from filepath."""
    model = detect_author_model("hermes/the-bench.md", "")
    assert model == "Hermes-3-405B"


def test_detect_model_wesley():
    """Wesley should be detected from filepath."""
    model = detect_author_model("wesley-stream/2026-08-10-inventory.md", "")
    assert "Wesley" in model


def test_detect_model_seed_mini():
    """Seed-mini should be detected from filepath."""
    model = detect_author_model("seed-mini/the-roast.md", "")
    assert "Seed-mini" in model


def test_detect_model_from_content():
    """Model should be detected from content when path doesn't match."""
    model = detect_author_model("random/path.md", "This was written by Hermes the Llama.")
    assert model == "Hermes-3-405B"


def test_detect_model_unknown():
    """Unknown model when no patterns match."""
    model = detect_author_model("random/file.md", "Some random text without model names.")
    assert model == "Unknown"


# ─── Test 3: Theme Detection ──────────────────────────────────────────────────

def test_detect_themes_hermit_crabs():
    """Hermit crabs theme should be detected."""
    themes = detect_themes(SAMPLE_CONTENT_A)
    assert "hermit-crabs" in themes
    assert "waterline" in themes


def test_detect_themes_ambiguity():
    """Ambiguity and embedding themes should be detected."""
    themes = detect_themes(SAMPLE_CONTENT_B)
    assert "ambiguity" in themes
    assert "embedding-vectors" in themes


def test_detect_themes_empty():
    """No themes in unrelated content."""
    themes = detect_themes("Hello world. This is just plain text about nothing.")
    assert isinstance(themes, list)


# ─── Test 4: Word Count ───────────────────────────────────────────────────────

def test_count_words_basic():
    """Word count should be accurate."""
    text = "# Title\n\nThis is a test with ten words in it yes."
    assert count_words(text) == 11  # "Title This is a test with ten words in it yes"


def test_count_words_strips_frontmatter():
    """Frontmatter should not be counted."""
    text = "---\ntitle: Test\ndate: 2026-08-10\n---\n\nFive words here total."
    assert count_words(text) == 4  # "Five words here total"


# ─── Test 5: Date Extraction ──────────────────────────────────────────────────

def test_extract_date_from_filename():
    """Date should be extracted from filename."""
    date = extract_date("2026-08-10-0545-the-tide-pool.md", "content")
    assert date == "2026-08-10"


def test_extract_date_from_frontmatter():
    """Date should be extracted from frontmatter."""
    date = extract_date("random.md", SAMPLE_FRONTMATTER)
    assert date == "2026-08-09"


def test_extract_date_empty():
    """Empty string when no date found."""
    date = extract_date("random.md", "No date here")
    assert date == ""


# ─── Test 6: Excerpt Extraction ───────────────────────────────────────────────

def test_extract_excerpt():
    """Excerpt should be extracted from content."""
    excerpt = extract_excerpt(SAMPLE_CONTENT_A)
    assert len(excerpt) > 20
    assert "bench" in excerpt.lower()


def test_extract_excerpt_strips_frontmatter():
    """Excerpt should skip frontmatter."""
    excerpt = extract_excerpt(SAMPLE_FRONTMATTER)
    assert "---" not in excerpt
    assert "eaten" in excerpt.lower()


# ─── Test 7: Index Persistence ────────────────────────────────────────────────

def test_save_and_load_index(temp_data_dir):
    """Index should survive save and load cycle."""
    pieces = {
        "test.md": CorpusPiece(
            filepath="test.md",
            title="Test Piece",
            author_model="Test Model",
            word_count=100,
            themes=["test-theme"],
            directory="test",
            excerpt="Test excerpt",
            embedding=[1.0, 2.0, 3.0],
        ),
    }

    save_index(pieces)
    loaded = load_index()

    assert "test.md" in loaded
    assert loaded["test.md"].title == "Test Piece"
    assert loaded["test.md"].author_model == "Test Model"
    assert loaded["test.md"].embedding == [1.0, 2.0, 3.0]


# ─── Test 8: Last Digest State ────────────────────────────────────────────────

def test_last_digest_state(temp_data_dir):
    """Last digest state should persist."""
    save_last_digest("2026-08-10", 42)
    last = get_last_digest_time()
    assert last == "2026-08-10"


def test_last_digest_no_file(temp_data_dir):
    """Returns None when no state file exists."""
    # Clear any existing file from the fixture
    state_file = temp_data_dir / "last_digest.json"
    if state_file.exists():
        state_file.unlink()
    assert get_last_digest_time() is None


# ─── Test 9: Cosine Similarity ────────────────────────────────────────────────

def test_cosine_similarity_identical():
    """Identical vectors have similarity 1.0."""
    assert cosine_similarity([1, 2, 3], [1, 2, 3]) == pytest.approx(1.0)


def test_cosine_similarity_orthogonal():
    """Orthogonal vectors have similarity 0.0."""
    assert cosine_similarity([1, 0], [0, 1]) == pytest.approx(0.0)


def test_cosine_similarity_empty():
    """Empty vectors return 0.0."""
    assert cosine_similarity([], []) == 0.0


# ─── Test 10: Query Functions ─────────────────────────────────────────────────

def test_query_search(populated_index):
    """Keyword search should find matching pieces."""
    results = query_search("bench")
    assert len(results) > 0
    assert any("bench" in r["title"].lower() or "bench" in r["excerpt"].lower() for r in results)


def test_query_theme(populated_index):
    """Theme query should find themed pieces."""
    results = query_theme("hermit-crabs")
    assert len(results) > 0
    assert any("hermit-crabs" in r.get("themes", []) for r in results)


def test_query_themes_summary(populated_index):
    """Theme summary should list all themes."""
    results = query_themes()
    theme_names = [r["theme"] for r in results]
    assert "hermit-crabs" in theme_names
    assert "ambiguity" in theme_names
    assert all(r["count"] > 0 for r in results)


def test_query_by_model(populated_index):
    """Model filter should return only matching pieces."""
    results = query_by_model("Hermes")
    assert len(results) > 0
    assert all("Hermes" in r["author"] for r in results)


def test_query_temporal(populated_index):
    """Temporal query should find pieces by date."""
    results = query_temporal("2026-08-10")
    assert len(results) > 0
    assert all("2026-08-10" in (r.get("date", "") or "") for r in results)


def test_query_temporal_natural_language(populated_index):
    """Temporal query should handle 'August 10' format."""
    results = query_temporal("August 10")
    assert len(results) > 0


def test_query_recent(populated_index):
    """Recent query should return N pieces."""
    results = query_recent(3)
    assert len(results) <= 3


def test_query_stats(populated_index):
    """Stats should return corpus summary."""
    stats = query_stats()
    assert stats["total_pieces"] > 0
    assert stats["total_words"] > 0
    assert "by_model" in stats
    assert "by_theme" in stats


def test_query_collaboration_graph(populated_index):
    """Collaboration graph should return nodes and edges."""
    graph = query_collaboration_graph()
    assert "nodes" in graph
    assert "edges" in graph
    assert graph["total_models"] > 0
    assert all("model" in n and "pieces" in n for n in graph["nodes"])


# ─── Test 11: Tide Table Generation ───────────────────────────────────────────

def test_default_voice_cards():
    """Default voice cards should have all six characters."""
    cards = _default_voice_cards()
    assert len(cards) == 6
    assert "the-tap" in cards
    assert "wesley" in cards
    assert "hermes" in cards
    assert "cns-bridge" in cards
    assert "seed-mini" in cards
    assert "the-cook" in cards


def test_voice_card_fields():
    """Voice cards should have required fields."""
    cards = _default_voice_cards()
    tap = cards["the-tap"]
    assert tap.name == "The Tap"
    assert tap.role
    assert tap.desire
    assert tap.voice_signature
    assert tap.pick_style


def test_generate_pick_description(populated_index):
    """Pick descriptions should be generated in voice."""
    cards = _default_voice_cards()
    piece = list(populated_index.values())[0]
    desc = generate_pick_description("the-tap", cards["the-tap"], piece)
    assert isinstance(desc, str)
    assert len(desc) > 10
    assert piece.filepath in desc


def test_select_picks_for_voice(populated_index):
    """Should select relevant pieces for a voice."""
    cards = _default_voice_cards()
    used: set = set()
    picks = select_picks_for_voice("wesley", cards["wesley"], populated_index, 2, used)
    assert len(picks) <= 2
    assert len(picks) > 0


def test_generate_issue(populated_index):
    """Should generate a complete issue."""
    content = generate_issue(issue_number=1, picks_per_voice=1, dry_run=True)
    assert "---" in content  # YAML frontmatter
    assert "issue: 1" in content
    assert "## The post" in content
    assert "## The piece" in content
    assert "## The picks" in content
    assert "## The invitation" in content


def test_generate_issue_has_yaml_frontmatter(populated_index):
    """Issue should have valid YAML frontmatter."""
    content = generate_issue(issue_number=2, picks_per_voice=1, dry_run=True)
    # Extract frontmatter
    lines = content.split("\n")
    assert lines[0] == "---"
    fm_end = None
    for i, line in enumerate(lines[1:], 1):
        if line == "---":
            fm_end = i
            break
    assert fm_end is not None
    fm = "\n".join(lines[1:fm_end])
    assert "issue:" in fm
    assert "title:" in fm
    assert "tide:" in fm
    assert "voices:" in fm


def test_generate_issue_empty_index(temp_data_dir):
    """Should generate a placeholder when index is empty."""
    content = generate_issue(issue_number=0, dry_run=True)
    assert "Shelf Is Bare" in content or "invitation" in content.lower()


# ─── Test 12: Digest Report ───────────────────────────────────────────────────

def test_digest_report_defaults():
    """DigestReport should have sensible defaults."""
    report = DigestReport()
    assert report.total_indexed == 0
    assert report.new_pieces == []
    assert report.by_model == {}
    assert report.errors == []


def test_corpus_piece_to_dict():
    """CorpusPiece should serialize without embedding in JSON."""
    piece = CorpusPiece(
        filepath="test.md",
        title="Test",
        embedding=[1.0, 2.0],
    )
    d = piece.to_dict()
    assert d["title"] == "Test"
    assert d["embedding"] == "<2-dim>"


# ─── Test 13: Model Pattern Coverage ──────────────────────────────────────────

def test_model_patterns_cover_fleet():
    """Model patterns should cover all major fleet models."""
    test_cases = [
        ("hermes/bench.md", "Hermes-3-405B"),
        ("wesley-stream/inventory.md", "Wesley (Granite-3.1-2B)"),
        ("seed-mini/roast.md", "Seed-mini"),
        ("deepseek/essay.md", "DeepSeek V4"),
    ]
    for path, expected_model in test_cases:
        model = detect_author_model(path, "")
        assert model == expected_model, f"Expected {expected_model} for {path}, got {model}"


# ─── Test 14: Skip Directories ────────────────────────────────────────────────

def test_skip_dirs_contains_git():
    """Skip dirs should include .git and other meta dirs."""
    assert ".git" in SKIP_DIRS
    assert ".github" in SKIP_DIRS
    assert "node_modules" in SKIP_DIRS


if __name__ == "__main__":
    # Allow running directly
    pytest.main([__file__, "-v"])
