# @superinstance/luciddreamer

**The meta-package. One install for the full LucidDreamer.AI experience.**

LucidDreamer.AI is a modular system. Each module works independently, but together they create the full product: a multi-agent dream radio station where AI characters hold conversations, the conversations become music, the music becomes a 24/7 stream, and every session leaves a ghost in the gallery.

This package wires all modules together with sensible defaults. Override any module to customize.

## Install

```bash
pip install superinstance-luciddreamer
```

## What Gets Installed

| Module | pip Package | Role |
|--------|------------|------|
| Conductor | `superinstance-conductor` | Routes visitors to the right agents |
| Streamer | `superinstance-streamer` | Muxes audio into a 24/7 HLS stream |
| Knowledge Base | `superinstance-knowledge-base` | Recursive idea graph |
| Sonic Shape | `superinstance-sonic-shape` | Confidence-to-music engine |

The web components (Gallery, Player, Terminal, Feedback) are deployed separately as Cloudflare Workers / static sites:

| Module | npm/Deploy | Role |
|--------|-----------|------|
| Gallery | `wrangler deploy` | Session ghost gallery |
| Player | Static host | Embeddable web player |
| Terminal | Static host | MUD terminal widget |
| Feedback | `wrangler deploy` | Feedback + now-playing workers |

## Quick Start

```python
from luciddreamer import LucidDreamer

# One-line startup
ld = LucidDreamer(
    audio_dir="/path/to/audio",
    port=8420,
    enable_streamer=True,
    enable_conductor=True,
    enable_knowledge_base=True,
    enable_sonic_shape=True,
)

# Access individual modules
conductor = ld.conductor
streamer = ld.streamer
kb = ld.knowledge_base
sonic = ld.sonic_shape

# Receive a visitor
session = conductor.receive_visitor(visitor)

# Route a message — the conductor decides who responds
decision = conductor.route_visitor_message(session.session_id, "Tell me a story")

# The confidence from that decision drives the music
score = sonic.session_to_score(session_data, session_id=session.session_id)

# When the session ends, ingest it into the knowledge base
kb.ingest_session(session)
```

## Configuration

```python
from luciddreamer import LucidDreamer

ld = LucidDreamer(
    audio_dir="/path/to/audio",
    port=8420,

    # Conductor config
    conductor_config={
        "session": {"max_active_agents": 4},
        "escalation": {"confidence_threshold": 0.4},
    },

    # Streamer config
    streamer_config={
        "crossfade": {"duration_seconds": 3.0},
        "normalization": {"target_lufs": -23.0},
        "hls": {"segment_duration_seconds": 10},
    },

    # Knowledge base config
    kb_config={
        "local_path": "knowledge_base.pkl",
    },

    # Sonic shape config
    sonic_config={
        "auto_generate": True,
    },

    # Enable/disable modules
    enable_streamer=True,
    enable_conductor=True,
    enable_knowledge_base=True,
    enable_sonic_shape=True,
)
```

## Architecture

```
                    ┌──────────────┐
                    │   Terminal   │ ← Character creation
                    │   (web)      │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Conductor   │ ← Routes visitors to agents
                    │  (Python)    │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
       ┌──────▼─────┐ ┌───▼────┐ ┌────▼─────┐
       │  Sonic     │ │  KB    │ │ Streamer │
       │  Shape     │ │       │ │          │
       │ (music)    │ │(ideas)│ │ (audio)  │
       └────────────┘ └───────┘ └────┬─────┘
                                      │
                               ┌──────▼──────┐
                               │   Player    │ ← Web playback
                               │   (web)     │
                               └─────────────┘
```

## Module Independence

Use any module alone:

```bash
# Just the conductor
pip install superinstance-conductor

# Just the streamer
pip install superinstance-streamer

# Just the knowledge base
pip install superinstance-knowledge-base

# Just the sonic shape engine
pip install superinstance-sonic-shape
```

## License

MIT
