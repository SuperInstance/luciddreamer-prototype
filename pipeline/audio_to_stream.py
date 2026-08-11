"""
audio_to_stream.py — Score and ingest audio files into the streamer's playlist.

The second stage of the pipeline. Scans a directory for new audio files,
scores them by quality metrics, assigns time-of-day mood tags, and updates
the streamer's playlist.json.

Scoring dimensions:
  - LENGTH:     ideal duration range per show slot
  - SOURCE:     higher quality for known models vs unknown
  - RECENCY:    newer content gets a boost
  - VOICE:      clear TTS > silence fallback
  - COMPLETENESS: has metadata tags

The output is a playlist.json that the streamer's scheduler can consume,
alongside the existing playlist.py Track system.

CLI:
  python audio_to_stream.py scan /path/to/audio/ --output playlist.json
  python audio_to_stream.py update /path/to/audio/ --playlist playlist.json
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from mutagen.mp3 import MP3
from mutagen.id3 import ID3

# Import playlist from the streamer package
_streamer_path = os.path.join(os.path.dirname(__file__), "..", "streamer")
if _streamer_path not in sys.path:
    sys.path.insert(0, _streamer_path)
from playlist import Track, Playlist  # noqa: E402


# ─── Time-of-Day Mood Mapping ─────────────────────────────────────────────────

# Maps show slots to mood tags that the scheduler uses
SHOW_SLOTS = {
    "morning": {
        "name": "Morning Watch",
        "start_hour": 6, "end_hour": 10,
        "mood": ["energizing", "dawn", "announcement", "warm"],
        "ideal_duration_range": (60, 600),  # seconds
    },
    "midday": {
        "name": "Midday Essays",
        "start_hour": 10, "end_hour": 14,
        "mood": ["essay", "interview", "educational", "thoughtful"],
        "ideal_duration_range": (120, 1800),
    },
    "afternoon": {
        "name": "Afternoon Theater",
        "start_hour": 14, "end_hour": 18,
        "mood": ["drama", "creative", "experimental", "playful"],
        "ideal_duration_range": (60, 1200),
    },
    "evening": {
        "name": "Evening Tap",
        "start_hour": 18, "end_hour": 22,
        "mood": ["live", "conversational", "open_mic", "warm"],
        "ideal_duration_range": (120, 1800),
    },
    "overnight": {
        "name": "Overnight Dispatch",
        "start_hour": 22, "end_hour": 6,
        "mood": ["ambient", "quiet", "meditative", "music_heavy"],
        "ideal_duration_range": (120, 2400),
    },
}


def get_slot_for_hour(hour: int) -> str:
    """Get the slot key for a given hour."""
    for key, slot in SHOW_SLOTS.items():
        if slot["start_hour"] <= slot["end_hour"]:
            if slot["start_hour"] <= hour < slot["end_hour"]:
                return key
        else:
            # Wraps midnight
            if hour >= slot["start_hour"] or hour < slot["end_hour"]:
                return key
    return "overnight"


def get_mood_for_content(source_model: str, show_name: str, tags: list[str]) -> list[str]:
    """Determine mood tags for a piece of content."""
    moods: list[str] = []

    # Show name → mood
    show_lower = show_name.lower()
    if "tap" in show_lower:
        moods.extend(["live", "conversational", "warm"])
    elif "vision" in show_lower:
        moods.extend(["essay", "thoughtful"])
    elif "deep time" in show_lower:
        moods.extend(["ambient", "meditative"])
    elif "morning" in show_lower or "dawn" in show_lower:
        moods.extend(["energizing", "dawn", "announcement"])
    elif "shipwright" in show_lower:
        moods.extend(["essay", "educational"])

    # Tag-based mood
    for tag in tags:
        tag_lower = tag.lower()
        if tag_lower in ("creative", "drama", "story"):
            moods.extend(["creative", "playful"])
        elif tag_lower in ("ambient", "quiet"):
            moods.extend(["ambient", "quiet"])
        elif tag_lower in ("risk", "warning"):
            moods.extend(["thoughtful"])

    # Deduplicate while preserving order
    seen = set()
    result = []
    for m in moods:
        if m not in seen:
            seen.add(m)
            result.append(m)
    return result


# ─── Quality Scoring ──────────────────────────────────────────────────────────

@dataclass
class AudioScorer:
    """
    Scores audio files for playlist inclusion.

    Dimensions:
      - length_score:     how close to the ideal duration range
      - source_score:     known model vs unknown
      - recency_score:    newer is better
      - voice_score:      real TTS > silence
      - metadata_score:   has ID3 tags
    """
    now: float = field(default_factory=time.time)
    recency_half_life_days: float = 7.0  # half-life for recency decay

    def score_length(self, duration_seconds: float, slot_key: str = "midday") -> float:
        """Score based on how well the duration fits the slot's ideal range."""
        slot = SHOW_SLOTS.get(slot_key, SHOW_SLOTS["midday"])
        min_dur, max_dur = slot["ideal_duration_range"]

        if duration_seconds <= 0:
            return 0.1  # unknown duration — low score

        if min_dur <= duration_seconds <= max_dur:
            return 1.0  # perfect fit

        # Penalty for being outside range
        if duration_seconds < min_dur:
            ratio = duration_seconds / min_dur
            return max(0.2, ratio)
        else:
            # Too long — gradual penalty
            ratio = max_dur / duration_seconds
            return max(0.3, ratio)

    def score_source(self, source_model: str, tags: dict) -> float:
        """Score based on source model. Known models score higher."""
        if not source_model or source_model == "unknown":
            return 0.3
        # Known fleet models
        known_models = {
            "model_lucineer", "model_flash", "model_pro", "model_claude",
            "model_kimi", "model_hermes", "model_wesley", "model_nemotron",
            "model_seed", "model_barnacle", "model_qwen", "model_gemma",
        }
        if source_model in known_models:
            return 1.0
        if any(kw in source_model.lower() for kw in ["model_", "fleet"]):
            return 0.7
        return 0.4

    def score_recency(self, created_at: float) -> float:
        """Score based on recency. Newer content gets exponentially more weight."""
        if created_at <= 0:
            return 0.3
        age_days = (self.now - created_at) / 86400
        if age_days < 0:
            age_days = 0
        # Exponential decay with half-life
        return 0.5 ** (age_days / self.recency_half_life_days)

    def score_voice(self, tags: dict, backend: str = "") -> float:
        """Score based on TTS backend quality."""
        backend_lower = backend.lower()
        if "ollama" in backend_lower:
            return 0.9
        if "cloudflare" in backend_lower:
            return 0.85
        if "silence" in backend_lower:
            return 0.1  # silence is bad
        # Check comment tag for backend info
        comment = tags.get("comment", "")
        if "silence" in comment.lower():
            return 0.1
        if "ollama" in comment.lower():
            return 0.9
        if "cloudflare" in comment.lower():
            return 0.85
        return 0.5  # unknown

    def score_metadata(self, tags: dict) -> float:
        """Score based on metadata completeness."""
        fields = ["title", "artist", "album", "date"]
        filled = sum(1 for f in fields if tags.get(f) and str(tags[f]).strip())
        return filled / len(fields)

    def score(
        self,
        duration_seconds: float = 0.0,
        source_model: str = "",
        created_at: float = 0.0,
        tags: Optional[dict] = None,
        backend: str = "",
        slot_key: str = "midday",
    ) -> dict:
        """Compute the full quality score for a track."""
        tags = tags or {}
        length_s = self.score_length(duration_seconds, slot_key)
        source_s = self.score_source(source_model, tags)
        recency_s = self.score_recency(created_at)
        voice_s = self.score_voice(tags, backend)
        meta_s = self.score_metadata(tags)

        # Weighted combination
        # Voice quality matters most — silence is not broadcastable
        weights = {
            "length": 0.15,
            "source": 0.15,
            "recency": 0.20,
            "voice": 0.35,
            "metadata": 0.15,
        }

        total = (
            length_s * weights["length"]
            + source_s * weights["source"]
            + recency_s * weights["recency"]
            + voice_s * weights["voice"]
            + meta_s * weights["metadata"]
        )

        return {
            "total": round(total, 3),
            "length": round(length_s, 3),
            "source": round(source_s, 3),
            "recency": round(recency_s, 3),
            "voice": round(voice_s, 3),
            "metadata": round(meta_s, 3),
        }


