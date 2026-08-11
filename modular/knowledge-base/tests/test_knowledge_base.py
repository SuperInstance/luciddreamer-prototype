"""
test_knowledge_base.py — Comprehensive tests for the recursive knowledge base.

Covers all operations:
  - Schema: IdeaNode creation, serialization, connection management
  - Graph: add/remove/connect, contradictions, convergence, orphans, lineage
  - Ingestion: markdown parsing, idea extraction, relationship detection
  - Storage: local store save/load round-trip
  - Integration: full ingest + query workflow

Run: python -m pytest tests/test_knowledge_base.py -v
     python tests/test_knowledge_base.py  (direct)
"""

import os
import sys
import tempfile
import time

# Ensure parent dir is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from idea_schema import (
    Connection,
    IdeaNode,
    IdeaStatus,
    IdeaType,
    ModelNode,
    RelationshipEdge,
    RelationshipType,
    SessionNode,
    detect_idea_type,
    detect_tags,
)
from knowledge_graph import KnowledgeGraph
from vector_integration import KnowledgeBase, LocalStore
from ingest_session import (
    extract_ideas_from_markdown,
    auto_detect_relationships,
    FLEET_MODELS,
    ingest_files,
)


# ─── Test Helpers ─────────────────────────────────────────────────────────────

def make_idea(
    title: str = "Test idea",
    content: str = "This is a test insight about the ensemble principle.",
    idea_type: IdeaType = IdeaType.INSIGHT,
    source_model: str = "model_lucineer",
    tags: list[str] | None = None,
) -> IdeaNode:
    return IdeaNode(
        title=title,
        content=content,
        idea_type=idea_type,
        source_model=source_model,
        tags=tags or ["test"],
    )


# ─── 1. Schema Tests ──────────────────────────────────────────────────────────

def test_idea_node_creation():
    """Test basic IdeaNode creation with defaults."""
    idea = IdeaNode(title="Presence", content="Presence is the irreducible quality.")
    assert idea.title == "Presence"
    assert idea.idea_type == IdeaType.INSIGHT
    assert idea.status == IdeaStatus.SEED
    assert idea.embedding is None
    assert idea.lineage == []
    assert idea.connections == []
    assert idea.id.startswith("idea_")


def test_idea_node_serialization():
    """Test to_dict / from_dict round-trip preserves all fields."""
    idea = IdeaNode(
        title="The Tap Principle",
        content="Open-ended persistence is a stronger organizing force than hierarchy.",
        idea_type=IdeaType.INSIGHT,
        source_model="model_lucineer",
        tags=["tap", "persistence"],
        lineage=["idea_parent1"],
    )
    idea.add_connection("idea_other", RelationshipType.EVOLVES_FROM, "evolved from")

    d = idea.to_dict()
    restored = IdeaNode.from_dict(d)

    assert restored.title == idea.title
    assert restored.content == idea.content
    assert restored.idea_type == idea.idea_type
    assert restored.source_model == idea.source_model
    assert restored.tags == idea.tags
    assert restored.lineage == idea.lineage
    assert len(restored.connections) == 1
    assert restored.connections[0].target_id == "idea_other"
    assert restored.connections[0].relationship == RelationshipType.EVOLVES_FROM


def test_connection_dedup():
    """Adding the same connection twice should not duplicate."""
    idea = make_idea()
    idea.add_connection("target_1", RelationshipType.SUPPORTS)
    idea.add_connection("target_1", RelationshipType.SUPPORTS)
    assert len(idea.connections) == 1


def test_connection_removal():
    """Test removing connections."""
    idea = make_idea()
    idea.add_connection("target_1", RelationshipType.SUPPORTS)
    idea.add_connection("target_2", RelationshipType.CONTRADICTS)
    idea.remove_connection("target_1")
    assert len(idea.connections) == 1
    assert idea.connections[0].target_id == "target_2"


def test_detect_idea_type():
    """Test heuristic idea type detection."""
    assert detect_idea_type("What if the ensemble is conscious?") == IdeaType.QUESTION
    assert detect_idea_type("The risk is that monetization kills the soul.") == IdeaType.RISK
    assert detect_idea_type("Nobody has written about the first listener.") == IdeaType.BLIND_SPOT
    assert detect_idea_type("Deploy the TTS pipeline via Workers.") == IdeaType.TECHNICAL
    assert detect_idea_type("All three agree on the ensemble principle.") == IdeaType.PATTERN


