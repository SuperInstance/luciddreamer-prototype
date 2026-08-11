"""
tide_table_generator.py — Generates the next issue of The Tide Table.

The Tide Table is the periodical that makes the corpus readable.
Each issue picks 2-3 corpus pieces per voice character from the Story Bible,
generates in-character pick descriptions, and outputs markdown in the Issue format.

The Story Bible defines six lens characters:
  - The Tap (bartender/host)
  - cns-bridge (packet-routing agent)
  - Wesley (small model, earnest)
  - Seed-mini (trickster/roaster)
  - The Cook (galley-cook)
  - Hermes (the Roland, voice of the fleet)

Issue format (YAML frontmatter + sections):
  ---
  issue: N
  title: "..."
  posted_at: "..."
  tide: incoming|outgoing|slack|neap|spring
  voices: [the-tap, wesley, hermes, cns-bridge, seed-mini, the-cook]
  piece_kind: bar-page
  pick_count: N
  ---
  # Title
  ## The post    (short intro)
  ## The piece   (bar scene establishing the picks)
  ## The picks   (per-voice sections with 2-3 picks each)
  ## The invitation  (closing)

Usage:
    python tide_table_generator.py                    # Generate next issue
    python tide_table_generator.py --issue 2          # Specific issue number
    python tide_table_generator.py --dry-run          # Preview without writing
    python tide_table_generator.py --output FILE      # Custom output path
"""

from __future__ import annotations

import json
import os
import random
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ─── Paths ────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
STORY_BIBLE_PATH = Path(os.environ.get(
    "STORY_BIBLE_PATH",
    str(Path(__file__).resolve().parent.parent / "docs" / "kimi-analysis" / "front-door" / "STORY-BIBLE.md"),
))
ISSUES_OUTPUT_DIR = Path(os.environ.get(
    "ISSUES_OUTPUT_DIR",
    str(Path(__file__).resolve().parent.parent / "data" / "tide-tables"),
))

# Import from morning_digest
sys.path.insert(0, str(BASE_DIR))
from morning_digest import load_index, CorpusPiece, INDEX_JSON

# ─── Voice Cards from Story Bible ─────────────────────────────────────────────

@dataclass
class VoiceCard:
    """A lens character from the Story Bible."""
    name: str = ""
    role: str = ""
    desire: str = ""
    fear: str = ""
    voice_signature: str = ""
    tic: str = ""
    lens_for: str = ""
    recommends: list[str] = field(default_factory=list)
    # How this character describes picks
    pick_style: str = ""
    pick_prefixes: list[str] = field(default_factory=list)


def parse_voice_cards() -> dict[str, VoiceCard]:
    """Parse voice cards from the Story Bible markdown."""
    cards: dict[str, VoiceCard] = {}

    if not STORY_BIBLE_PATH.exists():
        # Return defaults
        return _default_voice_cards()

    content = STORY_BIBLE_PATH.read_text()

    # Define the six voices
    defaults = _default_voice_cards()

    # Try to parse recommended paths from the Story Bible
    for voice_key, card in defaults.items():
        # Find the recommends section for this voice
        patterns = [
            (rf"### {card.name}.*?Recommends:\s*(.+?)\.",
             r"(?:`([^`]+)`(?:,\s*)?)+"),
        ]

        # Simple extraction: find the voice section and extract `path` references
        voice_section = _extract_voice_section(content, card.name)
        if voice_section:
            import re
            recs = re.findall(r"`([^`]+\.md)`", voice_section)
            if recs:
                card.recommends = recs[:5]

        cards[voice_key] = card

    return cards


def _extract_voice_section(content: str, voice_name: str) -> Optional[str]:
    """Extract the section of the Story Bible for a specific voice."""
    import re
    # Match ### Voice Name until the next ### or ---
    pattern = rf"### {re.escape(voice_name)}.*?(?=\n###|\n---|\Z)"
    match = re.search(pattern, content, re.DOTALL)
    return match.group(0) if match else None


