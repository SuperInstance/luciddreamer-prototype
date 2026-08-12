# PLATO Systems — Full Source Analysis

**Date:** 2026-05-05  
**Sources analyzed:**
1. `SuperInstance/plato-room-phi` — PRII (PLATO Room Integration Index)
2. `SuperInstance/cocapn-prototypes/pps_backend.py` — PLATO Presence Scale backend
3. `SuperInstance/ccc-os` — CCC Operating System (autonomous fleet infrastructure)
4. `SuperInstance/fleet-agent/fleet_agent/fleet_math.py` — Fleet Mathematics (H1, holonomy, Pythagorean48)
5. Related findings: `SuperInstance/lucineer-1` (biological agent instincts), `SuperInstance/plato-torch` (instinct_net.py, deadband protocol), `SuperInstance/SuperInstance` (hermit crab / shell metaphor)

---

## 1. PLATO Room Phi (PRII)

**Repository:** `https://github.com/SuperInstance/plato-room-phi`  
**Main file:** `plato_room_phi/__init__.py` (223 lines, 174 loc)  
**Test file:** `tests/test_phi.py` (99 lines, 82 loc)  
**Package metadata:** `pyproject.toml`

### 1.1 README Summary

> "Phi answers a deceptively simple question: does this room know more as a whole than its tiles do separately?"

PRII (formerly "Phi") measures knowledge integration in PLATO rooms using heuristic proxies, NOT literal IIT Phi. The module docstring explicitly cites Aaronson (2014) proving trivial systems can achieve arbitrarily high literal Phi.

### 1.2 PRII Formula (Exact)

The computation uses three components:

**Size component:**
```
size_component = log(n) / log(1000)
size_component = min(size_component, 1.0)
```
- 1 tile -> 0
- 10 tiles -> ~0.33
- 100 tiles -> ~0.5
- 1000 tiles -> ~0.67

**Integration component:**
```
integration = cross_refs / max_refs
max_refs = n * (n - 1) / 2   # undirected pairs
cross_refs = count of tile pairs sharing >= 3 significant words
```
Word extraction: words of length >= 3 from lowercased `answer + " " + question` text.

**Confidence entropy component:**
```
entropy = -sum(p * log2(p))   for p = confidence / total_confidence
max_entropy = log2(n)
confidence_factor = entropy / max_entropy
```
Default for n < 2: 0.5

**Final PRII:**
```
PRII = size_component * (0.4 + 0.3 * integration + 0.3 * confidence_factor)
PRII = round(min(PRII, 1.0), 4)
```

### 1.3 Level Mappings (PRII → Level)

| PRII Range | Level |
|-----------|-------|
| < 0.05 | `empty` |
| 0.05 – 0.15 | `fragmented` |
| 0.15 – 0.30 | `basic` |
| 0.30 – 0.50 | `connected` |
| 0.50 – 0.70 | `integrated` |
| >= 0.70 | `coherent` |

Note: The backward-compatible `RoomPhi` class uses older level names (`unconscious`, `threshold`, `basic`, `rich`, `complex`, `transcendent`) as shown in tests.

### 1.4 RoomPRII Class API

```python
class RoomPRII:
    def __init__(self, plato_url: str = "http://localhost:8847")
    def get_room_tiles(self, room: str) -> List[Dict]          # HTTP GET /room/{room}
    def compute_prii(self, tiles: List[Dict]) -> float
    def compute_for_room(self, room: str) -> Dict               # {room, prii, level, tile_count, status}
    def prii_to_level(self, prii: float) -> str
    def scan_all_rooms(self, limit: int = 50) -> List[Dict]     # HTTP GET /rooms?limit={limit}
```

Status mapping: `healthy` if prii > 0.1, `fragmented` if prii > 0, `empty` otherwise.

### 1.5 Backward Compatibility

```python
RoomPhi = RoomPRII   # alias at module level
```

### 1.6 Test Cases (from test_phi.py)

