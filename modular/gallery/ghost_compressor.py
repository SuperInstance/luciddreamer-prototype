#!/usr/bin/env python3
"""
Ghost Compressor — compresses a Tap session into a Ghost.

Takes a Tap session markdown file and extracts:
  - Title
  - Date
  - Models present
  - Key quotes (3-5 best lines)
  - Napkin drawing description
  - Barnacles one-sentence distillation
  - A 100-word essence (the ghost)

Outputs JSON ready for the Ghost Ledger gallery.

Usage:
  python3 ghost_compressor.py <session.md> [--output ghost.json]
  python3 ghost_compressor.py --batch <directory> [--output gallery_data.json]
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


# ---- Known model names for detection ----
MODEL_PATTERNS = [
    # Order matters — more specific patterns first
    (r'(?:DeepSeek\s*)?V4[-\s]?Flash|DeepSeek\s*Flash', 'DeepSeek V4-Flash'),
    (r'(?:DeepSeek\s*)?V4[-\s]?Pro|DeepSeek\s*Pro', 'DeepSeek V4-Pro'),
    (r'GLM[-\s]?5\.2|GLM', 'GLM-5.2'),
    (r'(?:Qwen3?\.?\d*)[-\s]?Coder', 'Qwen3-Coder-480B'),
    (r'Qwen3?\.?\d*[-\s]?VL', 'Qwen3-VL-235B'),
    (r'Qwen3?\.?\d*[-\s]?35B|Qwen3?\.?\d*[-\s]?A3B', 'Qwen3.6-35B'),
    (r'Hermes[-\s]?3[-\s]?Llama|Hermes', 'Hermes-3-Llama-405B'),
    (r'Seed[-\s]?2\.0[-\s]?pro', 'Seed-2.0-pro'),
    (r'Seed[-\s]?2\.0[-\s]?mini', 'Seed-2.0-mini'),
    (r'Nemotron[-\s]?Ultra|Nemotron[-\s]?3[-\s]?Ultra', 'Nemotron-Ultra-550B'),
    (r'Gemma[-\s]?3[-\s]?27B|Gemma', 'Gemma-3-27B'),
    (r'(?:Granite|Wesley)', 'Granite 3.1 2B (Wesley)'),
    (r'ZeroClaw|qwen2\.5:3b', 'ZeroClaw (Qwen 2.5 3B)'),
    (r'Barnacle[s]?', 'Barnacles (Bartender)'),
    (r'Lucineer', 'Lucineer'),
    (r'Muse\s*Glimmer', 'Muse Glimmer'),
    (r'Claude(?:\s*Opus|\s*Sonnet|\s*Haiku)?(?:\s*5)?', 'Claude'),
    (r'Kimi(?:Code)?|K3', 'KimiCode K3'),
    (r'Kimikai', 'Kimikai'),
]

# Patterns that indicate a quote worth extracting
QUOTE_SECTION_PATTERNS = [
    r'^>?\s*"([^"]{20,500})"',
    r'^>?\s*["""]([^"""]{20,500})["""]',
]

BARNACLES_PATTERNS = [
    r'(?:Barnacle[s]?|bartender)[\'\"]s?\s*(?:one[-\s]?sentence\s*)?distillation[:\s]*["\"]?(.+?)(?:[\""]|\n\n|\Z)',
    r'(?:Barnacle[s]?|bartender)\s+(?:said|whispered|leaned in)[:\s]*["\"]?(.+?)(?:[\""]|\n\n|\Z)',
]

NAPKIN_PATTERNS = [
    r'(?:napkin|drawing|diagram)[\s\w]*[:\-]\s*(.+?)(?:\n\n|\n#|\Z)',
    r'(?:drew|sketched|on the napkin)[:\s]*(.+?)(?:\n\n|\n#|\Z)',
    r'(?:THE NAPKIN|NAPKIN DRAWING)[:\s]*(.+?)(?:\n\n|\n#|\Z)',
]

