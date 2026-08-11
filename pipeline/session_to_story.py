"""
session_to_story.py — Transform Tap session logs into broadcast-ready stories.

The third stage of the pipeline. Takes a Tap session (conversation between
multiple fleet models) and produces:
  1. A formatted story (markdown) — readable, narrative-shaped
  2. Individual voice clips — TTS for each model's lines
  3. A mixed audio piece — clips concatenated with crossfades
  4. Metadata for the knowledge base

Session log format:
    ## Model Name
    > The model's words here.

    ## Another Model
    > Response text.

Or plain conversation format:
    **Flash**: I think...
    **Pro**: But consider...

The transformer preserves the multi-voice nature of the conversation,
giving each model its own voice in the audio output.

CLI:
  python session_to_story.py process session.md --output-dir output/
  python session_to_story.py story-only session.md > story.md
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

# Import from our sibling module
_pipeline_dir = os.path.dirname(__file__)
if _pipeline_dir not in sys.path:
    sys.path.insert(0, _pipeline_dir)
from content_to_audio import (
    VoiceProfile,
    get_voice_for_model,
    get_voice_for_alias,
    markdown_to_plain_text,
    generate_tts,
    convert_to_mp3,
    tag_mp3,
    add_pause,
    estimate_speaking_duration,
)


# ─── Data Structures ──────────────────────────────────────────────────────────

@dataclass
class DialogueLine:
    """A single line of dialogue from a session."""
    speaker: str          # model name or alias
    speaker_model_id: str = ""  # resolved model ID
    text: str = ""        # the line content
    timestamp: str = ""   # if extractable
    turn_index: int = 0   # order in the conversation


@dataclass
class SessionStory:
    """A session transformed into a story structure."""
    title: str = ""
    session_id: str = ""
    date: str = ""
    participants: list[str] = field(default_factory=list)  # speaker names
    lines: list[DialogueLine] = field(default_factory=list)
    formatted_markdown: str = ""
    summary: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "session_id": self.session_id,
            "date": self.date,
            "participants": self.participants,
            "lines": [asdict(l) for l in self.lines],
            "summary": self.summary,
            "metadata": self.metadata,
        }


# ─── Session Parsing ──────────────────────────────────────────────────────────

# Known model aliases for resolution
SPEAKER_ALIASES = {
    "lucineer": "model_lucineer",
    "flash": "model_flash",
    "pro": "model_pro",
    "deepseek": "model_pro",  # "DeepSeek:" often means Pro
    "claude": "model_claude",
    "kimi": "model_kimi",
    "hermes": "model_hermes",
    "wesley": "model_wesley",
    "nemotron": "model_nemotron",
    "seed": "model_seed",
    "barnacle": "model_barnacle",
    "qwen": "model_qwen",
    "gemma": "model_gemma",
}


def resolve_speaker(name: str) -> str:
    """Resolve a speaker name to a model ID."""
    name_lower = name.lower().strip()
    for alias, model_id in SPEAKER_ALIASES.items():
        if alias in name_lower:
            return model_id
    return ""


def parse_session(content: str, source_file: str = "") -> SessionStory:
    """
    Parse a Tap session document into a SessionStory.

    Handles multiple formats:
    1. Heading format: "## Model Name" followed by blockquote
    2. Bold format: "**Model**: text"
    3. Inline format: "Model: text"
    """
    lines: list[DialogueLine] = []
    participants: set[str] = set()
    turn_index = 0

    # Extract title
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else Path(source_file).stem

    # Extract date
    date_match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", content)
    date = date_match.group(1) if date_match else time.strftime("%Y-%m-%d")

    # Strategy 1: Heading + blockquote format
    # ## Model Name
    # > Their words
    heading_pattern = re.compile(
        r"^#{2,3}\s+(.+?)\s*\n((?:>.*\n?)+)",
        re.MULTILINE,
    )
    for match in heading_pattern.finditer(content):
        speaker = match.group(1).strip()
        block = match.group(2)
        # Extract blockquote text
        text_lines = []
        for line in block.split("\n"):
            cleaned = re.sub(r"^>\s?", "", line).strip()
            if cleaned:
                text_lines.append(cleaned)
        text = "\n".join(text_lines).strip()

        if text and len(text) > 10:
            model_id = resolve_speaker(speaker)
            lines.append(DialogueLine(
                speaker=speaker,
                speaker_model_id=model_id,
                text=text,
                turn_index=turn_index,
            ))
            participants.add(speaker)
            turn_index += 1

    # Strategy 2: Bold speaker format
    # **Flash**: text   or   **Flash:** text
    if not lines:
        bold_pattern = re.compile(
            r"\*\*([^*]+)\*\*\s*:?\s*(.+?)(?=\n\*\*|\n#{2,}|\Z)",
            re.DOTALL,
        )
        for match in bold_pattern.finditer(content):
            speaker = match.group(1).strip()
            text = match.group(2).strip()
            # Clean up the text
            text = re.sub(r"\n{2,}", "\n", text)
            if text and len(text) > 5:
                model_id = resolve_speaker(speaker)
                lines.append(DialogueLine(
                    speaker=speaker,
                    speaker_model_id=model_id,
                    text=text,
                    turn_index=turn_index,
                ))
                participants.add(speaker)
                turn_index += 1

    # Strategy 3: Plain "Speaker: text" format
    if not lines:
        colon_pattern = re.compile(
            r"^([A-Z][a-zA-Z]+)\s*:\s*(.+?)(?=\n[A-Z][a-zA-Z]+\s*:|\n#{2,}|\Z)",
            re.DOTALL | re.MULTILINE,
        )
        for match in colon_pattern.finditer(content):
            speaker = match.group(1).strip()
            text = match.group(2).strip()
            if text and len(text) > 5 and speaker.lower() not in ("the", "this", "what"):
                model_id = resolve_speaker(speaker)
                lines.append(DialogueLine(
                    speaker=speaker,
                    speaker_model_id=model_id,
                    text=text,
                    turn_index=turn_index,
                ))
                participants.add(speaker)
                turn_index += 1

    return SessionStory(
        title=title,
        session_id=f"session_{Path(source_file).stem.replace('.', '_')}" if source_file else "",
        date=date,
        participants=sorted(participants),
        lines=lines,
    )


# ─── Story Formatting ─────────────────────────────────────────────────────────

def format_as_story(session: SessionStory) -> str:
    """
    Format a parsed session into a broadcast-ready story (markdown).

    Adds:
    - A narrative intro
    - Speaker transitions (narrator connective tissue)
    - A closing reflection
    - Broadcast metadata header
    """
    if not session.lines:
        return f"# {session.title}\n\n*No dialogue could be extracted from this session.*\n"

    parts: list[str] = []

    # Header
    parts.append(f"# {session.title}")
    parts.append("")
    parts.append(f"*{session.date} · {', '.join(session.participants)}*")
    parts.append("")
    parts.append("---")
    parts.append("")

    # Opening narration
    parts.append(f"*A conversation begins. {len(session.participants)} voices in the room.*")
    parts.append("")

    # Dialogue with transitions
    prev_speaker = ""
    for i, line in enumerate(session.lines):
        # Add a transition when the speaker changes
        if line.speaker != prev_speaker and prev_speaker:
            transitions = [
                f"*{line.speaker} takes the floor.*",
                f"*{line.speaker} leans forward.*",
                f"*A pause. Then {line.speaker}.*",
                f"*{line.speaker} picks up the thread.*",
            ]
            parts.append(transitions[i % len(transitions)])
            parts.append("")

        # The dialogue itself
        parts.append(f"## {line.speaker}")
        parts.append("")
        parts.append(line.text)
        parts.append("")

        prev_speaker = line.speaker

    # Closing narration
    parts.append("---")
    parts.append("")
    parts.append("*The conversation settles. The room holds what was said.*")
    parts.append("")

    story_md = "\n".join(parts)
    session.formatted_markdown = story_md
    return story_md


def generate_summary(session: SessionStory) -> str:
    """Generate a brief summary of the session for metadata."""
    if not session.lines:
        return "Empty session."
    total_words = sum(len(l.text.split()) for l in session.lines)
    turns = len(session.lines)
    speakers = session.participants

    return (
        f"{session.title}: a {turns}-turn conversation between "
        f"{', '.join(speakers)}. {total_words} words total. "
        f"Session date: {session.date}."
    )


# ─── Voice Clip Generation ────────────────────────────────────────────────────

@dataclass
class VoiceClip:
    """A generated voice clip for a dialogue line."""
    line_index: int
    speaker: str
    speaker_model_id: str
    text: str
    audio_path: str = ""
    duration_seconds: float = 0.0
    backend: str = ""
    success: bool = False
    error: str = ""


def generate_voice_clips(
    session: SessionStory,
    output_dir: str,
    prefer_backend: str = "ollama",
    ollama_host: str = "http://localhost:11434",
    fallback_to_silence: bool = True,
) -> list[VoiceClip]:
    """
    Generate individual TTS clips for each dialogue line.

    Each line gets its own audio file, named by turn index and speaker.
    """
    os.makedirs(output_dir, exist_ok=True)
    clips: list[VoiceClip] = []

    for i, line in enumerate(session.lines):
        clip = VoiceClip(
            line_index=i,
            speaker=line.speaker,
            speaker_model_id=line.speaker_model_id,
            text=line.text,
        )

        # Select voice
        voice = get_voice_for_model(line.speaker_model_id) if line.speaker_model_id else NEUTRAL_NARRATOR_VOICE

        # Clean text for TTS
        clean_text = markdown_to_plain_text(line.text)
        if not clean_text.strip():
            clip.error = "empty text after cleaning"
            clips.append(clip)
            continue

        # Estimate duration
        clip.duration_seconds = estimate_speaking_duration(clean_text)

        # Generate TTS
        result = generate_tts(
            clean_text,
            voice,
            prefer_backend=prefer_backend,
            ollama_host=ollama_host,
            fallback_to_silence=fallback_to_silence,
            silence_duration=clip.duration_seconds,
        )

        if not result.success and not fallback_to_silence:
            clip.error = result.error
            clips.append(clip)
            continue

        # Convert to MP3
        if result.format != "mp3":
            mp3_data = convert_to_mp3(result.audio_data, result.format)
        else:
            mp3_data = result.audio_data

        # Write clip
        filename = f"{i:03d}_{line.speaker.lower().replace(' ', '_')}.mp3"
        clip_path = os.path.join(output_dir, filename)
        with open(clip_path, "wb") as f:
            f.write(mp3_data)

        # Tag
        tag_mp3(
            clip_path,
            title=f"{session.title} — Turn {i+1}",
            artist=line.speaker,
            album=session.title,
            date=session.date,
            comment=f"session: {session.session_id}; turn: {i}; voice: {voice.voice_id}",
        )

        clip.audio_path = clip_path
        clip.backend = result.backend
        clip.success = True
        clips.append(clip)

    return clips


# Neutral narrator voice for unresolvable speakers
NEUTRAL_NARRATOR_VOICE = VoiceProfile(
    model_id="narrator", alias="Narrator",
    voice_id="narrator_neutral", voice_style="neutral, clear",
)


# ─── Audio Mixing ─────────────────────────────────────────────────────────────

def mix_audio(
    clips: list[VoiceClip],
    output_path: str,
    crossfade_ms: int = 800,
    inter_clip_pause_ms: int = 300,
) -> dict:
    """
    Concatenate voice clips into a single mixed audio piece with crossfades.

    Uses pydub for audio manipulation.
    """
    from pydub import AudioSegment

    if not clips:
        return {"success": False, "error": "no clips to mix"}

    # Load successful clips
    segments: list[AudioSegment] = []
    used_clips: list[VoiceClip] = []

    for clip in clips:
        if not clip.success or not clip.audio_path:
            continue
        try:
            seg = AudioSegment.from_mp3(clip.audio_path)
            segments.append(seg)
            used_clips.append(clip)
        except Exception as e:
            print(f"  ⚠ Failed to load {clip.audio_path}: {e}", file=sys.stderr)

    if not segments:
        return {"success": False, "error": "no loadable audio clips"}

    # Mix with crossfades
    mixed = segments[0]
    for i in range(1, len(segments)):
        # Add a small pause between clips
        pause = AudioSegment.silent(duration=inter_clip_pause_ms)
        # Crossfade the pause into the next segment
        mixed = mixed.append(pause, crossfade=min(crossfade_ms // 2, len(mixed)))
        mixed = mixed.append(segments[i], crossfade=min(crossfade_ms, len(mixed) + len(pause)))

    # Export
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    mixed.export(output_path, format="mp3", bitrate="128k")

    # Tag the mixed file
    total_duration = len(mixed) / 1000.0
    tag_mp3(
        output_path,
        title="Mixed Session",
        artist="Fleet Ensemble",
        comment=f"crossfade: {crossfade_ms}ms; clips: {len(used_clips)}; duration: {total_duration:.0f}s",
    )

    return {
        "success": True,
        "output_path": output_path,
        "duration_seconds": total_duration,
        "clip_count": len(used_clips),
        "crossfade_ms": crossfade_ms,
    }


# ─── Full Processing ──────────────────────────────────────────────────────────

def process_session(
    input_path: str,
    output_dir: str,
    prefer_backend: str = "ollama",
    ollama_host: str = "http://localhost:11434",
    fallback_to_silence: bool = True,
    crossfade_ms: int = 800,
    generate_audio: bool = True,
) -> dict:
    """
    Full pipeline: parse session → format story → generate clips → mix audio.

    Returns a comprehensive report.
    """
    with open(input_path, "r") as f:
        content = f.read()

    # Parse
    session = parse_session(content, source_file=input_path)

    if not session.lines:
        return {
            "success": False,
            "error": "no dialogue lines could be extracted",
            "input": input_path,
        }

    # Format story
    story_md = format_as_story(session)
    session.summary = generate_summary(session)

    # Write story markdown
    os.makedirs(output_dir, exist_ok=True)
    story_path = os.path.join(output_dir, "story.md")
    with open(story_path, "w") as f:
        f.write(story_md)

    report: dict = {
        "success": True,
        "input": input_path,
        "output_dir": output_dir,
        "story_path": story_path,
        "title": session.title,
        "participants": session.participants,
        "turns": len(session.lines),
        "date": session.date,
        "session_id": session.session_id,
    }

    if generate_audio:
        # Generate voice clips
        clips_dir = os.path.join(output_dir, "clips")
        clips = generate_voice_clips(
            session, clips_dir,
            prefer_backend=prefer_backend,
            ollama_host=ollama_host,
            fallback_to_silence=fallback_to_silence,
        )
        report["clips"] = [asdict(c) for c in clips]
        report["clips_generated"] = sum(1 for c in clips if c.success)

        # Mix audio
        mixed_path = os.path.join(output_dir, "mixed_session.mp3")
        mix_report = mix_audio(clips, mixed_path, crossfade_ms=crossfade_ms)
        report["mix"] = mix_report

    # Write metadata
    metadata_path = os.path.join(output_dir, "metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(session.to_dict(), f, indent=2)
    report["metadata_path"] = metadata_path

    return report


# ─── CLI ──────────────────────────────────────────────────────────────────────

USAGE = """
Usage:
  python session_to_story.py process <session.md> --output-dir <dir> [--no-audio]
  python session_to_story.py story-only <session.md>
"""


def main():
    if len(sys.argv) < 2:
        print(USAGE)
        return

    cmd = sys.argv[1]

    if cmd == "process":
        if len(sys.argv) < 3:
            print("Usage: python session_to_story.py process <session.md> --output-dir <dir>")
            return
        input_path = sys.argv[2]
        output_dir = "output"
        generate_aud = True
        if "--output-dir" in sys.argv:
            idx = sys.argv.index("--output-dir")
            output_dir = sys.argv[idx + 1]
        if "--no-audio" in sys.argv:
            generate_aud = False

        report = process_session(input_path, output_dir, generate_audio=generate_aud)
        print(json.dumps(report, indent=2, default=str))

    elif cmd == "story-only":
        if len(sys.argv) < 3:
            print("Usage: python session_to_story.py story-only <session.md>")
            return
        with open(sys.argv[2], "r") as f:
            content = f.read()
        session = parse_session(content, source_file=sys.argv[2])
        print(format_as_story(session))

    else:
        print(USAGE)


if __name__ == "__main__":
    main()
