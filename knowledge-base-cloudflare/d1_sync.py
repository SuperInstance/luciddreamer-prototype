#!/usr/bin/env python3
"""
d1_sync.py — Sync the knowledge graph to Cloudflare D1.

Creates tables (ideas, relationships, sessions, models), generates
SQL migration files, and executes them via wrangler.

Usage:
    python d1_sync.py                          # Full sync
    python d1_sync.py --generate-only          # Just generate SQL files
    python d1_sync.py --db-name luciddreamer-kb  # Custom DB name
    python d1_sync.py --verify                 # Verify after sync
"""

from __future__ import annotations

import argparse
import json
import os
import pickle
import subprocess
import sys
from pathlib import Path
from typing import Optional

# ─── Config ───────────────────────────────────────────────────────────────────

KB_PKL = Path(__file__).parent.parent / "docs" / "knowledge-base" / "knowledge_base.pkl"
MIGRATIONS_DIR = Path(__file__).parent / "migrations"
DEFAULT_DB_NAME = "luciddreamer-kb"


# ─── Schema ───────────────────────────────────────────────────────────────────

SCHEMA_SQL = """-- ─── Ideas Table ─────────────────────────────────────────────────
-- The atomic unit: a single insight, question, risk, vision, etc.
CREATE TABLE IF NOT EXISTS ideas (
    id              TEXT PRIMARY KEY,
    title           TEXT NOT NULL,
    content         TEXT,
    idea_type       TEXT NOT NULL DEFAULT 'insight',
    source_model    TEXT,
    source_session  TEXT,
    source_file     TEXT,
    lineage         TEXT,  -- JSON array of parent idea IDs
    status          TEXT NOT NULL DEFAULT 'seed',
    tags            TEXT,  -- JSON array of string tags
    connections     TEXT,  -- JSON array of connection objects
    timestamp       REAL,
    metadata        TEXT   -- JSON object for extensible properties
);

-- ─── Relationships Table ─────────────────────────────────────────────────
-- Typed edges between ideas: evolves_from, contradicts, supports, etc.
CREATE TABLE IF NOT EXISTS relationships (
    source_id       TEXT NOT NULL,
    target_id       TEXT NOT NULL,
    relationship    TEXT NOT NULL,
    note            TEXT,
    strength        REAL DEFAULT 1.0,
    PRIMARY KEY (source_id, target_id, relationship),
    FOREIGN KEY (source_id) REFERENCES ideas(id),
    FOREIGN KEY (target_id) REFERENCES ideas(id)
);

-- ─── Sessions Table ──────────────────────────────────────────────────────
-- Research sessions, Tap sessions, creative sessions that produced ideas.
CREATE TABLE IF NOT EXISTS sessions (
    id              TEXT PRIMARY KEY,
    title           TEXT,
    date            TEXT,
    source_file     TEXT,
    session_type    TEXT,
    participants    TEXT,  -- JSON array of model IDs/names
    description     TEXT,
    ideas_produced  TEXT,  -- JSON array of idea IDs
    timestamp       REAL
);

-- ─── Models Table ────────────────────────────────────────────────────────
-- AI models that contributed ideas. Each has a personality and perspective.
CREATE TABLE IF NOT EXISTS models (
    id                  TEXT PRIMARY KEY,
    name                TEXT,
    alias               TEXT,
    personality         TEXT,
    strengths           TEXT,  -- JSON array
    perspective         TEXT,
    sessions_contributed TEXT, -- JSON array of session IDs
    ideas_contributed   TEXT   -- JSON array of idea IDs
);

-- ─── Indexes ─────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_ideas_type    ON ideas(idea_type);
CREATE INDEX IF NOT EXISTS idx_ideas_model   ON ideas(source_model);
CREATE INDEX IF NOT EXISTS idx_ideas_status  ON ideas(status);
CREATE INDEX IF NOT EXISTS idx_ideas_session ON ideas(source_session);
CREATE INDEX IF NOT EXISTS idx_rel_source    ON relationships(source_id);
CREATE INDEX IF NOT EXISTS idx_rel_target    ON relationships(target_id);
CREATE INDEX IF NOT EXISTS idx_rel_type      ON relationships(relationship);
CREATE INDEX IF NOT EXISTS idx_sessions_type ON sessions(session_type);
"""


# ─── Load Knowledge Base ──────────────────────────────────────────────────────

