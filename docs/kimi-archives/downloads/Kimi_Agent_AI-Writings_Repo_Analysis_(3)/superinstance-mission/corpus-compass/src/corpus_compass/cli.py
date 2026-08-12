"""corpus-compass CLI: index / search / digest."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .digest import generate_digest
from .index import build_index
from .search import search, vibe_search

DEFAULT_DB = "corpus-compass.db"


def _make_embedder(ollama: bool, ollama_model: str):
    if not ollama:
        return None
    from .embeddings import OllamaEmbedder

    return OllamaEmbedder(model=ollama_model)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="corpus-compass",
        description="AI-Writings retrieval + self-indexing (offline FTS5 first)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_index = sub.add_parser("index", help="index a corpus directory")
    p_index.add_argument("dir", type=Path, help="corpus directory")
    p_index.add_argument("--db", type=Path, default=Path(DEFAULT_DB))
    p_index.add_argument(
        "--ollama-embed",
        action="store_true",
        help="also compute embeddings via local Ollama (nomic-embed-text)",
    )
    p_index.add_argument("--ollama-model", default="nomic-embed-text")

    p_search = sub.add_parser("search", help="search the index")
    p_search.add_argument("query")
    p_search.add_argument("--db", type=Path, default=Path(DEFAULT_DB))
    p_search.add_argument("-k", type=int, default=10)
    p_search.add_argument(
        "--vibe",
        action="store_true",
        help="cosine similarity over embeddings instead of FTS5 BM25",
    )
    p_search.add_argument(
        "--ollama-model",
        default="nomic-embed-text",
        help="embedder model for --vibe (uses local Ollama)",
    )

    p_digest = sub.add_parser("digest", help="morning briefing from git log")
    p_digest.add_argument("repo", type=Path, help="git repo (e.g. AI-Writings)")
    p_digest.add_argument("--since", default="24 hours ago")
    p_digest.add_argument("--db", type=Path, default=Path(DEFAULT_DB))
    p_digest.add_argument("--out", type=Path, default=None)
    p_digest.add_argument(
        "--content-dir",
        action="append",
        default=None,
        help="content dir(s) under the repo (default: corpus)",
    )

    args = parser.parse_args(argv)

    if args.command == "index":
        embedder = _make_embedder(args.ollama_embed, args.ollama_model)
        stats = build_index(args.dir, args.db, embeddings=embedder)
        print(
            f"indexed {stats.indexed} new/changed, skipped {stats.skipped}"
            f" unchanged of {stats.total_files} files"
            + (f", embedded {stats.embedded}" if stats.embedded else "")
            + f" -> {stats.db_path}"
        )
        return 0

    if args.command == "search":
        if args.vibe:
            from .embeddings import OllamaEmbedder

            results = vibe_search(
                args.db, args.query, k=args.k,
                embedder=OllamaEmbedder(model=args.ollama_model),
            )
        else:
            results = search(args.db, args.query, k=args.k)
        for r in results:
            persona = f" [{r.persona}]" if r.persona else ""
            print(f"{r.score:8.4f}  {r.path}{persona}")
            print(f"          {r.title}")
            if r.snippet:
                print(f"          {r.snippet}")
        if not results:
            print("no results", file=sys.stderr)
        return 0

    if args.command == "digest":
        content_dirs = tuple(args.content_dir) if args.content_dir else ("corpus",)
        markdown = generate_digest(
            args.repo,
            args.db,
            since=args.since,
            out_path=args.out,
            content_dirs=content_dirs,
        )
        print(markdown)
        return 0

    return 2  # pragma: no cover


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
