# LucidDreamer.AI — Streaming Audio Muxer

**Built by ZeroClaw. First build. The transmitter.**

*"A 24/7 stream is a days-long Markov chain in latent space.
 Temporal coherence drift is the systemic risk." — Nemotron*

## What This Is

The streaming audio muxer is the radio station's transmitter. It takes
audio files from local disk (or R2 in production) and creates a continuous
stream with crossfades, normalization, and time-aware scheduling.

This is the piece that makes LucidDreamer.AI actually broadcast.

## Components

```
streamer/
├── config.yaml          — station configuration
├── playlist.py          — weighted, schedule-aware playlist engine
├── scheduler.py         — time-of-day content scheduling
├── muxer.py             — audio concat, crossfade, normalization, HLS
├── stream_server.py     — HTTP server serving HLS stream
├── conftest.py          — pytest config
└── tests/
    ├── test_playlist.py — 10 tests (loading, selection, rotation, anchors)
    ├── test_scheduler.py — 7 tests (slots, time-of-day, queue, anchors)
    └── test_muxer.py    — 7 tests (config, duration, audio load, HLS)
```

## Quick Start

```bash
# Run the stream server (uses channel-42-dawn audio by default)
cd streamer
python3 stream_server.py --audio-dir /path/to/audio --port 8420

# Listen in VLC
vlc http://localhost:8420/listen.m3u8

# Open the web player
open http://localhost:8420
```

## Running Tests

```bash
cd streamer
python3 -m pytest tests/ -v
```

## Design Notes

### Coherence Anchors

Nemotron's warning from the Tap session: a 24/7 stream drifts into a
fixed-point attractor — semantically null, locally consistent, globally
meaningless. "A dream that forgot it was dreaming."

Our defense: every N tracks, the scheduler forces a high-quality
"anchor" piece. This resets the stream's trajectory, preventing drift
into context-inappropriate territory. The anchor system is the semantic
checkpoint that keeps the stream coherent over days.

### Schedule

The station follows a day/night rhythm:

| Time         | Show               | Vibe                                    |
|--------------|--------------------|-----------------------------------------|
| 06:00–10:00 | Morning Watch      | Fleet Radio, dawn broadcasts, energizing |
| 10:00–14:00 | Midday Essays      | Long-form, educational, thoughtful       |
| 14:00–18:00 | Afternoon Theater  | Radio drama, creative, experimental      |
| 18:00–22:00 | Evening Tap        | Live-feel, conversational, open mic      |
| 22:00–06:00 | Overnight Dispatch | Ambient, quiet, meditative               |

### Why pydub + ffmpeg?

pydub provides clean Python-level audio manipulation (crossfades,
normalization, silence insertion). ffmpeg handles the heavy lifting
(decoding/encoding any audio format). Together they cover everything
the prototype needs without native dependencies beyond the ffmpeg binary.

### Dependencies

- Python 3.12+
- ffmpeg (static binary works fine)
- pydub (`pip install pydub`)
- PyYAML (`pip install pyyaml`)
- pytest (for tests)

---

*iron sharpens iron*
