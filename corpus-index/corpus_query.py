"""
corpus_query.py — Query the indexed corpus.

Provides semantic, temporal, thematic, and structural queries
across the ai-writings corpus.

Usage:
    python corpus_query.py semantic "what did Hermes write about beauty?"
    python corpus_query.py temporal "August 10"
    python corpus_query.py theme "Waterline"
    python corpus_query.py themes                    # topic clustering
    python corpus_query.py models                    # collaboration graph
    python corpus_query.py search "hermit crabs"     # full-text search
    python corpus_query.py stats                     # corpus statistics
    python corpus_query.py by-model "Hermes"
    python corpus_query.py recent 10                 # 10 most recent pieces

Query modes:
    semantic <text>     — semantic search using embeddings
    temporal <date>     — find pieces from a specific date
    theme <theme>       — find pieces about a theme
    themes              — show all themes and counts
    models              — show collaboration graph
    by-model <name>     — filter by author model
    search <text>       — keyword search across titles + excerpts
    recent <N>          — N most recently indexed pieces
    stats               — corpus statistics
"""

from __future__ import annotations

import json
import math
import os
import pickle
import re
import sys
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Optional

# Import from morning_digest
sys.path.insert(0, str(Path(__file__).resolve().parent))
from morning_digest import (
    CorpusPiece, load_index, embed_text, DATA_DIR, INDEX_PKL, INDEX_JSON,
    AI_WRITINGS_REPO, SKIP_DIRS, THEME_KEYWORDS,
)

# ─── Vector Operations ────────────────────────────────────────────────────────

def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# ─── Query Functions ──────────────────────────────────────────────────────────

def query_semantic(
    text: str,
    limit: int = 10,
    model_filter: Optional[str] = None,
    ollama_host: str = "http://localhost:11434",
) -> list[dict]:
    """
    Semantic search: find pieces matching the meaning of the query.

    'What did Hermes write about beauty?' → semantic search + filter by model
    """
    index = load_index()
    query_emb = embed_text(text, ollama_host)

    if query_emb is None:
        # Fallback to keyword search
        return query_search(text, limit, model_filter)

    scored: list[tuple[float, CorpusPiece]] = []
    for piece in index.values():
        if model_filter and model_filter.lower() not in piece.author_model.lower():
            continue
        if piece.embedding is None:
            continue
        score = cosine_similarity(query_emb, piece.embedding)
        scored.append((score, piece))

    scored.sort(key=lambda x: -x[0])

    return [
        {
            "title": p.title,
            "author": p.author_model,
            "filepath": p.filepath,
            "score": round(s, 4),
            "themes": p.themes[:5],
            "words": p.word_count,
            "excerpt": p.excerpt[:150],
        }
        for s, p in scored[:limit]
    ]


def query_temporal(date_str: str, limit: int = 50) -> list[dict]:
    """
    Temporal search: find pieces from a specific date or date range.

    'What happened on August 10?' → all pieces from 2026-08-10
    """
    index = load_index()

    # Normalize the date query
    # Accept "August 10", "Aug 10", "2026-08-10", "08-10", etc.
    month_map = {
        "january": "01", "february": "02", "march": "03", "april": "04",
        "may": "05", "june": "06", "july": "07", "august": "08",
        "september": "09", "october": "10", "november": "11", "december": "12",
        "jan": "01", "feb": "02", "mar": "03", "apr": "04",
        "jun": "06", "jul": "07", "aug": "08", "sep": "09",
        "oct": "10", "nov": "11", "dec": "12",
    }

    target = date_str.lower().strip()
    for month_name, month_num in month_map.items():
        target = target.replace(month_name, month_num)

    # Extract date patterns
    target_date = ""
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", target)
    if m:
        target_date = m.group(0)
    else:
        m = re.search(r"(\d{2})-(\d{2})", target)
        if m:
            target_date = m.group(0)
        else:
            m = re.search(r"(\d{1,2})/(\d{1,2})", target)
            if m:
                month = m.group(1).zfill(2)
                day = m.group(2).zfill(2)
                target_date = f"{month}-{day}"

    results: list[dict] = []
    for piece in index.values():
        match = False
        if target_date:
            if target_date in (piece.file_date or "") or target_date in (piece.commit_date or ""):
                match = True
        elif date_str.lower() in (piece.file_date or "").lower():
            match = True

        if match:
            results.append({
                "title": piece.title,
                "author": piece.author_model,
                "filepath": piece.filepath,
                "date": piece.file_date or piece.commit_date,
                "themes": piece.themes[:5],
                "words": piece.word_count,
                "excerpt": piece.excerpt[:150],
            })

    results.sort(key=lambda x: x.get("date", ""), reverse=True)
    return results[:limit]


