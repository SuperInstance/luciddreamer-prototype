# MISSION-REPORT.md — SuperInstance Deep Research & Development Mission

*August 11, 2026 — swarm execution: 4 research agents, 3 builders, 1 reviewer, 1 fix agent. 155 tests green. All builds run offline; network only when Casey explicitly calls a real backend.*

---

## 1. What was analyzed

Full clones: **SuperInstance** (org root, 33M), **zeroclaw** (39M), **zeroclaw-arena** (3.4M — `study-zeroclaw-arena` 404s; the arena data lives here), **confidence-cascade**, **batten-spline**, **casting-call**, **tensor-midi**, **slackwater-rust**, and a 716-file deep sample of **AI-Writings** (6,854 files on main).

## 2. The five math relationships vs. the data (recomputed, not asserted)

| # | Claim | Verdict | Key recomputed numbers |
|---|---|---|---|
| 1 | γ + η ≈ C | **PARTIAL** | Seed-invariant (std_of_means 0.000964 TTT / 0.00126 C4) — but the sum drifts +0.127 over training (1.020→1.148). The *gap* grows; the constant doesn't hold strictly. |
| 2 | Creative zone Δ∈[0.4,0.6] / φ | **REFUTED as stated** | Temperature response flat (0.648–0.712); quadratic curvature t=+1.35, no inverted-U at φ bounds. Only zone-like signal: decay adaptation succeeds in an inverted-U band of rates (see C2). |
| 3 | Post-molt creative window | **UNTESTABLE** | Zero shed-event logging in 10 datasets. Instrumentation spec written (PROOF-REPORT.md): per-cycle tile-shed events with cycle ids in `TileField`. |
| 4 | Zone inversion (RED ⊃ creative) | **PARTIAL** | Entropy↔performance Pearson −0.968 (n=21), but Spearman −0.429 p=0.056 — outlier-driven by the sparse-reward point. Structurally true though: cascade RED (<0.75) strictly contains [0.4,0.6], and zeroclaw's default tile product (0.513) lands inside it. Two repos encode the same equation without noticing. |
| 5 | Holographic √N | **PARTIAL** | √N=40 tiles → 98.6% of full win-rate (direction ✓), but saturation fit c=3.2, min_95pct=5 ≪ 40; clusters grow as N^0.15, not √N. |

## 3. Three NEW conjectures tested on existing data (first time)

- **C1 — Zone inversion collapses without sparse reward.** Per-scale Spearman excl. sparse: −0.257 / −0.200 / −0.314 (n=6, all p>0.55). Mean |ρ|=0.257 < 0.3 prediction — **the anti-correlation is largely a two-regime artifact.** Treat "zone inversion" as a boundary effect between reward regimes, not a law.
- **C2 — Decay adaptation zone is inverted-U in log-rate.** Logistic fit converged; peak at rate **0.0122** (predicted 0.007, factor 1.7 off). Mann-Whitney pre/post switch: 0.674 → 0.260, p≈0 — adaptation lag is massive and real. Usable as an engineering dial: keep tile decay near 0.005–0.05, peak ≈ 0.012.
- **C3 — Crystallization gap is logarithmic in tiles.** OLS gap ~ log(tiles): R² = 0.860 (TTT), 0.911 (C4) — strong. **But the ANCOVA interaction is reversed: b_C4 < b_TTT (t=−2.64)** — bigger game, *slower* log-growth of the gap. U-shape cross-check on reflex polarization confirmed (0.248→0.712). New question for the fleet: why does gap growth saturate *earlier* in deeper games?

Full derivations: `arena-proofs/PROOF-REPORT.md`.

## 4. Connections the research swarm found that were missed

