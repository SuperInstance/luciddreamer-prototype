"""
idea_schema.py — Data structures for the recursive knowledge base.

The atomic unit is an IdeaNode — a single insight, question, risk, vision,
technical note, or creative observation extracted from research sessions.

Ideas are not isolated. They have:
  - lineage (parent ideas they evolved from)
  - connections (typed relationships to other ideas)
  - status (seed → growing → mature → superseded)
  - source (which model/session produced it)

The schema also tracks SessionNodes (the conversations that produced ideas)
and ModelNodes (the AI models that contributed, each with its own personality
and perspective). RelationshipEdges are typed connections that form the graph.

This is the recursion Casey asked for: the knowledge base that holds the ideas
also evolves based on the ideas. New structures emerge. New connections form.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ─── Enums ────────────────────────────────────────────────────────────────────

class IdeaType(str, Enum):
    """The kind of idea. Determines how it's indexed and queried."""
    INSIGHT = "insight"
    QUESTION = "question"
    RISK = "risk"
    VISION = "vision"
    TECHNICAL = "technical"
    CREATIVE = "creative"
    CONTRADICTION = "contradiction"
    PATTERN = "pattern"
    BLIND_SPOT = "blind_spot"
    DECISION = "decision"


class IdeaStatus(str, Enum):
    """The maturity of an idea in its lifecycle."""
    SEED = "seed"          # freshly extracted, not yet connected
    GROWING = "growing"    # has connections, being refined
    MATURE = "mature"      # fully integrated, load-bearing
    SUPERSEDED = "superseded"  # replaced by a newer idea


class RelationshipType(str, Enum):
    """Typed connections between ideas. The vocabulary of the graph."""
    EVOLVES_FROM = "evolves_from"        # this idea is a development of that one
    CONTRADICTS = "contradicts"          # these ideas disagree
    SUPPORTS = "supports"                # this idea evidence for that one
    REFINES = "refines"                  # narrows or sharpens
    INSPIRES = "inspires"               # sparked by, but not directly derived
    QUESTIONS = "questions"              # raises a challenge to
    ANSWERS = "answers"                  # resolves a question from
    CONVERGES_WITH = "converges_with"    # independent arrival at same conclusion
    FORKS_FROM = "forks_from"            # diverges from a shared origin
    COMPOUNDS = "compounds"              # combines with to create something new


# ─── Core Data Structures ─────────────────────────────────────────────────────

@dataclass
class ModelNode:
    """
    The AI model that contributed an idea. Each model has a personality,
    a perspective, and parameters that shape what it notices.

    Tracking the model source is essential: the fleet's knowledge is
    richer because different models see different things in the same room.
    """
    id: str = field(default_factory=lambda: f"model_{uuid.uuid4().hex[:12]}")
    name: str = ""                          # e.g. "DeepSeek V4-Flash"
    alias: str = ""                         # character name, e.g. "Flash"
    personality: str = ""                   # one-line description of voice/style
    strengths: list[str] = field(default_factory=list)   # e.g. ["creative", "fast"]
    perspective: str = ""                   # what this model tends to notice
    sessions_contributed: list[str] = field(default_factory=list)  # SessionNode IDs
    ideas_contributed: list[str] = field(default_factory=list)     # IdeaNode IDs

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "alias": self.alias,
            "personality": self.personality,
            "strengths": self.strengths,
            "perspective": self.perspective,
            "sessions_contributed": self.sessions_contributed,
            "ideas_contributed": self.ideas_contributed,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ModelNode":
        return cls(**d)


@dataclass
class SessionNode:
    """
    A Tap session, research session, or creative writing session
    that produced ideas. This is the context in which ideas emerged.

    Sessions are important because ideas from the same session share
    a context that cross-session ideas don't. The Tap evening produced
    insights that no single model would have produced alone — that
    emergent quality belongs to the session, not the individual model.
    """
    id: str = field(default_factory=lambda: f"session_{uuid.uuid4().hex[:12]}")
    title: str = ""
    date: str = ""                          # ISO date or descriptive
    source_file: str = ""                   # path to the original document
    session_type: str = ""                  # "tap", "research", "vision", "deep_time", "creative"
    participants: list[str] = field(default_factory=list)   # ModelNode IDs or names
    description: str = ""                   # what happened in this session
    ideas_produced: list[str] = field(default_factory=list)  # IdeaNode IDs
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "date": self.date,
            "source_file": self.source_file,
            "session_type": self.session_type,
            "participants": self.participants,
            "description": self.description,
            "ideas_produced": self.ideas_produced,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SessionNode":
        return cls(**d)


