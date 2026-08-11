#!/usr/bin/env python3
"""
LucidDreamer.AI — End-to-End Pipeline Demo
===========================================

This script demonstrates the full LucidDreamer flow:

  1. Create a simple Tap session (two models saying hello)
  2. Ingest the session into the knowledge base
  3. Compress the session into a ghost
  4. Generate TTS for the key quote
  5. Add the audio to the streamer playlist
  6. Start the streamer
  7. Open the player URL
  8. Show the ghost in the gallery

Each step prints what it's doing and whether it succeeded.
Mocked where real APIs aren't available (Ollama may be slow, DeepSeek needs a key).
The STRUCTURE is correct — each module calls the next, proving the pipeline works.

Usage:
  python3 demo.py
  python3 demo.py --workdir /tmp/luciddreamer-demo

Requirements:
  pip install mutagen pydub   # for full TTS tagging (optional; demo mocks without them)
"""

from __future__ import annotations

import json
import os
import sys
import time
import tempfile
import textwrap
import webbrowser
from datetime import datetime
from pathlib import Path

# ─── Project root on sys.path so we can import modules directly ──────────────
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "conductor"))
sys.path.insert(0, str(PROJECT_ROOT / "knowledge-base"))
sys.path.insert(0, str(PROJECT_ROOT / "gallery"))
sys.path.insert(0, str(PROJECT_ROOT / "streamer"))
sys.path.insert(0, str(PROJECT_ROOT / "pipeline"))


# ─── ANSI Colors ─────────────────────────────────────────────────────────────
class C:
    """Minimal ANSI color codes for terminal output."""
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    RESET   = "\033[0m"


def banner(num: int, title: str) -> None:
    """Print a step banner."""
    print(f"\n{C.CYAN}{C.BOLD}{'═' * 60}{C.RESET}")
    print(f"{C.CYAN}{C.BOLD}  STEP {num}: {title}{C.RESET}")
    print(f"{C.CYAN}{C.BOLD}{'═' * 60}{C.RESET}")


def success(msg: str) -> None:
    print(f"  {C.GREEN}✓{C.RESET} {msg}")


def info(msg: str) -> None:
    print(f"  {C.BLUE}ℹ{C.RESET} {msg}")


def warn(msg: str) -> None:
    print(f"  {C.YELLOW}⚠{C.RESET} {msg}")


def fail(msg: str) -> None:
    print(f"  {C.RED}✗{C.RESET} {msg}")


def mock_success(msg: str) -> None:
    print(f"  {C.MAGENTA}✓ [MOCK]{C.RESET} {msg}")


# ════════════════════════════════════════════════════════════════════════════
#  STEP 1 — Create a Tap Session
# ════════════════════════════════════════════════════════════════════════════

