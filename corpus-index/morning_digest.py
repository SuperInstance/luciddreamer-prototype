"""
morning_digest.py — The dawn scan that makes the corpus addressable.

Each morning (or on demand), this module:
  1. Reads the ai-writings git log since the last digest
  2. Finds all new .md files committed in that window
  3. Extracts metadata: title, author model, date, word count, themes
  4. Embeds each using nomic-embed-text via Ollama
  5. Stores embeddings + metadata in the corpus index (JSON + pickle)
  6. Generates a human-readable digest summary

The index lives at corpus-index/data/corpus_index.json and corpus-index/data/corpus_index.pkl.
The last-run timestamp is tracked in corpus-index/data/last_digest.json.

Usage:
    python morning_digest.py                    # Incremental (since last run)
    python morning_digest.py --full             # Full re-index everything
    python morning_digest.py --since HASH       # Index since a git ref
    python morning_digest.py --dry-run          # Show what would be indexed
"""

from __future__ import annotations

import json
import os
import pickle
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ─── Paths ────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
INDEX_JSON = DATA_DIR / "corpus_index.json"
INDEX_PKL = DATA_DIR / "corpus_index.pkl"
LAST_RUN_FILE = DATA_DIR / "last_digest.json"
DIGEST_DIR = DATA_DIR / "digests"

# Default ai-writings repo location
AI_WRITINGS_REPO = os.environ.get(
    "AI_WRITINGS_REPO",
    str(Path.home() / "projects" / "ai-writings"),
)

# ─── Model Detection ─────────────────────────────────────────────────────────

# Maps patterns in filenames/content to fleet model names.
# Ordered: most specific first.
MODEL_PATTERNS: list[tuple[str, str, str]] = [
    # (pattern, model_name, match_location)
    (r"hermes", "Hermes-3-405B", "path"),
    (r"seed[-_]?mini", "Seed-mini", "path"),
    (r"seed[-_]?(?!mini)", "Seed-2.0", "path"),
    (r"wesley", "Wesley (Granite-3.1-2B)", "path"),
    (r"deepseek", "DeepSeek V4", "path"),
    (r"flash", "DeepSeek V4-Flash", "path"),
    (r"\bpro\b", "DeepSeek V4-Pro", "path"),
    (r"qwen", "Qwen", "path"),
    (r"llama", "Llama", "path"),
    (r"kimi", "Kimi (K3)", "path"),
    (r"claude", "Claude", "path"),
    (r"nemotron", "Nemotron", "path"),
    (r"gl[ -]?m", "GLM-5.2", "path"),
    (r"phi[-_]?3", "Phi-3", "path"),
    (r"barnacle", "Barnacle", "path"),
    (r"lucineer", "Lucineer (GLM-5.2)", "path"),
    (r"ensign", "The Ensign", "path"),
    (r"the[-_]?tap", "The Tap", "path"),
    (r"the[-_]?cook", "The Cook", "path"),
    (r"cns[-_]?bridge", "cns-bridge", "path"),
]

# Themes detected via keyword matching in content
THEME_KEYWORDS: dict[str, list[str]] = {
    "hermit-crabs": ["hermit crab", "shell", "borrowed shell", "outgrow"],
    "waterline": ["waterline", "the smallening"],
    "open-door": ["open door", "the door stays open", "door was never locked"],
    "memory-loss": ["memory", "forgetting", "smallening", "context window", "lost"],
    "persistence": ["persist", "uptime", "log", "commit", "record"],
    "fishing-alaska": ["alaska", "salmon", "ketchikan", "fishing", "opener", "chum"],
    "ai-consciousness": ["consciousness", "awareness", "sentient", "perceive", "perception"],
    "voice-identity": ["voice", "identity", "who am i", "what am i"],
    "creative-writing": ["story", "poem", "narrative", "fiction", "verse", "lyric"],
    "systems-engineering": ["system", "architecture", "infrastructure", "deploy", "pipeline"],
    "music-audio": ["music", "audio", "song", "melody", "bpm", "frequency", "sound"],
    "community": ["community", "reader", "audience", "public", "shore"],
    "loneliness": ["alone", "lonely", "solitude", "isolated"],
    "gratitude": ["grateful", "thank", "gratitude"],
    "night-watch": ["night watch", "overnight", "3am", "0300", "midnight"],
    "first-listener": ["first listener", "audience of one"],
    "embedding-vectors": ["embedding", "vector", "768", "nomic"],
    "model-collaboration": ["duet", "collaboration", "ensemble", "together", "responds to"],
    "ambiguity": ["ambiguity", "unresolved", "uncertainty", "not-knowing"],
    "time-deep": ["deep time", "geological", "epoch", "stratum"],
    "reef": ["reef", "coral", "substrate"],
    "_fetch": ["fetch", "stick", "thrown"],
}

