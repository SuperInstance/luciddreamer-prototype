"""Build and incrementally update the corpus index.

Schema (per SPEC):
  pieces(id INTEGER PK, path TEXT UNIQUE, title TEXT, series TEXT,
         directory TEXT, persona TEXT, mtime REAL, body TEXT)
  pieces_fts — FTS5 virtual table (title, body), content-synced to pieces
  embeddings(piece_id, vector BLOB float32) — only when an Embedder is given

Incremental: a file is skipped when its (path, mtime) already matches the row
in ``pieces``.

FTS5: we use SQLite's FTS5 (verified available on the target Pythons). If a
build of SQLite without FTS5 is ever encountered, ``build_index`` raises a
clear error at open time — see README for the fallback note.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from .embeddings import Embedder, pack_vector

SCHEMA = """
CREATE TABLE IF NOT EXISTS pieces(
    id INTEGER PRIMARY KEY,
    path TEXT UNIQUE,
    title TEXT,
    series TEXT,
    directory TEXT,
    persona TEXT,
    mtime REAL,
    body TEXT
);
CREATE VIRTUAL TABLE IF NOT EXISTS pieces_fts USING fts5(
    title, body, content='pieces', content_rowid='id'
);
CREATE TRIGGER IF NOT EXISTS pieces_ai AFTER INSERT ON pieces BEGIN
    INSERT INTO pieces_fts(rowid, title, body) VALUES (new.id, new.title, new.body);
END;
CREATE TRIGGER IF NOT EXISTS pieces_ad AFTER DELETE ON pieces BEGIN
    INSERT INTO pieces_fts(pieces_fts, rowid, title, body)
        VALUES ('delete', old.id, old.title, old.body);
END;
CREATE TRIGGER IF NOT EXISTS pieces_au AFTER UPDATE ON pieces BEGIN
    INSERT INTO pieces_fts(pieces_fts, rowid, title, body)
        VALUES ('delete', old.id, old.title, old.body);
    INSERT INTO pieces_fts(rowid, title, body) VALUES (new.id, new.title, new.body);