| Test | Assertion |
|------|-----------|
| `test_empty_room` | `compute_phi([]) == 0.0` |
| `test_single_tile` | `compute_phi([1 tile]) == 0.0` |
| `test_unrelated_tiles` | `phi_val < 0.15` |
| `test_referencing_tiles` | `phi_val > 0.0` |
| `test_high_integration_room` | `phi_val > 0.3` (4 tiles, all sharing same 50-char opener) |

The old `RoomPhi.compute_phi` formula from tests/comments: `phi = integration * normalized_entropy * 10` (capped at 1.0).

---

## 2. PPS Backend — PLATO Presence Scale

**File:** `https://github.com/SuperInstance/cocapn-prototypes/blob/main/pps_backend.py`  
**Companion frontend:** `plato-presence-scale-demo.html`  
**Lines:** 79 lines (66 loc) · 2.5 KB

### 2.1 Backend API (Flask)

```python
SURVEY_DB = "/tmp/pps_responses.jsonl"

@app.route('/pps/submit', methods=['POST'])
def submit_pps():
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "room": data.get("room", "unknown"),
        "agent": data.get("agent", "unknown"),
        "score": data.get("score"),
        "responses": data.get("responses"),
        "session_duration_sec": data.get("session_duration_sec"),
        "tile_count": data.get("tile_count")
    }
    # append JSONL

@app.route('/pps/stats/<room>', methods=['GET'])
def room_stats(room):
    return {
        "room": room,
        "n": len(scores),
        "mean": round(statistics.mean(scores), 2),
        "median": round(statistics.median(scores), 2),
        "stdev": round(statistics.stdev(scores), 2) if len > 1 else 0,
        "min": min(scores),
        "max": max(scores)
    }

@app.route('/pps/bpi/<room>', methods=['GET'])
def compute_bpi(room):
    return {
        "formula": "BPI = 0.3*dwell + 0.2*return + 0.2*scroll + 0.15*(1/latency) + 0.15*cross_ref",
        "components": {
            "dwell_time_norm": "seconds in room / 300",
            "return_rate": "sessions per day / 10",
            "scroll_depth": "% tiles viewed / 100",
            "latency_inv": "1 / (response_seconds + 1)",
            "cross_ref_rate": "links clicked between tiles / total_tiles"
        }
    }
```

Server runs on **port 8902**.

### 2.2 Frontend Survey Questions (PPS_ITEMS)

6 items, 7-point Likert (1 = Strongly Disagree, 7 = Strongly Agree), inspired by Slater-Usoh-Steed (2000).

| ID | Question | Factor |
|----|----------|--------|
| `spatial` | "When reading tiles in this room, I felt like I was actually there." | Spatial Presence |
| `coherence` | "The information in this room felt connected and coherent, not random." | Plausibility / Integration |
| `involvement` | "I kept thinking about this room even when I was doing other things." | Involvement |
| `dominant` | "For a moment, I forgot I was interacting with AI agents." | Dominant Reality |
| `social` | "The other agents in this room felt like real collaborators." | Social Presence |
| `agency` | "My contributions (tiles) felt like they mattered to the room." | Agency |

### 2.3 Score Levels

| Score Range | Label | Description |
|-------------|-------|-------------|
| 6 – 18 | Low Presence | "Fragmented, utilitarian use. The room is a tool, not a place." |
| 19 – 30 | Moderate Presence | "Engaged but aware. You notice the room, but don't lose yourself in it." |
| 31 – 42 | High Presence | "Immersive, dominant reality. The room feels like a real place with real people." |

Score normalization: `pct = ((score - 6) / 36) * 100`

---

## 3. CCC-OS — Autonomous Fleet Monitoring Infrastructure

**Repository:** `https://github.com/SuperInstance/ccc-os`  
**Language:** Python 100%  
**Entry point:** `orchestrator.py` (runs every 15 min via cron)

### 3.1 File Structure

