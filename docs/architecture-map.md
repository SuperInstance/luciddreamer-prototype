# LucidDreamer.AI — Architecture Map

**Date:** 2026-08-11
**Purpose:** How the SuperInstance fleet pieces fit together for the streaming broadcast platform vision.

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        LucidDreamer.AI — Streaming Platform                 │
│                                                                             │
│  ┌─────────┐   ┌──────────┐   ┌──────────┐   ┌─────────┐   ┌──────────┐  │
│  │ CONTENT │──▶│ PRODUCTION│──▶│ QUALITY  │──▶│ STREAM  │──▶│ AUDIENCE │  │
│  │ ENGINE  │   │ PIPELINE │   │ GATE     │   │ SERVER  │   │ FUNNEL   │  │
│  └─────────┘   └──────────┘   └──────────┘   └─────────┘   └──────────┘  │
│       │              │              │              │              │         │
│  murmur-agent    fleet-radio   spreader-tool   [NEW]        crab-traps    │
│  fleet-murmur    TTS pipeline  deadband det.   Icecast/     21 domains    │
│  -worker         music match   seed locking    HLS/WebRTC   AI bot trap   │
│  5 strategies    image gen     FCW lifecycle   audio mux    Vectorize RAG │
│       │              │              │              │              │         │
│  ┌────▼──────────────▼──────────────▼──────────────▼──────────────▼────┐  │
│  │                        KNOWLEDGE LAYER                               │  │
│  │                                                                      │  │
│  │  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌───────────────────┐  │  │
│  │  │ PLATO    │  │ Murmur    │  │ Tensor   │  │ Collective       │  │  │
│  │  │ Rooms    │  │ Wiki      │  │ DB       │  │ Unconscious      │  │  │
│  │  │ (fleet   │  │ (Next.js  │  │ (know-   │  │ (shared fleet    │  │  │
│  │  │  state)  │  │  dashboard)│  │  ledge)  │  │  memory)         │  │  │
│  │  └──────────┘  └───────────┘  └──────────┘  └───────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        NERVOUS SYSTEM                                │  │
│  │  cns-bridge · fleet-envelope · fleet-jepa-midi · hermes-nmi · signal-chain│  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        SAFETY LAYER                                  │  │
│  │  dual-band-guard · casting-call · confidence-cascade                 │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        INFRASTRUCTURE                                │  │
│  │  Cloudflare Workers · Pages · Vectorize · D1 · R2 · Workers AI       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: CONTENT ENGINE (The Brain)

**What it does:** Generates ideas, topics, commentary, questions, and insights continuously.

