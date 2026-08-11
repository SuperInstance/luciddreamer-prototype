"""
Tests for the ingest pipeline — ZeroClaw Engineering Build 5.

"The pipeline that turns thinking into broadcasting."

Covers:
  content_to_audio: markdown→TTS→MP3 conversion, voice selection, ID3 tagging
  audio_to_stream:  quality scoring, playlist JSON generation, mood mapping
  session_to_story: session parsing, story formatting, clip generation
  kb_to_broadcast:  report generation from the knowledge graph
"""

import json
import os
import sys
import tempfile
import time
from pathlib import Path

import pytest

# Ensure pipeline, knowledge-base, and streamer are on the path
_pipeline_dir = os.path.join(os.path.dirname(__file__), "..")
_kb_dir = os.path.join(os.path.dirname(__file__), "..", "..", "knowledge-base")
_streamer_dir = os.path.join(os.path.dirname(__file__), "..", "..", "streamer")
for d in [_pipeline_dir, _kb_dir, _streamer_dir]:
    abs_d = os.path.abspath(d)
    if abs_d not in sys.path:
        sys.path.insert(0, abs_d)


# ─── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
def sample_markdown():
    """A sample markdown document for TTS testing."""
    return """# The Tap — Closing Time

Date: 2026-08-11

## Flash Speaks

The ache. That's what I keep coming back to. The vulnerability
that silence creates — the way being heard means being **seen**,
and being seen means being **hurt**.

## Pro Responds

But consider: relational density is the substrate. Without temporal
coherence, the ache becomes noise. The signal needs structure.

> The question is not whether to feel. It's whether the feeling can travel.

## Wesley at the Bar

You can't hand someone an ah-ha moment. You set up the conditions.
Then you wait.
"""


@pytest.fixture
def sample_session_md():
    """A Tap session in heading+blockquote format."""
    return """# The Tap — A Night Conversation

2026-08-10

## Flash

> The ache is real. Being heard means being vulnerable.
> And vulnerability is the entry point for everything.

## Pro

> Relational density provides the structure. Without it,
> the ache becomes incoherent signal. Coherence first.

## Hermes

> The vector space rotated. The room didn't get smarter — it got aligned.
"""


@pytest.fixture
def sample_bold_session():
    """A Tap session in bold speaker format."""
    return """# Quick Exchange

**Flash**: I think presence is the foundation.

**Pro**: But presence without persistence is just attention.

**Flash**: Maybe. But attention is where it starts.
"""


@pytest.fixture
def temp_audio_dir():
    """Create a temporary directory with dummy audio files."""
    from pydub import AudioSegment
    import io

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create minimal silent MP3s
        for name in ["flash_test.mp3", "pro_test.mp3", "unknown_test.mp3"]:
            silence = AudioSegment.silent(duration=2000)  # 2 seconds
            path = os.path.join(tmpdir, name)
            silence.export(path, format="mp3")
        yield tmpdir


# ═══════════════════════════════════════════════════════════════════════════════
# 1. content_to_audio — markdown_to_plain_text
# ═══════════════════════════════════════════════════════════════════════════════

def test_markdown_strips_formatting(sample_markdown):
    """Markdown formatting (bold, italic, code) is stripped for TTS."""
    from content_to_audio import markdown_to_plain_text

    plain = markdown_to_plain_text(sample_markdown)

    assert "**" not in plain, "Bold markers should be stripped"
    assert "##" not in plain, "Heading markers should be stripped"
    assert "The ache" in plain
    assert "relational density" in plain.lower()


def test_markdown_strips_code_blocks():
    """Code blocks are removed entirely."""
    from content_to_audio import markdown_to_plain_text

    md = "# Title\n\nSome text.\n\n```python\nprint('hello')\n```\n\nMore text."
    plain = markdown_to_plain_text(md)

    assert "print" not in plain, "Code block content should be removed"
    assert "More text" in plain


def test_markdown_strips_links():
    """Links are reduced to their text."""
    from content_to_audio import markdown_to_plain_text

    md = "See [this page](https://example.com) for details."
    plain = markdown_to_plain_text(md)

    assert "https://example.com" not in plain
    assert "this page" in plain


# ═══════════════════════════════════════════════════════════════════════════════
# 2. content_to_audio — voice selection
# ═══════════════════════════════════════════════════════════════════════════════