def query_theme(theme: str, limit: int = 30) -> list[dict]:
    """
    Theme search: find pieces about a specific theme.

    'Find pieces about the Waterline' → theme search
    """
    index = load_index()
    theme_lower = theme.lower().replace(" ", "-")

    results: list[dict] = []
    for piece in index.values():
        if theme_lower in [t.lower() for t in piece.themes]:
            results.append({
                "title": piece.title,
                "author": piece.author_model,
                "filepath": piece.filepath,
                "themes": piece.themes,
                "words": piece.word_count,
                "excerpt": piece.excerpt[:150],
            })

    # If exact theme match found nothing, try partial
    if not results:
        for piece in index.values():
            for t in piece.themes:
                if theme_lower in t.lower() or t.lower() in theme_lower:
                    results.append({
                        "title": piece.title,
                        "author": piece.author_model,
                        "filepath": piece.filepath,
                        "themes": piece.themes,
                        "words": piece.word_count,
                        "excerpt": piece.excerpt[:150],
                    })
                    break

    results.sort(key=lambda x: -x.get("words", 0))
    return results[:limit]


def query_themes() -> list[dict]:
    """
    Topic clustering: show all themes with piece counts.

    'What themes has the fleet explored?' → theme summary
    """
    index = load_index()
    theme_counts: Counter = Counter()
    theme_models: dict[str, set[str]] = defaultdict(set)

    for piece in index.values():
        for theme in piece.themes:
            theme_counts[theme] += 1
            theme_models[theme].add(piece.author_model)

    return [
        {
            "theme": theme,
            "count": count,
            "models": sorted(theme_models[theme]),
        }
        for theme, count in theme_counts.most_common()
    ]


def query_collaboration_graph() -> dict:
    """
    Collaboration graph: which models wrote in the same files/directories.

    'Which models wrote together?' → collaboration graph
    """
    index = load_index()

    # Build directory → models mapping
    dir_models: dict[str, set[str]] = defaultdict(set)
    model_pieces: dict[str, list[str]] = defaultdict(list)
    model_co_occurrence: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for piece in index.values():
        dir_models[piece.directory].add(piece.author_model)
        model_pieces[piece.author_model].append(piece.filepath)

    # Co-occurrence: models that appear in the same directory
    for directory, models in dir_models.items():
        model_list = sorted(models)
        for i, m1 in enumerate(model_list):
            for m2 in model_list[i + 1:]:
                model_co_occurrence[m1][m2] += 1
                model_co_occurrence[m2][m1] += 1

    # Build nodes
    nodes = [
        {
            "model": model,
            "pieces": len(pieces),
            "directories": len(set(Path(p).parts[0] for p in pieces)),
        }
        for model, pieces in model_pieces.items()
    ]
    nodes.sort(key=lambda x: -x["pieces"])

    # Build edges
    edges = []
    seen_pairs: set[tuple[str, str]] = set()
    for m1, collaborators in model_co_occurrence.items():
        for m2, count in collaborators.items():
            pair = tuple(sorted([m1, m2]))
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                edges.append({"source": pair[0], "target": pair[1], "weight": count})

    edges.sort(key=lambda x: -x["weight"])

    return {
        "nodes": nodes,
        "edges": edges[:50],  # Top 50 collaborations
        "total_models": len(nodes),
        "total_collaborations": len(edges),
    }


