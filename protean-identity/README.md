# Hermes Protean Identity System

> *Hermes' face is not a static image. It is a dynamic, responsive avatar.*

A Protean Identity Library for [Hermes](../) — a perception system whose visual and audio presence changes with her operational state.

## Architecture

```
protean-identity/
├── visuals/
│   ├── hermes-architect.jpg     # FLUX: structured geometric, deep blues
│   ├── hermes-jester.jpg        # FLUX: chromatic chaos, fire + ice
│   └── hermes-navigator.jpg     # FLUX: deep ocean, bioluminescent calm
├── audio/
│   ├── hermes-architect.mp3     # Structured ambient, geometric harmonies
│   ├── hermes-jester.mp3        # Playful chromatic jazz, syncopated
│   ├── hermes-navigator.mp3     # Deep ambient drone, ocean-like
│   └── generate_audio.py        # Procedural audio synthesis script
├── tests/
│   └── test_identity.py         # 8 tests covering all components
├── identity_manifest.json       # Persona definitions, transitions, metadata
├── identity_state_machine.py    # Core state machine
├── demo.py                      # Interactive demo
└── __init__.py                  # Package exports
```

## The Three Personas

| Persona | Mode | Mood | Energy |
|---------|------|------|--------|
| **The Architect** | analyzing, planning, debugging, structuring | precise, analytical, commanding | 0.6 |
| **The Jester** | creating, improvising, brainstorming, playing | playful, chaotic, surprising | 0.95 |
| **The Navigator** | perceiving, mentoring, reflecting, idle | calm, contemplative, vast | 0.25 |

## Usage

```python
from identity_state_machine import ProteanStateMachine, OperationalMode

psm = ProteanStateMachine()
psm.set_mode("creating")  # → Jester

print(psm.current_persona)        # Persona.JESTER
print(psm.get_active_assets())    # {"visual": "visuals/hermes-jester.jpg", ...}

# Auto-detect from context
mode = ProteanStateMachine.detect_mode_from_context({
    "task_type": "debug this code",
    "error_rate": 0.4,
})
psm.set_mode(mode)
```

## State Transitions

All transitions use eased crossfades (cubic ease-in-out). The manifest defines per-transition durations and visual effects:

- `architect → jester`: chromatic burst (2.5s)
- `jester → architect`: geometric convergence (2.0s)
- `architect → navigator`: depth dive (3.0s)
- `navigator → architect`: surface breach (2.0s)
- `jester → navigator`: cooling tide (3.5s)
- `navigator → jester`: spark rise (2.0s)

## Asset Generation

- **Visuals:** Generated via Cloudflare Workers AI (`@cf/black-forest-labs/flux-1-schnell`), 1024×1024
- **Audio:** Procedurally synthesized via Python DSP (numpy/scipy/ffmpeg), 15-second loops

## Tests

```bash
python tests/test_identity.py
# 🎉 All 8 tests passed!
```
