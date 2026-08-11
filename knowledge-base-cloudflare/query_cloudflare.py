#!/usr/bin/env python3
"""
query_cloudflare.py — Query the Cloudflare Vectorize index.

Provides semantic search and filtered queries against the
luciddreamer-kb Vectorize index on Cloudflare.

Usage:
    python query_cloudflare.py "presence"                    # Semantic search
    python query_cloudflare.py --model hermes "consciousness" # Filter by model
    python query_cloudflare.py --type risk                    # All risks
    python query_cloudflare.py --status mature                # All mature ideas
    python query_cloudflare.py --tag presence                 # By tag
    python query_cloudflare.py --model hermes                 # All Hermes ideas
    python query_cloudflare.py --top-k 20 "boat"              # More results
    python query_cloudflare.py --list-models                  # Show all models
    python query_cloudflare.py --stats                        # Index info
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

# ─── Config ───────────────────────────────────────────────────────────────────

INDEX_NAME = "luciddreamer-kb"
EMBED_MODEL = "nomic-embed-text"
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
D1_DB = "luciddreamer-kb"

# Import schema for local fallback queries
KB_PKL = Path(__file__).parent.parent / "docs" / "knowledge-base" / "knowledge_base.pkl"


# ─── Embedding ────────────────────────────────────────────────────────────────

def embed_text(text: str) -> Optional[list[float]]:
    """Generate embedding via Ollama for query text."""
    url = f"{OLLAMA_HOST}/api/embeddings"
    payload = json.dumps({"model": EMBED_MODEL, "prompt": text}).encode()
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data.get("embedding")
    except (urllib.error.URLError, ConnectionRefusedError, TimeoutError):
        return None


# ─── Wrangler Vectorize Query ─────────────────────────────────────────────────

def run_wrangler(args: list[str], timeout: int = 60) -> tuple[int, str, str]:
    """Run a wrangler command."""
    cmd = ["wrangler"] + args
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"


def query_vectorize(
    query_text: str,
    top_k: int = 10,
    return_metadata: str = "all",
) -> list[dict]:
    """
    Semantic search against the Vectorize index.
    Returns ranked results with metadata.
    """
    # Embed the query
    embedding = embed_text(query_text)
    if embedding is None:
        print("  ⚠ Ollama unavailable — cannot embed query")
        return []

    # Write the query vector to a temp file
    query_file = Path("/tmp/vectorize_query.json")
    query_data = {
        "vector": embedding,
        "topK": top_k,
        "returnMetadata": return_metadata,
    }
    with open(query_file, "w") as f:
        json.dump(query_data, f)

    # Query via wrangler
    rc, out, err = run_wrangler([
        "vectorize", "query", INDEX_NAME,
        "--query", str(query_file),
        "--top-k", str(top_k),
    ], timeout=30)

    if rc != 0:
        # Try alternative: pass query as raw JSON
        query_json = json.dumps(embedding)
        rc, out, err = run_wrangler([
            "vectorize", "query", INDEX_NAME,
            "--query", query_json,
            "--top-k", str(top_k),
        ], timeout=30)

    results = []
    if rc == 0:
        # Parse wrangler output — it varies by version
        try:
            # Try parsing as JSON directly
            data = json.loads(out)
            if isinstance(data, list):
                results = data
            elif isinstance(data, dict) and "matches" in data:
                results = data["matches"]
            elif isinstance(data, dict) and "results" in data:
                results = data["results"]
        except json.JSONDecodeError:
            # wrangler may print a table — extract matches
            results = parse_wrangler_table(out)
    else:
        print(f"  ⚠ Query failed: {err[:200]}")

    return results


def parse_wrangler_table(output: str) -> list[dict]:
    """Parse wrangler's table output format as fallback."""
    results = []
    lines = output.strip().split("\n")
    current = {}
    for line in lines:
        line = line.strip()
        if line.startswith("│") and "│" in line[1:]:
            parts = [p.strip() for p in line.split("│") if p.strip()]
            if parts and parts[0] not in ("name", ""):
                if "id" in parts[0].lower() or "score" in parts[0].lower():
                    if current:
                        results.append(current)
                    current = {}
                for p in parts:
                    if ":" in p:
                        k, v = p.split(":", 1)
                        current[k.strip()] = v.strip()
    if current:
        results.append(current)
    return results


