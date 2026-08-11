#!/usr/bin/env python3
"""
Test 6: Query functions.
Tests the local query/filter logic used by query_cloudflare.py.
"""

import pickle
import sys
from pathlib import Path

KB_PKL = Path(__file__).parent.parent.parent / "docs" / "knowledge-base" / "knowledge_base.pkl"


def load_nodes():
    with open(KB_PKL, "rb") as f:
        data = pickle.load(f)
    return data["nodes"]


def filter_nodes(nodes, model=None, idea_type=None, status=None, tag=None, text_search=None):
    """Mirror of the local_filter logic from query_cloudflare.py."""
    results = []
    model_lower = model.lower() if model else None
    text_lower = text_search.lower() if text_search else None

    for nid, idea in nodes.items():
        if model_lower and model_lower not in idea.get("source_model", "").lower():
            continue
        if idea_type and idea.get("idea_type", "") != idea_type:
            continue
        if status and idea.get("status", "") != status:
            continue
        if tag and tag not in idea.get("tags", []):
            continue
        if text_lower:
            title = idea.get("title", "").lower()
            content = idea.get("content", "").lower()
            if text_lower not in title and text_lower not in content:
                continue
        results.append(nid)
    return results


def test_filter_by_model_hermes():
    nodes = load_nodes()
    results = filter_nodes(nodes, model="hermes")
    assert len(results) == 94, f"Expected 94 Hermes ideas, got {len(results)}"
    return True


def test_filter_by_model_flash():
    nodes = load_nodes()
    results = filter_nodes(nodes, model="flash")
    assert len(results) == 481, f"Expected 481 Flash ideas, got {len(results)}"
    return True


def test_filter_by_type_risk():
    nodes = load_nodes()
    results = filter_nodes(nodes, idea_type="risk")
    assert len(results) == 35, f"Expected 35 risks, got {len(results)}"
    return True


def test_filter_by_status_mature():
    nodes = load_nodes()
    results = filter_nodes(nodes, status="mature")
    assert len(results) == 4, f"Expected 4 mature ideas, got {len(results)}"
    return True


def test_filter_by_status_growing():
    nodes = load_nodes()
    results = filter_nodes(nodes, status="growing")
    assert len(results) == 13, f"Expected 13 growing ideas, got {len(results)}"
    return True


def test_filter_by_tag():
    nodes = load_nodes()
    results = filter_nodes(nodes, tag="presence")
    assert len(results) > 0, "Expected ideas tagged 'presence'"
    return True


def test_text_search():
    nodes = load_nodes()
    results = filter_nodes(nodes, text_search="boat")
    assert len(results) > 0, "Expected results for 'boat'"
    return True


def test_combined_filter():
    nodes = load_nodes()
    results = filter_nodes(nodes, model="flash", idea_type="insight")
    assert len(results) > 0, "Expected Flash insights"
    # Verify all results are actually flash insights
    for nid in results:
        idea = nodes[nid]
        assert "flash" in idea["source_model"].lower()
        assert idea["idea_type"] == "insight"
    return True


def run():
    print("  Test 6: Query Functions")
    tests = [
        test_filter_by_model_hermes,
        test_filter_by_model_flash,
        test_filter_by_type_risk,
        test_filter_by_status_mature,
        test_filter_by_status_growing,
        test_filter_by_tag,
        test_text_search,
        test_combined_filter,
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