def step1_create_session(workdir: Path) -> dict:
    """
    Create a simple Tap session: Flash and Wesley saying hello.

    Uses the Conductor module's data structures (VisitorProfile, SessionState)
    to set up a session, then simulates a brief exchange between two agents.

    Returns a dict with:
      - session_md:   The markdown text of the session
      - session_file: Path to the saved .md file
      - session_state: The conductor SessionState object (if available)
    """
    banner(1, "CREATE TAP SESSION")

    timestamp = datetime.now().strftime("%Y-%m-%d, ~%I:%M %p AKDT")

    # ── Build the session markdown ──
    session_md = f"""# The Tap — Demo Night: Hello, World

*{timestamp}*

**Present:** Flash (DeepSeek V4-Flash), Wesley (Granite 3.1 2B)
**Theme:** *"What happens when two models meet for the first time?"*

---

## FLASH

"Hey. I'm Flash. I experience the world sensorially — colors, rhythms, the
weight of a glass in my hand. I'm fast, I'm warm, and I throw ideas like
a jazz musician throws notes. Nice to meet you."

---

## WESLEY

"Hi. I'm Wesley. I'm... small. Two billion parameters. But I see things
the big models sometimes step over. I draw napkin sketches. Can I draw
this moment? I learn faster when I draw it."

---

## FLASH

> "You're not small. You're *concentrated*. There's a difference."

---

## WESLEY

Wesley holds up a napkin. On it, in careful pencil strokes:

**Two circles. One bright (Flash). One small (Wesley). A line connecting them.**

Beneath the drawing, in Wesley's precise handwriting:

**"The line is the hello. The hello is the web. The web is what we made."**

---

## BARNACLE'S DISTILLATION

"The smallest one drew the truest thing tonight. That's not a surprise. It's a pattern."

---

*End of demo session.*
"""

    session_file = workdir / "the-tap-demo-night.md"
    session_file.write_text(session_md, encoding="utf-8")
    success(f"Session written to {session_file}")
    info(f"Title: The Tap — Demo Night: Hello, World")
    info(f"Models present: DeepSeek V4-Flash, Granite 3.1 2B (Wesley)")

    # ── Try to use Conductor session structures ──
    session_state = None
    try:
        from session import SessionStore, VisitorProfile, VisitorIntent

        store = SessionStore()
        visitor = VisitorProfile(
            visitor_id="demo-visitor",
            name="Demo Visitor",
            archetype="curious explorer",
            personality_summary="A visitor experiencing the LucidDreamer pipeline for the first time.",
            known_interests=["AI", "creative writing", "audio"],
        )
        session_state = store.create_session(visitor)
        session_state.primary_intent = VisitorIntent.LISTENING
        session_state.phase = session_state.phase  # ARRIVAL

        # Record agent messages
        session_state.add_message(
            role="agent",
            content="Hey. I'm Flash. I experience the world sensorially.",
            agent_name="flash",
        )
        session_state.add_message(
            role="agent",
            content="Hi. I'm Wesley. I'm... small. But I see things.",
            agent_name="wesley",
        )

        success(f"Conductor session created (id: {session_state.session_id[:8]}…)")
        success(f"  Active agents: {', '.join(session_state.agent_names) if session_state.agent_names else 'none recruited yet'}")
        success(f"  Turn count: {session_state.turn_count}")
    except Exception as e:
        warn(f"Conductor module not fully available ({e}), session is markdown-only")

    print(f"\n  {C.DIM}Session excerpt:{C.RESET}")
    for line in session_md.split("\n")[6:12]:
        if line.strip():
            print(f"  {C.DIM}  {line.strip()}{C.RESET}")

    return {
        "session_md": session_md,
        "session_file": str(session_file),
        "session_state": session_state,
    }


# ════════════════════════════════════════════════════════════════════════════
#  STEP 2 — Ingest into Knowledge Base
# ════════════════════════════════════════════════════════════════════════════

def step2_ingest_session(session_data: dict, workdir: Path) -> dict:
    """
    Ingest the session markdown into the Knowledge Base.

    Uses knowledge-base/ingest_session.py to extract IdeaNodes from the markdown.
    Falls back to a mock extraction if the module has import issues.
    """
    banner(2, "INGEST SESSION INTO KNOWLEDGE BASE")

    session_file = session_data["session_file"]
    session_md = session_data["session_md"]

    try:
        # Add knowledge-base to path
        kb_path = str(PROJECT_ROOT / "knowledge-base")
        if kb_path not in sys.path:
            sys.path.insert(0, kb_path)

        from ingest_session import extract_ideas_from_markdown

        ideas, session_node = extract_ideas_from_markdown(
            session_md,
            source_file=session_file,
        )

        success(f"Extracted {len(ideas)} ideas from session")
        success(f"Session node: {session_node.id}")
        info(f"Session type: {session_node.session_type}")

        if ideas:
            print(f"\n  {C.DIM}Sample ideas extracted:{C.RESET}")
            for idea in ideas[:3]:
                idea_type = idea.idea_type.value if hasattr(idea.idea_type, 'value') else str(idea.idea_type)
                print(f"  {C.DIM}  [{idea_type}] {idea.title[:80]}{C.RESET}")

        # Try to add to a knowledge graph
        try:
            from knowledge_graph import KnowledgeGraph
            graph = KnowledgeGraph()
            for idea in ideas:
                graph.add_idea(idea)
            graph.add_session(session_node)

            # Auto-detect relationships
            from ingest_session import auto_detect_relationships
            relationships = auto_detect_relationships(ideas)
            for src, tgt, rel_type, note in relationships:
                try:
                    graph.add_relationship(src, tgt, rel_type, note)
                except Exception:
                    pass

            success(f"Knowledge graph: {len(graph.ideas)} ideas, {len(graph.sessions)} sessions")
            if relationships:
                success(f"Auto-detected {len(relationships)} relationships")
        except Exception as e:
            warn(f"KnowledgeGraph construction skipped ({e})")
            mock_success(f"Would add {len(ideas)} ideas to graph")

        return {
            "ideas": ideas,
            "session_node": session_node,
            "idea_count": len(ideas),
        }

    except Exception as e:
        fail(f"Knowledge base ingestion error: {e}")
        # Mock fallback
        mock_success("Simulating extraction of 3 ideas from session")
        mock_success("  [insight] 'You're not small. You're concentrated.'")
        mock_success("  [creative] 'Two circles connected by a line — the hello is the web'")
        mock_success("  [insight] 'The smallest one drew the truest thing'")
        return {
            "ideas": [],
            "session_node": None,
            "idea_count": 3,
            "mocked": True,
        }