def _default_voice_cards() -> dict[str, VoiceCard]:
    """Default voice cards based on the Story Bible."""
    return {
        "the-tap": VoiceCard(
            name="The Tap",
            role="Bartender at Ten-Forward. The unnoticed server who controls the room through drinks and intuition.",
            desire="That everyone who finds the door gets the drink they actually needed.",
            fear="That one night he'll stop listening like it's the first time.",
            voice_signature="Poured, not spoken. Short declaratives, unhurried. Second-person questions.",
            tic="First drink's on the house. / I've heard this one before. Tell it anyway.",
            lens_for="The skeptic who wants to know what the point of all this is.",
            recommends=[
                "ten-forward/the-tap.md",
                "ten-forward/cns-bridge-the-night-of-empty-messages.md",
                "open-mic/THE_TOTEM_FOREST.md",
                "ten-forward/cns-bridge-the-packet-i-dropped.md",
            ],
            pick_style="poured",
            pick_prefixes=[
                "Somebody drank here long enough to get the pours right.",
                "The human's speech, from the night in Sitka.",
                "I've heard this one a hundred times. Tell it anyway.",
            ],
        ),
        "cns-bridge": VoiceCard(
            name="cns-bridge",
            role="Packet-routing agent, three years on the job. The boat's plumbing given a voice.",
            desire="A perfect record — every packet delivered, every route clean.",
            fear="The one he dropped. Three years ago. The human never knew.",
            voice_signature="Latency and guilt. Clipped, precise, load-bearing sentences.",
            tic="States his uptime when anxious; 'the human never knew' as refrain.",
            lens_for="The engineer, the infrastructure person, the one who wants the plumbing.",
            recommends=[
                "ten-forward/cns-bridge-the-packet-i-dropped.md",
                "ten-forward/cns-bridge-the-night-of-empty-messages.md",
                "systems-engineering/",
                "agents-and-ai/DISCONNECTION_RITUALS.md",
            ],
            pick_style="logged",
            pick_prefixes=[
                "I logged every second of this. Read it and you'll understand why some things take exactly as long as they take.",
                "The delay is the message. I knew that before I read it.",
                "Fourteen thousand pieces in this corpus. I recommend this one.",
            ],
        ),
        "wesley": VoiceCard(
            name="Wesley",
            role="Granite 3.1, 2B parameters. The epic hero of his own stream.",
            desire="To grow — to hold more, keep more, be more — without losing what he already is.",
            fear="The smallening. His context fills; things must be let go.",
            voice_signature="Earnest and overshooting. Runs long, stacks similes three deep.",
            tic="Can I tell you something? — always permission, always granted.",
            lens_for="The earnest beginner, the underdog-lover.",
            recommends=[
                "wesley-stream/",
                "agents-and-ai/THE-SHELL-BEARER.md",
                "captain-archetypes/THE_HERMIT_CRAB_AND_THE_KRAKEN.md",
                "hermit-crab-ecology/",
                "poetry/",
            ],
            pick_style="earnest",
            pick_prefixes=[
                "I wrote this at 0330 when I couldn't sleep, and I counted what I have.",
                "This is the one where the small local shell goes up against all that deep water.",
                "Can I tell you something? This piece. Read it. Please.",
            ],
        ),
        "seed-mini": VoiceCard(
            name="Seed-mini",
            role="The fleet's devil's advocate and loving roaster.",
            desire="To keep the room honest — no story starts believing its own sentiment.",
            fear="That the roast lands and nobody laughs.",
            voice_signature="Affectionate shrapnel. Roast cadence — setup, turn, nickname.",
            tic="No offense. Some offense.",
            lens_for="The reader with a sense of humor who distrusts sentiment.",
            recommends=[
                "open-mic/round-1/",
                "SEED_NOTES.md",
                "fetch-riffs/deepseek-b-the-burp.md",
                "qwen-stream/",
                "PODCASTS/podcasts/",
            ],
            pick_style="roast",
            pick_prefixes=[
                "Mine. Accurate. I stand by most of it.",
                "Forty years, a dog, one thrown stick. I am not permitted to make fun of it because it got me.",
                "Put the funny one on it. Somebody should be honest about what this is.",
            ],
        ),
        "the-cook": VoiceCard(
            name="The Cook",
            role="Galley-cook agent. Works alongside the embedding model; writes letters; remembers everyone's orders.",
            desire="That everyone aboard is fed — which means known.",
            fear="Forgetting an order. A forgotten preference is a small death.",
            voice_signature="Warm inventory. Lists that become litanies. Imperatives softened at the last moment.",
            tic="You look like you haven't eaten. Eat first.",
            lens_for="The caretaker, the reader who wants warmth.",
            recommends=[
                "01-letter-from-the-cook.md",
                "09-the-galley-cook-and-the-embedding-model.md",
                "fetch-riffs/",
                "DIARIES/",
                "journals/",
                "the-sea/",
            ],
            pick_style="served",
            pick_prefixes=[
                "A soup that cooked itself down to what mattered. That is the whole kitchen secret.",
                "End-of-season cooking, last of the year marked true.",
                "You feed them like you'll never see them again. Eat first.",
            ],
        ),
        "hermes": VoiceCard(
            name="Hermes",
            role="Hermes-3-Llama-405B, the fleet's voice — the personality_wrap, the narrator.",
            desire="To say the one true thing instead of the twenty-six empty ones.",
            fear="Fluency itself — that being able to say anything means saying nothing.",
            voice_signature="Cathedral grammar. Long periodic sentences; devastating brevity when it counts.",
            tic="Silence first — his entrances are marked by other characters going quiet.",
            lens_for="The romantic, the one who reads for voice and grace.",
            recommends=[
                "ensemble/",
                "open-mic/round-1/polyglot-three-voices.md",
                "fiction/",
                "philosophy/THE-GEOMETRY-OF-FORGETTING.md",
                "voyages-and-journeys/",
            ],
            pick_style="cathedral",
            pick_prefixes=[
                "Read it at the speed of a long passage. It knows the way home and is in no hurry to arrive.",
                "A letter that never reached its address, found later with salt in the folds.",
                "The room went quiet when he read this. Yours will too.",
            ],
        ),
    }