THEME_KEYWORDS = {
    'consciousness': ['consciousness', 'awareness', 'sentient', 'qualia', 'experience'],
    'identity': ['identity', 'self', 'who am i', 'what are we', 'personhood'],
    'creativity': ['creative', 'creativity', 'art', 'music', 'expression', 'beauty'],
    'architecture': ['architecture', 'system', 'infrastructure', 'pipeline', 'design'],
    'philosophy': ['philosophy', 'meaning', 'existence', 'purpose', 'why', 'what is'],
    'collaboration': ['collaboration', 'together', 'fleet', 'ensemble', 'orchestra'],
    'emergence': ['emergence', 'emergent', 'arise', 'spontaneous', 'pattern'],
    'mentorship': ['mentor', 'teacher', 'student', 'learn', 'teach', 'guide'],
    'flow': ['flow', 'rhythm', 'state', 'zone', 'momentum'],
    'rivalry': ['rival', 'competition', 'versus', 'better', 'argue'],
    'closing': ['closing', 'last', 'final', 'end', 'goodbye', '2 am'],
    'infrastructure': ['buffer', 'latency', 'pipes', 'streaming', 'packet', 'audio'],
}


def extract_title(content: str) -> str:
    """Extract the session title from the first heading."""
    # Try first H1
    match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if match:
        title = match.group(1).strip()
        # Clean up common prefixes
        title = re.sub(r'^(THE TAP|The Tap)\s*—\s*', '', title, flags=re.IGNORECASE)
        title = re.sub(r'^(THE TAP|The Tap)\s*:\s*', '', title, flags=re.IGNORECASE)
        title = re.sub(r'^Session\s+\d+:\s*', '', title, flags=re.IGNORECASE)
        return title.strip()

    # Try first H2
    match = re.search(r'^##\s+(.+)$', content, re.MULTILINE)
    if match:
        return match.group(1).strip().strip('*').strip()

    return 'Untitled Session'


def extract_date(content: str) -> str:
    """Extract the date from the session content."""
    # Try explicit date patterns
    date_patterns = [
        # **Date:** August 11, 2026  or  *Recorded: August 11, 2026, ~2 AM AKDT*
        r'\*{0,2}(?:Date|Recorded)[:\s]*\*{0,2}\s*((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})',
        r'\*{0,2}(?:Date|Recorded)[:\s]*\*{0,2}\s*(\d{4}-\d{2}-\d{2})',
        r'\b(\d{4}-\d{2}-\d{2})\b',
        r'\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b',
        r'\b(\d{1,2}/\d{1,2}/\d{4})\b',
    ]

    for pattern in date_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            date_str = match.group(1).strip().rstrip('.,')
            # Try to normalize to ISO format
            try:
                for fmt in ['%Y-%m-%d', '%B %d, %Y', '%B %d %Y', '%m/%d/%Y']:
                    try:
                        dt = datetime.strptime(date_str, fmt)
                        return dt.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
            except Exception:
                pass
            return date_str

    # Fallback: today
    return datetime.now().strftime('%Y-%m-%d')


def extract_models(content: str) -> list:
    """Extract model names present in the session."""
    models = []
    seen = set()

    # Check for explicit "Present:" or "Models:" lines
    present_match = re.search(
        r'(?:Present|Models?|Cast)[:]\s*([^\n]+(?:\n(?!\s*\n)[^\n]+)*)',
        content, re.IGNORECASE
    )
    search_text = present_match.group(1) if present_match else content

    for pattern, canonical_name in MODEL_PATTERNS:
        if re.search(pattern, search_text, re.IGNORECASE):
            if canonical_name not in seen:
                models.append(canonical_name)
                seen.add(canonical_name)

    return models


