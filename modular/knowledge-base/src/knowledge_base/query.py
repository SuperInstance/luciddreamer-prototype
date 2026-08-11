"""
query.py — Query the knowledge base.

Provides high-level query functions and a CLI interface:
  - "What ideas has Hermes contributed?" → filter by model
  - "What contradictions exist in the fleet's thinking?" → find contradiction clusters
  - "How has the idea of PRESENCE evolved?" → trace lineage
  - "What are our blind spots?" → find orphan ideas and unexplored territories
  - "What converged across multiple independent sessions?" → convergence clusters

Usage:
    python query.py contradictions
    python query.py convergence
    python query.py orphans
    python query.py lineage <keyword>
    python query.py model <model_name>
    python query.py evolution <keyword>
    python query.py stats
    python query.py search <text>
    python query.py summary
"""

from __future__ import annotations

import sys
import textwrap
from typing import Optional

from idea_schema import IdeaStatus, IdeaType, RelationshipType
from knowledge_graph import KnowledgeGraph
from vector_integration import LocalStore


def load_graph(path: str = "knowledge_base.pkl") -> KnowledgeGraph:
    """Load the knowledge graph from local store."""
    store = LocalStore(path)
    if store.exists():
        return store.load()
    return KnowledgeGraph()


# ─── Query Functions ──────────────────────────────────────────────────────────

def query_by_model(graph: KnowledgeGraph, model_name: str) -> list[dict]:
    """
    'What ideas has Hermes contributed?'
    Returns ideas filtered by model name/alias.
    """
    ideas = graph.filter_by_model(model_name)
    return [
        {
            "id": i.id,
            "title": i.title,
            "type": i.idea_type.value if hasattr(i.idea_type, "value") else str(i.idea_type),
            "status": i.status.value if hasattr(i.status, "value") else str(i.status),
            "content": i.content[:200],
            "source_file": i.source_file,
            "tags": i.tags[:5],
        }
        for i in ideas
    ]


def query_contradictions(graph: KnowledgeGraph) -> list[dict]:
    """
    'What contradictions exist in the fleet's thinking?'
    Returns contradiction clusters with the ideas involved.
    """
    clusters = graph.find_contradiction_clusters()
    results: list[dict] = []
    for cluster in clusters:
        cluster_ideas: list[dict] = []
        for idea_id in cluster:
            node = graph.get(idea_id)
            if node:
                cluster_ideas.append({
                    "id": node.id,
                    "title": node.title,
                    "type": node.idea_type.value if hasattr(node.idea_type, "value") else str(node.idea_type),
                    "source_model": node.source_model,
                    "content": node.content[:200],
                })
        results.append({
            "size": len(cluster),
            "ideas": cluster_ideas,
        })
    return results


def query_convergence(graph: KnowledgeGraph) -> list[dict]:
    """
    'What converged across multiple independent sessions?'
    Returns convergence clusters — ideas from different models that
    independently arrived at the same conclusion.
    """
    return graph.find_convergence_clusters()


def query_lineage(graph: KnowledgeGraph, keyword: str) -> list[dict]:
    """
    'How has the idea of PRESENCE evolved?'
    Traces the lineage of ideas matching the keyword.
    """
    return graph.trace_evolution(keyword)


def query_orphans(graph: KnowledgeGraph) -> list[dict]:
    """
    'What are our blind spots?'
    Returns orphan ideas — high quality but unconnected to the rest
    of the knowledge base. These are potential blind spots or
    unexplored territories.
    """
    orphans = graph.find_orphans()
    return [
        {
            "id": o.id,
            "title": o.title,
            "type": o.idea_type.value if hasattr(o.idea_type, "value") else str(o.idea_type),
            "content": o.content[:200],
            "source_model": o.source_model,
            "tags": o.tags[:5],
        }
        for o in orphans
    ]


def query_evolution(graph: KnowledgeGraph, keyword: str) -> list[dict]:
    """
    Trace how ideas about a topic evolved through statuses:
    seed → growing → mature → superseded
    """
    matches = graph.search_text(keyword)
    by_status: dict[str, list[dict]] = {}

    for match in matches:
        status = match.status.value if hasattr(match.status, "value") else str(match.status)
        if status not in by_status:
            by_status[status] = []
        by_status[status].append({
            "id": match.id,
            "title": match.title,
            "source_model": match.source_model,
            "source_session": match.source_session,
            "tags": match.tags[:5],
        })

    return [{"status": s, "ideas": items} for s, items in by_status.items()]


def query_blind_spots(graph: KnowledgeGraph) -> list[dict]:
    """
    Find explicit blind_spot type ideas AND orphan ideas.
    Combines both signals for a comprehensive blind spot report.
    """
    explicit = graph.filter_by_type(IdeaType.BLIND_SPOT)
    orphans = graph.find_orphans(min_content_length=100)

    results: list[dict] = []

    for idea in explicit:
        results.append({
            "id": idea.id,
            "title": idea.title,
            "content": idea.content[:200],
            "source": "explicit blind spot",
            "source_model": idea.source_model,
        })

    seen_ids = {r["id"] for r in results}

    for orphan in orphans:
        if orphan.id not in seen_ids:
            results.append({
                "id": orphan.id,
                "title": orphan.title,
                "content": orphan.content[:200],
                "source": "orphan (unconnected)",
                "source_model": orphan.source_model,
            })

    return results


def query_stats(graph: KnowledgeGraph) -> dict:
    """Return full statistics."""
    return graph.stats()