def load_kb() -> tuple[dict, list]:
    """Load the pickle. Returns (nodes, edges)."""
    if not KB_PKL.exists():
        print(f"  ✗ Knowledge base not found at {KB_PKL}")
        sys.exit(1)

    with open(KB_PKL, "rb") as f:
        data = pickle.load(f)

    nodes = data.get("nodes", {})
    edges = data.get("edges", [])
    print(f"  ✓ Loaded {len(nodes)} ideas, {len(edges)} relationships")
    return nodes, edges


# ─── SQL Escaping ─────────────────────────────────────────────────────────────

def esc(s) -> str:
    """Escape a value for SQL insertion."""
    if s is None:
        return ""
    if isinstance(s, (int, float)):
        return str(s)
    return str(s).replace("'", "''")


def sql_json(obj) -> str:
    """Convert a Python object to escaped JSON for SQL."""
    return esc(json.dumps(obj, ensure_ascii=False))


# ─── Migration Generators ─────────────────────────────────────────────────────

def generate_schema_migration() -> Path:
    """Generate the schema creation SQL file."""
    MIGRATIONS_DIR.mkdir(parents=True, exist_ok=True)
    path = MIGRATIONS_DIR / "0001_schema.sql"
    with open(path, "w") as f:
        f.write("-- LucidDreamer Knowledge Base — D1 Schema\n")
        f.write(f"-- Generated by d1_sync.py\n\n")
        f.write(SCHEMA_SQL)
    print(f"  ✓ Schema migration: {path}")
    return path


def generate_ideas_migration(nodes: dict) -> Path:
    """Generate INSERT statements for all ideas."""
    MIGRATIONS_DIR.mkdir(parents=True, exist_ok=True)
    path = MIGRATIONS_DIR / "0002_insert_ideas.sql"
    with open(path, "w") as f:
        f.write("-- Insert all ideas\n")
        f.write(f"-- {len(nodes)} ideas\n\n")

        for idea_id, idea in nodes.items():
            f.write(
                f"INSERT OR REPLACE INTO ideas "
                f"(id, title, content, idea_type, source_model, source_session, "
                f"source_file, lineage, status, tags, connections, timestamp, metadata) "
                f"VALUES (\n"
                f"  '{esc(idea_id)}',\n"
                f"  '{esc(idea.get('title', ''))}',\n"
                f"  '{esc(idea.get('content', '')[:4000])}',\n"
                f"  '{esc(idea.get('idea_type', 'insight'))}',\n"
                f"  '{esc(idea.get('source_model', ''))}',\n"
                f"  '{esc(idea.get('source_session', ''))}',\n"
                f"  '{esc(idea.get('source_file', ''))}',\n"
                f"  '{sql_json(idea.get('lineage', []))}',\n"
                f"  '{esc(idea.get('status', 'seed'))}',\n"
                f"  '{sql_json(idea.get('tags', []))}',\n"
                f"  '{sql_json(idea.get('connections', []))}',\n"
                f"  {idea.get('timestamp', 0)},\n"
                f"  '{sql_json(idea.get('metadata', {}))}'\n"
                f");\n\n"
            )

    print(f"  ✓ Ideas migration: {path} ({len(nodes)} rows)")
    return path


def generate_relationships_migration(edges: list) -> Path:
    """Generate INSERT statements for all relationships."""
    MIGRATIONS_DIR.mkdir(parents=True, exist_ok=True)
    path = MIGRATIONS_DIR / "0003_insert_relationships.sql"
    with open(path, "w") as f:
        f.write("-- Insert all relationships\n")
        f.write(f"-- {len(edges)} edges\n\n")

        for edge in edges:
            f.write(
                f"INSERT OR REPLACE INTO relationships "
                f"(source_id, target_id, relationship, note, strength) "
                f"VALUES (\n"
                f"  '{esc(edge.get('source_id', ''))}',\n"
                f"  '{esc(edge.get('target_id', ''))}',\n"
                f"  '{esc(edge.get('relationship', 'supports'))}',\n"
                f"  '{esc(edge.get('note', ''))}',\n"
                f"  {edge.get('strength', 1.0)}\n"
                f");\n\n"
            )

    print(f"  ✓ Relationships migration: {path} ({len(edges)} rows)")
    return path