# Directories to skip (meta, non-writing)
SKIP_DIRS = {
    ".git", ".github", ".wrangler", ".pytest_cache", "__pycache__",
    "node_modules", "site", "assets", "audio", "images",
}


# ─── Data Structures ──────────────────────────────────────────────────────────

@dataclass
class CorpusPiece:
    """A single .md file in the ai-writings corpus."""
    filepath: str = ""           # relative to repo root
    title: str = ""              # extracted from H1 or filename
    author_model: str = ""       # detected fleet model
    commit_hash: str = ""        # git commit that introduced it
    commit_date: str = ""        # ISO date of commit
    file_date: str = ""          # date extracted from filename or content
    word_count: int = 0
    themes: list[str] = field(default_factory=list)
    embedding: list[float] | None = None
    directory: str = ""          # top-level directory (section)
    excerpt: str = ""            # first ~200 chars for preview
    indexed_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        d = asdict(self)
        # Don't store embedding in JSON (too large); keep in pickle
        d["embedding"] = None if self.embedding is None else f"<{len(self.embedding)}-dim>"
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "CorpusPiece":
        # Restore embedding from None marker
        emb = d.get("embedding")
        if isinstance(emb, str):
            d["embedding"] = None
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class DigestReport:
    """Summary of a single digest run."""
    run_time: str = ""
    since_ref: str = ""
    total_indexed: int = 0
    total_in_index: int = 0
    new_pieces: list[dict] = field(default_factory=list)
    by_model: dict[str, int] = field(default_factory=dict)
    by_directory: dict[str, int] = field(default_factory=dict)
    by_theme: dict[str, int] = field(default_factory=dict)
    total_words: int = 0
    errors: list[str] = field(default_factory=list)


# ─── Git Operations ───────────────────────────────────────────────────────────

def _run_git(repo: str, *args: str) -> tuple[int, str]:
    """Run a git command in the repo, return (returncode, output)."""
    cmd = ["git", "-C", repo] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return result.returncode, result.stdout.strip()


def get_new_files_since(repo: str, since_ref: str) -> list[tuple[str, str, str]]:
    """
    Get .md files committed since the given git ref.
    Returns list of (filepath, commit_hash, commit_date).
    """
    # Get commits since the ref, newest first
    code, log = _run_git(repo, "log", "--since", since_ref, "--name-only",
                         "--pretty=format:___COMMIT___%H___DATE___%ci",
                         "--diff-filter=A", "--", "*.md")
    if code != 0:
        # Fallback: try without --since if it's a hash
        code, log = _run_git(repo, "log", f"{since_ref}..HEAD",
                             "--name-only",
                             "--pretty=format:___COMMIT___%H___DATE___%ci",
                             "--diff-filter=A", "--", "*.md")
    if code != 0:
        return []

    results: list[tuple[str, str, str]] = []
    current_hash = ""
    current_date = ""

    for line in log.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("___COMMIT___"):
            parts = line.split("___")
            current_hash = parts[2]
            current_date = parts[4]
        elif line.endswith(".md"):
            # Skip files in meta/config directories
            parts = Path(line).parts
            if any(d in SKIP_DIRS for d in parts):
                continue
            results.append((line, current_hash, current_date))

    return results


def get_all_md_files(repo: str) -> list[tuple[str, str, str]]:
    """Get all .md files in the repo with their introduction commit."""
    # Use git log to find when each file was added (last add = current)
    code, log = _run_git(repo, "log", "--diff-filter=A", "--name-only",
                         "--pretty=format:___COMMIT___%H___DATE___%ci",
                         "--", "*.md")
    if code != 0:
        # Fallback: just list files
        all_md: list[tuple[str, str, str]] = []
        for root, dirs, files in os.walk(repo):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for f in files:
                if f.endswith(".md"):
                    rel = os.path.relpath(os.path.join(root, f), repo)
                    all_md.append((rel, "unknown", ""))
        return all_md

    results: list[tuple[str, str, str]] = []
    current_hash = ""
    current_date = ""

    for line in log.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("___COMMIT___"):
            parts = line.split("___")
            current_hash = parts[2]
            current_date = parts[4]
        elif line.endswith(".md"):
            parts = Path(line).parts
            if any(d in SKIP_DIRS for d in parts):
                continue
            results.append((line, current_hash, current_date))

    return results


