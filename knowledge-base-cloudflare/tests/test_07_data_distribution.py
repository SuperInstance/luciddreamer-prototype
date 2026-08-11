#!/usr/bin/env python3
"""
Test 7: Data distribution.
Verifies the expected distribution of types, statuses, and models
matches the known knowledge base statistics.
"""

import pickle
import sys
from collections import Counter
from pathlib import Path

KB_PKL = Path(__file__).parent.parent.parent / "docs" / "knowledge-base" / "knowledge_base.pkl"


def load_kb():
    with open(KB_PKL, "rb") as f:
        data = pickle.load(f)
    return data["nodes"], data["edges"]


def test_type_distribution():
    nodes, _ = load_kb()
    types = Counter()
    for idea in nodes.values():
        types[idea.get("idea_type", "unknown")] += 1

    expected = {
        "insight": 528, "question": 179, "technical": 143,
        "vision": 39, "risk": 35, "decision": 34,
        "creative": 32, "blind_spot": 26, "pattern": 22,
        "contradiction": 4,
    }

    for t, count in expected.items():
        actual = types.get(t, 0)
        assert actual == count, f"Type '{t}': expected {count}, got {actual}"
    return True


def test_status_distribution():
    nodes, _ = load_kb()
    statuses = Counter()
    for idea in nodes.values():
        statuses[idea.get("status", "unknown")] += 1

    expected = {"seed": 1025, "growing": 13, "mature": 4}
    for s, count in expected.items():
        actual = statuses.get(s, 0)
        assert actual == count, f"Status '{s}': expected {count}, got {actual}"
    return True


def test_model_distribution():
    nodes, _ = load_kb()
    models = Counter()
    for idea in nodes.values():
        models[idea.get("source_model", "unknown")] += 1

    expected = {"model_flash": 481, "model_lucineer": 325,
                "model_wesley": 142, "model_hermes": 94}
    for m, count in expected.items():
        actual = models.get(m, 0)
        assert actual == count, f"Model '{m}': expected {count}, got {actual}"
    return True


def test_relationship_types():
    _, edges = load_kb()
    rel_types = Counter()
    for edge in edges:
        rel_types[edge.get("relationship", "unknown")] += 1
    # Should have at least some converges_with relationships
    assert rel_types.get("converges_with", 0) > 0, "No converges_with relationships"
    return True


def test_all_ids_unique():
    nodes, _ = load_kb()
    ids = [idea.get("id") for idea in nodes.values()]
    assert len(ids) == len(set(ids)), "Duplicate idea IDs found"
    return True


def run():
    print("  Test 7: Data Distribution")
    tests = [
        test_type_distribution,
        test_status_distribution,
        test_model_distribution,
        test_relationship_types,
        test_all_ids_unique,
    ]
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