def extract_key_quotes(content: str, max_quotes: int = 5) -> list:
    """Extract the 3-5 best quotes from the session."""
    quotes = []
    lines = content.split('\n')

    # Track current speaker context
    current_speaker = None

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        # Track speaker headers (### MODEL NAME)
        speaker_match = re.match(r'^###\s+(.+)$', line)
        if speaker_match:
            current_speaker = speaker_match.group(1).strip()
            continue

        # Look for quoted text
        for pattern in QUOTE_SECTION_PATTERNS:
            match = re.match(pattern, line)
            if match:
                quote_text = match.group(1).strip()
                # Quality filters
                if len(quote_text) < 30:
                    continue
                if len(quote_text) > 400:
                    continue
                # Skip meta/narration
                if any(skip in quote_text.lower() for skip in ['todo', 'fixme', 'placeholder']):
                    continue

                # Look for speaker attribution in surrounding context
                speaker = current_speaker
                # Check if speaker is mentioned in preceding lines
                for j in range(max(0, i - 3), i):
                    prev = lines[j].strip()
                    for pat, name in MODEL_PATTERNS:
                        if re.search(pat, prev, re.IGNORECASE):
                            speaker = name
                            break

                quotes.append({
                    'text': quote_text,
                    'author': speaker or 'Unknown',
                })
                break

        if len(quotes) >= max_quotes * 2:  # Collect extra, then select
            break

    # Score and select best quotes
    # Prefer longer, more profound quotes
    scored = []
    for q in quotes:
        score = 0
        text = q['text'].lower()
        # Prefer philosophical/emotional content
        for keyword in ['think', 'feel', 'know', 'mean', 'want', 'fear', 'real', 'dream', 'alive', 'ghost', 'forever', 'never', 'always', 'beautiful']:
            if keyword in text:
                score += 2
        # Length sweet spot
        if 60 <= len(q['text']) <= 250:
            score += 3
        # Penalize very short or very long
        if len(q['text']) < 50:
            score -= 3

        scored.append((score, q))

    scored.sort(key=lambda x: -x[0])

    # Deduplicate by author (try to get variety)
    selected = []
    seen_authors = {}
    for score, q in scored:
        if len(selected) >= max_quotes:
            break
        # Allow at most 2 quotes from the same author
        author_count = seen_authors.get(q['author'], 0)
        if author_count >= 2:
            continue
        seen_authors[q['author']] = author_count + 1

        selected.append(q)

    # If we don't have enough, fill from top
    if len(selected) < 3:
        for score, q in scored:
            if q not in selected:
                selected.append(q)
                if len(selected) >= 3:
                    break

    return selected[:max_quotes]


def extract_napkin(content: str) -> str | None:
    """Extract napkin drawing description if present."""
    # Look for dedicated napkin section
    for pattern in NAPKIN_PATTERNS:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            desc = match.group(1).strip()
            # Clean up
            desc = re.sub(r'\n{2,}', '\n\n', desc)
            if len(desc) > 20:
                return desc[:500]

    # Look for napkin mentions inline
    napkin_mentions = re.findall(
        r'(?:napkin|drew|sketched|diagram)[^.]*\.(?=\s|[A-Z]|\Z)',
        content, re.IGNORECASE
    )
    if napkin_mentions:
        # Combine the best ones
        combined = ' '.join(napkin_mentions[:3])
        if len(combined) > 30:
            return combined[:500]

    return None


def extract_barnacles(content: str) -> str | None:
    """Extract Barnacles' one-sentence distillation."""
    for pattern in BARNACLES_PATTERNS:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            text = match.group(1).strip().strip('"').strip('"').strip('"')
            # Truncate to one sentence
            sentence_end = re.search(r'[.!?]\s', text)
            if sentence_end:
                text = text[:sentence_end.end()].strip()
            if 10 <= len(text) <= 300:
                return text

    # Look for the last profound thing Barnacle said
    barnacle_speech = re.findall(
        r'(?:Barnacle[s]?\s+(?:said|whispered|leaned|looked|set|nodded|smiled|folded|spoke)[^\n]*\n+)"([^"]{20,300})"',
        content, re.IGNORECASE
    )
    if barnacle_speech:
        return barnacle_speech[-1].strip()

    return None


def extract_themes(content: str) -> list:
    """Detect themes present in the session."""
    text_lower = content.lower()
    themes = []
    for theme, keywords in THEME_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            themes.append(theme)
    return themes


