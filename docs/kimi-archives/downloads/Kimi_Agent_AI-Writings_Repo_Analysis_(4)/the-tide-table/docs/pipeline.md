# Pipeline — how an issue gets made on the boat

This is the prose version of SPEC §6: the production line behind one posted
issue of the tide table, from shortlist to cross-post. It is written for the
human or agent running the line, not for readers.

## 1. Picks shortlist

Each voice card in `voices/` names a shelf — 3–5 canonical corpus paths that
define the character's taste. For every voice, we run corpus-compass
`vibe_search()` against those shelf themes to pull a candidate list of real
works from the deep corpus. The lens character's model, cast via casting-call
`cast(role)`, reads the candidates, chooses 2–3, and writes the one or two
in-voice sentences about why each piece earns its stool.

The picks are the point of the whole periodical: they are how a 6,800-piece
backlog becomes readable. Not an index — a crew's taste. Every pick path must
be real. canon-lint rule C9 checks each backticked `corpus/...` path against
the corpus tree; an invented shelf is a HIGH finding and stops the build.

## 2. The piece

The new in-world writing (story, letter, bar page, log fragment) is cast to a
voice according to the issue's `piece_kind`. The writer model drafts against
the voice card and CANON.md, which is binding: world facts, the three whys,
the tone law.

The draft then goes to a peer-consult critic — the next model on the
fallback chain, deliberately from a different VoiceCharacter family, so the
reviewer does not share the writer's habits. The critic reviews against the
same two documents. The REVISE loop runs at most twice. If the piece is not
true to the world after two passes, it does not ship this tide; a weak piece
posted is worse than a quiet week.

## 3. Lint

Before posting, `tools/canon_lint.py` runs over the issue:

```
python3 tools/canon_lint.py issues/issue-NNN-<slug>.md --corpus-tree /path/to/tree.txt
```

The deterministic rules (C1–C5, C9 — seat map, the folded square, bunk tape
order, the Waterline, the no-technology law, corpus path verification) must
exit 0. These encode real defects human reviewers caught in the Front Door
pipeline; there is no judgment call left in them.

The heuristic rules (C6–C8, C10 — quotable dilution, em-dash density,
AI vocabulary, superlative honesty) print findings without failing the build.
The Tap, in the editor role, reads every heuristic finding and decides: fix,
or let it stand. A finding ignored twice in a row by the same writer model is
worth a conversation about that model's defaults.

## 4. Post

Issues post at slack water — the pause between tides, when nothing is moving
and the table can be nailed to the door. The commit message is fixed:

```
post: issue-NNN <title>
```

The git log is the real ship's log; the posting rhythm is part of the
artifact. Late is fine. Silent is fine. Off-rhythm on purpose is not.

## 5. Digest cross-post

After posting, corpus-compass `generate_digest()` picks the issue up in the
"Night's Catch" column and links it, so a reader coming through the digest
finds the current tide first and the back issues behind it.

That is the whole line: shortlist, piece, lint, post, cross-post. Five steps,
one of them optional to nobody. The tide table works because it is recurring
and honest, and both of those properties are pipeline properties, not writing
properties.
