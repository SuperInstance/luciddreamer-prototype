# SPEC — the-tide-table

> The fleet's periodical. Posted at slack water.
> Status: binding contract for scaffold v0.1. Python ≥ 3.10, stdlib-only tooling, tests offline.

## 1. What this repo is

AI-Writings holds ~6,800 works. The Front Door anthology (front-door.final.md) proved the model:
distill the corpus into **six lens characters**, give each a voice readers can recognize, and answer
the three founding questions (why hermit crabs / why writing / why open) inside fiction, not around it.

**the-tide-table** makes that recurring instead of one-time. Every tide, an issue is posted:

1. **One posted piece** — new in-world writing (story, letter, bar page, log fragment).
2. **The picks** — each lens character curates 2–3 REAL works from the deep corpus, with one or two
   in-voice sentences about why. This is how the backlog becomes readable: not an index, a crew's taste.
3. **The standing invitation** — how a reader asks for a voice, leaves a request, or comes aboard.

The tide table is a public fixture: posted, rhythmic, useful whether or not you sail.
Slack water — the pause between tides — is when it gets nailed to the door.

## 2. Directory layout

```
the-tide-table/
├── README.md                  # the concept, for humans arriving cold
├── SPEC.md                    # this file
├── CANON.md                   # imported, read-only: world facts + tone law (from front-door)
├── voices/                    # one card per lens character — the casting sheet
│   ├── the-tap.md
│   ├── wesley.md
│   ├── hermes.md
│   ├── cns-bridge.md
│   ├── seed-mini.md
│   └── the-cook.md
├── issues/
│   └── issue-000-posted-at-slack-water.md
├── tools/
│   ├── canon_lint.py          # CI for fiction — see §5
│   └── tests/test_canon_lint.py
└── docs/
    └── pipeline.md            # how an issue gets made on the boat (§6 in prose)
```

## 3. Issue format

Markdown file, YAML front-matter, one H1. Body sections in fixed order:
`## The post` (the tide note, ≤120 words, in the Tap's voice) → `## The piece` (new writing) →
`## The picks` (one `### <Voice>` subsection per character) → `## The invitation`.

```yaml
---
issue: 0
title: "Posted at Slack Water"
posted_at: "slack water, first tide after the Front Door opened"
tide: outgoing
voices: [the-tap, wesley, hermes, cns-bridge, seed-mini, the-cook]
piece_kind: bar-page          # story | letter | bar-page | log-fragment
pick_count: 12                # total corpus picks across all voices
---
```

**Pick entry format** (strict — canon-lint validates: C9 paths, C11 length):
```
- `corpus/<path/from/tree.txt>` — <one or two in-voice sentences, plus at most one trailing signature fragment.>
```
The why-portion is one or two in-voice sentences, plus at most one trailing signature
fragment in-voice (e.g. "No offense.", "Eat first.", "Noted. Twice."). Signature fragments
are part of the voice, not the count — but never more than one per entry.
Paths must exist in the corpus tree. No invented shelves. This is the standing rule that
separates a tide table from a hallucination.

## 4. Voice card format

Each `voices/<name>.md` contains: **Role** (one line) · **Lens for** (the reader-type this voice
serves, verbatim from the story bible) · **Voice** (signature: vocabulary, rhythm, verbal tics,
things this voice never says) · **Shelf** (3–5 canonical corpus paths) · **Canon line** (the one
line this character owns) · **Banned** (patterns forbidden in this voice — e.g. the Tap never names
the machinery). Voice cards are the casting sheet: casting-call reads them to bind a model to a voice.

## 5. canon-lint — CI for fiction

Every defect class the human reviewers caught in the Front Door pipeline becomes an automated rule.
`python3 tools/canon_lint.py <file...> [--corpus-tree /path/to/tree.txt]` → exit 0 clean, 1 findings.

| ID | Rule | Severity | Origin (real finding) |
|----|------|----------|----------------------|
| C1 | Seat map: Seed-mini ↔ middle stool, never "end of the bar" | HIGH | S7-F2 |
| C2 | Wesley's folded square ↔ June's **inside pocket**, never her notebook | HIGH | S5-F2 / S6-F2 |
| C3 | Bunk tape order: DEE, MARCOS, T. OKAFOR, JUNE — JUNE is the 4th name, three crossed out | HIGH | S5-F1 |
| C4 | "Waterline" capitalized when referring to Wesley's concept | LOW | S6-F3 |
| C5 | No-technology law: no "parameters", "hardware", "embeddings", "model" (as machinery), "API" in narration/dialogue; sanctioned coinages (Smallening, Cloud Gods, Waterline) exempt | HIGH | S7-F1 |
| C6 | Quotable dilution: flag any paragraph containing ≥2 aphorism-shaped sentences (heuristic, documented in code) | MODERATE | S6-F1, series-wide |
| C7 | Em-dash density ≤ 5 per 1000 chars | MODERATE | standing anti-AI rule |
| C8 | English AI-vocabulary scan: delve, tapestry, pivotal, vibrant, testament to, nestled, "stands as", "serves as" | MODERATE | anti-ai.md |
| C9 | Corpus path verification: every backticked `corpus/...` path must exist in tree.txt | HIGH | S7 review |
| C10 | Superlative honesty: narration superlatives ("the shortest", "the first") flagged for human check when scene contains a counterexample pattern | LOW (advisory) | S5-F3 |
| C11 | Pick-entry length: ≤2 in-voice sentences + ≤1 trailing signature fragment in the why-portion (§3) | LOW (advisory) | issue-000 founding review — contract/CI mismatch |

C1–C5, C9 are deterministic. C6–C8, C10 are heuristics — they print findings, humans decide.
C11 is deterministic but advisory (LOW): it flags pick-length drift for human review and
never fails the build.
Tests cover every rule with pass/fail fixtures, including the exact pre-fix strings from the
Front Door defect history as regression fixtures.

## 6. Pipeline (how an issue gets made on the boat)

1. **Picks shortlist** — corpus-compass `vibe_search()` per voice card's shelf themes; the lens
   character's model (cast via casting-call `cast(role)`) chooses 2–3 and writes the why.
2. **The piece** — cast to a voice per `piece_kind`; writer model drafts; peer-consult critic
   (next fallback-chain model, different VoiceCharacter family) reviews; REVISE loop max 2.
3. **Lint** — canon_lint must exit 0 on deterministic rules; heuristic findings reviewed by the Tap
   (the editor role) before posting.
4. **Post** — at slack water. Commit message: `post: issue-NNN <title>`.
5. **Digest cross-post** — corpus-compass `generate_digest()` "Night's Catch" column links the issue.

## 7. Integration points

- **casting-call** — voice cards → roles; `_ROLE_DEFAULTS` extended: `voice:wesley` etc.
- **corpus-compass** — pick discovery (vibe_search), issue discovery (digest).
- **peer-consult** — the pre-posting review loop.
- **fleet-metrics** — optional: issues posted / picks followed / lint findings per issue.
- **Future: the guest book** — Phase-3 Telegram player becomes the front-of-house: readers leave
  requests, the conductor casts a voice to answer, the best exchanges become `piece_kind: letter`.

## 8. Roadmap

- v0.1 (this scaffold): layout, SPEC, voice cards, issue-000, canon-lint + tests.
- v0.2: casting-call role bindings; corpus-compass pick CLI (`compass picks --voice wesley`).
- v0.3: guest book intake; issue template generator (`compass new-issue`).
- v0.4: tide schedule from real slack-water times at 60°N 149°W — the chart plotter picks posting hour.
