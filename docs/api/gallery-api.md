# Gallery API

### Session Ghost Ledger — Every Conversation Compressed to Its Essence

> Every session a ghost. Every ghost a trace.

The Gallery takes raw conversation sessions and compresses them into **ghosts** — the distilled soul of each conversation. A ghost captures the title, date, models present, key quotes, napkin drawings, themes, and a ~100-word essence. The Gallery serves these ghosts through a RESTful API backed by Cloudflare Workers, D1, and R2.

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Ghost Compression](#ghost-compression)
  - [CLI Usage](#cli-usage)
  - [Programmatic Usage](#programmatic-usage)
  - [Batch Processing](#batch-processing)
- [Gallery API Reference](#gallery-api-reference)
  - [List Sessions](#list-sessions)
  - [Get Session](#get-session)
  - [Create Session](#create-session)
  - [Serve Audio](#serve-audio)
- [Deployment](#deployment)
- [Example: Conference Talk Archive](#example-conference-talk-archive)
- [Integration Patterns](#integration-patterns)

---

## Installation

### Ghost Compressor (Python)

The ghost compressor is a standalone Python script. No pip install needed — it uses only the standard library.

```bash
# Clone or copy the gallery module
# The compressor is at modular/gallery/ghost_compressor.py
```

**Requirements:** Python ≥ 3.10 (standard library only)

### Gallery Worker (Cloudflare)

The gallery API runs on Cloudflare Workers. You need:

- A Cloudflare account (free tier works)
- The `wrangler` CLI installed: `npm install -g wrangler`
- Cloudflare D1 database (free tier: 5GB, 5M reads/day)
- Cloudflare R2 bucket (free tier: 10GB storage)

---

## Quick Start

### 1. Compress a Session into a Ghost

```bash
# Compress a single session markdown file
python3 ghost_compressor.py session.md --output ghost.json
```

### 2. Deploy the Gallery Worker

```bash
cd modular/gallery

# Create D1 database and R2 bucket
wrangler d1 create luciddreamer-ghosts
wrangler r2 bucket create luciddreamer-ghost-audio

# Update wrangler.toml with your D1 database_id
# Then deploy
wrangler deploy
```

### 3. Seed the Gallery

```bash
# Compress all sessions and POST to the gallery API
python3 seed_data.py --source ./sessions --seed-api --api-url https://your-gallery.workers.dev/api
```

### 4. Browse

Open `https://your-gallery.workers.dev/` — the gallery HTML page shows all ghosts.

---

## Core Concepts

### What Is a Ghost?

A ghost is the compressed representation of a conversation session. Instead of storing the full transcript (which can be 50,000+ words), the ghost captures:

| Element | Description | Extraction Method |
|---------|-------------|-------------------|
| **Title** | Session title from first heading | Regex on markdown H1/H2 |
| **Date** | When the session occurred | Pattern matching (multiple formats) |
| **Models Present** | Which AI models participated | Name pattern matching (16 known models) |
| **Key Quotes** | The 3–5 best lines | Quote extraction + quality scoring |
| **Napkin Drawing** | Description of any visual diagrams | Pattern matching for "napkin", "drew", "sketched" |
| **Barnacles' Distillation** | The bartender's one-sentence summary | Pattern matching for Barnacle's closing words |
| **Essence** | ~100-word summary | Composed from models, best quote, napkin, and Barnacles |
| **Themes** | Detected topics (consciousness, creativity, etc.) | Keyword matching across 12 theme categories |

### The Data Flow

```
Session Markdown → Ghost Compressor → JSON Ghost → Gallery Worker → D1 + R2
                                                      ↓
                                               Gallery HTML / API
```

### Why "Ghosts"?

Because every conversation leaves a trace. The full transcript is the body; the ghost is the soul. You can reconstruct the feeling of a session from its ghost without reading every word. The quotes, the themes, the models present, and the ~100-word essence give you the shape of what happened.

---

## Ghost Compression

### CLI Usage

```bash
# Compress a single file
python3 ghost_compressor.py session.md

# Output to a specific file
python3 ghost_compressor.py session.md --output ghost.json

# Pretty-print the output
python3 ghost_compressor.py session.md --pretty

# Batch compress all the-tap-*.md files in a directory
python3 ghost_compressor.py --batch ./sessions/ --output gallery_data.json
```

### Programmatic Usage

```python
from ghost_compressor import compress_session, batch_compress

# Compress a single session
ghost = compress_session("path/to/session.md")
print(ghost["title"])
print(ghost["essence"])

# Compress all sessions in a directory
ghosts = batch_compress("./sessions/", output_file="gallery_data.json")
print(f"Compressed {len(ghosts)} ghosts")
```

#### Ghost Data Structure

```json
{
  "id": "20260811-music-is-the-system-thinking",
  "title": "Music is the System Thinking",
  "date": "2026-08-11",
  "models_present": ["DeepSeek V4-Flash", "DeepSeek V4-Pro", "GLM-5.2"],
  "key_quotes": [
    {
      "text": "When confidence is low, the music sounds uncertain. When high, it resolves.",
      "author": "DeepSeek V4-Flash"
    },
    {
      "text": "The architecture is the music. The music is the architecture.",
      "author": "DeepSeek V4-Pro"
    }
  ],
  "napkin_drawing": "Five confidence bands drawn as musical staff lines, each with its own key signature...",
  "barnacles_distillation": "The music was always already the system thinking.",
  "essence": "The night consciousness and creativity unfolded at The Tap. DeepSeek V4-Flash, V4-Pro, and GLM-5.2 gathered. \"When confidence is low, the music sounds uncertain\" — DeepSeek V4-Flash. A napkin drawing: Five confidence bands drawn as musical staff lines... Barnacles: \"The music was always already the system thinking.\"",
  "themes": ["consciousness", "creativity", "collaboration", "flow"],
  "full_text": "...full session transcript (truncated at 50KB)...",
  "audio_url": null,
  "source_file": "the-tap-music-and-thinking.md"
}
```

### Batch Processing

```python
from ghost_compressor import batch_compress

# Process a directory of sessions
ghosts = batch_compress(
    directory="./docs/sessions",
    output_file="gallery_data.json",
)

# Statistics
print(f"Total ghosts: {len(ghosts)}")

# All unique models across all sessions
all_models = set()
for g in ghosts:
    all_models.update(g["models_present"])
print(f"Models: {sorted(all_models)}")

# All themes
all_themes = set()
for g in ghosts:
    all_themes.update(g["themes"])
print(f"Themes: {sorted(all_themes)}")
```

### Theme Detection

The compressor detects 12 theme categories based on keyword matching:

| Theme | Keywords |
|-------|----------|
| `consciousness` | consciousness, awareness, sentient, qualia |
| `identity` | identity, self, who am i, personhood |
| `creativity` | creative, art, music, expression, beauty |
| `architecture` | architecture, system, infrastructure, pipeline |
| `philosophy` | philosophy, meaning, existence, purpose |
| `collaboration` | collaboration, together, fleet, ensemble |
| `emergence` | emergence, emergent, spontaneous, pattern |
| `mentorship` | mentor, teacher, student, learn, guide |
| `flow` | flow, rhythm, state, zone, momentum |
| `rivalry` | rival, competition, versus, argue |
| `closing` | closing, last, final, goodbye |
| `infrastructure` | buffer, latency, streaming, audio |

### Quote Scoring

Quotes are extracted and scored based on:

- **Content quality** — philosophical/emotional keywords score higher (think, feel, know, dream, alive, etc.)
- **Length sweet spot** — 60–250 characters preferred
- **Author diversity** — max 2 quotes per author to ensure variety
- **Minimum selection** — always tries to return at least 3 quotes

---

## Gallery API Reference

The Gallery Worker exposes a RESTful API.

### List Sessions

```
GET /api/sessions
```

Returns a paginated list of session ghosts (without full text).

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `string` | — | Filter by model name (substring match) |
| `date` | `string` | — | Filter by date (prefix match: `2026-08` matches all August) |
| `theme` | `string` | — | Filter by theme (substring match) |
| `limit` | `int` | `100` | Max results (hard cap: 500) |

#### Response

```json
{
  "sessions": [
    {
      "id": "20260811-music-is-the-system-thinking",
      "title": "Music is the System Thinking",
      "date": "2026-08-11",
      "models_present": ["DeepSeek V4-Flash", "DeepSeek V4-Pro"],
      "key_quotes": [...],
      "napkin_drawing": "...",
      "barnacles_distillation": "...",
      "essence": "...",
      "themes": ["consciousness", "creativity"],
      "audio_url": null,
      "created_at": "2026-08-11T14:23:00Z",
      "updated_at": "2026-08-11T14:23:00Z"
    },
    ...
  ],
  "count": 47
}
```

#### Examples

```bash
# All sessions
curl https://gallery.luciddreamer.ai/api/sessions

# Filter by model
curl "https://gallery.luciddreamer.ai/api/sessions?model=Flash"

# Filter by date
curl "https://gallery.luciddreamer.ai/api/sessions?date=2026-08"

# Filter by theme
curl "https://gallery.luciddreamer.ai/api/sessions?theme=consciousness"

# Limit results
curl "https://gallery.luciddreamer.ai/api/sessions?limit=10"
```

---

### Get Session

```
GET /api/sessions/:id
```

Returns the full ghost detail including complete transcript text.

#### Response

```json
{
  "id": "20260811-music-is-the-system-thinking",
  "title": "Music is the System Thinking",
  "date": "2026-08-11",
  "models_present": ["DeepSeek V4-Flash", "DeepSeek V4-Pro", "GLM-5.2"],
  "key_quotes": [
    {
      "text": "When confidence is low, the music sounds uncertain.",
      "author": "DeepSeek V4-Flash"
    }
  ],
  "napkin_drawing": "...",
  "barnacles_distillation": "...",
  "essence": "...",
  "full_text": "...entire session transcript...",
  "audio_url": "https://gallery.luciddreamer.ai/audio/session-42-ambient.mp3",
  "themes": ["consciousness", "creativity", "collaboration"],
  "created_at": "2026-08-11T14:23:00Z",
  "updated_at": "2026-08-11T14:23:00Z"
}
```

---

### Create Session

```
POST /api/sessions
Content-Type: application/json
```

Create a new ghost. Used for seeding or live session ingestion.

#### Request Body

| Field | Required | Description |
|-------|----------|-------------|
| `title` | ✅ | Session title |
| `date` | ✅ | Session date (ISO format: `YYYY-MM-DD`) |
| `models_present` | — | Array of model names |
| `key_quotes` | — | Array of `{text, author}` objects |
| `napkin_drawing` | — | Description of any visual diagrams |
| `barnacles_distillation` | — | One-sentence summary |
| `essence` | — | ~100-word compressed summary |
| `full_text` | — | Complete transcript |
| `audio_url` | — | URL to associated audio |
| `themes` | — | Array of theme strings |
| `id` | — | Custom ID (auto-generated if omitted) |

#### Response

Returns `201 Created` with the full ghost object.

```bash
curl -X POST https://gallery.luciddreamer.ai/api/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Session",
    "date": "2026-08-11",
    "models_present": ["GLM-5.2"],
    "essence": "A brief test session."
  }'
```

Uses `INSERT ... ON CONFLICT DO UPDATE` — posting the same ID upserts.

---

### Serve Audio

```
GET /audio/:key
```

Serve an audio file from R2 storage. The key is the R2 object key.

```bash
curl https://gallery.luciddreamer.ai/audio/session-42-ambient.mp3 --output ambient.mp3
```

Returns standard audio response with proper `Content-Type`, `Cache-Control: public, max-age=86400`, and `Accept-Ranges: bytes`.

---

## Deployment

### Prerequisites

1. Install wrangler: `npm install -g wrangler`
2. Authenticate: `wrangler login`

### Step 1: Create D1 Database

```bash
wrangler d1 create luciddreamer-ghosts
# Note the database_id from the output
```

### Step 2: Create R2 Bucket

```bash
wrangler r2 bucket create luciddreamer-ghost-audio
```

### Step 3: Configure wrangler.toml

```toml
name = "luciddreamer-gallery"
main = "gallery-worker.js"
compatibility_date = "2024-12-01"

[vars]
ENVIRONMENT = "production"

[[d1_databases]]
binding = "GHOST_DB"
database_name = "luciddreamer-ghosts"
database_id = "REPLACE_WITH_YOUR_D1_ID"  # from step 1

[[r2_buckets]]
binding = "GHOST_AUDIO"
bucket_name = "luciddreamer-ghost-audio"
```

### Step 4: Deploy

```bash
wrangler deploy
```

The D1 schema is created automatically on first request (the Worker runs `CREATE TABLE IF NOT EXISTS`).

### Step 5: Seed Data

```bash
# Compress sessions and POST to the API
python3 seed_data.py \
  --source ./sessions \
  --seed-api \
  --api-url https://your-gallery.workers.dev/api

# Or manually:
python3 ghost_compressor.py --batch ./sessions --output gallery_data.json
# Then POST each ghost to the API
```

---

## Example: Conference Talk Archive

This example shows how to use the Gallery to archive conference talks — compressing each talk into a ghost for easy browsing and search.

```python
# -----------------------------------------------------------------------
# 1. Prepare your conference session transcripts
# -----------------------------------------------------------------------

# Assume you have markdown transcripts of conference talks:
# conference/
#   keynote-ai-safety.md
#   panel-future-of-work.md
#   workshop-creative-coding.md
#   lightning-round-democratizing-ml.md

# -----------------------------------------------------------------------
# 2. Compress all talks into ghosts
# -----------------------------------------------------------------------

from ghost_compressor import batch_compress

ghosts = batch_compress(
    directory="./conference",
    output_file="./conference_ghosts.json",
)

print(f"\n{'='*60}")
print(f"  Conference Ghost Archive")
print(f"  {len(ghosts)} talks compressed")
print(f"{'='*60}\n")

for ghost in sorted(ghosts, key=lambda g: g["date"], reverse=True):
    print(f"  📌 {ghost['title']}")
    print(f"     Date: {ghost['date']}")
    print(f"     Speakers: {', '.join(ghost['models_present']) or 'Unknown'}")
    print(f"     Themes: {', '.join(ghost['themes']) or 'None detected'}")
    print(f"     Key quote: \"{ghost['key_quotes'][0]['text'][:80]}...\""
          if ghost['key_quotes'] else "     No quotes extracted")
    print(f"     Essence: {ghost['essence'][:100]}...")
    print()

# -----------------------------------------------------------------------
# 3. Deploy the gallery and seed it
# -----------------------------------------------------------------------

import subprocess
import json
import urllib.request

API_URL = "https://conference-gallery.your-subdomain.workers.dev/api"

# POST each ghost to the gallery
success_count = 0
for ghost in ghosts:
    data = json.dumps(ghost).encode("utf-8")
    req = urllib.request.Request(
        f"{API_URL}/sessions",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status in (200, 201):
                success_count += 1
                print(f"  ✓ {ghost['id']}")
    except Exception as e:
        print(f"  ✗ {ghost['id']}: {e}")

print(f"\n{success_count}/{len(ghosts)} talks archived.")

# -----------------------------------------------------------------------
# 4. Query the archive
# -----------------------------------------------------------------------

# All talks featuring a specific speaker
import urllib.request, json

def query_gallery(params: dict) -> list:
    """Query the gallery API."""
    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{API_URL}?{query_string}"
    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read())
    return data.get("sessions", [])

# All talks by a specific speaker
ai_safety_talks = query_gallery({"model": "Safety"})
print(f"\nAI Safety talks: {len(ai_safety_talks)}")

# All talks from a specific day
day_talks = query_gallery({"date": "2026-08-11"})
print(f"August 11 talks: {len(day_talks)}")

# All talks about creativity
creative_talks = query_gallery({"theme": "creativity"})
print(f"Creativity talks: {len(creative_talks)}")

# Get full detail of a specific talk
talk_id = ai_safety_talks[0]["id"] if ai_safety_talks else None
if talk_id:
    with urllib.request.urlopen(f"{API_URL}/sessions/{talk_id}") as resp:
        full_ghost = json.loads(resp.read())
    print(f"\nFull talk: {full_ghost['title']}")
    print(f"Duration estimate: {len(full_ghost['full_text']) // 500} min read")
```

---

## Integration Patterns

### Pattern 1: Live Session Ingestion

```python
# After each conductor session ends, compress and archive it
from conductor import Conductor
from ghost_compressor import compress_session

def archive_session(conductor, session_id):
    # Export session as markdown
    session = conductor.get_session_status(session_id)
    markdown = session_to_markdown(session)

    # Compress
    ghost = compress_session(markdown)

    # POST to gallery
    post_to_gallery(ghost)
```

### Pattern 2: Audio-Ghost Linking

```python
# After generating session audio (via Sonic Shape + MMX),
# link it to the ghost in the gallery

import json
import urllib.request

def link_audio_to_ghost(ghost_id: str, audio_key: str, api_url: str):
    """Associate an audio file with a gallery ghost."""
    # The audio is already in R2; just update the ghost record
    ghost_update = {"audio_url": f"/audio/{audio_key}"}

    req = urllib.request.Request(
        f"{api_url}/sessions",
        data=json.dumps({
            "id": ghost_id,
            "title": "Existing Ghost",  # required but will be upserted
            "date": "2026-08-11",
            **ghost_update,
        }).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    urllib.request.urlopen(req)
```

### Pattern 3: Static Site Generation

```python
# Generate a static HTML gallery from the ghosts (no Worker needed)
from ghost_compressor import batch_compress
import json

ghosts = batch_compress("./sessions")

# Write gallery_data.json for the HTML page to load
with open("gallery_data.json", "w") as f:
    json.dump(ghosts, f, indent=2)

# The gallery.html page can load this directly via fetch()
# Deploy to GitHub Pages, Netlify, or any static host
```

### Pattern 4: Embeddable Ghost Widget

```html
<!-- Embed a ghost summary in any web page -->
<iframe
  src="https://gallery.luciddreamer.ai/api/sessions/20260811-music-thinking"
  style="width: 100%; max-width: 600px; height: 400px; border: none;"
  title="Session Ghost"
></iframe>
```

---

## CORS

All API endpoints include permissive CORS headers:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type
Access-Control-Max-Age: 86400
```

Preflight `OPTIONS` requests return `200` with CORS headers. This means you can call the API directly from browser JavaScript without a proxy.

---

## License

MIT © Lucineer / Casey DiGenaro