def generate_sessions_migration(nodes: dict) -> Path:
    """Extract and insert sessions from the knowledge base."""
    MIGRATIONS_DIR.mkdir(parents=True, exist_ok=True)
    path = MIGRATIONS_DIR / "0004_insert_sessions.sql"

    # Extract unique sessions from idea source_session fields
    sessions: dict[str, dict] = {}
    for idea in nodes.values():
        sid = idea.get("source_session", "")
        if sid and sid not in sessions:
            sessions[sid] = {
                "id": sid,
                "title": sid.replace("session_", "").replace("_", " ").title(),
                "source_file": idea.get("source_file", ""),
                "ideas_produced": [],
            }
        if sid:
            sessions[sid]["ideas_produced"].append(idea.get("id", ""))

    with open(path, "w") as f:
        f.write("-- Insert sessions extracted from ideas\n")
        f.write(f"-- {len(sessions)} sessions\n\n")

        for sess in sessions.values():
            f.write(
                f"INSERT OR REPLACE INTO sessions "
                f"(id, title, source_file, ideas_produced) "
                f"VALUES (\n"
                f"  '{esc(sess['id'])}',\n"
                f"  '{esc(sess['title'])}',\n"
                f"  '{esc(sess['source_file'])}',\n"
                f"  '{sql_json(sess['ideas_produced'])}'\n"
                f");\n\n"
            )

    print(f"  ✓ Sessions migration: {path} ({len(sessions)} rows)")
    return path


def generate_models_migration(nodes: dict) -> Path:
    """Extract and insert models from the knowledge base."""
    MIGRATIONS_DIR.mkdir(parents=True, exist_ok=True)
    path = MIGRATIONS_DIR / "0005_insert_models.sql"

    # Extract unique models and aggregate their stats
    models: dict[str, dict] = {}
    for idea in nodes.values():
        mid = idea.get("source_model", "")
        if mid and mid not in models:
            # Derive a friendly name from the model ID
            name = mid.replace("model_", "").replace("_", " ").title()
            alias = mid.replace("model_", "")

            models[mid] = {
                "id": mid,
                "name": name,
                "alias": alias,
                "personality": "",
                "perspective": "",
                "ideas_contributed": [],
                "sessions_contributed": [],
            }
        if mid:
            models[mid]["ideas_contributed"].append(idea.get("id", ""))
            sid = idea.get("source_session", "")
            if sid and sid not in models[mid]["sessions_contributed"]:
                models[mid]["sessions_contributed"].append(sid)

    with open(path, "w") as f:
        f.write("-- Insert models extracted from ideas\n")
        f.write(f"-- {len(models)} models\n\n")

        for model in models.values():
            f.write(
                f"INSERT OR REPLACE INTO models "
                f"(id, name, alias, personality, perspective, "
                f"sessions_contributed, ideas_contributed) "
                f"VALUES (\n"
                f"  '{esc(model['id'])}',\n"
                f"  '{esc(model['name'])}',\n"
                f"  '{esc(model['alias'])}',\n"
                f"  '{esc(model['personality'])}',\n"
                f"  '{esc(model['perspective'])}',\n"
                f"  '{sql_json(model['sessions_contributed'])}',\n"
                f"  '{sql_json(model['ideas_contributed'])}'\n"
                f");\n\n"
            )

    print(f"  ✓ Models migration: {path} ({len(models)} rows)")
    return path


# ─── Wrangler D1 Operations ───────────────────────────────────────────────────

def run_wrangler(args: list[str], timeout: int = 120) -> tuple[int, str, str]:
    cmd = ["wrangler"] + args
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"


def ensure_database(db_name: str) -> bool:
    """Create the D1 database if it doesn't exist."""
    rc, out, err = run_wrangler(["d1", "list"])
    if db_name in out:
        print(f"  ✓ D1 database '{db_name}' already exists")
        return True

    print(f"  → Creating D1 database '{db_name}'...")
    rc, out, err = run_wrangler(["d1", "create", db_name])
    if rc == 0 or "already" in (out + err).lower():
        print(f"  ✓ Database created")
        return True
    else:
        print(f"  ✗ Failed to create database: {err}")
        return False


def execute_migration(db_name: str, sql_file: Path) -> bool:
    """Execute a SQL migration file against D1."""
    rc, out, err = run_wrangler([
        "d1", "execute", db_name,
        "--file", str(sql_file),
    ], timeout=180)

    if rc == 0:
        print(f"  ✓ Applied {sql_file.name}")
        return True
    else:
        # Check if it's just a "already exists" warning
        combined = out + err
        if "already exists" in combined.lower():
            print(f"  ✓ {sql_file.name} (already applied)")
            return True
        print(f"  ✗ Failed to apply {sql_file.name}: {err[:300]}")
        return False


