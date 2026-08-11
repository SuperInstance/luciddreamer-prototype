# Modular Package Manifest

> All 9 independent repos under the [SuperInstance](https://github.com/SuperInstance) org.
> Created: 2026-08-11

## Repositories

| # | Module | Repo | Description | Source Dir |
|---|--------|------|-------------|------------|
| 1 | **Conductor** | [SuperInstance/conductor](https://github.com/SuperInstance/conductor) | Agent routing layer for multi-agent systems | `modular/conductor/` |
| 2 | **Streamer** | [SuperInstance/streamer](https://github.com/SuperInstance/streamer) | Audio streaming muxer with scheduling and crossfades | `modular/streamer/` |
| 3 | **Knowledge Graph** | [SuperInstance/knowledge-graph](https://github.com/SuperInstance/knowledge-graph) | Recursive vectorized idea graph for institutional knowledge | `modular/knowledge-base/` |
| 4 | **Sonic Shape** | [SuperInstance/sonic-shape](https://github.com/SuperInstance/sonic-shape) | Confidence-to-music mapping engine | `modular/sonic-shape/` |
| 5 | **Ghost Ledger** | [SuperInstance/ghost-ledger](https://github.com/SuperInstance/ghost-ledger) | Public session gallery and artifact compression | `modular/gallery/` |
| 6 | **Player Widget** | [SuperInstance/player-widget](https://github.com/SuperInstance/player-widget) | Embeddable streaming audio player widget | `modular/player/` |
| 7 | **MUD Terminal** | [SuperInstance/mud-terminal](https://github.com/SuperInstance/mud-terminal) | Browser-based MUD terminal with character creation | `modular/terminal/` |
| 8 | **Feedback Engine** | [SuperInstance/feedback-engine](https://github.com/SuperInstance/feedback-engine) | Feedback processing and recommendation engine | `modular/feedback/` |
| 9 | **LucidDreamer** | [SuperInstance/luciddreamer](https://github.com/SuperInstance/luciddreamer) | Meta-package: auto-assembling modular AI broadcasting platform | `modular/luciddreamer/` |

## Module Details

### 1. Conductor
- **Purpose:** Routes tasks across multiple AI agents, manages agent pools, session state, and configuration.
- **Language:** Python (with YAML config)
- **Key files:** `src/conductor.py`, `src/agent_pool.py`, `src/session.py`, `src/config.yaml`, `src/tests/test_conductor.py`

### 2. Streamer
- **Purpose:** Multiplexes audio streams with scheduling support and crossfade transitions.
- **Language:** Python (with YAML config)
- **Key files:** `__init__.py`, `config.yaml`, `setup.py`

### 3. Knowledge Graph
- **Purpose:** Stores and retrieves ideas as a recursive vectorized graph — institutional memory that grows smarter over time.
- **Language:** Python
- **Key files:** `__init__.py`, `setup.py`

### 4. Sonic Shape
- **Purpose:** Maps AI confidence scores to musical parameters, turning model uncertainty into expressive musical output.
- **Language:** Python
- **Key files:** `__init__.py`, `setup.py`

### 5. Ghost Ledger
- **Purpose:** Public-facing session gallery with artifact compression. Sessions are "ghosted" (compressed) for long-term storage and display.
- **Language:** JavaScript (Cloudflare Workers), Python (compression/seed), HTML
- **Key files:** `gallery-worker.js`, `gallery.html`, `ghost_compressor.py`, `gallery_data.json`, `wrangler.toml`

### 6. Player Widget
- **Purpose:** Embeddable streaming audio player with feedback collection and now-playing tracking.
- **Language:** JavaScript (Cloudflare Workers), HTML, CSS
- **Key files:** `app.js`, `index.html`, `style.css`, `feedback-worker.js`, `now-playing-worker.js`, `package.json`

### 7. MUD Terminal
- **Purpose:** Browser-based MUD (Multi-User Domain) terminal with character creation and schema validation.
- **Language:** JavaScript, HTML, CSS, JSON Schema
- **Key files:** `app.js`, `index.html`, `style.css`, `character-schema.json`

### 8. Feedback Engine
- **Purpose:** Processes user feedback (reactions, ratings) and generates recommendations via Cloudflare Workers.
- **Language:** JavaScript (Cloudflare Workers)
- **Key files:** `feedback-worker.js`, `now-playing-worker.js`

### 9. LucidDreamer (Meta-Package)
- **Purpose:** The umbrella project. Auto-assembles all modules into a complete AI broadcasting platform. Currently a meta-package with documentation; will grow orchestration tooling.
- **Language:** Multi
- **Key files:** `README.md`

## Architecture

```
LucidDreamer (meta)
├── Conductor ─────── routes tasks to agents
├── Streamer ──────── muxes audio + crossfades
├── Knowledge Graph── vectorized idea memory
├── Sonic Shape ───── confidence → music mapping
├── Ghost Ledger ──── session gallery + compression
├── Player Widget ─── embeddable audio player
├── MUD Terminal ──── browser MUD interface
└── Feedback Engine── reactions + recommendations
```

Each module is independently deployable. The Conductor wires them together.

## License

Private — SuperInstance org. All rights reserved.