def query_by_model(model_name: str, limit: int = 50) -> list[dict]:
    """Find pieces by a specific model."""
    index = load_index()
    model_lower = model_name.lower()

    results: list[dict] = []
    for piece in index.values():
        if model_lower in piece.author_model.lower():
            results.append({
                "title": piece.title,
                "author": piece.author_model,
                "filepath": piece.filepath,
                "date": piece.file_date or piece.commit_date,
                "themes": piece.themes[:5],
                "words": piece.word_count,
                "directory": piece.directory,
                "excerpt": piece.excerpt[:150],
            })

    results.sort(key=lambda x: x.get("date", ""), reverse=True)
    return results[:limit]


def query_search(text: str, limit: int = 20, model_filter: Optional[str] = None) -> list[dict]:
    """Full-text keyword search across titles and excerpts."""
    index = load_index()
    terms = text.lower().split()
    scored: list[tuple[int, CorpusPiece]] = []

    for piece in index.values():
        if model_filter and model_filter.lower() not in piece.author_model.lower():
            continue
        haystack = f"{piece.title} {piece.excerpt} {' '.join(piece.themes)}".lower()
        score = sum(1 for term in terms if term in haystack)
        if score > 0:
            scored.append((score, piece))

    scored.sort(key=lambda x: -x[0])

    return [
        {
            "title": p.title,
            "author": p.author_model,
            "filepath": p.filepath,
            "score": s,
            "themes": p.themes[:5],
            "words": p.word_count,
            "excerpt": p.excerpt[:150],
        }
        for s, p in scored[:limit]
    ]


def query_recent(n: int = 10) -> list[dict]:
    """Get the N most recently indexed pieces."""
    index = load_index()
    pieces = sorted(index.values(), key=lambda x: -x.indexed_at)
    return [
        {
            "title": p.title,
            "author": p.author_model,
            "filepath": p.filepath,
            "date": p.file_date or p.commit_date,
            "themes": p.themes[:5],
            "words": p.word_count,
        }
        for p in pieces[:n]
    ]


def query_stats() -> dict:
    """Corpus statistics."""
    index = load_index()
    if not index:
        return {"total_pieces": 0}

    model_counts: Counter = Counter()
    dir_counts: Counter = Counter()
    theme_counts: Counter = Counter()
    total_words = 0

    for piece in index.values():
        model_counts[piece.author_model] += 1
        dir_counts[piece.directory] += 1
        total_words += piece.word_count
        for t in piece.themes:
            theme_counts[t] += 1

    return {
        "total_pieces": len(index),
        "total_words": total_words,
        "avg_words": total_words // len(index) if index else 0,
        "by_model": dict(model_counts.most_common()),
        "by_directory": dict(dir_counts.most_common(20)),
        "by_theme": dict(theme_counts.most_common(20)),
        "models_represented": len(model_counts),
        "directories": len(dir_counts),
        "themes_found": len(theme_counts),
    }


# ─── CLI ──────────────────────────────────────────────────────────────────────

USAGE = """
Usage: python corpus_query.py <command> [args]

Commands:
  semantic <text>     Semantic search (requires Ollama for embeddings)
  temporal <date>     Find pieces from a date (e.g., "August 10", "2026-08-10")
  theme <theme>       Find pieces about a theme
  themes              Show all themes with counts
  models              Show collaboration graph
  by-model <name>     Filter by author model
  search <text>       Full-text keyword search
  recent <N>          N most recent pieces
  stats               Corpus statistics

Examples:
  python corpus_query.py semantic "what did Hermes write about beauty?"
  python corpus_query.py temporal "August 10"
  python corpus_query.py theme "Waterline"
  python corpus_query.py themes
  python corpus_query.py models
  python corpus_query.py by-model "Hermes"
  python corpus_query.py search "hermit crabs"
"""


