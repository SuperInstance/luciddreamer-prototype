# @superinstance/streamer

**Audio streaming muxer — takes audio files and creates a continuous stream.**

Crossfades, normalization, HLS segments, time-of-day scheduling, and coherence anchoring. Works with any audio source directory.

> "A 24/7 stream is a days-long Markov chain in latent space. Temporal coherence drift is the systemic risk." — Nemotron

## Install

```bash
pip install superinstance-streamer
```

**System requirement:** `ffmpeg` must be installed and on your PATH.

## Quick Start

### Run a streaming server

```bash
python -m streamer.stream_server --audio-dir /path/to/audio --port 8420
```

Then open `http://localhost:8420` in your browser.

### Use programmatically

```python
from streamer import Playlist, Scheduler, Muxer

# Load tracks
playlist = Playlist(audio_dir="/path/to/audio")
print(f"Loaded {playlist.size} tracks")

# Schedule based on time of day
scheduler = Scheduler(playlist=playlist)
queue = scheduler.now_playing_queue(size=5)

# Mux into a continuous stream
muxer = Muxer()
output = muxer.concatenate_streaming(queue, "output.mp3")
```

## Components

### Playlist
- Loads audio files from a directory
- Weighted scoring (quality, recency, mood, play count)
- No-repeat windows to prevent over-rotation
- Coherence anchors — high-quality tracks inserted periodically to prevent drift

### Scheduler
- Time-of-day programming (Morning Watch, Midday Essays, Afternoon Theater, Evening Tap, Overnight Dispatch)
- Mood-aware track selection
- Coherence anchor insertion every N tracks

### Muxer
- Crossfade between tracks (configurable duration)
- Loudness normalization (target dBFS)
- HLS segmentation (.m3u8 + .ts files)
- Silent gap insertion between segments

### Stream Server
- HLS streaming HTTP server
- Now-playing status endpoint (`/status`)
- Minimal embedded player at `/`
- Threaded for multiple listeners

## Dependencies

**Required:** `pydub` (audio manipulation)

**System:** `ffmpeg`

**Optional:**
- `pyyaml` — for YAML config files
- `superinstance/conductor` — for agent-aware scheduling
- `superinstance/sonic-shape` — for confidence-driven music generation

## Configuration

```yaml
# config.yaml
audio_dir: /path/to/audio
output_dir: ./output

crossfade:
  duration_seconds: 3.0

normalization:
  enabled: true
  target_lufs: -23.0

hls:
  segment_duration_seconds: 10
  playlist_entries: 15

server:
  host: 0.0.0.0
  port: 8420
```

## License

MIT
