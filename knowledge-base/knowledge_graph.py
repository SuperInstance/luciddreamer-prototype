"""
knowledge_graph.py — A graph layer over IdeaNodes.

The graph layer provides structural queries that semantic search can't:
  - Find contradiction clusters (ideas that disagree)
  - Find convergence clusters (ideas from different sources pointing the same direction)
  - Find orphan ideas (high quality but unconnected — potential blind spots)
  - Trace idea evolution: seed → growing → mature
  - Find lineages (how ideas compound across sessions)

Pure Python. No external deps beyond dataclasses, typing, and collections.
Works on lists of IdeaNodes directly — no database required for local operation.
"""

from __future__ import annotations

import textwrap
from collections import defaultdict, deque
from typing import Optional

from idea_schema import (
    Connection,
    IdeaNode,
    IdeaStatus,
    IdeaType,
    RelationshipEdge,
    RelationshipType,
)


class KnowledgeGraph:
    """
    In-memory graph over IdeaNodes. Supports:
      - Add/remove ideas and connections
      - Query by type, status, model, session, tags
      - Find contradiction clusters
      - Find convergence clusters
      - Find orphan ideas
      - Trace idea evolution and lineages
      - Compute graph statistics
    """

    def __init__(self) -> None:
        self.nodes: dict[str, IdeaNode] = {}
        self._edges: list[RelationshipEdge] = []
        self._adjacency: dict[str, list[tuple[str, RelationshipType]]] = defaultdict(list)
        self._reverse_adjacency: dict[str, list[tuple[str, RelationshipType]]] = defaultdict(list)

    # ─── Building the Graph ───────────────────────────────────────────────

    def add_idea(self, idea: IdeaNode) -> None:
        """Add an idea node to the graph, indexing its connections."""
        self.nodes[idea.id] = idea
        for conn in idea.connections:
            self._register_edge(idea.id, conn)

    def add_ideas(self, ideas: list[IdeaNode]) -> None:
        """Bulk add ideas."""
        for idea in ideas:
            self.add_idea(idea)

    def remove_idea(self, idea_id: str) -> None:
        """Remove an idea and all its connections."""
        if idea_id not in self.nodes:
            return
        # Remove from adjacency
        for target_id, _ in self._adjacency.get(idea_id, []):
            self._reverse_adjacency[target_id] = [
                (s, r) for s, r in self._reverse_adjacency.get(target_id, [])
                if s != idea_id
            ]
        for source_id, _ in self._reverse_adjacency.get(idea_id, []):
            self._adjacency[source_id] = [
                (t, r) for t, r in self._adjacency.get(source_id, [])
                if t != idea_id
            ]
        self._adjacency.pop(idea_id, None)
        self._reverse_adjacency.pop(idea_id, None)
        # Remove edges
        self._edges = [
            e for e in self._edges
            if e.source_id != idea_id and e.target_id != idea_id
        ]
        del self.nodes[idea_id]

    def connect(
        self,
        source_id: str,
        target_id: str,
        relationship: RelationshipType,
        note: str = "",
        strength: float = 1.0,
    ) -> None:
        """
        Create a typed connection between two ideas.
        Updates both the inline connections and the adjacency indexes.
        """
        if source_id not in self.nodes:
            raise KeyError(f"Source idea {source_id} not in graph")
        if target_id not in self.nodes:
            raise KeyError(f"Target idea {target_id} not in graph")

        conn = Connection(
            target_id=target_id,
            relationship=relationship,
            note=note,
            strength=strength,
        )
        self.nodes[source_id].add_connection(
            target_id, relationship, note, strength
        )
        self._register_edge(source_id, conn)

    def _register_edge(self, source_id: str, conn: Connection) -> None:
        edge = RelationshipEdge(
            source_id=source_id,
            target_id=conn.target_id,
            relationship=conn.relationship,
            note=conn.note,
            strength=conn.strength,
        )
        self._edges.append(edge)
        self._adjacency[source_id].append((conn.target_id, conn.relationship))
        self._reverse_adjacency[conn.target_id].append((source_id, conn.relationship))

    @property
    def edges(self) -> list[RelationshipEdge]:
        return list(self._edges)

    # ─── Basic Queries ────────────────────────────────────────────────────

    def get(self, idea_id: str) -> Optional[IdeaNode]:
        return self.nodes.get(idea_id)

    def filter_by_type(self, idea_type: IdeaType) -> list[IdeaNode]:
        return [n for n in self.nodes.values() if n.idea_type == idea_type]

    def filter_by_status(self, status: IdeaStatus) -> list[IdeaNode]:
        return [n for n in self.nodes.values() if n.status == status]

    def filter_by_model(self, model_id_or_name: str) -> list[IdeaNode]:
        """Return all ideas from a given model (matches ID or name)."""
        results = []
        for node in self.nodes.values():
            if (node.source_model == model_id_or_name or
                model_id_or_name.lower() in node.source_model.lower()):
                results.append(node)
        return results

    def filter_by_session(self, session_id: str) -> list[IdeaNode]:
        return [n for n in self.nodes.values() if n.source_session == session_id]

    def filter_by_tag(self, tag: str) -> list[IdeaNode]:
        return [n for n in self.nodes.values() if tag in n.tags]

    def search_text(self, query: str) -> list[IdeaNode]:
        """Simple text search across title and content."""
        query_lower = query.lower()
        return [
            n for n in self.nodes.values()
            if query_lower in n.title.lower() or query_lower in n.content.lower()
        ]

    # ─── Structural Queries ───────────────────────────────────────────────

    def find_contradiction_clusters(self) -> list[list[str]]:
        """
        Find clusters of ideas that contradict each other.
        Returns lists of idea IDs that participate in contradiction relationships.
        Uses connected components on the contradiction subgraph.
        """
        # Build contradiction-only adjacency
        contradict_adj: dict[str, set[str]] = defaultdict(set)
        for edge in self._edges:
            if edge.relationship == RelationshipType.CONTRADICTS:
                contradict_adj[edge.source_id].add(edge.target_id)
                contradict_adj[edge.target_id].add(edge.source_id)

        # Connected components via BFS
        visited: set[str] = set()
        clusters: list[list[str]] = []
        for start in contradict_adj:
            if start in visited:
                continue
            component: list[str] = []
            queue = deque([start])
            while queue:
                node = queue.popleft()
                if node in visited:
                    continue
                visited.add(node)
                component.append(node)
                for neighbor in contradict_adj[node]:
                    if neighbor not in visited:
                        queue.append(neighbor)
            if len(component) > 1:
                clusters.append(component)

        return clusters

    def find_convergence_clusters(self) -> list[dict]:
        """
        Find ideas from DIFFERENT source models/sessions that point
        in the same direction (support or converge_with relationships).

        Returns a list of convergence reports, each containing:
          - idea_ids: the ideas that converge
          - models: the distinct models that produced them
          - center: the idea being supported (if any)
          - strength: aggregate confidence
        """
        # Group supports/converges_by by target
        support_map: dict[str, list[str]] = defaultdict(list)
        for edge in self._edges:
            if edge.relationship in (RelationshipType.SUPPORTS, RelationshipType.CONVERGES_WITH):
                support_map[edge.target_id].append(edge.source_id)

        clusters: list[dict] = []
        for target_id, supporters in support_map.items():
            # Check if supporters come from different models
            models_seen: set[str] = set()
            for sid in supporters:
                node = self.nodes.get(sid)
                if node:
                    models_seen.add(node.source_model)

            if len(models_seen) >= 2:
                target_node = self.nodes.get(target_id)
                clusters.append({
                    "center_idea": target_id,
                    "center_title": target_node.title if target_node else "Unknown",
                    "supporting_ideas": supporters,
                    "distinct_models": list(models_seen),
                    "convergence_strength": len(supporters),
                })

        # Sort by strength (most convergent first)
        clusters.sort(key=lambda c: c["convergence_strength"], reverse=True)
        return clusters

    def find_orphans(self, min_content_length: int = 50) -> list[IdeaNode]:
        """
        Find ideas that have no connections to other ideas.
        These are potential blind spots — ideas that haven't been
        related to the rest of the knowledge base yet.

        Args:
            min_content_length: filter out very short/trivial ideas
        """
        orphans: list[IdeaNode] = []
        for node in self.nodes.values():
            if len(node.content) < min_content_length:
                continue
            has_incoming = node.id in self._reverse_adjacency
            has_outgoing = node.id in self._adjacency
            if not has_incoming and not has_outgoing:
                orphans.append(node)
        return orphans

    def trace_lineage(self, idea_id: str, direction: str = "ancestors") -> dict:
        """
        Trace the lineage of an idea — either its ancestors (what it
        evolved from) or its descendants (what evolved from it).

        Returns a tree structure showing the evolutionary path.
        """
        if direction == "ancestors":
            return self._trace_ancestors(idea_id, set())
        else:
            return self._trace_descendants(idea_id, set())

    def _trace_ancestors(self, idea_id: str, visited: set[str]) -> dict:
        if idea_id in visited:
            return {"id": idea_id, "title": "(cycle)", "parents": []}
        visited.add(idea_id)
        node = self.nodes.get(idea_id)
        if not node:
            return {"id": idea_id, "title": "Unknown", "parents": []}

        parents: list[dict] = []
        # Check explicit lineage
        for parent_id in node.lineage:
            parents.append(self._trace_ancestors(parent_id, visited))
        # Check evolves_from connections
        for conn in node.connections:
            if conn.relationship == RelationshipType.EVOLVES_FROM:
                parents.append(self._trace_ancestors(conn.target_id, visited))
        # Check reverse adjacency for evolves_from pointing to this node
        for source_id, rel in self._reverse_adjacency.get(idea_id, []):
            if rel == RelationshipType.EVOLVES_FROM and source_id not in [p["id"] for p in parents]:
                # source_id evolves_from idea_id — that's descendants, skip
                pass

        return {
            "id": idea_id,
            "title": node.title,
            "type": node.idea_type.value if isinstance(node.idea_type, IdeaType) else str(node.idea_type),
            "status": node.status.value if isinstance(node.status, IdeaStatus) else str(node.status),
            "parents": parents,
        }

    def _trace_descendants(self, idea_id: str, visited: set[str]) -> dict:
        if idea_id in visited:
            return {"id": idea_id, "title": "(cycle)", "children": []}
        visited.add(idea_id)
        node = self.nodes.get(idea_id)
        if not node:
            return {"id": idea_id, "title": "Unknown", "children": []}

        children: list[dict] = []
        # Find ideas that list this one in their lineage or evolves_from
        for other_id, rel_list in self._reverse_adjacency.items():
            for _, rel in rel_list:
                if rel == RelationshipType.EVOLVES_FROM and other_id not in visited:
                    other = self.nodes.get(other_id)
                    if other and idea_id in other.lineage:
                        pass  # Already handled via lineage
                    if other:
                        children.append(self._trace_descendants(other_id, visited))

        # Also check ideas that have this one in their lineage
        for other in self.nodes.values():
            if idea_id in other.lineage and other.id not in visited:
                children.append(self._trace_descendants(other.id, visited))

        return {
            "id": idea_id,
            "title": node.title,
            "type": node.idea_type.value if isinstance(node.idea_type, IdeaType) else str(node.idea_type),
            "status": node.status.value if isinstance(node.status, IdeaStatus) else str(node.status),
            "children": children,
        }

    def trace_evolution(self, keyword: str) -> list[dict]:
        """
        Trace how an idea (identified by keyword search) evolved
        across sessions and models. Returns all matching idea lineages.

        Example: trace_evolution("presence") shows every idea tagged
        with or mentioning "presence" and their evolutionary paths.
        """
        matches = self.search_text(keyword)
        results: list[dict] = []
        for match in matches:
            results.append({
                "idea_id": match.id,
                "title": match.title,
                "status": match.status.value if isinstance(match.status, IdeaStatus) else str(match.status),
                "source_model": match.source_model,
                "source_session": match.source_session,
                "ancestry": self.trace_lineage(match.id, "ancestors"),
            })
        return results

    # ─── Idea Lifecycle ───────────────────────────────────────────────────

    def promote_idea(self, idea_id: str, new_status: IdeaStatus) -> None:
        """Change an idea's status (e.g., seed → growing → mature)."""
        if idea_id in self.nodes:
            self.nodes[idea_id].status = new_status

    def supersede_idea(self, old_id: str, new_id: str, note: str = "") -> None:
        """
        Mark an idea as superseded by a newer one.
        Creates an evolves_from connection from new → old.
        """
        if old_id in self.nodes and new_id in self.nodes:
            self.nodes[old_id].status = IdeaStatus.SUPERSEDED
            self.connect(
                new_id, old_id, RelationshipType.EVOLVES_FROM,
                note=note or "superseded by newer idea"
            )
            self.nodes[new_id].lineage.append(old_id)
            self.promote_idea(new_id, IdeaStatus.GROWING)

    # ─── Statistics ───────────────────────────────────────────────────────

    def stats(self) -> dict:
        """Return summary statistics about the knowledge graph."""
        type_counts: dict[str, int] = defaultdict(int)
        status_counts: dict[str, int] = defaultdict(int)
        model_counts: dict[str, int] = defaultdict(int)
        tag_counts: dict[str, int] = defaultdict(int)

        for node in self.nodes.values():
            t = node.idea_type.value if isinstance(node.idea_type, IdeaType) else str(node.idea_type)
            s = node.status.value if isinstance(node.status, IdeaStatus) else str(node.status)
            type_counts[t] += 1
            status_counts[s] += 1
            model_counts[node.source_model or "unknown"] += 1
            for tag in node.tags:
                tag_counts[tag] += 1

        return {
            "total_ideas": len(self.nodes),
            "total_edges": len(self._edges),
            "by_type": dict(type_counts),
            "by_status": dict(status_counts),
            "by_model": dict(model_counts),
            "top_tags": dict(sorted(tag_counts.items(), key=lambda x: -x[1])[:15]),
            "contradiction_clusters": len(self.find_contradiction_clusters()),
            "convergence_clusters": len(self.find_convergence_clusters()),
            "orphans": len(self.find_orphans()),
        }

    # ─── Serialization ───────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
            "edges": [e.to_dict() for e in self._edges],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "KnowledgeGraph":
        graph = cls()
        for idea_data in d.get("nodes", {}).values():
            graph.add_idea(IdeaNode.from_dict(idea_data))
        # Edges are reconstructed from connections during add_idea
        return graph

    # ─── Pretty Printing ─────────────────────────────────────────────────

    def summary(self) -> str:
        """Human-readable summary of the graph."""
        s = self.stats()
        lines = [
            f"Knowledge Graph Summary",
            f"  Total ideas: {s['total_ideas']}",
            f"  Total edges: {s['total_edges']}",
            f"  Contradiction clusters: {s['contradiction_clusters']}",
            f"  Convergence clusters: {s['convergence_clusters']}",
            f"  Orphan ideas: {s['orphans']}",
            "",
            "  By type:",
        ]
        for t, c in sorted(s["by_type"].items(), key=lambda x: -x[1]):
            lines.append(f"    {t}: {c}")
        lines.append("")
        lines.append("  By status:")
        for st, c in sorted(s["by_status"].items(), key=lambda x: -x[1]):
            lines.append(f"    {st}: {c}")
        lines.append("")
        lines.append("  By model:")
        for m, c in sorted(s["by_model"].items(), key=lambda x: -x[1]):
            lines.append(f"    {m}: {c}")
        return "\n".join(lines)
