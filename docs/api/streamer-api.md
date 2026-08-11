# Streamer API

### Audio Streaming Muxer with HLS, Crossfades, and Time-of-Day Scheduling

> "A 24/7 stream is a days-long Markov chain in latent space. Temporal coherence drift is the systemic risk." — Nemotron

The Streamer takes a directory of audio files and produces a continuous, professional-grade stream with crossfades, loudness normalization, HLS segmentation, and time-aware programming. It's a complete radio station transmitter in a Python package.

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Full API Reference](#full-api-reference)
  - [Playlist](#playlist)
  - [Scheduler](#scheduler)
  - [Muxer](#muxer)
  - [MuxerConfig](#muxerconfig)
  - [Track](#track)
  - [ScheduleSlot](#scheduleslot)
- [Configuration File](#configuration-file)
- [Example: Music Radio Station](#example-music-radio-station)
- [Integration Patterns](#integration-patterns)

---

## Installation

```bash
pip install superinstance-streamer
```

**Requirements:**

- Python ≥ 3.10
- **`ffmpeg`** must be installed and on your PATH (system requirement)
- `pydub` (installed automatically)

**Optional dependencies:**

```bash
pip install superinstance-streamer[config]   # PyYAML for config files
pip install superinstance-streamer[dev]      # pytest for tests
```

**Install ffmpeg:**

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows (via chocolatey)
choco install ffmpeg
```

---

## Quick Start

### Run a Streaming Server

```bash
python -m streamer.stream_server --audio-dir /path/to/audio --port 8420
```

Open `http://localhost:8420` in your browser. The embedded player starts playing immediately.

### Use Programmatically

```python
from streamer import Playlist, Scheduler, Muxer

# 1. Load tracks from a directory
playlist = Playlist(audio_dir="/path/to/audio")
print(f"Loaded {playlist.size} tracks")

# 2. Schedule based on time of day
scheduler = Scheduler(playlist=playlist)
queue = scheduler.now_playing_queue(size=5)  # next 5 tracks
for track in queue:
    print(f"  {track.title} ({track.duration_seconds}s)")

# 3. Mux into a continuous stream
muxer = Muxer()
output = muxer.concatenate_streaming(queue, "output.mp3")
print(f"Wrote {output}")
```

---

## Core Concepts

### The Pipeline

```
Audio Files → Playlist → Scheduler → Muxer → HLS Stream
                 ↑           ↑          ↑
            Weighting    Time-of-day  Crossfade
            No-repeat    Coherence    Normalize
                         Anchors      Segment
```

### Programming Slots

The Scheduler divides the day into named programming blocks. Each slot defines mood, minimum quality, and duration constraints. This mirrors how real radio stations program their broadcast day.

| Slot | Hours | Mood | Description |
|------|-------|------|-------------|
| Morning Watch | 06:00–10:00 | energizing, dawn, warm | Morning show, dawn broadcasts |
| Midday Essays | 10:00–14:00 | essay, educational, thoughtful | Essays, interviews, long-form |
| Afternoon Theater | 14:00–18:00 | drama, creative, playful | Radio theater, creative pieces |
| Evening Tap | 18:00–22:00 | live, conversational, warm | Live sessions, open mic |
| Overnight Dispatch | 22:00–06:00 | ambient, quiet, meditative | Ambient, music-heavy, quiet |

### Coherence Anchors

A key innovation. Over long streaming periods, playlists drift toward fixed-point attractors — repeating the same narrow set of tracks. Coherence anchors prevent this by forcing a high-quality "anchor" track every N tracks (default: 8), resetting the playlist's trajectory.

### No-Repeat Windows

Tracks are prevented from replaying within a configurable time window (default: 4 hours / 240 minutes). This ensures variety without requiring massive content libraries.

---

## Full API Reference

### `Playlist`

Manages the pool of available audio tracks. Handles loading, weighting, and rotation rules.

#### Constructor

```python
Playlist(
    audio_dir: str,
    no_repeat_window_minutes: int = 240,
    weight_by_quality: bool = True,
    weight_by_recency: bool = True,
    recency_boost_multiplier: float = 1.5,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `audio_dir` | `str` | — | Path to directory of audio files (mp3, wav, m4a, flac) |
| `no_repeat_window_minutes` | `int` | `240` | Minimum time before a track can replay (4 hours) |
| `weight_by_quality` | `bool` | `True` | Higher quality tracks play more often |
| `weight_by_recency` | `bool` | `True` | Newer content gets a play boost |
| `recency_boost_multiplier` | `float` | `1.5` | How much newer tracks are boosted |

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `size` | `int` | Number of loaded tracks |
| `tracks` | `list[Track]` | All loaded track objects |

#### Methods

##### `Playlist.select(mood: list[str] | None = None, min_quality: float = 0.0, max_duration: int | None = None, exclude: set[str] | None = None) -> Track | None`

Select the next track to play based on filters and weighting. Returns `None` if no track matches.

```python
track = playlist.select(
    mood=["energizing", "dawn"],
    min_quality=0.3,
    max_duration=600,
)
```

##### `Playlist.mark_played(track_id: str) -> None`

Record that a track was played (updates play count and last-played timestamp for no-repeat tracking).

##### `Playlist.reset_play_history() -> None`

Clear all play history. Allows everything to be selected again.

---

### `Scheduler`

Time-of-day aware track selector. Knows what programming slot is active and selects tracks accordingly.

#### Constructor

```python
Scheduler(
    playlist: Playlist,
    slots: list[ScheduleSlot] | None = None,
    coherence_anchor_interval: int = 8,
    coherence_anchor_min_quality: float = 0.8,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `playlist` | `Playlist` | — | The track pool |
| `slots` | `list[ScheduleSlot] \| None` | `None` | Custom schedule slots (defaults to built-in 5-slot programming) |
| `coherence_anchor_interval` | `int` | `8` | Insert an anchor track every N tracks |
| `coherence_anchor_min_quality` | `float` | `0.8` | Minimum quality for anchor tracks |

#### Methods

##### `Scheduler.current_slot() -> ScheduleSlot`

Return the programming slot active right now based on the current hour.

```python
slot = scheduler.current_slot()
print(f"Now playing: {slot.name}")  # "Midday Essays"
print(f"Mood: {slot.mood}")         # ["essay", "educational", "thoughtful"]
```

##### `Scheduler.now_playing_queue(size: int = 5) -> list[Track]`

Build the next N-track queue. Applies scheduling rules, coherence anchoring, and no-repeat windows.

```python
queue = scheduler.now_playing_queue(size=10)
for i, track in enumerate(queue):
    print(f"{i+1}. {track.title} [{track.duration_seconds}s]")
```

##### `Scheduler.next_track() -> Track | None`

Select just the next single track. Applies coherence anchor logic (every Nth track is forced to be a high-quality anchor).

---

### `Muxer`

Audio processing: crossfades, normalization, HLS segmentation.

#### Constructor

```python
Muxer(config: MuxerConfig | None = None)
```

#### Methods

##### `Muxer.concatenate_streaming(tracks: list[Track], output_path: str) -> str`

Concatenate a list of tracks into a single continuous audio file with crossfades applied between each track. Returns the output file path.

```python
output = muxer.concatenate_streaming(queue, "stream_output.mp3")
```

##### `Muxer.crossfade(track_a_path: str, track_b_path: str, duration_seconds: float = 3.0) -> str`

Crossfade two audio files. Returns the path to the resulting file.

##### `Muxer.normalize(input_path: str, target_lufs: float = -23.0) -> str`

Apply loudness normalization to hit a target LUFS (Loudness Units Full Scale). Broadcast standard is −23 LUFS.

```python
normalized = muxer.normalize("raw_track.mp3", target_lufs=-23.0)
```

##### `Muxer.segment_hls(input_path: str, output_dir: str, segment_duration: int = 10, playlist_entries: int = 15) -> str`

Segment an audio file into HLS format (.m3u8 playlist + .ts segments).

```python
muxer.segment_hls(
    "stream_output.mp3",
    output_dir="./hls_output",
    segment_duration=10,     # 10-second segments
    playlist_entries=15,     # rolling window of 15 segments
)
# Produces:
#   ./hls_output/index.m3u8
#   ./hls_output/segment_001.ts
#   ./hls_output/segment_002.ts
#   ...
```

##### `Muxer.insert_silence(duration_seconds: float, output_path: str) -> str`

Generate a silent audio file of the specified duration (for inter-segment gaps).

---

### `MuxerConfig`

Configuration for the Muxer.

```python
from streamer import MuxerConfig

config = MuxerConfig(
    crossfade_duration=3.0,        # seconds of overlap between tracks
    crossfade_curve="linear",      # linear | exponential | logarithmic
    normalization_enabled=True,
    target_lufs=-23.0,            # broadcast standard
    hls_segment_duration=10,       # seconds per .ts segment
    hls_playlist_entries=15,       # rolling window size
    inter_segment_silence=1.0,    # gap between segments (0 = seamless)
)

muxer = Muxer(config=config)
```

#### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `crossfade_duration` | `float` | `3.0` | Crossfade overlap in seconds |
| `crossfade_curve` | `str` | `"linear"` | Fade curve type |
| `normalization_enabled` | `bool` | `True` | Apply loudness normalization |
| `target_lufs` | `float` | `-23.0` | Target loudness (broadcast standard) |
| `hls_segment_duration` | `int` | `10` | HLS segment length in seconds |
| `hls_playlist_entries` | `int` | `15` | Number of segments in rolling .m3u8 |
| `inter_segment_silence` | `float` | `1.0` | Gap between segments (0 = seamless) |

---

### `Track`

Represents a single audio track in the playlist.

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique identifier (filename-based) |
| `title` | `str` | Track title |
| `filepath` | `str` | Absolute path to audio file |
| `duration_seconds` | `int` | Track duration |
| `quality_score` | `float` | Quality rating (0.0–1.0) used for weighting |
| `mood_tags` | `list[str]` | Mood descriptors (e.g., `["energizing", "dawn"]`) |
| `play_count` | `int` | Times this track has been selected |
| `last_played` | `float \| None` | Timestamp of last play (for no-repeat windows) |
| `created_at` | `float` | When the track was added (for recency boosting) |

---

### `ScheduleSlot`

Defines a programming block in the daily schedule.

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Slot name (e.g., `"Morning Watch"`) |
| `start_hour` | `int` | Start hour (0–23, inclusive) |
| `end_hour` | `int` | End hour (exclusive; wraps overnight if end < start) |
| `mood` | `list[str]` | Mood tags for track selection |
| `min_quality` | `float` | Minimum quality score for tracks in this slot |
| `max_duration_seconds` | `int` | Maximum track duration |
| `description` | `str` | Human-readable slot description |

---

## Configuration File

```yaml
# streamer config.yaml

audio_dir: /path/to/audio/files
output_dir: ./output

crossfade:
  duration_seconds: 3.0
  fade_out_curve: linear      # linear | exponential | logarithmic
  fade_in_curve: linear

inter_segment_silence: 1.0    # seconds between segments (0 = seamless)

normalization:
  enabled: true
  target_lufs: -23.0          # broadcast standard

hls:
  segment_duration_seconds: 10
  playlist_entries: 15

server:
  host: 0.0.0.0
  port: 8420
  max_listeners: 50

schedule:
  slots:
    - name: "Morning Watch"
      start_hour: 6
      end_hour: 10
      mood: [energizing, dawn, warm]
      min_quality: 0.3
      max_duration_seconds: 600
      description: "Morning show, energizing pieces"

    - name: "Overnight Dispatch"
      start_hour: 22
      end_hour: 6
      mood: [ambient, quiet, meditative]
      min_quality: 0.2
      max_duration_seconds: 2400
      description: "Ambient, quiet pieces, overnight"

playlist:
  no_repeat_window_minutes: 240
  min_queue_size: 3
  max_queue_size: 10
  weight_by_quality: true
  weight_by_recency: true
  recency_boost_multiplier: 1.5

coherence:
  anchor_interval_tracks: 8
  anchor_min_quality: 0.8
```

---

## Example: Music Radio Station

A complete example showing how to build a 24/7 music radio station.

```python
import time
import threading
from streamer import Playlist, Scheduler, Muxer, MuxerConfig

# -----------------------------------------------------------------------
# 1. Set up the stream
# -----------------------------------------------------------------------

playlist = Playlist(
    audio_dir="/music/library",
    no_repeat_window_minutes=180,   # 3-hour no-repeat window
    weight_by_quality=True,
    weight_by_recency=True,
)

scheduler = Scheduler(
    playlist=playlist,
    coherence_anchor_interval=8,     # anchor every 8 tracks
    coherence_anchor_min_quality=0.8,
)

config = MuxerConfig(
    crossfade_duration=4.0,          # longer crossfades for music
    normalization_enabled=True,
    target_lufs=-16.0,              # louder than broadcast — this is music
    hls_segment_duration=10,
    inter_segment_silence=0,        # seamless for music
)

muxer = Muxer(config=config)

# -----------------------------------------------------------------------
# 2. Custom schedule for a music station
# -----------------------------------------------------------------------

from streamer import ScheduleSlot

custom_slots = [
    ScheduleSlot(
        name="Sunrise Jazz",
        start_hour=5,
        end_hour=9,
        mood=["jazz", "smooth", "warm", "morning"],
        min_quality=0.4,
        max_duration_seconds=480,
        description="Smooth jazz for waking up",
    ),
    ScheduleSlot(
        name="Morning Classics",
        start_hour=9,
        end_hour=12,
        mood=["classical", "orchestral", "focused"],
        min_quality=0.5,
        max_duration_seconds=900,
        description="Classical music for the morning",
    ),
    ScheduleSlot(
        name="Indie Afternoon",
        start_hour=12,
        end_hour=17,
        mood=["indie", "rock", "energetic", "alternative"],
        min_quality=0.3,
        max_duration_seconds=360,
        description="Indie and alternative rock",
    ),
    ScheduleSlot(
        name="Electronic Evening",
        start_hour=17,
        end_hour=21,
        mood=["electronic", "dance", "upbeat"],
        min_quality=0.4,
        max_duration_seconds=420,
        description="Electronic and dance music",
    ),
    ScheduleSlot(
        name="Late Night Ambient",
        start_hour=21,
        end_hour=5,
        mood=["ambient", "chill", "downtempo", "sleep"],
        min_quality=0.2,
        max_duration_seconds=1200,
        description="Ambient and chill for late night",
    ),
]

scheduler.slots = custom_slots

# -----------------------------------------------------------------------
# 3. Continuous streaming loop
# -----------------------------------------------------------------------

def run_station(output_dir: str = "./stream_output"):
    """Run the station continuously, generating HLS segments."""
    import os
    os.makedirs(output_dir, exist_ok=True)

    segment_counter = 0

    while True:
        # Get the current programming slot
        slot = scheduler.current_slot()
        print(f"[{time.strftime('%H:%M')}] Slot: {slot.name}")

        # Build the next queue
        queue = scheduler.now_playing_queue(size=5)
        print(f"  Queue: {len(queue)} tracks")
        for track in queue:
            print(f"    · {track.title} ({track.duration_seconds}s)")

        # Mux into continuous audio
        batch_output = os.path.join(output_dir, f"batch_{segment_counter}.mp3")
        muxer.concatenate_streaming(queue, batch_output)

        # Segment into HLS
        hls_dir = os.path.join(output_dir, "hls")
        muxer.segment_hls(batch_output, hls_dir)

        # Mark tracks as played
        for track in queue:
            playlist.mark_played(track.id)

        segment_counter += 1

        # Wait before generating next batch
        # (in production, this would be driven by actual playback timing)
        batch_duration = sum(t.duration_seconds for t in queue)
        print(f"  Batch duration: {batch_duration}s")
        time.sleep(min(batch_duration, 60))  # check every minute

# Run the station
# run_station()
```

### Serving the HLS Stream

The streamer includes a built-in HLS server:

```bash
python -m streamer.stream_server \
  --audio-dir /music/library \
  --port 8420
```

Or serve the HLS output with any HTTP server:

```bash
# nginx config
location /stream/ {
    types {
        application/vnd.apple.mpegurl m3u8;
        video/mp2t ts;
    }
    root /path/to/stream_output/hls;
    add_header Cache-Control no-cache;
}
```

---

## Integration Patterns

### Pattern 1: Conductor-Aware Scheduling

```python
from conductor import Conductor
from streamer import Playlist, Scheduler

conductor = Conductor()
playlist = Playlist(audio_dir="/audio")
scheduler = Scheduler(playlist=playlist)

# Adjust music based on conductor session activity
stats = conductor.get_stats()
if stats["active_sessions"] > 10:
    # Busy — play more ambient/background content
    scheduler.current_mood_override = ["ambient", "background"]
else:
    # Quiet — play feature content
    scheduler.current_mood_override = None
```

### Pattern 2: Sonic Shape Integration

```python
from sonic_shape import confidence_to_music
from streamer import Playlist, Scheduler

# When the conductor's confidence is low, inject uncertain music
playlist = Playlist(audio_dir="/audio")

# Generate a confidence-based track and add it
params = confidence_to_music(0.20)  # low confidence → minor key, sparse
mmx_prompt = params.to_mmx_prompt()
# Generate audio via MMX, then add to playlist
# playlist.add_generated_track(generated_audio_path, mood=params.mood_words)
```

### Pattern 3: Cloudflare Workers Backend

For production deployment, use Cloudflare Workers + R2 for serving:

```javascript
// now-playing-worker.js
// Serves the current playing track metadata
export default {
  async fetch(request, env) {
    const nowPlaying = await env.STREAM_KV.get("now_playing", "json");
    return Response.json(nowPlaying);
  }
};
```

```javascript
// HLS segments served from R2
// Upload .ts files and .m3u8 to R2, serve via Worker or directly
```

### Pattern 4: Podcast / Episodic Content

```python
from streamer import Playlist, ScheduleSlot

# Schedule podcast episodes at specific times
podcast_slots = [
    ScheduleSlot(
        name="Daily News Podcast",
        start_hour=7,
        end_hour=8,
        mood=["news", "spoken", "informative"],
        min_quality=0.8,
        max_duration_seconds=1800,
    ),
    ScheduleSlot(
        name="Tech Talk Hour",
        start_hour=13,
        end_hour=14,
        mood=["technology", "interview", "educational"],
        min_quality=0.7,
        max_duration_seconds=3600,
    ),
]

scheduler = Scheduler(playlist=podcast_playlist, slots=podcast_slots)
```

---

## License

MIT © Lucineer / Casey DiGenaro