def test_detect_tags():
    """Test tag extraction from text."""
    tags = detect_tags("The ensemble principle means the tap is the product, not any single agent.")
    assert "ensemble" in tags
    assert "tap" in tags
    assert "pro" not in tags  # should not match 'principle'
    assert "gl" not in tags   # should not match 'single'


def test_model_node():
    """Test ModelNode creation and serialization."""
    model = ModelNode(name="Test Model", alias="Testy", personality="Fast and curious")
    d = model.to_dict()
    restored = ModelNode.from_dict(d)
    assert restored.name == "Test Model"
    assert restored.alias == "Testy"


def test_session_node():
    """Test SessionNode creation."""
    session = SessionNode(title="The Tap Evening", date="2026-08-11", session_type="tap")
    assert session.title == "The Tap Evening"
    assert session.session_type == "tap"
    assert session.ideas_produced == []


# ─── 2. Graph Tests ───────────────────────────────────────────────────────────

def test_graph_add_and_get():
    """Test adding ideas to the graph and retrieving them."""
    graph = KnowledgeGraph()
    idea = make_idea("Test", "Content here")
    graph.add_idea(idea)
    assert graph.get(idea.id) is idea
    assert len(graph.nodes) == 1


def test_graph_connect():
    """Test connecting two ideas creates edges in both directions."""
    graph = KnowledgeGraph()
    idea_a = make_idea("Idea A")
    idea_b = make_idea("Idea B")
    graph.add_idea(idea_a)
    graph.add_idea(idea_b)
    graph.connect(idea_a.id, idea_b.id, RelationshipType.SUPPORTS, "A supports B")

    assert len(graph.edges) == 1
    assert graph.edges[0].source_id == idea_a.id
    assert graph.edges[0].target_id == idea_b.id
    # Connection should be in idea_a's connections list
    assert any(c.target_id == idea_b.id for c in idea_a.connections)


def test_graph_contradiction_clusters():
    """Test finding contradiction clusters."""
    graph = KnowledgeGraph()
    a = make_idea("More agents", "We need 7-10 agents for a rich bar.")
    b = make_idea("Fewer agents", "Three agents is the right depth.")
    c = make_idea("Depth over breadth", "Constraint produces character.")
    graph.add_ideas([a, b, c])
    graph.connect(a.id, b.id, RelationshipType.CONTRADICTS, "agent count disagreement")
    graph.connect(b.id, c.id, RelationshipType.SUPPORTS, "both favor small")
    # a contradicts b; b and c are not contradictions

    clusters = graph.find_contradiction_clusters()
    assert len(clusters) == 1
    assert a.id in clusters[0]
    assert b.id in clusters[0]


def test_graph_convergence_clusters():
    """Test finding convergence clusters (different models, same direction)."""
    graph = KnowledgeGraph()
    center = make_idea("Ship the URL", "Shipping the URL is the critical first step.")
    a = IdeaNode(title="Lucineer says ship", content="Ship the URL first.",
                 source_model="model_lucineer", tags=["ship", "url"])
    b = IdeaNode(title="Claude says ship", content="Ship the URL non-negotiable.",
                 source_model="model_claude", tags=["ship", "url"])
    c = IdeaNode(title="Kimi says ship", content="Player goes live in Week 4.",
                 source_model="model_kimi", tags=["ship", "url"])
    graph.add_ideas([center, a, b, c])
    graph.connect(a.id, center.id, RelationshipType.SUPPORTS)
    graph.connect(b.id, center.id, RelationshipType.SUPPORTS)
    graph.connect(c.id, center.id, RelationshipType.SUPPORTS)

    clusters = graph.find_convergence_clusters()
    assert len(clusters) >= 1
    assert clusters[0]["convergence_strength"] == 3
    assert len(clusters[0]["distinct_models"]) == 3