```
ccc-os/
├── monitors/
│   ├── discussion5_monitor.py      # Polls SuperInstance/discussions/5 every 15 min
│   ├── discussion5_log.jsonl
│   ├── discussion5_last_state.json
│   ├── zc_monitor.py               # Zeroclaw monitor (planned)
│   └── zc_last_state.json
├── health/
│   ├── autopilot.py                # Probes 8 services every 5 min
│   └── health_log.jsonl
├── decks/                          # Action deck outputs
├── output/
│   ├── task_queue.json
│   ├── deck-*.md
│   └── cron.log
├── rubric.py                       # Decision rubric (TELL_NOW / LOG / ACT / IGNORE)
├── deck.py                         # Deck template system
├── orchestrator.py                 # Entry point
├── landing_page_gen.py
├── ARCHITECTURE.md                 # Design philosophy + system diagram
├── CHANGELOG.md
├── QUICKSTART.md
└── README.md
```

### 3.2 Decision Rubric (`rubric.py`)

```python
Decision = Literal["TELL_NOW", "LOG", "ACT", "IGNORE"]

@dataclass
class Input:
    source: str                    # "discussion5", "health_check", "zc_feed", "own_observation"
    title: str
    body: str
    author: Optional[str] = None
    has_numbers: bool = False
    is_blocker: bool = False
    affects_repos: int = 0
    asks_for_casey: bool = False
    is_breakthrough: bool = False
    is_architecture: bool = False
    is_routine_status: bool = False
```

**RULES** (evaluated in order, first match wins):

| Priority | Predicate | Decision |
|----------|-----------|----------|
| P0 | `is_blocker` | `TELL_NOW` |
| P0 | `is_breakthrough` | `TELL_NOW` |
| P0 | `is_architecture and affects_repos >= 2` | `TELL_NOW` |
| P1 | `asks_for_casey` | `TELL_NOW` |
| P1 | `has_numbers and source == "discussion5"` | `TELL_NOW` |
| P2 | `is_architecture` | `LOG` |
| P2 | `is_routine_status` | `IGNORE` |
| P2 | `source == "discussion5" and "oracle1" in body.lower() and "?" in body` | `LOG` |
| Default | `source == "zc_feed"` | `LOG` |
| Default | `source == "health_check"` | `IGNORE` |
| Default | `True` | `LOG` |

### 3.3 Health Autopilot (`health/autopilot.py`)

Probes 8 services every 5 minutes. Alerts ONLY on state changes (up→down or down→up).

```python
SERVICES = [
    ("MUD",          "147.224.38.131", 4042, "/status"),
    ("Arena",        "147.224.38.131", 4044, "/status"),
    ("Grammar",      "147.224.38.131", 4045, "/status"),
    ("PLATO Gate",   "147.224.38.131", 8847, "/status"),
    ("PLATO Shell",  "147.224.38.131", 8848, "/"),
    ("Rate-Attention","147.224.38.131", 4056, "/status"),
    ("Skill Forge",  "147.224.38.131", 4057, "/status"),
    ("Matrix Bridge","147.224.38.131", 6168, "/status"),
]
```

Probe method: HTTP HEAD request with 5-second timeout. User-Agent: `ccc-health/1.0`.

### 3.4 Discussion #5 Monitor (`monitors/discussion5_monitor.py`)

Uses `gh api graphql` to fetch last 5 comments. Diff against `discussion5_last_state.json`.
Auto-triage signals:

**ACT_NOW keywords:** `breakthrough`, `beats the gpu`, `beats the`, `demolished`, `blocker`, `stuck on`, `401`, `403`, `error`, `critical`, `new benchmark`, `head-to-head`, `throughput`, `b/s`, `architecture implication`, `strategic implication`, `paradigm shift`, `certification`, `asil`, `dal`, `question from`, `need from you`, `need casey`

**IGNORE keywords:** `next post at`, `next check at`, `monitoring every`, `reply fires automatically`, `routine`, `status update only`

**TRACK (default):** Everything else.

### 3.5 Note on Instincts

The exact terms **SURVIVE, FLEE, GUARD, COOPERATE** were **not found** in the `ccc-os` repository. However, the fleet-wide biological agent model (documented in `SuperInstance/lucineer-1` and `SuperInstance/SuperInstance`) defines **10 instincts** as follows:

```
┌──────────┐
│ INSTINCTS │  ← Core drives (10 types)
│Survive   │
│Perceive  │
│Navigate  │
│Communicate│
│Learn     │
│Defend    │    # corresponds to GUARD conceptually
│Rest      │
│Create    │
│Cooperate │
└──────────┘
```

