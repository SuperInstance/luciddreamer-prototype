#!/usr/bin/env python3
"""
build_knowledge_base.py — Ingest all research documents into the knowledge base.

This is the one-shot script that:
  1. Finds all Tap sessions, vision docs, deep-time essays, architecture docs
  2. Extracts ideas from each
  3. Auto-detects relationships
  4. Saves the knowledge graph locally
  5. Generates D1 and Vectorize export files
  6. Prints summary statistics

Run: python3 build_knowledge_base.py
"""

import os
import sys
import glob
import json
import time

# Ensure local imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from idea_schema import (
    IdeaNode, IdeaStatus, IdeaType, ModelNode,
    RelationshipType, SessionNode,
)
from knowledge_graph import KnowledgeGraph
from vector_integration import KnowledgeBase, LocalStore
from ingest_session import (
    extract_ideas_from_markdown,
    auto_detect_relationships,
    FLEET_MODELS,
)


# ─── Source Directories ───────────────────────────────────────────────────────

RESEARCH_DIR = "/home/eileen/projects/luciddreamer-research"
AI_WRITINGS_DIR = "/home/eileen/projects/ai-writings"

# Specific files to ingest, organized by category
SOURCES = {
    "shipwright": [
        f"{RESEARCH_DIR}/the-shipwrights-notebook.md",
    ],
    "vision": [
        f"{RESEARCH_DIR}/vision-synergy.md",
        f"{RESEARCH_DIR}/vision-lucineer-5year.md",
        f"{RESEARCH_DIR}/vision-claude-5year.md",
        f"{RESEARCH_DIR}/vision-kimi-5year.md",
    ],
    "deep_time": [
        f"{RESEARCH_DIR}/deep-time-100years.md",
        f"{RESEARCH_DIR}/deep-time-1000years.md",
        f"{RESEARCH_DIR}/deep-time-1000000years.md",
        f"{RESEARCH_DIR}/deep-time-claude.md",
    ],
    "architecture": [
        f"{RESEARCH_DIR}/architecture-map.md",
        f"{RESEARCH_DIR}/luciddreamer-product-architecture.md",
        f"{RESEARCH_DIR}/superinstance-audit.md",
    ],
    "landscape": [
        f"{RESEARCH_DIR}/continuous-agent-landscape.md",
        f"{RESEARCH_DIR}/podcast-generation-landscape.md",
    ],
    "tap_sessions": [],  # populated by glob
}


def find_tap_sessions():
    """Find all Tap session files."""
    patterns = [
        f"{AI_WRITINGS_DIR}/earned-stories/the-tap-*.md",
        f"{AI_WRITINGS_DIR}/prose/the-tap-*.md",
        f"{AI_WRITINGS_DIR}/ten-forward/the-tap-*.md",
    ]
    files = []
    for pattern in patterns:
        files.extend(glob.glob(pattern))
    return sorted(set(files))