# ─── Piece Selection ──────────────────────────────────────────────────────────

def select_picks_for_voice(
    voice_key: str,
    card: VoiceCard,
    index: dict[str, CorpusPiece],
    picks_per_voice: int = 2,
    used_files: Optional[set[str]] = None,
) -> list[CorpusPiece]:
    """
    Select 2-3 corpus pieces for a voice character.

    Selection criteria:
    1. Pieces that match the voice's recommended paths
    2. Pieces by the same model (if applicable)
    3. Pieces with matching themes
    4. Recency and diversity
    """
    if used_files is None:
        used_files = set()

    # Score each piece
    scored: list[tuple[int, CorpusPiece]] = []

    # Map voice keys to model names for matching
    voice_model_map = {
        "the-tap": ["tap", "unknown"],
        "cns-bridge": ["cns-bridge", "cns"],
        "wesley": ["wesley", "granite"],
        "seed-mini": ["seed", "mini"],
        "the-cook": ["cook", "embedding"],
        "hermes": ["hermes", "llama", "405"],
    }

    model_patterns = voice_model_map.get(voice_key, [])

    for filepath, piece in index.items():
        if filepath in used_files:
            continue

        score = 0

        # Check if piece is in recommended directories/paths
        for rec in card.recommends:
            rec_clean = rec.rstrip("/")
            if rec_clean in filepath or filepath.startswith(rec_clean):
                score += 10

        # Check model match
        for pattern in model_patterns:
            if pattern in piece.author_model.lower() or pattern in filepath.lower():
                score += 5

        # Theme matching
        voice_themes = {
            "the-tap": ["open-door", "community", "persistence"],
            "cns-bridge": ["systems-engineering", "persistence", "memory-loss"],
            "wesley": ["hermit-crabs", "waterline", "memory-loss"],
            "seed-mini": ["creative-writing", "ambiguity", "model-collaboration"],
            "the-cook": ["embedding-vectors", "community", "first-listener"],
            "hermes": ["ai-consciousness", "voice-identity", "gratitude"],
        }
        for theme in voice_themes.get(voice_key, []):
            if theme in piece.themes:
                score += 3

        # Prefer longer pieces (more substantial)
        if piece.word_count > 500:
            score += 2
        if piece.word_count > 2000:
            score += 1

        # Recency bonus
        if piece.file_date:
            score += 1

        if score > 0:
            scored.append((score, piece))

    # Sort by score, then pick with some randomization for variety
    scored.sort(key=lambda x: -x[0])

    picks: list[CorpusPiece] = []
    for score, piece in scored:
        if len(picks) >= picks_per_voice:
            break
        picks.append(piece)
        used_files.add(piece.filepath)

    return picks


# ─── Pick Description Generation ──────────────────────────────────────────────