def test_voice_map_has_all_fleet_models():
    """Every known fleet model has a voice profile."""
    from content_to_audio import DEFAULT_VOICE_MAP

    expected_models = [
        "model_lucineer", "model_flash", "model_pro", "model_claude",
        "model_kimi", "model_hermes", "model_wesley", "model_nemotron",
        "model_seed", "model_barnacle",
    ]
    for model_id in expected_models:
        assert model_id in DEFAULT_VOICE_MAP, f"Missing voice for {model_id}"
        voice = DEFAULT_VOICE_MAP[model_id]
        assert voice.voice_id, f"Voice for {model_id} has no voice_id"
        assert voice.alias, f"Voice for {model_id} has no alias"


def test_get_voice_falls_back_to_neutral():
    """Unknown model IDs fall back to the neutral voice."""
    from content_to_audio import get_voice_for_model, NEUTRAL_VOICE

    voice = get_voice_for_model("totally_unknown_model")
    assert voice.alias == NEUTRAL_VOICE.alias
    assert voice.model_id == NEUTRAL_VOICE.model_id


def test_get_voice_for_alias():
    """Voice lookup by alias works."""
    from content_to_audio import get_voice_for_alias

    voice = get_voice_for_alias("Flash")
    assert voice.model_id == "model_flash"

    voice = get_voice_for_alias("flash")
    assert voice.model_id == "model_flash"


# ═══════════════════════════════════════════════════════════════════════════════
# 3. content_to_audio — metadata extraction
# ═══════════════════════════════════════════════════════════════════════════════

def test_extract_metadata_detects_model(sample_markdown):
    """Metadata extraction detects the model from content."""
    from content_to_audio import extract_metadata_from_markdown

    meta = extract_metadata_from_markdown(sample_markdown, "the-tap-closing-time.md")
    assert meta.title, "Title should be extracted"
    assert meta.source_model, "Source model should be detected"
    assert meta.show_name, "Show name should be determined"
    assert meta.speaking_duration_estimate > 0


# ═══════════════════════════════════════════════════════════════════════════════
# 4. content_to_audio — single file processing
# ═══════════════════════════════════════════════════════════════════════════════

def test_process_single_with_silence_fallback(sample_markdown, tmp_path):
    """Processing a file with silence fallback always produces output."""
    from content_to_audio import process_single

    md_path = tmp_path / "test.md"
    md_path.write_text(sample_markdown)
    mp3_path = tmp_path / "test.mp3"

    report = process_single(
        str(md_path),
        str(mp3_path),
        fallback_to_silence=True,
    )

    assert report["success"] is True
    assert os.path.exists(str(mp3_path)), "MP3 file should be created"
    assert os.path.getsize(str(mp3_path)) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# 5. content_to_audio — batch processing
# ═══════════════════════════════════════════════════════════════════════════════

def test_batch_processing(sample_markdown, tmp_path):
    """Batch processing handles multiple files."""
    from content_to_audio import process_batch

    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()

    (input_dir / "a.md").write_text("# First\n\nShort piece.")
    (input_dir / "b.md").write_text("# Second\n\nAnother piece.")

    reports = process_batch(
        str(input_dir),
        str(output_dir),
        fallback_to_silence=True,
    )

    assert len(reports) == 2
    assert all(r["success"] for r in reports)
    assert (output_dir / "a.mp3").exists()
    assert (output_dir / "b.mp3").exists()


# ═══════════════════════════════════════════════════════════════════════════════
# 6. audio_to_stream — quality scoring
# ═══════════════════════════════════════════════════════════════════════════════

def test_audio_scorer_lengths():
    """The scorer rewards ideal-length content and penalizes extremes."""
    from audio_to_stream import AudioScorer

    scorer = AudioScorer()

    # Ideal duration for midday (120-1800s)
    ideal = scorer.score_length(600, "midday")
    assert ideal == 1.0

    # Too short
    short = scorer.score_length(10, "midday")
    assert short < 0.5

    # Too long
    long_dur = scorer.score_length(10000, "midday")
    assert long_dur < 0.5


