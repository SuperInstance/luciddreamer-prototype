# Semantic Bridge — Cloudflare Knowledge Base

The LucidDreamer knowledge base deployed as queryable infrastructure on Cloudflare.

## Architecture

```
Local Pickle (1,042 ideas)
    ↓
    ├── Vectorize (semantic search)
    ├── D1 (structural SQL queries)
    └── Ollama nomic-embed-text (768-dim embeddings)
```

## Components

| File | Purpose |
|------|---------|
| `vectorize_ideas.py` | Embed ideas via Ollama, push to Cloudflare Vectorize |
| `query_cloudflare.py` | Query the Vectorize index (semantic + filtered) |
| `d1_sync.py` | Sync knowledge graph to D1 (ideas, relationships, sessions, models) |
| `deploy.sh` | One-command deploy: index + D1 + vectors + verify |
| `tests/` | 10 tests covering embedding, upload, query, and D1 sync |

## Indexes

- **Vectorize:** `luciddreamer-kb` (768-dim, cosine, nomic-embed-text)
- **D1:** `luciddreamer-kb`

## Quick Start

```bash
./deploy.sh                    # Deploy everything
python query_cloudflare.py "presence"  # Semantic search
python query_cloudflare.py --model hermes  # Filter by model
```

This IS the Molt. The philosophy becomes queryable infrastructure.
