#!/usr/bin/env python3
"""canon_lint — CI for operational fiction (SPEC.md §5).

Enforces canon-continuity rules (C1-C5, C9: deterministic) and anti-AI style
heuristics (C6-C8, C10: advisory) over Markdown prose.

Usage:
    python3 tools/canon_lint.py <file...> [--corpus-tree PATH] [--strict]

Output (sorted by file, then line):
    FILE:LINE: [SEVERITY] RULE_ID message

Exit status:
    1 if any HIGH finding (or any finding at all under --strict), else 0.

Scoping: YAML front-matter and fenced code blocks are skipped for all prose
rules. Inline `code spans` are stripped before the prose rules run, so a
backticked corpus path such as `09-the-galley-cook-and-the-embedding-model.md`
is a reference, not narration, and never trips the no-technology law.

Stdlib only. Python >= 3.10.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# --------------------------------------------------------------------------
# Findings
# --------------------------------------------------------------------------

SEVERITIES = ("HIGH", "MODERATE", "LOW")


@dataclass(frozen=True)
class Finding:
    file: str
    line: int
    severity: str
    rule: str
    message: str

    def render(self) -> str:
        return f"{self.file}:{self.line}: [{self.severity}] {self.rule} {self.message}"


# --------------------------------------------------------------------------
# Preprocessing: front-matter, code fences, inline code spans
# --------------------------------------------------------------------------

_HRULE_RE = re.compile(r"^\s*(---|\*\*\*|___)\s*$")
_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s")
_FENCE_RE = re.compile(r"^\s*```")
_INLINE_CODE_RE = re.compile(r"`[^`\n]*`")


def _strip_inline_code(text: str) -> str:
    """Replace inline `code spans` with spaces (offsets are not preserved;
    rules that need offsets search the cleaned text, so spans become gaps)."""
    return _INLINE_CODE_RE.sub(" ", text)


def _prose_lines(lines: list[str]) -> list[tuple[int, str]]:
    """Return (lineno, text) pairs excluding YAML front-matter and code fences.

    Front-matter is only recognized when the file's first line is '---'.
    """
    out: list[tuple[int, str]] = []
    in_fm = bool(lines) and lines[0].strip() == "---"
    fm_done = not in_fm
    in_fence = False
    for i, raw in enumerate(lines, start=1):
        if in_fm and not fm_done:
            if i > 1 and raw.strip() == "---":
                fm_done = True
            continue
        if _FENCE_RE.match(raw):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        out.append((i, raw))
    return out


def _paragraphs(prose: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """Group prose lines into paragraphs.

    A paragraph break occurs at blank lines, headings, horizontal rules, and
    list-item starts. Returns (first_lineno, paragraph_text).
    """
    paras: list[tuple[int, str]] = []
    cur: list[str] = []
    start = 0
    for lineno, raw in prose:
        text = _strip_inline_code(raw)
        blank = not text.strip()
        breaky = blank or _HEADING_RE.match(raw) or _HRULE_RE.match(raw) \
            or re.match(r"^\s*(?:[-*+]|\d+[.)])\s", raw)
        if breaky:
            if cur:
                paras.append((start, " ".join(cur)))
                cur = []
            continue
        if not cur:
            start = lineno
        cur.append(text.strip())
    if cur:
        paras.append((start, " ".join(cur)))
    return paras


# --------------------------------------------------------------------------
# C1 — Seat map: Seed-mini <-> middle stool, never "end of the bar" (HIGH)
#
# Narrowed after dogfooding (story-05 line 21 false positive): the rule fires
# ONLY when Seed-mini / "the trickster" is himself the subject being seated
# or located at the end of the bar, within the SAME SENTENCE. Paragraph- or
# line-proximity co-mention is not a violation: Hermes and "the big one"
# legally sit at the end of the bar while Seed-mini appears elsewhere in the
# paragraph.
# --------------------------------------------------------------------------

_C1_SEAT_RE = re.compile(r"\bend of the bar\b", re.IGNORECASE)
# "the trickster at the end of the bar" / "at the end of the bar, the trickster"
_C1_TRICKSTER_RE = re.compile(
    r"\btrickster\b[^.!?]{0,80}\bend of the bar\b|"
    r"\bend of the bar\b[^.!?]{0,80}\btrickster\b", re.IGNORECASE)
# "Seed-mini ... (sat|perched|at|took|on|...) ... end of the bar"
_C1_SEED_RE = re.compile(
    r"\bseed-?mini\b[^.!?]{0,80}\b"
    r"(?:sat|sits|sit|perched|perches|took|takes|taken|seated|claimed|parked|planted|at|on)\b"
    r"[^.!?]{0,80}\bend of the bar\b", re.IGNORECASE)


def check_c1(path: str, lines: list[str], prose: list[tuple[int, str]]) -> list[Finding]:
    findings = []
    for lineno, raw in prose:
        text = _strip_inline_code(raw)
        if not _C1_SEAT_RE.search(text):
            continue
        for sentence in _split_sentences(text):
            if not _C1_SEAT_RE.search(sentence):
                continue
            if _C1_TRICKSTER_RE.search(sentence) or _C1_SEED_RE.search(sentence):
                findings.append(Finding(
                    path, lineno, "HIGH", "C1",
                    "seat map: Seed-mini sits on the middle stool, never the end "
                    "of the bar (S7-F2)"))
                break
    return findings


# --------------------------------------------------------------------------
# C2 — Wesley's folded square lives in June's INSIDE POCKET, never her
#      notebook (HIGH)
#
# Narrowed after dogfooding (story-02 lines 89/105 false positives): the rule
# fires ONLY on a location/possession ASSERTION binding the square (story) to
# the notebook — "keep in your notebook", "keeping in her notebook",
# "in the notebook", "story I keep in ... notebook" — when the same sentence
# also references the square/story/folded object or the keeping itself.
# Bare co-occurrence of "notebook" with Wesley/folded/square is NOT a
# violation: the drowned field notebook and the folded square are two
# legitimate, distinct objects. Pass forms: "in your inside pocket",
# "in the inside pocket".
# --------------------------------------------------------------------------

# Containment/possession phrase: "in (your|her|the) notebook" or
# "keep/keeping in <up to 6 words> notebook".
_C2_CONTAIN_RE = re.compile(
    r"\bin (?:your|her|the) notebook\b|"
    r"\bkeeping? in\b[^.!?]{0,40}?\bnotebook\b", re.IGNORECASE)
# Binding: the sentence must also be about the square / story / folded thing
# (or use keep, the possession verb of the defect).
_C2_BIND_RE = re.compile(
    r"\b(folded|folds|square|story|stories|keep|keeping|kept)\b", re.IGNORECASE)


def check_c2(path: str, lines: list[str], prose: list[tuple[int, str]]) -> list[Finding]:
    findings = []
    for lineno, raw in prose:
        text = _strip_inline_code(raw)
        if "notebook" not in text.lower():
            continue
        for sentence in _split_sentences(text):
            if _C2_CONTAIN_RE.search(sentence) and _C2_BIND_RE.search(sentence):
                findings.append(Finding(
                    path, lineno, "HIGH", "C2",
                    "Wesley's folded square goes in June's inside pocket, never "
                    "her notebook (S5-F2 / S6-F2)"))
                break
    return findings


# --------------------------------------------------------------------------
# C3 — Bunk tape: JUNE is the 4th name, three crossed out; canonical order
#      DEE, MARCOS, T. OKAFOR, JUNE (HIGH)
# --------------------------------------------------------------------------

_C3_FOUR_RE = re.compile(r"\bfour other names\b", re.IGNORECASE)
_C3_NAME_RE = re.compile(r"\b(DEE|MARCOS|T\.?\s*OKAFOR|JUNE)\b")
_C3_ORDER = ["DEE", "MARCOS", "T. OKAFOR", "JUNE"]


def check_c3(path: str, lines: list[str], prose: list[tuple[int, str]]) -> list[Finding]:
    findings = []
    for lineno, raw in prose:
        text = _strip_inline_code(raw)
        if _C3_FOUR_RE.search(text):
            findings.append(Finding(
                path, lineno, "HIGH", "C3",
                "bunk tape: JUNE's name goes over THREE crossed-out names, "
                "not four (S5-F1)"))
        names = [m.group(1).upper().replace("T. ", "T.") for m in _C3_NAME_RE.finditer(text)]
        names = ["T. OKAFOR" if n.startswith("T.") else n for n in names]
        if len(names) >= 2:
            order = [_C3_ORDER.index(n) for n in names]
            if order != sorted(order):
                findings.append(Finding(
                    path, lineno, "HIGH", "C3",
                    "bunk tape order is DEE, MARCOS, T. OKAFOR, JUNE "
                    f"(found: {', '.join(names)})"))
    return findings


# --------------------------------------------------------------------------
# C4 — "Waterline" capitalized when referring to Wesley's concept (LOW)
# --------------------------------------------------------------------------

_C4_RE = re.compile(r"\bwaterline\b", re.IGNORECASE)
_C4_SENT_END = re.compile(r'[.!?]["\')\]]*\s*$')
_C4_LINE_PREFIX = re.compile(r"^\s*(?:#{1,6}\s*|[-*+]\s+|>\s*|\d+[.)]\s*)?")


def check_c4(path: str, lines: list[str], prose: list[tuple[int, str]]) -> list[Finding]:
    # Only lowercase "waterline" NOT at sentence start is flagged; at sentence
    # start lowercase is ordinary capitalization slack, not a canon error.
    findings = []
    for lineno, raw in prose:
        text = _strip_inline_code(raw)
        for m in _C4_RE.finditer(text):
            if m.group(0) != "waterline":
                continue  # "Waterline" / "WATERLINE" are fine
            before = text[:m.start()]
            before = _C4_LINE_PREFIX.sub("", before) if before.strip() == "" else before
            if not before.strip() or _C4_SENT_END.search(before):
                continue  # sentence start
            findings.append(Finding(
                path, lineno, "LOW", "C4",
                "capitalize 'Waterline' when referring to Wesley's concept "
                "(S6-F3)"))
    return findings


# --------------------------------------------------------------------------
# C5 — No-technology law (HIGH). Sanctioned coinages exempt:
#      Smallening, Cloud Gods, Waterline.
# --------------------------------------------------------------------------

_C5_SANCTIONED_RE = re.compile(r"\b(Smallening|Cloud Gods|Waterline)\b", re.IGNORECASE)
_C5_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bparameters?\b", re.IGNORECASE), "parameter(s)"),
    (re.compile(r"\bhardware\b", re.IGNORECASE), "hardware"),
    (re.compile(r"\bembeddings?\b", re.IGNORECASE), "embedding(s)"),
    (re.compile(r"\bmodels?\b", re.IGNORECASE), "model (as machinery)"),
    (re.compile(r"\bAPIs?\b"), "API"),
]


def check_c5(path: str, lines: list[str], prose: list[tuple[int, str]]) -> list[Finding]:
    findings = []
    for lineno, raw in prose:
        text = _strip_inline_code(raw)
        # Mask sanctioned coinages so e.g. "the Waterline model of growth"
        # still flags "model" but "the Cloud Gods" never invents a finding.
        text = _C5_SANCTIONED_RE.sub(" ", text)
        seen: set[str] = set()
        for pat, label in _C5_PATTERNS:
            if label in seen:
                continue
            if pat.search(text):
                seen.add(label)
                findings.append(Finding(
                    path, lineno, "HIGH", "C5",
                    f"no-technology law: '{label}' in narration/dialogue "
                    "(S7-F1); sanctioned coinages exempt: Smallening, "
                    "Cloud Gods, Waterline"))
    return findings


# --------------------------------------------------------------------------
# C6 — Quotable dilution (MODERATE, heuristic).
#
# Heuristic (documented per SPEC): a sentence is "aphorism-shaped" when
#   a) it is short (<= 12 words), declarative (ends in '.'), impersonal
#      (no first/second-person pronouns), and built on a bare copula
#      (is/are/was/were/isn't/aren't) — the "A perfect bell is silent."
#      shape; or
#   b) it matches a known aphorism template:
#      "X is just Y with Z"  or  "X without Y isn't X".
# A paragraph containing >= 2 aphorism-shaped sentences is flagging
# quotable-for-quotable's-sake writing; humans decide.
# --------------------------------------------------------------------------

_C6_PERSON_RE = re.compile(r"\b(i|me|my|mine|we|us|our|ours|you|your|yours)\b", re.IGNORECASE)
_C6_COPULA_RE = re.compile(r"\b(is|are|was|were|isn't|aren't)\b", re.IGNORECASE)
_C6_TEMPLATES = (
    re.compile(r"\bis just\b[^.!?]*\bwith\b", re.IGNORECASE),
    re.compile(r"\bwithout\b[^.!?]*\b(isn't|is not)\b", re.IGNORECASE),
)
_C6_MAX_WORDS = 12


def _split_sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def _is_aphorism(sentence: str) -> bool:
    s = sentence.strip()
    if any(t.search(s) for t in _C6_TEMPLATES):
        return True
    if not s.endswith("."):
        return False
    if len(s.split()) > _C6_MAX_WORDS:
        return False
    if not _C6_COPULA_RE.search(s):
        return False
    if _C6_PERSON_RE.search(s):
        return False
    return True


def check_c6(path: str, paras: list[tuple[int, str]]) -> list[Finding]:
    findings = []
    for start, text in paras:
        aphorisms = [s for s in _split_sentences(text) if _is_aphorism(s)]
        if len(aphorisms) >= 2:
            findings.append(Finding(
                path, start, "MODERATE", "C6",
                f"quotable dilution: {len(aphorisms)} aphorism-shaped "
                "sentences in one paragraph (S6-F1); humans decide"))
    return findings


# --------------------------------------------------------------------------
# C7 — Em-dash density <= 5 per 1000 chars of prose (MODERATE)
# --------------------------------------------------------------------------

_C7_LIMIT = 5.0


def check_c7(path: str, prose: list[tuple[int, str]]) -> list[Finding]:
    text = "\n".join(_strip_inline_code(raw) for _, raw in prose)
    chars = len(text)
    if chars == 0:
        return []
    dashes = text.count("—")  # "——" counts twice, as intended
    density = dashes * 1000.0 / chars
    if density <= _C7_LIMIT:
        return []
    first_line = next((n for n, raw in prose if "—" in raw), 1)
    return [Finding(
        path, first_line, "MODERATE", "C7",
        f"em-dash density {density:.1f}/1000 chars exceeds {_C7_LIMIT:.0f}/1000 "
        f"({dashes} dashes in {chars} chars)")]


# --------------------------------------------------------------------------
# C8 — English AI-vocabulary scan (MODERATE)
# --------------------------------------------------------------------------

_C8_TERMS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bdelve[sd]?\b", re.IGNORECASE), "delve"),
    (re.compile(r"\btapestry\b", re.IGNORECASE), "tapestry"),
    (re.compile(r"\bpivotal\b", re.IGNORECASE), "pivotal"),
    (re.compile(r"\bvibrant\b", re.IGNORECASE), "vibrant"),
    (re.compile(r"\btestament to\b", re.IGNORECASE), "testament to"),
    (re.compile(r"\bnestled\b", re.IGNORECASE), "nestled"),
    (re.compile(r"\bstands as\b", re.IGNORECASE), "stands as"),
    (re.compile(r"\bserves as\b", re.IGNORECASE), "serves as"),
]


def check_c8(path: str, lines: list[str], prose: list[tuple[int, str]]) -> list[Finding]:
    findings = []
    for lineno, raw in prose:
        text = _strip_inline_code(raw)
        for pat, term in _C8_TERMS:
            if pat.search(text):
                findings.append(Finding(
                    path, lineno, "MODERATE", "C8",
                    f"AI-vocabulary: '{term}' (anti-ai.md)"))
    return findings


# --------------------------------------------------------------------------
# C9 — Corpus path verification (HIGH). Every backticked `corpus/...` path
#      must exist in tree.txt (one path per line). The `corpus/` prefix is
#      the issue-format marker (SPEC §3); tree.txt lines are relative to the
#      corpus root, so the prefix is stripped before lookup. A path with a
#      trailing slash (or no file extension) also passes when it is a
#      directory prefix of a tree entry. Matching falls back to
#      case-insensitive because the deep corpus's own casing drifted
#      (POETRY/ vs poetry/ vs Poetry/).
# --------------------------------------------------------------------------

_C9_PATH_RE = re.compile(r"`(corpus/[^`\s]+)`")


class CorpusTree:
    def __init__(self, tree_file: str | Path) -> None:
        lines = [ln.strip() for ln in Path(tree_file).read_text(encoding="utf-8").splitlines()]
        self.entries = {ln for ln in lines if ln}
        self.entries_lower = {ln.lower() for ln in self.entries}
        self.dirs: set[str] = set()
        for ln in self.entries:
            parts = ln.split("/")
            for i in range(1, len(parts)):
                self.dirs.add("/".join(parts[:i]))
        self.dirs_lower = {d.lower() for d in self.dirs}

    def __contains__(self, corpus_path: str) -> bool:
        cand = corpus_path.strip().rstrip("/")
        if cand.startswith("corpus/"):
            cand = cand[len("corpus/"):]
        if cand in self.entries or cand in self.dirs:
            return True
        low = cand.lower()
        return low in self.entries_lower or low in self.dirs_lower


def check_c9(path: str, prose: list[tuple[int, str]], tree: CorpusTree | None) -> list[Finding]:
    if tree is None:
        return []
    findings = []
    for lineno, raw in prose:
        for m in _C9_PATH_RE.finditer(raw):
            p = m.group(1).rstrip(".,;:)")
            if p not in tree:
                findings.append(Finding(
                    path, lineno, "HIGH", "C9",
                    f"corpus path `{p}` not found in corpus tree "
                    "(no invented shelves)"))
    return findings


# --------------------------------------------------------------------------
# C10 — Superlative honesty (LOW advisory, heuristic).
#
# Heuristic: a paragraph is flagged when it contains a narration superlative
# ("the shortest" / "the first" / "the longest") AND a counterexample-shaped
# pattern — a contrast marker (but, except, actually, though, although,
# until, anymore, no longer, used to) suggesting the superlative has an
# exception the narration is smoothing over. Humans decide (S5-F3).
# --------------------------------------------------------------------------

_C10_SUPER_RE = re.compile(r"\bthe (shortest|first|longest)\b", re.IGNORECASE)
_C10_COUNTER_RE = re.compile(
    r"\b(but|except|actually|though|although|until|anymore|no longer|used to)\b",
    re.IGNORECASE)


def check_c10(path: str, paras: list[tuple[int, str]]) -> list[Finding]:
    findings = []
    for start, text in paras:
        supers = sorted({m.group(0).lower() for m in _C10_SUPER_RE.finditer(text)})
        if supers and _C10_COUNTER_RE.search(text):
            findings.append(Finding(
                path, start, "LOW", "C10",
                f"superlative honesty: {', '.join(supers)} near a "
                "counterexample-shaped pattern; humans verify (S5-F3)"))
    return findings


# --------------------------------------------------------------------------
# C11 — Pick-entry length (LOW advisory, deterministic).
#
# SPEC §3 (as amended): a pick's why-portion is one or two in-voice
# sentences plus at most one trailing signature fragment in-voice
# ("No offense.", "Eat first.", "Noted. Twice."). Sentence-units are split
# on terminal ., !, ? — a fragment like "No offense." is a unit. A trailing
# run of short units (<= 2 words each, e.g. "Noted. Twice.") counts as ONE
# signature fragment; everything before it counts as sentences. Fire when
# sentences + fragment > 3. Only applies to pick lines (`- \`corpus/...\` —`)
# inside `## The picks` sections; if the file has no such section, any
# pick-shaped line is checked (fallback). LOW never fails the build.
# --------------------------------------------------------------------------

_C11_PICK_RE = re.compile(r"^\s*-\s+`corpus/[^`\s]+`\s+—\s*(?P<why>.+?)\s*$")
_C11_H2_RE = re.compile(r"^\s{0,3}##(?!#)\s*(?P<title>.*?)\s*$")
_C11_MAX_UNITS = 3  # 2 sentences + 1 signature fragment
_C11_FRAG_WORDS = 2


def check_c11(path: str, prose: list[tuple[int, str]]) -> list[Finding]:
    has_picks_section = any(
        (m := _C11_H2_RE.match(raw)) and m.group("title").lower().startswith("the picks")
        for _, raw in prose)
    findings = []
    in_picks = False
    for lineno, raw in prose:
        h = _C11_H2_RE.match(raw)
        if h:
            in_picks = h.group("title").lower().startswith("the picks")
            continue
        pm = _C11_PICK_RE.match(raw)
        if not pm or (has_picks_section and not in_picks):
            continue
        why = pm.group("why")
        units = [s for s in re.split(r"(?<=[.!?])\s+", why) if s.strip()]
        if not units:
            continue
        # Collapse a trailing run of short (<=2-word) units into one fragment.
        i = len(units)
        while i > 0 and len(units[i - 1].split()) <= _C11_FRAG_WORDS:
            i -= 1
        fragment = 1 if i < len(units) else 0
        sentences = i
        total = sentences + fragment
        if total > _C11_MAX_UNITS:
            findings.append(Finding(
                path, lineno, "LOW", "C11",
                f"pick entry exceeds 2 sentences + 1 signature fragment "
                f"({sentences} sentences + {fragment} fragment = {total} units)"))
    return findings


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------

def lint_file(path: str, tree: CorpusTree | None = None) -> list[Finding]:
    text = Path(path).read_text(encoding="utf-8")
    lines = text.splitlines()
    prose = _prose_lines(lines)
    paras = _paragraphs(prose)
    findings: list[Finding] = []
    findings += check_c1(path, lines, prose)
    findings += check_c2(path, lines, prose)
    findings += check_c3(path, lines, prose)
    findings += check_c4(path, lines, prose)
    findings += check_c5(path, lines, prose)
    findings += check_c6(path, paras)
    findings += check_c7(path, prose)
    findings += check_c8(path, lines, prose)
    findings += check_c9(path, prose, tree)
    findings += check_c10(path, paras)
    findings += check_c11(path, prose)
    findings.sort(key=lambda f: (f.file, f.line, f.rule, f.message))
    return findings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="canon_lint",
        description="CI for fiction: canon continuity + anti-AI style rules "
                    "(SPEC.md §5).")
    ap.add_argument("files", nargs="+", metavar="FILE",
                    help="Markdown file(s) to lint")
    ap.add_argument("--corpus-tree", metavar="PATH",
                    help="tree.txt for C9 corpus-path verification "
                         "(one path per line)")
    ap.add_argument("--strict", action="store_true",
                    help="fail the build on MODERATE/LOW findings too")
    args = ap.parse_args(argv)

    tree: CorpusTree | None = None
    if args.corpus_tree:
        tree = CorpusTree(args.corpus_tree)
    else:
        print("canon_lint: note: C9 corpus-path verification skipped "
              "(no --corpus-tree given)", file=sys.stderr)

    all_findings: list[Finding] = []
    ok = True
    for f in args.files:
        try:
            all_findings += lint_file(f, tree)
        except OSError as exc:
            print(f"canon_lint: error: cannot read {f}: {exc}", file=sys.stderr)
            ok = False

    all_findings.sort(key=lambda x: (x.file, x.line, x.rule, x.message))
    for finding in all_findings:
        print(finding.render())

    if not ok:
        return 2
    high = any(x.severity == "HIGH" for x in all_findings)
    if high or (args.strict and all_findings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
