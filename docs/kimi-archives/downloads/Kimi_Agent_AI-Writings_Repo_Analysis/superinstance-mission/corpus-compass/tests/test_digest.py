"""Digest: 'The Corpus Indexes Itself' morning briefing with fake git_runner."""

import os
import subprocess
import time
from pathlib import Path

import pytest

from corpus_compass.digest import default_git_runner, generate_digest, parse_since
from corpus_compass.index import build_index

NOW = time.time()


def fake_git_runner(changed_lines: list[str]):
    def _run(args: list[str]) -> str:
        assert args[:1] == ["log"]
        return "\n".join(changed_lines) + "\n"

    return _run


@pytest.fixture()
def repo(tmp_corpus, db_path):
    """repo_dir whose content lives under corpus/ (like AI-Writings)."""
    repo_dir = tmp_corpus.parent
    build_index(tmp_corpus, db_path)
    return repo_dir


def test_digest_contains_all_new_files_and_sections(repo, db_path):
    runner = fake_git_runner(
        [
            "",
            "corpus/wesley-stream/03-the-ensign-counts.md",
            "corpus/essays/the-anchor-chain.md",
            "corpus/README.txt",  # not .md -> filtered
            "site/index.md",  # not under content dir -> filtered
        ]
    )
    md = generate_digest(
        repo, db_path, since="24 hours ago", git_runner=runner, now=NOW
    )

    assert md.startswith("# The Corpus Indexes Itself — ")
    for section in ("## Night's Catch", "## New Voices", "## Threads to Pull", "## Numbers"):
        assert section in md

    assert "wesley-stream/03-the-ensign-counts.md" in md
    assert "essays/the-anchor-chain.md" in md
    assert "The Ensign Counts the Stars" in md  # title from the index
    assert "The Anchor Chain" in md
    assert "README.txt" not in md
    assert "site/index.md" not in md

    # grouped by directory
    assert "### wesley-stream" in md
    assert "### essays" in md


def test_digest_threads_pull_archive_neighbors(repo, db_path):
    # The anchor-chain essay is "new"; ballast-and-buoyancy shares its
    # FTS neighborhood ("anchor") and is old -> a thread to pull.
    runner = fake_git_runner(["corpus/essays/the-anchor-chain.md"])
    md = generate_digest(
        repo, db_path, since="24 hours ago", git_runner=runner, now=NOW
    )
    assert "essays/ballast-and-buoyancy.md" in md
    assert "Threads to Pull" in md


def test_digest_new_voices(repo, db_path):
    # Backdate every wesley piece so 'wesley' is NOT a new voice,
    # while 'qwen' (only new file) IS.
    old = NOW - 10 * 86400
    for f in (repo / "corpus" / "wesley-stream").glob("*.md"):
        os.utime(f, (old, old))
    build_index(repo / "corpus", db_path)

    runner = fake_git_runner(
        [
            "corpus/wesley-stream/07-night-watch.md",
            "corpus/qwen-stream/01-lantern-on-the-water.md",
        ]
    )
    md = generate_digest(
        repo, db_path, since="1 days ago", git_runner=runner, now=NOW
    )
    new_voices = md.split("## New Voices")[1].split("## Threads to Pull")[0]
    assert "**qwen**" in new_voices
    assert "**wesley**" not in new_voices


def test_digest_writes_out_path(repo, db_path, tmp_path):
    runner = fake_git_runner(["corpus/essays/the-anchor-chain.md"])
    out = tmp_path / "briefing.md"
    md = generate_digest(
        repo, db_path, since="24 hours ago", git_runner=runner,
        out_path=out, now=NOW,
    )
    assert out.read_text() == md


def test_digest_works_without_index(repo, tmp_path):
    missing_db = tmp_path / "nope.db"
    runner = fake_git_runner(["corpus/essays/the-anchor-chain.md"])
    md = generate_digest(
        repo, missing_db, since="24 hours ago", git_runner=runner, now=NOW
    )
    # titles fall back to reading the file from disk
    assert "The Anchor Chain" in md
    assert "Total pieces in index: 0" in md
    assert not missing_db.exists()


def test_digest_empty_catch(repo, db_path):
    runner = fake_git_runner([])
    md = generate_digest(
        repo, db_path, since="24 hours ago", git_runner=runner, now=NOW
    )
    assert "_Nothing new surfaced overnight._" in md
    assert "New pieces: 0" in md


def test_digest_empty_repo_no_commits(tmp_path):
    """A real `git init` repo with ZERO commits must yield an empty catch,
    not a CalledProcessError."""
    repo_dir = tmp_path / "fresh"
    repo_dir.mkdir()
    subprocess.run(
        ["git", "init", str(repo_dir)], check=True, capture_output=True
    )
    md = generate_digest(
        repo_dir,
        tmp_path / "no.db",
        since="24 hours ago",
        now=NOW,  # default git_runner used
    )
    assert "_Nothing new surfaced overnight._" in md
    assert "New pieces: 0" in md


def test_default_git_runner_other_errors_still_raise(tmp_path):
    """A directory that is not a git repo at all must still raise."""
    not_a_repo = tmp_path / "plain"
    not_a_repo.mkdir()
    runner = default_git_runner(not_a_repo)
    with pytest.raises(subprocess.CalledProcessError):
        runner(["log", "--pretty=format:"])


def test_parse_since_relative():
    now = 1_000_000.0
    assert parse_since("24 hours ago", now=now) == now - 24 * 3600
    assert parse_since("1 day ago", now=now) == now - 86400
    assert parse_since("2 weeks ago", now=now) == now - 2 * 604800
    assert parse_since("30 minutes ago", now=now) == now - 1800


def test_parse_since_iso_and_timestamp():
    ts = parse_since("2026-01-01")
    assert ts > 0
    assert parse_since(str(ts)) == pytest.approx(ts)


def test_parse_since_garbage_raises():
    with pytest.raises(ValueError, match="cannot parse"):
        parse_since("whenever")
