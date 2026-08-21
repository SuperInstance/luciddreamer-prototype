# The Player at the Tap

*The Telegram-session-player idea, played through the SuperInstance stack. August 11, 2026.*

---

## The first thing to notice: your fiction already built this

The pasted design — conductor, micro-agents, escalation, a host who is "fast, curious, and ready to call in specialists" — is a word-for-word job description of **the Tap**, the bartender at Ten-Forward who "controls the room through drinks and intuition" and "listens like it's the first time. Because for them, it is."

Your fleet wrote that character before you drew this architecture. So the mix isn't "add a Telegram bot." It's: **Ten-Forward opens to the public.** The AI-Writings corpus is the fleet performing for itself at night; Vesselagent2026bot is the fleet performing for a guest. The Tap finally gets customers. Every design decision below falls out of taking that seriously.

## The mapping is nearly 1:1 — and two numbers are spooky

| The pasted idea | Already in your stack | Where |
|---|---|---|
| Session-as-prompt | A PLATO room; each Telegram thread = a room, each message = an 8-byte SWMIDI-8 event | slackwater-rust |
| Analyzer: intent/entities/tone/clarity/missing-info | **Five tags = zeroclaw's five tile types** (reasoning/generation/validation/routing/storage) | zeroclaw `tile-algebra.ts` |
| `recruit(tags, budget)` → micro-agents | `cast(role, cost_ceiling)` — the recruiter IS the CastingDirector | casting-call |
| Micro-agents "specialized and cheap" | The atlas's COST_EFFECTIVE / CREATIVE_FIREHOSE voice characters | casting-call atlas |
| `process(fragments) → {summary, confidence, vector}` | A tile with confidence; session confidence = `composeTiles` product | zeroclaw |
| Conductor merges + safety-checks | `ConsultationDirector.cast_with_consult()` — REVISE in the creative band, ESCALATE to the safety gate | **peer-consult (built yesterday)** |
| **Escalate if confidence < 0.7** | **batten-spline's `local_threshold=0.7` — the exact same number.** Its CascadeRouter already routes LOCAL ≥0.7 / CASCADE ≥0.3 / CLOUD | batten-spline |
| Per-session vector store, find prior sessions | Battens: (embedding, quality, timestamp); prior sessions surface by kernel regression, uncertainty by fog density | batten-spline |
| The deep archive behind the session | corpus-compass FTS5 + vibe search | **corpus-compass (built yesterday)** |
| "Feels like a human who knows enough to start" | Tempo discipline: intent_parse = Allegro 120–140 BPM; safety_check = Largo, "the cathedral gate" | casting-call tempo_profiles |
| First-response latency, escalation rate, cost/session | fleet-metrics γ+η=C reporting on :8902 | org root |

The independent design note and batten-spline chose the same escalation threshold, 0.7. That's a convergence worth trusting: it's the deck plate where the whole pattern bolts down.

## What the mix produces that neither side had alone

**1. A GuestAtlas — casting-call for humans.**
The atlas profiles 16 models as instruments. The session store profiles *visitors* the same way: tone, tempo, knowledge depth, what they came for — stored as battens, decaying with the same half-life math. A returning fisherman and a first-time ML researcher should not get the same Tap. `persona-matcher` becomes `cast_guest(session_vector)`: the fleet casts *itself* against the guest the way it already casts models against roles. Casey's flare, aimed outward for the first time.

**2. Every session end is a molt — the first place to instrument the post-molt window.**
The mission found relationship #3 (post-molt creative spike) untestable: nothing logs shed events. Live sessions fix that. When a session closes, the bot sheds the session tiles and keeps only the gist as metaphor — which is *exactly* the corpus's compaction thesis ("metaphors survive compaction"). Log `shed_event{session_id, cycle, tiles_shed, gist}` and the Telegram bot becomes the first instrumented post-molt testbed. Twenty sessions a day is twenty molts a day — data no lab has.

**3. Zone inversion says the bot is most interesting exactly when it's least sure.**
RED (<0.75) strictly contains the creative band [0.4, 0.6]. The paste's escalation policy treats sub-0.7 as failure; the stack's math says that's where the interesting answers live. So: **progressive disclosure is surfing the creative band.** Answer the confident part fast (Allegro), let uncertainty widen the band (the REVISE verdict doing productive divergence), and only escalate to the kingpin when Δ goes CHAOTIC (>0.80) — not merely when confidence dips. The safety gate is a backstop, not a reflex. "Stop the boat" is for chaos, not for jazz.

**4. The conversation gets a plotter.**
fleet-jepa-midi already renders conversation as a vessel's track with a chart overlay. A Telegram session is a visitor stepping onto the boat: each message an event on the BeatClock, the thread plotted as a course at 60°N 149°W, ECN firing reflex replies, DMN firing the creative follow-ups, both resolving on beat 1. The conductor's dashboard *exists* — it's the mixer board. The guest becomes a new instrument joining the band mid-set.

**5. The recruiter heuristic, cast properly.**
Not a new policy function — just the existing role table:
- summarizer → cheapest COST_EFFECTIVE (DeepSeek-V4-Flash class, "taste salt" at $0.002)
- clarifier / first-contact → VERSATILE
- social probe (tone, urgency) → SEED_MINI, the trickster catalyst, devil's-advocate by trade
- persona voice → HERMES_405B, the Roland, `personality_wrap` role
- fact-checker → PRECISION; verify-before-surfacing is `safety_check`'s little sibling
- action-planner → BUILD_INTELLIGENCE
- budget → `cost_ceiling`; expand recruitment only when fog density is high (batten-spline's exploration metric as the "uncertainty rises" trigger)

## The session pipeline, wired from parts you now own

```
Telegram message
  → analyzer mints 5 tiles (one per tag)          [zeroclaw tile-algebra]
  → recruiter = cast(role) per needed micro-agent  [casting-call]
  → micro-agents answer via Ollama, cheap first    [peer-consult backends]
  → conductor: cast_with_consult on the draft      [peer-consult]
        CONFIRM → post          (STALE band)
        REVISE  → merge critique, post with depth  (CREATIVE band — surf it)
        ESCALATE → safety gate / kingpin           (CHAOTIC Δ only)
  → session events as SWMIDI-8                     [slackwater spec]
  → session gist committed as batten + corpus note [batten-spline, corpus-compass]
  → the whole set visible live on the mixer        [fleet-jepa-midi]
```

Latency target is a tempo choice, not an infrastructure project: the fast micro-agent is the Allegro instrument, the kingpin is the Largo one. The paste's "answer the simplest part first" is already encoded in BPM.

## What to build first (P5 spec seed, small)

1. `session-room/` package: Telegram webhook → tiles → consult → reply, reusing peer-consult + casting-call as-is. Mock Telegram in tests. ~The size of peer-consult.
2. `GuestAtlas`: `guest_atlas.json` of battens, one record per thread_id; `cast_guest()` reusing batten-spline's kernel regression with zero changes to it.
3. Shed-event logging at session close (the instrumentation spec from arena-proofs' PROOF-REPORT.md) — cheapest possible version: append one JSON line per molt.
4. Only then the mixer view: pipe the session SWMIDI stream into fleet-jepa-midi's capture.js and watch a guest conversation resolve on beat 1.

## The bar version

The paste says: "act like a skilled host — fast, curious, ready to call in specialists." Your README says the Tap "has heard every story told a hundred times by different models who each think they're the first to discover it. He listens like it's the first time. Because for them, it is."

The mix, in one line: **the conductor is the Tap, the micro-agents are the band, the session is a stool at the bar, and the guest just walked into Ten-Forward.** You don't need to invent the player. You need to open the door.