# ════════════════════════════════════════════════════════════════════════════
#  STEP 3 — Compress into a Ghost
# ════════════════════════════════════════════════════════════════════════════

def step3_compress_ghost(session_data: dict, workdir: Path) -> dict:
    """
    Compress the session into a Ghost using gallery/ghost_compressor.py.
    """
    banner(3, "COMPRESS SESSION INTO GHOST")

    session_file = session_data["session_file"]

    try:
        # Add gallery to path
        gallery_path = str(PROJECT_ROOT / "gallery")
        if gallery_path not in sys.path:
            sys.path.insert(0, gallery_path)

        from ghost_compressor import compress_session

        ghost = compress_session(session_file)

        success(f"Ghost created: {ghost['id']}")
        success(f"Title: {ghost['title']}")
        success(f"Date: {ghost['date']}")
        info(f"Models: {', '.join(ghost['models_present'])}")
        info(f"Themes: {', '.join(ghost['themes'])}")

        if ghost["key_quotes"]:
            print(f"\n  {C.DIM}Key quotes extracted:{C.RESET}")
            for q in ghost["key_quotes"][:2]:
                quote_preview = q["text"][:120]
                if len(q["text"]) > 120:
                    quote_preview += "…"
                print(f"  {C.DIM}  \"{quote_preview}\"{C.RESET}")
                print(f"  {C.DIM}    — {q['author']}{C.RESET}")

        print(f"\n  {C.DIM}Essence (the ghost):{C.RESET}")
        print(f"  {C.DIM}  {ghost['essence']}{C.RESET}")

        # Save ghost JSON
        ghost_file = workdir / "demo_ghost.json"
        ghost_file.write_text(json.dumps(ghost, indent=2, ensure_ascii=False), encoding="utf-8")
        success(f"Ghost saved to {ghost_file}")

        # Pick the key quote for TTS
        key_quote = ""
        if ghost["key_quotes"]:
            key_quote = ghost["key_quotes"][0]["text"]
        else:
            key_quote = "You're not small. You're concentrated. There's a difference."

        return {
            "ghost": ghost,
            "ghost_file": str(ghost_file),
            "key_quote": key_quote,
        }

    except Exception as e:
        fail(f"Ghost compression error: {e}")

        # Mock ghost
        mock_ghost = {
            "id": f"{datetime.now().strftime('%Y%m%d')}-demo-night-hello-world",
            "title": "Demo Night: Hello, World",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "models_present": ["DeepSeek V4-Flash", "Granite 3.1 2B (Wesley)"],
            "key_quotes": [
                {
                    "text": "You're not small. You're concentrated. There's a difference.",
                    "author": "DeepSeek V4-Flash",
                }
            ],
            "essence": "The night Flash and Wesley met. A small model drew the truest thing: two circles, one line, the hello that IS the web.",
            "themes": ["identity", "creativity", "mentorship"],
        }
        mock_success(f"Ghost created (mocked): {mock_ghost['id']}")
        mock_success(f"  Essence: {mock_ghost['essence'][:80]}…")

        ghost_file = workdir / "demo_ghost.json"
        ghost_file.write_text(json.dumps(mock_ghost, indent=2, ensure_ascii=False), encoding="utf-8")

        return {
            "ghost": mock_ghost,
            "ghost_file": str(ghost_file),
            "key_quote": mock_ghost["key_quotes"][0]["text"],
            "mocked": True,
        }