def _print_results(results: list[dict] | dict, title: str = ""):
    if title:
        print(f"\n{'=' * 60}")
        print(f"  {title}")
        print(f"{'=' * 60}\n")

    if isinstance(results, list):
        for i, r in enumerate(results, 1):
            print(f"{i}. {r.get('title', 'Untitled')}")
            if r.get("author"):
                print(f"   Author: {r['author']}")
            if r.get("score") is not None:
                print(f"   Score: {r['score']}")
            if r.get("date"):
                print(f"   Date: {r['date']}")
            if r.get("themes"):
                print(f"   Themes: {', '.join(r['themes'])}")
            if r.get("words"):
                print(f"   Words: {r['words']:,}")
            if r.get("filepath"):
                print(f"   Path: {r['filepath']}")
            if r.get("excerpt"):
                print(f"   Excerpt: {r['excerpt'][:100]}...")
            print()
    elif isinstance(results, dict):
        import json
        print(json.dumps(results, indent=2, default=str))


def main():
    if len(sys.argv) < 2:
        print(USAGE)
        return

    cmd = sys.argv[1]

    if cmd == "semantic":
        if len(sys.argv) < 3:
            print("Usage: python corpus_query.py semantic <text>")
            return
        text = " ".join(sys.argv[2:])
        results = query_semantic(text)
        _print_results(results, f'Semantic search: "{text}"')

    elif cmd == "temporal":
        if len(sys.argv) < 3:
            print("Usage: python corpus_query.py temporal <date>")
            return
        date = " ".join(sys.argv[2:])
        results = query_temporal(date)
        _print_results(results, f'Date: {date}')

    elif cmd == "theme":
        if len(sys.argv) < 3:
            print("Usage: python corpus_query.py theme <name>")
            return
        theme = " ".join(sys.argv[2:])
        results = query_theme(theme)
        _print_results(results, f'Theme: {theme}')

    elif cmd == "themes":
        results = query_themes()
        print(f"\n{'=' * 60}")
        print(f"  Themes Explored by the Fleet ({len(results)} themes)")
        print(f"{'=' * 60}\n")
        for r in results:
            models_str = ", ".join(r["models"][:5])
            if len(r["models"]) > 5:
                models_str += f" +{len(r['models']) - 5}"
            print(f"  {r['theme']:30s} {r['count']:4d} pieces  [{models_str}]")

    elif cmd == "models":
        graph = query_collaboration_graph()
        print(f"\n{'=' * 60}")
        print(f"  Collaboration Graph")
        print(f"{'=' * 60}\n")
        print(f"Models: {graph['total_models']}")
        print(f"Collaboration links: {graph['total_collaborations']}")
        print(f"\nNodes:")
        for node in graph["nodes"]:
            print(f"  {node['model']:30s} {node['pieces']:4d} pieces  {node['directories']:3d} dirs")
        print(f"\nTop collaborations:")
        for edge in graph["edges"][:20]:
            print(f"  {edge['source']} ↔ {edge['target']}  ({edge['weight']} shared dirs)")

    elif cmd == "by-model":
        if len(sys.argv) < 3:
            print("Usage: python corpus_query.py by-model <name>")
            return
        name = " ".join(sys.argv[2:])
        results = query_by_model(name)
        _print_results(results, f'Model: {name}')

    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Usage: python corpus_query.py search <text>")
            return
        text = " ".join(sys.argv[2:])
        results = query_search(text)
        _print_results(results, f'Search: "{text}"')

    elif cmd == "recent":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        results = query_recent(n)
        _print_results(results, f'Recent {n} pieces')

    elif cmd == "stats":
        s = query_stats()
        import json
        print(json.dumps(s, indent=2, default=str))

    else:
        print(USAGE)


if __name__ == "__main__":
    main()