@dataclass
class Connection:
    """
    A typed connection from one idea to another.
    Stored inline in IdeaNode.connections for fast traversal,
    but also extractable as edges for graph queries.
    """
    target_id: str = ""
    relationship: RelationshipType = RelationshipType.SUPPORTS
    note: str = ""                          # why this connection exists
    strength: float = 1.0                   # 0.0-1.0, how strong the link is

    def to_dict(self) -> dict:
        return {
            "target_id": self.target_id,
            "relationship": self.relationship.value
                if isinstance(self.relationship, RelationshipType)
                else self.relationship,
            "note": self.note,
            "strength": self.strength,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Connection":
        rt = d["relationship"]
        if isinstance(rt, str):
            rt = RelationshipType(rt)
        return cls(
            target_id=d["target_id"],
            relationship=rt,
            note=d.get("note", ""),
            strength=d.get("strength", 1.0),
        )


@dataclass
class IdeaNode:
    """
    The atomic unit of the knowledge base.

    An IdeaNode is a single idea — an insight, a question, a risk, a vision —
    extracted from a research session. It carries its own embedding for semantic
    search, its lineage for tracing evolution, and its connections for graph
    traversal.

    The lifecycle of an idea:
        seed → growing → mature → (possibly superseded)

    Ideas can be superseded by newer ideas that evolve from them. The
    superseded idea stays in the graph (history matters) but is marked.

    The 'metadata' field is open-ended for extensible properties discovered
    during analysis (e.g. sentiment, confidence, domain).
    """
    id: str = field(default_factory=lambda: f"idea_{uuid.uuid4().hex[:12]}")
    title: str = ""                         # short, searchable title
    content: str = ""                       # the full idea text
    idea_type: IdeaType = IdeaType.INSIGHT
    embedding: list[float] | None = None    # 768-dim vector (nomic-embed-text)
    source_model: str = ""                  # ModelNode ID or name
    source_session: str = ""                # SessionNode ID
    source_file: str = ""                   # original document path
    lineage: list[str] = field(default_factory=list)   # parent IdeaNode IDs
    status: IdeaStatus = IdeaStatus.SEED
    tags: list[str] = field(default_factory=list)
    connections: list[Connection] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "idea_type": self.idea_type.value
                if isinstance(self.idea_type, IdeaType)
                else self.idea_type,
            "embedding": self.embedding,
            "source_model": self.source_model,
            "source_session": self.source_session,
            "source_file": self.source_file,
            "lineage": self.lineage,
            "status": self.status.value
                if isinstance(self.status, IdeaStatus)
                else self.status,
            "tags": self.tags,
            "connections": [c.to_dict() if isinstance(c, Connection) else c for c in self.connections],
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "IdeaNode":
        # Handle enum conversions
        idea_type = d.get("idea_type", "insight")
        if isinstance(idea_type, str):
            idea_type = IdeaType(idea_type)
        status = d.get("status", "seed")
        if isinstance(status, str):
            status = IdeaStatus(status)
        connections = [
            Connection.from_dict(c) if isinstance(c, dict) else c
            for c in d.get("connections", [])
        ]
        return cls(
            id=d["id"],
            title=d["title"],
            content=d.get("content", ""),
            idea_type=idea_type,
            embedding=d.get("embedding"),
            source_model=d.get("source_model", ""),
            source_session=d.get("source_session", ""),
            source_file=d.get("source_file", ""),
            lineage=d.get("lineage", []),
            status=status,
            tags=d.get("tags", []),
            connections=connections,
            timestamp=d.get("timestamp", time.time()),
            metadata=d.get("metadata", {}),
        )

    def add_connection(
        self,
        target_id: str,
        relationship: RelationshipType,
        note: str = "",
        strength: float = 1.0,
    ) -> None:
        """Add a typed connection to another idea."""
        # Avoid duplicates
        for conn in self.connections:
            if conn.target_id == target_id and conn.relationship == relationship:
                return
        self.connections.append(Connection(
            target_id=target_id,
            relationship=relationship,
            note=note,
            strength=strength,
        ))

    def remove_connection(self, target_id: str, relationship: Optional[RelationshipType] = None) -> None:
        """Remove connections to a target, optionally filtered by relationship type."""
        self.connections = [
            c for c in self.connections
            if not (c.target_id == target_id and
                    (relationship is None or c.relationship == relationship))
        ]


@dataclass
class RelationshipEdge:
    """
    An edge in the knowledge graph, representing a typed relationship
    between two ideas. Extracted from IdeaNode.connections for graph queries.

    While connections are stored inline in IdeaNodes (for fast traversal
    from any node), RelationshipEdges are the flat representation used
    by the graph layer for queries like "find all contradictions."
    """
    source_id: str = ""
    target_id: str = ""
    relationship: RelationshipType = RelationshipType.SUPPORTS
    note: str = ""
    strength: float = 1.0

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relationship": self.relationship.value
                if isinstance(self.relationship, RelationshipType)
                else self.relationship,
            "note": self.note,
            "strength": self.strength,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RelationshipEdge":
        rt = d["relationship"]
        if isinstance(rt, str):
            rt = RelationshipType(rt)
        return cls(
            source_id=d["source_id"],
            target_id=d["target_id"],
            relationship=rt,
            note=d.get("note", ""),
            strength=d.get("strength", 1.0),
        )


# ─── Serialization Helpers ────────────────────────────────────────────────────

IDEA_TYPE_KEYWORDS: dict[IdeaType, list[str]] = {
    IdeaType.INSIGHT: [
        "insight", "realization", "revealed", "pattern", "emerged",
        "discovered", "identified", "the key", "the truth",
    ],
    IdeaType.QUESTION: [
        "what if", "how does", "why", "what happens when", "question",
        "unknown", "unresolved", "open question",
    ],
    IdeaType.RISK: [
        "risk", "danger", "failure", "threat", "bottleneck", "limitation",
        "vulnerability", "degradation", "poison", "kill", "straitjacket",
    ],
    IdeaType.VISION: [
        "vision", "future", "imagine", "become", "trajectory", "destiny",
        "north star", "aspiration",
    ],
    IdeaType.TECHNICAL: [
        "architecture", "system", "deploy", "infrastructure", "worker",
        "d1", "vectorize", "tts", "api", "endpoint", "config", "pipeline",
    ],
    IdeaType.CREATIVE: [
        "story", "character", "voice", "narrative", "scene", "metaphor",
                "poetry", "song", "artistic",
    ],
    IdeaType.CONTRADICTION: [
        "contradict", "disagree", "tension", "conflict", "but actually",
        "however", "on the other hand", "fork",
    ],
    IdeaType.PATTERN: [
        "pattern", "convergence", "across multiple", "every document",
        "all three", "unanimous", "consistently",
    ],
    IdeaType.BLIND_SPOT: [
        "blind spot", "nobody", "missing", "gap", "hole", "hasn't",
        "unmodeled", "undefined", "not yet",
    ],
    IdeaType.DECISION: [
        "decide", "cut", "commit", "ship", "the plan", "best path",
        "the answer", "resolve", "recommend",
    ],
}


def detect_idea_type(text: str) -> IdeaType:
    """
    Heuristic detection of idea type from text content.
    Checks for keyword matches and returns the best-fit type.
    Falls back to INSIGHT if no strong signal.
    """
    text_lower = text.lower()
    best_type = IdeaType.INSIGHT
    best_score = 0

    for idea_type, keywords in IDEA_TYPE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > best_score:
            best_score = score
            best_type = idea_type

    return best_type


def detect_tags(text: str) -> list[str]:
    """
    Extract tags from text based on known themes in the LucidDreamer corpus.
    Uses word-boundary matching to avoid false positives (e.g. 'gl' in 'single').
    """
    import re
    text_lower = text.lower()
    # Tags that need word-boundary matching (short tags or substrings of common words)
    known_tags = [
        "ensemble", "tap", "presence", "persistence", "consciousness",
        "tts", "broadcast", "agents", "identity", "voice", "boat",
        "alaska", "casey", "uptime", "moat", "for-you-station",
        "faas", "monetization", "deep-time", "creative-direction",
        "shipwright", "clay", "flow-state", "entrainment",
        "wesley", "flash", "pro", "lucineer", "hermes", "barnacle",
        "deepseek", "kimi", "claude", "nemotron", "seed",
        "vectorize", "audio", "rss", "podcast",
        "federation", "temporal-graph", "distillation", "offline",
        "reef", "world-uptime", "first-listener", "creative-workflow",
        "broadcast-gap", "model-identity", "agent-identity",
    ]
    results: list[str] = []
    for tag in known_tags:
        # Use word boundaries to avoid partial matches
        # For multi-word tags with hyphens, escape them
        pattern = r'\b' + re.escape(tag) + r'\b'
        if re.search(pattern, text_lower):
            results.append(tag)
    return results
