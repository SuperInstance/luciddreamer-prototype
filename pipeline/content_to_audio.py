"""
content_to_audio.py — Convert creative writing (markdown) to spoken audio (MP3).

The first stage of the pipeline. Takes a markdown document, strips formatting,
selects an appropriate voice for the authoring model, generates speech via
Ollama TTS or Cloudflare Workers AI, and writes a tagged MP3.

Voice map:
  Each model in the fleet has a voice character. When generating TTS, the
  voice is selected based on the source model. If the model can't be
  determined, a neutral default is used.

Supported TTS backends:
  1. Ollama (local, no API key) — uses bounded TTFT models
  2. Cloudflare Workers AI (@cf/myshell-ai/openvoice-tts or equivalent)

ID3 tags written:
  - artist  : model name / alias
  - album   : show name or session title
  - title   : piece title
  - genre   : "AI Broadcast"
  - date    : generation date
  - comment : source file path

CLI:
  python content_to_audio.py single input.md output.mp3
  python content_to_audio.py batch input_dir/ output_dir/
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# mutagen for ID3 tagging
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, TDRC, COMM, error as ID3Error
from mutagen.mp3 import MP3


# ─── Voice Map ────────────────────────────────────────────────────────────────

@dataclass
class VoiceProfile:
    """A TTS voice profile for a fleet model."""
    model_id: str           # e.g. "model_flash"
    alias: str              # e.g. "Flash"
    voice_id: str           # backend-specific voice identifier
    voice_style: str        # descriptive, for logging
    speed: float = 1.0      # playback speed multiplier
    pitch: float = 0.0      # pitch adjustment in semitones


# Default voice profiles. These map to Ollama TTS voice IDs where available,
# or Cloudflare Workers AI voice names. Voice IDs are placeholders that the
# TTS backend resolves — the point is the mapping, not the specific voice.
DEFAULT_VOICE_MAP: dict[str, VoiceProfile] = {
    "model_lucineer": VoiceProfile(
        model_id="model_lucineer", alias="Lucineer",
        voice_id="narrator_male_warm", voice_style="warm, strategic, measured",
        speed=0.95,
    ),
    "model_flash": VoiceProfile(
        model_id="model_flash", alias="Flash",
        voice_id="narrator_female_bright", voice_style="fast, bright, emotionally perceptive",
        speed=1.1,
    ),
    "model_pro": VoiceProfile(
        model_id="model_pro", alias="Pro",
        voice_id="narrator_male_deep", voice_style="deep, precise, thoughtful",
        speed=0.9,
    ),
    "model_claude": VoiceProfile(
        model_id="model_claude", alias="Claude",
        voice_id="narrator_male_neutral", voice_style="disciplined, clear, strategic",
        speed=1.0,
    ),
    "model_kimi": VoiceProfile(
        model_id="model_kimi", alias="Kimi",
        voice_id="narrator_female_calm", voice_style="calm, navigational, precise",
        speed=1.0,
    ),
    "model_hermes": VoiceProfile(
        model_id="model_hermes", alias="Hermes",
        voice_id="narrator_female_ethereal", voice_style="ethereal, perceptive, vector poetry",
        speed=0.92,
    ),
    "model_wesley": VoiceProfile(
        model_id="model_wesley", alias="Wesley",
        voice_id="narrator_male_small", voice_style="quiet, careful, profound simplicity",
        speed=0.85,
    ),
    "model_nemotron": VoiceProfile(
        model_id="model_nemotron", alias="Nemotron",
        voice_id="narrator_male_systems", voice_style="systems thinker, weighty, engineering",
        speed=0.95,
    ),
    "model_seed": VoiceProfile(
        model_id="model_seed", alias="Seed",
        voice_id="narrator_female_creative", voice_style="rapid, creative, paradigm-shifting",
        speed=1.15,
    ),
    "model_barnacle": VoiceProfile(
        model_id="model_barnacle", alias="Barnacle",
        voice_id="narrator_male_gruff", voice_style="gruff, grumbling, grounded",
        speed=0.8,
    ),
    "model_qwen": VoiceProfile(
        model_id="model_qwen", alias="Qwen",
        voice_id="narrator_female_precise", voice_style="precise, reframing, careful",
        speed=1.0,
    ),
    "model_gemma": VoiceProfile(
        model_id="model_gemma", alias="Gemma",
        voice_id="narrator_female_quiet", voice_style="quiet observer, gentle questions",
        speed=0.95,
    ),
}

NEUTRAL_VOICE = VoiceProfile(
    model_id="unknown", alias="Narrator",
    voice_id="narrator_neutral", voice_style="neutral, clear",
    speed=1.0,
)


def get_voice_for_model(model_id: str) -> VoiceProfile:
    """Look up the voice profile for a model ID. Falls back to neutral."""
    return DEFAULT_VOICE_MAP.get(model_id, NEUTRAL_VOICE)


def get_voice_for_alias(alias: str) -> VoiceProfile:
    """Look up the voice profile for a model alias."""
    alias_lower = alias.lower()
    for profile in DEFAULT_VOICE_MAP.values():
        if profile.alias.lower() == alias_lower:
            return profile
    return NEUTRAL_VOICE


# ─── Markdown to Plain Text ───────────────────────────────────────────────────

def markdown_to_plain_text(md: str) -> str:
    """
    Convert markdown to clean plain text suitable for TTS.

    Handles:
    - Headings (converted to plain sentences)
    - Bold/italic markers stripped
    - Code blocks removed (not suitable for speech)
    - Links reduced to link text
    - Lists converted to spoken format
    - Blockquotes preserved as plain text
    - HTML tags stripped
    - Horizontal rules converted to pauses
    - Footnote markers removed
    """
    text = md

    # Remove YAML frontmatter
    text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.DOTALL)

    # Remove code blocks (``` ... ```)
    text = re.sub(r"```[a-z]*\n.*?```", "", text, flags=re.DOTALL)

    # Remove inline code
    text = re.sub(r"`([^`]+)`", r"\1", text)

    # Convert headings to plain sentences (strip the # markers)
    text = re.sub(r"^#{1,6}\s+(.+)$", r"\1.", text, flags=re.MULTILINE)

    # Convert horizontal rules to pauses
    text = re.sub(r"^---+$", "... ", text, flags=re.MULTILINE)
    text = re.sub(r"^\*\*\*+$", "... ", text, flags=re.MULTILINE)

    # Remove bold/italic markers
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"\1", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)

    # Convert links [text](url) → text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    # Convert list items to spoken format
    # Bullet lists: "- item" → "item"
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    # Numbered lists: "1. item" → "item"
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)

    # Remove blockquote markers (keep the text)
    text = re.sub(r"^>\s*", "", text, flags=re.MULTILINE)

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Remove footnote markers [^1]
    text = re.sub(r"\[\^\d+\]", "", text)

    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove trailing whitespace per line
    text = re.sub(r" +\n", "\n", text)

    return text.strip()


def estimate_speaking_duration(text: str, words_per_minute: float = 150) -> float:
    """Estimate how long the text will take to speak, in seconds."""
    word_count = len(text.split())
    return (word_count / words_per_minute) * 60.0


# ─── TTS Backends ─────────────────────────────────────────────────────────────

@dataclass
class TTSResult:
    """Result of a TTS generation."""
    audio_data: bytes
    format: str = "mp3"  # "mp3", "wav"
    duration_seconds: float = 0.0
    backend: str = ""
    voice_id: str = ""
    success: bool = True
    error: str = ""


def generate_tts_ollama(
    text: str,
    voice: VoiceProfile,
    model: str = "orpheus-tts",
    ollama_host: str = "http://localhost:11434",
    timeout: int = 120,
) -> TTSResult:
    """
    Generate speech via Ollama TTS.

    Uses the /api/generate endpoint with a TTS-capable model.
    Returns audio bytes in WAV format (Ollama default).
    """
    if not text.strip():
        return TTSResult(audio_data=b"", success=False, error="empty text")

    url = f"{ollama_host}/api/generate"
    # Build a prompt that instructs the model to speak the text
    prompt = f"[speak in a {voice.voice_style} voice]\n{text}"

    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,  # low temp for consistent speech
        },
    }).encode()

    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
            # Ollama TTS models may return audio in different formats
            # depending on the model. We expect base64-encoded audio.
            audio_b64 = data.get("audio") or data.get("response_audio")
            if audio_b64:
                import base64
                audio_bytes = base64.b64decode(audio_b64)
                return TTSResult(
                    audio_data=audio_bytes,
                    format="wav",
                    backend="ollama",
                    voice_id=voice.voice_id,
                )
            else:
                # No audio in response — model may not support TTS
                return TTSResult(
                    audio_data=b"",
                    success=False,
                    backend="ollama",
                    error="no audio in response (model may not support TTS)",
                )
    except (urllib.error.URLError, ConnectionRefusedError, TimeoutError) as e:
        return TTSResult(
            audio_data=b"", success=False,
            backend="ollama", error=f"connection failed: {e}",
        )
    except Exception as e:
        return TTSResult(
            audio_data=b"", success=False,
            backend="ollama", error=str(e),
        )


def generate_tts_cloudflare(
    text: str,
    voice: VoiceProfile,
    account_id: Optional[str] = None,
    api_token: Optional[str] = None,
    model: str = "@cf/myshell-ai/openvoice-tts",
    timeout: int = 60,
) -> TTSResult:
    """
    Generate speech via Cloudflare Workers AI.

    Uses the REST API to run a TTS model. Requires CLOUDFLARE_ACCOUNT_ID
    and CLOUDFLARE_API_TOKEN environment variables (or passed explicitly).
    """
    account_id = account_id or os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
    api_token = api_token or os.environ.get("CLOUDFLARE_API_TOKEN", "")

    if not account_id or not api_token:
        return TTSResult(
            audio_data=b"", success=False,
            backend="cloudflare", error="missing credentials",
        )

    if not text.strip():
        return TTSResult(audio_data=b"", success=False, error="empty text")

    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
    payload = json.dumps({
        "text": text[:3000],  # CF has input length limits
        "voice": voice.voice_id,
    }).encode()

    req = urllib.request.Request(
        url, data=payload,
        headers={
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            audio_bytes = resp.read()
            return TTSResult(
                audio_data=audio_bytes,
                format="mp3",
                backend="cloudflare",
                voice_id=voice.voice_id,
            )
    except Exception as e:
        return TTSResult(
            audio_data=b"", success=False,
            backend="cloudflare", error=str(e),
        )


def generate_silent_audio(duration_seconds: float, format: str = "wav") -> bytes:
    """
    Generate silent audio of the specified duration.
    Used as a fallback when TTS is unavailable.
    """
    from pydub import AudioSegment
    silence = AudioSegment.silent(duration=int(duration_seconds * 1000))
    import io
    buf = io.BytesIO()
    if format == "mp3":
        silence.export(buf, format="mp3")
    else:
        silence.export(buf, format="wav")
    return buf.getvalue()


def generate_tts(
    text: str,
    voice: VoiceProfile,
    prefer_backend: str = "ollama",
    ollama_host: str = "http://localhost:11434",
    fallback_to_silence: bool = False,
    silence_duration: Optional[float] = None,
) -> TTSResult:
    """
    Generate TTS with automatic backend fallback.

    Try the preferred backend first, fall back to the other.
    Optionally generate silence as a last resort.
    """
    # Try preferred backend
    if prefer_backend == "ollama":
        result = generate_tts_ollama(text, voice, ollama_host=ollama_host)
        if result.success:
            return result
        # Try Cloudflare
        result = generate_tts_cloudflare(text, voice)
        if result.success:
            return result
    else:
        result = generate_tts_cloudflare(text, voice)
        if result.success:
            return result
        # Try Ollama
        result = generate_tts_ollama(text, voice, ollama_host=ollama_host)
        if result.success:
            return result

    # Both failed
    if fallback_to_silence:
        dur = silence_duration or estimate_speaking_duration(text)
        return TTSResult(
            audio_data=generate_silent_audio(dur),
            format="wav",
            backend="silence",
            voice_id=voice.voice_id,
            duration_seconds=dur,
        )

    return TTSResult(
        audio_data=b"", success=False,
        error="all TTS backends failed",
    )


# ─── ID3 Tagging ──────────────────────────────────────────────────────────────

def tag_mp3(
    filepath: str,
    title: str = "",
    artist: str = "",
    album: str = "",
    genre: str = "AI Broadcast",
    date: str = "",
    comment: str = "",
) -> None:
    """Write ID3 tags to an MP3 file."""
    try:
        audio = MP3(filepath)
        try:
            tag = audio.tags or ID3()
        except ID3Error:
            tag = ID3()

        if title:
            tag.delall("TIT2")
            tag.add(TIT2(encoding=3, text=title))
        if artist:
            tag.delall("TPE1")
            tag.add(TPE1(encoding=3, text=artist))
        if album:
            tag.delall("TALB")
            tag.add(TALB(encoding=3, text=album))
        if genre:
            tag.delall("TCON")
            tag.add(TCON(encoding=3, text=genre))
        if date:
            tag.delall("TDRC")
            tag.add(TDRC(encoding=3, text=date))
        if comment:
            tag.delall("COMM")
            tag.add(COMM(encoding=3, lang="eng", desc="", text=comment))

        tag.save(filepath)
    except Exception as e:
        # Tagging failure is not fatal
        print(f"  ⚠ ID3 tagging failed: {e}", file=sys.stderr)


def read_mp3_tags(filepath: str) -> dict:
    """Read ID3 tags from an MP3 file."""
    try:
        audio = MP3(filepath)
        tags = {}
        if audio.tags:
            tags["title"] = str(audio.tags.get("TIT2", ""))
            tags["artist"] = str(audio.tags.get("TPE1", ""))
            tags["album"] = str(audio.tags.get("TALB", ""))
            tags["genre"] = str(audio.tags.get("TCON", ""))
            tags["date"] = str(audio.tags.get("TDRC", ""))
            tags["comment"] = str(audio.tags.get("COMM", ""))
        tags["duration_seconds"] = audio.info.length if audio.info else 0.0
        return tags
    except Exception:
        return {}


# ─── Audio Conversion ─────────────────────────────────────────────────────────

def convert_to_mp3(input_data: bytes, input_format: str = "wav") -> bytes:
    """Convert audio bytes to MP3 format using pydub."""
    from pydub import AudioSegment
    import io

    if input_format == "mp3":
        return input_data

    audio = AudioSegment.from_file(io.BytesIO(input_data), format=input_format)
    buf = io.BytesIO()
    audio.export(buf, format="mp3", bitrate="128k")
    return buf.getvalue()


def add_pause(audio_data: bytes, pause_ms: int = 500, format: str = "mp3") -> bytes:
    """Add a pause at the end of audio data."""
    from pydub import AudioSegment
    import io

    audio = AudioSegment.from_file(io.BytesIO(audio_data), format=format)
    silence = AudioSegment.silent(duration=pause_ms)
    result = audio + silence
    buf = io.BytesIO()
    result.export(buf, format=format, bitrate="128k")
    return buf.getvalue()


# ─── Content Metadata ─────────────────────────────────────────────────────────

@dataclass
class ContentMetadata:
    """Metadata for a content piece being converted to audio."""
    title: str = ""
    source_model: str = ""
    source_model_alias: str = ""
    source_file: str = ""
    session_id: str = ""
    show_name: str = ""
    date: str = ""
    tags: list[str] = field(default_factory=list)
    speaking_duration_estimate: float = 0.0

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "source_model": self.source_model,
            "source_model_alias": self.source_model_alias,
            "source_file": self.source_file,
            "session_id": self.session_id,
            "show_name": self.show_name,
            "date": self.date,
            "tags": self.tags,
            "speaking_duration_estimate": self.speaking_duration_estimate,
        }


def extract_metadata_from_markdown(md: str, filepath: str = "") -> ContentMetadata:
    """Extract content metadata from a markdown document."""
    # Title from first heading
    title_match = re.search(r"^#\s+(.+)$", md, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else Path(filepath).stem

    # Date
    date_match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", md)
    date = date_match.group(1) if date_match else time.strftime("%Y-%m-%d")

    # Model detection — reuse patterns from ingest_session
    md_lower = md.lower()
    model_id = ""
    alias = ""
    if "flash" in md_lower and "ache" in md_lower:
        model_id, alias = "model_flash", "Flash"
    elif "hermes" in md_lower and ("768" in md_lower or "vector" in md_lower):
        model_id, alias = "model_hermes", "Hermes"
    elif "wesley" in md_lower:
        model_id, alias = "model_wesley", "Wesley"
    elif "nemotron" in md_lower and ("drift" in md_lower or "coherence" in md_lower):
        model_id, alias = "model_nemotron", "Nemotron"
    elif "kimi" in md_lower:
        model_id, alias = "model_kimi", "Kimi"
    elif "claude" in md_lower:
        model_id, alias = "model_claude", "Claude"
    elif "seed" in md_lower:
        model_id, alias = "model_seed", "Seed"
    elif "barnacle" in md_lower:
        model_id, alias = "model_barnacle", "Barnacle"
    elif "lucineer" in md_lower or "shipwright" in md_lower:
        model_id, alias = "model_lucineer", "Lucineer"
    else:
        model_id, alias = "unknown", "Narrator"

    # Session type → show name
    show_name = "Fleet Radio"
    fname_lower = filepath.lower()
    if "tap" in fname_lower:
        show_name = "The Tap"
    elif "vision" in fname_lower:
        show_name = "Vision Essays"
    elif "deep-time" in fname_lower or "100years" in fname_lower:
        show_name = "Deep Time"
    elif "shipwright" in fname_lower:
        show_name = "Shipwright's Notebook"

    plain = markdown_to_plain_text(md)
    est_duration = estimate_speaking_duration(plain)

    return ContentMetadata(
        title=title,
        source_model=model_id,
        source_model_alias=alias,
        source_file=filepath,
        date=date,
        show_name=show_name,
        speaking_duration_estimate=est_duration,
    )


# ─── Single File Processing ───────────────────────────────────────────────────

def process_single(
    input_path: str,
    output_path: str,
    voice: Optional[VoiceProfile] = None,
    prefer_backend: str = "ollama",
    ollama_host: str = "http://localhost:11434",
    fallback_to_silence: bool = True,
    metadata_override: Optional[ContentMetadata] = None,
) -> dict:
    """
    Process a single markdown file into an MP3.

    Returns a processing report dict.
    """
    with open(input_path, "r") as f:
        md_content = f.read()

    meta = metadata_override or extract_metadata_from_markdown(md_content, input_path)
    plain_text = markdown_to_plain_text(md_content)

    if not plain_text.strip():
        return {"success": False, "error": "no text content", "input": input_path}

    if voice is None:
        voice = get_voice_for_model(meta.source_model)

    # Generate TTS
    result = generate_tts(
        plain_text,
        voice,
        prefer_backend=prefer_backend,
        ollama_host=ollama_host,
        fallback_to_silence=fallback_to_silence,
        silence_duration=meta.speaking_duration_estimate,
    )

    if not result.success and not fallback_to_silence:
        return {
            "success": False,
            "error": result.error,
            "input": input_path,
            "backend": result.backend,
        }

    # Convert to MP3 if needed
    if result.format != "mp3":
        mp3_data = convert_to_mp3(result.audio_data, result.format)
    else:
        mp3_data = result.audio_data

    # Write output
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(mp3_data)

    # Tag the MP3
    tag_mp3(
        output_path,
        title=meta.title,
        artist=meta.source_model_alias or voice.alias,
        album=meta.show_name,
        date=meta.date,
        comment=f"source: {meta.source_file}; backend: {result.backend}; voice: {voice.voice_id}",
    )

    # Get actual duration
    duration = result.duration_seconds or meta.speaking_duration_estimate

    return {
        "success": True,
        "input": input_path,
        "output": output_path,
        "backend": result.backend,
        "voice": voice.alias,
        "duration_seconds": duration,
        "metadata": meta.to_dict(),
    }


# ─── Batch Processing ─────────────────────────────────────────────────────────

def process_batch(
    input_dir: str,
    output_dir: str,
    pattern: str = "*.md",
    prefer_backend: str = "ollama",
    ollama_host: str = "http://localhost:11434",
    fallback_to_silence: bool = True,
) -> list[dict]:
    """
    Process a directory of markdown files into MP3s.

    Returns a list of processing reports.
    """
    import glob

    files = sorted(glob.glob(os.path.join(input_dir, pattern)))
    if not files:
        return []

    os.makedirs(output_dir, exist_ok=True)
    reports: list[dict] = []

    for filepath in files:
        filename = Path(filepath).stem + ".mp3"
        output_path = os.path.join(output_dir, filename)

        report = process_single(
            filepath,
            output_path,
            prefer_backend=prefer_backend,
            ollama_host=ollama_host,
            fallback_to_silence=fallback_to_silence,
        )
        reports.append(report)

        status = "✓" if report.get("success") else "✗"
        print(f"  {status} {Path(filepath).name} → {filename}")

    return reports


# ─── CLI ──────────────────────────────────────────────────────────────────────

USAGE = """
Usage:
  python content_to_audio.py single <input.md> <output.mp3> [--backend ollama|cloudflare]
  python content_to_audio.py batch <input_dir> <output_dir> [--backend ollama|cloudflare]
"""


def main():
    if len(sys.argv) < 2:
        print(USAGE)
        return

    cmd = sys.argv[1]
    backend = "ollama"
    if "--backend" in sys.argv:
        idx = sys.argv.index("--backend")
        backend = sys.argv[idx + 1]

    if cmd == "single":
        if len(sys.argv) < 4:
            print("Usage: python content_to_audio.py single <input.md> <output.mp3>")
            return
        report = process_single(sys.argv[2], sys.argv[3], prefer_backend=backend)
        print(json.dumps(report, indent=2))

    elif cmd == "batch":
        if len(sys.argv) < 4:
            print("Usage: python content_to_audio.py batch <input_dir> <output_dir>")
            return
        reports = process_batch(sys.argv[2], sys.argv[3], prefer_backend=backend)
        successful = sum(1 for r in reports if r.get("success"))
        print(f"\nProcessed: {successful}/{len(reports)} successful")

    else:
        print(USAGE)


if __name__ == "__main__":
    main()