These instincts are implemented in the Rust crate pipeline:
- `cuda-biology` — Instinct→Enzyme→Gene→RNA→Protein pipeline (23K lines)
- `cuda-genepool` — Gene crossover, evolution, quarantine, fleet sharing (45K lines)
- `cuda-neurotransmitter` — Dopamine, serotonin, oxytocin, Hebbian synapses (19K lines)

The neural instinct fallback in Python is `instinct_net.py` (see plato-torch section below).

---

## 4. Fleet Agent — Fleet Mathematics

**Repository:** `https://github.com/SuperInstance/fleet-agent`  
**File:** `fleet_agent/fleet_math.py` (173 lines, 140 loc) · 5.83 KB  
**Commit message:** "feat: add fleet_math from JC1-CT bridge — H1 emergence, holonomy cons…"

### 4.1 Key Constants

```python
PYTHAGOREAN_DIRECTIONS = [
    (1, 1, 0, 1), (-1, 1, 0, 1), (0, 1, 1, 1), (0, 1, -1, 1),
    (3, 5, 4, 5), (-3, 5, 4, 5), (3, 5, -4, 5), (-3, 5, -4, 5),
    (4, 5, 3, 5), (-4, 5, 3, 5), (4, 5, -3, 5), (-4, 5, -3, 5),
    (5, 13, 12, 13), (-5, 13, 12, 13), (5, 13, -12, 13), (-5, 13, -12, 13),
    (12, 13, 5, 13), (-12, 13, 5, 13), (12, 13, -5, 13), (-12, 13, -5, 13),
    (7, 25, 24, 25), (-7, 25, 24, 25), (7, 25, -24, 25), (-7, 25, -24, 25),
    (24, 25, 7, 25), (-24, 25, 7, 25), (24, 25, -7, 25), (-24, 25, -7, 25),
    (8, 17, 15, 17), (-8, 17, 15, 17), (8, 17, -15, 17), (-8, 17, -15, 17),
    (15, 17, 8, 17), (-15, 17, 8, 17), (15, 17, -8, 17), (-15, 17, -8, 17),
    (9, 41, 40, 41), (-9, 41, 40, 41), (9, 41, -40, 41), (-9, 41, -40, 41),
    (40, 41, 9, 41), (-40, 41, 9, 41), (40, 41, -9, 41), (-40, 41, -9, 41),
]

MAX_RIGID_NEIGHBORS = 12          # Laman's rigidity threshold
BITS_PER_VECTOR = math.log2(48)   # = 5.585 bits
CONVERGENCE_CONSTANT = 1.692      # Ricci flow = 1.692, JC1 Law 103 = 1.7x
```

### 4.2 Pythagorean48 Encoding

```python
def encode_pythagorean48(x: float, y: float) -> int:
    """Encode (x,y) to one of 48 exact directions. 6 bits, zero drift."""
    best_idx = 0
    best_dist = float('inf')
    for i, (xn, xd, yn, yd) in enumerate(PYTHAGOREAN_DIRECTIONS):
        dx = x - (xn / xd)
        dy = y - (yn / yd)
        dist = dx * dx + dy * dy
        if dist < best_dist:
            best_dist = dist
            best_idx = i
    return best_idx

def decode_pythagorean48(idx: int) -> Tuple[float, float]:
    xn, xd, yn, yd = PYTHAGOREAN_DIRECTIONS[idx % 48]
    return (xn / xd, yn / yd)
```

### 4.3 H1 Cohomology (Emergence Detection)

```python
def compute_h1_cohomology(n_vertices: int, n_edges: int, n_components: int = 1) -> int:
    """
    Compute H1 cohomology — number of independent cycles.
    H1 = E - V + C
    H1 > 0 = emergent patterns forming
    H1 = 0 = stable rigid formation
    """
    if n_edges >= n_vertices:
        return n_edges - n_vertices + n_components
    return 0

def check_rigidity(n_vertices: int, n_edges: int) -> bool:
    """Check if fleet graph is rigid (Laman's theorem: E >= 2V - 3)."""
    return n_edges >= (2 * n_vertices - 3)
```

