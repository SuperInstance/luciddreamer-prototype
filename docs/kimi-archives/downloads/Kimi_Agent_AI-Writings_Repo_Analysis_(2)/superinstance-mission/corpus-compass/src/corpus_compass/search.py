"""Search the corpus index: FTS5 BM25 keyword search + cosine vibe search."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from .embeddings import Embedder, cosine, unpack_vector
from .index import connect

_TOKEN_RE = re.compile(r"[\w]+")


@dataclass(frozen=True)
class SearchResult:
    path: str
    title: str
    persona: str | None
    score: float
    snippet: str


def _open(db: sqlite3.Connection | str | Path) -> tuple[sqlite3.Connection, bool]:
    if isinstance(db, sqlite3.Connection):
        return db, False
    return connect(db), True


def _match_query(query: str) -> str:
    """Build a safe FTS5 MATCH expression: quoted tokens joined with OR."""
    tokens = _TOKEN_RE.findall(query)
    return " OR ".join('"' + t.replace('"', '""') + '"' for t in tokens)


def search(
    db: sqlite3.Connection | str | Path,
    query: str,
    k: int = 10,
) -> list[SearchResult]:
    """FTS5 BM25 keyword search with snippet extraction."""
    conn, owned = _open(db)
    try:
        match = _match_query(query)
        if not match:
            return []
        rows = conn.execute(
            """
            SELECT p.path, p.title, p.persona,
                   bm25(pieces_fts) AS rank,
                   snippet(pieces_fts, 1, '>>>', '<<<', ' … ', 24) AS snip
            FROM pieces_fts
            JOIN pieces p ON p.id = pieces_fts.rowid
            WHERE pieces_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (match, k),
        ).fetchall()
        return [
            SearchResult(
                path=path,
                title=title,
                persona=persona,
                score=-rank,  # bm25() is <= 0; negate so higher = better
                snippet=snip,
            )
            for path, title, persona, rank, snip in rows
        ]
    finally:
        if owned:
            conn.close()


def vibe_search(
    db: sqlite3.Connection | str | Path,
    text: str,
    k: int = 10,
    embedder: Embedder | None = None,
) -> list[SearchResult]:
    """Cosine similarity over the embeddings table (numpy-free).

    Requires the index to have been built with an Embedder. The same (or a
    compatible) embedder must be passed here to embed the query text.
    """
    if embedder is None:
        raise ValueError("vibe_search requires an embedder")
    conn, owned = _open(db)
    try:
        rows = conn.execute(
            """
            SELECT p.path, p.title, p.persona, p.body, e.vector
            FROM embeddings e
            JOIN pieces p ON p.id = e.piece_id
            """
        ).fetchall()
        if not rows:
            return []
        qvec = embedder.embed([text])[0]
        scored = []
        for path, title, persona, body, blob in rows:
            sim = cosine(qvec, unpack_vector(blob))
            snippet = " ".join(body.split())[:160]
            scored.append(
                SearchResult(
                    path=path,
                    title=title,
                    persona=persona,
                    score=sim,
                    snippet=snippet,
                )
            )
        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:k]
    finally:
        if owned:
            conn.close()