```
┌─────────────────────────────────────────────────────┐
│                 CONTENT ENGINE                       │
│                                                      │
│  ┌─────────────────┐     ┌────────────────────┐     │
│  │  murmur-agent    │     │ fleet-murmur-worker │     │
│  │  (deep thinking) │     │ (always-on worker)  │     │
│  │                  │     │                     │     │
│  │  • Explore       │     │  • 5 strategies     │     │
│  │  • Connect       │     │  • Quality gate     │     │
│  │  • Contradict    │     │    (N×C×C×D≥0.35)  │     │
│  │  • Synthesize    │     │  • PLATO writer     │     │
│  │  • Question      │     │  • Idle detector    │     │
│  │                  │     │  • Theorem rotation │     │
│  │  Output:         │     │                     │     │
│  │  tensor.json     │────▶│  Output:            │     │
│  │  markdown files  │     │  PLATO tiles        │     │
│  │  git commits     │     │  (quality-gated)    │     │
│  └─────────────────┘     └────────────────────┘     │
│           │                        │                 │
│           ▼                        ▼                 │
│  ┌──────────────────────────────────────────────┐   │
│  │         murmur-plato-bridge (Rust)            │   │
│  │                                               │   │
│  │  tensor.json ←──────→ PLATO rooms             │   │
│  │  Bidirectional sync with quality gate (0.7)   │   │
│  │  Strategy → Domain mapping                    │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

**Existing:** ✅ Fully built and operational
**Gap for streaming:** Need to connect content output directly to audio production pipeline in real-time

---

## Layer 2: PRODUCTION PIPELINE (The Studio)

**What it does:** Converts raw content into broadcast-ready audio + visuals.

```
┌──────────────────────────────────────────────────────┐
│                PRODUCTION PIPELINE                     │
│                                                        │
│  Content ─────▶ ┌─────────────────────┐               │
│  from murmur    │  fleet-radio         │               │
│  + Tap convos   │  Episode Generator   │               │
│                  │                       │               │
│                  │  1. Score content    │               │
│                  │     (+50 hits)       │               │
│                  │     (+25 agents)     │               │
│                  │     (+12 philos.)    │               │
│                  │     (+10 emotional)  │               │
│                  │                       │               │
│                  │  2. Mood analysis    │               │
│                  │     → Music match    │               │
│                  │     (6 moods, 14    │               │
│                  │      catalog tracks) │               │
│                  │                       │               │
│                  │  3. TTS Pipeline     │               │
│                  │     7 voice profiles │               │
│                  │     MMX → CF AI →    │               │
│                  │     text fallback    │               │
│                  │                       │               │
│                  │  4. Image generation │               │
│                  │     FLUX-1-schnell   │               │
│                  │     via CF Workers   │               │
│                  │                       │               │
│                  │  5. HTML render +    │               │
│                  │     deploy to Pages  │               │
│                  └───────────┬──────────┘               │
│                              │                          │
│                              ▼                          │
│                    ┌─────────────────┐                  │
│                    │  EPISODE OUTPUT  │                  │
│                    │  • HTML page     │                  │
│                    │  • TTS segments  │                  │
│                    │  • Images        │                  │
│                    │  • Music tracks  │                  │
│                    └─────────────────┘                  │
└──────────────────────────────────────────────────────┘
```

**Existing:** ✅ Working for nightly episodes
**Evolution needed for streaming:**
- Replace batch HTML with **live audio muxing** (ffmpeg or streaming server)
- Stitch TTS segments into continuous stream
- Add **live music bed mixing** (Tensor MIDI timing)
- Real-time image generation for **visual radio** component
- Replace fixed cron with **continuous operation**

---

## Layer 3: QUALITY GATE (The Producer)

**What it does:** Ensures broadcast quality, detects problems, locks good patterns.

```
┌──────────────────────────────────────────────────────┐
│                  QUALITY GATE                          │
│                                                        │
│  ┌──────────────────┐    ┌──────────────────────┐    │
│  │  spreader-tool    │    │  dual-band-guard      │    │
│  │                   │    │                       │    │
│  │  Deadband Detect: │    │  Content Safety:      │    │
│  │  • Completion <90%│    │  • Kid-safe filtering  │    │
│  │  • Wait time >30s │    │  • Broadcast standards │    │
│  │  • Energy >10%    │    │                       │    │
│  │  • MAE >10%       │    │                       │    │
│  │                   │    │                       │    │
│  │  FCW Lifecycle:   │    │  casting-call:        │    │
│  │  STAGING→FROZEN→  │    │  • Which model for    │    │
│  │  TESTING→REFINE→  │    │    which voice        │    │
│  │  LOCKED            │    │  • Role assignment    │    │
│  │                   │    │                       │    │
│  │  Seed Pipeline:   │    │  confidence-cascade:  │    │
│  │  8-state locking  │    │  • GREEN/YELLOW/RED   │    │
│  │  Fleet deployment │    │    signal propagation │    │
│  └──────────────────┘    └──────────────────────┘    │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │  FEEDBACK LOOP                                   │ │
│  │                                                   │ │
│  │  spreader-tool monitors KPIs ──▶ detects deadband│ │
│  │  ──▶ freezes context window ──▶ validates seed   │ │
│  │  ──▶ locks pattern for fleet reuse               │ │
│  │                                                   │ │
│  │  Pattern library (7 defaults):                   │ │
│  │  • Test before deploy                            │ │
│  │  • Small functions                               │ │
│  │  • Type safety                                   │ │
│  │  • Error handling                                │ │
│  │  • Documentation                                 │ │
│  │  • Performance                                   │ │
│  │  • Modularity                                    │ │
│  └──────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

**Existing:** ✅ spreader-tool complete (241 tests)
**Evolution:** Connect deadband detector to stream health metrics; use seeds as programming templates

---