def query_search(graph: KnowledgeGraph, text: str) -> list[dict]:
    """Full-text search across all ideas."""
    results = graph.search_text(text)
    return [
        {
            "id": r.id,
            "title": r.title,
            "type": r.idea_type.value if hasattr(r.idea_type, "value") else str(r.idea_type),
            "content": r.content[:200],
            "source_model": r.source_model,
            "tags": r.tags[:5],
        }
        for r in results
    ]


def query_tags(graph: KnowledgeGraph, tag: str) -> list[dict]:
    """Find ideas by tag."""
    ideas = graph.filter_by_tag(tag)
    return [
        {
            "id": i.id,
            "title": i.title,
            "type": i.idea_type.value if hasattr(i.idea_type, "value") else str(i.idea_type),
            "source_model": i.source_model,
        }
        for i in ideas
    ]


# ─── CLI ──────────────────────────────────────────────────────────────────────

USAGE = """
Usage: python query.py <command> [args]

Commands:
  contradictions     Show contradiction clusters
  convergence        Show convergence clusters (cross-model agreement)
  orphans            Show unconnected ideas (potential blind spots)
  blind-spots        Show explicit blind spots + orphans
  lineage <keyword>  Trace how an idea evolved (ancestors)
  evolution <keyword> Show ideas by status for a keyword
  model <name>       Show ideas from a specific model
  search <text>      Full-text search
  tags <tag>         Filter by tag
  stats              Show statistics
  summary            Human-readable summary

Examples:
  python query.py contradictions
  python query.py lineage presence
  python query.py model hermes
  python query.py search "first listener"
"""


def format_idea_brief(idea: dict, indent: int = 2) -> str:
    pad = " " * indent
    lines = [
        f"{pad}• {idea.get('title', 'Untitled')} [{idea.get('type', '?')}]",
    ]
    if "content" in idea:
        wrapped = textwrap.fill(
            idea["content"][:150],
            width=80,
            initial_indent=f"{pad}  ",
            subsequent_indent=f"{pad}  ",
        )
        lines.append(wrapped)
    if idea.get("source_model"):
        lines.append(f"{pad}  Model: {idea['source_model']}")
    if idea.get("tags"):
        lines.append(f"{pad}  Tags: {', '.join(idea['tags'])}")
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print(USAGE)
        return

    cmd = sys.argv[1]
    graph = load_graph()

    if cmd == "contradictions":
        clusters = query_contradictions(graph)
        if not clusters:
            print("No contradiction clusters found.")
        for i, cluster in enumerate(clusters):
            print(f"\nContradiction Cluster {i+1} ({cluster['size']} ideas):")
            for idea in cluster["ideas"]:
                print(format_idea_brief(idea))

    elif cmd == "convergence":
        convergences = query_convergence(graph)
        if not convergences:
            print("No convergence clusters found.")
        for i, conv in enumerate(convergences[:10]):
            print(f"\nConvergence {i+1}: {conv['center_title']}")
            print(f"  Strength: {conv['convergence_strength']}")
            print(f"  Models: {', '.join(conv['distinct_models'])}")

    elif cmd == "orphans":
        orphans = query_orphans(graph)
        print(f"\n{len(orphans)} orphan ideas found:\n")
        for o in orphans:
            print(format_idea_brief(o))

    elif cmd == "blind-spots":
        spots = query_blind_spots(graph)
        print(f"\n{len(spots)} blind spots found:\n")
        for s in spots:
            print(format_idea_brief(s))

    elif cmd == "lineage":
        if len(sys.argv) < 3:
            print("Usage: python query.py lineage <keyword>")
            return
        keyword = sys.argv[2]
        lineages = query_lineage(graph, keyword)
        if not lineages:
            print(f"No ideas found matching '{keyword}'")
        for lin in lineages:
            print(f"\n{lin['title']} [{lin['status']}]")
            print(f"  Model: {lin['source_model']}")
            import json
            print(f"  Ancestry: {json.dumps(lin['ancestry'], indent=2)}")

    elif cmd == "evolution":
        if len(sys.argv) < 3:
            print("Usage: python query.py evolution <keyword>")
            return
        keyword = sys.argv[2]
        evos = query_evolution(graph, keyword)
        if not evos:
            print(f"No ideas found matching '{keyword}'")
        for evo in evos:
            print(f"\n{evo['status'].upper()}:")
            for idea in evo["ideas"]:
                print(f"  • {idea['title']}")

    elif cmd == "model":
        if len(sys.argv) < 3:
            print("Usage: python query.py model <name>")
            return
        name = sys.argv[2]
        ideas = query_by_model(graph, name)
        print(f"\n{len(ideas)} ideas from model matching '{name}':\n")
        for idea in ideas:
            print(format_idea_brief(idea))

    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Usage: python query.py search <text>")
            return
        text = " ".join(sys.argv[2:])
        results = query_search(graph, text)
        print(f"\n{len(results)} ideas matching '{text}':\n")
        for r in results:
            print(format_idea_brief(r))

    elif cmd == "tags":
        if len(sys.argv) < 3:
            print("Usage: python query.py tags <tag>")
            return
        tag = sys.argv[2]
        ideas = query_tags(graph, tag)
        print(f"\n{len(ideas)} ideas tagged '{tag}':\n")
        for idea in ideas:
            print(format_idea_brief(idea))

    elif cmd == "stats":
        import json
        s = query_stats(graph)
        print(json.dumps(s, indent=2))

    elif cmd == "summary":
        print(graph.summary())

    else:
        print(USAGE)


if __name__ == "__main__":
    main()