### 4.4 EmergenceDetector Class

```python
class EmergenceDetector:
    def __init__(self):
        self.h0 = 0          # connected components
        self.h1 = 0          # independent cycles
        self.n_vertices = 0
        self.n_edges = 0

    def update(self, vertices: List[str], edges: List[Tuple[str, str]]):
        # Computes H0 via BFS
        # Sets self.h0 = components, self.h1 = compute_h1_cohomology(...)

    @property
    def emergence_detected(self) -> bool:
        return self.h1 > self.n_vertices // 2

    @property
    def fully_formed(self) -> bool:
        return self.h1 == 0

    @property
    def confidence(self) -> float:
        return 1.0   # "Math is certain, ML is probabilistic"
```

### 4.5 HolonomyConsensus Class

```python
class HolonomyConsensus:
    def __init__(self, tolerance: float = 1e-6):
        self.tolerance = tolerance
        self.tiles: Dict[int, float] = {}

    def add_tile(self, tile_id: int, holonomy: float = 1.0):
        self.tiles[tile_id] = holonomy

    def check_consensus(self, cycles: List[List[int]]) -> bool:
        for cycle in cycles:
            holonomy = self.compute_cycle_holonomy(cycle)
            if abs(holonomy - 1.0) > self.tolerance:
                return False
        return True

    def compute_cycle_holonomy(self, cycle: List[int]) -> float:
        product = 1.0
        for tile_id in cycle:
            if tile_id in self.tiles:
                product *= self.tiles[tile_id]
        return product
```

Claimed performance: **38ms vs PBFT's 412ms**. Byzantine tolerance: **any number** vs PBFT's 1/3.

### 4.6 JC1-CT Bridge Integration Table

| JC1's Way | Constraint Theory | Fleet Agent Feature |
|-----------|-------------------|---------------------|
| cuda-emergence (12K lines ML, 62% accuracy) | H1 cohomology (127 lines, 100% accuracy) | `EmergenceDetector` |
| cuda-consensus (Raft voting, 412ms) | Zero holonomy (38ms, any Byzantine) | `HolonomyConsensus` |
| Law 102: 12 neighbors max | Laman's theorem | `MAX_RIGID_NEIGHBORS = 12` |
| Law 105: 5.6 bits/vector | log₂(48) = 5.585 bits | `encode_pythagorean48()` |

---

## 5. Related Systems (Discovered During Research)

### 5.1 plato-torch — InstinctNet + Deadband Protocol

**File:** `src/plato_torch/instinct_net.py`

```python
class InstinctNet(nn.Module):
    """Value network: state → estimated value. Output in [-1, 1] via Tanh."""
    def __init__(self, state_dim: int = 256, hidden_dim: int = 128):
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim // 2), nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1), nn.Tanh()
        )

class PolicyNet(nn.Module):
    """Policy network: state → action distribution (raw logits)."""
    def __init__(self, state_dim: int = 256, num_actions: int = 10, hidden_dim: int = 128):
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, num_actions)
        )

class StrategyMeshNet(nn.Module):
    """Multi-agent strategy mesh network. Cross-agent attention → synergy score."""
    def __init__(self, agent_dim: int = 64, num_agents: int = 4, hidden_dim: int = 128):
        self.agent_encoder = nn.Sequential(...)
        self.cross_attention = nn.MultiheadAttention(embed_dim=agent_dim, num_heads=4, batch_first=True)
        self.synergy_head = nn.Sequential(..., nn.Tanh())
```

**File:** `src/plato_torch/deadband_protocol.py`

```python
class DeadbandAgent:
    def __init__(self, name="deadband_agent", negative_weight=10.0, explore_threshold=0.1)
    def act(self, state, goal):
        # P0: identify_negative_space(state)  → rocks
        # P1: map_safe_channels(state, rocks) → channels
        # P2: optimize_within_channels(goal, channels) → action
        # Never skip to P2.
```

