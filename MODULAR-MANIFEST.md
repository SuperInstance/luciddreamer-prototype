# LucidDreamer.AI — Modular Manifest

> All repos for the modular LucidDreamer.AI ecosystem. Each module works independently. Together they create the full product.

## Repositories

### Python Packages (PyPI)

| Repo | Module | Description |
|------|--------|-------------|
| [SuperInstance/si-conductor](https://github.com/SuperInstance/si-conductor) | Conductor | Agent routing layer for multi-agent systems |
| [SuperInstance/si-streamer](https://github.com/SuperInstance/si-streamer) | Streamer | Audio streaming muxer with scheduling and crossfades |
| [SuperInstance/si-knowledge-base](https://github.com/SuperInstance/si-knowledge-base) | Knowledge Base | A recursive idea graph that grows smarter as you feed it |
| [SuperInstance/si-knowledge-graph](https://github.com/SuperInstance/si-knowledge-graph) | Knowledge Graph | Recursive vectorized idea graph for institutional knowledge |
| [SuperInstance/si-sonic-shape](https://github.com/SuperInstance/si-sonic-shape) | Sonic Shape | Confidence-to-music mapping engine |
| [SuperInstance/si-ghost-ledger](https://github.com/SuperInstance/si-ghost-ledger) | Ghost Ledger | Session compression into public artifacts |

### JavaScript Packages (npm)

| Repo | Module | Description |
|------|--------|-------------|
| [SuperInstance/si-player](https://github.com/SuperInstance/si-player) | Player | Embeddable streaming audio player widget |
| [SuperInstance/si-terminal](https://github.com/SuperInstance/si-terminal) | Terminal | Browser-based MUD terminal with character creation |

### Cloudflare Workers

| Repo | Module | Description |
|------|--------|-------------|
| [SuperInstance/si-feedback](https://github.com/SuperInstance/si-feedback) | Feedback | Feedback processing and recommendation engine |

### Meta-Package

| Repo | Module | Description |
|------|--------|-------------|
| [SuperInstance/luciddreamer](https://github.com/SuperInstance/luciddreamer) | LucidDreamer | Meta-package: auto-assembling modular AI broadcasting platform |

### Prototype

| Repo | Description |
|------|-------------|
| [SuperInstance/luciddreamer-prototype](https://github.com/SuperInstance/luciddreamer-prototype) | Original prototype and research repo |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     LUCIDDREAMER.AI                              │
│                                                                  │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐     │
│  │ Conductor│   │  Sonic   │   │Knowledge │   │ Streamer │     │
│  │          │──▶│  Shape   │   │  Base    │   │          │     │
│  └────┬─────┘   └──────────┘   └──────────┘   └────┬─────┘     │
│       │                                           │            │
│       │         ┌─────────────────┐               │            │
│       └────────▶│  GLUE LAYER    │◀──────────────┘            │
│                 │ (luciddreamer)  │                            │
│                 └────────┬────────┘                            │
│                          │                                     │
│         ┌────────────────┼────────────────┐                    │
│         │                │                │                    │
│  ┌──────▼─────┐  ┌──────▼──────┐  ┌──────▼──────┐             │
│  │  Terminal  │  │   Player    │  │   Gallery   │             │
│  └────────────┘  └──────┬──────┘  └─────────────┘             │
│                         │                                       │
│                  ┌──────▼──────┐                                │
│                  │  Feedback   │                                │
│                  └─────────────┘                                │
└─────────────────────────────────────────────────────────────────┘
```

## Install

### Individual modules

```bash
# Python
pip install superinstance-conductor superinstance-streamer superinstance-knowledge-base superinstance-sonic-shape

# npm
npm install @superinstance/player @superinstance/terminal
```

### Full system

```bash
pip install superinstance-luciddreamer
```

## Module Count

- **6** Python packages
- **2** JavaScript packages
- **1** Cloudflare Worker
- **1** Meta-package (glue layer)
- **= 10** total repositories
