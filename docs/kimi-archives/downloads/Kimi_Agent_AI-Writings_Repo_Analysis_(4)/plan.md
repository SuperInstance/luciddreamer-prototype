# Plan — New Repo: "the-tide-table" (creative-side expansion)

## Concept (locked by orchestrator)
A periodical repo for the SuperInstance org: **the fleet's tide table, posted at slack water.**
The Front Door (7 stories + reader's map) was a one-time anthology. The Tide Table turns it into a
standing creative engine: every tide, an issue — one new in-world piece, crew picks from the deep
corpus (6,854 works) curated IN-VOICE by the six lens characters, and the canon-lint CI that
automates every defect class the human review pipeline caught by hand.

## Stage 0 — Setup (orchestrator)
- Write this plan.md
- Check repo name availability (github.com/SuperInstance/the-tide-table should 404)
- Scaffold /mnt/agents/output/the-tide-table/ directory + git init

## Stage 1 — SPEC.md (orchestrator authors, per vibecoding-general-swarm spec-first rule)
- Repo purpose, directory layout, issue format (YAML front-matter + markdown body)
- Voice card format (6 lens characters from CANON.md)
- canon-lint rule registry (10 rules distilled from actual Front Door review findings)
- Pipeline integration: corpus-compass (picks via vibe_search/digest), casting-call (voice casting),
  fleet-metrics (optional), Phase-3 guest-book hook (future)

## Stage 2 — Parallel build (two subagents, independent workstreams)
- **A. coder**: tools/canon_lint.py + tests (10 rules, stdlib-only, corpus path verifier against
  /mnt/agents/repos/tree.txt) + README scaffold mechanics. Command: `python3 -m pytest` chained
  with pip install in ONE shell call.
- **B. fiction_writer**: voices/*.md (6 voice cards curated from CANON.md + STORY-BIBLE.md) +
  issues/issue-000-posted-at-slack-water.md (~1,500 words: the Tap posts the first tide table;
  six crew picks, each 2 REAL corpus paths from tree.txt + in-voice one-liner; standing invitation).
  Anti-AI rules inline. One traveling line per card max.

## Stage 3 — Integration & dogfood (orchestrator)
- Run canon_lint against issue-000 AND all 7 front-door stories (post-fix stories should pass —
  validates the tool on known-good text; any failure = real bug in either)
- Review pass on issue-000 (style/canon reviewer subagent); fix via dispatched fix subagent if WARNING+
- Package: tar.gz of the repo + final tree listing

## Stage 4 — Deliver
- Response with KIMI_REF tags: the-tide-table.tar.gz, README concept summary
- Note to Casey: check org for name collision before `gh repo create`