def verify_database(db_name: str) -> dict:
    """Verify the D1 database has expected data."""
    checks = {}

    # Count ideas
    rc, out, err = run_wrangler([
        "d1", "execute", db_name,
        "--command", "SELECT COUNT(*) as count FROM ideas;",
        "--json",
    ])
    if rc == 0:
        try:
            data = json.loads(out)
            if isinstance(data, list) and data:
                checks["ideas"] = data[0].get("count", data[0].get("results", [{}])[0].get("count", "?"))
            elif isinstance(data, dict):
                results = data.get("results", [])
                if results:
                    checks["ideas"] = results[0].get("count", "?")
        except json.JSONDecodeError:
            checks["ideas"] = "? (parse error)"

    # Count relationships
    rc, out, err = run_wrangler([
        "d1", "execute", db_name,
        "--command", "SELECT COUNT(*) as count FROM relationships;",
        "--json",
    ])
    if rc == 0:
        try:
            data = json.loads(out)
            if isinstance(data, list) and data:
                checks["relationships"] = data[0].get("count", data[0].get("results", [{}])[0].get("count", "?"))
            elif isinstance(data, dict):
                results = data.get("results", [])
                if results:
                    checks["relationships"] = results[0].get("count", "?")
        except json.JSONDecodeError:
            checks["relationships"] = "? (parse error)"

    # Count models
    rc, out, err = run_wrangler([
        "d1", "execute", db_name,
        "--command", "SELECT COUNT(*) as count FROM models;",
        "--json",
    ])
    if rc == 0:
        try:
            data = json.loads(out)
            if isinstance(data, list) and data:
                checks["models"] = data[0].get("count", data[0].get("results", [{}])[0].get("count", "?"))
            elif isinstance(data, dict):
                results = data.get("results", [])
                if results:
                    checks["models"] = results[0].get("count", "?")
        except json.JSONDecodeError:
            checks["models"] = "? (parse error)"

    # Count sessions
    rc, out, err = run_wrangler([
        "d1", "execute", db_name,
        "--command", "SELECT COUNT(*) as count FROM sessions;",
        "--json",
    ])
    if rc == 0:
        try:
            data = json.loads(out)
            if isinstance(data, list) and data:
                checks["sessions"] = data[0].get("count", data[0].get("results", [{}])[0].get("count", "?"))
            elif isinstance(data, dict):
                results = data.get("results", [])
                if results:
                    checks["sessions"] = results[0].get("count", "?")
        except json.JSONDecodeError:
            checks["sessions"] = "? (parse error)"

    return checks


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Sync LucidDreamer knowledge base to Cloudflare D1"
    )
    parser.add_argument(
        "--generate-only", action="store_true",
        help="Only generate SQL files, don't execute"
    )
    parser.add_argument(
        "--db-name", default=DEFAULT_DB_NAME,
        help=f"D1 database name (default: {DEFAULT_DB_NAME})"
    )
    parser.add_argument(
        "--verify", action="store_true",
        help="Verify database contents after sync"
    )
    args = parser.parse_args()

    print("\n🗄️  Semantic Bridge — D1 Sync")
    print(f"   Database: {args.db_name}")

    # Load KB
    nodes, edges = load_kb()

    # Generate migrations
    print(f"\n{'─' * 50}")
    print("  Generating SQL migrations...")
    print(f"{'─' * 50}")
    schema_path = generate_schema_migration()
    ideas_path = generate_ideas_migration(nodes)
    rels_path = generate_relationships_migration(edges)
    sessions_path = generate_sessions_migration(nodes)
    models_path = generate_models_migration(nodes)

    if args.generate_only:
        print("\n  ✓ Migrations generated (generate-only mode)")
        return

    # Execute migrations
    print(f"\n{'─' * 50}")
    print("  Deploying to D1...")
    print(f"{'─' * 50}")

    if not ensure_database(args.db_name):
        print("  ✗ Cannot proceed without database")
        sys.exit(1)

    migrations = [
        schema_path,
        ideas_path,
        rels_path,
        sessions_path,
        models_path,
    ]

    for migration in migrations:
        if not execute_migration(args.db_name, migration):
            print(f"  ⚠ Migration {migration.name} had errors, continuing...")

    # Verify
    if args.verify:
        print(f"\n{'─' * 50}")
        print("  Verifying...")
        print(f"{'─' * 50}")
        checks = verify_database(args.db_name)
        for table, count in checks.items():
            print(f"    {table}: {count}")

    print(f"\n  ✓ D1 sync complete!")


if __name__ == "__main__":
    main()
