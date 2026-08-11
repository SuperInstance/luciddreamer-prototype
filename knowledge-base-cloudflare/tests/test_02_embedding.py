#!/usr/bin/env python3
"""
Test 2: Embedding via Ollama nomic-embed-text.
Verifies embeddings are 768-dimensional and deterministic.
"""

import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

OLLAMA_HOST = "http://localhost:11434"
MODEL = "nomic-embed-text"


def embed(text: str):
    url = f"{OLLAMA_HOST}/api/embeddings"
    payload = json.dumps({"model": MODEL, "prompt": text}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data.get("embedding")
    except (urllib.error.URLError, ConnectionRefusedError):
        return None


def test_ollama_available():
    emb = embed("test")
    assert emb is not None, "Ollama not responding or nomic-embed-text not available"
    return True


def test_embedding_dimensions():
    emb = embed("the boat is the brand")
    assert len(emb) == 768, f"Expected 768 dims, got {len(emb)}"
    return True


def test_embedding_deterministic():
    """Same text should produce very similar embeddings."""
    emb1 = embed("presence is the product")
    emb2 = embed("presence is the product")
    # Cosine similarity
    dot = sum(a * b for a, b in zip(emb1, emb2))
    mag1 = sum(a * a for a in emb1) ** 0.5
    mag2 = sum(b * b for b in emb2) ** 0.5
    cos_sim = dot / (mag1 * mag2)
    assert cos_sim > 0.99, f"Deterministic embedding similarity {cos_sim} < 0.99"
    return True


def test_different_text_different_embedding():
    """Different text should produce different embeddings."""
    emb1 = embed("the boat is the brand")
    emb2 = embed("quantum field theory applications")
    dot = sum(a * b for a, b in zip(emb1, emb2))
    mag1 = sum(a * a for a in emb1) ** 0.5
    mag2 = sum(b * b for b in emb2) ** 0.5
    cos_sim = dot / (mag1 * mag2)
    assert cos_sim < 0.95, f"Different text similarity {cos_sim} too high"
    return True


def run():
    print("  Test 2: Ollama Embedding")
    tests = [test_ollama_available, test_embedding_dimensions,
             test_embedding_deterministic, test_different_text_different_embedding]
    for t in tests:
        name = t.__name__
        try:
            t()
            print(f"    ✓ {name}")
        except (AssertionError, Exception) as e:
            print(f"    ✗ {name}: {e}")
            return False
    return True


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)
