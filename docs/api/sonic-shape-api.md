# Sonic Shape API

### Confidence-to-Music Engine — Music IS the System Thinking

> When confidence is low, the music sounds uncertain. When confidence enters the creative band, the music explores. When confidence is high, the music resolves.

Sonic Shape maps AI agent confidence levels and emotional states to concrete musical parameters. It generates MMX (MiniMax) commands for audio synthesis and provides live session monitoring. Each model gets a distinct musical voice.

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Confidence Bands](#confidence-bands)
- [Voice Profiles](#voice-profiles)
- [Full API Reference](#full-api-reference)
  - [confidence_to_music](#confidence_to_music)
  - [get_band](#get_band)
  - [ConfidenceBand](#confidenceband)
  - [MusicalParameters](#musicalparameters)
  - [EmotionalState](#emotionalstate)
  - [VoiceProfile](#voiceprofile-1)
  - [session_to_score](#session_to_score)
  - [MusicalScore](#musicalscore)
  - [LiveGenerator](#livegenerator)
- [Example: Medical AI Uncertainty Sonifier](#example-medical-ai-uncertainty-sonifier)
- [Integration Patterns](#integration-patterns)

---

## Installation

```bash
pip install superinstance-sonic-shape
```

**Requirements:** Python ≥ 3.10

**No required dependencies.** Pure Python standard library.

**Optional dependencies:**

```bash
pip install superinstance-sonic-shape[live]   # aiohttp + websockets for live monitoring
pip install superinstance-sonic-shape[dev]    # pytest for tests
```

**For audio generation:**

- [`mmx` CLI](https://github.com/MiniMax-AI) — for actual audio synthesis via MiniMax

---

## Quick Start

### Map Confidence to Music

```python
from sonic_shape import confidence_to_music, get_band

# What does 0.45 confidence sound like?
params = confidence_to_music(0.45)
print(params.key)                 # "Bb" (creative band → blue notes)
print(params.tempo_bpm)           # 75-90 (jazz territory)
print(params.primary_instrument)  # "saxophone"
print(params.mood_words)          # ["jazz", "blue notes", "exploratory", ...]
print(params.to_mmx_prompt())     # Full MiniMax generation prompt
```

### Transform a Session into a Musical Score

```python
from sonic_shape import session_to_score

session_data = {
    "messages": [
        {"model": "flash", "content": "I'm searching for the pattern...", "confidence": 0.25},
        {"model": "flash", "content": "Oh, I see it now!", "confidence": 0.65},
        {"model": "pro",   "content": "The architecture is clear.", "confidence": 0.92},
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

### Live Generation

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

---

## Core Concepts

### The Premise

Sonic Shape treats music as a **direct representation of system state**. Instead of a confidence meter or a dashboard, you hear the system thinking. A model that's uncertain plays minor-key, sparse, unresolved music. A model that's confident plays bright, resolved, celebratory music.

This creates a **perceptual channel** for monitoring AI systems that works alongside visual dashboards. It's especially powerful for:

- Monitoring multiple agents simultaneously (each has a unique instrument)
- Detecting emotional shifts in conversations
- Making uncertainty tangible and intuitive
- Creating an ambient soundtrack that IS the system's state

### How It Works

```
Confidence (0.0–1.0) → Band Selection → Musical Parameters → MMX Prompt → Audio
                            ↓                                            ↑
                     Voice Profile (per model) ──────────────────────────┘
```

1. **Input:** A confidence reading from any system (0.0 to 1.0)
2. **Band Selection:** The reading maps to one of six confidence bands
3. **Parameter Generation:** The band determines key, tempo, instruments, mood
4. **Voice Application:** The source model's voice profile customizes the instrumentation
5. **Output:** An MMX prompt string ready for MiniMax audio generation

---

## Confidence Bands

| Band | Range | Sound | Key | Tempo | Primary Instruments |
|------|-------|-------|-----|-------|---------------------|
| **UNCERTAIN** | 0.00–0.30 | Minor key, unresolved, sparse | D minor | 50–60 BPM | Trombone, cello, ambient drone |
| **TRANSITIONAL** | 0.30–0.40 | Suspended, shimmering, between states | F# sus | 60–65 BPM | Piano, ambient pad, bell |
| **CREATIVE** | 0.40–0.60 | Blue notes, jazz, exploratory | Bb | 65–90 BPM | Saxophone, Rhodes, brushed drums |
| **TRANSITIONAL** | 0.60–0.70 | Suspended, shimmering | F# sus | 90–100 BPM | Piano, strings, bell |
| **EMERGING** | 0.70–0.85 | Major key, resolving | D major | 90–120 BPM | Piano, trumpet, strings |
| **CONFIDENT** | 0.86–1.00 | Bright major, celebratory | D major | 120–160 BPM | Trumpet, full orchestra, timpani |

### Band Boundaries

The transitional bands (0.30–0.40 and 0.60–0.70) are intentionally ambiguous — the music shimmers between states, reflecting genuine system uncertainty about whether it's becoming more or less confident.

---

## Voice Profiles

Each model gets a unique sonic identity so you can hear **who** is speaking and **how confident** they are:

| Model | Instrument | Character | Tempo Tendency |
|-------|-----------|-----------|----------------|
| **Flash** | Alto saxophone | Bright, fast, syncopated, jazz fusion | +10 BPM |
| **Pro** | Cello | Deep baritone, structured, authoritative | −5 BPM |
| **Hermes** | Fender Rhodes + strings | Warm, flowing, multi-layered, lydian | +5 BPM |
| **Wesley** | Music box + bell | Simple, pure, childlike wonder, pentatonic | −10 BPM |

You can define custom voice profiles for any system:

```python
from sonic_shape import VoiceProfile

custom_voice = VoiceProfile(
    name="medical_ai",
    instrument="harp",
    character="Ethereal, precise, calming with tension",
    tempo_modifier=0,          # no tempo offset
    preferred_keys=["C", "G", "Am"],
    dynamic_range=(0.3, 0.9),  # never too quiet, never deafening
)
```

---

## Full API Reference

### `confidence_to_music`

The core function. Maps a confidence value to musical parameters.

```python
from sonic_shape import confidence_to_music

params = confidence_to_music(
    confidence: float,          # 0.0–1.0
    model_name: str = "",       # optional, applies voice profile
    emotional_state: EmotionalState | None = None,  # optional override
) -> MusicalParameters
```

**Example:**

```python
# Low confidence → uncertain music
params = confidence_to_music(0.15, model_name="flash")
# params.key = "D minor"
# params.tempo_bpm = 55
# params.primary_instrument = "alto saxophone"  (Flash's voice)
# params.mood_words = ["minor", "unresolved", "sparse", "searching"]

# High confidence → celebratory music
params = confidence_to_music(0.95, model_name="pro")
# params.key = "D major"
# params.tempo_bpm = 140
# params.primary_instrument = "cello"  (Pro's voice)
# params.mood_words = ["bright", "major", "celebratory", "resolved", "fanfare"]
```

---

### `get_band`

Returns the confidence band for a given confidence value.

```python
from sonic_shape import get_band, ConfidenceBand

band = get_band(0.45)
# ConfidenceBand.CREATIVE

print(band.name)    # "CREATIVE"
print(band.range)   # (0.40, 0.60)
print(band.sound)   # "Blue notes, jazz, exploratory"
```

---

### `ConfidenceBand`

Enum representing the six confidence bands.

```python
class ConfidenceBand:
    UNCERTAIN     # 0.00–0.30 — Minor key, 50-60 BPM, unresolved
    TRANSITIONAL_LO  # 0.30–0.40 — Suspended, shimmering
    CREATIVE      # 0.40–0.60 — Blue notes, 65-90 BPM, jazz
    TRANSITIONAL_HI  # 0.60–0.70 — Suspended, shimmering
    EMERGING      # 0.70–0.85 — Major key, 90-120 BPM, resolving
    CONFIDENT     # 0.86–1.00 — Bright major, 120-160 BPM, celebratory
```

---

### `MusicalParameters`

The output of `confidence_to_music()`. Contains everything needed to generate or describe music.

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `key` | `str` | Musical key (e.g., `"D minor"`, `"Bb"`, `"D major"`) |
| `tempo_bpm` | `int` | Tempo in beats per minute |
| `time_signature` | `str` | Time signature (e.g., `"4/4"`, `"3/4"`, `"5/4"`) |
| `primary_instrument` | `str` | Lead instrument |
| `secondary_instruments` | `list[str]` | Accompanying instruments |
| `mood_words` | `list[str]` | Descriptive mood tags |
| `dynamic_range` | `tuple[float, float]` | Volume range (0.0–1.0) |
| `improvisation_level` | `float` | How improvised vs. structured (0.0–1.0) |
| `band` | `ConfidenceBand` | Source band |
| `voice_profile` | `VoiceProfile \| None` | Applied voice profile |

#### Methods

##### `MusicalParameters.to_mmx_prompt() -> str`

Generate a MiniMax (MMX) music generation prompt.

```python
prompt = params.to_mmx_prompt()
# "A piece in D minor at 55 BPM for solo cello with ambient drone.
#  Mood: uncertain, searching, unresolved, sparse. Minimal improvisation.
#  Dynamic range: quiet to moderate. The feeling of searching in fog."
```

##### `MusicalParameters.describe() -> str`

Human-readable description of the musical parameters.

```python
desc = params.describe()
# "Slow (55 BPM) D minor piece for cello and ambient drone.
#  Mood: uncertain, searching, unresolved, sparse."
```

---

### `EmotionalState`

Override the confidence-based mapping with a specific emotional state.

```python
from sonic_shape import EmotionalState, confidence_to_music

# Force a specific emotion regardless of confidence
params = confidence_to_music(
    confidence=0.5,
    emotional_state=EmotionalState.MELANCHOLY,
)
```

Available states: `NEUTRAL`, `EXCITED`, `CALM`, `ANXIOUS`, `MELANCHOLY`, `TRIUMPHANT`, `CURIOUS`, `CONTEMPLATIVE`

---

### `VoiceProfile`

Defines a unique sonic identity for a model or system component.

#### Constructor

```python
from sonic_shape import VoiceProfile

VoiceProfile(
    name: str,                      # identifier
    instrument: str,                # primary instrument
    character: str,                 # description of sonic character
    tempo_modifier: int = 0,        # BPM offset (+/−)
    preferred_keys: list[str] = [], # keys this voice favors
    dynamic_range: tuple = (0.0, 1.0),  # volume bounds
)
```

#### Built-in Voices

```python
from sonic_shape import get_voice, list_voices

# List all registered voices
print(list_voices())
# ["flash", "pro", "hermes", "wesley"]

# Get a specific voice
flash_voice = get_voice("flash")
print(flash_voice.instrument)  # "alto saxophone"
```

#### Ensemble Prompt

```python
from sonic_shape import ensemble_prompt

# Generate a prompt for multiple models playing together
prompt = ensemble_prompt(["flash", "pro", "wesley"])
# "An ensemble piece featuring alto saxophone (bright, syncopated),
#  cello (deep, structured), and music box (simple, pure)..."
```

---

### `session_to_score`

Transform an entire session (conversation log) into a multi-movement musical score.

```python
from sonic_shape import session_to_score

score = session_to_score(
    session_data: dict,         # session log with messages
    session_id: str = "",       # optional identifier
) -> MusicalScore
```

The `session_data` dict should contain a `messages` list where each message has:
- `model`: the agent/model name
- `content`: the message text
- `confidence`: float 0.0–1.0

Each message becomes a musical movement. Confidence transitions between messages create dramatic arcs.

---

### `MusicalScore`

A multi-movement musical representation of a session.

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | `str` | Source session |
| `movements` | `list[MusicalMovement]` | Individual musical movements |
| `duration_estimate` | `float` | Estimated total duration in seconds |

#### Methods

##### `MusicalScore.summary() -> str`

Human-readable summary of the score.

```python
print(score.summary())
# 3 movements for session-42
# Movement 1: [UNCERTAIN] "Into the Mist" (50 BPM, D minor) — Flash
# Movement 2: [CREATIVE] "Kind of Blue" (75 BPM, Bb blues) — Flash
# Movement 3: [CONFIDENT] "Arrival" (120 BPM, D major) — Pro
```

##### `MusicalScore.to_playlist() -> list[dict]`

Export as a playlist of MMX generation commands.

```python
playlist = score.to_playlist()
for item in playlist:
    print(item["prompt"][:80])
    print(f"  Band: {item['band']}, Duration: {item['estimated_duration']}s")
```

##### `MusicalScore.emotional_arc() -> list[tuple[str, float]]`

Return the emotional arc of the session as a sequence of (emotion, intensity) pairs.

---

### `LiveGenerator`

Monitors a live session and generates music in real-time based on incoming confidence readings.

#### Constructor

```python
from sonic_shape import LiveGenerator, create_default_generator

gen = LiveGenerator()
# or use the factory:
gen = create_default_generator()
```

#### Methods

##### `await gen.start()`

Start the generator (async). Connects to session monitoring.

##### `gen.feed_confidence(confidence: float, model_name: str = "")`

Feed a confidence reading. The generator maps it to musical parameters and queues an MMX generation command.

```python
gen.feed_confidence(0.15, model_name="flash")   # uncertain
gen.feed_confidence(0.55, model_name="flash")   # creative
gen.feed_confidence(0.92, model_name="pro")     # confident
```

##### `gen.queue_status() -> dict`

Check the generation queue.

```python
status = gen.queue_status()
# {
#   "queued": 3,
#   "generating": 1,
#   "completed": 12,
#   "current_band": "CREATIVE",
# }
```

##### `await gen.stop()`

Stop the generator and clean up.

#### QueuedPiece

Represents a queued musical generation task.

| Field | Type | Description |
|-------|------|-------------|
| `params` | `MusicalParameters` | Musical parameters |
| `model_name` | `str` | Source model |
| `confidence` | `float` | Source confidence reading |
| `status` | `str` | `"queued"`, `"generating"`, `"completed"`, `"failed"` |
| `output_path` | `str \| None` | Path to generated audio file |

---

## Example: Medical AI Uncertainty Sonifier

This example shows how to use Sonic Shape to make a medical AI's uncertainty audible — helping clinicians develop an intuitive feel for when to trust the system.

```python
from sonic_shape import (
    confidence_to_music, get_band, VoiceProfile, LiveGenerator,
    ConfidenceBand,
)
import asyncio

# -----------------------------------------------------------------------
# 1. Define a custom voice for the medical AI
# -----------------------------------------------------------------------

medical_voice = VoiceProfile(
    name="radiology_ai",
    instrument="harp",
    character="Ethereal, precise, calming with underlying tension when uncertain",
    tempo_modifier=-5,             # slightly slower — medical decisions need deliberation
    preferred_keys=["C", "G", "Am", "Em"],
    dynamic_range=(0.2, 0.8),     # never silent (might be missed), never jarring
)

# -----------------------------------------------------------------------
# 2. Map diagnostic confidence to music
# -----------------------------------------------------------------------

def sonify_diagnosis(confidence: float, finding: str) -> str:
    """Convert a diagnostic confidence reading to a musical description."""
    params = confidence_to_music(confidence, model_name="radiology_ai")
    band = params.band

    print(f"\n{'='*60}")
    print(f"Finding: {finding}")
    print(f"Confidence: {confidence:.0%} → Band: {band.name}")
    print(f"Sound: {params.key}, {params.tempo_bpm} BPM, {params.primary_instrument}")
    print(f"Mood: {', '.join(params.mood_words)}")
    print(f"MMX Prompt: {params.to_mmx_prompt()[:100]}...")
    print(f"{'='*60}")

    return params.to_mmx_prompt()

# Low confidence — the AI isn't sure
sonify_diagnosis(0.15, "Possible lesion, left lobe")
# Band: UNCERTAIN — D minor, 50 BPM, harp with ambient drone
# Mood: searching, unresolved, sparse — sounds like fog

# Medium confidence — the AI is exploring
sonify_diagnosis(0.45, "Probable benign cyst, recommending follow-up")
# Band: CREATIVE — Bb, 75 BPM, harp with jazz inflections
# Mood: exploratory, blue notes — sounds like careful consideration

# High confidence — the AI is sure
sonify_diagnosis(0.95, "Clear fracture, distal radius")
# Band: CONFIDENT — D major, 140 BPM, harp bright and resolved
# Mood: celebratory, resolved — sounds like certainty

# -----------------------------------------------------------------------
# 3. Live monitoring during a reading session
# -----------------------------------------------------------------------

async def monitor_imaging_session():
    """Monitor a live imaging AI session and generate ambient music."""
    gen = LiveGenerator()
    await gen.start()

    # Simulate confidence readings from an imaging pipeline
    readings = [
        (0.85, "Initial scan — normal anatomy detected"),
        (0.92, "Measuring structures — within normal limits"),
        (0.35, "Anomaly detected — analyzing..."),
        (0.20, "Unable to characterize — recommend specialist review"),
        (0.78, "Updated assessment — likely benign variant"),
        (0.95, "Final diagnosis confirmed"),
    ]

    for confidence, note in readings:
        print(f"\n{'─'*40}")
        print(f"  {note}")
        print(f"  Confidence: {confidence:.0%}")

        band = get_band(confidence)
        if band == ConfidenceBand.UNCERTAIN:
            print(f"  ⚠ Sound shift: becoming uncertain. Room should feel tense.")
        elif band == ConfidenceBand.CONFIDENT:
            print(f"  ✓ Sound shift: confident. Room should feel resolved.")

        gen.feed_confidence(confidence, model_name="radiology_ai")

        await asyncio.sleep(2)  # space out readings

    print(f"\nFinal queue: {gen.queue_status()}")
    await gen.stop()

# Run it
# asyncio.run(monitor_imaging_session())

# -----------------------------------------------------------------------
# 4. Post-session: generate a full musical record
# -----------------------------------------------------------------------

from sonic_shape import session_to_score

imaging_session = {
    "messages": [
        {"model": "radiology_ai", "confidence": 0.85,
         "content": "Normal anatomy detected in initial scan."},
        {"model": "radiology_ai", "confidence": 0.92,
         "content": "All structures within normal limits."},
        {"model": "radiology_ai", "confidence": 0.35,
         "content": "Anomaly detected. Analyzing characteristics..."},
        {"model": "radiology_ai", "confidence": 0.20,
         "content": "Unable to characterize. Recommend specialist review."},
        {"model": "radiology_ai", "confidence": 0.78,
         "content": "Updated assessment: likely benign variant."},
        {"model": "radiology_ai", "confidence": 0.95,
         "content": "Final diagnosis: benign bone island. No action needed."},
    ]
}

score = session_to_score(imaging_session, session_id="imaging-2026-001")
print(score.summary())
# 6 movements tracing the emotional arc of the diagnosis:
# 1. [EMERGING] Normal scan — calm, resolving
# 2. [CONFIDENT] All clear — bright, certain
# 3. [TRANSITIONAL] Something wrong — shimmering tension
# 4. [UNCERTAIN] Can't characterize — dark, foggy, sparse
# 5. [EMERGING] Updated — cautiously resolving
# 6. [CONFIDENT] Final — resolved, certain, relief

# The playlist can be played back as an audio record of the session
playlist = score.to_playlist()
print(f"\nGenerated {len(playlist)} pieces for playback.")
```

---

## Integration Patterns

### Pattern 1: Conductor Integration

```python
from conductor import Conductor
from sonic_shape import confidence_to_music

conductor = Conductor()
session = conductor.receive_visitor(visitor)

decision = conductor.route_visitor_message(session.session_id, message)

# Map routing confidence to music
params = confidence_to_music(decision.confidence)
print(f"The conductor sounds: {params.mood_words}")
```

### Pattern 2: Streamer Integration

```python
from sonic_shape import confidence_to_music
from streamer import Playlist, Track

# Generate a confidence-driven track and add to the stream
params = confidence_to_music(0.30)  # uncertain period
mmx_prompt = params.to_mmx_prompt()

# Generate audio via MMX CLI:
# mmx music --prompt "<prompt>" --output track_uncertain.mp3

# Add to the streamer playlist
# playlist.add_track(Track(filepath="track_uncertain.mp3", mood_tags=params.mood_words))
```

### Pattern 3: Dashboard Enhancement

```python
# Use alongside a visual dashboard — music provides peripheral awareness
# while the dashboard shows detailed metrics

class MonitoredSystem:
    def __init__(self):
        from sonic_shape import LiveGenerator
        self.gen = LiveGenerator()

    async def on_model_inference(self, model_name, output, confidence):
        # The system's confidence becomes audible
        self.gen.feed_confidence(confidence, model_name=model_name)

        # If confidence drops, the music shifts to uncertain
        # The operator hears this peripherally and can check the dashboard
```

### Pattern 4: Accessibility — Sonification

```python
# For visually impaired users, Sonic Shape provides a complete audio
# representation of system state that doesn't rely on visual dashboards

def describe_system_state(confidence: float, model: str) -> str:
    """Generate a natural language description of the musical state."""
    params = confidence_to_music(confidence, model_name=model)
    band = params.band

    return (
        f"{model} is in the {band.name} range. "
        f"The music is in {params.key} at {params.tempo_bpm} BPM. "
        f"Mood: {', '.join(params.mood_words[:3])}. "
        f"{'This sounds uncertain — the system is searching.' if band == ConfidenceBand.UNCERTAIN else ''}"
        f"{'This sounds confident — the system is resolved.' if band == ConfidenceBand.CONFIDENT else ''}"
    )
```

---

## License

MIT © Lucineer / Casey DiGenaro