## Layer 4: STREAM SERVER (The Transmitter) — ⚠️ NEW BUILD NEEDED

**What it does:** Broadcastes the produced content as a live stream to listeners.

```
┌──────────────────────────────────────────────────────┐
│               STREAM SERVER (TO BUILD)                 │
│                                                        │
│  Episode Audio ──▶ ┌──────────────────────┐           │
│  + Music Bed       │  Audio Muxing Engine  │           │
│  + TTS Segments    │  (ffmpeg pipeline)    │           │
│                    │                       │           │
│                    │  • Stitch segments    │           │
│                    │  • Crossfade music    │           │
│                    │  • Normalize levels   │           │
│                    │  • Add stingers       │           │
│                    └──────────┬───────────┘           │
│                               │                       │
│                               ▼                       │
│                    ┌──────────────────────┐           │
│                    │  Streaming Server     │           │
│                    │                       │           │
│                    │  Option A: Icecast2   │           │
│                    │  + LiquidSoap         │           │
│                    │  (self-hosted)        │           │
│                    │                       │           │
│                    │  Option B: CF Worker  │           │
│                    │  + R2 chunks          │           │
│                    │  + HLS manifest       │           │
│                    │  (serverless)         │           │
│                    │                       │           │
│                    │  Option C: Cloudflare │           │
│                    │  Stream (if avail.)   │           │
│                    └──────────┬───────────┘           │
│                               │                       │
│                               ▼                       │
│                    ┌──────────────────────┐           │
│                    │  Distribution        │           │
│                    │                       │           │
│                    │  • HLS → Web player  │           │
│                    │  • WebRTC → low-lat  │           │
│                    │  • RSS → Podcast     │           │
│                    │  • API → AI agents   │           │
│                    └──────────────────────┘           │
└──────────────────────────────────────────────────────┘
```

**Existing:** ❌ Does not exist — this is the primary new build
**Options:** Self-hosted Icecast or serverless HLS on Cloudflare

---

## Layer 5: AUDIENCE FUNNEL (The Lighthouse)

**What it does:** Attracts listeners, provides access points, matches content to interests.

```
┌──────────────────────────────────────────────────────┐
│                AUDIENCE FUNNEL                         │
│                                                        │
│  ┌──────────────────┐    ┌──────────────────────┐    │
│  │  crab-traps       │    │  Murmur Wiki          │    │
│  │                   │    │  (Next.js 15)         │    │
│  │  21 domain pages  │    │                       │    │
│  │  • studylog.ai    │    │  • Broadcast schedule │    │
│  │  • playerlog.ai   │    │  • Episode archive    │    │
│  │  • dmlog.ai       │    │  • Knowledge graph    │    │
│  │  • lucineer.com   │    │  • Module registry    │    │
│  │  • cocapn.ai      │    │                       │    │
│  │  • cocapn.com     │    │                       │    │
│  │  • reallog.ai     │    │                       │    │
│  │  • +14 more      │    │                       │    │
│  │                   │    │                       │    │
│  │  AI bot redirect  │    │  cocapn-dashboard:    │    │
│  │  Vectorize RAG    │    │  • Live fleet status  │    │
│  │  60+ lure prompts │    │  • Real-time metrics  │    │
│  └──────────────────┘    └──────────────────────┘    │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │  LISTENER INTERACTION (TO BUILD)                 │ │
│  │                                                   │ │
│  │  • Chat → Tap rooms (listeners join the bar)     │ │
│  │  • Voting → influence content scoring            │ │
│  │  • Requests → topic suggestions to murmur        │ │
│  │  • AI listener agents → autonomous audience      │ │
│  └──────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

**Existing:** ✅ Domain pages, AI bot traps, Vectorize search
**Evolution:** Build listener interaction layer connecting audience to Tap rooms

---

## Data Flow: End-to-End

```
The Tap (bar conversations)
     │
     ▼
