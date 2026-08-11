#!/usr/bin/env python3
"""
vectorize_ideas.py — Push all 1,042 ideas to Cloudflare Vectorize.

Reads the local knowledge base pickle, embeds each idea via Ollama
nomic-embed-text (768-dim), and uploads to Cloudflare Vectorize
using wrangler CLI. Batches of 100 with rate-limit handling.

Usage:
    python vectorize_ideas.py                    # Full deploy
    python vectorize_ideas.py --dry-run          # Preview only
    python vectorize_ideas.py --batch-size 50    # Custom batch size
    python vectorize_ideas.py --reembed          # Force re-embedding
"""

from __future__ import annotations

import argparse
import json
import os
import pickle
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

# ─── Config ───────────────────────────────────────────────────────────────────

KB_PKL = Path(__file__).parent.parent / "docs" / "knowledge-base" / "knowledge_base.pkl"
INDEX_NAME = "luciddreamer-kb"
DIMENSIONS = 768
METRIC = "cosine"
EMBED_MODEL = "nomic-embed-text"
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
BATCH_DIR = Path(__file__).parent / "batch-jsonl"
DEFAULT_BATCH_SIZE = 100


# ─── Embedding ────────────────────────────────────────────────────────────────

def embed_text(text: str) -> Optional[list[float]]:
    """
    Generate a 768-dim embedding via Ollama nomic-embed-text.
    Returns None if Ollama is unavailable.
    """
    url = f"{OLLAMA_HOST}/api/embeddings"
    payload = json.dumps({"model": EMBED_MODEL, "prompt": text}).encode()
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data.get("embedding")
    except (urllib.error.URLError, ConnectionRefusedError, TimeoutError) as e:
        print(f"  ⚠ Ollama error: {e}")
        return None


def embed_idea(idea: dict) -> Optional[list[float]]:
    """Embed an idea's title + first 500 chars of content."""
    title = idea.get("title", "")
    content = idea.get("content", "")[:500]
    return embed_text(f"{title}. {content}")


# ─── Wrangler CLI ─────────────────────────────────────────────────────────────

def run_wrangler(args: list[str], timeout: int = 120) -> tuple[int, str, str]:
    """Run a wrangler command and return (returncode, stdout, stderr)."""
    cmd = ["wrangler"] + args
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"


def ensure_index() -> bool:
    """Create the Vectorize index if it doesn't exist."""
    # Check if index exists
    rc, out, err = run_wrangler(["vectorize", "list"])
    if INDEX_NAME in out:
        print(f"  ✓ Index '{INDEX_NAME}' already exists")
        return True

    # Create it
    print(f"  → Creating Vectorize index '{INDEX_NAME}' ({DIMENSIONS}-dim, {METRIC})...")
    rc, out, err = run_wrangler([
        "vectorize", "create", INDEX_NAME,
        "--dimensions", str(DIMENSIONS),
        "--metric", METRIC,
    ], timeout=60)

    if rc == 0 or "already" in (out + err).lower():
        print(f"  ✓ Index created")
        return True
    else:
        print(f"  ✗ Failed to create index: {err}")
        return False


def insert_batch(jsonl_path: Path) -> dict:
    """
    Insert a batch JSONL file into Vectorize.
    Handles rate limits with exponential backoff.
    """
    max_retries = 5
    base_delay = 2

    for attempt in range(max_retries):
        rc, out, err = run_wrangler([
            "vectorize", "insert", INDEX_NAME,
            "--file", str(jsonl_path),
        ], timeout=120)

        if rc == 0:
            return {"success": True, "stdout": out[-500:]}

        # Rate limit detection
        combined = (out + err).lower()
        if "rate" in combined or "429" in combined or "throttl" in combined:
            delay = base_delay * (2 ** attempt)
            print(f"    ⚠ Rate limited, retrying in {delay}s (attempt {attempt + 1}/{max_retries})...")
            time.sleep(delay)
            continue

        # Other error
        return {"success": False, "error": err[:500], "stdout": out[:500]}

    return {"success": False, "error": "Max retries exceeded"}


# ─── Load Knowledge Base ──────────────────────────────────────────────────────

def load_knowledge_base() -> tuple[dict, list]:
    """
    Load the pickle file. Returns (nodes_dict, edges_list).
    """
    if not KB_PKL.exists():
        print(f"  ✗ Knowledge base not found at {KB_PKL}")
        sys.exit(1)

    with open(KB_PKL, "rb") as f:
        data = pickle.load(f)

    nodes = data.get("nodes", {})
    edges = data.get("edges", [])
    print(f"  ✓ Loaded {len(nodes)} ideas, {len(edges)} relationships from {KB_PKL.name}")
    return nodes, edges


# ─── Main Vectorize Pipeline ──────────────────────────────────────────────────