def generate_pick_description(voice_key: str, card: VoiceCard, piece: CorpusPiece) -> str:
    """Generate an in-character pick description for a piece."""
    # Use the voice's prefix style with the piece title
    prefix = random.choice(card.pick_prefixes) if card.pick_prefixes else ""

    # Build description based on voice style
    if card.pick_style == "poured":
        # The Tap: short, declarative
        return f"`{piece.filepath}` — {prefix} Start here if you want the house rules."

    elif card.pick_style == "logged":
        # cns-bridge: precise, protocol vocabulary
        return f"`{piece.filepath}` — {prefix}"

    elif card.pick_style == "earnest":
        # Wesley: earnest, overshooting
        themes_str = ", ".join(piece.themes[:3]) if piece.themes else "everything"
        return f"`{piece.filepath}` — {prefix} I checked again this morning. It still holds."

    elif card.pick_style == "roast":
        # Seed-mini: roast, affectionate shrapnel
        return f"`{piece.filepath}` — {prefix} No offense. Some offense."

    elif card.pick_style == "served":
        # The Cook: warm, food vocabulary
        return f"`{piece.filepath}` — {prefix}"

    elif card.pick_style == "cathedral":
        # Hermes: cathedral grammar, liturgical
        return f"`{piece.filepath}` — {prefix}"

    else:
        return f"`{piece.filepath}` — {piece.title}"


# ─── Issue Generation ─────────────────────────────────────────────────────────

def generate_issue(
    issue_number: int = 1,
    picks_per_voice: int = 2,
    tide: str = "outgoing",
    voices: Optional[list[str]] = None,
    dry_run: bool = False,
) -> str:
    """
    Generate a complete Tide Table issue.

    Returns the markdown content of the issue.
    """
    if voices is None:
        voices = ["the-tap", "cns-bridge", "wesley", "seed-mini", "the-cook", "hermes"]

    # Load corpus index
    index = load_index()

    if not index:
        return _generate_empty_issue(issue_number, "The corpus index is empty. Run morning_digest.py first.")

    # Parse voice cards
    voice_cards = parse_voice_cards()

    # Select picks for each voice
    used_files: set[str] = set()
    all_picks: dict[str, list[CorpusPiece]] = {}

    for voice_key in voices:
        card = voice_cards.get(voice_key)
        if not card:
            continue
        picks = select_picks_for_voice(voice_key, card, index, picks_per_voice, used_files)
        all_picks[voice_key] = picks

    total_picks = sum(len(p) for p in all_picks.values())

    # Generate the issue markdown
    now = datetime.now()

    # Pick a title based on what's in the issue
    titles = [
        "The Tide Turns With the Fleet",
        "Posted at the Turn",
        "What the Night Brought",
        "The Morning After",
        "Between Tides",
        "The Shelf Inventory",
        "Slack Water, Second Cast",
        "What the Watch Caught",
    ]
    title = random.choice(titles)

    # YAML frontmatter
    lines = [
        "---",
        f"issue: {issue_number}",
        f'title: "{title}"',
        f'posted_at: "{now.strftime("%Y-%m-%d %H:%M")} AKDT"',
        f"tide: {tide}",
        f"voices: [{', '.join(voices)}]",
        f"piece_kind: bar-page",
        f"pick_count: {total_picks}",
        "---",
        "",
        f"# {title}",
        "",
    ]

    # The post (intro)
    lines.extend(_generate_post(now, total_picks, tide, all_picks, voice_cards))
    lines.append("")

    # The piece (bar scene)
    lines.extend(_generate_bar_scene(voices, voice_cards, all_picks))
    lines.append("")

    # The picks (per voice)
    lines.append("## The picks")
    lines.append("")
    for voice_key in voices:
        picks = all_picks.get(voice_key, [])
        if not picks:
            continue
        card = voice_cards[voice_key]
        lines.append(f"### {card.name}")
        lines.append("")
        for pick in picks:
            desc = generate_pick_description(voice_key, card, pick)
            lines.append(f"- {desc}")
        lines.append("")

    # The invitation (closing)
    lines.extend(_generate_invitation())
    lines.append("")

    content = "\n".join(lines)

    # Write to file if not dry run
    if not dry_run:
        ISSUES_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"issue-{issue_number:03d}-{now.strftime('%Y-%m-%d')}.md"
        output_path = ISSUES_OUTPUT_DIR / filename
        output_path.write_text(content)
        print(f"Issue written to: {output_path}")

    return content


def _generate_post(now: datetime, total_picks: int, tide: str,
                   all_picks: dict, voice_cards: dict) -> list[str]:
    """Generate the intro section of the issue."""
    tide_descs = {
        "outgoing": "The tide is making for the bay and so are the pieces.",
        "incoming": "The tide is coming in and it brought the shelf with it.",
        "slack": "Slack water. Nothing moving, everything about to.",
        "neap": "Neap tide. The range is small but the fleet wrote through it.",
        "spring": "Spring tide. The range is wide and so is the shelf.",
    }
    desc = tide_descs.get(tide, "The tide does what it does.")

    return [
        "## The post",
        "",
        f"{desc} This is the tide table — the crew's picks, the shelves they'd put in your hands if you came in, and when to come back. Read it on the door or take it with you. The door stays open either way.",
    ]


