"""CLI smoke tests: index -> search -> digest, all offline."""

from pathlib import Path

from corpus_compass.cli import main


def test_cli_index_and_search(corpus_dir, tmp_path, capsys):
    db = tmp_path / "cli.db"
    rc = main(["index", str(corpus_dir), "--db", str(db)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "indexed 10" in out

    rc = main(["search", "anchor", "--db", str(db), "-k", "3"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "essays/the-anchor-chain.md" in out
    assert "The Anchor Chain" in out


def test_cli_search_no_results(corpus_dir, tmp_path, capsys):
    db = tmp_path / "cli.db"
    main(["index", str(corpus_dir), "--db", str(db)])
    capsys.readouterr()
    rc = main(["search", "zzzzqqq", "--db", str(db)])
    assert rc == 0
    assert "no results" in capsys.readouterr().err


def test_cli_digest(tmp_corpus, tmp_path, capsys, monkeypatch):
    db = tmp_path / "cli.db"
    repo = tmp_corpus.parent
    main(["index", str(tmp_corpus), "--db", str(db)])
    capsys.readouterr()

    from corpus_compass import digest as digest_mod

    monkeypatch.setattr(
        digest_mod,
        "default_git_runner",
        lambda repo_dir: lambda args: "corpus/essays/the-anchor-chain.md\n",
    )
    rc = main(["digest", str(repo), "--db", str(db), "--since", "24 hours ago"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "# The Corpus Indexes Itself" in out
    assert "The Anchor Chain" in out
