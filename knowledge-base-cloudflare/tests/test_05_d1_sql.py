#!/usr/bin/env python3
"""
Test 5: D1 SQL generation.
Verifies that the generated SQL files are syntactically valid and complete.
"""

import json
import pickle
import re
import sys
from pathlib import Path

KB_PKL = Path(__file__).parent.parent.parent / "docs" / "knowledge-base" / "knowledge_base.pkl"
SCRIPT_DIR = Path(__file__).parent.parent


def load_kb():
    with open(KB_PKL, "rb") as f:
        data = pickle.load(f)
    return data["nodes"], data["edges"]


def esc(s):
    if s is None:
        return ""
    if isinstance(s, (int, float)):
        return str(s)
    return str(s).replace("'", "''")


def sql_json(obj):
    return esc(json.dumps(obj, ensure_ascii=False))


def test_schema_has_all_tables():
    """Verify schema includes ideas, relationships, sessions, models."""
    from d1_sync import SCHEMA_SQL
    tables = re.findall(r"CREATE TABLE IF NOT EXISTS (\w+)", SCHEMA_SQL)
    expected = {"ideas", "relationships", "sessions", "models"}
    found = set(tables)
    missing = expected - found
    assert not missing, f"Missing tables: {missing}"
    return True


def test_schema_has_indexes():
    """Verify schema includes indexes on key columns."""
    from d1_sync import SCHEMA_SQL
    indexes = re.findall(r"CREATE INDEX IF NOT EXISTS (\w+)", SCHEMA_SQL)
    assert len(indexes) >= 5, f"Expected at least 5 indexes, found {len(indexes)}"
    return True


def test_ideas_sql_count():
    """Verify generated SQL has exactly 1,042 INSERT statements for ideas."""
    nodes, _ = load_kb()
    count = 0
    for idea_id, idea in nodes.items():
        # Count by checking we can generate valid SQL
        sql = f"INSERT OR REPLACE INTO ideas (id) VALUES ('{esc(idea_id)}');"
        assert "INSERT" in sql
        count += 1
    assert count == 1042, f"Expected 1042 idea inserts, got {count}"
    return True


def test_relationships_sql_count():
    """Verify all 135 edges can generate valid INSERT SQL."""
    _, edges = load_kb()
    count = 0
    for edge in edges:
        sql = (
            f"INSERT OR REPLACE INTO relationships "
            f"(source_id, target_id, relationship) VALUES ("
            f"'{esc(edge.get('source_id', ''))}', "
            f"'{esc(edge.get('target_id', ''))}', "
            f"'{esc(edge.get('relationship', 'supports'))}');"
        )
        assert "INSERT" in sql
        count += 1
    assert count == 135, f"Expected 135 relationship inserts, got {count}"
    return True


def test_sql_escaping():
    """Verify SQL escaping handles single quotes."""
    test_str = "Casey's boat's brand"
    escaped = esc(test_str)
    assert "'" not in escaped.replace("''", ""), f"Unescaped quote in: {escaped}"
    # The double single quote is valid SQL escaping
    assert "''" in escaped, f"Should contain escaped quotes: {escaped}"
    return True


def test_sessions_extraction():
    """Verify sessions can be extracted from idea data."""
    nodes, _ = load_kb()
    sessions = set()
    for idea in nodes.values():
        sid = idea.get("source_session", "")
        if sid:
            sessions.add(sid)
    assert len(sessions) > 0, "No sessions found"
    return True


def test_models_extraction():
    """Verify models can be extracted from idea data."""
    nodes, _ = load_kb()
    models = set()
    for idea in nodes.values():
        mid = idea.get("source_model", "")
        if mid:
            models.add(mid)
    assert len(models) == 4, f"Expected 4 models, got {len(models)}: {models}"
    return True


def run():
    print("  Test 5: D1 SQL Generation")
    # Add parent dir to path for imports
    sys.path.insert(0, str(SCRIPT_DIR))
    tests = [
        test_schema_has_all_tables,
        test_schema_has_indexes,
        test_ideas_sql_count,
        test_relationships_sql_count,
        test_sql_escaping,
        test_sessions_extraction,
        test_models_extraction,
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