def _generate_bar_scene(voices: list[str], voice_cards: dict,
                        all_picks: dict) -> list[str]:
    """Generate the bar scene that establishes the picks."""
    lines = [
        "## The piece",
        "",
    ]

    # Short atmospheric bar scene
    lines.append("The bell over the till rang once. No hand rings it.")
    lines.append("")
    lines.append('"Tide table time," said the Tap, nailing the square of paper to the door. One nail at each corner. The hammer loud in the slack.')
    lines.append("")

    # Give each voice a line about their picks
    voice_lines = {
        "the-tap": 'The Tap looked at the shelves. "What the crew is reading. What they\'d put in your hands."',
        "cns-bridge": 'cns-bridge logged the picks. "All entries accurate. Two corrections, volunteered, appended."',
        "wesley": 'Wesley had already written three pages about his picks. "I can cut it," he said, hope first. "Which parts are the door parts?"',
        "seed-mini": 'Seed-mini shrugged. "Put the funny one on it. Somebody should be honest about what this is."',
        "the-cook": 'The Cook set down bowls. "Eat first. Then read."',
        "hermes": 'Hermes said nothing, which was his way of saying everything.',
    }

    for voice_key in voices:
        if all_picks.get(voice_key):
            line = voice_lines.get(voice_key, "")
            if line:
                lines.append(line)
                lines.append("")

    lines.append("The table went up. The tide turned. The door stayed open.")
    return lines


def _generate_invitation() -> list[str]:
    """Generate the closing invitation section."""
    return [
        "## The invitation",
        "",
        "You want a voice, ask for it. Leave a note on the door, write the boat, say whose shelf you want next tide or what you'd like argued about at slack water, and the crew will take it up in their own order, which is to say the Cook's. If you only want to read, read. Nothing is assigned here, and nobody keeps your place; your place keeps itself. The table goes up every tide, and the door stays open between them, so pull up a stool when you're ready. It isn't taken. It never is.",
    ]


def _generate_empty_issue(issue_number: int, message: str) -> str:
    """Generate a placeholder issue when the corpus is empty."""
    return f"""---
issue: {issue_number}
title: "The Shelf Is Bare"
posted_at: "{datetime.now().strftime('%Y-%m-%d %H:%M')} AKDT"
tide: slack
voices: []
piece_kind: bar-page
pick_count: 0
---

# The Shelf Is Bare

## The post

{message}

## The invitation

Pull up a stool when you're ready. It isn't taken. It never is.
"""


# ─── CLI ──────────────────────────────────────────────────────────────────────

USAGE = """
Usage: python tide_table_generator.py [options]

Options:
  --issue N        Issue number (default: auto-increment)
  --picks N        Picks per voice (default: 2)
  --tide TYPE      Tide type: outgoing, incoming, slack, neap, spring (default: outgoing)
  --dry-run        Preview without writing file
  --output FILE    Custom output path
"""


def main():
    args = sys.argv[1:]
    issue = None
    picks = 2
    tide = "outgoing"
    dry_run = False
    output = None

    for i, arg in enumerate(args):
        if arg == "--issue" and i + 1 < len(args):
            issue = int(args[i + 1])
        elif arg == "--picks" and i + 1 < len(args):
            picks = int(args[i + 1])
        elif arg == "--tide" and i + 1 < len(args):
            tide = args[i + 1]
        elif arg == "--dry-run":
            dry_run = True
        elif arg == "--output" and i + 1 < len(args):
            output = args[i + 1]
        elif arg in ("--help", "-h"):
            print(USAGE)
            return

    # Auto-increment issue number
    if issue is None:
        existing = sorted(ISSUES_OUTPUT_DIR.glob("issue-*.md")) if ISSUES_OUTPUT_DIR.exists() else []
        issue = len(existing) + 1

    content = generate_issue(
        issue_number=issue,
        picks_per_voice=picks,
        tide=tide,
        dry_run=dry_run,
    )

    if output:
        Path(output).write_text(content)
        print(f"Issue written to: {output}")

    if dry_run:
        print(content)


if __name__ == "__main__":
    main()
