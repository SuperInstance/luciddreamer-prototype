#!/usr/bin/env python3
"""
Test 1: Knowledge base loads correctly.
Verifies 1,042 ideas and 135 relationships are present.
"""

import pickle
import sys
from pathlib import Path

KB_PKL = Path(__file__).parent.parent.parent / "docs" / "knowledge-base" / "knowledge_base.pkl"


def test_loads():
    with open(KB_PKL, "rb") as f:
        data = pickle.load(f)
    return isinstance(data, dict) and "nodes" in data and "edges" in data


def test_idea_count():
    with open(KB_PKL, "rb") as f:
        data = pickle.load(f)
    nodes = data["nodes"]
    assert len(nodes) == 1042, f"Expected 1042 ideas, got {len(nodes)}"
    return True


def test_edge_count():
    with open(KB_PKL, "rb") as f:
        data = pickle.load(f)
    edges = data["edges"]
    assert len(edges) == 135, f"Expected 135 edges, got {len(edges)}"
    return True


def test_idea_fields():
    """Verify idea dicts have all required fields."""
    with open(KB_PKL, "rb") as f:
        data = pickle.load(f)
    nodes = data["nodes"]

    required = {"id", "title", "content", "idea_type", "status",
                "source_model", "source_session", "tags"}
    for nid, idea in nodes.items():
        missing = required - set(idea.keys())
        assert not missing, f"Idea {nid} missing fields: {missing}"
    return True


def test_edge_fields():
    """Verify edges have required fields."""
    with open(KB_PKL, "rb") as f:
        data = pickle.load(f)
    edges = data["edges"]

    required = {"source_id", "target_id", "relationship"}
    for i, edge in enumerate(edges):
        missing = required - set(edge.keys())
        assert not missing, f"Edge {i} missing fields: {missing}"
    return True


def run():
    print("  Test 1: Knowledge Base Integrity")
    tests = [test_loads, test_idea_count, test_edge_count, test_idea_fields, test_edge_fields]
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