# ─── Local Fallback Queries ───────────────────────────────────────────────────

def load_local_kb() -> tuple[dict, list]:
    """Load the pickle for local filtering."""
    import pickle
    with open(KB_PKL, "rb") as f:
        data = pickle.load(f)
    return data.get("nodes", {}), data.get("edges", [])


def local_filter(
    nodes: dict,
    model: Optional[str] = None,
    idea_type: Optional[str] = None,
    status: Optional[str] = None,
    tag: Optional[str] = None,
    text_search: Optional[str] = None,
    limit: int = 20,
) -> list[dict]:
    """
    Filter ideas locally (fallback when Vectorize isn't available).
    Returns matching ideas as dicts.
    """
    results = []
    model_lower = model.lower() if model else None
    text_lower = text_search.lower() if text_search else None

    for nid, idea in nodes.items():
        # Model filter
        if model_lower:
            sm = idea.get("source_model", "").lower()
            if model_lower not in sm:
                continue

        # Type filter
        if idea_type:
            if idea.get("idea_type", "") != idea_type:
                continue

        # Status filter
        if status:
            if idea.get("status", "") != status:
                continue

        # Tag filter
        if tag:
            if tag not in idea.get("tags", []):
                continue

        # Text search
        if text_lower:
            title = idea.get("title", "").lower()
            content = idea.get("content", "").lower()
            if text_lower not in title and text_lower not in content:
                continue

        results.append({
            "id": nid,
            "title": idea.get("title", ""),
            "type": idea.get("idea_type", ""),
            "status": idea.get("status", ""),
            "source_model": idea.get("source_model", ""),
            "session": idea.get("source_session", ""),
            "tags": idea.get("tags", [])[:8],
            "content": idea.get("content", "")[:300],
            "score": 1.0,  # No semantic score for local
        })

        if len(results) >= limit:
            break

    return results


# ─── D1 Queries ───────────────────────────────────────────────────────────────

def query_d1(sql: str) -> list[dict]:
    """
    Execute a SQL query against D1 via wrangler.
    Returns parsed JSON results.
    """
    rc, out, err = run_wrangler([
        "d1", "execute", D1_DB,
        "--command", sql,
        "--json",
    ], timeout=30)

    if rc != 0:
        print(f"  ⚠ D1 query failed: {err[:200]}")
        return []

    try:
        data = json.loads(out)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "results" in data:
            return data["results"]
    except json.JSONDecodeError:
        pass
    return []


# ─── Formatters ───────────────────────────────────────────────────────────────

def format_results(results: list[dict], verbose: bool = False) -> str:
    """Format query results for display."""
    if not results:
        return "  No results found."

    lines = [f"\n  Found {len(results)} results:\n"]
    for i, r in enumerate(results):
        score = r.get("score", r.get("similarity", ""))
        score_str = f" (score: {score:.4f})" if isinstance(score, float) else ""

        meta = r.get("metadata", r)
        title = meta.get("title", r.get("title", "Untitled"))
        idea_type = meta.get("type", r.get("type", meta.get("idea_type", "?")))
        model = meta.get("source_model", r.get("source_model", "?"))
        status = meta.get("status", r.get("status", "?"))

        lines.append(f"  {i + 1}. [{idea_type}] {title}{score_str}")
        lines.append(f"     Model: {model} | Status: {status}")

        tags = meta.get("tags", r.get("tags", []))
        if tags:
            lines.append(f"     Tags: {', '.join(tags[:5])}")

        if verbose:
            content = meta.get("content", r.get("content", ""))
            if content:
                # Wrap content
                snippet = content[:200]
                if len(content) > 200:
                    snippet += "..."
                lines.append(f"     {snippet}")

        lines.append("")

    return "\n".join(lines)


