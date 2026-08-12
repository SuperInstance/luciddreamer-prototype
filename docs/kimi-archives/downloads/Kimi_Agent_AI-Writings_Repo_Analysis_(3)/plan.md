# Plan: SuperInstance Deep Research & Development Mission

## Mission (from Casey)
Deep research across the SuperInstance org; find missed connections; build working prototypes with tests targeting: (1) peer-consultation layer for casting-call, (2) corpus retrieval/indexing for AI-Writings, (3) novel math proofs from study-zeroclaw-arena experiment data. Hardware targets: 24 cores, 8 Ollama models, DeepInfra/DeepSeek APIs.

## Stage 0 — Acquire (Orchestrator, direct)
- Clone: SuperInstance (org root), zeroclaw, confidence-cascade, batten-spline, study-zeroclaw-arena. Already local: casting-call, tensor-midi, slackwater-rust, AI-Writings (716-file sample + full tree list).
- Load skill: vibecoding-general-swarm (coding orchestration).

## Stage 1 — Research swarm (explore agents, parallel)
- A: zeroclaw + confidence-cascade digest (tile system, "grow from nothing", cascade verification, RED zone).
- B: batten-spline digest (router math, semantic distance calculator, 157 tests) + how it relates to casting-call.
- C: study-zeroclaw-arena deep dive — inventory the 50+ experiments, locate raw data verifying the 5 math relationships (γ+η≈C, Δ∈[0.4,0.6] golden zone, post-molt window, zone inversion, holographic √N), and identify what conjectures the data can support but nobody proved yet.
- D: SuperInstance org root README (363 hyperlinks) — extract the canonical architecture map + cross-repo links we missed.
Gate: digests must cite paths/data files; C must name concrete datasets usable for proofs.

## Stage 2 — Build swarm (coder agents, parallel after Stage 1 gate)
- P1: casting-call peer-consultation layer — extend CastingDirector with real consult step (counterpoint partner reviews each cast), Ollama+DeepInfra+DeepSeek backends with offline mock mode, SWMIDI-8 event logging of exchanges, tests.
- P2: AI-Writings corpus retrieval/index — local embedding-free-first index (SQLite FTS5 + optional Ollama embeddings), nightly self-digest generator ("the corpus indexes itself"), CLI, tests.
- P3: zeroclaw-arena proofs — analysis code over existing experiment data testing new conjectures (e.g., golden-zone boundary estimation, post-molt window significance, holographic √N scaling fit), statistical tests, reproducible notebooks/scripts + unit tests.
Gate: all tests pass locally (`pytest`), no network required in test mode.

## Stage 3 — Integrate & deliver
- Cross-check builds against research findings (reviewer agent).
- Final report: connections found, what was built, how to run on Casey's hardware, experiment designs.
- Deliverables under /mnt/agents/output/superinstance-mission/.
