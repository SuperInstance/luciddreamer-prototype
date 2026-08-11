# SPEC.md — SuperInstance Mission Builds (single source of truth)

Three independent Python packages. Shared constraints for ALL packages:
- Python ≥3.10, installable via `pip install -e .`, pytest suite under `tests/`.
- **Tests must pass with NO network access.** All network/LLM/embedding calls behind injectable interfaces with offline fakes.
- Style matches casting-call: frozen dataclasses, pure functions where possible, stdlib-first. numpy allowed only in arena-proofs. No other hard deps.
- Each package ships `README.md` with a "Run on the boat" section: 24 cores, Ollama at localhost:11434, DEEPINFRA_API_KEY, DEEPSEEK_API_KEY.

Research context (from Stage 1 digests, binding):
- casting-call (`/mnt/agents/repos/casting-call`): `CastingDirector` (casting_call/casting.py) with `cast()`, `what_if()`, `counterpoint_check()`; `ModelAtlas`/`ModelProfile`/`VoiceCharacter` (casting_call/atlas.py); roles + fallback chains `_ROLE_DEFAULTS`/`_ROLE_FALLBACKS`; `pip install -e /mnt/agents/repos/casting-call` to depend on it.
- batten-spline: Δ semantic distance = 1 − cosine on L2-normalized embeddings; zones STALE <0.20, TRANSITIONAL_LOW 0.20–0.40, CREATIVE 0.40–0.60, TRANSITIONAL_HIGH 0.60–0.80, CHAOTIC >0.80. DeepInfra embeddings: OpenAI-compatible `https://api.deepinfra.com/v1/openai/embeddings`, model `BAAI/bge-m3`.
- slackwater-rust SWMIDI-8: 8 bytes LE — [status (event-nibble<<4 | channel), pitch(0–127 event type), velocity(0–127 weight), error_mask(8 friction bits), tick u32 @96 PPQ].
- confidence-cascade: zones GREEN ≥0.90, YELLOW 0.75–0.89, RED <0.75; RED strictly contains the creative zone [0.4,0.6] ("zone inversion" is structural).

---

## P1 — `peer-consult/` (peer consultation layer for casting-call)

Models don't consult each other yet; this makes `cast()` a conversation. Depends on casting-call (path install).