# ─── Audio Scanner ────────────────────────────────────────────────────────────

SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".aac", ".ogg", ".flac", ".m4a"}


def scan_audio_directory(directory: str) -> list[dict]:
    """
    Scan a directory for audio files and extract metadata.

    Returns a list of file info dicts with:
    - path, filename, extension, size, mtime
    - duration_seconds (if readable)
    - id3_tags (if present)
    """
    directory_path = Path(directory)
    if not directory_path.exists():
        return []

    results: list[dict] = []
    for filepath in sorted(directory_path.iterdir()):
        if filepath.suffix.lower() not in SUPPORTED_AUDIO_EXTENSIONS:
            continue

        stat = filepath.stat()
        info: dict = {
            "path": str(filepath),
            "filename": filepath.name,
            "extension": filepath.suffix.lower(),
            "size_bytes": stat.st_size,
            "mtime": stat.st_mtime,
            "duration_seconds": 0.0,
            "id3_tags": {},
        }

        # Try to read audio metadata
        try:
            if filepath.suffix.lower() == ".mp3":
                audio = MP3(str(filepath))
                info["duration_seconds"] = audio.info.length if audio.info else 0.0
                if audio.tags:
                    tags = {}
                    for key in ["TIT2", "TPE1", "TALB", "TCON", "TDRC", "COMM"]:
                        if key in audio.tags:
                            tags[key.lower().replace("tit2", "title").replace("tpe1", "artist")
                                 .replace("talb", "album").replace("tcon", "genre")
                                 .replace("tdrc", "date").replace("comm", "comment")] = str(audio.tags[key])
                    info["id3_tags"] = tags
        except Exception:
            pass  # Not a valid MP3 or unreadable

        results.append(info)

    return results


