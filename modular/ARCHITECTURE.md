# LucidDreamer.AI — Modular Architecture

> Generated 2026-08-11. Breaking the monolith into independently usable packages.

## Design Principles

1. **Each module works alone** — no hard cross-dependencies. Pull just the conductor, or just the streamer.
2. **The meta-package auto-assembles** — `pip install superinstance-luciddreamer` gets you everything, wired together.
3. **Web components deploy independently** — Cloudflare Workers and static sites, not pip packages.
4. **Clear boundaries** — each module has a single responsibility, a public API, and explicit optional integrations.

## Module Map

```
┌─────────────────────────────────────────────────────────────────┐
│                     LUCIDDREAMER.AI                              │
│                                                                  │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐     │
│  │ Conductor│   │  Sonic   │   │ Knowledge│   │ Streamer │     │
│  │          │   │  Shape   │   │  Base    │   │          │     │
│  │ Routes   │──▶│ Music    │   │ Ideas    │   │ Audio    │     │
│  │ Agents   │   │ from    │   │ Graph    │   │ HLS      │     │
│  │          │   │ signals  │   │          │   │ Stream   │     │
│  └────┬─────┘   └──────────┘   └──────────┘   └────┬─────┘     │
│       │                                           │            │
│       │         ┌─────────────────┐               │            │
│       └────────▶│  GLUE LAYER    │◀──────────────┘            │
│                 │ (meta-package)  │                            │
│                 └────────┬────────┘                            │
│                          │                                     │
│         ┌────────────────┼────────────────┐                    │
│         │                │                │                    │
│  ┌──────▼─────┐  ┌──────▼──────┐  ┌──────▼──────┐             │
│  │  Terminal  │  │   Player    │  │   Gallery   │             │
│  │  (web)     │  │   (web)     │  │   (Worker)  │             │
│  │ Character  │  │ HLS audio   │  │ Session     │             │
│  │ Creation   │  │ Visualizer  │  │ Ghosts      │             │
│  │ + MUD      │  │ Feedback    │  │             │             │
│  └────────────┘  └──────┬──────┘  └─────────────┘             │
│                         │                                       │
│                  ┌──────▼──────┐                                │
│                  │  Feedback   │                                │
│                  │  (Worker)   │                                │
│                  │ Now-Playing │                                │
│                  │ + Feedback  │                                │
│                  └─────────────┘                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Module Details

### Python Packages (PyPI)

#### 1. `superinstance-conductor`
- **Source:** `conductor/`
- **Does:** Agent routing, intent analysis, engagement tracking, escalation
- **Hard deps:** None (pure Python)
- **Optional deps:** `pyyaml` (config files)
- **Install:** `pip install superinstance-conductor`

#### 2. `superinstance-streamer`
- **Source:** `streamer/`
- **Does:** Playlist management, scheduling, crossfading, HLS segmentation, streaming HTTP server
- **Hard deps:** `pydub`, `ffmpeg` (system)
- **Optional deps:** `pyyaml` (config files)
- **Install:** `pip install superinstance-streamer`

#### 3. `superinstance-knowledge-base`
- **Source:** `knowledge-base/`
- **Does:** Recursive idea graph, contradiction detection, convergence clustering, lineage tracking, D1+Vectorize export
- **Hard deps:** None (pure Python)
- **Optional deps:** `ollama` (embeddings), `wrangler` (Cloudflare deploy)
- **Install:** `pip install superinstance-knowledge-base`

#### 4. `superinstance-sonic-shape`
- **Source:** `sonic-shape/`
- **Does:** Confidence-to-music mapping, session-to-score transformation, live music generation
- **Hard deps:** None (pure Python)
- **Optional deps:** `mmx` CLI (audio generation), `websockets` (live monitoring), `aiohttp` (polling)
- **Install:** `pip install superinstance-sonic-shape`

#### 9. `superinstance-luciddreamer` (Glue Layer)
- **Source:** `luciddreamer/`
- **Does:** Imports all Python modules, wires them together, provides unified API
- **Hard deps:** All four Python packages above
- **Install:** `pip install superinstance-luciddreamer`

### JavaScript Packages (npm)

#### 6. `@superinstance/player`
- **Source:** `player/`
- **Does:** HLS audio player with visualizer, now-playing polling, feedback submission
- **Hard deps:** `hls.js` (loaded from CDN)
- **Install:** `npm install @superinstance/player`

#### 7. `@superinstance/terminal`
- **Source:** `terminal/`
- **Does:** Character sheet builder, crab-trap prompt generation, xterm.js MUD terminal
- **Hard deps:** `xterm.js` (loaded from CDN)
- **Install:** `npm install @superinstance/terminal`

### Cloudflare Workers

#### 5. Gallery
- **Source:** `gallery/`
- **Does:** Session ghost gallery API, ghost compression, D1 storage, R2 audio
- **Deploy:** `wrangler deploy` (in `gallery/`)
- **Requires:** Cloudflare D1 + R2

#### 8. Feedback
- **Source:** `feedback/`
- **Does:** Listener feedback collection (KV), now-playing metadata API (KV)
- **Deploy:** `wrangler deploy` (in `feedback/`)
- **Requires:** Cloudflare KV

## Dependency Graph

```
                    ┌──────────────┐
                    │  luciddreamer │ (meta)
                    └──────┬───────┘
           ┌──────┬────────┼────────┬──────┐
           │      │        │        │      │
     ┌─────▼──┐┌──▼──┐┌───▼──┐┌────▼───┐  │
     │conductor││stream││  kb  ││sonic  │  │
     │         │er    ││      ││shape  │  │
     └─────────┘└─────┘└──────┘└────────┘  │
                                         │
          Web components (independent) ───┘
     ┌─────────┐┌────────┐┌───────┐┌──────────┐
     │ player  ││terminal││gallery││ feedback │
     └─────────┘└────────┘└───────┘└──────────┘
