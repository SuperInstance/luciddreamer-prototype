#!/usr/bin/env python3
"""
Test 3: Vectorize metadata format.
Verifies that idea records produce correct Vectorize JSONL entries.
"""

import json
import pickle
import sys
from pathlib import Path

KB_PKL = Path(__file__).parent.parent.parent / "docs" / "knowledge-base" / "knowledge_base.pkl"


def load_nodes():
    with open(KB_PKL, "rb") as f:
        data = pickle.load(f)
    return data["nodes"]


def test_metadata_fields():
    """Verify all required metadata fields are present in idea records."""
    nodes = load_nodes()
    required_meta = {"idea_id", "title", "type", "source_model", "session", "tags", "status"}

    # Simulate what vectorize_ideas.py does
    for idea_id, idea in list(nodes.items())[:10]:
        metadata = {
            "idea_id": idea_id,
            "title": idea.get("title", ""),
            "type": idea.get("idea_type", "insight"),
            "source_model": idea.get("source_model", ""),
            "session": idea.get("source_session", ""),
            "tags": idea.get("tags", []),
            "status": idea.get("status", "seed"),
        }
        missing = required_meta - set(metadata.keys())
        assert not missing, f"Missing metadata fields for {idea_id}: {missing}"
    return True


def test_jsonl_format():
    """Verify JSONL records are valid JSON with required keys."""
    nodes = load_nodes()

    for idea_id, idea in list(nodes.items())[:5]:
        # Build a record like vectorize_ideas.py would
        record = {
            "id": idea_id,
            "values": [0.1] * 768,  # Fake embedding
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
        # Must be JSON-serializable
        json_str = json.dumps(record)
        parsed = json.loads(json_str)
        assert parsed["id"] == idea_id
        assert "values" in parsed
        assert "metadata" in parsed
        assert len(parsed["values"]) == 768
    return True


def test_all_types_represented():
    """Verify all 10 idea types are present in the data."""
    nodes = load_nodes()
    types_found = set()
    for idea in nodes.values():
        types_found.add(idea.get("idea_type", ""))
    expected_types = {
        "insight", "question", "risk", "vision", "technical",
        "creative", "contradiction", "pattern", "blind_spot", "decision"
    }
    missing = expected_types - types_found
    assert not missing, f"Missing idea types: {missing}"
    return True


def test_all_models_represented():
    """Verify all 4 models are present."""
    nodes = load_nodes()
    models_found = set()
    for idea in nodes.values():
        models_found.add(idea.get("source_model", ""))
    expected = {"model_flash", "model_lucineer", "model_wesley", "model_hermes"}
    missing = expected - models_found
    assert not missing, f"Missing models: {missing}"
    return True


def run():
    print("  Test 3: Metadata Format")
    tests = [test_metadata_fields, test_jsonl_format,
             test_all_types_represented, test_all_models_represented]
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