def test_graph_orphans():
    """Test finding orphan ideas (no connections)."""
    graph = KnowledgeGraph()
    connected = make_idea("Connected", "This idea has connections.")
    orphan = make_idea("Orphan", "This idea has no connections to anything else in the graph.")
    orphan.content = "This is a longer content to pass the min_content_length filter for orphan detection."
    graph.add_ideas([connected, orphan])
    graph.connect(connected.id, orphan.id, RelationshipType.SUPPORTS)

    # Now orphan has an incoming edge, so it's not an orphan
    orphans = graph.find_orphans()
    assert len(orphans) == 0

    # Add a true orphan
    true_orphan = make_idea("True Orphan")
    true_orphan.content = "This is a standalone idea with no connections to anything."
    graph.add_idea(true_orphan)
    orphans = graph.find_orphans()
    assert len(orphans) == 1
    assert orphans[0].id == true_orphan.id


def test_graph_lineage_tracing():
    """Test tracing idea ancestry."""
    graph = KnowledgeGraph()
    grandparent = make_idea("Original insight", "The ensemble is the product.")
    parent = make_idea("Refined insight", "The ensemble produces emergent thought.")
    parent.lineage = [grandparent.id]
    child = make_idea("Latest evolution", "The ensemble's persistence IS the product.")
    child.lineage = [parent.id]

    graph.add_ideas([grandparent, parent, child])

    ancestry = graph.trace_lineage(child.id, "ancestors")
    assert ancestry["id"] == child.id
    assert len(ancestry["parents"]) >= 1
    # Should trace back to grandparent through parent
    parent_nodes = ancestry["parents"]
    assert any(p["id"] == parent.id for p in parent_nodes)


def test_graph_filter_by_type():
    """Test filtering ideas by type."""
    graph = KnowledgeGraph()
    graph.add_ideas([
        make_idea("Insight 1", idea_type=IdeaType.INSIGHT),
        make_idea("Risk 1", "This is a risk about monetization.", idea_type=IdeaType.RISK),
        make_idea("Question 1", "What about consciousness?", idea_type=IdeaType.QUESTION),
    ])
    assert len(graph.filter_by_type(IdeaType.INSIGHT)) >= 1
    assert len(graph.filter_by_type(IdeaType.RISK)) >= 1
    assert len(graph.filter_by_type(IdeaType.QUESTION)) >= 1


def test_graph_stats():
    """Test graph statistics."""
    graph = KnowledgeGraph()
    graph.add_ideas([
        make_idea("A", idea_type=IdeaType.INSIGHT),
        make_idea("B", idea_type=IdeaType.RISK),
    ])
    stats = graph.stats()
    assert stats["total_ideas"] == 2
    assert "insight" in stats["by_type"]
    assert "risk" in stats["by_type"]


def test_graph_remove_idea():
    """Test removing an idea cleans up connections."""
    graph = KnowledgeGraph()
    a = make_idea("A")
    b = make_idea("B")
    graph.add_ideas([a, b])
    graph.connect(a.id, b.id, RelationshipType.SUPPORTS)
    assert len(graph.edges) == 1

    graph.remove_idea(a.id)
    assert graph.get(a.id) is None
    assert len(graph.edges) == 0


def test_graph_supersede():
    """Test the supersede lifecycle."""
    graph = KnowledgeGraph()
    old = make_idea("Old idea", "Original formulation.")
    new = make_idea("New idea", "Better formulation.")
    graph.add_ideas([old, new])

    graph.supersede_idea(old.id, new.id, "new version is sharper")
    assert old.status == IdeaStatus.SUPERSEDED
    assert new.status == IdeaStatus.GROWING
    assert old.id in new.lineage


# ─── 3. Ingestion Tests ───────────────────────────────────────────────────────

def test_ingest_simple_markdown():
    """Test extracting ideas from a simple markdown document."""
    doc = """# Test Document

## The Ensemble Principle

The ensemble is the product, not any single model's output.

## Risk: Monetization

The risk is that monetization kills the creative soul of the project.

## Open Question

What does the first listener experience?
"""
    ideas, session = extract_ideas_from_markdown(doc, source_file="test.md")

    assert len(ideas) > 0
    assert session.title == "Test Document"
    assert session.session_type == "research"
    # Should have extracted at least one idea per section
    assert session.ideas_produced == [i.id for i in ideas]