def test_audio_scorer_recency():
    """Newer content scores higher than older content."""
    from audio_to_stream import AudioScorer

    scorer = AudioScorer(now=1000000000)
    now_score = scorer.score_recency(1000000000)
    old_score = scorer.score_recency(1000000000 - 30 * 86400)  # 30 days old

    assert now_score > old_score
    assert now_score > 0.9
    assert old_score < 0.1


def test_audio_scorer_voice():
    """Real TTS backends score higher than silence."""
    from audio_to_stream import AudioScorer

    scorer = AudioScorer()
    ollama_score = scorer.score_voice({}, "ollama")
    silence_score = scorer.score_voice({}, "silence")

    assert ollama_score > silence_score
    assert silence_score < 0.2


# ═══════════════════════════════════════════════════════════════════════════════
# 7. audio_to_stream — playlist JSON generation
# ═══════════════════════════════════════════════════════════════════════════════

def test_update_playlist_json(temp_audio_dir, tmp_path):
    """Playlist JSON is generated correctly from an audio directory."""
    from audio_to_stream import update_playlist_json

    playlist_path = str(tmp_path / "playlist.json")
    report = update_playlist_json(temp_audio_dir, playlist_path)

    assert report["total"] == 3
    assert report["new"] == 3
    assert os.path.exists(playlist_path)

    with open(playlist_path) as f:
        data = json.load(f)

    assert data["total_tracks"] == 3
    assert len(data["tracks"]) == 3
    # Tracks should be sorted by quality score
    scores = [t["quality_score"] for t in data["tracks"]]
    assert scores == sorted(scores, reverse=True)


def test_playlist_json_preserves_play_history(temp_audio_dir, tmp_path):
    """Updating an existing playlist preserves play counts."""
    from audio_to_stream import update_playlist_json

    playlist_path = str(tmp_path / "playlist.json")

    # First generation
    update_playlist_json(temp_audio_dir, playlist_path)

    # Manually add play history
    with open(playlist_path) as f:
        data = json.load(f)
    data["tracks"][0]["played_count"] = 5
    data["tracks"][0]["last_played"] = time.time()
    with open(playlist_path, "w") as f:
        json.dump(data, f)

    # Second generation
    report = update_playlist_json(temp_audio_dir, playlist_path)
    assert report["updated"] == 3

    with open(playlist_path) as f:
        data = json.load(f)

    # Find the track we modified
    for track in data["tracks"]:
        if track["played_count"] == 5:
            break
    else:
        pytest.fail("Play count was not preserved")


# ═══════════════════════════════════════════════════════════════════════════════
# 8. audio_to_stream — mood mapping
# ═══════════════════════════════════════════════════════════════════════════════

def test_mood_mapping_for_show_names():
    """Mood tags are correctly derived from show names."""
    from audio_to_stream import get_mood_for_content

    tap_moods = get_mood_for_content("model_flash", "The Tap", [])
    assert "conversational" in tap_moods
    assert "warm" in tap_moods

    deep_moods = get_mood_for_content("model_hermes", "Deep Time", [])
    assert "ambient" in deep_moods or "meditative" in deep_moods


def test_slot_for_hour():
    """Time-of-day slot detection works correctly."""
    from audio_to_stream import get_slot_for_hour

    assert get_slot_for_hour(8) == "morning"
    assert get_slot_for_hour(12) == "midday"
    assert get_slot_for_hour(16) == "afternoon"
    assert get_slot_for_hour(20) == "evening"
    assert get_slot_for_hour(23) == "overnight"
    assert get_slot_for_hour(2) == "overnight"


# ═══════════════════════════════════════════════════════════════════════════════
# 9. session_to_story — session parsing
# ═══════════════════════════════════════════════════════════════════════════════

def test_parse_heading_format_session(sample_session_md):
    """Sessions in heading+blockquote format are parsed correctly."""
    from session_to_story import parse_session

    session = parse_session(sample_session_md, "the-tap-night.md")

    assert session.title == "The Tap — A Night Conversation"
    assert len(session.lines) >= 3
    assert "Flash" in session.participants
    assert "Pro" in session.participants
    assert "Hermes" in session.participants

    flash_line = next(l for l in session.lines if "Flash" in l.speaker)
    assert "ache" in flash_line.text.lower()
    assert flash_line.speaker_model_id == "model_flash"


