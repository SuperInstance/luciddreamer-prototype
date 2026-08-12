"""The Corpus Indexes Itself — morning briefing from the git log.

Runs ``git -C repo_dir log --since <since> --name-only --pretty=format:``
(the git invocation is behind an injectable ``git_runner`` callable so tests
stay offline), filters .md files under the content dirs, pulls titles and
first lines from the index, and renders a markdown briefing with the four
sections from the SPEC: Night's Catch, New Voices, Threads to Pull, Numbers.
"""

from __future__ import annotations

import re
import subprocess
import time
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Callable

from .index import connect, title_from_body

GitRunner = Callable[[list[str]], str]

_RELATIVE_SINCE_RE = re.compile(
    r"^(\d+)\s+(second|minute|hour|day|week)s?\s+ago$", re.IGNORECASE
)
_UNIT_SECONDS = {
    "second": 1,
    "minute": 60,
    "hour": 3600,
    "day": 86400,
    "week": 604800,
}


def default_git_runner(repo_dir: Path) -> GitRunner:
    """git_runner backed by subprocess git.

    A repo with zero commits is treated as an empty log, not an error:
    ``git log`` exits 128 with "fatal: your current branch ... does not
    have any commits yet". Any other git failure still raises
    ``CalledProcessError``.
    """
    def _run(args: list[str]) -> str:
        try:
            proc = subprocess.run(
                ["git", "-C", str(repo_dir), *args],
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            if "does not have any commits yet" in (exc.stderr or ""):
                return ""
            raise
        return proc.stdout

    return _run


def parse_since(since: str, *, now: float | None = None) -> float:
    """Convert a --since spec to a cutoff unix timestamp.

    Accepts "N seconds/minutes/hours/days/weeks ago", ISO dates
    (YYYY-MM-DD), or a raw unix timestamp.
    """
    now = time.time() if now is None else now
    m = _RELATIVE_SINCE_RE.match(since.strip())
    if m:
        return now - int(m.group(1)) * _UNIT_SECONDS[m.group(2).lower()]
    try:
        return datetime.fromisoformat(since.strip()).timestamp()
    except ValueError:
        pass
    try:
        return float(since.strip())
    except ValueError:
        raise ValueError(
            f"cannot parse --since value {since!r}; use e.g. '24 hours ago',"
            " '3 days ago', an ISO date, or a unix timestamp"
        )


def _first_line(body: str) -> str:
    for line in body.splitlines():
        line = line.strip().lstrip("#").strip()
        if line:
            return line[:160]
    return ""


def _changed_md_files(git_runner: GitRunner, since: str,
                      content_dirs: tuple[str, ...]) -> list[str]:
    out = git_runner(["log", "--since", since, "--name-only", "--pretty=format:"])
    paths = []
    for line in out.splitlines():
        line = line.strip()
        if not line or not line.endswith(".md"):
            continue
        top = line.split("/", 1)[0]
        if content_dirs and top not in content_dirs:
            continue
        if line not in paths:
            paths.append(line)
    return paths


def _index_lookup(conn, rel_posix: str, content_dirs: tuple[str, ...]):
    """Find a piece row for a repo-relative git path by stripping the
    content-dir prefix to match the corpus-relative index path."""
    candidates = [rel_posix]
    for cdir in content_dirs:
        prefix = cdir.rstrip("/") + "/"
        if rel_posix.startswith(prefix):
            candidates.append(rel_posix[len(prefix):])
    for cand in candidates:
        row = conn.execute(
            "SELECT path, title, series, directory, persona, mtime, body"
            " FROM pieces WHERE path = ?",
            (cand,),
        ).fetchone()
        if row is not None:
            return row
    return None


def generate_digest(
    repo_dir: Path,
    db_path: Path,
    *,
    since: str = "24 hours ago",
    out_path: Path | None = None,
    git_runner: GitRunner | None = None,
    content_dirs: tuple[str, ...] = ("corpus",),
    now: float | None = None,
) -> str:
    """Build the morning briefing markdown; write it if out_path is given."""
    repo_dir = Path(repo_dir)
    db_path = Path(db_path)
    if git_runner is None:
        git_runner = default_git_runner(repo_dir)
    now = time.time() if now is None else now
    cutoff = parse_since(since, now=now)
    today = date.fromtimestamp(now).isoformat()

    changed = _changed_md_files(git_runner, since, content_dirs)

    conn = connect(db_path) if db_path.exists() else None

    # --- gather new pieces -------------------------------------------------
    new_pieces = []  # dicts: git_path, path, title, persona, directory, first_line
    for git_path in changed:
        row = _index_lookup(conn, git_path, content_dirs) if conn else None
        if row is not None:
            path, title, _series, directory, persona, _mtime, body = row
            first_line = _first_line(body)
        else:
            disk = repo_dir / git_path
            body = (
                disk.read_text(encoding="utf-8", errors="replace")
                if disk.exists()
                else ""
            )
            path = git_path
            title = title_from_body(body, Path(git_path).stem)
            directory = str(Path(git_path).parent)
            persona = None
            first_line = _first_line(body)
        new_pieces.append(
            {
                "git_path": git_path,
                "path": path,
                "title": title,
                "persona": persona,
                "directory": directory,
                "first_line": first_line,
            }
        )

    # --- Night's Catch: new pieces grouped by directory --------------------
    by_dir: dict[str, list[dict]] = defaultdict(list)
    for piece in new_pieces:
        by_dir[piece["directory"] or "."].append(piece)

    # --- New Voices: personas with nothing in the index before the cutoff --
    new_personas = sorted(
        {p["persona"] for p in new_pieces if p["persona"]}
    )
    new_voices: dict[str, list[str]] = {}
    for persona in new_personas:
        prior = 0
        if conn is not None:
            prior = conn.execute(
                "SELECT COUNT(*) FROM pieces WHERE persona = ? AND mtime < ?",
                (persona, cutoff),
            ).fetchone()[0]
        if prior == 0:
            new_voices[persona] = [
                p["title"] for p in new_pieces if p["persona"] == persona
            ]

    # --- Threads to Pull: archive pieces in the new pieces' FTS neighborhood
    threads: list[tuple[float, str, str, str]] = []  # weight, path, title, via
    if conn is not None and new_pieces:
        new_paths = {p["path"] for p in new_pieces}
        scores: dict[str, list] = {}
        for piece in new_pieces:
            tokens = re.findall(r"[a-z0-9]+", piece["title"].lower())
            tokens = [t for t in tokens if len(t) > 3][:6]
            if not tokens:
                continue
            match = " OR ".join(f'"{t}"' for t in tokens)
            try:
                rows = conn.execute(
                    """
                    SELECT p.path, p.title, bm25(pieces_fts) AS rank
                    FROM pieces_fts
                    JOIN pieces p ON p.id = pieces_fts.rowid
                    WHERE pieces_fts MATCH ?
                    ORDER BY rank
                    LIMIT 8
                    """,
                    (match,),
                ).fetchall()
            except Exception:
                continue
            for path, title, rank in rows:
                if path in new_paths:
                    continue
                weight = -rank
                if path in scores:
                    scores[path][0] += weight
                    scores[path][2].append(piece["title"])
                else:
                    scores[path] = [weight, title, [piece["title"]]]
        best = sorted(scores.items(), key=lambda kv: kv[1][0], reverse=True)[:3]
        threads = [
            (w, path, title, via[0]) for path, (w, title, via) in best
        ]

    # --- Numbers -------------------------------------------------------------
    total = 0
    persona_count = 0
    if conn is not None:
        total = conn.execute("SELECT COUNT(*) FROM pieces").fetchone()[0]
        persona_count = conn.execute(
            "SELECT COUNT(DISTINCT persona) FROM pieces WHERE persona IS NOT NULL"
        ).fetchone()[0]
    if conn is not None:
        conn.close()

    # --- render ---------------------------------------------------------------
    lines = [f"# The Corpus Indexes Itself — {today}", ""]
    lines.append(
        f"_Briefing for `{repo_dir.name}` — git log since {since!r}._"
    )
    lines.append("")

    lines.append("## Night's Catch")
    lines.append("")
    if not by_dir:
        lines.append("_Nothing new surfaced overnight._")
    for directory in sorted(by_dir):
        lines.append(f"### {directory}")
        for piece in by_dir[directory]:
            entry = f"- **{piece['title']}** (`{piece['git_path']}`)"
            if piece["first_line"] and piece["first_line"] != piece["title"]:
                entry += f" — {piece['first_line']}"
            lines.append(entry)
        lines.append("")

    lines.append("## New Voices")
    lines.append("")
    if not new_voices:
        lines.append("_No new personas joined the corpus._")
    for persona in sorted(new_voices):
        titles = "; ".join(new_voices[persona])
        lines.append(f"- **{persona}** — {titles}")
    lines.append("")

    lines.append("## Threads to Pull")
    lines.append("")
    if not threads:
        lines.append("_No archive threads overlap the night's catch yet._")
    for _w, path, title, via in threads:
        lines.append(
            f"- **{title}** (`{path}`) — its FTS neighborhood overlaps"
            f" the new “{via}”"
        )
    lines.append("")

    lines.append("## Numbers")
    lines.append("")
    lines.append(f"- New pieces: {len(new_pieces)}")
    lines.append(f"- Directories touched: {len(by_dir)}")
    lines.append(f"- New voices: {len(new_voices)}")
    lines.append(f"- Threads to pull: {len(threads)}")
    lines.append(f"- Total pieces in index: {total}")
    lines.append(f"- Distinct personas in index: {persona_count}")
    lines.append("")

    markdown = "\n".join(lines)
    if out_path is not None:
        Path(out_path).write_text(markdown, encoding="utf-8")
    return markdown
