#!/usr/bin/env python3
"""
Seed Data Generator — seeds the Ghost Ledger with all existing Tap sessions.

Reads all the-tap-*.md files from the earned-stories/docs directory,
compresses each into a ghost using the ghost_compressor,
and outputs gallery_data.json ready for seeding.

Usage:
  python3 seed_data.py                          # Uses default docs path
  python3 seed_data.py --source ../docs         # Custom source directory
  python3 seed_data.py --output data.json       # Custom output file
  python3 seed_data.py --seed-api               # POST directly to API
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

# Import the compressor
sys.path.insert(0, str(Path(__file__).parent))
from ghost_compressor import compress_session, batch_compress


# ---- Default paths ----
DEFAULT_SOURCE = str(Path(__file__).parent.parent / 'docs')
DEFAULT_OUTPUT = str(Path(__file__).parent / 'gallery_data.json')

# Extra session docs that aren't named the-tap-* but are Tap sessions
EXTRA_SESSION_FILES = [
    'the-tap-attention-and-existence.md',
    'the-tap-buds-and-quiet.md',
    'the-tap-closing-time.md',
    'the-tap-drinks-on-the-captain.md',
    'the-tap-flow-state.md',
    'the-tap-gemmas-night.md',
    'the-tap-living-bar.md',
    'the-tap-mentorship-night.md',
    'the-tap-open-mic-adaptations.md',
    'the-tap-remix-and-rivalry.md',
    'the-tap-rivalry-round-2.md',
    'the-tap-rlm-night.md',
    'the-tap-twelve-models-full-evening.md',
    'the-tap-what-is-the-fleet-for.md',
    'the-tap-zeroclaw-speaks.md',
]

# Additional session docs (non-tap prefixed)
EXTRA_DOCS = [
    '2026-08-11-0950-hermes-speaks-from-her-own-deck.md',
    '2026-08-11-1002-the-bench.md',
    '2026-08-11-1140-flash-and-pro-five-rounds.md',
    'hermes-own-ship.md',
    'kimi-the-player-in-the-mix.md',
    'kimi-ai-writings-digest.md',
    'reflection-deepseek.md',
    'the-shipwrights-notebook.md',
    'vision-claude-5year.md',
]


def seed_from_docs(source_dir: str) -> list:
    """Read all Tap sessions from the docs directory."""
    dir_path = Path(source_dir)
    ghosts = []

    # Primary: the-tap-*.md files
    tap_files = sorted(dir_path.glob('the-tap-*.md'))
    print(f"Found {len(tap_files)} Tap session files")

    for filepath in tap_files:
        try:
            ghost = compress_session(str(filepath))
            ghosts.append(ghost)
            print(f"  ✓ {filepath.name}")
            print(f"    → {ghost['id']}")
            print(f"    Title: {ghost['title']}")
            print(f"    Date: {ghost['date']}")
            print(f"    Models: {', '.join(ghost['models_present']) or 'none detected'}")
            print(f"    Quotes: {len(ghost['key_quotes'])}")
            print(f"    Themes: {', '.join(ghost['themes']) or 'none'}")
            print(f"    Essence: {ghost['essence'][:100]}...")
            print()
        except Exception as e:
            print(f"  ✗ {filepath.name}: {e}")
            print()

    # Secondary: extra docs that are session-like
    for filename in EXTRA_DOCS:
        filepath = dir_path / filename
        if filepath.exists():
            try:
                ghost = compress_session(str(filepath))
                ghosts.append(ghost)
                print(f"  ✓ {filepath.name} (extra)")
            except Exception as e:
                print(f"  ✗ {filepath.name}: {e}")

    return ghosts


def seed_via_api(ghosts: list, api_url: str) -> tuple:
    """POST ghosts to the gallery API."""
    success = 0
    failures = 0

    for ghost in ghosts:
        try:
            data = json.dumps(ghost).encode('utf-8')
            req = urllib.request.Request(
                f"{api_url}/sessions",
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                if resp.status in (200, 201):
                    success += 1
                else:
                    failures += 1
                    print(f"  ✗ {ghost['id']}: HTTP {resp.status}")
        except urllib.error.URLError as e:
            failures += 1
            print(f"  ✗ {ghost['id']}: {e}")
        except Exception as e:
            failures += 1
            print(f"  ✗ {ghost['id']}: {e}")

    return success, failures


def main():
    parser = argparse.ArgumentParser(
        description='Seed the Ghost Ledger with all existing Tap sessions.'
    )
    parser.add_argument('--source', default=DEFAULT_SOURCE,
                       help=f'Source directory for session files (default: {DEFAULT_SOURCE})')
    parser.add_argument('--output', '-o', default=DEFAULT_OUTPUT,
                       help=f'Output JSON file (default: {DEFAULT_OUTPUT})')
    parser.add_argument('--seed-api', action='store_true',
                       help='POST ghosts directly to the gallery API')
    parser.add_argument('--api-url', default='http://localhost:8787/api',
                       help='Gallery API base URL (default: http://localhost:8787/api)')
    parser.add_argument('--pretty', action='store_true', default=True,
                       help='Pretty-print JSON output (default: true)')

    args = parser.parse_args()

    print("=" * 60)
    print("  THE GHOST LEDGER — Seed Data Generator")
    print("  Compressing Tap sessions into ghosts…")
    print("=" * 60)
    print()

    # Generate ghosts
    ghosts = seed_from_docs(args.source)

    if not ghosts:
        print("\n⚠ No ghosts generated. Check source directory.")
        sys.exit(1)

    # Sort by date
    ghosts.sort(key=lambda g: g.get('date', ''), reverse=True)

    # Write output file
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(ghosts, indent=2 if args.pretty else None, ensure_ascii=False),
        encoding='utf-8'
    )

    print()
    print("=" * 60)
    print(f"  ✓ {len(ghosts)} ghosts generated")
    print(f"  ✓ Written to {args.output}")
    print(f"  Total size: {output_path.stat().st_size / 1024:.1f} KB")
    print("=" * 60)

    # Print summary stats
    all_models = set()
    all_themes = set()
    for g in ghosts:
        all_models.update(g.get('models_present', []))
        all_themes.update(g.get('themes', []))

    print()
    print(f"  Unique models across all sessions: {len(all_models)}")
    for m in sorted(all_models):
        print(f"    · {m}")

    print()
    print(f"  Themes detected: {len(all_themes)}")
    for t in sorted(all_themes):
        print(f"    · {t}")

    # Seed via API if requested
    if args.seed_api:
        print()
        print("=" * 60)
        print(f"  Seeding via API: {args.api_url}")
        print("=" * 60)

        success, failures = seed_via_api(ghosts, args.api_url)
        print()
        print(f"  ✓ {success} ghosts seeded")
        if failures:
            print(f"  ✗ {failures} failures")

    print()
    print("  The Ghost Ledger is ready.")
    print("  Every session a ghost. Every ghost a trace.")
    print()


if __name__ == '__main__':
    main()