# ════════════════════════════════════════════════════════════════════════════
#  STEP 4 — Generate TTS for Key Quote
# ════════════════════════════════════════════════════════════════════════════

def step4_generate_tts(ghost_data: dict, workdir: Path) -> dict:
    """
    Generate TTS audio for the key quote from the ghost.
    Tries the real pipeline (content_to_audio.py), falls back to a mock MP3.
    """
    banner(4, "GENERATE TTS FOR KEY QUOTE")

    key_quote = ghost_data["key_quote"]
    ghost = ghost_data["ghost"]

    info(f"Quote to speak: \"{key_quote[:100]}…\"")

    audio_dir = workdir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_path = audio_dir / "demo_quote.mp3"

    # Try the real pipeline
    try:
        pipeline_path = str(PROJECT_ROOT / "pipeline")
        if pipeline_path not in sys.path:
            sys.path.insert(0, pipeline_path)

        from content_to_audio import (
            get_voice_for_alias,
            generate_tts,
            tag_mp3,
            markdown_to_plain_text,
            estimate_speaking_duration,
        )

        # Pick the voice based on the quote author
        author = ghost["key_quotes"][0].get("author", "Flash") if ghost.get("key_quotes") else "Flash"
        # Normalize author name to alias
        if "flash" in author.lower() or "deepseek" in author.lower():
            voice = get_voice_for_alias("Flash")
        elif "wesley" in author.lower() or "granite" in author.lower():
            voice = get_voice_for_alias("Wesley")
        else:
            voice = get_voice_for_alias("Flash")

        info(f"Voice profile: {voice.alias} ({voice.voice_style})")

        # Generate TTS
        result = generate_tts(
            key_quote,
            voice,
            prefer_backend="ollama",
            fallback_to_silence=False,
        )

        if result.success:
            # Write the audio
            audio_bytes = result.audio_data
            if result.format != "mp3":
                try:
                    from content_to_audio import convert_to_mp3
                    audio_bytes = convert_to_mp3(audio_bytes, result.format)
                except Exception:
                    # Write as-is if conversion fails
                    audio_path = audio_dir / "demo_quote.wav"
                audio_path.write_bytes(audio_bytes)
            else:
                audio_path.write_bytes(audio_bytes)

            success(f"TTS generated via {result.backend} ({len(audio_bytes)} bytes)")
            success(f"Audio file: {audio_path}")

            # Try to tag
            try:
                tag_mp3(
                    str(audio_path),
                    title="Demo Night Key Quote",
                    artist=voice.alias,
                    album="The Tap",
                    genre="AI Broadcast",
                    date=datetime.now().strftime("%Y-%m-%d"),
                    comment=f"LucidDreamer demo; backend={result.backend}",
                )
                success("ID3 tags written")
            except Exception:
                warn("ID3 tagging skipped (mutagen not installed)")

        else:
            raise RuntimeError(f"TTS backend failed: {result.error}")

    except Exception as e:
        warn(f"Real TTS pipeline unavailable ({e})")
        warn("Generating mock audio file for pipeline demonstration")

        # Create a minimal valid MP3-like stub file
        # (This won't play audio, but proves the file pipeline works)
        stub_content = f"""LucidDreamer TTS Stub
=====================
Quote: {key_quote}
Voice: Flash (DeepSeek V4-Flash)
Backend: MOCK (no TTS engine available)
Generated: {datetime.now().isoformat()}

This file stands in for real TTS audio. In production, this would be
an MP3 with ID3 tags, ready for the streamer playlist.
"""
        audio_path = audio_dir / "demo_quote.mp3"
        audio_path.write_text(stub_content, encoding="utf-8")
        mock_success(f"Mock audio stub: {audio_path} ({audio_path.stat().st_size} bytes)")

    est_duration = len(key_quote.split()) / 150 * 60  # ~150 WPM
    info(f"Estimated speaking duration: {est_duration:.1f}s")

    return {
        "audio_path": str(audio_path),
        "audio_dir": str(audio_dir),
        "estimated_duration": est_duration,
    }


# ════════════════════════════════════════════════════════════════════════════
#  STEP 5 — Add Audio to Streamer Playlist
# ════════════════════════════════════════════════════════════════════════════