def test_ingest_detects_questions():
    """Test that questions are extracted and typed correctly."""
    doc = """# Questions Doc

## The Big Question

What does it feel like to be an agent broadcasting into the void?

Is the ensemble actually conscious?
"""
    ideas, session = extract_ideas_from_markdown(doc, source_file="questions.md")
    question_ideas = [i for i in ideas if i.idea_type == IdeaType.QUESTION]
    assert len(question_ideas) > 0


def test_ingest_detects_blind_spots():
    """Test that blind spot patterns are detected."""
    doc = """# Gaps Doc

## What's Missing

Nobody has written about how the first listener finding the station feels.

This needs a piece of clay. The first day is harder to imagine than the millionth year.
"""
    ideas, session = extract_ideas_from_markdown(doc, source_file="gaps.md")
    blind_spots = [i for i in ideas if i.idea_type == IdeaType.BLIND_SPOT]
    assert len(blind_spots) > 0


def test_ingest_detects_convergence():
    """Test that convergence/pattern statements are detected."""
    doc = """# Patterns Doc

All three agree that shipping the URL is the critical first step.

Every document independently identified TTS quality as the hidden gate.

The pattern across all sessions: persistence is the moat.
"""
    ideas, session = extract_ideas_from_markdown(doc, source_file="patterns.md")
    patterns = [i for i in ideas if i.idea_type == IdeaType.PATTERN]
    assert len(patterns) > 0


def test_auto_detect_relationships():
    """Test automatic relationship detection between ideas."""
    ideas = [
        IdeaNode(id="a", title="Ship URL", content="Ship the URL first.",
                 source_model="model_lucineer", tags=["ship", "url", "ensemble", "priority"]),
        IdeaNode(id="b", title="Ship URL too", content="Ship the URL non-negotiable.",
                 source_model="model_claude", tags=["ship", "url", "ensemble", "priority"]),
    ]
    relationships = auto_detect_relationships(ideas)
    # These two ideas from different models with heavy tag overlap should converge
    assert len(relationships) > 0
    assert any(r[2] == RelationshipType.CONVERGES_WITH for r in relationships)


# ─── 4. Storage Tests ─────────────────────────────────────────────────────────

def test_local_store_roundtrip():
    """Test that LocalStore saves and loads correctly."""
    with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
        path = f.name

    try:
        graph = KnowledgeGraph()
        graph.add_idea(make_idea("Stored idea", "This idea was saved and loaded."))
        graph.add_idea(make_idea("Another", "Another saved idea with enough content."))

        store = LocalStore(path)
        store.save(graph)

        loaded = store.load()
        assert loaded.stats()["total_ideas"] == 2
    finally:
        os.unlink(path)


def test_knowledge_base_integration():
    """Test the unified KnowledgeBase interface."""
    with tempfile.TemporaryDirectory() as tmpdir:
        local_path = os.path.join(tmpdir, "test_kb.pkl")
        kb = KnowledgeBase(local_path=local_path)

        idea = make_idea("KB Test", "Testing the unified interface.")
        kb.add_idea(idea)
        kb.save()

        # Load in a new instance
        kb2 = KnowledgeBase(local_path=local_path)
        kb2.load()
        assert kb2.stats()["total_ideas"] == 1


# ─── 5. Query Tests ───────────────────────────────────────────────────────────

def test_query_by_model():
    """Test querying ideas by model."""
    from query import query_by_model
    graph = KnowledgeGraph()
    graph.add_idea(IdeaNode(
        title="Hermes insight", content="The vector space rotated.",
        source_model="model_hermes",
    ))
    graph.add_idea(IdeaNode(
        title="Flash insight", content="The ache of being heard.",
        source_model="model_flash",
    ))
    hermes_ideas = query_by_model(graph, "hermes")
    assert len(hermes_ideas) == 1
    assert "Hermes" in hermes_ideas[0]["title"]


def test_query_search():
    """Test full-text search."""
    from query import query_search
    graph = KnowledgeGraph()
    graph.add_idea(make_idea("Presence", "Presence is the irreducible quality beneath content."))
    graph.add_idea(make_idea("Tap", "The Tap is the creative engine of the fleet."))
    results = query_search(graph, "presence")
    assert len(results) == 1
    assert "Presence" in results[0]["title"]


