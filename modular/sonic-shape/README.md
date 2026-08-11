# @superinstance/sonic-shape

**Confidence-to-music engine. Music IS the system thinking.**

Maps agent confidence levels and emotional states to concrete musical parameters. Generates MMX commands for audio synthesis. Each model gets a distinct musical voice.

> When confidence is low, the music sounds uncertain. When confidence enters the creative band, the music explores. When confidence is high, the music resolves.

## Install

```bash
pip install superinstance-sonic-shape
```

## Quick Start

### Map confidence to music

```python
from sonic_shape import confidence_to_music, get_band

# What does 0.45 confidence sound like?
params = confidence_to_music(0.45)
print(params.key)              # "Bb" (creative band)
print(params.tempo_bpm)        # 75-90 (jazz territory)
print(params.primary_instrument)  # "saxophone"
print(params.mood_words)       # ["jazz", "blue notes", "exploratory", ...]
print(params.to_mmx_prompt())  # full MiniMax generation prompt
```

### Transform a session into a musical score

```python
from sonic_shape import session_to_score

session_data = {
    "messages": [
        {"model": "flash", "content": "I'm searching for the pattern...", "confidence": 0.25},
        {"model": "flash", "content": "Oh, I see it now!", "confidence": 0.65},
        {"model": "pro", "content": "The architecture is clear.", "confidence": 0.92},
    ]
}

score = session_to_score(session_data, session_id="session-42")
print(score.summary())
# Movement 1: [UNCERTAIN] Into the Mist (50 BPM, D minor) — Flash
# Movement 2: [CREATIVE] Kind of Blue (75 BPM, Bb blues) — Flash
# Movement 3: [CONFIDENT] Arrival (120 BPM, D major) — Pro

# Export as playlist of MMX commands
playlist = score.to_playlist()
```

### Live generation

```python
import asyncio
from sonic_shape import LiveGenerator

async def main():
    gen = LiveGenerator()
    await gen.start()

    # Feed confidence readings → generates music
    gen.feed_confidence(0.15, model_name="flash")  # uncertain → blue notes
    gen.feed_confidence(0.50, model_name="flash")  # creative → jazz
    gen.feed_confidence(0.95, model_name="pro")    # confident → fanfare

    print(gen.queue_status())
    await gen.stop()

asyncio.run(main())
```

## Confidence Bands

| Band | Range | Sound | Key Instruments |
|------|-------|-------|-----------------|
| UNCERTAIN | 0.0–0.30 | Minor key, 50–60 BPM, unresolved, sparse | Trombone, cello, ambient drone |
| TRANSITIONAL | 0.30–0.40 | Suspended, shimmering, between states | Piano, ambient pad, bell |
| CREATIVE | 0.40–0.60 | Blue notes, 65–90 BPM, jazz, exploratory | Saxophone, Rhodes, brushed drums |
| TRANSITIONAL | 0.60–0.70 | Suspended, shimmering | Piano, strings, bell |
| EMERGING | 0.70–0.85 | Major key, 90–120 BPM, resolving | Piano, trumpet, strings |
| CONFIDENT | 0.86–1.0 | Bright major, 120–160 BPM, celebratory | Trumpet, full orchestra, timpani |

## Voice Profiles

Each model gets a sonic identity:

| Model | Voice | Character |
|-------|-------|-----------|
| Flash | Alto saxophone | Bright, fast, syncopated, jazz fusion |
| Pro | Cello | Deep baritone, structured, authoritative |
| Hermes | Fender Rhodes + strings | Warm, flowing, multi-layered, lydian |
| Wesley | Music box + bell | Simple, pure, childlike wonder, pentatonic |

## Dependencies

**Required:** None (pure Python)

**Optional:**
- `mmx` CLI — for actual audio generation via MiniMax
- `websockets` — for WebSocket-based live session monitoring
- `aiohttp` — for HTTP polling session monitoring
- `superinstance/conductor` — for direct conductor confidence integration

## License

MIT