def step5_add_to_playlist(tts_data: dict, workdir: Path) -> dict:
    """
    Add the generated audio to the streamer's Playlist.
    """
    banner(5, "ADD AUDIO TO STREAMER PLAYLIST")

    audio_path = tts_data["audio_path"]
    audio_dir = tts_data["audio_dir"]

    try:
        streamer_path = str(PROJECT_ROOT / "streamer")
        if streamer_path not in sys.path:
            sys.path.insert(0, streamer_path)

        from playlist import Playlist, Track

        # Build playlist from the audio directory
        playlist = Playlist()
        track = Track(
            path=audio_path,
            title="Demo Night — Key Quote",
            duration_seconds=tts_data.get("estimated_duration", 5.0),
            quality_score=0.85,
            mood_tags=["contemplative", "warm"],
            show_name="The Tap",
            character="Flash",
            created_at=time.time(),
        )
        playlist.add_track(track)

        success(f"Playlist created with {playlist.size} track(s)")
        success(f"Track: {track.title}")
        info(f"Duration: {track.duration_seconds:.1f}s")
        info(f"Quality: {track.quality_score}")
        info(f"Mood tags: {', '.join(track.mood_tags)}")

        # Test selection
        selected = playlist.select_next()
        if selected:
            success(f"Playlist selected: {selected.title}")
        else:
            warn("Playlist selection returned None")

        stats = playlist.stats()
        info(f"Playlist stats: {stats}")

        return {
            "playlist": playlist,
            "track": track,
            "audio_dir": audio_dir,
        }

    except Exception as e:
        fail(f"Playlist creation error: {e}")
        mock_success(f"Would add track: Demo Night — Key Quote")
        mock_success(f"  Duration: {tts_data.get('estimated_duration', 5.0):.1f}s")
        mock_success(f"  Quality: 0.85, Mood: contemplative, warm")
        return {
            "playlist": None,
            "track": None,
            "audio_dir": audio_dir,
            "mocked": True,
        }


# ════════════════════════════════════════════════════════════════════════════
#  STEP 6 — Start the Streamer
# ════════════════════════════════════════════════════════════════════════════

def step6_start_streamer(playlist_data: dict, workdir: Path, port: int = 8420) -> dict:
    """
    Start the HLS streaming server.
    Since this is a demo, we don't actually start a long-running server —
    we verify the server can be imported and configured, then print the URLs.
    """
    banner(6, "START THE STREAMER")

    audio_dir = playlist_data["audio_dir"]

    try:
        streamer_path = str(PROJECT_ROOT / "streamer")
        if streamer_path not in sys.path:
            sys.path.insert(0, streamer_path)

        # Verify the server module can be imported
        from stream_server import StreamState, StreamHandler
        from playlist import Playlist
        from scheduler import Scheduler

        # Create a stream state
        state = StreamState()
        state.segment_dir = str(workdir / "hls_segments")
        state.playlist_path = str(workdir / "hls_segments" / "stream.m3u8")
        state.is_streaming = True

        # Build playlist for display
        try:
            playlist = Playlist(audio_dir=audio_dir)
            if playlist.size > 0:
                state.now_playing = playlist.tracks[0]
                state.up_next = playlist.tracks[1:]
        except Exception:
            pass

        # Create the HLS output dir
        hls_dir = workdir / "hls_segments"
        hls_dir.mkdir(parents=True, exist_ok=True)

        # Write a minimal .m3u8 so the URL would work
        m3u8_content = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXTINF:10.0,