Modules (`src/peer_consult/`):
1. `backends.py` — `class ModelBackend(Protocol): def complete(self, prompt: str, *, temperature: float = 0.7, max_tokens: int = 512) -> str`. Implementations: `OllamaBackend(model, host="http://localhost:11434")` (POST /api/generate via urllib), `DeepInfraBackend(model, api_key=None)` (env DEEPINFRA_API_KEY, OpenAI-compatible chat completions), `DeepSeekBackend(model="deepseek-chat", api_key=None)` (env DEEPSEEK_API_KEY), `MockBackend(fn: Callable[[str], str])` for tests.
2. `embeddings.py` — `class Embedder(Protocol): def embed(self, texts: list[str]) -> list[list[float]]`. `HashEmbedder(dim=256)` (deterministic token-hashing bag-of-words, L2-normalized, OFFLINE), `OllamaEmbedder(model="nomic-embed-text")`, `DeepInfraEmbedder(model="BAAI/bge-m3")`. `delta(a, b) -> float` = 1 − cos. `classify_zone(d) -> Zone` enum with the five bands above.
3. `consult.py` —
   - `@frozen Consultation`: role, primary_model, critic_model, primary_answer, critique, delta, zone, verdict, rationale, swmidi: bytes.
   - `Verdict` enum: CONFIRM (STALE band — redundant agreement), REVISE (CREATIVE band 0.40–0.60 — productive divergence; critic's objections merged into rationale), ESCALATE (CHAOTIC >0.80 — route to safety_check model per atlas), NOTE (transitional bands).
   - `class ConsultationDirector`: wraps a `CastingDirector` (constructor-injected, default `CastingDirector()` with default atlas) + a `BackendResolver` mapping atlas model names → ModelBackend (with explicit overrides; unknown models raise a clear error listing known mappings). Method `cast_with_consult(role: str, task: str, *, context=None, max_cost=None) -> Consultation`:
     a. `cast(role)` → primary; select critic = the next model in the role's fallback chain with a DIFFERENT VoiceCharacter family than primary (counterpoint constraint, no parallel octaves).
     b. Primary answers `task` via its backend; critic receives critique prompt (primary's answer + role + instruction to challenge assumptions, devil's-advocate style — the Seed-mini role).
     c. Δ(primary_answer, critique) via Embedder → zone → verdict per rules above.
     d. Encode 3 SWMIDI-8 events (cast=1, consult=2, verdict=3 on the primary model's atlas channel; velocity = round(confidence*127) with confidence = 1−delta; error_mask bit SEMANTIC=0b0000_0100 set when zone is CHAOTIC (corrected post-review: slackwater flux-core/src/error_mask.rs defines SEMANTIC as bit 2; 0b00100000 is TOPOLOGY)).
4. `swmidi.py` — `encode_event(status_type, channel, pitch, velocity, error_mask, tick) -> bytes` (8 bytes LE), `decode_event(bytes) -> dict`, channel helper from casting-call profile's `channel` field.
5. `cli.py` — `peer-consult "role" "task text" [--ollama-model-map primary=granite3.1:2b ...] [--mock]`.

Tests: MockBackend + HashEmbedder only. Cover: verdict for each zone band (engineered MockBackend outputs + HashEmbedder), critic≠primary voice family enforced, ESCALATE path hits safety_check role model, SWMIDI round-trip encode/decode, cost ceiling respected, deterministic.

---

## P2 — `corpus-compass/` (AI-Writings retrieval + self-indexing)

The corpus is write-mostly; this makes it addressable. Offline-first (FTS5), optional Ollama embeddings. NO hard deps beyond stdlib (sqlite3, urllib).

Modules (`src/corpus_compass/`):
1. `index.py` — `build_index(corpus_dir: Path, db_path: Path, *, embeddings: Embedder|None = None) -> IndexStats`. Schema: `pieces(id INTEGER PK, path TEXT UNIQUE, title TEXT, series TEXT, directory TEXT, persona TEXT, mtime REAL, body TEXT)`; `pieces_fts` FTS5 virtual table (title, body) content-synced; `embeddings(piece_id, vector BLOB float32)` only when an Embedder is given. Incremental: skip unchanged (path, mtime). Persona extraction: from path segments (wesley-stream→wesley, qwen-stream→qwen, ensemble/<name>-*, model-portraits/*, fetch-riffs/*) with a small explicit mapping table + None fallback; series = leading `NN-` filename prefix or directory name.
2. `search.py` — `search(db, query, k=10) -> list[SearchResult]` (FTS5 BM25, snippet extraction); `vibe_search(db, text, k=10, embedder)` cosine over embeddings table (numpy-free: array module + math). `@frozen SearchResult`: path, title, persona, score, snippet.
3. `digest.py` — `generate_digest(repo_dir, db_path, *, since: str = "24 hours ago", out_path=None) -> str` — runs `git -C repo_dir log --since --name-only --pretty=format:` (via subprocess; injectable `git_runner` callable for tests), filters .md under content dirs, pulls titles/first-lines from the index, groups by directory, and writes a morning briefing markdown titled "The Corpus Indexes Itself — <date>": sections **Night's Catch** (new pieces grouped by theme/dir), **New Voices** (personas not seen in index before `since`), **Threads to Pull** (3 pieces from the archive whose FTS neighborhood overlaps the new pieces — the corpus connecting its own roots), **Numbers**. Returns the markdown; writes it if out_path given.
4. `cli.py` — `corpus-compass index DIR [--db PATH] [--ollama-embed]` / `search "query" [--vibe]` / `digest REPO [--since "24 hours ago"]`.

Tests: fixture corpus (~10 tiny .md files incl. wesley-stream/ & ensemble/ paths), tmp dirs, fake git_runner. Cover: incremental re-index skips unchanged, persona mapping, FTS ranking sanity, digest contains all new files + sections, vibe_search on HashEmbedder (reuse pattern from P1: small local HashEmbedder copy — do NOT depend on peer-consult package).

---

## P3 — `arena-proofs/` (proofs & claims audit from zeroclaw-arena data)

Reproducible analysis over existing experiment JSONs. numpy allowed. **No scipy** — implement stats by hand. Data source: `/mnt/agents/repos/zeroclaw-arena` (read-only). Vendor the needed JSONs into `data/` at build time via a `Makefile`/script `scripts/fetch_data.sh` that copies from ZARENA_DIR (default /mnt/agents/repos/zeroclaw-arena); committed copies must be present so tests run offline. Required files (locate exact paths in repo; names approximate): scaling-emergence-results.json, decay-results.json, temporal-dynamics*, reflex-evolution-v2*, tile-conservation-results.json, holographic-bound*, tile-capacity-results.json, entropy-production*, min-exposure-results.json.

Modules (`src/arena_proofs/`):
1. `stats.py` — `pearson(x,y)`, `spearman(x,y)` (average ranks), `permutation_p(stat_fn, x, y, observed, n=10000, seed)`, `ols(X, y)` returning (beta, se, t, R²), `mannwhitneyu(x,y)` (normal approx w/ continuity correction ok), `logistic_gd(X, y, lr, iters)` (gradient descent, return beta + converged flag). All deterministic with explicit seeds. Known-answer tests on synthetic data (e.g., spearman of identical series = 1; ols recovers known slope).
2. `datasets.py` — typed loaders: `load(name) -> dict` from bundled `data/`; schema docstrings citing the arena digest fields (e.g., decay: `conditions.with_switch` 35 trials with `adaptation_speed`, `windows` per-20-game win rates; temporal-dynamics: 20 snapshots × {ttt,c4} with tiles/gap/entropy; scaling-emergence: 21 points `reward_entropy`/`reward_performance` over 3 scales incl. sparse-reward point).
3. `claims_audit.py` — `ClaimVerdict` dataclass (claim, verdict ∈ SUPPORTED/PARTIAL/REFUTED/UNTESTABLE, evidence: dict, summary: str). Functions `check_conservation()` (seed-invariance std_of_means ≈0.001 support; additive drift 1.020→1.148 refutes strict form → PARTIAL), `check_creative_zone()` (no φ support; flat temperature 0.648–0.712 → REFUTED as stated), `check_post_molt()` (no shed-event logging → UNTESTABLE + write the instrumentation spec), `check_zone_inversion()` (Pearson −0.969 n=5; Spearman −0.43 p=0.053 outlier-driven → PARTIAL), `check_holographic()` (√N direction supported but fit c≈4.1≠40; clusters 7/10/14 sublinear but not √N → PARTIAL). Each recomputes its numbers from the bundled data.
4. `c1_collapse.py` — Conjecture 1: per-scale Spearman(reward_entropy, reward_performance) excluding sparse-reward points; prediction |ρ|<0.3 within scale. Report rhos + permutation p-values + verdict.
5. `c2_decay_zone.py` — Conjecture 2: logistic regression of adapted(0/1) on [1, log rate, (log rate)²] over the 35 with_switch trials → report peak rate; Mann-Whitney on `windows` win rates pre- vs post-game-300 → adaptation lag. Verdict vs prediction peak ≈ 0.007.
6. `c3_log_gap.py` — Conjecture 3: OLS gap ~ a + b·log(tiles) for TTT and C4 (expect R²>0.85 given corr 0.927/0.955); ANCOVA-style interaction test b_C4 > b_TTT; cross-validate shape against reflex-evolution-v2 `polarization_history` U-shape (0.248→0.712). Verdicts.
7. `report.py` — `generate_report() -> str` renders **PROOF-REPORT.md**: claims-audit table, three conjecture results with numbers, and a "New instrumentation needed" section (post-molt event logging spec: per-cycle tile shed events with timestamps/cycle ids in zeroclaw-arena's `TileField`).

Tests: known-answer stats tests; smoke tests on bundled data (verdicts are stable, functions return expected dataclass); determinism (same seed → same p-value); report generation end-to-end.

---

## Coordination
- Shared repo: `/mnt/agents/output/superinstance-mission` (git, main branch, this SPEC committed).
- Each builder works on branch `p1`/`p2`/`p3` in worktree `$HOME/work-p1` etc. (`git worktree add $HOME/work-pX pX`). Never edit main directly; never `git worktree prune`. Commit with clear messages.
- Gate before merge: `pip install -e . && python -m pytest -q` green in the package dir, offline.
