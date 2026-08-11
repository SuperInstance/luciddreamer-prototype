# Recursive Knowledge Base for SuperInstance

**What this is:** A structured knowledge base that holds the fleet's ideas, relationships, evolutions, and contradictions — and grows smarter as we feed it.

## Architecture

```
knowledge-base/
├── idea_schema.py          # Data structures (IdeaNode, SessionNode, ModelNode, RelationshipEdge)
├── knowledge_graph.py      # Graph layer (contradictions, convergence, orphans, lineage)
├── vector_integration.py   # Dual storage (local pickle + D1 + Vectorize)
├── ingest_session.py       # Markdown extraction (Tap sessions → ideas)
├── query.py                # Query CLI
├── build_knowledge_base.py # One-shot builder that ingests all sources
├── knowledge_base.pkl      # The built graph (1042 ideas, 135 relationships)
├── tests/
│   └── test_knowledge_base.py  # 30 tests, all passing
├── d1-migrations/          # SQL exports for Cloudflare D1
└── vectorize-data/         # JSONL exports for Cloudflare Vectorize
```

## Current State

After ingesting 37 source documents (Shipwright's Notebook, 4 vision docs, 4 deep-time essays, 3 architecture docs, 2 landscape reports, 23 Tap sessions):

| Metric | Count |
|--------|-------|
| Total ideas | 1,042 |
| Total relationships | 135 |
| Contradiction clusters | 3 |
| Convergence clusters | 6 |
| Orphan ideas | 580 |
| Sessions | 37 |
| Fleet models tracked | 12 |

### Ideas by Type
- **insight**: 528
- **question**: 179
- **technical**: 143
- **vision**: 39
- **risk**: 35
- **decision**: 34
- **creative**: 32
- **blind_spot**: 26
- **pattern**: 22
- **contradiction**: 4

### Ideas by Model
- **DeepSeek V4-Flash**: 481
- **GLM-5.2 (Lucineer)**: 325
- **Wesley (granite)**: 142
- **Hermes-3-405B**: 94

## Usage

```bash
# Query the knowledge base
python3 query.py contradictions     # Show contradiction clusters
python3 query.py convergence        # Show convergence clusters
python3 query.py orphans            # Show unconnected ideas
python3 query.py blind-spots        # Explicit + orphan blind spots
python3 query.py lineage presence   # Trace how an idea evolved
python3 query.py model hermes       # Ideas from a specific model
python3 query.py search "first listener"  # Full-text search
python3 query.py stats              # Statistics
python3 query.py summary            # Human-readable summary

# Rebuild from sources
python3 build_knowledge_base.py

# Run tests
python3 tests/test_knowledge_base.py
```

## The Recursion

This IS the recursion: the knowledge base that holds the ideas also evolves based on the ideas. New structures emerge. New connections form. The system gets smarter about itself.

Each ingestion run:
1. Extracts ideas from new documents
2. Auto-detects relationships (contradictions, convergence, evolution)
3. Promotes ideas through statuses (seed → growing → mature)
4. Identifies new blind spots
5. Updates the graph for the next query

As more Tap sessions and research docs are added, the graph compounds — exactly like the reef metaphor from the deep-time essays.
