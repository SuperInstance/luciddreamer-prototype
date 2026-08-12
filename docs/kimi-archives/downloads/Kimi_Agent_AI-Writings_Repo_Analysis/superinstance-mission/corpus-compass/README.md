# corpus-compass

AI-Writings retrieval + self-indexing. The corpus is write-mostly; this makes
it addressable.

Offline-first: keyword search is SQLite **FTS5 BM25** (stdlib `sqlite3`, no
services). Embeddings are optional and only computed when you ask for them
(local Ollama). No hard dependencies beyond the Python ≥3.10 standard library
(`sqlite3`, `subprocess`, `urllib`, `array`, `math`, `hashlib`, `argparse`).

## Install

```bash
pip install -e .
```

## Commands

```bash
# Index a corpus directory into a sqlite db (incremental: skips unchanged files)
corpus-compass index /path/to/AI-Writings/corpus --db compass.db

# Same, plus embeddings via local Ollama (nomic-embed-text)
corpus-compass index /path/to/AI-Writings/corpus --db compass.db --ollama-embed

# Keyword search (FTS5 BM25 + snippets)
corpus-compass search "anchor chain" --db compass.db

# Vibe search (cosine over embeddings; needs --ollama-embed at index time)
corpus-compass search "a ship that dreams of being a song" --db compass.db --vibe

# Morning briefing from the git log: "The Corpus Indexes Itself — <date>"
corpus-compass digest /path/to/AI-Writings --db compass.db --since "24 hours ago"
```

## What gets indexed

Every `.md` file under the corpus dir becomes a row in
`pieces(id, path, title, series, directory, persona, mtime, body)`, mirrored
into an FTS5 table `pieces_fts(title, body)` (content-synced via triggers).
With `--ollama-embed`, vectors also land in `embeddings(piece_id, vector)`
as float32 BLOBs.

- **title** — first `# Heading`, else first non-empty line, else the filename.
- **series** — leading `NN-` filename prefix, else the directory name.
- **persona** — path-driven, explicit mapping table + `None` fallback:
  - `wesley-stream/**` → `wesley`
  - `qwen-stream/**` → `qwen`
  - `ensemble/<name>-*.md` → `<name>` (token before the first dash)
  - `model-portraits/*.md`, `fetch-riffs/*.md` → leading name token
    (numeric/date tokens skipped)
  - everything else → `None`

## The digest

`corpus-compass digest REPO` runs
`git -C REPO log --since <since> --name-only --pretty=format:`, keeps `.md`
files under the content dirs (`corpus/` by default; `--content-dir` to change),
pulls titles and first lines from the index, and renders
**The Corpus Indexes Itself — \<date\>** with four sections:

- **Night's Catch** — new pieces grouped by directory.
- **New Voices** — personas of the new pieces with nothing in the index older
  than `--since`.
- **Threads to Pull** — 3 archive pieces whose FTS neighborhood overlaps the
  new pieces: the corpus connecting its own roots.
- **Numbers** — counts of the above plus index totals.

`--since` accepts `"N hours/days/weeks ago"`, ISO dates, or unix timestamps.

## FTS5 note

FTS5 ships with CPython's bundled SQLite on all supported platforms
(verified: `python3 -c "import sqlite3; c=sqlite3.connect(':memory:'); c.execute('CREATE VIRTUAL TABLE t USING fts5(x)')"`).
`build_index` probes for FTS5 at startup and raises a clear error if a Python
build lacks it. Should that ever happen, the fallback is a plain inverted-index
BM25 over the `pieces` table (tokenize into `terms(term, piece_id, tf)` and
score with the standard BM25 formula) — same `search()` signature. It is not
shipped because FTS5 is present in every environment we target.

## Tests

```bash
python3 -m pytest -q
```

Fully offline: tests use a ~10-file fixture corpus in `tests/fixtures/`,
a deterministic `HashEmbedder` (token hashing, L2-normalized), and an
injected fake `git_runner`. No network, no Ollama, no git repo needed.

## Run on the boat

24 cores, Ollama at `localhost:11434`, keys in the environment
(`DEEPINFRA_API_KEY`, `DEEPSEEK_API_KEY` — unused here; this package talks
only to local Ollama, and only when asked).

```bash
# one-time, if you want vibe search:
ollama pull nomic-embed-text

cd ~/AI-Writings   # the writings repo (corpus/ inside)
corpus-compass index corpus --db ~/.compass.db
corpus-compass index corpus --db ~/.compass.db --ollama-embed   # optional
corpus-compass search "tide tables" --db ~/.compass.db
corpus-compass search "what the commits say when nobody is reading" --db ~/.compass.db --vibe
corpus-compass digest . --db ~/.compass.db --since "24 hours ago" --out briefing.md
```

Re-run `index` each morning; it is incremental and only touches changed files.
