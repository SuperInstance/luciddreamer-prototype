"""
vector_integration.py — Dual-storage integration for the knowledge base.

Three storage layers:
  1. LOCAL (Python pickle) — fast iteration, no network needed.
     Stores the full KnowledgeGraph for local queries and development.
  2. D1 (Cloudflare D1) — structural graph storage.
     Stores IdeaNodes as rows for SQL relationship queries via Workers.
  3. Vectorize (Cloudflare Vectorize) — semantic search.
     Stores embeddings for "find similar ideas" queries.

Embeddings are generated via nomic-embed-text through Ollama (local),
matching the existing fleet-wiki setup (768 dims).

This module provides:
  - embed_text(): generate embeddings via Ollama
  - LocalStore: pickle-based persistence
  - D1Store: D1 SQL schema + sync (via wrangler)
  - VectorizeStore: Vectorize sync (via wrangler)
  - KnowledgeBase: unified interface wrapping all three layers
"""

from __future__ import annotations

import json
import os
import pickle
import subprocess
import time
from typing import Any, Optional

from idea_schema import IdeaNode, IdeaStatus, IdeaType, ModelNode, RelationshipType, SessionNode
from knowledge_graph import KnowledgeGraph


# ─── Embedding via Ollama ─────────────────────────────────────────────────────