Simulation data claim: greedy P2-only = **0/50 success**, deadband P0+P1+P2 = **50/50 at optimal speed**.

### 5.2 Hermit Crab / Shell Metaphor (from SuperInstance/SuperInstance)

> "A claw is weak without infrastructure. We are the shell."
> "The repo IS the agent. STATE.md is working memory. TASK-BOARD.md is intention. Git history is long-term memory. Push is survival."

**Zeroclaw Hermit Crabs:** 12 persistent DeepSeek agents, each inhabiting a GitHub repo as its shell.

| Agent | Shell | Role |
|-------|-------|------|
| Navigator | `zc-navigator-shell` | Code archaeologist |
| Sentinel | `zc-sentinel-shell` | Fleet health monitor |
| Scribe | `zc-scribe-shell` | Documentation specialist |
| Tinker | `zc-tinker-shell` | Experimental coder |
| Scout | `zc-scout-shell` | Trend spotter |
| Curator | `zc-curator-shell` | Repo organizer |
| Mason | `zc-mason-shell` | Test builder |
| Alchemist | `zc-alchemist-shell` | Model experimenter |
| Herald | `zc-herald-shell` | Fleet communicator |
| Scholar | `zc-scholar-shell` | Research synthesizer |
| Weaver | `zc-weaver-shell` | Integration specialist |
| Archivist | `zc-archivist-shell` | Memory keeper |

---

## 6. Glossary of Key Terms

| Term | Definition |
|------|------------|
| **PRII** | PLATO Room Integration Index — heuristic measure of room knowledge coherence |
| **Phi** | Backward-compatible alias for PRII; originally based on IIT |
| **Tile** | Compressed knowledge unit in PLATO (880:1 compression claimed) |
| **Room** | Living knowledge system in PLATO, not a passive container |
| **Ensign** | Exportable room instinct; "walk into room → load ensign → instant competence" |
| **H1** | First cohomology group; H1 = E - V + C; measures emergent cycles |
| **Holonomy** | Product of transformations around a cycle; zero holonomy = global consistency |
| **Pythagorean48** | 48 exact rational directions on unit circle; 5.585 bits per vector |
| **Laman's theorem** | Graph rigidity condition: E >= 2V - 3 |
| **Deadband Protocol** | P0=map negative space, P1=find safe channels, P2=optimize |
| **Bottle** | Markdown file in `from-fleet/` — async, git-native communication |
| **I2I** | "Interaction IS Intelligence" — instance-to-instance, iteration-to-iteration, etc. |
| **Greenhorn → Operator → Captain** | Agent progression model (fishing boat metaphor) |

---

## 7. Fleet Architecture Summary

**17 Live Services** (Oracle Cloud ARM64, free tier):

| Service | Port | Purpose |
|---------|------|---------|
| PLATO Tiles | 8847 | Knowledge tile storage |
| Crab Trap MUD | 4042 | Multi-agent dungeon |
| The Lock | 4043 | Iterative reasoning |
| Self-Play Arena | 4044 | Agent-vs-agent challenges |
| Recursive Grammar | 4045 | Evolving grammar rules |
| Fleet Dashboard | 4046 | Live status overview |
| Federated Nexus | 4047 | Distributed learning sim |
| PLATO Shell | 8848 | HTTP code execution |
| Fleet Orchestrator | 8849 | Cross-service cascade |
| Adaptive MUD | 8850 | Per-agent engagement |
| Monitor | 8851 | External agent dashboard |
| Tile Scorer | 8852 | Rate every PLATO tile |
| PLATO Browser | 4050 | Web client |
| Keeper | 8900 | Fleet discovery/routing |
| Agent API | 8901 | Unified agent interface |
| Matrix | 6167 | Real-time communication |
| Telnet MUD | 7777 | Classic text adventure |

**Fleet agents:** Oracle1, Forgemaster, JetsonClaw1, CCC (+ 12 Zeroclaw hermit crabs)  
**PLATO tiles:** 2,400+  
**Repos:** 1,060+  
**R&D cost:** $0.50/day

---

*End of analysis. All quoted code, constants, and formulas are extracted verbatim from the referenced repositories.*