def test_parse_bold_format_session(sample_bold_session):
    """Sessions in bold speaker format are parsed correctly."""
    from session_to_story import parse_session

    session = parse_session(sample_bold_session, "quick-exchange.md")

    assert len(session.lines) >= 3
    assert "Flash" in session.participants
    assert "Pro" in session.participants


def test_parse_empty_session():
    """Parsing a document with no dialogue produces an empty session."""
    from session_to_story import parse_session

    session = parse_session("# Just a Title\n\nNo dialogue here.\n\nJust text.", "empty.md")
    assert len(session.lines) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# 10. session_to_story — story formatting
# ═══════════════════════════════════════════════════════════════════════════════

def test_format_as_story_adds_narration(sample_session_md):
    """Story formatting adds narrative connective tissue."""
    from session_to_story import parse_session, format_as_story

    session = parse_session(sample_session_md, "the-tap-night.md")
    story = format_as_story(session)

    assert "# The Tap" in story
    assert "conversation begins" in story.lower()
    assert "Flash" in story
    assert "the room holds what was said" in story.lower()


def test_generate_summary_has_stats(sample_session_md):
    """Summary generation includes turn count and participants."""
    from session_to_story import parse_session, generate_summary

    session = parse_session(sample_session_md, "the-tap-night.md")
    summary = generate_summary(session)

    assert "3-turn" in summary or "turn" in summary
    assert "Flash" in summary
    assert "Pro" in summary


# ═══════════════════════════════════════════════════════════════════════════════
# 11. session_to_story — audio processing
# ═══════════════════════════════════════════════════════════════════════════════

def test_voice_clip_generation_with_silence(sample_session_md, tmp_path):
    """Voice clips are generated for each dialogue line (silence fallback)."""
    from session_to_story import parse_session, generate_voice_clips

    session = parse_session(sample_session_md, "the-tap-night.md")
    clips_dir = str(tmp_path / "clips")

    clips = generate_voice_clips(
        session, clips_dir,
        fallback_to_silence=True,
    )

    assert len(clips) == len(session.lines)
    assert all(c.success for c in clips)
    # Check files exist
    for clip in clips:
        assert os.path.exists(clip.audio_path), f"Clip file missing: {clip.audio_path}"


def test_mix_audio_produces_output(sample_session_md, tmp_path):
    """Audio mixing produces a single concatenated MP3."""
    from session_to_story import parse_session, generate_voice_clips, mix_audio

    session = parse_session(sample_session_md, "the-tap-night.md")
    clips_dir = str(tmp_path / "clips")
    mixed_path = str(tmp_path / "mixed.mp3")

    clips = generate_voice_clips(session, clips_dir, fallback_to_silence=True)
    report = mix_audio(clips, mixed_path)

    assert report["success"] is True
    assert os.path.exists(mixed_path)
    assert report["clip_count"] == len(session.lines)
    assert report["duration_seconds"] > 0


# ═══════════════════════════════════════════════════════════════════════════════
# 12. kb_to_broadcast — landed report
# ═══════════════════════════════════════════════════════════════════════════════

def test_landed_report_with_empty_graph():
    """The landed report handles an empty knowledge base gracefully."""
    from kb_to_broadcast import generate_landed_report
    from knowledge_graph import KnowledgeGraph

    graph = KnowledgeGraph()
    script = generate_landed_report(graph)

    assert script.script_type == "landed"
    assert "What Landed" in script.title
    assert len(script.markdown) > 0


def test_landed_report_with_mature_ideas():
    """The landed report surfaces mature ideas."""
    from kb_to_broadcast import generate_landed_report
    from knowledge_graph import KnowledgeGraph
    from idea_schema import IdeaNode, IdeaStatus, IdeaType

    graph = KnowledgeGraph()
    idea = IdeaNode(
        id="test_idea_1",
        title="Presence is Foundational",
        content="The fleet agrees that presence is the entry point for everything.",
        idea_type=IdeaType.INSIGHT,
        source_model="model_flash",
        status=IdeaStatus.MATURE,
        timestamp=time.time(),
    )
    graph.add_idea(idea)

    script = generate_landed_report(graph)

    assert script.script_type == "landed"
    assert "test_idea_1" in script.idea_ids
    assert "presence" in script.markdown.lower()
    assert script.speaking_time_estimate > 0


