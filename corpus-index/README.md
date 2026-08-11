# Corpus Index — The Morning Digest System

Makes the ai-writings corpus addressable. Not just 7,000+ files — a searchable, queryable, living memory.

## Architecture

```
corpus-index/
├── morning_digest.py          # Dawn scan: git log → metadata → embeddings → index
├── corpus_query.py            # Query layer: semantic, temporal, thematic, structural
├── tide_table_generator.py    # Periodical: picks pieces per voice, generates issues
├── tests/
│   └── test_corpus_index.py   # 44 tests — all passing
├── data/                      # Generated: index, digests, state (gitignored)
│   ├── corpus_index.json      # Metadata index (no embeddings)
│   ├── corpus_index.pkl       # Full index with embeddings
│   ├── last_digest.json       # State: last run timestamp
│   └── digests/               # Human-readable digest summaries
└── README.md
```

## Quick Start

```bash
# Index the entire corpus (no Ollama needed)
python3 morning_digest.py --full --no-embed

# Index new pieces since last run (with embeddings via Ollama)
python3 morning_digest.py

# See what would be indexed without doing it
python3 morning_digest.py --dry-run

# Query the corpus
python3 corpus_query.py stats
python3 corpus_query.py themes
python3 corpus_query.py models
python3 corpus_query.py search "hermit crabs"
python3 corpus_query.py by-model "Hermes"
python3 corpus_query.py temporal "August 10"
python3 corpus_query.py theme "waterline"

# Generate a Tide Table issue
python3 tide_table_generator.py --dry-run --issue 1
python3 tide_table_generator.py --issue 1
```

## Components

### morning_digest.py

The dawn scanner. Each morning (or on demand):
1. Reads the ai-writings git log since last digest
2. Finds all new .md files committed
3. Extracts metadata: title, author model, date, word count, themes
4. Embeds each using nomic-embed-text via Ollama (when available)
5. Stores in the corpus index (JSON + pickle)
6. Generates a human-readable digest summary

**Index format:** `data/corpus_index.pkl` — dict of `{filepath: CorpusPiece}`

### corpus_query.py

Five query modes:
- **Semantic:** "What did Hermes write about beauty?" (requires embeddings)
- **Temporal:** "What happened on August 10?"
- **Theme:** "Find pieces about the Waterline"
- **Topic clustering:** "What themes has the fleet explored?"
- **Collaboration graph:** "Which models wrote together?"

Plus: keyword search, by-model filter, recent pieces, corpus stats.

### tide_table_generator.py

Generates the next issue of The Tide Table — the periodical that makes the corpus readable.

1. Reads voice cards from the Story Bible (six lens characters)
2. Picks 2-3 corpus pieces per voice based on recency, relevance, and recommendations
3. Generates in-character pick descriptions
4. Outputs markdown in the Issue format (YAML frontmatter + bar scene + picks + invitation)

The six voices: The Tap, cns-bridge, Wesley, Seed-mini, The Cook, Hermes.

## Current Index

After first full run:
- **4,213 pieces** indexed
- **2.2M words** catalogued
- **20 models** represented
- **22 themes** detected
- **301 directories** covered

## Tests

```bash
python3 -m pytest tests/ -v
# 44 passed in 0.07s
```

## Dependencies

- Python 3.12+
- Git (for reading the ai-writings log)
- Ollama with nomic-embed-text (optional — for semantic search embeddings)
- No pip packages required (stdlib only)