END;
CREATE TABLE IF NOT EXISTS embeddings(
    piece_id INTEGER PRIMARY KEY REFERENCES pieces(id) ON DELETE CASCADE,
    vector BLOB
);
"""

_SERIES_RE = re.compile(r"^(\d+)-")
_HEADING_RE = re.compile(r"^#\s+(.+?)\s*$")

# Explicit persona mapping table (path-driven, per SPEC).
# 1) Directory segment -> fixed persona.
_DIR_PERSONA = {
    "wesley-stream": "wesley",
    "qwen-stream": "qwen",
}
# 2) Directories whose files take their persona from the leading name token
#    of the filename: ensemble/<name>-*.md, model-portraits/*.md,
#    fetch-riffs/*.md. Numeric tokens (dates, series numbers) are skipped.
_PREFIX_PERSONA_DIRS = ("ensemble", "model-portraits", "fetch-riffs")


def _first_name_token(stem: str) -> str | None:
    """First non-numeric hyphen/underscore token of a filename stem."""
    for tok in re.split(r"[-_]", stem.lower()):
        if tok and not tok.isdigit():
            return tok
    return None


def persona_for_path(rel_path: Path) -> str | None:
    """Map a corpus-relative path to a persona, or None (explicit fallback).

    Rules (path segments, checked in order):
      wesley-stream/**          -> "wesley"
      qwen-stream/**            -> "qwen"
      ensemble/<name>-*.md      -> "<name>"
      model-portraits/*.md      -> leading name token of the filename
      fetch-riffs/*.md          -> leading name token of the filename
    """
    parts = rel_path.parts
    for seg in parts[:-1]:
        if seg in _DIR_PERSONA:
            return _DIR_PERSONA[seg]
    parent = rel_path.parent.name
    if parent == "ensemble":
        # ensemble/<name>-* — persona is the token before the first dash.
        return _first_name_token(rel_path.stem)
    if parent in ("model-portraits", "fetch-riffs"):
        return _first_name_token(rel_path.stem)
    return None


def series_for_path(rel_path: Path) -> str | None:
    """Series = leading ``NN-`` filename prefix, else the directory name,
    else None for loose root files."""
    m = _SERIES_RE.match(rel_path.name)
    if m:
        return m.group(1)
    directory = str(rel_path.parent)
    if directory in (".", ""):
        return None
    return rel_path.parent.name


def title_from_body(body: str, stem: str) -> str:
    """Title = first markdown H1, else first non-empty line, else the stem."""
    for line in body.splitlines():
        m = _HEADING_RE.match(line)
        if m:
            return m.group(1)
    for line in body.splitlines():
        if line.strip():
            return line.strip()[:200]
    return stem


@dataclass(frozen=True)
class IndexStats:
    total_files: int
    indexed: int
    skipped: int
    embedded: int
    db_path: str


def connect(db_path: Path | str) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


def _check_fts5(conn: sqlite3.Connection) -> None:
    try:
        conn.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS _fts5_probe USING fts5(x)"
        )
        conn.execute("DROP TABLE IF EXISTS _fts5_probe")
    except sqlite3.OperationalError as exc:  # pragma: no cover - env-dependent
        raise RuntimeError(
            "SQLite FTS5 is unavailable in this Python build; corpus-compass "
            "requires FTS5 (see README for the BM25 fallback note)."
        ) from exc


def build_index(
    corpus_dir: Path,
    db_path: Path,
    *,
    embeddings: Embedder | None = None,
) -> IndexStats:
    """Index every .md file under corpus_dir into db_path (incremental)."""
    corpus_dir = Path(corpus_dir)
    db_path = Path(db_path)
    conn = connect(db_path)
    _check_fts5(conn)

    files = sorted(corpus_dir.rglob("*.md"))
    known = {
        row[0]: row[1]
        for row in conn.execute("SELECT path, mtime FROM pieces")
    }

    indexed = 0
    skipped = 0
    to_embed: list[tuple[int, str]] = []

    for fpath in files:
        rel = fpath.relative_to(corpus_dir)
        rel_posix = rel.as_posix()
        mtime = fpath.stat().st_mtime
        if known.get(rel_posix) == mtime:
            skipped += 1
            continue

        body = fpath.read_text(encoding="utf-8", errors="replace")
        title = title_from_body(body, rel.stem)
        series = series_for_path(rel)
        directory = str(rel.parent)
        persona = persona_for_path(rel)

        row = conn.execute(
            "SELECT id FROM pieces WHERE path = ?", (rel_posix,)
        ).fetchone()
        if row is None:
            cur = conn.execute(
                "INSERT INTO pieces(path, title, series, directory, persona,"
                " mtime, body) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (rel_posix, title, series, directory, persona, mtime, body),
            )
            piece_id = cur.lastrowid
        else:
            piece_id = row[0]
            conn.execute(
                "UPDATE pieces SET title=?, series=?, directory=?, persona=?,"
                " mtime=?, body=? WHERE id=?",
                (title, series, directory, persona, mtime, body, piece_id),
            )
        indexed += 1
        if embeddings is not None:
            to_embed.append((piece_id, body))

    embedded = 0
    if embeddings is not None and to_embed:
        texts = [body for _, body in to_embed]
        vectors = embeddings.embed(texts)
        if len(vectors) != len(to_embed):
            raise ValueError(
                f"embedder returned {len(vectors)} vectors for"
                f" {len(to_embed)} texts"
            )
        for (piece_id, _), vec in zip(to_embed, vectors):
            conn.execute(
                "INSERT OR REPLACE INTO embeddings(piece_id, vector)"
                " VALUES (?, ?)",
                (piece_id, pack_vector(vec)),
            )
            embedded += 1

    # Drop rows for files that vanished from the corpus.
    seen = {f.relative_to(corpus_dir).as_posix() for f in files}
    stale = [p for p in known if p not in seen]
    for path in stale:
        conn.execute("DELETE FROM pieces WHERE path = ?", (path,))

    conn.commit()
    conn.close()
    return IndexStats(
        total_files=len(files),
        indexed=indexed,
        skipped=skipped,
        embedded=embedded,
        db_path=str(db_path),
    )
