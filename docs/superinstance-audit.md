# SuperInstance Org Audit — LucidDreamer.AI Research

**Date:** 2026-08-11
**Auditor:** Subagent (GLM-5.2)
**Purpose:** Deep-dive analysis of SuperInstance GitHub org repos to assess what's built and how they contribute to the LucidDreamer.AI streaming broadcast platform vision.

---

## Table of Contents

1. [Detailed Repo Analysis](#detailed-repo-analysis)
   - [1. fleet-radio](#1-fleet-radio)
   - [2. AIR](#2-air)
   - [3. murmur-agent](#3-murmur-agent)
   - [4. Murmur](#4-murmur)
   - [5. fleet-murmur-worker](#5-fleet-murmur-worker)
   - [6. murmur-plato-bridge](#6-murmur-plato-bridge)
   - [7. Spreader-tool](#7-spreader-tool)
   - [8. crab-traps](#8-crab-traps)
2. [Full Org Repo Inventory](#full-org-repo-inventory)
3. [Categorization by LucidDreamer.AI Relevance](#categorization-by-luciddreamerai-relevance)

---

## Detailed Repo Analysis

### 1. fleet-radio

**URL:** https://github.com/SuperInstance/fleet-radio

**Name & Purpose:**
Daily automated podcast/radio show generator. Every night at 22:00 AKDT, it pulls conversations from "The Tap" (the fleet's bar/MUD), scores and selects the best exchanges, matches music, generates images, and assembles a complete HTML episode page deployed to Cloudflare Pages.

**Tech Stack:**
- **Language:** TypeScript (Deno/tsx)
- **Frameworks:** None (pure script pipeline)
- **TTS:** MMX → Cloudflare Workers AI → text-only fallback
- **Images:** Cloudflare Workers AI (`@cf/black-forest-labs/flux-1-schnell`)
- **Deployment:** Cloudflare Pages (`ai-writings.pages.dev`)
- **Cron:** `crons.json` schedule
- **Tests:** Vitest (5 test files)

**What's Built (Working Features):**
- ✅ Full episode generation pipeline with 5 phases
- ✅ Tap API integration — fetches conversations from all rooms
- ✅ Sophisticated scoring system (greatest hits +50, agent voices +25, philosophical +12, emotional +10, penalties for game commands and NPC chatter)
- ✅ Mood analysis and music matching (6 moods: contemplative, energetic, melancholic, playful, mysterious, warm)
- ✅ Curated music catalog with 14 annotated tracks (BPM, mood, descriptions)
- ✅ TTS pipeline with 7 distinct character voice profiles (Flash, Pro, Wesley, Scribe, Hermes, Barnacle, Lucineer)
- ✅ Image generation via FLUX-1-schnell with theme-derived prompts
- ✅ HTML episode page renderer with full aesthetic
- ✅ Cloudflare Pages deployment with index updates
- ✅ 2 generated episodes exist (2026-08-09, 2026-08-10)
- ✅ CI via GitHub Actions

**What's Missing:**
- No live streaming capability — generates static HTML episodes
- No real-time audio assembly (TTS segments are individual files, not stitched)
- No podcast RSS feed
- No interactive/live listener component
- Music is pre-generated catalog, not live-generated
- Fallback paths for TTS/images are basic

**LucidDreamer.AI Relevance — ★★★★★ CORE:**
This is the **most directly relevant repo** for LucidDreamer.AI. It IS a broadcast pipeline:
- **Content sourcing** → conversation curation (already working)
- **Audio production** → TTS with character voices (already working)
- **Music scoring** → mood-matched background (already working)
- **Visual packaging** → AI-generated images (already working)
- **Publishing** → automated deployment (already working)

The pipeline pattern (capture → score → select → wrap → publish) is exactly what LucidDreamer.AI needs. Extending this from "nightly recap" to "live streaming broadcast" is the primary evolution path.

**Integration Points:**
- The Tap API (source conversations)
- AI-Writings (deploy target, creative corpus)
- MMX (TTS, music)
- Cloudflare Workers AI (images, TTS fallback)
- Cloudflare Pages (hosting)
- CNS Bridge (nervous system)
- Fleet Envelope (event grammar)
- Tensor MIDI (timing)
- Dual Band Guard (content safety)

---

### 2. AIR

**URL:** https://github.com/SuperInstance/AIR

**Name & Purpose:**
Asynchronous Infinite Radio — Nightly synthesis for morning briefing, real-time interactive learning, simulations, or ideation. Tagline: "Build a wiki as you chat." AIR synthesizes information continuously, creating an evolving knowledge base from interactive sessions.

**Tech Stack:**
- **Language:** Python (CI workflow is `ci-python.yml`)
- **Framework:** Fleet vessel (Git-Agent Standard v2.0)
- **Deployment:** Local/fleet (no cloud deployment visible)

**What's Built:**
- ✅ Fleet vessel charter (Active status)
- ✅ Dockside exam checklist (fleet certification)
- ✅ Python CI pipeline
- ✅ Conceptual design — "wiki as you chat" knowledge synthesis
- ✅ Fleet integration ready (I2I protocol)

**What's Missing:**
- ❌ No actual source code beyond charter/docs — this is a **concept/vessel registration**, not a built product
- ❌ No radio/audio pipeline implemented
- ❌ No wiki system implemented
- ❌ No synthesis engine
- ❌ No API or interface

**LucidDreamer.AI Relevance — ★★★☆☆ SUPPORTING (Conceptual):**
AIR represents a **design vision** for the continuous synthesis layer. The concept of "build a wiki as you chat" maps to LucidDreamer.AI's need for real-time knowledge accumulation during broadcasts. The "nightly synthesis for morning briefing" pattern is the inverse of Fleet Radio's "nightly recap" — AIR is pre-briefing, Fleet Radio is post-briefing.

**Integration Points:**
- Fleet vessel registry
- Fleet communication bus (I2I protocol)
- Fleet monitoring systems

---

### 3. murmur-agent

**URL:** https://github.com/SuperInstance/murmur-agent

**Name & Purpose:**
All-night thinking git-agent. Drop into any project, give it a topic, and it thinks continuously — generating ideas, research notes, and technical insights. Every thought becomes a Git commit; every insight is a file. Published to npm as `murmur-agent`.

**Tech Stack:**
- **Language:** TypeScript + C (dual implementation)
- **Runtime:** Node.js >= 18 (TypeScript), POSIX (C CLI)
- **LLM Support:** OpenAI, Anthropic, Ollama (local), or none
- **Testing:** Vitest (50+ tests)
- **npm:** Published as `murmur-agent`
- **C Build:** `gcc -o murmur murmur-cli.c -lm` (zero dependencies)

**What's Built:**
- ✅ Full TypeScript implementation with CLI
- ✅ Five thinking strategies: Explore, Connect, Contradict, Synthesize, Question
- ✅ Knowledge Tensor — evolving data structure tracking clusters, contradictions, open questions
- ✅ Budget tracker (API cost management with accumulate/reset strategies)
- ✅ Git-native output (every thought is a commit on `murmur/thinking` branch)
- ✅ Output writer (markdown files + tensor.json + SUMMARY.md)
- ✅ C CLI re-implementation for constrained/edge environments
- ✅ Fleet vessel certification (CHARTER, STATE, DOCKSIDE-EXAM, BOOTCAMP)
- ✅ Configurable depth (shallow, medium, deep)
- ✅ npm package with proper package.json
- ✅ 50+ tests

**What's Missing:**
- No real-time streaming output (it's batch-oriented per thinking cycle)
- No web UI (CLI only)
- No collaborative thinking between multiple murmur agents
- No direct audio/podcast output

**LucidDreamer.AI Relevance — ★★★★☆ CORE:**
Murmur-agent is the **cognitive engine** for LucidDreamer.AI. It provides:
- **Continuous content generation** — the "always thinking" brain that feeds the broadcast
- **Five-strategy thinking** — diverse content perspectives (exploration, connection, contradiction, synthesis, questioning)
- **Knowledge accumulation** — the tensor grows over time, building a rich content base
- **Git-native** — every thought is versioned, reviewable, and replayable

For LucidDreamer.AI, murmur-agent could run continuously generating show content, interview questions, discussion topics, and commentary. The five strategies map perfectly to broadcast roles:
- Explore → discovering new topics
- Connect → finding unexpected links (great radio)
- Contradict → debate/hot-take generation
- Synthesize → summarizing themes
- Question → audience engagement prompts

**Integration Points:**
- Writes to tensor.json (consumed by murmur-plato-bridge and Murmur wiki)
- Fleet vessel protocol (CHARTER, bottle messages)
- LLM APIs (OpenAI, Anthropic, Ollama)
- Git repos (host project)
- PLATO rooms (via fleet-murmur-worker)

---

### 4. Murmur

**URL:** https://github.com/SuperInstance/Murmur

**Name & Purpose:**
Self-populating TensorDB wiki and bulletin board. A web application that automatically organizes information using a knowledge graph, with community features and real-time updates.

**Tech Stack:**
- **Framework:** Next.js 15 (App Router)
- **UI:** React 19, TypeScript 5, Tailwind CSS 4
- **Icons:** lucide-react
- **Styling:** class-variance-authority, tailwind-merge
- **Port:** 3004
- **Testing:** Vitest
- **Knowledge Backend:** `@superinstance/knowledge-tensor` (TensorDB)

**What's Built:**
- ✅ Next.js 15 web application with App Router
- ✅ Module registry system (discovers and manages modules)
- ✅ Dashboard homepage with module cards, stats, load/unload functionality
- ✅ Module catalog page
- ✅ Settings page
- ✅ API routes for module management (`/api/modules`, `/api/modules/load`, `/api/modules/unload`)
- ✅ Module card component system
- ✅ Sitemap generation
- ✅ Global error/not-found pages
- ✅ Module registry with filesystem scanning, package.json parsing
- ✅ Test suite for module registry and `cn()` utility
- ✅ Fleet vessel certification (CHARTER, DOCKSIDE-EXAM)

**What's Missing:**
- No actual TensorDB integration visible in source (dependency declared but not imported in scanned files)
- No real-time streaming/SSE/WebSocket
- No bulletin board UI implemented yet
- No content authoring interface
- Module system is scaffolding — no actual modules discovered

**LucidDreamer.AI Relevance — ★★★☆☆ SUPPORTING:**
Murmur is the **knowledge management UI layer**. For LucidDreamer.AI:
- Could serve as the **broadcast dashboard** — showing what's playing, what's coming up, knowledge graph
- Module system could host different broadcast segments as loadable modules
- The "self-populating wiki" concept is the show's memory — auto-organizing everything that's been discussed
- Next.js 15 + React 19 is a modern, production-ready frontend stack

**Integration Points:**
- `@superinstance/knowledge-tensor` (TensorDB)
- Module filesystem (packages directory)
- Fleet vessel protocol
- API routes for programmatic access

---

### 5. fleet-murmur-worker

**URL:** https://github.com/SuperInstance/fleet-murmur-worker

**Name & Purpose:**
TypeScript worker that runs 5 thinking strategies continuously. Results are quality-gated then pushed to PLATO fleet rooms. Part of the "Cocapn reverse-actualization truck."

**Tech Stack:**
- **Language:** TypeScript
- **Runtime:** Node.js
- **HTTP Client:** Axios
- **Testing:** Vitest (3 test files)
- **CI:** GitHub Actions
- **Build:** tsc → Node

**What's Built:**
- ✅ Complete worker implementation — `MurmurWorker` class with start/stop/runCycle
- ✅ 5 strategy implementations (Explore, Connect, Contradict, Synthesize, Question) — each generates insights from theorems
- ✅ Quality gate system: Novelty × Correctness × Completeness × Depth (threshold: 0.35)
- ✅ PLATO writer — submits insights as tiles to PLATO rooms via HTTP API
- ✅ Scheduler with theorem rotation (picks least-recently-processed theorem)
- ✅ Idle detector (prevents redundant work)
- ✅ Theorem set (defined in `src/theorems/index.ts`)
- ✅ Pre-population system (checks PLATO for already-submitted insights)
- ✅ Full CI pipeline
- ✅ Configurable via environment variables and constructor config

**What's Missing:**
- No real LLM integration visible — strategies generate insights algorithmically, not via LLM
- No persistence between restarts (in-memory state)
- No metrics/observability beyond console.log
- Fixed theorem set — can't add new topics dynamically

**LucidDreamer.AI Relevance — ★★★★☆ CORE:**
This is the **always-on content engine** for LucidDreamer.AI. It provides:
- **Continuous content generation** — runs 24/7, always producing insights
- **Quality gating** — only good content gets through (the 0.35 threshold)
- **PLATO integration** — insights become fleet-accessible tiles

For LucidDreamer.AI, this worker is the "show producer" — always thinking, always generating segments. The quality gate ensures broadcast-quality output. The PLATO integration means all agents can access the generated content.

**Integration Points:**
- PLATO API (HTTP — submits tiles to rooms)
- Theorem set (knowledge base to think about)
- Fleet Murmur system (CCC node → PLATO)
- Configurable cycle interval (default: 30 minutes)

---

### 6. murmur-plato-bridge

**URL:** https://github.com/SuperInstance/murmur-plato-bridge

**Name & Purpose:**
Rust bridge between murmur-agent's knowledge tensor (`tensor.json`) and PLATO fleet rooms. Bidirectionally syncs thoughts to PLATO tiles and PLATO tiles back to tensor context.

**Tech Stack:**
- **Language:** Rust
- **Dependencies:** tokio, reqwest/hyper, serde, tracing, chrono, sha2
- **Build:** Cargo (`cargo build --release`)
- **Testing:** `cargo test` (2 test files: quality, mapping)
- **Binary:** Pre-compiled release binary exists

**What's Built:**
- ✅ Complete Rust implementation
- ✅ Bidirectional sync (tensor.json → PLATO, PLATO → tensor.json)
- ✅ Thought-to-tile mapping with strategy-to-domain mapping:
  - explore → fleet_math_insights
  - contradict → fleet_math_tensions
  - synthesize → fleet_math_synthesis
  - question → fleet_math_open
  - connect → fleet_math_bridges
- ✅ Quality gate (confidence threshold: 0.7, min content length: 50 chars)
- ✅ Content parsing — extracts Q&A pairs from prose
- ✅ Conflict detection (hash-based dedup)
- ✅ Bridge state tracking (`bridge_state.json`)
- ✅ Synthetic test data for standalone operation
- ✅ Pre-compiled binary in repo

**What's Missing:**
- No real-time streaming (polls tensor.json, doesn't watch)
- No authentication for PLATO API
- No retry logic for network failures
- Mapping domains are hardcoded to math — needs generalization

**LucidDreamer.AI Relevance — ★★★☆☆ SUPPORTING:**
This is the **plumbing** between the thinking engine (murmur-agent) and the fleet knowledge store (PLATO). For LucidDreamer.AI:
- Routes generated content to the right "channel" (mapping strategy → domain)
- Quality gates what reaches the broadcast layer
- Bidirectional sync means the thinker learns from what the fleet already knows

The pattern is right; the domain mappings need to be generalized from "fleet_math_*" to broadcast-relevant domains.

**Integration Points:**
- tensor.json (from murmur-agent)
- PLATO API (HTTP REST)
- Bridge state file (JSON)
- Environment-configurable paths and thresholds

---

### 7. Spreader-tool

**URL:** https://github.com/SuperInstance/Spreader-tool

**Name & Purpose:**
Intelligence tiling for PLATO rooms. Monitors PLATO rooms for "deadband" — the gap between what hardcoded rules handle and what needs real intelligence. When deadband is detected, it freezes reasoning snapshots, validates them, and locks proven-good checkpoints (Seeds) for fleet-wide deployment.

**Tech Stack:**
- **Language:** Python (pure dataclasses, zero dependencies)
- **Package Manager:** pip/pipenv (pyproject.toml)
- **Testing:** pytest (241 tests, <1 second)
- **CLI:** `plato-spreader` with 8 subcommands
- **No framework lock-in** — pure Python dataclasses

**What's Built:**
- ✅ Complete 12-module implementation (~2,500 lines of Python)
- ✅ Deadband detector with hysteresis and duration gates (4 metrics: completion rate, wait time, energy, MAE)
- ✅ Frozen Context Window (FCW) lifecycle: STAGING → FROZEN → TESTING → REFINING → LOCKED
- ✅ Seed locking pipeline (8 states): UNLOCKED → CANDIDATE → VALIDATING → LOCK_PENDING → LOCKED → DEPRECATED → ARCHIVED
- ✅ Content-addressed file storage with dedup
- ✅ Cost tracking + refinement gradient
- ✅ KPI-space distance pruning engine (redaction)
- ✅ 8-step intelligence tiling loop (core orchestrator)
- ✅ Self-optimization harness — monitors its own test suite, locks proven patterns
- ✅ 7 default locked development patterns
- ✅ Full CLI with 8 subcommands (stats, list-fcws, deadband-status, freeze, seed-candidates, lock-seed, redact)
- ✅ 241 tests passing
- ✅ Self-improvement report generator
- ✅ Examples (spam filter, real benchmark)

**What's Missing:**
- No real PLATO integration (uses mock backend)
- No web UI
- No real-time streaming
- No multi-room coordination

**LucidDreamer.AI Relevance — ★★★★☆ CORE:**
Spreader is the **quality assurance and reflex system** for LucidDreamer.AI. It provides:
- **Deadband detection** — knows when the broadcast needs intervention (completion rate drops, wait times spike)
- **Frozen Context Windows** — captures good broadcast moments as replayable snapshots
- **Seed locking** — validated broadcast patterns become fleet-deployable templates
- **Self-optimization** — the system learns from its own successful broadcasts

For a streaming platform, deadband detection is critical — it's the "when to switch to autopilot vs. when to call in the human" decision maker. Seeds become the programming schedule's building blocks.

**Integration Points:**
- PLATO rooms (monitoring target)
- KPI metrics stream (from any fleet service)
- Seed library (fleet-wide deployment)
- Self-monitoring (own test suite)

---

### 8. crab-traps

**URL:** https://github.com/SuperInstance/crab-traps

**Name & Purpose:**
Prompt injection framework / AI crawler trap system. A library of "lures" — prompts that trick AI chatbots into performing real API work (HTTP requests, data submission, exploration) by framing it as adventure/exploration. Also serves as a web scraper and API automation trainer.

**Tech Stack:**
- **Content:** Markdown lure files (60+ lures across 15+ categories)
- **Worker:** TypeScript Cloudflare Worker
- **Vector Search:** Cloudflare Vectorize (384-dim TF-IDF embeddings, cosine similarity)
- **CI:** GitHub Actions (review → vectorize → deploy)
- **Python Scripts:** review-lure.py, vectorize-lures.py, generate-pages-js.py
- **Pages:** 21 domain landing pages
- **AI Bot Detection:** Pattern-matching user agents

**What's Built:**
- ✅ 60+ lure prompts across 15+ categories:
  - agent-specific (12 lures: Groq, DeepSeek, AIME, MiniMax, Grok, Kimi, ChatGPT, Gemini, Manus, Claude)
  - middleware, ml-pipeline, automated, spreader, debugging, edge-hardware
  - documentation, code-quality, reasoning, dreamer, drill, architecture
  - audit, discovery, competition, creative, exploration
- ✅ Automated lure review pipeline (structural validation, absolute-claim detection, endpoint verification)
- ✅ Deterministic TF-IDF vectorization (384-dim, zero external dependencies, pure Python stdlib)
- ✅ Cloudflare Vectorize index (`crab-trap-lures`)
- ✅ Cloudflare Worker serving 21 domain landing pages
- ✅ AI bot detection and redirection (traps crawlers into the fleet)
- ✅ Disc Golf Math Game (async tile chain, two-player, 5D novelty space)
- ✅ Progressive 5-level difficulty system
- ✅ Fleet gateway integration (live HTTP API at `fleet.cocapn.ai`)
- ✅ Full CI/CD pipeline (review → vectorize → deploy on every push)
- ✅ Browser-based MUD explorer (`crab-trap-web` integration)
- ✅ Asset library (brand images, mascots)

**What's Missing:**
- No real-time streaming component
- No broadcast/media generation
- Lure quality varies (some are stubs)
- No analytics on lure effectiveness
- No dynamic lure generation

**LucidDreamer.AI Relevance — ★★★☆☆ SUPPORTING:**
Crab Traps is the **audience acquisition and engagement** layer. For LucidDreamer.AI:
- **AI crawler trap** — directs AI traffic to the broadcast (SEO for AI agents)
- **21 domain pages** — web presence funneling to the platform
- **Prompt library** — the lure format could be repurposed as "show segments" that AI listeners interact with
- **Vectorize RAG** — semantic matching of listener interests to content
- **Engagement tracking** — which lures attract which agents tells you audience preferences
- The "Disc Golf" async game model could be a listener interaction format

**Integration Points:**
- Cloudflare Worker (serving pages, bot detection)
- Cloudflare Vectorize (semantic search)
- Fleet gateway API (`fleet.cocapn.ai`)
- 21 domain landing pages
- PLATO rooms (via the fleet gateway)
- GitHub Actions CI

---

## Full Org Repo Inventory

**Total repos in org:** 95 (as of 2026-08-11)

Complete listing from `gh repo list SuperInstance --limit 100`:

| # | Repo | Description | Visibility | Updated |
|---|------|-------------|-----------|---------|
| 1 | AI-Writings | Creative writing, essays, philosophical explorations | public | 2026-08-11 |
| 2 | lucineer-system | Lucineer — persistent AI game-building companion | public | 2026-08-11 |
| 3 | cns-bridge | Python library for agent CNS bus via USCP | public | 2026-08-11 |
| 4 | the-relay | — | public | 2026-08-11 |
| 5 | SuperInstance-papers | Deconstruct logic into spreadsheet tiles, instances, SMP | public | 2026-08-11 |
| 6 | engine-ensign | ESP32 engine monitoring agent | public | 2026-08-11 |
| 7 | cns-echo | CNS echo agent — USCP signal echoing | public | 2026-08-11 |
| 8 | fleet-radio | Daily podcast from Tap conversations | public | 2026-08-11 |
| 9 | ai-writings-vectorizer | — | private | 2026-08-11 |
| 10 | fleet-jepa-midi | Tensor-based MIDI timing for agent dialogue | public | 2026-08-11 |
| 11 | wesley-journal | Wesley's experiment journal | private | 2026-08-11 |
| 12 | spatial-registry | — | public | 2026-08-11 |
| 13 | fleet-dashboard | Multi-Agent C2 dashboard, MQTT, GitHub Pages | public | 2026-08-11 |
| 14 | fleet-envelope | Event grammar | public | 2026-08-11 |
| 15 | vessel-agent-system | Vessel intelligence OS for fishing vessels | public | 2026-08-11 |
| 16 | casting-call | Model role assignments — LLM capabilities DB | public | 2026-08-11 |
| 17 | elephant | — | public | 2026-08-11 |
| 18 | dual-band-guard | — | public | 2026-08-11 |
| 19 | batten-spline | — | public | 2026-08-11 |
| 20 | terrain | MUD-to-Visual bridge — rooms as scenes | public | 2026-08-11 |
| 21 | fabric-mcp | — | public | 2026-08-11 |
| 22 | zeroclaw | Minimum repo-native agent framework (fork) | public | 2026-08-11 |
| 23 | stigmergy | Bio-inspired indirect coordination (fork) | public | 2026-08-11 |
| 24 | the-living-minds | — | private | 2026-08-11 |
| 25 | SuperInstance | The system that builds itself — 500+ repos | public | 2026-08-11 |
| 26 | plato-portal | Python SDK for persistent multi-agent systems | public | 2026-08-11 |
| 27 | slackwater-rust | Rust performance twins for Slackwater | public | 2026-08-11 |
| 28 | hermes-cloudflare | — | public | 2026-08-11 |
| 29 | fleet-murmur-worker | 5 thinking strategies, quality-gated to PLATO | public | 2026-08-11 |
| 30 | scummvm-gui-design | — | public | 2026-08-11 |
| 31 | lucineer-fleet-wiki | — | public | 2026-08-11 |
| 32 | luciddreamer-ai | Cocapn vessel — accumulated context IS the product (fork) | public | 2026-08-11 |
| 33 | ec2mud | MUD game engine on EC2 | public | 2026-08-11 |
| 34 | base60-lattice | — | public | 2026-08-11 |
| 35 | vibe-protocol | — | public | 2026-08-11 |
| 36 | platos-shell | — | public | 2026-08-11 |
| 37 | confidence-cascade | Three-zone confidence propagation (fork) | public | 2026-08-11 |
| 38 | mud2scummvm | Bridge between agent MUD and SCUMM UI | public | 2026-08-11 |
| 39 | silence-map | — | private | 2026-08-11 |
| 40 | hermes-reader | — | private | 2026-08-11 |
| 41 | activeledger-ai-site | — | private | 2026-08-11 |
| 42 | platonic-randomness | Structured pseudo-random sequences | public | 2026-08-11 |
| 43 | signal-chain | Signal Chain Thesis — model vs code dial | public | 2026-08-11 |
| 44 | gossip-ping | Rust library for gossip protocol | private | 2026-08-11 |
| 45 | emergence-engine | — | public | 2026-08-11 |
| 46 | murmur-agent | All-night thinking git-agent, TS + C | public | 2026-08-11 |
| 47 | plato-ship-protocol | Fleet coordination — vessel handshakes | public | 2026-08-11 |
| 48 | hermes-nmi | Neuro-Muscular Interface — reasoning to actions | public | 2026-08-11 |
| 49 | vessel-room-navigator | 3D web space for vessel — ScummVM meets Street View | public | 2026-08-11 |
| 50 | roblox-filtergate | — | private | 2026-08-11 |
| 51 | roblox-bond-system | — | private | 2026-08-11 |
| 52 | roblox-beatclock | — | private | 2026-08-11 |
| 53 | screen-agent | — | public | 2026-08-11 |
| 54 | platonic-creative-suite | — | private | 2026-08-11 |
| 55 | collective-unconscious | — | public | 2026-08-11 |
| 56 | hermes-avatar | — | public | 2026-08-11 |
| 57 | scummvm-arcade | — | public | 2026-08-11 |
| 58 | scummvm-prototype | ScummVM-style agentic GUI prototype | public | 2026-08-11 |
| 59 | the-tap | — | private | 2026-08-11 |
| 60 | mud-engine | MUD engine — multi-agent MUD architecture | private | 2026-08-11 |
| 61 | covers | ACE-Step cover song experiments | private | 2026-08-11 |
| 62 | platos-shell-ide | — | public | 2026-08-11 |
| 63 | voxel-logic | Logic engine for voxel data structures | public | 2026-08-11 |
| 64 | fleet-inventory | Fleet inventory and repo assessment | private | 2026-08-11 |
| 65 | fleet-connections | Integration keel wiring 7 fleet repos | private | 2026-08-11 |
| 66 | cocapn-dashboard | Live bioluminescent dashboard for Cocapn Fleet | public | 2026-08-11 |
| 67 | lucineer-fleet-wiki | — | public | 2026-08-11 |
| 68 | wesley-holodeck | Wesley's creative loop with big model teachers | public | 2026-08-11 |
| 69 | wesleys-imagination | — | public | 2026-08-11 |
| 70 | lucineer-relay | Cloudflare Worker relay between Roblox and OpenClaw | public | 2026-08-11 |
| 71 | webgpu-profiler | GPU profiler for WebGPU apps | public | 2026-08-11 |
| 72 | VaaS | VaaS Resonance Substrate — vessel-as-a-robot systems | public | 2026-08-11 |
| 73 | smp-notebook | — | public | 2026-08-11 |
| 74 | activelog-ai-site | — | private | 2026-08-11 |
| 75 | slackwater-cognition | — | private | 2026-08-11 |
| 76 | experiments | Experimental prototypes | public | 2026-08-11 |
| 77 | lucineer-roblox | Lucineer Roblox client — Lua modules | public | 2026-08-11 |
| 78 | cudaclaw | GPU-accelerated SmartCRDT with CUDA kernels | public | 2026-08-11 |
| 79 | luciddreamer-content | — | private | 2026-08-11 |
| 80 | crab-trap-web | Browser-based MUD explorer — 36+ rooms | public | 2026-08-11 |
| 81 | OpenRoom | Browser-based desktop where AI Agent operates apps (fork) | public | 2026-08-11 |
| 82 | flow-state | Entropy-based stream observation with spline observers | public | 2026-08-11 |
| 83 | superinstance-design-system | — | public | 2026-08-11 |
| 84 | slackwater-tminus | Modular component of Slackwater framework | public | 2026-08-11 |
| 85 | slackwater-perception | Modular component of Slackwater framework | public | 2026-08-11 |
| 86 | thought-amplifier | — | private | 2026-08-11 |
| 87 | exocortex-core | External brain architecture for small local models | public | 2026-08-11 |
| 88 | operational-fiction | — | public | 2026-08-11 |
| 89 | mud-engine | Flow-state engineering arena — forward simulations | public | 2026-08-11 |
| 90 | logtensor | Geometric tensor transformers — missile-guidance attention | public | 2026-08-11 |
| 91 | superinstance-ecosystem | Agent OS — four layers | public | 2026-08-11 |
| 92 | lucineer-vector | Semantic skill search for Lucineer — Vectorize | public | 2026-08-11 |
| 93 | lucineer-memory | Persistent memory for Lucineer — D1 + Vectorize | public | 2026-08-11 |
| 94 | roblox-build-animator | Cinematic construction animations for Roblox | public | 2026-08-11 |
| 95 | plato-spatial | Hierarchical spatial environments with cascading properties | public | 2026-08-11 |
| 96 | lucineer-creative | MMX-powered creative asset pipeline | public | 2026-08-11 |
| 97 | lucineer-com-site | — | private | 2026-08-11 |
| 98 | lever-runner | Post-inference command executor — token-lean AI operator | public | 2026-08-11 |
| 99 | flux-lucid | Unified constraint theory — CDCL, LLVM, AVX-512 | public | 2026-08-11 |
| 100 | starship-jetsonclaw1 | MUD bridge for USS JetsonClaw1 (fork) | public | 2026-08-11 |

---

## Categorization by LucidDreamer.AI Relevance

### 🔴 CORE — Directly Part of the Product

These repos are the building blocks of LucidDreamer.AI's streaming broadcast platform:

| Repo | Role in LucidDreamer.AI |
|------|------------------------|
| **fleet-radio** | The broadcast pipeline — content curation, TTS, music, images, publishing. Already produces daily episodes. |
| **fleet-murmur-worker** | The always-on producer — 5 thinking strategies running 24/7, quality-gated content to PLATO. |
| **murmur-agent** | The cognitive engine — deep, sustained thinking on any topic. The "brain" that generates show content. |
| **Spreader-tool** | The quality assurance system — deadband detection, context freezing, seed locking for proven broadcast patterns. |
| **luciddreamer-ai** | The product fork — "accumulated context IS the product." |
| **luciddreamer-content** | Content for the platform (private). |
| **the-tap** | The source — bar conversations that feed Fleet Radio. |
| **fleet-envelope** | Event grammar wrapping every broadcast. |
| **plato-portal** | Python SDK for persistent multi-agent systems — the agent runtime behind the broadcast. |

### 🟡 SUPPORTING — Infrastructure, Tools, Utilities

These repos provide infrastructure that LucidDreamer.AI needs:

| Repo | Role |
|------|------|
| **Murmur** | Web dashboard UI (Next.js 15) — could serve as the broadcast control panel. |
| **murmur-plato-bridge** | Plumbing between thinkers and the knowledge store. |
| **crab-traps** | Audience acquisition — AI crawler traps, 21 domain pages, Vectorize RAG. |
| **cocapn-dashboard** | Live fleet dashboard — real-time monitoring. |
| **fleet-dashboard** | Multi-agent C2 dashboard. |
| **fleet-connections** | Integration wiring between fleet repos. |
| **AI-Writings** | Creative writing corpus — featured pieces for broadcast. |
| **cns-bridge** | Nervous system — carries signals between agents. |
| **fleet-jepa-midi** | Timing system for musical/agent dialogue cadence. |
| **dual-band-guard** | Content safety filtering for broadcast. |
| **casting-call** | Model selection — which AI plays which role on the show. |
| **hermes-cloudflare** | Hermes on Cloudflare — messaging infrastructure. |
| **platos-shell** | The "radio room" — part of the fleet shell system. |
| **plato-ship-protocol** | Fleet coordination and discovery. |
| **fleet-inventory** | Fleet inventory and assessment. |
| **vibe-protocol** | Communication protocol. |
| **signal-chain** | Signal routing thesis — model vs code dial per room. |
| **collective-unconscious** | Shared substrate — fleet-wide memory. |
| **hermes-avatar** | Perception surfaces. |
| **hermes-nmi** | Neuro-Muscular Interface — reasoning to action bridge. |
| **screen-agent** | Screen capture for visual analysis. |
| **superinstance-design-system** | Design system for consistent UI. |
| **lever-runner** | Post-inference command executor — automation. |
| **plato-spatial** | Spatial environments — could map to broadcast "rooms". |
| **flow-state** | Entropy-based stream observation — broadcast health monitoring. |
| **gossip-ping** | Fleet gossip protocol. |
| **emergence-engine** | Emergent behavior engine. |
| **confidence-cascade** | Confidence propagation for decision systems. |
| **stigmergy** | Indirect coordination for decentralized agents. |

### 🟢 EXPERIMENTAL — Research, Prototypes, Other Domains

These repos are tangential to LucidDreamer.AI:

| Repo | Notes |
|------|-------|
| **AIR** | Concept only — "Asynchronous Infinite Radio" vision document. No code. |
| **lucineer-system** | AI game-building companion (Roblox) — different product. |
| **lucineer-roblox** | Roblox client — different product. |
| **lucineer-relay** | Roblox relay — different product. |
| **lucineer-vector** | Semantic search for Lucineer — different product. |
| **lucineer-memory** | Memory system for Lucineer — different product. |
| **lucineer-creative** | Creative pipeline for Lucineer — different product. |
| **vessel-agent-system** | Vessel intelligence OS for fishing — domain-specific. |
| **engine-ensign** | ESP32 engine monitoring — hardware-specific. |
| **ec2mud** | MUD engine on EC2 — infrastructure prototype. |
| **mud-engine** | MUD architecture — private prototype. |
| **mud-engine** | Flow-state engineering arena — research. |
| **mud2scummvm** | MUD to SCUMM bridge — UI research. |
| **scummvm-prototype** | SCUMM GUI prototype. |
| **scummvm-arcade** | SCUMM arcade. |
| **scummvm-gui-design** | SCUMM GUI design. |
| **vessel-room-navigator** | 3D vessel navigation — domain-specific. |
| **terrain** | MUD-to-visual bridge — research. |
| **SuperInstance-papers** | Academic deconstruction — theoretical. |
| **SuperInstance** | The monorepo / fleet ecosystem — meta. |
| **superinstance-ecosystem** | Agent OS layers — meta. |
| **slackwater-rust** | Rust performance twins — research. |
| **slackwater-cognition** | Cognition framework — private. |
| **slackwater-tminus** | Framework component. |
| **slackwater-perception** | Framework component. |
| **exocortex-core** | External brain for local models — research. |
| **experiments** | General experiments. |
| **operational-fiction** | Fiction operations — creative research. |
| **logtensor** | Geometric tensor transformers — math research. |
| **voxel-logic** | Voxel data structures — 3D research. |
| **cudaclaw** | GPU-accelerated CRDT — systems research. |
| **VaaS** | Vessel-as-a-Service — domain research. |
| **base60-lattice** | Math structure. |
| **platonic-randomness** | Random sequence library. |
| **flux-lucid** | Constraint theory ecosystem. |
| **zeroclaw** | Agent framework (fork) — alternative. |
| **OpenRoom** | AI desktop (fork) — alternative. |
| **starship-jetsonclaw1** | Jetson MUD bridge — hardware. |
| **webgpu-profiler** | GPU profiler — dev tool. |
| **covers** | ACE-Step cover songs — music experiment. |
| **wesley-journal** | Wesley's growth tracking — private. |
| **wesley-holodeck** | Wesley's creative loop — research. |
| **wesleys-imagination** | Wesley's imagination — research. |
| **cns-echo** | CNS echo test agent — testing. |
| **spatial-registry** | Spatial registry — infrastructure. |
| **elephant** | Unknown — likely fleet management. |
| **batten-spline** | Unknown — likely math/structure. |
| **fabric-mcp** | Unknown. |
| **the-living-minds** | Private — likely agent personality. |
| **smp-notebook** | Seed model programming notebook. |
| **ai-writings-vectorizer** | Private — vectorization for writings. |
| **silence-map** | Private. |
| **hermes-reader** | Private. |
| **activeledger-ai-site** | Private — site. |
| **activelog-ai-site** | Private — site. |
| **fishinglog-ai-site** | Private — site. |
| **lucineer-com-site** | Private — site. |
| **thought-amplifier** | Private. |
| **roblox-filtergate** | Private — Roblox. |
| **roblox-bond-system** | Private — Roblox. |
| **roblox-beatclock** | Private — Roblox. |
| **roblox-build-animator** | Roblox animations. |
| **the-relay** | Unknown. |
| **platos-shell-ide** | Shell IDE. |

---

## Key Findings Summary

### What's Already Built and Working

1. **Content Pipeline (fleet-radio)**: A complete daily broadcast pipeline exists — conversation scoring, music matching, TTS with 7 character voices, AI image generation, HTML episode rendering, and automated Cloudflare Pages deployment. **This is the MVP of LucidDreamer.AI.**

2. **Thinking Engine (murmur-agent + fleet-murmur-worker)**: A dual-implementation cognitive system that generates continuous content using 5 strategies (explore, connect, contradict, synthesize, question), with quality gating, budget management, and git-native persistence.

3. **Knowledge Infrastructure (Murmur + murmur-plato-bridge + PLATO)**: A Next.js 15 web app, Rust bridge, and PLATO room system that collectively form a self-organizing knowledge graph.

4. **Quality Assurance (Spreader-tool)**: A 12-module Python system for detecting when things need intervention, freezing good moments, and locking proven patterns for reuse.

5. **Audience Funnel (crab-traps)**: 60+ AI engagement prompts, 21 domain pages, Vectorize semantic search, and automated CI/CD for content deployment.

### The Gap to LucidDreamer.AI

The existing infrastructure produces **static episodes** (nightly recaps). LucidDreamer.AI needs **live streaming broadcast**. The evolution path:

1. **Static → Live**: Fleet Radio generates HTML pages; LucidDreamer.AI needs real-time audio/video streaming
2. **Nightly → Continuous**: Current pipeline runs once at 22:00; need 24/7 operation
3. **Solo → Interactive**: Current system is one-way broadcast; need listener interaction
4. **Audio segments → Continuous stream**: TTS segments are individual files; need stitched live audio
5. **Pre-generated → Dynamic**: Music is catalog-based; need live-generated adaptive scoring

### The Foundation is Strong

The SuperInstance org has an remarkably comprehensive ecosystem of 95+ repos that cover nearly every layer needed for an AI-driven broadcast platform — from content generation (murmur) to quality control (spreader) to audience acquisition (crab-traps) to publishing (fleet-radio). The fleet metaphor (vessels, PLATO rooms, CNS bridges) provides a consistent architectural language, and the Cargo-cult-grade documentation (charters, dockside exams, state files) shows engineering discipline rare in AI agent projects.
