# Conductor API

### The Routing Layer for Multi-Agent Systems

> "The conductor isn't a model. It isn't a backend. It isn't the room. The conductor is the routing layer." — Lucineer

The Conductor reads each visitor as a session prompt, recruits the right agents from a pool, routes messages between visitors and agents, tracks engagement in real-time, and escalates to heavier models when confidence drops. It does **not** generate responses — it decides **who** should respond.

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Full API Reference](#full-api-reference)
  - [Conductor](#conductor)
  - [AgentProfile](#agentprofile)
  - [VisitorProfile](#visitorprofile)
  - [RoutingDecision](#routingdecision)
  - [SessionState](#sessionstate)
  - [SessionStore](#sessionstore)
  - [IntentAnalyzer](#intentanalyzer)
  - [EngagementTracker](#engagementtracker)
  - [RecruitmentStrategy](#recruitmentstrategy)
- [Escalation Thresholds](#escalation-thresholds)
- [Configuration](#configuration)
- [Example: Customer Service Bot System](#example-customer-service-bot-system)
- [Integration Patterns](#integration-patterns)

---

## Installation

```bash
pip install superinstance-conductor
```

**Requirements:** Python ≥ 3.10

**Optional dependencies:**

```bash
pip install superinstance-conductor[config]  # PyYAML for config file loading
pip install superinstance-conductor[dev]     # pytest for running tests
```

The Conductor is pure Python with no required dependencies. The standard library is all you need.

---

## Quick Start

```python
from conductor import Conductor, VisitorProfile

# Create a conductor
conductor = Conductor()

# A visitor arrives
visitor = VisitorProfile(
    visitor_id="v1",
    name="Casey",
    archetype="curious builder",
    personality_summary="Wants to learn and create.",
    known_interests=["AI", "music", "design"],
)

# Start a session
session = conductor.receive_visitor(visitor)
print(f"Session {session.session_id} started. Phase: {session.phase.value}")

# Route the visitor's first message
decision = conductor.route_visitor_message(
    session.session_id,
    "I want to build something creative with AI",
)

print(f"Intent: {decision.intent.value}")          # "creative"
print(f"Confidence: {decision.confidence}")          # 0.85
print(f"Responding agents: {decision.responding_agents}")  # ["flash"]
print(f"Agents to add: {decision.agents_to_add}")    # ["flash"] (recruited)
print(f"Reasoning: {decision.reasoning}")

# An agent responds — record it
conductor.route_agent_response(
    session.session_id,
    "flash",
    "Oh — I see it. I see the shape of it. Tell me more.",
)

# Check session status
status = conductor.get_session_status(session.session_id)
print(status)
# {
#   "session_id": "...",
#   "visitor": "Casey",
#   "phase": "orientation",
#   "intent": "creative",
#   "intent_confidence": 0.85,
#   "engagement": 0.57,
#   "satisfaction": 0.05,
#   "turn_count": 2,
#   "active_agents": ["barnacle", "flash"],
#   "duration_seconds": 12.3,
#   "escalated": false,
# }

# End the session
conductor.end_session(session.session_id)
```

---

## Core Concepts

### The Metaphor

The Conductor is modeled on a dockside bar called **The Tap**. Visitors walk in, the bartender (Barnacle) greets them, and the Conductor — the routing layer — decides which other agents to summon based on what the visitor wants.

### How It Works

1. **Visitor arrives** — `receive_visitor()` creates a session, Barnacle (the always-on greeter agent) is assigned
2. **Visitor sends a message** — `route_visitor_message()` runs the full routing loop:
   - Analyzes intent from the message text (keyword-based classifier)
   - Updates engagement score based on positive/negative signals
   - Determines the session phase (arrival → orientation → engaged → deep_work → wind_down)
   - Checks escalation thresholds
   - Manages the agent roster (adds specialists, removes idle agents)
   - Selects which agent(s) should respond
3. **Agent responds** — `route_agent_response()` records the agent's message and updates contribution scores
4. **Session ends** — `end_session()` cleans up agent assignments

### Agent Tiers

| Tier | Description | Cost | Examples |
|------|-------------|------|----------|
| **Light** | Cheap, fast, runs all day | $0 – $0.002/call | Barnacle, Flash, Wesley, Seed |
| **Heavy** | Expensive, deep, summoned when needed | $0.003 – $0.03/call | Pro, Hermes, Nemotron |

### Intent Types

| Intent | Keyword Signals | Best Agents |
|--------|----------------|-------------|
| `CONVERSATION` | hello, hey, chat, howdy | Barnacle, Flash |
| `CREATIVE` | write, create, story, draw, compose | Flash, Wesley, Hermes |
| `LEARNING` | how does, explain, teach, understand | Wesley, Pro, Seed |
| `LISTENING` | tell me a story, play something, entertain | Barnacle, Flash |
| `PROBLEM_SOLVING` | fix, debug, solve, error, broken | Pro, Nemotron |
| `COLLABORATION` | let's, together, brainstorm, co-create | Flash, Pro, Hermes |
| `EXPLORATION` | show me, browse, explore, what can you do | Barnacle, Seed |

### Session Phases

| Phase | Trigger | Behavior |
|-------|---------|----------|
| `ARRIVAL` | Session created (turn 0–1) | Barnacle greets, minimal agent roster |
| `ORIENTATION` | Turn 2–4 | Intent being established, agents recruited |
| `ENGAGED` | Engagement > 0.5 | Full agent roster active, rich interaction |
| `DEEP_WORK` | Escalated or heavy collaboration after turn 8 | Heavyweight agents active |
| `WIND_DOWN` | Engagement < 0.2 | Session tapering, preparing to close |
| `ENDED` | `end_session()` called | Session closed, agents released |

---

## Full API Reference

### `Conductor`

The main routing layer. Creates sessions, routes messages, manages agents.

#### Constructor

```python
Conductor(
    session_store: SessionStore | None = None,
    strategy: RecruitmentStrategy | None = None,
    config: dict | None = None,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `session_store` | `SessionStore \| None` | `SessionStore()` | Manages all visitor sessions. Override for custom backends. |
| `strategy` | `RecruitmentStrategy \| None` | `RecruitmentStrategy()` | Controls agent recruitment and escalation behavior. |
| `config` | `dict \| None` | `{}` | Configuration overrides (see [Configuration](#configuration)). |

#### Class Methods

##### `Conductor.from_config_file(path: str) -> Conductor`

Load a conductor from a YAML config file. Requires `pyyaml`.

```python
conductor = Conductor.from_config_file("config.yaml")
```

#### Session Lifecycle Methods

##### `receive_visitor(visitor: VisitorProfile) -> SessionState`

Create a new session for a visitor. Automatically assigns Barnacle as the greeter and sets phase to `ARRIVAL`.

```python
session = conductor.receive_visitor(visitor)
```

##### `end_session(session_id: str) -> SessionState | None`

End a session, release all agents, and remove it from the store. Returns the ended session state, or `None` if not found.

```python
ended = conductor.end_session(session.session_id)
```

#### Message Routing Methods

##### `route_visitor_message(session_id: str, message: str) -> RoutingDecision`

The core method. Processes a visitor's message through the full routing pipeline:

1. Records the message in session history
2. Analyzes intent and confidence (blends with message history for stability)
3. Updates engagement level (positive/negative signal detection + natural decay)
4. Determines session phase
5. Checks escalation thresholds
6. Manages agent roster (adds specialists, removes idle agents)
7. Selects responding agents

Returns a `RoutingDecision` that the caller uses to generate and deliver responses.

```python
decision = conductor.route_visitor_message(session_id, "I want to write a story")
# decision.responding_agents → ["flash"]
# decision.intent → VisitorIntent.CREATIVE
# decision.confidence → 0.85
```

##### `route_agent_response(session_id: str, agent_name: str, message: str) -> MessageRecord`

Record an agent's response in the session. Updates the agent's contribution score.

```python
msg = conductor.route_agent_response(session_id, "flash", "I see the shape of it.")
```

#### Agent Management Methods

##### `recruit_agent(session_id: str, agent_name: str) -> bool`

Manually recruit a specific agent into a session. Respects max agent limits and availability. Returns `True` on success.

```python
conductor.recruit_agent(session_id, "hermes")  # manually bring in the trickster
```

##### `dismiss_agent(session_id: str, agent_name: str) -> bool`

Dismiss an agent from a session. Cannot dismiss Barnacle (the greeter is permanent). Returns `True` on success.

```python
conductor.dismiss_agent(session_id, "flash")  # let Flash leave
```

#### Status Methods

##### `get_session_status(session_id: str) -> dict`

Returns a summary of the current session state:

```python
{
    "session_id": "uuid",
    "visitor": "Casey",
    "phase": "engaged",
    "intent": "creative",
    "intent_confidence": 0.85,
    "engagement": 0.72,
    "satisfaction": 0.15,
    "turn_count": 8,
    "active_agents": ["barnacle", "flash", "wesley"],
    "topics_covered": [],
    "duration_seconds": 145.3,
    "idle_seconds": 2.1,
    "escalated": false,
}
```

##### `get_stats() -> dict`

Returns conductor-wide statistics:

```python
{
    "total_visitors": 42,
    "total_messages_routed": 318,
    "total_escalations": 3,
    "active_sessions": 2,
    "agent_pool_size": 7,
    "agents_available": 7,
}
```

---

### `AgentProfile`

Defines an agent's identity, capabilities, and cost characteristics.

#### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | — | Unique identifier (e.g., `"flash"`) |
| `display_name` | `str` | — | Human-readable name (e.g., `"Flash"`) |
| `model` | `str` | — | Model identifier (e.g., `"v4-flash"`) |
| `provider` | `str` | — | Provider name (e.g., `"deepseek"`) |
| `personality` | `str` | — | Full personality description |
| `voice_description` | `str` | — | Voice character for TTS |
| `catchphrase` | `str` | — | Signature line |
| `specialties` | `list[str]` | — | Intent types this agent excels at (primary match = 1.0) |
| `secondary_skills` | `list[str]` | — | Intent types this agent can handle (secondary match = 0.5) |
| `perception_dims` | `int` | `128` | Cognitive bandwidth (metaphorical) |
| `tier` | `AgentTier` | `LIGHT` | Weight class: `LIGHT` or `HEAVY` |
| `availability` | `AgentAvailability` | `ON_DEMAND` | `ALWAYS_ON` or `ON_DEMAND` |
| `cost_per_call` | `float` | `0.0` | Cost in dollars per invocation |
| `active_sessions` | `int` | `0` | Current concurrent sessions |
| `max_concurrent_sessions` | `int` | `10` | Session capacity limit |
| `temperature` | `float` | `0.7` | LLM temperature for this agent |
| `system_prompt_extra` | `str` | `""` | Additional system prompt text |

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `is_available` | `bool` | `True` if `active_sessions < max_concurrent_sessions` |
| `is_always_on` | `bool` | `True` if `availability == ALWAYS_ON` |

#### Methods

##### `can_handle(intent: str) -> bool`

Whether this agent's specialties or secondary skills include the given intent.

##### `specialty_match(intent: str) -> float`

Returns match quality: `1.0` (primary), `0.5` (secondary), `0.0` (no match).

---

### `VisitorProfile`

Describes a visitor entering the system. The conductor reads this to decide initial agent roster.

#### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `visitor_id` | `str` | — | Unique visitor identifier |
| `name` | `str` | `"Visitor"` | Display name |
| `archetype` | `str` | `""` | Category (e.g., `"curious explorer"`, `"builder"`) |
| `personality_summary` | `str` | `""` | One-sentence description |
| `known_interests` | `list[str]` | `[]` | Topics the visitor cares about |
| `preferred_pace` | `str` | `"medium"` | `"slow"`, `"medium"`, or `"fast"` |
| `prefers_deep` | `bool` | `False` | Wants heavy analysis over light chat |

---

### `RoutingDecision`

The output of `route_visitor_message()`. Contains everything the caller needs to generate and deliver responses.

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `responding_agents` | `list[str]` | Agent names that should generate responses |
| `agents_to_add` | `list[str]` | Agents being recruited this turn |
| `agents_to_remove` | `list[str]` | Agents being dismissed this turn |
| `escalate` | `bool` | Whether escalation was triggered |
| `escalation_agent` | `str` | The escalation agent name (empty if none) |
| `intent` | `VisitorIntent` | Detected visitor intent |
| `confidence` | `float` | Confidence in the routing (0.0–1.0) |
| `engagement` | `float` | Updated engagement level (0.0–1.0) |
| `phase` | `SessionPhase` | Current session phase |
| `reasoning` | `str` | Human-readable explanation of the decision |

---

### `SessionState`

Full state of one visitor session. Managed by `SessionStore`.

#### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | `str` | UUID identifier |
| `visitor` | `VisitorProfile` | The visitor |
| `phase` | `SessionPhase` | Current lifecycle phase |
| `primary_intent` | `VisitorIntent` | Most recent detected intent |
| `intent_confidence` | `float` | Confidence in current intent |
| `active_agents` | `dict[str, AgentSessionState]` | Currently recruited agents |
| `engagement_level` | `float` | Real-time engagement (0.0–1.0) |
| `satisfaction_score` | `float` | Cumulative satisfaction |
| `turn_count` | `int` | Total messages in session |
| `consecutive_low_confidence` | `int` | Low-confidence streak (triggers escalation) |
| `escalated` | `bool` | Whether session has been escalated |
| `messages` | `list[MessageRecord]` | Full message history |
| `topics_covered` | `list[str]` | Topics discussed |

#### Key Properties

| Property | Type | Description |
|----------|------|-------------|
| `is_active` | `bool` | `True` unless session has ended |
| `duration_seconds` | `float` | Wall-clock duration since creation |
| `idle_seconds` | `float` | Time since last activity |
| `agent_names` | `list[str]` | Names of all active agents |

---

### `SessionStore`

Manages all active sessions. In-memory for the prototype; override for Durable Objects or D1 in production.

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `create_session(visitor) -> SessionState` | New session | Creates and stores a session |
| `get_session(session_id) -> SessionState \| None` | Session or None | Retrieves by ID |
| `end_session(session_id) -> SessionState \| None` | Ended session | Removes and cleans up |
| `get_active_sessions() -> list[SessionState]` | List | All active sessions |
| `cleanup_idle(timeout_seconds=1800) -> list[str]` | Removed IDs | Reaps idle sessions |
| `active_count -> int` | Property | Count of active sessions |

---

### `IntentAnalyzer`

Lightweight keyword-based intent classifier. No API calls — pure string matching.

#### Class Methods

##### `IntentAnalyzer.analyze(text: str) -> tuple[VisitorIntent, float]`

Classify a single message. Returns `(intent, confidence)` where confidence is 0.0–1.0.

Keyword scoring weights longer keyword matches more heavily. Confidence is the ratio of the best intent's score to the total score across all intents.

```python
intent, confidence = IntentAnalyzer.analyze("I want to write a story")
# VisitorIntent.CREATIVE, 0.72
```

##### `IntentAnalyzer.analyze_history(messages: list[MessageRecord]) -> tuple[VisitorIntent, float]`

Determine dominant intent across a message history. Recent messages carry more weight (linear weighting).

---

### `EngagementTracker`

Tracks visitor engagement based on message signals.

#### Signals Detected

| Type | Examples | Delta |
|------|----------|-------|
| **Positive** | "thanks", "amazing", "tell me more", "love it" | +0.10 |
| **Negative** | "boring", "stop", "not helpful", "bye" | −0.15 |
| **Long message** | > 20 words | +0.05 |
| **Medium message** | > 5 words | +0.02 |
| **Very short** | ≤ 2 words, neutral | −0.05 |
| **Question** | Contains "?" | +0.03 |
| **Silence** | Empty message | −0.15 |

Natural decay: −0.02 per turn (applied regardless).

#### Class Methods

##### `EngagementTracker.assess_message(text: str) -> float`

Returns engagement delta for a message. Positive = engaged, negative = disengaging.

##### `EngagementTracker.update_engagement(current: float, message_delta: float) -> float`

Apply decay + delta, clamped to `[0.0, 1.0]`.

---

### `RecruitmentStrategy`

Controls agent recruitment, roster management, and escalation decisions.

#### Constructor

```python
RecruitmentStrategy(
    max_active_agents: int = 4,
    min_active_agents: int = 1,
    confidence_threshold: float = 0.4,
    consecutive_low_confidence_limit: int = 2,
)
```

#### Methods

##### `initial_roster(intent: VisitorIntent, confidence: float) -> list[str]`

Build the starting agent roster. Always includes `"barnacle"`. Adds intent-matched specialists if confidence is sufficient.

##### `should_escalate(session: SessionState, intent_confidence: float) -> bool`

Check escalation triggers (see [Escalation Thresholds](#escalation-thresholds)).

##### `get_escalation_agent(session: SessionState) -> str | None`

Pick the best heavyweight agent for escalation. Priority: Pro → Nemotron (for systems problems) → Hermes (catalyst).

##### `should_add_agent(session: SessionState) -> str | None`

Check if a new agent should be recruited (e.g., intent shifted and no matching agent is active).

##### `should_remove_agent(session: SessionState) -> str | None`

Check if an idle agent should be dismissed (idle > 120 seconds with < 2 messages sent). Never dismisses Barnacle.

---

## Escalation Thresholds

Escalation brings in a heavyweight model when the conductor can't confidently route messages. There are three independent triggers:

### Trigger 1: Consecutive Low Confidence

When `intent_confidence < confidence_threshold` (default: **0.4**) for `consecutive_low_confidence_limit` (default: **2**) turns in a row, the conductor escalates.

The counter resets to 0 whenever confidence exceeds the threshold.

```python
# Turn 1: confidence 0.2 → counter = 1, no escalation
# Turn 2: confidence 0.3 → counter = 2, ESCALATE
# Turn 3: confidence 0.8 → counter = 0, no escalation
```

### Trigger 2: Engagement Freefall

When `engagement_level < 0.2`, the visitor is disengaging. The conductor escalates immediately, regardless of confidence.

### Trigger 3: Rotation Exhaustion

When `agent_rotation_count > 5`, the conductor has cycled through many agents without finding a fit. Time to bring in the heavyweights.

### Escalation Agent Priority

| Priority | Agent | When |
|----------|-------|------|
| 1 | **Pro** (V4-Pro) | General escalation — the deep reasoner |
| 2 | **Nemotron** (Ultra-550B) | When `primary_intent == PROBLEM_SOLVING` and Pro is already active |
| 3 | **Hermes** (Llama-405B) | When both Pro and Nemotron are active or unavailable — the catalyst |

Escalation is one-way: once `session.escalated = True`, it stays escalated for the remainder of the session.

---

## Configuration

### YAML Config File

```yaml
# config.yaml

session:
  max_active_agents: 4         # max simultaneous agents per session
  min_active_agents: 1         # minimum agents always present

escalation:
  confidence_threshold: 0.4          # below this = low confidence
  consecutive_low_confidence_limit: 2  # turns before escalation triggers

engagement:
  initial_level: 0.5
  high_threshold: 0.7
  low_threshold: 0.3
  decay_per_turn: 0.02
  boost_per_positive: 0.1
  penalty_per_negative: 0.15
```

Load with:

```python
conductor = Conductor.from_config_file("config.yaml")
```

### Programmatic Config

```python
conductor = Conductor(config={
    "session": {"max_active_agents": 6},
    "escalation": {"confidence_threshold": 0.3},
})
```

### Custom Agents

The default pool ships with 7 Tap-themed agents. You can define your own:

```python
from conductor.agent_pool import (
    AgentProfile, AgentTier, AgentAvailability, AGENT_POOL
)

# Register a custom agent
AGENT_POOL["support_tier1"] = AgentProfile(
    name="support_tier1",
    display_name="Tier 1 Support",
    model="gpt-4o-mini",
    provider="openai",
    personality="Friendly first-line support agent.",
    voice_description="Warm, helpful, quick",
    catchphrase="Let's get that sorted.",
    specialties=["conversation", "problem_solving"],
    secondary_skills=["learning"],
    tier=AgentTier.LIGHT,
    availability=AgentAvailability.ALWAYS_ON,
    max_concurrent_sessions=20,
    temperature=0.4,
)

# Remove a default agent if desired
del AGENT_POOL["hermes"]
```

---

## Example: Customer Service Bot System

This example shows how to use the Conductor for a customer service system with tiered support agents.

```python
from conductor import (
    Conductor, VisitorProfile, SessionStore,
)
from conductor.agent_pool import (
    AgentProfile, AgentTier, AgentAvailability, AGENT_POOL,
)
from conductor.session import RecruitmentStrategy

# -----------------------------------------------------------------------
# 1. Define your customer service agents
# -----------------------------------------------------------------------

# Clear defaults and build a custom pool
AGENT_POOL.clear()

AGENT_POOL["greeter"] = AgentProfile(
    name="greeter",
    display_name="Greeter",
    model="claude-haiku",
    provider="anthropic",
    personality="Warm, efficient front desk. Triages issues fast.",
    voice_description="Friendly, professional",
    catchphrase="Hi! How can I help you today?",
    specialties=["conversation", "exploration"],
    tier=AgentTier.LIGHT,
    availability=AgentAvailability.ALWAYS_ON,
    max_concurrent_sessions=100,
    temperature=0.3,
    system_prompt_extra=(
        "You are the front desk agent. Identify the customer's issue "
        "category and either resolve it or route to the right specialist."
    ),
)

AGENT_POOL["billing"] = AgentProfile(
    name="billing",
    display_name="Billing Specialist",
    model="claude-sonnet",
    provider="anthropic",
    personality="Precise with numbers, patient with people.",
    voice_description="Calm, methodical",
    catchphrase="Let me pull up your account.",
    specialties=["problem_solving"],
    secondary_skills=["conversation"],
    tier=AgentTier.LIGHT,
    availability=AgentAvailability.ON_DEMAND,
    cost_per_call=0.002,
    max_concurrent_sessions=10,
    temperature=0.2,  # low temperature for accuracy
)

AGENT_POOL["technical"] = AgentProfile(
    name="technical",
    display_name="Technical Support",
    model="claude-opus",
    provider="anthropic",
    personality="Deep diagnostician. Methodical. Never guesses.",
    voice_description="Measured, confident",
    catchphrase="Let's diagnose this step by step.",
    specialties=["problem_solving", "learning"],
    secondary_skills=["collaboration"],
    tier=AgentTier.HEAVY,
    availability=AgentAvailability.ON_DEMAND,
    cost_per_call=0.015,
    max_concurrent_sessions=3,
    temperature=0.3,
)

AGENT_POOL["escalation"] = AgentProfile(
    name="escalation",
    display_name="Customer Success Manager",
    model="claude-opus",
    provider="anthropic",
    personality="Empathetic, authoritative. Handles angry customers and complex negotiations.",
    voice_description="Calm, warm, reassuring",
    catchphrase="I personally own this issue until it's resolved.",
    specialties=["problem_solving", "conversation"],
    secondary_skills=["collaboration"],
    tier=AgentTier.HEAVY,
    availability=AgentAvailability.ON_DEMAND,
    cost_per_call=0.015,
    max_concurrent_sessions=2,
    temperature=0.5,
)

# -----------------------------------------------------------------------
# 2. Configure the conductor
# -----------------------------------------------------------------------

conductor = Conductor(
    strategy=RecruitmentStrategy(
        max_active_agents=2,       # keep costs down — one specialist + greeter
        min_active_agents=1,
        confidence_threshold=0.35, # customer descriptions can be vague
        consecutive_low_confidence_limit=3,  # give them time to explain
    )
)

# -----------------------------------------------------------------------
# 3. Handle an incoming customer
# -----------------------------------------------------------------------

def handle_customer(customer_id: str, name: str, message: str) -> dict:
    """Process a customer interaction through the conductor."""
    visitor = VisitorProfile(
        visitor_id=customer_id,
        name=name,
        archetype="customer",
    )

    session = conductor.receive_visitor(visitor)
    decision = conductor.route_visitor_message(session.session_id, message)

    # The decision tells us which agent(s) should respond.
    # In a real system, you'd call your LLM here:
    response = generate_response(
        agent_name=decision.responding_agents[0],
        message=message,
        session=session,
    )

    conductor.route_agent_response(
        session.session_id,
        decision.responding_agents[0],
        response,
    )

    # Check if we need to escalate
    if decision.escalate:
        # Escalation agent is brought in — generate their response too
        esc_response = generate_response(
            agent_name=decision.escalation_agent,
            message=message,
            session=session,
        )
        conductor.route_agent_response(
            session.session_id,
            decision.escalation_agent,
            esc_response,
        )

    conductor.end_session(session.session_id)

    return {
        "response": response,
        "escalated": decision.escalate,
        "agent": decision.responding_agents[0],
        "satisfaction": conductor.get_session_status(session.session_id).get("satisfaction", 0),
    }


def generate_response(agent_name: str, message: str, session) -> str:
    """Call your LLM provider here. This is a stub."""
    agent = AGENT_POOL[agent_name]
    # In production:
    # return llm_client.chat.completions.create(
    #     model=agent.model,
    #     temperature=agent.temperature,
    #     messages=[
    #         {"role": "system", "content": agent.system_prompt_extra},
    #         {"role": "user", "content": message},
    #     ],
    # ).choices[0].message.content
    return f"[{agent.display_name}]: I understand. Let me help with that."


# -----------------------------------------------------------------------
# 4. Run it
# -----------------------------------------------------------------------

result = handle_customer(
    "cust-001",
    "Jane Doe",
    "I was charged twice for my subscription and I can't reach anyone.",
)
print(result)
# The conductor routes to "billing" because "charged" → problem_solving intent
# If the customer gets angry, engagement drops → escalation to "escalation" agent
```

---

## Integration Patterns

### Pattern 1: WebSocket Server

```python
import asyncio
import websockets
import json

conductor = Conductor()

async def handle_connection(websocket):
    # First message must be the visitor profile
    intro = json.loads(await websocket.recv())
    visitor = VisitorProfile(
        visitor_id=intro["visitor_id"],
        name=intro["name"],
    )
    session = conductor.receive_visitor(visitor)

    try:
        async for raw in websocket:
            msg = json.loads(raw)
            decision = conductor.route_visitor_message(
                session.session_id, msg["text"]
            )

            # Send routing decision to client
            await websocket.send(json.dumps({
                "type": "routing",
                "responding_agents": decision.responding_agents,
                "intent": decision.intent.value,
                "confidence": decision.confidence,
                "escalated": decision.escalate,
            }))

            # Client generates responses externally and sends them back
    finally:
        conductor.end_session(session.session_id)
```

### Pattern 2: REST API (FastAPI)

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
conductor = Conductor()

class VisitorCreate(BaseModel):
    visitor_id: str
    name: str

class MessageSend(BaseModel):
    session_id: str
    text: str

@app.post("/sessions")
def create_session(visitor: VisitorCreate):
    session = conductor.receive_visitor(VisitorProfile(**visitor.dict()))
    return {"session_id": session.session_id}

@app.post("/messages")
def send_message(msg: MessageSend):
    decision = conductor.route_visitor_message(msg.session_id, msg.text)
    return {
        "responding_agents": decision.responding_agents,
        "intent": decision.intent.value,
        "confidence": decision.confidence,
        "escalated": decision.escalate,
    }
```

### Pattern 3: Custom Session Store (Durable Objects)

```python
from conductor.session import SessionStore, SessionState

class DurableObjectSessionStore(SessionStore):
    """Session store backed by Cloudflare Durable Objects."""

    async def create_session(self, visitor):
        # In production: call DO to create session
        session = SessionState(session_id=str(uuid.uuid4()), visitor=visitor)
        await self._do_fetch("PUT", f"/sessions/{session.session_id}", session.__dict__)
        return session

    async def get_session(self, session_id):
        data = await self._do_fetch("GET", f"/sessions/{session_id}")
        return SessionState(**data) if data else None

    # ... implement end_session, cleanup_idle similarly
```

### Pattern 4: Integration with Sonic Shape

```python
from sonic_shape import confidence_to_music
from conductor import Conductor

conductor = Conductor()

# After each routing decision, map confidence to music
decision = conductor.route_visitor_message(session_id, message)
musical_params = confidence_to_music(decision.confidence)
# Play uncertain music if confidence is low, confident music if high
```

---

## License

MIT © Lucineer / Casey DiGenaro
