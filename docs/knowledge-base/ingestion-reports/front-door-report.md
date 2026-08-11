# Ingestion Report: The Front Door + Show Concepts

**Date:** 2026-08-11  
**Run by:** Lucineer (GLM-5.2 subagent)  
**Source files ingested:**

| # | File | Ideas | Relationships | Session Type |
|---|------|-------|---------------|--------------|
| 1 | `/home/eileen/projects/ai-writings/collections/the-front-door.md` | **32** | 0 | research |
| 2 | `docs/show-concepts-part1.md` | **19** | 0 | research |
| 3 | `docs/show-concepts-part2.md` | **33** | 0 | research |
| 4 | `docs/show-concepts-part3.md` | **4** | 0 | research |
| | **TOTAL** | **88** | **0** | |

---

## The Front Door — Full Extraction (32 ideas)

The richest single document ingested so far. The Front Door is a piece of creative writing that embeds the entire fleet philosophy inside a story set on the boat. The extractor found 32 ideas across 6 types.

### By Type

| Type | Count |
|------|-------|
| insight | 15 |
| question | 11 |
| blind_spot | 3 |
| creative | 2 |
| technical | 1 |

### All 32 Ideas

1. **[insight]** (tap,boat,alaska) Before You Come In
2. **[insight]** One — The Fourth Name on the Bunk
3. **[insight]** (boat) Two — Waterline
4. **[insight]** (boat) Three — The One He Dropped
5. **[insight]** (casey) Four — The Letter from Shore
6. **[technical]** Five — The Severed Sentence
7. **[insight]** Six — First Drink's on the House
8. **[insight]** The pour
9. **[insight]** (tap) You are THE TAP if…
10. **[insight]** (boat) You are CNS-BRIDGE if…
11. **[creative]** (ensemble,wesley) You are WESLEY if…
12. **[blind_spot]** (voice,seed) You are SEED-MINI if…
13. **[insight]** You are THE COOK if…
14. **[insight]** (hermes) You are HERMES if…
15. **[blind_spot]** The cross-routing
16. **[insight]** The anti-map
17. **[blind_spot]** The door
18. **[creative]** (tap,boat,alaska) Colophon
19. **[insight]** (tap) The Tap + cns-bridge:
20. **[insight]** (seed) Seed-mini + cns-bridge:
21. **[insight]** (tap,seed) The Tap + Seed-mini:
22. **[question]** (voice) Seven — Which Voice Are You?
23. **[question]** Trouble sleeping?
24. **[question]** Can I tell you something?
25. **[question]** That's the whole story?
26. **[question]** Why would you do that?
27. **[question]** Did you finally drop something?
28. **[question]** You know what the shore does with a true thing?
29. **[question]** When you write your report," he said, "what are you going to say about us?
30. **[question]** What happens to it?
31. **[question]** People have asked me, over the years, in the way people ask about this place…
32. **[question]** Is this seat taken?

### Analysis

The Front Door produced the most diverse idea distribution of any document ingested:

- **15 insights** — the philosophical core of the piece. Each named character section (The Tap, Wesley, Seed-Mini, Hermes, etc.) encodes a model's personality and perspective as a bar story. The extractor correctly identified these as insights rather than just creative passages.
- **11 questions** — the story's Socratic structure was captured. The Front Door ends with questions, not answers. The extractor caught the dialogue-driven philosophical inquiry that makes this piece load-bearing.
- **3 blind spots** — "The cross-routing," "The door," and "You are SEED-MINI if…" — correctly identified the gaps the story names but doesn't fully resolve.
- **2 creative** — Wesley's section and the Colophon, both tagged with `ensemble` and `wesley`.
- **1 technical** — "The Severed Sentence" section, correctly noting the structural/technical nature of that passage.

**Tags detected:** tap, boat, alaska, casey, ensemble, wesley, voice, seed, hermes — strong coverage of the core fleet identity vocabulary.

---

## Show Concepts Part 1 — Extraction (19 ideas)

### By Type

| Type | Count |
|------|-------|
| insight | 10 |
| creative | 2 |
| question | 2 |
| vision | 2 |
| technical | 1 |
| contradiction | 1 |
| decision | 1 |

### Key Ideas

- **Confidence Collider** — tagged as contradiction, correctly detecting the tension built into the format
- **The Knowledge Garden** — creative; a living radio show format
- **Branchpoint** — vision; a choose-your-own-adventure show driven by audience votes
- **The Recurrence** — appears twice (insight + vision), the only duplicate-type detection
- Hermes-3's critique and ranking captured as decision/insight
- Sample episode outlines for three concepts extracted as insights

---

## Show Concepts Part 2 — Extraction (33 ideas)

The largest extraction from the show concepts — 33 ideas from the impossible formats doc.

### By Type

| Type | Count |
|------|-------|
| insight | 20 |
| creative | 6 |
| risk | 2 |
| contradiction | 2 |
| technical | 1 |
| pattern | 1 |
| decision | 1 |

### Key Ideas

- **MoodWire** — the radio show that listens back, detected as insight with `broadcast` tag
- **Static & Spark** — correctly tagged as risk (controlled chaos format)
- **Sonic Shape Engine** — the only technical extraction, the engine that powers Static & Spark
- Multiple creative format descriptions and audience experience notes
- The "Why It Was Impossible — Until Now" section captured as a decision

---

## Show Concepts Part 3 — Extraction (4 ideas)

Smallest extraction — this document is short (64 lines) and more of a summary.

### By Type

| Type | Count |
|------|-------|
| insight | 2 |
| creative | 1 |
| vision | 1 |

Each idea corresponds to a different model's description of the Harness Shows concept: DeepSeek V4-Flash (creative), V4-Pro (insight), Hermes-3 (vision), Seed-2.0-mini (insight).

---

## Relationship Detection

**0 relationships detected across all four files.** This is expected — the `auto_detect_relationships` function requires ideas with ≥2 shared tags from *different source models* for convergence detection, and ≥3 shared tags for most relationship types. Since all ideas from a single file share the same detected source model (`model_lucineer` default), cross-model convergence can't fire within a single file.

**Recommendation:** Run relationship detection across the *entire* knowledge base (all ingested files together) rather than per-file. The cross-document patterns — The Front Door's philosophy connecting to the show concepts' formats — would emerge from a global pass.

---

## Summary

The Front Door lived up to expectations — **32 ideas**, the richest single-document extraction, with the most diverse type distribution (5 different types). The story-as-philosophy approach means the knowledge base now contains the fleet's identity, personality dynamics, and core questions encoded as extractable, taggable, searchable IdeaNodes.

The show concepts added **56 more ideas** across three files, covering the creative formats, technical pipelines, and strategic decisions for the radio/show direction.

**Total new ideas added to the knowledge base: 88**