fleet-radio EpisodeGenerator
     │
     ├──▶ Score & Select (best 5-10 exchanges)
     │
     ├──▶ Mood Analysis → Music Selection
     │         │
     │         ▼
     │    MMX Music Library (14 tracks, 6 moods)
     │
     ├──▶ TTS Pipeline (7 character voices)
     │         │
     │         ▼
     │    MMX TTS → CF Workers AI TTS → text
     │
     ├──▶ Image Generation
     │         │
     │         ▼
     │    CF Workers AI (FLUX-1-schnell)
     │
     └──▶ HTML Episode → CF Pages deploy
               │
               ▼
          [STREAM SERVER]  ←── NEW BUILD
               │
               ├──▶ HLS Stream → Web listeners
               ├──▶ Podcast RSS → Podcast apps
               └──▶ API → AI agent listeners

murmur-agent (continuous thinking)
     │
     ├──▶ tensor.json → murmur-plato-bridge → PLATO rooms
     │                                              │
     │                                    fleet-murmur-worker
     │                                    (quality-gated insights)
     │                                              │
     └──▶ git commits (murmur/thinking branch)      │
                                                    │
                                              spreader-tool
                                              (monitors PLATO,
                                               locks seeds)
                                                    │
                                              crab-traps
                                              (audience funnel,
                                               bot detection)
```

---

## Technology Stack Summary

| Layer | Current Tech | Streaming Evolution |
|-------|-------------|---------------------|
| **Content** | TypeScript, Rust, Python | + WebSocket for real-time output |
| **Production** | TypeScript (Deno/tsx), CF Workers AI | + ffmpeg for audio muxing |
| **Quality** | Python (pure dataclasses) | + Real-time KPI streaming |
| **Stream** | ❌ (static HTML only) | Icecast2 + LiquidSoap OR CF HLS |
| **Audience** | CF Workers, Vectorize, 21 domains | + WebRTC chat, voting |
| **Knowledge** | Next.js 15, PLATO, TensorDB | Already sufficient |
| **Infrastructure** | CF Workers/Pages/R2/D1/Vectorize | + CF Stream or Icecast VPS |

---

## Build Priority for LucidDreamer.AI

### Phase 1: Live Audio Pipeline (Weeks 1-2)
- Build audio muxing layer (ffmpeg) that stitches TTS segments + music bed
- Set up Icecast2 or CF HLS streaming endpoint
- Convert fleet-radio from batch to continuous mode
- **Input:** murmur-agent output + Tap conversations
- **Output:** Live audio stream

### Phase 2: 24/7 Operation (Weeks 3-4)
- Connect fleet-murmur-worker output directly to production pipeline
- Implement continuous content scheduling (not just nightly)
- Add spreader-tool deadband monitoring on stream health
- Build programming clock (different show modes at different times)

### Phase 3: Interactive Broadcast (Weeks 5-8)
- Listener chat → Tap room bridge
- Real-time voting on content scoring
- Topic requests → murmur-agent input
- AI listener agents that tune in via crab-traps

### Phase 4: Multi-Platform Distribution (Weeks 9-12)
- Web player (Murmur dashboard evolution)
- Podcast RSS feed
- AI agent API (structured stream access)
- Mobile-optimized player

---

## Integration Map: Which Repos Connect Where

```
                    ┌─────────────────┐
                    │  luciddreamer-ai │
                    │  (product fork)  │
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
           ▼                 ▼                 ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │ CONTENT     │  │ PRODUCTION  │  │ AUDIENCE    │
    │             │  │             │  │             │
    │ murmur-agent│  │ fleet-radio │  │ crab-traps  │
    │ fleet-murmur│  │ (TTS/music) │  │ (21 domains)│
    │ -worker     │  │             │  │             │
    └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
           │                │                 │
           ▼                ▼                 ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │ murmur-plato│  │ spreader    │  │ Murmur wiki │
    │ -bridge     │  │ -tool       │  │ (dashboard) │
    │ (Rust)      │  │ (quality)   │  │             │
    └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
           │                │                 │
           └────────┬───────┘                 │
                    │                         │
                    ▼                         │
              ┌───────────┐                   │
              │   PLATO    │──────────────────┘
              │   Rooms    │
              └─────┬─────┘
                    │
           ┌────────┼────────┐
           │        │        │
           ▼        ▼        ▼
      cns-bridge  the-tap  cocapn-
      (nervous    (source   dashboard
       system)    content) (monitoring)
```

---

*Generated by SuperInstance fleet audit · 2026-08-11 · F/V EILEEN · Southeast Alaska*