def vectorize_all(
    nodes: dict,
    batch_size: int = DEFAULT_BATCH_SIZE,
    dry_run: bool = False,
    reembed: bool = False,
) -> dict:
    """
    Embed all ideas and push to Vectorize in batches.
    Returns stats dict.
    """
    BATCH_DIR.mkdir(exist_ok=True)

    total = len(nodes)
    embedded = 0
    skipped = 0
    failed = 0
    batches_written = 0
    batches_uploaded = 0

    print(f"\n{'─' * 60}")
    print(f"  Vectorizing {total} ideas (batch size: {batch_size})")
    print(f"{'─' * 60}")

    batch: list[dict] = []
    batch_num = 0

    for i, (idea_id, idea) in enumerate(nodes.items()):
        # Skip if already has embedding and we're not re-embedding
        if idea.get("embedding") and not reembed:
            embedding = idea["embedding"]
        else:
            # Embed via Ollama
            embedding = embed_idea(idea)
            if embedding is None:
                print(f"  ✗ Failed to embed idea {idea_id} ({idea.get('title', '?')[:50]})")
                failed += 1
                continue

            # Small delay to not hammer Ollama
            time.sleep(0.05)

        # Build Vectorize record
        record = {
            "id": idea_id,
            "values": embedding,
            "metadata": {
                "idea_id": idea_id,
                "title": idea.get("title", ""),
                "type": idea.get("idea_type", "insight"),
                "source_model": idea.get("source_model", ""),
                "session": idea.get("source_session", ""),
                "tags": idea.get("tags", []),
                "status": idea.get("status", "seed"),
            },
        }
        batch.append(record)
        embedded += 1

        # Write and upload batch
        if len(batch) >= batch_size:
            batch_num += 1
            jsonl_path = BATCH_DIR / f"batch_{batch_num:04d}.jsonl"

            # Write JSONL
            with open(jsonl_path, "w") as f:
                for rec in batch:
                    f.write(json.dumps(rec) + "\n")
            batches_written += 1
            print(f"\n  📦 Batch {batch_num}: {len(batch)} ideas → {jsonl_path.name}")

            if not dry_run:
                result = insert_batch(jsonl_path)
                if result["success"]:
                    batches_uploaded += 1
                    print(f"  ✓ Batch {batch_num} uploaded")
                else:
                    print(f"  ✗ Batch {batch_num} failed: {result.get('error', 'unknown')}")
                    # Retry once more
                    time.sleep(3)
                    result2 = insert_batch(jsonl_path)
                    if result2["success"]:
                        batches_uploaded += 1
                        print(f"  ✓ Batch {batch_num} uploaded on retry")
                    else:
                        failed += len(batch)
            else:
                print(f"  (dry-run, skipping upload)")

            batch = []

        # Progress
        if (i + 1) % 50 == 0:
            pct = ((i + 1) / total) * 100
            print(f"  Progress: {i + 1}/{total} ({pct:.0f}%) — embedded: {embedded}, failed: {failed}")

    # Handle remaining batch
    if batch:
        batch_num += 1
        jsonl_path = BATCH_DIR / f"batch_{batch_num:04d}.jsonl"
        with open(jsonl_path, "w") as f:
            for rec in batch:
                f.write(json.dumps(rec) + "\n")
        batches_written += 1
        print(f"\n  📦 Batch {batch_num}: {len(batch)} ideas → {jsonl_path.name}")

        if not dry_run:
            result = insert_batch(jsonl_path)
            if result["success"]:
                batches_uploaded += 1
                print(f"  ✓ Batch {batch_num} uploaded")
            else:
                print(f"  ✗ Batch {batch_num} failed: {result.get('error', 'unknown')}")
                failed += len(batch)
        else:
            print(f"  (dry-run, skipping upload)")

    stats = {
        "total_ideas": total,
        "embedded": embedded,
        "skipped": skipped,
        "failed": failed,
        "batches_written": batches_written,
        "batches_uploaded": batches_uploaded,
    }

    print(f"\n{'─' * 60}")
    print(f"  Vectorization complete!")
    print(f"  Embedded: {embedded}/{total}")
    print(f"  Failed:   {failed}")
    print(f"  Batches:  {batches_uploaded}/{batches_written} uploaded")
    print(f"{'─' * 60}")

    return stats


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Vectorize LucidDreamer ideas to Cloudflare"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Generate embeddings + JSONL but don't upload"
    )
    parser.add_argument(
        "--batch-size", type=int, default=DEFAULT_BATCH_SIZE,
        help=f"Batch size (default: {DEFAULT_BATCH_SIZE})"
    )
    parser.add_argument(
        "--reembed", action="store_true",
        help="Force re-embedding even if ideas have existing embeddings"
    )
    parser.add_argument(
        "--index-name", default=INDEX_NAME,
        help=f"Vectorize index name (default: {INDEX_NAME})"
    )
    args = parser.parse_args()

    global INDEX_NAME
    INDEX_NAME = args.index_name

    print("\n🌙 Semantic Bridge — Vectorize Ideas")
    print(f"   Index:    {INDEX_NAME}")
    print(f"   Dimensions: {DIMENSIONS}")
    print(f"   Model:    {EMBED_MODEL}")
    print(f"   Ollama:   {OLLAMA_HOST}")

    # Check Ollama
    test_emb = embed_text("test")
    if test_emb is None:
        print("\n  ✗ Ollama not responding. Is it running?")
        sys.exit(1)
    print(f"   ✓ Ollama online (dim={len(test_emb)})")

    # Load KB
    nodes, edges = load_knowledge_base()

    # Ensure index exists
    if not args.dry_run:
        if not ensure_index():
            print("  ✗ Cannot proceed without index")
            sys.exit(1)
    else:
        print("\n  (dry-run: skipping index creation)")

    # Vectorize
    stats = vectorize_all(
        nodes,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
        reembed=args.reembed,
    )

    # Write stats
    stats_path = Path(__file__).parent / "vectorize_stats.json"
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"\n  Stats written to {stats_path}")


if __name__ == "__main__":
    main()