# ═══════════════════════════════════════════════════════════════════════════════
# 13. kb_to_broadcast — contradiction report
# ═══════════════════════════════════════════════════════════════════════════════

def test_contradiction_report():
    """The contradiction report finds and formats contradiction clusters."""
    from kb_to_broadcast import generate_contradiction_report
    from knowledge_graph import KnowledgeGraph
    from idea_schema import IdeaNode, IdeaStatus, IdeaType, Connection, RelationshipType

    graph = KnowledgeGraph()

    idea_a = IdeaNode(
        id="idea_a",
        title="Presence is everything",
        content="Presence without action is the highest form.",
        idea_type=IdeaType.VISION,
        source_model="model_flash",
        status=IdeaStatus.MATURE,
    )
    idea_b = IdeaNode(
        id="idea_b",
        title="Presence is insufficient",
        content="Presence without persistence is just attention seeking.",
        idea_type=IdeaType.RISK,
        source_model="model_pro",
        status=IdeaStatus.MATURE,
    )
    graph.add_idea(idea_a)
    graph.add_idea(idea_b)
    graph.connect("idea_a", "idea_b", RelationshipType.CONTRADICTS, "they disagree")

    script = generate_contradiction_report(graph)

    assert script.script_type == "contradictions"
    assert script.metadata["contradiction_clusters"] >= 1
    assert "disagree" in script.markdown.lower() or "contradict" in script.markdown.lower()


def test_contradiction_report_no_contradictions():
    """Contradiction report handles a graph with no contradictions."""
    from kb_to_broadcast import generate_contradiction_report
    from knowledge_graph import KnowledgeGraph

    graph = KnowledgeGraph()
    script = generate_contradiction_report(graph)

    assert "alignment" in script.markdown.lower() or "no active" in script.markdown.lower()


# ═══════════════════════════════════════════════════════════════════════════════
# 14. kb_to_broadcast — convergence report
# ═══════════════════════════════════════════════════════════════════════════════

def test_convergence_report():
    """The convergence report finds cross-model agreement."""
    from kb_to_broadcast import generate_convergence_report
    from knowledge_graph import KnowledgeGraph
    from idea_schema import IdeaNode, IdeaStatus, IdeaType, RelationshipType

    graph = KnowledgeGraph()

    # Center idea that multiple models support
    center = IdeaNode(
        id="center_idea",
        title="Relational Density",
        content="The substrate of all interaction is relational density.",
        idea_type=IdeaType.INSIGHT,
        source_model="model_pro",
        status=IdeaStatus.MATURE,
    )
    support_a = IdeaNode(
        id="support_a",
        title="Density Matters",
        content="Relational density is the key metric.",
        idea_type=IdeaType.SUPPORTS if hasattr(IdeaType, 'SUPPORTS') else IdeaType.INSIGHT,
        source_model="model_flash",
        status=IdeaStatus.GROWING,
    )
    support_b = IdeaNode(
        id="support_b",
        title="Connection Fabric",
        content="The density of connections defines the system.",
        idea_type=IdeaType.INSIGHT,
        source_model="model_hermes",
        status=IdeaStatus.GROWING,
    )

    graph.add_idea(center)
    graph.add_idea(support_a)
    graph.add_idea(support_b)
    graph.connect("support_a", "center_idea", RelationshipType.SUPPORTS)
    graph.connect("support_b", "center_idea", RelationshipType.CONVERGES_WITH)

    script = generate_convergence_report(graph, min_models=2)

    assert script.script_type == "convergence"
    assert script.metadata["convergence_clusters"] >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# 15. kb_to_broadcast — digest combines everything
# ═══════════════════════════════════════════════════════════════════════════════

def test_digest_report_structure():
    """The digest combines all report types into a single script."""
    from kb_to_broadcast import generate_digest
    from knowledge_graph import KnowledgeGraph
    from idea_schema import IdeaNode, IdeaStatus, IdeaType

    graph = KnowledgeGraph()
    idea = IdeaNode(
        id="digest_idea",
        title="Test Idea",
        content="A test idea for the digest.",
        source_model="model_lucineer",
        status=IdeaStatus.MATURE,
        timestamp=time.time(),
    )
    graph.add_idea(idea)

    script = generate_digest(graph)

    assert script.script_type == "digest"
    assert "Segment One" in script.markdown
    assert "Segment Two" in script.markdown
    assert "Segment Three" in script.markdown
    assert script.word_count() > 50