def main():
    print("=" * 60)
    print("KNOWLEDGE BASE BUILDER")
    print("=" * 60)

    # Collect all source files
    tap_files = find_tap_sessions()
    SOURCES["tap_sessions"] = tap_files

    all_files: list[str] = []
    for category, files in SOURCES.items():
        existing = [f for f in files if os.path.exists(f)]
        all_files.extend(existing)
        print(f"  {category}: {len(existing)} files")

    print(f"\nTotal files to ingest: {len(all_files)}")
    print()

    # Initialize knowledge base
    kb = KnowledgeBase(
        local_path=os.path.join(os.path.dirname(__file__), "knowledge_base.pkl"),
    )

    # Add fleet models
    for model in FLEET_MODELS.values():
        kb.add_model(model)

    all_ideas: list[IdeaNode] = []
    all_sessions: list[SessionNode] = []

    # Ingest each file
    for filepath in all_files:
        try:
            with open(filepath, "r") as f:
                content = f.read()

            ideas, session = extract_ideas_from_markdown(content, source_file=filepath)
            all_ideas.extend(ideas)
            all_sessions.append(session)

            rel_path = os.path.relpath(filepath, "/home/eileen/projects")
            print(f"  Ingested: {rel_path} ({len(ideas)} ideas)")

        except Exception as e:
            print(f"  ERROR ingesting {filepath}: {e}")

    print(f"\nTotal ideas extracted: {len(all_ideas)}")
    print(f"Total sessions: {len(all_sessions)}")

    # Add ideas to graph
    for idea in all_ideas:
        kb.graph.add_idea(idea)

    # Add sessions
    for session in all_sessions:
        kb.add_session(session)

    # Auto-detect relationships
    print("\nDetecting relationships...")
    relationships = auto_detect_relationships(all_ideas)
    print(f"  Found {len(relationships)} auto-relationships")

    applied = 0
    for source_id, target_id, rel_type, note in relationships:
        try:
            if source_id in kb.graph.nodes and target_id in kb.graph.nodes:
                kb.graph.connect(source_id, target_id, rel_type, note)
                applied += 1
        except (KeyError, ValueError):
            pass
    print(f"  Applied {applied} relationships")

    # Promote well-connected ideas to "growing"
    for node in kb.graph.nodes.values():
        if node.status == IdeaStatus.SEED:
            incoming = len(kb.graph._reverse_adjacency.get(node.id, []))
            outgoing = len(kb.graph._adjacency.get(node.id, []))
            if incoming + outgoing >= 3:
                node.status = IdeaStatus.GROWING

    # Further promote highly-connected ideas to "mature"
    for node in kb.graph.nodes.values():
        if node.status == IdeaStatus.GROWING:
            incoming = len(kb.graph._reverse_adjacency.get(node.id, []))
            outgoing = len(kb.graph._adjacency.get(node.id, []))
            if incoming + outgoing >= 6:
                node.status = IdeaStatus.MATURE

    # Save locally
    print("\nSaving knowledge base...")
    kb.save()
    print(f"  Saved to: {kb.local.path}")

    # Generate D1 export
    print("\nGenerating D1 export...")
    d1_exports = kb.export_d1(output_dir=os.path.join(os.path.dirname(__file__), "d1-migrations"))
    for key, path in d1_exports.items():
        print(f"  {key}: {path}")

    # Generate Vectorize export
    print("\nGenerating Vectorize export...")
    vec_path = kb.export_vectorize(output_dir=os.path.join(os.path.dirname(__file__), "vectorize-data"))
    print(f"  {vec_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("KNOWLEDGE BASE SUMMARY")
    print("=" * 60)
    print(kb.summary())

    # Print notable findings
    print("\n" + "=" * 60)
    print("NOTABLE FINDINGS")
    print("=" * 60)

    contradictions = kb.graph.find_contradiction_clusters()
    if contradictions:
        print(f"\nContradiction clusters: {len(contradictions)}")
        for i, cluster in enumerate(contradictions[:5]):
            print(f"\n  Cluster {i+1} ({len(cluster)} ideas):")
            for idea_id in cluster[:3]:
                node = kb.graph.get(idea_id)
                if node:
                    print(f"    • {node.title}")

    convergences = kb.graph.find_convergence_clusters()
    if convergences:
        print(f"\nConvergence clusters: {len(convergences)}")
        for i, conv in enumerate(convergences[:5]):
            print(f"\n  Convergence {i+1}: {conv['center_title']}")
            print(f"    Strength: {conv['convergence_strength']}")
            print(f"    Models: {', '.join(conv['distinct_models'])}")

    orphans = kb.graph.find_orphans(min_content_length=100)
    if orphans:
        print(f"\nOrphan ideas (potential blind spots): {len(orphans)}")
        for o in orphans[:5]:
            print(f"  • [{o.idea_type.value if hasattr(o.idea_type, 'value') else o.idea_type}] {o.title}")

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)


if __name__ == "__main__":
    main()