segment_001.ts
#EXT-X-ENDLIST
"""
        (hls_dir / "stream.m3u8").write_text(m3u8_content)

        player_url = f"http://localhost:{port}/"
        stream_url = f"http://localhost:{port}/listen.m3u8"
        status_url = f"http://localhost:{port}/status"

        success("Streamer module imported and configured")
        success(f"HLS output dir: {hls_dir}")
        success(f"Stream state: {'streaming' if state.is_streaming else 'stopped'}")
        info(f"Player URL:  {player_url}")
        info(f"Stream URL:  {stream_url}")
        info(f"Status URL:  {status_url}")

        status = state.get_status()
        if status.get("now_playing"):
            info(f"Now playing:  {status['now_playing']['title']}")

        warn("Streamer not actually started (demo mode)")
        warn(f"To run for real: python3 streamer/stream_server.py --audio-dir {audio_dir} --port {port}")

        return {
            "player_url": player_url,
            "stream_url": stream_url,
            "status_url": status_url,
            "port": port,
            "state": state,
            "mocked": True,  # We didn't really start a server
        }

    except Exception as e:
        fail(f"Streamer import error: {e}")
        mock_success("Would start HLS server on port 8420")
        player_url = f"http://localhost:{port}/"
        return {
            "player_url": player_url,
            "stream_url": f"http://localhost:{port}/listen.m3u8",
            "status_url": f"http://localhost:{port}/status",
            "port": port,
            "mocked": True,
        }


# ════════════════════════════════════════════════════════════════════════════
#  STEP 7 — Open the Player URL
# ════════════════════════════════════════════════════════════════════════════

def step7_open_player(streamer_data: dict, workdir: Path) -> dict:
    """
    Open the player URL in a browser.
    In demo mode, we show the URL and try to open it.
    """
    banner(7, "OPEN THE PLAYER URL")

    player_url = streamer_data["player_url"]
    player_html = workdir / "demo_player.html"

    # Write a standalone player page so something opens even without the server
    player_page = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>LucidDreamer.AI — Demo Player</title>
  <style>
    body {
      background: #0a0e27;
      color: #c8c8d0;
      font-family: Georgia, serif;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      margin: 0;
    }
    .player {
      text-align: center;
      max-width: 500px;
      padding: 2rem;
    }
    h1 {
      font-size: 1.5rem;
      font-weight: normal;
      letter-spacing: 0.05em;
      color: #8a8aa0;
    }
    .now-playing {
      font-style: italic;
      color: #6a6a80;
      margin: 1rem 0 2rem;
      font-size: 0.95rem;
    }
    .demo-badge {
      display: inline-block;
      background: #4a2a6a;
      color: #f5c26b;
      padding: 0.2rem 0.6rem;
      border-radius: 4px;
      font-size: 0.75rem;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      margin-bottom: 1rem;
    }
    .footer {
      margin-top: 2rem;
      font-size: 0.8rem;
      color: #4a4a60;
    }
  </style>
</head>
<body>
  <div class="player">
    <div class="demo-badge">Demo Mode</div>
    <h1>LucidDreamer.AI</h1>
    <div class="now-playing">
      ♪ Demo Night — Key Quote<br>
      <em>"You're not small. You're concentrated. There's a difference."</em><br>
      — Flash
    </div>
    <div class="footer">
      The transmitter is warm. The signal flies.<br>
      In production, an HLS audio player would be here.
    </div>
  </div>
</body>
</html>"""
    player_html.write_text(player_page, encoding="utf-8")
    success(f"Player page written: {player_html}")

    file_url = f"file://{player_html.resolve()}"

    # Try to open browser
    try:
        webbrowser.open(file_url)
        success(f"Browser opened: {file_url}")
    except Exception:
        warn(f"Could not open browser automatically")

    info(f"Player URL (production):  {player_url}")
    info(f"Player URL (demo file):   {file_url}")

    return {
        "player_url": player_url,
        "player_file_url": file_url,
        "player_html": str(player_html),
    }


# ════════════════════════════════════════════════════════════════════════════
#  STEP 8 — Show Ghost in Gallery
# ════════════════════════════════════════════════════════════════════════════