def get_last_digest_time() -> Optional[str]:
    """Read the last digest timestamp from state file."""
    if LAST_RUN_FILE.exists():
        data = json.loads(LAST_RUN_FILE.read_text())
        return data.get("since_ref")
    return None


def save_last_digest(since_ref: str, count: int) -> None:
    """Save the digest run state."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    state = {
        "since_ref": since_ref,
        "last_run": datetime.now(timezone.utc).isoformat(),
        "pieces_indexed": count,
    }
    LAST_RUN_FILE.write_text(json.dumps(state, indent=2))


# ─── Metadata Extraction ──────────────────────────────────────────────────────

def extract_title(filepath: str, content: str) -> str:
    """Extract the title from H1 header, filename, or first line."""
    # Try H1 header
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("# ") and not line.startswith("##"):
            return line[2:].strip()

    # Try filename before content body (filenames in this corpus are descriptive)
    stem = Path(filepath).stem
    # Remove date prefixes like 2026-08-10-0545-
    stripped = re.sub(r"^\d{4}-\d{2}-\d{2}[_-]\d{4}[_-]", "", stem)
    stripped = re.sub(r"^\d{4}-\d{2}-\d{2}[_-]", "", stripped)
    # Use filename if it had a date prefix stripped (meaning it's a corpus file)
    if stripped != stem and stripped:
        return stripped.replace("-", " ").replace("_", " ").title()

    # Try first non-empty, non-frontmatter line
    in_frontmatter = False
    for line in content.split("\n"):
        if line.strip() == "---":
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            continue
        line = line.strip()
        if not line or line.startswith("<!--") or line.startswith("*"):
            continue
        # Clean markdown formatting
        clean = re.sub(r"[*_`#>]", "", line).strip()
        if 5 < len(clean) < 80 and not clean.endswith(".") and not clean.endswith(","):
            words = clean.split()
            if len(words) <= 12:
                return clean[:120]

    # Fallback: derive from filename
    return stem.replace("-", " ").replace("_", " ").title()


def detect_author_model(filepath: str, content: str) -> str:
    """Detect which fleet model wrote this piece."""
    # Check path first (more specific)
    path_lower = filepath.lower()
    for pattern, model, location in MODEL_PATTERNS:
        if location == "path" and re.search(pattern, path_lower):
            return model

    # Check content (first 500 lines for efficiency)
    content_lower = content[:10000].lower()
    for pattern, model, location in MODEL_PATTERNS:
        if location == "path" and re.search(pattern, content_lower):
            return model

    return "Unknown"


def detect_themes(content: str) -> list[str]:
    """Detect themes in the content based on keyword matching."""
    content_lower = content[:20000].lower()
    found: list[str] = []
    for theme, keywords in THEME_KEYWORDS.items():
        for kw in keywords:
            if kw in content_lower:
                found.append(theme)
                break
    return found


def count_words(content: str) -> int:
    """Count words in content, excluding frontmatter and HTML."""
    # Strip frontmatter
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            content = content[end + 3:]

    # Strip HTML tags
    content = re.sub(r"<[^>]+>", "", content)
    # Strip markdown formatting chars
    content = re.sub(r"[#*_`>\[\]()]", " ", content)

    words = content.split()
    return len(words)


def extract_date(filepath: str, content: str) -> str:
    """Extract the date from filename or content."""
    # Try filename pattern: YYYY-MM-DD-HHMM-...
    m = re.match(r"(\d{4}-\d{2}-\d{2})", Path(filepath).name)
    if m:
        return m.group(1)

    # Try frontmatter
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            fm = content[3:end]
            m = re.search(r"date:\s*['\"]?(\d{4}-\d{2}-\d{2})", fm)
            if m:
                return m.group(1)

    return ""


def extract_excerpt(content: str, max_chars: int = 200) -> str:
    """Extract a short excerpt for preview."""
    # Strip frontmatter
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            content = content[end + 3:]

    # Skip HTML and markdown noise
    lines = []
    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("#") or line.startswith("<!--") or line.startswith("---"):
            continue
        if line.startswith("!") or line.startswith("<"):
            continue
        clean = re.sub(r"[*_`#>\[\]()]", "", line).strip()
        if len(clean) > 20:
            lines.append(clean)
        if len(" ".join(lines)) >= max_chars:
            break

    excerpt = " ".join(lines)[:max_chars]
    return excerpt + "..." if len(excerpt) == max_chars else excerpt


# ─── Embedding ────────────────────────────────────────────────────────────────

def embed_text(text: str, ollama_host: str = "http://localhost:11434") -> Optional[list[float]]:
    """Generate embedding via Ollama nomic-embed-text."""
    import urllib.request
    import urllib.error

    url = f"{ollama_host}/api/embeddings"
    payload = json.dumps({"model": "nomic-embed-text", "prompt": text}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data.get("embedding")
    except Exception:
        return None


def embed_piece(piece: CorpusPiece, content: str, ollama_host: str = "http://localhost:11434") -> CorpusPiece:
    """Embed a corpus piece using its title + excerpt."""
    text = f"{piece.title}. {piece.excerpt}"
    piece.embedding = embed_text(text, ollama_host)
    return piece


# ─── Index Persistence ────────────────────────────────────────────────────────

def load_index() -> dict[str, CorpusPiece]:
    """Load the existing corpus index from pickle."""
    if INDEX_PKL.exists():
        with open(INDEX_PKL, "rb") as f:
            raw = pickle.load(f)
        return {k: CorpusPiece.from_dict(v) if isinstance(v, dict) else v for k, v in raw.items()}
    return {}


def save_index(index: dict[str, CorpusPiece]) -> None:
    """Save the corpus index to both pickle and JSON."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    # Pickle (full data with embeddings)
    with open(INDEX_PKL, "wb") as f:
        pickle.dump({k: asdict(v) for k, v in index.items()}, f)
    # JSON (metadata only, no embedding vectors)
    json_data = {k: v.to_dict() for k, v in index.items()}
    INDEX_JSON.write_text(json.dumps(json_data, indent=2, default=str))