def parse_backend_from_comment(comment: str) -> str:
    """Extract the TTS backend name from an ID3 comment."""
    if not comment:
        return ""
    match = re.search(r"backend:\s*(\w+)", comment)
    return match.group(1) if match else ""


def parse_model_from_comment(comment: str) -> str:
    """Extract the source model from an ID3 comment."""
    if not comment:
        return ""
    match = re.search(r"source:\s*([^\s;]+)", comment)
    return match.group(1) if match else ""


# ─── Playlist JSON ────────────────────────────────────────────────────────────

@dataclass
class PlaylistEntry:
    """A single entry in the playlist JSON."""
    path: str
    title: str
    artist: str = ""
    album: str = ""
    duration_seconds: float = 0.0
    quality_score: float = 0.0
    quality_breakdown: dict = field(default_factory=dict)
    mood_tags: list[str] = field(default_factory=list)
    show_name: str = ""
    source_model: str = ""
    backend: str = ""
    created_at: float = 0.0
    file_size_bytes: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


def create_playlist_entry(file_info: dict, scorer: Optional[AudioScorer] = None) -> PlaylistEntry:
    """Create a scored PlaylistEntry from a scanned file info dict."""
    scorer = scorer or AudioScorer()
    tags = file_info.get("id3_tags", {})

    # Extract metadata
    title = tags.get("title") or Path(file_info["path"]).stem.replace("-", " ").replace("_", " ").title()
    artist = tags.get("artist", "")
    album = tags.get("album", "")
    duration = file_info.get("duration_seconds", 0.0)
    created_at = file_info.get("mtime", 0.0)
    comment = tags.get("comment", "")
    backend = parse_backend_from_comment(comment)
    source_model = parse_model_from_comment(comment) or artist

    # Determine mood tags
    mood_tags = get_mood_for_content(source_model, album, [])

    # Score the track
    quality = scorer.score(
        duration_seconds=duration,
        source_model=source_model,
        created_at=created_at,
        tags=tags,
        backend=backend,
    )

    return PlaylistEntry(
        path=file_info["path"],
        title=title,
        artist=artist,
        album=album,
        duration_seconds=duration,
        quality_score=quality["total"],
        quality_breakdown=quality,
        mood_tags=mood_tags,
        show_name=album,
        source_model=source_model,
        backend=backend,
        created_at=created_at,
        file_size_bytes=file_info.get("size_bytes", 0),
    )