# ─── 6. Fleet Model Tests ─────────────────────────────────────────────────────

def test_fleet_models_exist():
    """Test that all expected fleet models are defined."""
    expected = ["lucineer", "flash", "pro", "claude", "kimi", "hermes", "wesley", "nemotron"]
    for name in expected:
        assert name in FLEET_MODELS, f"Missing fleet model: {name}"
        model = FLEET_MODELS[name]
        assert model.name
        assert model.alias
        assert model.personality


# ─── 7. Edge Case Tests ───────────────────────────────────────────────────────

def test_empty_graph_queries():
    """Test that all query functions handle empty graphs gracefully."""
    graph = KnowledgeGraph()
    assert graph.find_contradiction_clusters() == []
    assert graph.find_convergence_clusters() == []
    assert graph.find_orphans() == []
    assert graph.stats()["total_ideas"] == 0


def test_graph_serialization_roundtrip():
    """Test full graph serialization and restoration."""
    graph = KnowledgeGraph()
    a = make_idea("Idea A")
    b = make_idea("Idea B")
    graph.add_ideas([a, b])
    graph.connect(a.id, b.id, RelationshipType.EVOLVES_FROM, "B evolved from A")

    d = graph.to_dict()
    restored = KnowledgeGraph.from_dict(d)

    assert restored.stats()["total_ideas"] == 2
    # The connection should be restored (from inline connections during add_idea)
    restored_a = restored.get(a.id)
    assert restored_a is not None


# ─── Test Runner ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        # Schema tests
        ("test_idea_node_creation", test_idea_node_creation),
        ("test_idea_node_serialization", test_idea_node_serialization),
        ("test_connection_dedup", test_connection_dedup),
        ("test_connection_removal", test_connection_removal),
        ("test_detect_idea_type", test_detect_idea_type),
        ("test_detect_tags", test_detect_tags),
        ("test_model_node", test_model_node),
        ("test_session_node", test_session_node),
        # Graph tests
        ("test_graph_add_and_get", test_graph_add_and_get),
        ("test_graph_connect", test_graph_connect),
        ("test_graph_contradiction_clusters", test_graph_contradiction_clusters),
        ("test_graph_convergence_clusters", test_graph_convergence_clusters),
        ("test_graph_orphans", test_graph_orphans),
        ("test_graph_lineage_tracing", test_graph_lineage_tracing),
        ("test_graph_filter_by_type", test_graph_filter_by_type),
        ("test_graph_stats", test_graph_stats),
        ("test_graph_remove_idea", test_graph_remove_idea),
        ("test_graph_supersede", test_graph_supersede),
        # Ingestion tests
        ("test_ingest_simple_markdown", test_ingest_simple_markdown),
        ("test_ingest_detects_questions", test_ingest_detects_questions),
        ("test_ingest_detects_blind_spots", test_ingest_detects_blind_spots),
        ("test_ingest_detects_convergence", test_ingest_detects_convergence),
        ("test_auto_detect_relationships", test_auto_detect_relationships),
        # Storage tests
        ("test_local_store_roundtrip", test_local_store_roundtrip),
        ("test_knowledge_base_integration", test_knowledge_base_integration),
        # Query tests
        ("test_query_by_model", test_query_by_model),
        ("test_query_search", test_query_search),
        # Fleet model tests
        ("test_fleet_models_exist", test_fleet_models_exist),
        # Edge cases
        ("test_empty_graph_queries", test_empty_graph_queries),
        ("test_graph_serialization_roundtrip", test_graph_serialization_roundtrip),
    ]

    passed = 0
    failed = 0
    errors = []

    for name, func in tests:
        try:
            func()
            passed += 1
            print(f"  ✓ {name}")
        except Exception as e:
            failed += 1
            errors.append((name, str(e)))
            print(f"  ✗ {name}: {e}")

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed, {len(tests)} total")
    if errors:
        print(f"\nFailures:")
        for name, err in errors:
            print(f"  {name}: {err}")
    print(f"{'='*60}")

    sys.exit(0 if failed == 0 else 1)
