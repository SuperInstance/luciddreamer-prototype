# Knowledge Graph API

### A Recursive Idea Graph That Grows Smarter as You Feed It

> "The knowledge base that holds the ideas also evolves based on the ideas."

The Knowledge Graph is a recursive idea network for teams of AI agents (or humans). It holds ideas as nodes, relationships as edges, and provides structural queries: contradiction detection, convergence clustering, orphan discovery, and lineage tracing. It gets smarter the more you use it.

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Full API Reference](#full-api-reference)
  - [KnowledgeGraph](#knowledgegraph)
  - [IdeaNode](#ideanode)
  - [IdeaType](#ideatype)
  - [IdeaStatus](#ideastatus)
  - [RelationshipType](#relationshiptype)
  - [Connection](#connection)
  - [KnowledgeBase](#knowledgebase)
- [Storage Layers](#storage-layers)
- [CLI](#cli)
- [Example: Research Lab Institutional Knowledge](#example-research-lab-institutional-knowledge)
- [Integration Patterns](#integration-patterns)

---

## Installation

```bash
pip install superinstance-knowledge-base
```

**Requirements:** Python ≥ 3.10

**No required dependencies.** Pure Python standard library.

**Optional dependencies:**

```bash
pip install superinstance-knowledge-base[embeddings]  # ollama for vector embeddings
pip install superinstance-knowledge-base[cloudflare]  # wrangler CLI for D1/Vectorize
pip install superinstance-knowledge-base[dev]         # pytest for tests
```

---

## Quick Start

```python
from knowledge_base import (
    KnowledgeGraph, IdeaNode, IdeaType, IdeaStatus,
    RelationshipType, Connection,
)

# Create the graph
graph = KnowledgeGraph()

# Add ideas
idea1 = IdeaNode(
    title="Music is the system thinking",
    content="When confidence is low, the music sounds uncertain. When high, it resolves.",
    idea_type=IdeaType.INSIGHT,
    source_model="hermes",
)
idea2 = IdeaNode(
    title="Confidence bands map to harmonic territory",
    content="Five bands from uncertain to confident, each with distinct musical parameters.",
    idea_type=IdeaType.TECHNICAL,
    source_model="flash",
    lineage=[idea1.id],  # idea2 evolved from idea1
)

graph.add_idea(idea1)
graph.add_idea(idea2)

# Connect them with a typed relationship
graph.connect(idea2.id, idea1.id, RelationshipType.SUPPORTS, "direct implementation")

# Query the graph
print(graph.summary())
# "Knowledge Graph: 2 ideas, 1 connections, 2 models contributing"

# Find structural patterns
print(graph.find_convergence_clusters())   # ideas that multiple models agree on
print(graph.find_contradictions())         # ideas that conflict
print(graph.find_orphans())               # ideas with no connections
print(graph.trace_lineage(idea2.id, direction="ancestors"))  # idea2 ← idea1
```

---

## Core Concepts

### Idea Types

Every idea in the graph has a type that shapes how it's analyzed:

| Type | Description | Example |
|------|-------------|---------|
| `INSIGHT` | A realized truth or understanding | "Music IS the system thinking" |
| `QUESTION` | An open inquiry | "What happens when confidence bands overlap?" |
| `RISK` | A potential failure mode | "Temporal coherence drift over long sessions" |
| `VISION` | A future aspiration or goal | "Every session becomes a ghost in the gallery" |
| `TECHNICAL` | Implementation detail or spec | "Confidence bands map to harmonic territory" |
| `CREATIVE` | A creative observation or idea | "The room should feel like 2 AM at a dockside bar" |
| `CONTRADICTION` | A noted conflict between ideas | "Wesley sees the shape; Pro sees the system" |
| `PATTERN` | A recurring structure | "Every model that enters The Tap finds its own voice" |
| `BLIND_SPOT` | Something potentially missed | "We haven't considered what happens at 10,000 sessions" |
| `DECISION` | A settled choice | "Use HLS for streaming, not WebRTC" |

### Relationship Types

Ideas are connected with typed edges:

| Relationship | Meaning | Example |
|-------------|---------|---------|
| `EVOLVES_FROM` | This idea grew out of another | idea2 evolves_from idea1 |
| `CONTRADICTS` | This idea conflicts with another | risk contradicts vision |
| `SUPPORTS` | This idea provides evidence for another | technical supports insight |
| `REFINES` | This idea narrows or sharpens another | decision refines question |
| `INSPIRES` | This idea sparked another (creative link) | creative inspires vision |
| `QUESTIONS` | This idea challenges another | question questions assumption |
| `ANSWERS` | This idea resolves a question | decision answers question |
| `CONVERGES_WITH` | Two ideas point to the same conclusion | Two models' insights converge |
| `FORKS_FROM` | This idea took a different branch | approach_B forks_from approach_A |
| `COMPOUNDS` | This idea amplifies another's effect | risk compounds risk |

### Idea Lifecycle

```
SEED → GROWING → MATURE → SUPERSEDED
```

| Status | Meaning |
|--------|---------|
| `SEED` | Just planted, not yet developed |
| `GROWING` | Being actively discussed and connected |
| `MATURE` | Settled, well-connected, accepted |
| `SUPERSEDED` | Replaced by a newer idea (still kept for history) |

---

## Full API Reference

### `KnowledgeGraph`

The main graph structure. Holds all ideas and their connections.

#### Constructor

```python
KnowledgeGraph()
```

Creates an empty graph. No parameters needed.

#### Adding Ideas

##### `KnowledgeGraph.add_idea(idea: IdeaNode) -> None`

Add an idea node to the graph. The idea's `id` must be unique.

```python
idea = IdeaNode(
    title="Decentralized agents need shared memory",
    content="Without a shared knowledge layer, agents rediscover the same things.",
    idea_type=IdeaType.INSIGHT,
    source_model="pro",
)
graph.add_idea(idea)
```

##### `KnowledgeGraph.add_ideas(ideas: list[IdeaNode]) -> None`

Batch-add multiple ideas.

#### Connecting Ideas

##### `KnowledgeGraph.connect(source_id: str, target_id: str, relationship: RelationshipType, note: str = "") -> Connection`

Create a typed edge between two ideas. Both must already exist in the graph.

```python
graph.connect(
    source_id=technical_idea.id,
    target_id=insight_idea.id,
    relationship=RelationshipType.SUPPORTS,
    note="This is the concrete implementation of that insight.",
)
```

##### `KnowledgeGraph.auto_connect() -> int`

Automatically detect and create relationships between ideas using heuristic matching (shared keywords, overlapping themes, common lineage). Returns the number of connections created.

```python
new_connections = graph.auto_connect()
print(f"Auto-detected {new_connections} relationships")
```

#### Querying

##### `KnowledgeGraph.find_contradictions() -> list[list[str]]`

Find clusters of ideas that contradict each other. Returns groups of idea IDs.

```python
conflicts = graph.find_contradictions()
for cluster in conflicts:
    print("CONFLICT:")
    for idea_id in cluster:
        idea = graph.get_idea(idea_id)
        print(f"  · {idea.title}")
```

##### `KnowledgeGraph.find_convergence_clusters() -> list[list[str]]`

Find ideas where multiple independent sources (models) converge on the same conclusion. This is one of the most powerful queries — it reveals ideas that have broad support across different perspectives.

```python
convergences = graph.find_convergence_clusters()
for cluster in convergences:
    models = set()
    for idea_id in cluster:
        idea = graph.get_idea(idea_id)
        models.add(idea.source_model)
    print(f"Convergence across {len(models)} models: {models}")
```

##### `KnowledgeGraph.find_orphans() -> list[str]`

Find ideas with no connections to any other idea. These are potential blind spots or ideas that haven't been developed yet.

```python
orphans = graph.find_orphans()
for idea_id in orphans:
    idea = graph.get_idea(idea_id)
    print(f"ORPHAN: {idea.title} (from {idea.source_model})")
```

##### `KnowledgeGraph.trace_lineage(idea_id: str, direction: str = "ancestors") -> list[str]`

Trace the ancestry or descendants of an idea.

```python
# What ideas led to this one?
ancestors = graph.trace_lineage(idea_id, direction="ancestors")

# What ideas grew from this one?
descendants = graph.trace_lineage(idea_id, direction="descendants")
```

##### `KnowledgeGraph.get_idea(idea_id: str) -> IdeaNode | None`

Retrieve a specific idea by ID.

##### `KnowledgeGraph.get_connections(idea_id: str) -> list[Connection]`

Get all connections (incoming and outgoing) for a specific idea.

##### `KnowledgeGraph.get_by_type(idea_type: IdeaType) -> list[IdeaNode]`

Filter ideas by type.

```python
all_risks = graph.get_by_type(IdeaType.RISK)
all_questions = graph.get_by_type(IdeaType.QUESTION)
```

##### `KnowledgeGraph.get_by_model(model_name: str) -> list[IdeaNode]`

Filter ideas by which model produced them.

```python
flash_ideas = graph.get_by_model("flash")
```

##### `KnowledgeGraph.get_by_status(status: IdeaStatus) -> list[IdeaNode]`

Filter ideas by lifecycle status.

##### `KnowledgeGraph.search(query: str) -> list[IdeaNode]`

Simple text search across idea titles and content.

```python
results = graph.search("confidence")
```

#### Graph Analysis

##### `KnowledgeGraph.summary() -> str`

Human-readable summary of the graph state.

```python
print(graph.summary())
# "Knowledge Graph: 47 ideas, 132 connections, 5 models contributing.
#  Types: 12 INSIGHT, 8 QUESTION, 5 RISK, 3 VISION, 15 TECHNICAL, 4 OTHER.
#  Status: 8 SEED, 22 GROWING, 15 MATURE, 2 SUPERSEDED."
```

##### `KnowledgeGraph.model_agreement(model_a: str, model_b: str) -> float`

Calculate how often two models' ideas converge (0.0–1.0). Useful for understanding model relationships.

```python
agreement = graph.model_agreement("flash", "pro")
print(f"Flash and Pro agree {agreement*100:.0f}% of the time")
```

##### `KnowledgeGraph.density() -> float`

Graph density (ratio of actual connections to possible connections). Higher density = more interconnected.

---

### `IdeaNode`

The fundamental unit of the graph. Represents a single idea, observation, question, or decision.

#### Constructor

```python
IdeaNode(
    title: str,
    content: str,
    idea_type: IdeaType = IdeaType.INSIGHT,
    status: IdeaStatus = IdeaStatus.SEED,
    source_model: str = "",
    source_session: str = "",
    tags: list[str] = [],
    lineage: list[str] = [],   # parent idea IDs
    confidence: float = 1.0,
)
```

#### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | `str` | auto-generated | Unique identifier (UUID) |
| `title` | `str` | — | Short title (1–100 chars) |
| `content` | `str` | — | Full idea text |
| `idea_type` | `IdeaType` | `INSIGHT` | Categorization |
| `status` | `IdeaStatus` | `SEED` | Lifecycle stage |
| `source_model` | `str` | `""` | Which model produced this |
| `source_session` | `str` | `""` | Which session produced this |
| `tags` | `list[str]` | `[]` | Freeform tags for filtering |
| `lineage` | `list[str]` | `[]` | Parent idea IDs (evolutionary ancestry) |
| `confidence` | `float` | `1.0` | Confidence in this idea (0.0–1.0) |
| `created_at` | `float` | now() | Creation timestamp |
| `updated_at` | `float` | now() | Last modification timestamp |

---

### `IdeaType`

Enum of idea categories.

```python
from knowledge_base import IdeaType

IdeaType.INSIGHT        # A realized truth
IdeaType.QUESTION       # An open inquiry
IdeaType.RISK           # A potential failure mode
IdeaType.VISION         # A future aspiration
IdeaType.TECHNICAL      # Implementation detail
IdeaType.CREATIVE       # Creative observation
IdeaType.CONTRADICTION  # A noted conflict
IdeaType.PATTERN        # A recurring structure
IdeaType.BLIND_SPOT     # Something potentially missed
IdeaType.DECISION       # A settled choice
```

---

### `IdeaStatus`

```python
from knowledge_base import IdeaStatus

IdeaStatus.SEED        # Just planted
IdeaStatus.GROWING     # Being discussed
IdeaStatus.MATURE      # Settled and connected
IdeaStatus.SUPERSEDED  # Replaced by a newer idea
```

---

### `RelationshipType`

```python
from knowledge_base import RelationshipType

RelationshipType.EVOLVES_FROM    # This idea grew out of another
RelationshipType.CONTRADICTS    # This idea conflicts with another
RelationshipType.SUPPORTS       # This idea provides evidence
RelationshipType.REFINES        # This idea narrows another
RelationshipType.INSPIRES       # This idea sparked another
RelationshipType.QUESTIONS      # This idea challenges another
RelationshipType.ANSWERS        # This idea resolves a question
RelationshipType.CONVERGES_WITH # Two ideas point to the same conclusion
RelationshipType.FORKS_FROM     # This idea took a different branch
RelationshipType.COMPOUNDS      # This idea amplifies another
```

---

### `Connection`

Represents an edge between two ideas.

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `source_id` | `str` | Source idea ID |
| `target_id` | `str` | Target idea ID |
| `relationship` | `RelationshipType` | Edge type |
| `note` | `str` | Human-readable explanation |
| `created_at` | `float` | Timestamp |

---

### `KnowledgeBase`

Higher-level wrapper that combines the `KnowledgeGraph` with persistence and vector search. Use this for production applications.

#### Constructor

```python
from knowledge_base import KnowledgeBase

kb = KnowledgeBase(
    graph=None,             # auto-creates empty KnowledgeGraph
    storage=None,           # defaults to LocalStore
    vector_store=None,      # defaults to None (disabled)
)
```

#### Methods

##### `KnowledgeBase.add_idea(idea: IdeaNode) -> None`

Add an idea and optionally generate embeddings.

##### `KnowledgeBase.save() -> None`

Persist the graph to the configured storage backend.

##### `KnowledgeBase.load() -> None`

Load the graph from storage.

##### `KnowledgeBase.semantic_search(query: str, limit: int = 10) -> list[IdeaNode]`

Semantic search using vector embeddings (requires ollama running locally with `nomic-embed-text`).

```python
results = kb.semantic_search("how do we handle uncertainty in the system?", limit=5)
```

##### `KnowledgeBase.export_d1(path: str = "./d1_migration") -> str`

Generate SQL migration files for Cloudflare D1 deployment.

##### `KnowledgeBase.export_vectorize(path: str = "./vectorize_export.jsonl") -> str`

Generate JSONL file for Cloudflare Vectorize ingestion.

---

## Storage Layers

### Local Store (Default)

Pickle-based persistence. No network needed.

```python
from knowledge_base import KnowledgeBase, LocalStore

kb = KnowledgeBase(storage=LocalStore(path="./knowledge_base.pkl"))
kb.add_idea(idea)
kb.save()  # writes to disk
# Later:
kb.load()  # restores from disk
```

### Cloudflare D1 (Optional)

SQL schema for structural queries via Workers.

```python
kb.export_d1("./d1_migration")
# Generates:
#   ./d1_migration/001_create_tables.sql
#   ./d1_migration/002_seed_data.sql
```

Deploy:

```bash
wrangler d1 create luciddreamer-knowledge
wrangler d1 execute luciddreamer-knowledge --file=./d1_migration/001_create_tables.sql
wrangler d1 execute luciddreamer-knowledge --file=./d1_migration/002_seed_data.sql
```

### Cloudflare Vectorize (Optional)

Semantic search embeddings via Ollama (`nomic-embed-text`, 768 dimensions).

```python
kb.export_vectorize("./vectorize_export.jsonl")
# Generates JSONL with embeddings for Vectorize ingestion
```

Deploy:

```bash
wrangler vectorize create luciddreamer-embeddings --dimensions 768
# Upload JSONL via Workers API
```

---

## CLI

```bash
# Find contradictions
python -m knowledge_base.query contradictions

# Find convergence clusters
python -m knowledge_base.query convergence

# Find orphan ideas
python -m knowledge_base.query orphans

# Trace lineage of a specific idea
python -m knowledge_base.query lineage presence

# Filter by model
python -m knowledge_base.query model hermes

# Full-text search
python -m knowledge_base.query search "first listener"

# Graph statistics
python -m knowledge_base.query stats
```

---

## Example: Research Lab Institutional Knowledge

This example shows how a research lab can use the Knowledge Graph to capture and query institutional knowledge from multiple team members and AI agents.

```python
from knowledge_base import (
    KnowledgeGraph, IdeaNode, IdeaType, IdeaStatus,
    RelationshipType, KnowledgeBase,
)
from datetime import datetime

# -----------------------------------------------------------------------
# 1. Initialize the knowledge base with persistence
# -----------------------------------------------------------------------

kb = KnowledgeBase()
graph = kb.graph

# -----------------------------------------------------------------------
# 2. Team members add ideas from experiments and literature reviews
# -----------------------------------------------------------------------

# Dr. Chen's insight from a protein folding experiment
chens_insight = IdeaNode(
    title="AlphaFold confidence scores correlate with wet-lab stability",
    content=(
        "Across 47 targets, AF2 pLDDT scores > 80 predicted "
        "thermal stability (Tm) within 3°C. Scores 50-70 were unreliable."
    ),
    idea_type=IdeaType.INSIGHT,
    source_model="dr_chen",
    tags=["alphafold", "protein_stability", "wet_lab"],
    status=IdeaStatus.GROWING,
)
graph.add_idea(chens_insight)

# Dr. Patel's contradicting finding
patels_finding = IdeaNode(
    title="AlphaFold confidence unreliable for membrane proteins",
    content=(
        "In our membrane protein study (n=23), pLDDT > 80 still "
        "showed 40% misfolding rate in detergents. The confidence "
        "scores don't account for lipid environment."
    ),
    idea_type=IdeaType.RISK,
    source_model="dr_patel",
    tags=["alphafold", "membrane_proteins", "caveat"],
    status=IdeaStatus.GROWING,
)
graph.add_idea(patels_finding)

# Mark's technical observation
marks_observation = IdeaNode(
    title="MD simulations after AF2 prediction improve reliability",
    content=(
        "Running 100ns MD relaxation after AF2 prediction catches "
        "false-confidence cases. RMSD > 3Å during MD correlates with "
        "wet-lab failure regardless of pLDDT."
    ),
    idea_type=IdeaType.TECHNICAL,
    source_model="mark_grad",
    tags=["md_simulations", "validation", "reliability"],
    lineage=[chens_insight.id, patels_finding.id],
)
graph.add_idea(marks_observation)

# A question from a new student
student_question = IdeaNode(
    title="Can we combine pLDDT + MD RMSD into a composite score?",
    content=(
        "If pLDDT and MD RMSD each have partial predictive power, "
        "maybe a composite metric would be more robust than either alone?"
    ),
    idea_type=IdeaType.QUESTION,
    source_model="sarah_new",
    tags=["composite_score", "methodology"],
    lineage=[marks_observation.id],
)
graph.add_idea(student_question)

# -----------------------------------------------------------------------
# 3. Connect the ideas
# -----------------------------------------------------------------------

# Patel's finding contradicts Chen's initial insight
graph.connect(
    patels_finding.id, chens_insight.id,
    RelationshipType.CONTRADICTS,
    "Membrane proteins are an exception to the general pLDDT correlation"
)

# Mark's observation refines both
graph.connect(
    marks_observation.id, chens_insight.id,
    RelationshipType.REFINES,
    "MD relaxation adds a validation layer"
)
graph.connect(
    marks_observation.id, patels_finding.id,
    RelationshipType.REFINES,
    "MD catches the false-confidence cases Patel identified"
)

# Student's question is inspired by the technical observation
graph.connect(
    student_question.id, marks_observation.id,
    RelationshipType.INSPIRES,
    "The composite score idea came from combining both metrics"
)

# -----------------------------------------------------------------------
# 4. Query the graph for insights
# -----------------------------------------------------------------------

print("=== GRAPH SUMMARY ===")
print(graph.summary())

print("\n=== CONTRADICTIONS ===")
contradictions = graph.find_contradictions()
for cluster in contradictions:
    print("Conflict cluster:")
    for idea_id in cluster:
        idea = graph.get_idea(idea_id)
        print(f"  · [{idea.idea_type.value}] {idea.title}")
        print(f"    by {idea.source_model}")

print("\n=== CONVERGENCE ===")
# Ideas from different people that agree
convergences = graph.find_convergence_clusters()
for cluster in convergences:
    models = {graph.get_idea(i).source_model for i in cluster}
    if len(models) > 1:
        print(f"Multi-researcher agreement ({models}):")
        for idea_id in cluster:
            idea = graph.get_idea(idea_id)
            print(f"  · {idea.title}")

print("\n=== ORPHANS ===")
orphans = graph.find_orphans()
if orphans:
    for idea_id in orphans:
        idea = graph.get_idea(idea_id)
        print(f"  · {idea.title} (needs connections)")
else:
    print("  No orphans — all ideas are connected.")

print("\n=== LINEAGE: Sarah's question ===")
ancestry = graph.trace_lineage(student_question.id, direction="ancestors")
print("  Sarah's question traces back through:")
for idea_id in ancestry:
    idea = graph.get_idea(idea_id)
    print(f"  ← [{idea.idea_type.value}] {idea.title} ({idea.source_model})")

# -----------------------------------------------------------------------
# 5. Persist for tomorrow
# -----------------------------------------------------------------------

kb.save()
print("\n✓ Knowledge base saved. Institutional memory preserved.")
```

---

## Integration Patterns

### Pattern 1: Conductor Session Ingestion

```python
from conductor import Conductor
from knowledge_base import KnowledgeGraph, IdeaNode, IdeaType

graph = KnowledgeGraph()
conductor = Conductor()

# After a session ends, extract ideas and add to graph
def ingest_session(graph, session):
    """Extract ideas from a completed session and add to the knowledge graph."""
    for message in session.messages:
        if message.role == "agent":
            # In production, use an LLM to classify and extract ideas
            idea = IdeaNode(
                title=message.content[:80],
                content=message.content,
                idea_type=IdeaType.INSIGHT,
                source_model=message.agent_name,
                source_session=session.session_id,
            )
            graph.add_idea(idea)

    # Auto-detect relationships
    graph.auto_connect()
```

### Pattern 2: Real-Time Contradiction Detection

```python
# Watch for contradictions as ideas stream in
def on_new_idea(idea: IdeaNode):
    graph.add_idea(idea)
    conflicts = graph.find_contradictions()
    if conflicts:
        for cluster in conflicts:
            if idea.id in cluster:
                print(f"⚠ CONTRADICTION DETECTED with new idea: {idea.title}")
                for cid in cluster:
                    if cid != idea.id:
                        other = graph.get_idea(cid)
                        print(f"  Conflicts with: {other.title} ({other.source_model})")
```

### Pattern 3: Semantic Search via Vectorize

```python
from knowledge_base import KnowledgeBase

kb = KnowledgeBase(vector_store="vectorize")

# Find ideas semantically similar to a query
results = kb.semantic_search(
    "how do we handle model uncertainty in production?",
    limit=10,
)
for idea in results:
    print(f"  [{idea.confidence:.0%}] {idea.title} — {idea.source_model}")
```

### Pattern 4: Decision Audit Trail

```python
# When a decision is made, trace its full lineage
decision = graph.get_idea("decision-uuid")
lineage = graph.trace_lineage(decision.id, direction="ancestors")

print(f"Decision: {decision.title}")
print(f"\nBased on {len(lineage)} prior ideas:")
for idea_id in lineage:
    idea = graph.get_idea(idea_id)
    depth = lineage.index(idea_id) + 1
    print(f"  {'  ' * depth}← [{idea.idea_type.value}] {idea.title}")
    print(f"  {'  ' * depth}  by {idea.source_model} on {idea.created_at}")
```

---

## License

MIT © Lucineer / Casey DiGenaro