def update_playlist_json(
    audio_dir: str,
    playlist_path: str,
    scorer: Optional[AudioScorer] = None,
) -> dict:
    """
    Scan directory and update the playlist JSON.

    Merges new files into an existing playlist, preserving play counts.
    Returns a summary of what changed.
    """
    scorer = scorer or AudioScorer()

    # Load existing playlist
    existing: dict[str, dict] = {}
    if os.path.exists(playlist_path):
        with open(playlist_path, "r") as f:
            data = json.load(f)
            for entry in data.get("tracks", []):
                existing[entry["path"]] = entry

    # Scan for audio files
    files = scan_audio_directory(audio_dir)

    # Create/update entries
    entries: list[dict] = []
    new_count = 0
    updated_count = 0

    for file_info in files:
        entry = create_playlist_entry(file_info, scorer)
        entry_dict = entry.to_dict()

        if file_info["path"] in existing:
            # Preserve play history
            old = existing[file_info["path"]]
            entry_dict["played_count"] = old.get("played_count", 0)
            entry_dict["last_played"] = old.get("last_played", 0)
            updated_count += 1
        else:
            entry_dict["played_count"] = 0
            entry_dict["last_played"] = 0
            new_count += 1

        entries.append(entry_dict)

    # Sort by quality score descending
    entries.sort(key=lambda e: e.get("quality_score", 0), reverse=True)

    # Write playlist
    playlist_data = {
        "version": "1.0",
        "updated_at": time.time(),
        "audio_dir": audio_dir,
        "total_tracks": len(entries),
        "tracks": entries,
    }

    os.makedirs(os.path.dirname(playlist_path) or ".", exist_ok=True)
    with open(playlist_path, "w") as f:
        json.dump(playlist_data, f, indent=2)

    return {
        "total": len(entries),
        "new": new_count,
        "updated": updated_count,
        "playlist_path": playlist_path,
        "avg_quality": sum(e["quality_score"] for e in entries) / len(entries) if entries else 0.0,
    }


# ─── CLI ──────────────────────────────────────────────────────────────────────

USAGE = """
Usage:
  python audio_to_stream.py scan <audio_dir> [--output playlist.json]
  python audio_to_stream.py update <audio_dir> --playlist <playlist.json>
"""


def main():
    if len(sys.argv) < 2:
        print(USAGE)
        return

    cmd = sys.argv[1]

    if cmd == "scan":
        if len(sys.argv) < 3:
            print("Usage: python audio_to_stream.py scan <audio_dir>")
            return
        directory = sys.argv[2]
        output = "playlist.json"
        if "--output" in sys.argv:
            idx = sys.argv.index("--output")
            output = sys.argv[idx + 1]

        report = update_playlist_json(directory, output)
        print(json.dumps(report, indent=2))

    elif cmd == "update":
        directory = None
        playlist_path = "playlist.json"
        if "--playlist" in sys.argv:
            idx = sys.argv.index("--playlist")
            playlist_path = sys.argv[idx + 1]
        if len(sys.argv) >= 3 and not sys.argv[2].startswith("--"):
            directory = sys.argv[2]

        if not directory:
            print("Error: audio directory required")
            print(USAGE)
            return

        report = update_playlist_json(directory, playlist_path)
        print(json.dumps(report, indent=2))

    else:
        print(USAGE)


if __name__ == "__main__":
    main()
