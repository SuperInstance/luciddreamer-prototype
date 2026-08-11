# 🧠 Knowledge Graph

*Recursive vectorized idea graph for institutional knowledge*

![🧠 Knowledge Graph](docs/images/knowledge-graph.jpg)

## What It Is

Not just semantic search. A STRUCTURED knowledge base that holds ideas, relationships, evolutions, and contradictions — and grows smarter as you feed it.

Ideas have lineage. They evolve from seeds to mature insights. They contradict each other. They converge from independent sources. The system surfaces blind spots and tracks how thinking compounds over time.

## Install

```bash
pip install superinstance-knowledge-base
```

## Features

- IdeaNode with typed relationships (supports/contradicts/evolves/refines)
- Contradiction cluster detection
- Convergence cluster detection (independent agreement)
- Orphan idea detection (blind spots)
- Lineage tracing: seed → growing → mature → superseded
- Triple storage: local pickle + D1 + Cloudflare Vectorize

## Quick Start

```python
from superinstance import knowledge_graph

# See docs/api/knowledge-graph-api.md for full documentation
```

## Use It For

**Research lab tracking how hypotheses evolve, contradict, and converge**

Or anything else. This module is independently useful and Apache-2.0 licensed. Grow it for your industry. Send improvements back.

---

*Part of [LucidDreamer.AI](https://github.com/SuperInstance/luciddreamer-prototype) — built by [SuperInstance](https://github.com/SuperInstance).*