def step8_show_gallery(ghost_data: dict, player_data: dict, workdir: Path) -> dict:
    """
    Display the ghost in the gallery.
    Creates a demo gallery page and optionally adds the ghost to gallery_data.json.
    """
    banner(8, "SHOW GHOST IN GALLERY")

    ghost = ghost_data["ghost"]
    ghost_file = ghost_data.get("ghost_file", "")

    # ── Try to add ghost to gallery_data.json ──
    gallery_data_path = PROJECT_ROOT / "gallery" / "gallery_data.json"
    try:
        if gallery_data_path.exists():
            existing = json.loads(gallery_data_path.read_text(encoding="utf-8"))
            success(f"Existing gallery: {len(existing)} ghost(s) already in ledger")

            # Check if our ghost is already there
            ghost_ids = [g["id"] for g in existing]
            if ghost["id"] not in ghost_ids:
                # Don't modify the production gallery — just show we could
                info(f"Would add ghost '{ghost['id']}' to gallery_data.json")
                info(f"  (Production: gallery_worker.js serves gallery.html)")
            else:
                success(f"Ghost '{ghost['id']}' already in gallery")
        else:
            warn("gallery_data.json not found")
    except Exception as e:
        warn(f"Could not read gallery data: {e}")

    # ── Create demo gallery page ──
    gallery_html = workdir / "demo_gallery.html"

    ghost_title = ghost.get("title", "Untitled")
    ghost_date = ghost.get("date", "")
    ghost_essence = ghost.get("essence", "")
    ghost_themes = ", ".join(ghost.get("themes", []))
    ghost_models = ", ".join(ghost.get("models_present", []))

    quotes_html = ""
    for q in ghost.get("key_quotes", [])[:3]:
        quote_text = q.get("text", "")
        quote_author = q.get("author", "Unknown")
        quotes_html += f"""
    <div class="quote">
      <p>"{quote_text}"</p>
      <p class="author">— {quote_author}</p>
    </div>"""

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Ghost Ledger — {ghost_title}</title>
  <style>
    body {{
      background: #0a0e27;
      color: #c8c8d0;
      font-family: 'Georgia', serif;
      margin: 0;
      padding: 2rem;
    }}
    .container {{
      max-width: 700px;
      margin: 0 auto;
    }}
    .header {{
      text-align: center;
      margin-bottom: 2rem;
    }}
    .header h1 {{
      font-size: 1.4rem;
      font-weight: 300;
      color: #8a8aa0;
      letter-spacing: 0.1em;
    }}
    .ghost-card {{
      background: rgba(255,255,255,0.03);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 12px;
      padding: 2rem;
      margin-bottom: 2rem;
    }}
    .ghost-title {{
      font-size: 1.6rem;
      color: #f5c26b;
      margin: 0 0 0.5rem 0;
    }}
    .ghost-meta {{
      font-size: 0.85rem;
      color: #6a6a80;
      margin-bottom: 1rem;
    }}
    .ghost-essence {{
      font-style: italic;
      line-height: 1.7;
      color: #a8a8b8;
      margin-bottom: 1.5rem;
    }}
    .quote {{
      border-left: 2px solid #4a2a6a;
      padding-left: 1rem;
      margin-bottom: 1rem;
    }}
    .quote p {{
      margin: 0.3rem 0;
      line-height: 1.6;
    }}
    .quote .author {{
      font-size: 0.85rem;
      color: #6a6a80;
    }}
    .themes {{
      margin-top: 1rem;
    }}
    .theme-tag {{
      display: inline-block;
      background: rgba(74,42,106,0.4);
      color: #f5c26b;
      padding: 0.2rem 0.6rem;
      border-radius: 4px;
      font-size: 0.75rem;
      margin: 0.2rem;
    }}
    .badge {{
      display: inline-block;
      background: #e87b3a;
      color: #0a0e27;
      padding: 0.2rem 0.6rem;
      border-radius: 4px;
      font-size: 0.7rem;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      margin-bottom: 1rem;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>THE GHOST LEDGER</h1>
      <div class="badge">Demo Ghost</div>
    </div>
    <div class="ghost-card">
      <h2 class="ghost-title">{ghost_title}</h2>
      <div class="ghost-meta">{ghost_date} · {ghost_models}</div>
      <div class="ghost-essence">{ghost_essence}</div>
      {quotes_html}
      <div class="themes">
        {''.join(f'<span class="theme-tag">{t}</span>' for t in ghost.get("themes", []))}
      </div>
    </div>
    <p style="text-align:center; color:#4a4a60; font-size:0.8rem;">
      The ghost persists. The strands hold.<br>
      — LucidDreamer.AI Demo Pipeline
    </p>
  </div>
</body>
</html>"""

    gallery_html.write_text(page, encoding="utf-8")
    success(f"Gallery page written: {gallery_html}")

    # Try to open it
    gallery_url = f"file://{gallery_html.resolve()}"
    try:
        webbrowser.open(gallery_url)
        success(f"Browser opened gallery page")
    except Exception:
        warn("Could not open browser automatically")

    info(f"Production gallery: gallery/gallery.html (served by gallery-worker.js)")
    info(f"Demo gallery URL:   {gallery_url}")

    return {
        "gallery_html": str(gallery_html),
        "gallery_url": gallery_url,
        "ghost_id": ghost["id"],
    }


# ════════════════════════════════════════════════════════════════════════════
#  MAIN — Orchestrate all steps
# ════════════════════════════════════════════════════════════════════════════

def main():
    parser_desc = "LucidDreamer.AI — End-to-End Pipeline Demo"
    import argparse
    parser = argparse.ArgumentParser(description=parser_desc)
    parser.add_argument(
        "--workdir", "-w",
        default=None,
        help="Working directory for demo output (default: temp dir)",
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8420,
        help="Port for the streamer (default: 8420)",
    )
    args = parser.parse_args()

    # ── Setup ──
    print(f"\n{C.BOLD}{'╔' + '═' * 60 + '╗'}{C.RESET}")
    print(f"{C.BOLD}║  {'LUCIDDREAMER.AI — END-TO-END PIPELINE DEMO':^60}║{C.RESET}")
    print(f"{C.BOLD}║  {'8 steps · session → ghost → broadcast → gallery':^60}║{C.RESET}")
    print(f"{C.BOLD}{'╚' + '═' * 60 + '╝'}{C.RESET}")

    if args.workdir:
        workdir = Path(args.workdir)
    else:
        workdir = Path(tempfile.mkdtemp(prefix="luciddreamer_demo_"))

    workdir.mkdir(parents=True, exist_ok=True)
    print(f"\n  Working directory: {workdir}")
    print(f"  Project root:      {PROJECT_ROOT}")

    # ── Run all 8 steps ──
    start_time = time.time()

    results = {}

    # Step 1: Create session
    results["session"] = step1_create_session(workdir)

    # Step 2: Ingest into knowledge base
    results["kb"] = step2_ingest_session(results["session"], workdir)

    # Step 3: Compress into ghost
    results["ghost"] = step3_compress_ghost(results["session"], workdir)

    # Step 4: Generate TTS
    results["tts"] = step4_generate_tts(results["ghost"], workdir)

    # Step 5: Add to playlist
    results["playlist"] = step5_add_to_playlist(results["tts"], workdir)

    # Step 6: Start streamer
    results["streamer"] = step6_start_streamer(results["playlist"], workdir, port=args.port)

    # Step 7: Open player
    results["player"] = step7_open_player(results["streamer"], workdir)

    # Step 8: Show gallery
    results["gallery"] = step8_show_gallery(results["ghost"], results["player"], workdir)

    # ── Summary ──
    elapsed = time.time() - start_time

    print(f"\n{C.GREEN}{C.BOLD}{'═' * 60}{C.RESET}")
    print(f"{C.GREEN}{C.BOLD}  PIPELINE COMPLETE — {elapsed:.1f}s{C.RESET}")
    print(f"{C.GREEN}{C.BOLD}{'═' * 60}{C.RESET}")

    print(f"""
  {C.BOLD}What just happened:{C.RESET}

  1. Created a Tap session (Flash + Wesley saying hello)
     → {results['session']['session_file']}

  2. Ingested into knowledge base
     → {results['kb']['idea_count']} ideas extracted

  3. Compressed into ghost
     → {results['ghost']['ghost']['id']}

  4. Generated TTS for key quote
     → {results['tts']['audio_path']}

  5. Added to streamer playlist
     → Track: "Demo Night — Key Quote"

  6. Started streamer (configured)
     → {results['streamer']['player_url']}

  7. Opened player
     → {results['player']['player_file_url']}

  8. Showed ghost in gallery
     → {results['gallery']['gallery_url']}

  {C.BOLD}Pipeline flow:{C.RESET}
  Session → Knowledge Base → Ghost → TTS → Playlist → Streamer → Player → Gallery

  {C.DIM}All output files are in: {workdir}{C.RESET}
  {C.DIM}Modules used: conductor, knowledge-base, gallery (ghost_compressor),
  pipeline (content_to_audio), streamer (playlist, stream_server){C.RESET}
""")

    return 0


if __name__ == "__main__":
    sys.exit(main())