def embed_text(text: str, model: str = "nomic-embed-text", ollama_host: str = "http://localhost:11434") -> Optional[list[float]]:
    """
    Generate an embedding for the given text using Ollama's nomic-embed-text.
    Returns a 768-dimensional float vector, or None if Ollama is unavailable.

    Matches the existing fleet-wiki embedding configuration.
    """
    import urllib.request
    import urllib.error

    url = f"{ollama_host}/api/embeddings"
    payload = json.dumps({"model": model, "prompt": text}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data.get("embedding")
    except (urllib.error.URLError, ConnectionRefusedError, TimeoutError):
        return None
    except Exception:
        return None


def embed_idea(idea: IdeaNode, ollama_host: str = "http://localhost:11434") -> IdeaNode:
    """Embed an idea's content and return the idea with embedding populated."""
    text_for_embedding = f"{idea.title}. {idea.content[:500]}"
    emb = embed_text(text_for_embedding, ollama_host=ollama_host)
    if emb:
        idea.embedding = emb
    return idea


# ─── Local Store (Pickle) ─────────────────────────────────────────────────────

class LocalStore:
    """
    Pickle-based local persistence for the KnowledgeGraph.
    Fast iteration without any network calls.
    """

    def __init__(self, path: str = "knowledge_base.pkl"):
        self.path = path

    def save(self, graph: KnowledgeGraph) -> None:
        with open(self.path, "wb") as f:
            pickle.dump(graph.to_dict(), f)

    def load(self) -> KnowledgeGraph:
        if not os.path.exists(self.path):
            return KnowledgeGraph()
        with open(self.path, "rb") as f:
            data = pickle.load(f)
        return KnowledgeGraph.from_dict(data)

    def exists(self) -> bool:
        return os.path.exists(self.path)


# ─── D1 Store (Cloudflare D1) ─────────────────────────────────────────────────

D1_SCHEMA = """
-- Idea nodes table
CREATE TABLE IF NOT EXISTS ideas (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    idea_type TEXT,
    source_model TEXT,
    source_session TEXT,
    source_file TEXT,
    lineage TEXT,        -- JSON array of parent IDs
    status TEXT,
    tags TEXT,           -- JSON array
    timestamp REAL,
    metadata TEXT        -- JSON object
);

-- Connections (edges) table
CREATE TABLE IF NOT EXISTS connections (
    source_id TEXT,
    target_id TEXT,
    relationship TEXT,
    note TEXT,
    strength REAL,
    PRIMARY KEY (source_id, target_id, relationship)
);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    title TEXT,
    date TEXT,
    source_file TEXT,
    session_type TEXT,
    participants TEXT,   -- JSON array
    description TEXT,
    timestamp REAL
);

-- Models table
CREATE TABLE IF NOT EXISTS models (
    id TEXT PRIMARY KEY,
    name TEXT,
    alias TEXT,
    personality TEXT,
    strengths TEXT,      -- JSON array
    perspective TEXT
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_ideas_type ON ideas(idea_type);
CREATE INDEX IF NOT EXISTS idx_ideas_model ON ideas(source_model);
CREATE INDEX IF NOT EXISTS idx_ideas_status ON ideas(status);
CREATE INDEX IF NOT EXISTS idx_connections_source ON connections(source_id);
CREATE INDEX IF NOT EXISTS idx_connections_target ON connections(target_id);
CREATE INDEX IF NOT EXISTS idx_connections_rel ON connections(relationship);
"""


class D1Store:
    """
    Cloudflare D1 integration for structural graph storage.
    Generates SQL files for wrangler d1 execute.
    """

    def __init__(
        self,
        db_name: str = "luciddreamer-kb",
        wrangler_path: str = "wrangler",
        output_dir: str = "./d1-migrations",
    ):
        self.db_name = db_name
        self.wrangler_path = wrangler_path
        self.output_dir = output_dir

    def generate_schema_sql(self, output_file: str = "schema.sql") -> str:
        """Write the D1 schema SQL file."""
        os.makedirs(self.output_dir, exist_ok=True)
        path = os.path.join(self.output_dir, output_file)
        with open(path, "w") as f:
            f.write(D1_SCHEMA)
        return path

    def generate_insert_sql(self, graph: KnowledgeGraph, output_file: str = "insert_ideas.sql") -> str:
        """Generate SQL INSERT statements for all ideas in the graph."""
        os.makedirs(self.output_dir, exist_ok=True)
        path = os.path.join(self.output_dir, output_file)
        with open(path, "w") as f:
            for node in graph.nodes.values():
                # Escape single quotes in SQL
                def esc(s: str) -> str:
                    return (s or "").replace("'", "''")

                f.write(
                    f"INSERT OR REPLACE INTO ideas "
                    f"(id, title, content, idea_type, source_model, source_session, "
                    f"source_file, lineage, status, tags, timestamp, metadata) "
                    f"VALUES (\n"
                    f"  '{esc(node.id)}',\n"
                    f"  '{esc(node.title)}',\n"
                    f"  '{esc(node.content[:2000])}',\n"
                    f"  '{node.idea_type.value if hasattr(node.idea_type, 'value') else node.idea_type}',\n"
                    f"  '{esc(node.source_model)}',\n"
                    f"  '{esc(node.source_session)}',\n"
                    f"  '{esc(node.source_file)}',\n"
                    f"  '{json.dumps(node.lineage)}',\n"
                    f"  '{node.status.value if hasattr(node.status, 'value') else node.status}',\n"
                    f"  '{json.dumps(node.tags)}',\n"
                    f"  {node.timestamp},\n"
                    f"  '{json.dumps(node.metadata)}'\n"
                    f");\n\n"
                )
                # Write connections
                for conn in node.connections:
                    rel_val = conn.relationship.value if hasattr(conn.relationship, "value") else str(conn.relationship)
                    f.write(
                        f"INSERT OR REPLACE INTO connections "
                        f"(source_id, target_id, relationship, note, strength) "
                        f"VALUES (\n"
                        f"  '{esc(node.id)}',\n"
                        f"  '{esc(conn.target_id)}',\n"
                        f"  '{rel_val}',\n"
                        f"  '{esc(conn.note)}',\n"
                        f"  {conn.strength}\n"
                        f");\n"
                    )
        return path

    def generate_sessions_sql(self, sessions: list[SessionNode], output_file: str = "insert_sessions.sql") -> str:
        os.makedirs(self.output_dir, exist_ok=True)
        path = os.path.join(self.output_dir, output_file)
        with open(path, "w") as f:
            for s in sessions:
                def esc(s_: str) -> str:
                    return (s_ or "").replace("'", "''")
                f.write(
                    f"INSERT OR REPLACE INTO sessions "
                    f"(id, title, date, source_file, session_type, participants, description, timestamp) "
                    f"VALUES (\n"
                    f"  '{esc(s.id)}',\n"
                    f"  '{esc(s.title)}',\n"
                    f"  '{esc(s.date)}',\n"
                    f"  '{esc(s.source_file)}',\n"
                    f"  '{esc(s.session_type)}',\n"
                    f"  '{json.dumps(s.participants)}',\n"
                    f"  '{esc(s.description)}',\n"
                    f"  {s.timestamp}\n"
                    f");\n\n"
                )
        return path

    def deploy(self, sql_file: str, dry_run: bool = True) -> dict:
        """
        Execute SQL against D1 via wrangler.
        Set dry_run=False to actually deploy.
        """
        cmd = [
            self.wrangler_path, "d1", "execute", self.db_name,
            "--file", sql_file,
        ]
        if dry_run:
            return {"cmd": " ".join(cmd), "dry_run": True}
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return {
                "returncode": result.returncode,
                "stdout": result.stdout[:2000],
                "stderr": result.stderr[:2000],
            }
        except Exception as e:
            return {"error": str(e)}


# ─── Vectorize Store ──────────────────────────────────────────────────────────

class VectorizeStore:
    """
    Cloudflare Vectorize integration for semantic search.
    Generates JSONL files for wrangler vectorize insert.
    """

    def __init__(
        self,
        index_name: str = "luciddreamer-kb",
        wrangler_path: str = "wrangler",
        output_dir: str = "./vectorize-data",
    ):
        self.index_name = index_name
        self.wrangler_path = wrangler_path
        self.output_dir = output_dir

    def generate_jsonl(self, graph: KnowledgeGraph, output_file: str = "ideas_vectors.jsonl") -> str:
        """
        Generate a JSONL file with embeddings for Vectorize insertion.
        Only includes ideas that have embeddings.
        """
        os.makedirs(self.output_dir, exist_ok=True)
        path = os.path.join(self.output_dir, output_file)
        with open(path, "w") as f:
            for node in graph.nodes.values():
                if node.embedding:
                    metadata = {
                        "title": node.title,
                        "idea_type": node.idea_type.value if hasattr(node.idea_type, "value") else str(node.idea_type),
                        "source_model": node.source_model,
                        "status": node.status.value if hasattr(node.status, "value") else str(node.status),
                        "tags": node.tags,
                        "source_file": node.source_file,
                    }
                    record = {
                        "id": node.id,
                        "values": node.embedding,
                        "metadata": metadata,
                    }
                    f.write(json.dumps(record) + "\n")
        return path

    def deploy(self, jsonl_file: str, dry_run: bool = True) -> dict:
        """Insert vectors into Vectorize via wrangler."""
        cmd = [
            self.wrangler_path, "vectorize", "insert", self.index_name,
            "--file", jsonl_file,
        ]
        if dry_run:
            return {"cmd": " ".join(cmd), "dry_run": True}
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            return {
                "returncode": result.returncode,
                "stdout": result.stdout[:2000],
                "stderr": result.stderr[:2000],
            }
        except Exception as e:
            return {"error": str(e)}


# ─── Unified Interface ────────────────────────────────────────────────────────

class KnowledgeBase:
    """
    Unified interface wrapping all three storage layers.

    Usage:
        kb = KnowledgeBase()
        kb.add_idea(idea)
        kb.save()         # saves locally
        kb.export_d1()    # generates D1 SQL
        kb.export_vectorize()  # generates Vectorize JSONL

    The local store is always available. D1 and Vectorize exports
    generate files that can be deployed via wrangler when ready.
    """

    def __init__(
        self,
        local_path: str = "knowledge_base.pkl",
        d1_db_name: str = "luciddreamer-kb",
        vectorize_index: str = "luciddreamer-kb",
        ollama_host: str = "http://localhost:11434",
    ):
        self.graph = KnowledgeGraph()
        self.local = LocalStore(local_path)
        self.d1 = D1Store(db_name=d1_db_name)
        self.vectorize = VectorizeStore(index_name=vectorize_index)
        self.ollama_host = ollama_host
        self.sessions: list[SessionNode] = []
        self.models: dict[str, ModelNode] = {}

    def load(self) -> None:
        """Load from local store."""
        self.graph = self.local.load()

    def save(self) -> None:
        """Save to local store."""
        self.local.save(self.graph)

    def add_idea(self, idea: IdeaNode, embed: bool = False) -> None:
        """Add an idea, optionally embedding it first."""
        if embed and not idea.embedding:
            idea = embed_idea(idea, ollama_host=self.ollama_host)
        self.graph.add_idea(idea)

    def add_ideas(self, ideas: list[IdeaNode], embed: bool = False) -> None:
        for idea in ideas:
            self.add_idea(idea, embed=embed)

    def add_session(self, session: SessionNode) -> None:
        self.sessions.append(session)

    def add_model(self, model: ModelNode) -> None:
        self.models[model.id] = model

    def connect(
        self,
        source_id: str,
        target_id: str,
        relationship: RelationshipType,
        note: str = "",
    ) -> None:
        self.graph.connect(source_id, target_id, relationship, note)

    def export_d1(self, output_dir: str = "./d1-migrations") -> dict:
        """Generate D1 SQL files for deployment."""
        self.d1.output_dir = output_dir
        schema_path = self.d1.generate_schema_sql()
        ideas_path = self.d1.generate_insert_sql(self.graph)
        sessions_path = self.d1.generate_sessions_sql(self.sessions)
        return {
            "schema": schema_path,
            "ideas": ideas_path,
            "sessions": sessions_path,
        }

    def export_vectorize(self, output_dir: str = "./vectorize-data") -> str:
        """Generate Vectorize JSONL for deployment."""
        self.vectorize.output_dir = output_dir
        return self.vectorize.generate_jsonl(self.graph)

    def stats(self) -> dict:
        return self.graph.stats()

    def summary(self) -> str:
        return self.graph.summary()
