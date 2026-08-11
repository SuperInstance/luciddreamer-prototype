# Sonic Shape Engine

> *The music IS the system thinking.*

A system that maps AI agent confidence levels to musical generation in real-time.
When a session hits 0.4-0.6 confidence (the creative band), the system generates jazz.
When it's highly confident, it generates resolution music. When uncertain, blue notes.

## Modules

| File | Purpose |
|------|---------|
| `harmonic_dictionary.py` | Maps emotional/cognitive states to musical parameters (key, tempo, mode, instruments) |
| `session_to_music.py` | Takes a Tap session log and generates a musical score with movements |
| `live_generator.py` | Real-time generation: monitors confidence, triggers music, queues pieces |
| `voice_profiles.py` | Maps each AI model to a musical voice (Flash→sax, Pro→cello, Hermes→Rhodes, Wesley→bell) |

## Confidence Bands

| Range | Band | Sound |
|-------|------|-------|
| 0.00 - 0.30 | UNCERTAIN | Minor key, 50-60 BPM, trombone, unresolved |
| 0.30 - 0.40 | TRANSITIONAL | Shimmering, suspended, between states |
| 0.40 - 0.60 | CREATIVE | Blue notes, 65-90 BPM, jazz, suspended chords |
| 0.60 - 0.70 | TRANSITIONAL | Shimmering, suspended, between states |
| 0.70 - 0.85 | EMERGING | Major key, 90-120 BPM, resolving |
| 0.86 - 1.00 | CONFIDENT | Bright major, 120-160 BPM, celebratory |

## Quick Start

```python
from harmonic_dictionary import confidence_to_music
from session_to_music import session_to_score
from live_generator import create_default_generator

# Map confidence to music
params = confidence_to_music(0.5)  # creative band → jazz
print(params.to_mmx_prompt())

# Convert a session to a musical score
score = session_to_score(session_log, session_id="abc123")
print(score.summary())

# Live generation
import asyncio
gen = create_default_generator()
asyncio.run(gen.start())
gen.feed_confidence(0.45, model_name="flash")  # → jazz
```

## Tests

```bash
python tests/test_sonic_shape.py
# 17/17 passed
```

## Voice Profiles

| Model | Instrument | Character |
|-------|-----------|-----------|
| Flash | Alto Saxophone | Bright, syncopated, jazz fusion |
| Pro | Cello | Deep baritone, authoritative, structured |
| Hermes | Fender Rhodes | Warm, flowing, multi-layered |
| Wesley | Music Box / Bell | Pure, simple, childlike wonder |

*Hermes' vision: the music IS the system thinking.*