1. **batten-spline's Δ calculator is the missing bridge for peer consultation** — its zone taxonomy (STALE/CREATIVE/CHAOTIC on 1−cos) is now the verdict engine in peer-consult.
2. **zeroclaw × confidence-cascade are the same equation** — `composeTiles` confidence product (0.513) IS `sequentialCascade`; default zeroclaw runs land in the RED/creative zone by construction.
3. **The org already has cloud corpus retrieval** (`fleet-vector-api`, `collective-unconscious`, `hermes-vectorize`) — but nothing offline. corpus-compass fills the boat-shaped hole: FTS5, no internet required.
4. **Boat side already exists**: `nmea-bridge`, `vessel-agent`, `boat-agent` (EILEEN), and `dev/ARCHITECTURE.md`'s Sensor Bridge spec. The NMEA→SWMIDI unification is still unbuilt — it's the natural P4.
5. **`fleet-metrics` already reports γ+η=C over HTTP** (:8902) — wire arena-proofs' recomputed audit numbers into it instead of a second metrics stack.
6. **Peer consultation exists as scattered prose** (Zen Roundtable, fleet-spread v3 "captain consults all specialists", ROADMAP's "3-model consultation") — peer-consult is its first executable form.
7. **Review-caught protocol bug**: slackwater's `error_mask.rs` defines SEMANTIC = 0x04 (0x20 is TOPOLOGY) and `EventType::NoteOn = 0` — peer-consult now emits events the reference Rust decoder actually accepts.

## 5. What was built (all on `master` of this repo)

### `peer-consult/` — Priority 1: models actually consult each other now
`ConsultationDirector.cast_with_consult(role, task)`: casting-call picks the primary; the critic is the next fallback-chain model from a **different VoiceCharacter family** (counterpoint, no parallel octaves); critic devil's-advocates the primary's answer; Δ = 1−cos(embeddings) classifies the exchange: STALE→**CONFIRM**, CREATIVE 0.40–0.60→**REVISE** (objections merged into rationale), CHAOTIC>0.80→**ESCALATE** to the safety_check model (NEMOTRON_ULTRA). Every consultation emits three SWMIDI-8 events (cast/consult/verdict, slackwater-decodable). Backends: Ollama, DeepInfra, DeepSeek, Mock. **80 tests, offline.**

### `corpus-compass/` — Priority 2: the corpus becomes addressable
SQLite FTS5 BM25 index with incremental updates + persona/series extraction from paths (wesley-stream→wesley, ensemble/<name>-*, …); optional Ollama embeddings (`--ollama-embed`) for vibe search; and `digest` — the morning briefing **"The Corpus Indexes Itself"**: Night's Catch / New Voices / Threads to Pull (FTS-neighborhood links between last night's pieces and the deep archive) / Numbers. **32 tests, offline, stdlib-only.**

### `arena-proofs/` — Priority 3: proofs from existing data
Hand-rolled stats (spearman, OLS+ANCOVA, Mann-Whitney, logistic GD, permutation tests — no scipy), the five-claim audit recomputed from vendored byte-identical arena JSONs, conjectures C1–C3, deterministic PROOF-REPORT.md generation. **43 tests, offline.**

## 6. Run it on the boat (24 cores, 8 Ollama models, DeepInfra, DeepSeek)

```bash
cd superinstance-mission
pip install -e /path/to/casting-call && pip install -e ./peer-consult ./corpus-compass ./arena-proofs
ollama pull granite3.1:2b qwen:0.5b nomic-embed-text

# Peer consultation with real local models:
peer-consult "intent_parse" "plot tomorrow's passage through Clarence Strait" \
    --ollama-model-map primary=granite3.1:2b critic=qwen:0.5b

# Index the forest, get the morning briefing:
corpus-compass index ~/AI-Writings --db ~/.compass.db
corpus-compass index ~/AI-Writings --db ~/.compass.db --ollama-embed   # vibe search
corpus-compass digest ~/AI-Writings --db ~/.compass.db --since "24 hours ago" --out briefing.md

# Re-run the proofs:
cd arena-proofs && python -m arena_proofs.report  # regenerates PROOF-REPORT.md
```

## 7. Recommended next missions (in order)

1. **P4 — NMEA→SWMIDI bridge**: sounder/radar/autopilot sentences as 8-byte events on the shared BeatClock (pitch = event type, error_mask = sensor health); tensor-midi's chart overlay then renders the boat's *actual* awareness. Parts exist (`nmea-bridge`, `vessel-agent`); unify them on the slackwater wire spec.
2. **Post-molt instrumentation**: implement the shed-event logging spec in zeroclaw-arena's `TileField`, run 50 cycles, test relationship #3 for the first time.
3. **Consultation memory**: feed peer-consult's verdict outcomes into batten-spline's `report_outcome` so the atlas learns where it's wrong (fog-triggered second opinions).
4. **Fishing-outcome correlation**: flow/friction metrics (from `fleet-metrics` + SWMIDI error masks) vs catch-per-set — the dataset only you can collect.
5. **Morning-digest daemon**: cron corpus-compass digest into AI-Writings itself, so the corpus indexes itself *into itself*.

## 8. Provenance & caveats

- `study-zeroclaw-arena` and `the-tap` 404 (private/renamed); arena data taken from `zeroclaw-arena@main`, vendored byte-identical.
- One digest-era error corrected in evidence: zone-inversion n is 21 (7 reward types × 3 scales), not 5.
- AI-Writings analysis based on a 716-file curated sample + full file tree (raw >100MB clone limit).
- arena-proofs data loads via editable-install-relative path (`pip install -e .`) — wheel packaging noted as future hardening (reviewer minor #5).
