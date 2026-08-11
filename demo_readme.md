# LucidDreamer.AI — End-to-End Pipeline Demo

## What This Proves

`demo.py` demonstrates the **full LucidDreamer pipeline** working end-to-end:

```
Tap Session → Knowledge Base → Ghost → TTS → Playlist → Streamer → Player → Gallery
```

Each module calls the next. Even when real APIs aren't available (Ollama not running, no DeepSeek key), the **structure is correct** — the demo mocks the external calls but exercises every internal module boundary.

## Quick Start

```bash
cd /home/eileen/projects/luciddreamer-prototype
python3 demo.py
```

That's it. The demo creates a temp directory, runs all 8 steps, and opens browser pages for the player and gallery.

### With a custom workdir:

```bash
python3 demo.py --workdir ./demo-output
```

### With a custom port:

```bash
python3 demo.py --port 9000
```

## What Each Step Does

### Step 1: Create a Tap Session
- Writes a markdown Tap session where Flash and Wesley meet for the first time
- Uses Conductor's `SessionStore`, `VisitorProfile`, and `SessionState` to create a real session
- Output: `the-tap-demo-night.md`

### Step 2: Ingest into Knowledge Base
- Uses `knowledge-base/ingest_session.py` to extract `IdeaNode`s from the markdown
- Auto-detects idea types (insight, creative, question, blind spot, pattern)
- Builds a `KnowledgeGraph` with auto-detected relationships
- Output: structured ideas + session node

### Step 3: Compress into a Ghost
- Uses `gallery/ghost_compressor.py` to compress the session
- Extracts: title, date, models present, key quotes, napkin drawing, themes
- Generates a ~100-word essence (the ghost)
- Output: `demo_ghost.json`

### Step 4: Generate TTS
- Uses `pipeline/content_to_audio.py` to generate speech for the key quote
- Selects voice profile based on the quote's author (Flash's voice)
- Tries Ollama → Cloudflare Workers AI → mock fallback
- Output: `audio/demo_quote.mp3`

### Step 5: Add to Streamer Playlist
- Uses `streamer/playlist.py` to create a `Playlist` and add the audio track
- Sets quality score, mood tags, show name
- Tests track selection (weighted random sampling)
- Output: configured Playlist object

### Step 6: Start the Streamer
- Uses `streamer/stream_server.py` to configure the HLS streaming server
- Creates `StreamState`, writes a minimal `.m3u8` playlist
- Prints player/stream/status URLs
- Does NOT actually start the HTTP server (demo mode)
- Output: HLS segment directory + stream URLs

### Step 7: Open the Player
- Writes a standalone HTML player page (dawn-themed, Channel 42 aesthetic)
- Opens it in the default browser
- Shows what the production player would look like
- Output: `demo_player.html` opened in browser

### Step 8: Show Ghost in Gallery
- Creates a Ghost Ledger gallery page for the demo ghost
- Displays title, date, models, essence, key quotes, themes
- Styled to match the production Ghost Ledger
- Checks if the ghost exists in `gallery/gallery_data.json`
- Output: `demo_gallery.html` opened in browser

## Modules Exercised

| Module | File | What's Used |
|--------|------|-------------|
| Conductor | `conductor/session.py` | `SessionStore`, `VisitorProfile`, `SessionState`, `MessageRecord` |
| Conductor | `conductor/agent_pool.py` | `AgentProfile`, `AGENT_POOL` (imported by session) |
| Knowledge Base | `knowledge-base/ingest_session.py` | `extract_ideas_from_markdown`, `auto_detect_relationships` |
| Knowledge Base | `knowledge-base/idea_schema.py` | `IdeaNode`, `SessionNode`, `IdeaType`, `IdeaStatus` |
| Knowledge Base | `knowledge-base/knowledge_graph.py` | `KnowledgeGraph` |
| Ghost Ledger | `gallery/ghost_compressor.py` | `compress_session` |
| Pipeline | `pipeline/content_to_audio.py` | `get_voice_for_alias`, `generate_tts`, `tag_mp3` |
| Streamer | `streamer/playlist.py` | `Playlist`, `Track` |
| Streamer | `streamer/scheduler.py` | `Scheduler` (imported by stream_server) |
| Streamer | `streamer/stream_server.py` | `StreamState`, `StreamHandler` |

## Output Files

After running, the workdir contains:

```
luciddreamer_demo_XXXX/
├── the-tap-demo-night.md      # Session markdown
├── demo_ghost.json            # Compressed ghost
├── audio/
│   └── demo_quote.mp3         # TTS audio (or stub)
├── hls_segments/
│   └── stream.m3u8            # HLS playlist
├── demo_player.html           # Player page
└── demo_gallery.html          # Gallery page
```

## When Real APIs Are Available

The demo gracefully upgrades when services are running:

- **Ollama running** (`localhost:11434`): Real TTS via `orpheus-tts` or similar model
- **Cloudflare credentials set** (`CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`): TTS via Workers AI
- **mutagen installed** (`pip install mutagen`): Proper ID3 tags on MP3 files
- **pydub installed** (`pip install pydub`): Audio conversion and silence generation

When none of these are available, the demo falls back to mocks that still exercise the module boundaries — proving the pipeline structure is sound.

## What the Demo Proves

1. **Session creation works** — Conductor data structures accept and track agent sessions
2. **Knowledge extraction works** — Markdown is parsed into structured IdeaNodes with typed relationships
3. **Ghost compression works** — Sessions are compressed into queryable artifacts with quotes, themes, and essence
4. **TTS pipeline works** — Voice profiles map to models, audio generation has a clear backend chain
5. **Playlist management works** — Tracks are added, scored, and selected with weighted sampling
6. **Streamer configuration works** — StreamState, HLS output paths, and server URLs are correctly wired
7. **Player output works** — A styled HTML player page is generated
8. **Gallery display works** — Ghosts render in a styled Ghost Ledger page

The demo is the proof that the pipeline — from session to broadcast to archive — holds together as a system.
