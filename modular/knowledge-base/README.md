# @superinstance/knowledge-base

**A recursive idea graph that grows smarter as you feed it.**

Holds ideas, relationships, evolutions, and contradictions. Pure Python graph layer with optional Cloudflare D1 + Vectorize integration for production scale.

> "The knowledge base that holds the ideas also evolves based on the ideas."

## Install

```bash
pip install superinstance-knowledge-base
```

## Quick Start

```python
from knowledge_base import KnowledgeGraph, IdeaNode, IdeaType, IdeaStatus

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
    lineage=[idea1.id],
)

graph.add_idea(idea1)
graph.add_idea(idea2)
graph.connect(idea2.id, idea1.id, RelationshipType.SUPPORTS, "direct implementation")

# Query the graph
print(graph.summary())
print(graph.find_convergence_clusters())
print(graph.find_orphans())
print(graph.trace_lineage(idea2.id, direction="ancestors"))
```

## What It Does

- **Idea nodes** — insights, questions, risks, visions, technical notes, creative observations, contradictions, patterns, blind spots, decisions
- **Typed relationships** — evolves_from, contradicts, supports, refines, inspires, questions, answers, converges_with, forks_from, compounds
- **Lifecycle tracking** — seed → growing → mature → superseded
- **Structural queries** — contradiction clusters, convergence clusters (cross-model agreement), orphan detection, lineage tracing
- **Auto-relationship detection** — heuristic matching for ideas about the same topic
- **Session & model tracking** — know which session and which model produced each idea

## Storage Layers

### Local (always available)
Pickle-based persistence. No network needed.

```python
from knowledge_base import KnowledgeBase

kb = KnowledgeBase()
kb.add_idea(idea)
kb.save()  # writes knowledge_base.pkl
```

### Cloudflare D1 (optional)
SQL schema generation for structural queries via Workers.

```python
kb.export_d1()  # generates SQL migration files
```

### Cloudflare Vectorize (optional)
Semantic search embeddings via Ollama (nomic-embed-text, 768 dims).

```python
kb.export_vectorize()  # generates JSONL for Vectorize insertion
```

## CLI

```bash
python -m knowledge_base.query contradictions
python -m knowledge_base.query convergence
python -m knowledge_base.query orphans
python -m knowledge_base.query lineage presence
python -m knowledge_base.query model hermes
python -m knowledge_base.query search "first listener"
python -m knowledge_base.query stats
```

## Dependencies

**Required:** None (pure Python)

**Optional:**
- `ollama` (running locally) — for generating embeddings
- `wrangler` CLI — for D1 and Vectorize deployment
- `superinstance/conductor` — for session-aware ingestion

## License

MIT