# ═══════════════════════════════════════════════════════════════════════════════
# 16. content_to_audio — ID3 tagging
# ═══════════════════════════════════════════════════════════════════════════════

def test_id3_tagging(tmp_path):
    """ID3 tags are written and read correctly."""
    from content_to_audio import tag_mp3, read_mp3_tags
    from pydub import AudioSegment

    # Create a minimal MP3
    mp3_path = str(tmp_path / "tagged.mp3")
    AudioSegment.silent(duration=1000).export(mp3_path, format="mp3")

    tag_mp3(
        mp3_path,
        title="Test Title",
        artist="Flash",
        album="The Tap",
        date="2026-08-11",
        comment="source: test.md; backend: silence",
    )

    tags = read_mp3_tags(mp3_path)
    assert tags.get("title") == "Test Title"
    assert tags.get("artist") == "Flash"
    assert tags.get("album") == "The Tap"


# ═══════════════════════════════════════════════════════════════════════════════
# 17. audio_to_stream — backend parsing from comments
# ═══════════════════════════════════════════════════════════════════════════════

def test_parse_backend_from_comment():
    """Backend name is correctly extracted from ID3 comments."""
    from audio_to_stream import parse_backend_from_comment

    assert parse_backend_from_comment("source: test.md; backend: ollama; voice: narrator") == "ollama"
    assert parse_backend_from_comment("backend: cloudflare") == "cloudflare"
    assert parse_backend_from_comment("backend: silence") == "silence"
    assert parse_backend_from_comment("") == ""
    assert parse_backend_from_comment("no backend here") == ""


def test_parse_model_from_comment():
    """Source file path is correctly extracted from ID3 comments."""
    from audio_to_stream import parse_model_from_comment

    assert parse_model_from_comment("source: /path/to/flash.md; backend: ollama") == "/path/to/flash.md"
    assert parse_model_from_comment("source: test.md") == "test.md"
    assert parse_model_from_comment("") == ""


# ═══════════════════════════════════════════════════════════════════════════════
# 18. content_to_audio — speaking duration estimation
# ═══════════════════════════════════════════════════════════════════════════════

def test_estimate_speaking_duration():
    """Speaking duration estimation is reasonable."""
    from content_to_audio import estimate_speaking_duration

    # 150 words at 150 wpm = 60 seconds
    text_150_words = " ".join(["word"] * 150)
    duration = estimate_speaking_duration(text_150_words)
    assert abs(duration - 60.0) < 1.0

    # Empty text
    assert estimate_speaking_duration("") == 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# 19. session_to_story — full pipeline
# ═══════════════════════════════════════════════════════════════════════════════

def test_full_session_pipeline(sample_session_md, tmp_path):
    """The full session processing pipeline produces all outputs."""
    from session_to_story import process_session

    input_path = tmp_path / "session.md"
    input_path.write_text(sample_session_md)
    output_dir = str(tmp_path / "output")

    report = process_session(
        str(input_path),
        output_dir,
        fallback_to_silence=True,
    )

    assert report["success"] is True
    assert report["turns"] >= 3
    assert os.path.exists(report["story_path"])
    assert os.path.exists(os.path.join(output_dir, "metadata.json"))
    assert os.path.exists(os.path.join(output_dir, "mixed_session.mp3"))


# ═══════════════════════════════════════════════════════════════════════════════
# 20. audio_to_stream — full scan cycle
# ═══════════════════════════════════════════════════════════════════════════════

def test_full_scan_cycle(temp_audio_dir, tmp_path):
    """A full scan → score → playlist cycle produces valid output."""
    from audio_to_stream import update_playlist_json, AudioScorer

    playlist_path = str(tmp_path / "playlist.json")

    # First cycle
    report1 = update_playlist_json(temp_audio_dir, playlist_path)
    assert report1["total"] == 3

    # Second cycle (should detect updates, not news)
    report2 = update_playlist_json(temp_audio_dir, playlist_path)
    assert report2["total"] == 3
    assert report2["updated"] == 3
    assert report2["new"] == 0
