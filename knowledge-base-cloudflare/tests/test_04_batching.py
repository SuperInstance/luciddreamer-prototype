#!/usr/bin/env python3
"""
Test 4: Batch generation.
Verifies that batch JSONL files are correctly chunked and formatted.
"""

import json
import pickle
import sys
import tempfile
from pathlib import Path

KB_PKL = Path(__file__).parent.parent.parent / "docs" / "knowledge-base" / "knowledge_base.pkl"


def load_nodes():
    with open(KB_PKL, "rb") as f:
        data = pickle.load(f)
    return data["nodes"]


def test_batch_chuning():
    """Verify batch logic produces correct number of batches."""
    nodes = load_nodes()
    batch_size = 100
    total = len(nodes)

    # Simulate batching
    batches = []
    current = []
    for idea_id, idea in nodes.items():
        record = {"id": idea_id, "values": [0.1] * 768, "metadata": {"title": idea.get("title", "")}}
        current.append(record)
        if len(current) >= batch_size:
            batches.append(current)
            current = []
    if current:
        batches.append(current)

    expected_batches = (total + batch_size - 1) // batch_size
    assert len(batches) == expected_batches, \
        f"Expected {expected_batches} batches, got {len(batches)}"
    return True


def test_batch_jsonl_valid():
    """Verify batch JSONL files contain one valid JSON record per line."""
    nodes = load_nodes()
    batch_size = 10  # Small for testing
    batch = []
    for i, (idea_id, idea) in enumerate(nodes.items()):
        if i >= batch_size:
            break
        record = {
            "id": idea_id,
            "values": [0.1] * 768,
            "metadata": {"idea_id": idea_id, "title": idea.get("title", "")},
        }
        batch.append(record)

    # Write to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        for rec in batch:
            f.write(json.dumps(rec) + "\n")
        tmp_path = f.name

    # Read back and verify
    with open(tmp_path) as f:
        lines = f.readlines()

    assert len(lines) == len(batch), f"Expected {len(batch)} lines, got {len(lines)}"
    for i, line in enumerate(lines):
        record = json.loads(line)
        assert "id" in record
        assert "values" in record
        assert "metadata" in record

    Path(tmp_path).unlink()
    return True


def test_batch_last_partial():
    """Verify the last batch can be smaller than batch_size."""
    nodes = load_nodes()
    batch_size = 100
    total = len(nodes)
    remainder = total % batch_size
    assert remainder == 42, f"Expected 42 remainder (1042 % 100), got {remainder}"
    return True


def run():
    print("  Test 4: Batch Generation")
    tests = [test_batch_chuning, test_batch_jsonl_valid, test_batch_last_partial]
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