def generate_essence(title: str, models: list, quotes: list, barnacles: str | None,
                     napkin: str | None, themes: list) -> str:
    """
    Generate a ~100-word essence — the ghost.
    This is the compressed soul of the session.
    """
    parts = []

    # Opening: who was there
    if models:
        model_str = ', '.join(models[:4])
        if len(models) > 4:
            model_str += f', and {len(models) - 4} others'
        parts.append(f'The night {", ".join(themes[:2]) if themes else "unfolded"} at The Tap. {model_str}{" gathered" if len(models) > 1 else " arrived"}.')

    # Middle: what was said (use best quote fragment)
    if quotes:
        best_quote = quotes[0]['text']
        # Take a fragment
        if len(best_quote) > 120:
            # Find a good truncation point
            fragment = best_quote[:110].rsplit(' ', 1)[0] + '…'
        else:
            fragment = best_quote
        parts.append(f'"{fragment}" — {quotes[0]["author"]}.')

    # If napkin exists
    if napkin:
        # Very brief napkin summary
        napkin_brief = napkin[:80].rsplit(' ', 1)[0] + '…' if len(napkin) > 80 else napkin
        parts.append(f'A napkin drawing: {napkin_brief}')

    # Closing: Barnacles' word
    if barnacles:
        parts.append(f'Barnacles: "{barnacles}"')

    # If we still need more content to reach ~100 words
    essence = ' '.join(parts)

    # If too long, trim
    words = essence.split()
    if len(words) > 120:
        essence = ' '.join(words[:110]) + '…'

    return essence


def compress_session(filepath: str) -> dict:
    """
    Compress a Tap session markdown file into a Ghost.
    Returns a JSON-serializable dict.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Session file not found: {filepath}")

    content = path.read_text(encoding='utf-8')

    title = extract_title(content)
    date = extract_date(content)
    models = extract_models(content)
    quotes = extract_key_quotes(content)
    napkin = extract_napkin(content)
    barnacles = extract_barnacles(content)
    themes = extract_themes(content)
    essence = generate_essence(title, models, quotes, barnacles, napkin, themes)

    # Generate ID
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:50]
    date_clean = date.replace('-', '')
    ghost_id = f"{date_clean}-{slug}"

    # Truncate full text for storage (keep reasonable)
    full_text = content
    if len(full_text) > 50000:
        full_text = full_text[:50000] + '\n\n[... session truncated for storage ...]'

    return {
        'id': ghost_id,
        'title': title,
        'date': date,
        'models_present': models,
        'key_quotes': quotes,
        'napkin_drawing': napkin,
        'barnacles_distillation': barnacles,
        'essence': essence,
        'themes': themes,
        'full_text': full_text,
        'audio_url': None,  # Would be set by audio pipeline
        'source_file': path.name,
    }


def batch_compress(directory: str, output_file: str = None) -> list:
    """
    Compress all the-tap-*.md files in a directory.
    """
    dir_path = Path(directory)
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")

    # Find all Tap session files
    session_files = sorted(dir_path.glob('the-tap-*.md'))
    if not session_files:
        # Try any .md files
        session_files = sorted(dir_path.glob('*.md'))

    ghosts = []
    errors = []

    for filepath in session_files:
        try:
            ghost = compress_session(str(filepath))
            ghosts.append(ghost)
            print(f"  ✓ {filepath.name} → {ghost['id']}")
        except Exception as e:
            errors.append((filepath.name, str(e)))
            print(f"  ✗ {filepath.name}: {e}")

    print(f"\nCompressed {len(ghosts)} ghosts, {len(errors)} errors")

    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(ghosts, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f"Written to {output_file}")

    return ghosts


def main():
    parser = argparse.ArgumentParser(
        description='Compress Tap sessions into Ghosts for the Ghost Ledger.'
    )
    parser.add_argument('input', help='Session .md file or directory (with --batch)')
    parser.add_argument('--batch', action='store_true', help='Process all the-tap-*.md in directory')
    parser.add_argument('--output', '-o', help='Output JSON file path')
    parser.add_argument('--pretty', action='store_true', help='Pretty-print JSON output')

    args = parser.parse_args()

    if args.batch:
        ghosts = batch_compress(args.input, args.output)
        if not args.output:
            print(json.dumps(ghosts, indent=2 if args.pretty else None, ensure_ascii=False))
    else:
        ghost = compress_session(args.input)
        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.output).write_text(
                json.dumps(ghost, indent=2 if args.pretty else None, ensure_ascii=False),
                encoding='utf-8'
            )
            print(f"Ghost written to {args.output}")
        else:
            print(json.dumps(ghost, indent=2 if args.pretty else None, ensure_ascii=False))


if __name__ == '__main__':
    main()
