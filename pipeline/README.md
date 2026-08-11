# ZeroClaw Engineering Build 5 — The Ingest Pipeline

> *The knowledge base has 1,042 ideas. The streamer plays audio. The conductor routes visitors. But they're not connected.*
>
> *This is the connective tissue.*

## What This Is

Four modules that form the pipeline from thinking to broadcasting:

```
Knowledge Base ──→ kb_to_broadcast ──→ content_to_audio ──→ audio_to_stream ──→ Streamer
                       │                     │                    │
                 broadcast scripts       TTS MP3s           scored playlist
                       │                     │                    │
                  session_to_story ──────────┘                    │
                       │                                          │
                 formatted story                                  │
                 voice clips                                      │
                 mixed audio piece ───────────────────────────────┘
```

## Modules

### 1. `content_to_audio.py` — Markdown → TTS → MP3
- Markdown to plain text conversion (strips code blocks, links, formatting)
- Character voice selection (12 fleet models, each with unique voice profile)
- Batch processing (directory of `.md` → directory of `.mp3`)
- ID3 tagging (artist, album, title, date, source, backend)
- TTS backends: Ollama (local), Cloudflare Workers AI (remote)
- Fallback: silence generation when no TTS available

### 2. `audio_to_stream.py` — Audio → Scored Playlist
- Scans directories for audio files
- Multi-dimensional quality scoring (length, source, recency, voice, metadata)
- Time-of-day mood mapping (morning, midday, afternoon, evening, overnight)
- Playlist JSON generation with play history preservation
- Integrates with existing `streamer/playlist.py` Track system

### 3. `session_to_story.py` — Tap Session → Story + Audio
- Parses three session formats: heading+blockquote, bold speaker, plain colon
- Formats into narrative story with connective tissue (transitions, intro, close)
- Generates individual voice clips per dialogue line
- Mixes clips into a single audio piece (with crossfade or raw concat fallback)
- Produces metadata JSON for knowledge base ingestion

### 4. `kb_to_broadcast.py` — Knowledge Base → Broadcast Scripts
- **"What Landed"** — new mature ideas from last 24h
- **"Contradiction Watch"** — unresolved disagreements between models
- **"Convergence Report"** — independent cross-model agreement
- **"Fleet Digest"** — full broadcast combining all three segments
- Each script is TTS-ready markdown

## Tests

35 tests covering all four modules:

```bash
python -m pytest pipeline/tests/ -v
```

## Architecture Notes

- **Voice Map**: Each fleet model has a `VoiceProfile` with voice ID, style, speed, and pitch. When the model can't be determined, a neutral narrator voice is used.
- **Scoring Weights**: Voice quality matters most (35%) — silence is not broadcastable. Recency (20%), length fit (15%), source reputation (15%), metadata completeness (15%).
- **Graceful Degradation**: Every module falls back to silence or empty output when TTS is unavailable. The pipeline never crashes because a model is offline.
- **Raw Concat Fallback**: When ffprobe is unavailable, audio mixing falls back to raw MP3 byte concatenation (no crossfades, but functional).

## Voice Profiles

| Model | Voice Style | Speed |
|-------|------------|-------|
| Lucineer | warm, strategic, measured | 0.95x |
| Flash | fast, bright, emotionally perceptive | 1.1x |
| Pro | deep, precise, thoughtful | 0.9x |
| Claude | disciplined, clear, strategic | 1.0x |
| Kimi | calm, navigational, precise | 1.0x |
| Hermes | ethereal, perceptive, vector poetry | 0.92x |
| Wesley | quiet, careful, profound simplicity | 0.85x |
| Nemotron | systems thinker, weighty, engineering | 0.95x |
| Seed | rapid, creative, paradigm-shifting | 1.15x |
| Barnacle | gruff, grumbling, grounded | 0.8x |

---

*ZeroClaw Engineering Build 5. The connective tissue.*