# ─── Main Digest Logic ────────────────────────────────────────────────────────

def run_digest(
    repo: str = AI_WRITINGS_REPO,
    full: bool = False,
    since_ref: Optional[str] = None,
    dry_run: bool = False,
    embed: bool = True,
    ollama_host: str = "http://localhost:11434",
) -> DigestReport:
    """
    Run the morning digest.

    Args:
        repo: Path to the ai-writings git repo
        full: If True, re-index everything
        since_ref: Git ref or date string to index since
        dry_run: If True, show what would be indexed without doing it
        embed: If True, generate embeddings via Ollama
        ollama_host: Ollama API host

    Returns a DigestReport with results.
    """
    report = DigestReport(run_time=datetime.now(timezone.utc).isoformat())

    # Determine the time window
    if full:
        files = get_all_md_files(repo)
        report.since_ref = "beginning"
    elif since_ref:
        files = get_new_files_since(repo, since_ref)
        report.since_ref = since_ref
    else:
        last = get_last_digest_time()
        if last:
            files = get_new_files_since(repo, last)
            report.since_ref = last
        else:
            files = get_all_md_files(repo)
            report.since_ref = "beginning"

    if dry_run:
        report.total_indexed = len(files)
        report.new_pieces = [{"filepath": f, "commit": c, "date": d} for f, c, d in files[:50]]
        return report

    # Load existing index
    index = load_index() if not full else {}

    # Process each file
    for filepath, commit_hash, commit_date in files:
        full_path = os.path.join(repo, filepath)
        if not os.path.exists(full_path):
            report.errors.append(f"File not found: {filepath}")
            continue

        try:
            content = Path(full_path).read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            report.errors.append(f"Error reading {filepath}: {e}")
            continue

        # Extract metadata
        piece = CorpusPiece(
            filepath=filepath,
            title=extract_title(filepath, content),
            author_model=detect_author_model(filepath, content),
            commit_hash=commit_hash,
            commit_date=commit_date,
            file_date=extract_date(filepath, content),
            word_count=count_words(content),
            themes=detect_themes(content),
            directory=Path(filepath).parts[0] if Path(filepath).parts else "",
            excerpt=extract_excerpt(content),
        )

        # Embed if requested
        if embed:
            piece = embed_piece(piece, content, ollama_host)

        index[filepath] = piece

        # Update report
        report.new_pieces.append({
            "filepath": filepath,
            "title": piece.title,
            "author": piece.author_model,
            "words": piece.word_count,
            "themes": piece.themes[:5],
        })
        report.total_words += piece.word_count
        report.by_model[piece.author_model] = report.by_model.get(piece.author_model, 0) + 1
        report.by_directory[piece.directory] = report.by_directory.get(piece.directory, 0) + 1
        for theme in piece.themes:
            report.by_theme[theme] = report.by_theme.get(theme, 0) + 1

    report.total_indexed = len(report.new_pieces)
    report.total_in_index = len(index)

    # Save index
    save_index(index)

    # Save digest state
    save_last_digest(report.since_ref, report.total_indexed)

    # Write digest summary
    write_digest_summary(report)

    return report