def print_stats():
    """Print index statistics."""
    rc, out, err = run_wrangler(["vectorize", "info", INDEX_NAME])
    if rc == 0:
        print(out)
    else:
        print(f"  ⚠ Could not get index info: {err[:200]}")

    # Also get local stats
    nodes, edges = load_local_kb()
    from collections import Counter

    types = Counter()
    statuses = Counter()
    models = Counter()
    for nd in nodes.values():
        types[nd.get("idea_type", "unknown")] += 1
        statuses[nd.get("status", "unknown")] += 1
        models[nd.get("source_model", "unknown")] += 1

    print(f"\n  Local Knowledge Base Stats:")
    print(f"  Total ideas: {len(nodes)}")
    print(f"  Total relationships: {len(edges)}")
    print(f"\n  By type:")
    for t, c in types.most_common():
        print(f"    {t}: {c}")
    print(f"\n  By status:")
    for s, c in statuses.most_common():
        print(f"    {s}: {c}")
    print(f"\n  By model:")
    for m, c in models.most_common():
        print(f"    {m}: {c}")


def list_models():
    """List all models in the knowledge base."""
    nodes, _ = load_local_kb()
    from collections import Counter
    models = Counter()
    model_sessions: dict[str, set] = {}
    for nd in nodes.values():
        m = nd.get("source_model", "unknown")
        models[m] += 1
        s = nd.get("source_session", "")
        if s:
            model_sessions.setdefault(m, set()).add(s)

    print(f"\n  Models in the knowledge base:")
    print(f"  {'─' * 50}")
    for m, c in models.most_common():
        sessions = len(model_sessions.get(m, set()))
        print(f"    {m}: {c} ideas ({sessions} sessions)")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Query the LucidDreamer Cloudflare Vectorize index"
    )
    parser.add_argument(
        "query", nargs="?", default=None,
        help="Semantic search query"
    )
    parser.add_argument(
        "--model", "-m", default=None,
        help="Filter by source model (e.g., 'hermes', 'flash', 'wesley')"
    )
    parser.add_argument(
        "--type", "-t", default=None,
        help="Filter by idea type (insight, question, risk, vision, etc.)"
    )
    parser.add_argument(
        "--status", "-s", default=None,
        help="Filter by status (seed, growing, mature, superseded)"
    )
    parser.add_argument(
        "--tag", default=None,
        help="Filter by tag"
    )
    parser.add_argument(
        "--top-k", type=int, default=10,
        help="Number of results (default: 10)"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show content snippets"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON"
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="Show index statistics"
    )
    parser.add_argument(
        "--list-models", action="store_true",
        help="List all models in the knowledge base"
    )

    args = parser.parse_args()

    # Stats mode
    if args.stats:
        print_stats()
        return

    # List models mode
    if args.list_models:
        list_models()
        return

    # Semantic search with Vectorize
    if args.query and not args.model and not args.type and not args.status and not args.tag:
        print(f"\n🔍 Semantic search: \"{args.query}\"")
        results = query_vectorize(args.query, top_k=args.top_k)
        if results:
            if args.json:
                print(json.dumps(results, indent=2))
            else:
                print(format_results(results, verbose=args.verbose))
        else:
            # Fallback to local text search
            print("  ⚠ Vectorize query returned nothing, falling back to local search...")
            nodes, _ = load_local_kb()
            results = local_filter(nodes, text_search=args.query, limit=args.top_k)
            print(format_results(results, verbose=args.verbose))
        return

    # Filtered queries — use local KB for structured filters
    # (Vectorize metadata filtering via wrangler is limited)
    if any([args.model, args.type, args.status, args.tag]):
        nodes, _ = load_local_kb()

        # If we also have a text query, combine with local text search
        text_search = args.query if args.query else None

        results = local_filter(
            nodes,
            model=args.model,
            idea_type=args.type,
            status=args.status,
            tag=args.tag,
            text_search=text_search,
            limit=args.top_k,
        )

        filter_desc = []
        if args.model:
            filter_desc.append(f"model={args.model}")
        if args.type:
            filter_desc.append(f"type={args.type}")
        if args.status:
            filter_desc.append(f"status={args.status}")
        if args.tag:
            filter_desc.append(f"tag={args.tag}")
        if text_search:
            filter_desc.append(f"text='{text_search}'")

        print(f"\n🔍 Filtered query: {' & '.join(filter_desc)}")

        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print(format_results(results, verbose=args.verbose))
        return

    # No query
    parser.print_help()


if __name__ == "__main__":
    main()