```

**No Python module requires another Python module.** Each is fully standalone. The glue layer imports them all and connects them, but you can use any combination.

## Integration Points

| From | To | Signal |
|------|----|--------|
| Conductor | Sonic Shape | Confidence level → music parameters |
| Conductor | Knowledge Base | Session messages → idea extraction |
| Sonic Shape | Streamer | MMX commands → audio files → playlist |
| Streamer | Player | HLS stream → web playback |
| Player | Feedback | Feedback submission → KV storage |
| Gallery | (any) | Session compression → ghost display |
| Terminal | Conductor | Character sheet → visitor session |

## File Structure

```
modular/
├── conductor/
│   ├── README.md
│   ├── setup.py
│   ├── __init__.py         (public API)
│   └── src/conductor/      (source from prototype)
├── streamer/
│   ├── README.md
│   ├── setup.py
│   ├── __init__.py
│   ├── config.yaml
│   └── src/                (playlist, scheduler, muxer, stream_server)
├── knowledge-base/
│   ├── README.md
│   ├── setup.py
│   ├── __init__.py
│   └── src/                (idea_schema, knowledge_graph, vector_integration, ...)
├── sonic-shape/
│   ├── README.md
│   ├── setup.py
│   ├── __init__.py
│   └── src/                (harmonic_dictionary, voice_profiles, session_to_music, live_generator)
├── gallery/
│   ├── README.md
│   ├── wrangler.toml
│   ├── gallery-worker.js
│   ├── gallery.html
│   ├── ghost_compressor.py
│   └── seed_data.py
├── player/
│   ├── README.md
│   ├── package.json
│   ├── index.html
│   ├── app.js
│   └── style.css
├── terminal/
│   ├── README.md
│   ├── package.json
│   ├── index.html
│   ├── app.js
│   ├── style.css
│   ├── character-schema.json
│   └── prompt-templates/
├── feedback/
│   ├── README.md
│   ├── package.json
│   ├── feedback-worker.js
│   ├── now-playing-worker.js
│   ├── wrangler-feedback.toml
│   └── wrangler-now-playing.toml
├── luciddreamer/
│   ├── README.md
│   ├── setup.py
│   └── src/luciddreamer/
│       ├── __init__.py     (assembly layer)
│       └── cli.py
├── assembly.sh             (creates separate repos + CI)
└── ARCHITECTURE.md         (this file)
```
