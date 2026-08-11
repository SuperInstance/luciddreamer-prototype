# LucidDreamer.AI — Modular Manifest

> Generated 2026-08-11. The monolith has been decomposed into 9 independent repos.

## Repositories

### Python Modules (PyPI-publishable)

| # | Repo | URL | Description |
|---|------|-----|-------------|
| 1 | **si-conductor** | https://github.com/SuperInstance/si-conductor | Agent routing layer for multi-agent systems |
| 2 | **si-streamer** | https://github.com/SuperInstance/si-streamer | Audio streaming muxer with scheduling and crossfades |
| 3 | **si-knowledge-graph** | https://github.com/SuperInstance/si-knowledge-graph | Recursive vectorized idea graph for institutional knowledge |
| 4 | **si-sonic-shape** | https://github.com/SuperInstance/si-sonic-shape | Confidence-to-music mapping engine |

### JavaScript Modules (npm-publishable)

| # | Repo | URL | Description |
|---|------|-----|-------------|
| 5 | **si-player** | https://github.com/SuperInstance/si-player | Embeddable streaming audio player widget |
| 6 | **si-terminal** | https://github.com/SuperInstance/si-terminal | Browser-based MUD terminal with character creation |

### Cloudflare Workers

| # | Repo | URL | Description |
|---|------|-----|-------------|
| 7 | **si-ghost-ledger** | https://github.com/SuperInstance/si-ghost-ledger | Public session gallery and artifact compression |
| 8 | **si-feedback** | https://github.com/SuperInstance/si-feedback | Feedback processing and recommendation engine |

### Meta-Package

| # | Repo | URL | Description |
|---|------|-----|-------------|
| 9 | **luciddreamer** | https://github.com/SuperInstance/luciddreamer | Meta-package: auto-assembling modular AI broadcasting platform |

## Module → Source Mapping

| Modular Dir | GitHub Repo | Type |
|-------------|-------------|------|
| `modular/conductor/` | `si-conductor` | Python |
| `modular/streamer/` | `si-streamer` | Python |
| `modular/knowledge-base/` | `si-knowledge-graph` | Python |
| `modular/sonic-shape/` | `si-sonic-shape` | Python |
| `modular/gallery/` | `si-ghost-ledger` | Cloudflare Worker |
| `modular/player/` | `si-player` | JavaScript |
| `modular/terminal/` | `si-terminal` | JavaScript |
| `modular/feedback/` | `si-feedback` | Cloudflare Worker |
| `modular/luciddreamer/` | `luciddreamer` | Python (meta) |

## Architecture

All modules are independently usable with no hard cross-dependencies. The meta-package (`luciddreamer`) imports all Python modules and wires them together.

```
                    ┌──────────────┐
                    │  luciddreamer │ (meta)
                    └──────┬───────┘
           ┌──────┬────────┼────────┬──────┐
           │      │        │        │      │
     ┌─────▼──┐┌──▼───┐┌───▼──┐┌────▼───┐  │
     │conduc- ││strea-││know- ││sonic   │  │
     │tor     ││mer   ││ledge ││shape   │  │
     └────────┘└──────┘└──────┘└────────┘  │
                                         │
          Web components (independent) ───┘
     ┌─────────┐┌────────┐┌───────┐┌──────────┐
     │ player  ││terminal││ghost  ││ feedback │
     │         ││        ││ledger ││          │
     └─────────┘└────────┘└───────┘└──────────┘
```

## License

All modules: **Apache-2.0**

## Assembly

These repos were assembled from the `luciddreamer-prototype` monolith using `modular/assembly.sh`. Each repo includes:
- Apache-2.0 LICENSE
- CI workflow (`.github/workflows/test.yml`)
- Proper `.gitignore` for the language
- `README.md`, `setup.py`/`package.json`, source files, and tests