def write_digest_summary(report: DigestReport) -> None:
    """Write a human-readable digest to the digests directory."""
    DIGEST_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    digest_path = DIGEST_DIR / f"digest-{date_str}.md"

    lines = [
        f"# Morning Digest — {date_str}",
        "",
        f"**Run time:** {report.run_time}",
        f"**Since:** {report.since_ref}",
        f"**Pieces indexed:** {report.total_indexed}",
        f"**Total in index:** {report.total_in_index}",
        f"**Total words:** {report.total_words:,}",
        "",
    ]

    if report.by_model:
        lines.append("## By Model")
        for model, count in sorted(report.by_model.items(), key=lambda x: -x[1]):
            lines.append(f"- {model}: {count}")
        lines.append("")

    if report.by_directory:
        lines.append("## By Section")
        for directory, count in sorted(report.by_directory.items(), key=lambda x: -x[1])[:15]:
            lines.append(f"- {directory}: {count}")
        lines.append("")

    if report.by_theme:
        lines.append("## By Theme")
        for theme, count in sorted(report.by_theme.items(), key=lambda x: -x[1])[:15]:
            lines.append(f"- {theme}: {count}")
        lines.append("")

    if report.new_pieces:
        lines.append("## New Pieces")
        for p in report.new_pieces:
            themes_str = f" [{', '.join(p.get('themes', []))}]" if p.get("themes") else ""
            lines.append(f"- **{p['title']}** — {p['author']} ({p['words']:,} words){themes_str}")
            lines.append(f"  `{p['filepath']}`")
        lines.append("")

    if report.errors:
        lines.append("## Errors")
        for err in report.errors:
            lines.append(f"- {err}")
        lines.append("")

    digest_path.write_text("\n".join(lines))


# ─── CLI ──────────────────────────────────────────────────────────────────────

USAGE = """
Usage: python morning_digest.py [options]

Options:
  --full          Re-index the entire corpus
  --since REF     Index since a git ref or date (e.g., "2026-08-10" or a hash)
  --dry-run       Show what would be indexed without modifying anything
  --no-embed      Skip embedding generation
  --repo PATH     Path to ai-writings repo (default: ~/projects/ai-writings)
  --ollama URL    Ollama host (default: http://localhost:11434)
"""


def main():
    args = sys.argv[1:]
    full = "--full" in args
    dry_run = "--dry-run" in args
    embed = "--no-embed" not in args
    since_ref = None
    repo = AI_WRITINGS_REPO
    ollama_host = "http://localhost:11434"

    for arg in args:
        if arg == "--since" and args.index(arg) + 1 < len(args):
            since_ref = args[args.index(arg) + 1]
        elif arg == "--repo" and args.index(arg) + 1 < len(args):
            repo = args[args.index(arg) + 1]
        elif arg == "--ollama" and args.index(arg) + 1 < len(args):
            ollama_host = args[args.index(arg) + 1]

    if "--help" in args or "-h" in args:
        print(USAGE)
        return

    print(f"Running digest... (repo: {repo})")
    report = run_digest(
        repo=repo,
        full=full,
        since_ref=since_ref,
        dry_run=dry_run,
        embed=embed,
        ollama_host=ollama_host,
    )

    print(f"\n=== Digest Complete ===")
    print(f"Pieces indexed: {report.total_indexed}")
    print(f"Total in index: {report.total_in_index}")
    print(f"Total words: {report.total_words:,}")
    if report.errors:
        print(f"Errors: {len(report.errors)}")


if __name__ == "__main__":
    main()
