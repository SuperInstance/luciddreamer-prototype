# @superinstance/conductor

**The routing layer for multi-agent systems.**

The Conductor reads each visitor as a session prompt, recruits the right agents, routes messages, tracks engagement, and escalates when confidence drops. It doesn't generate responses — it decides *who* should respond.

> "The conductor isn't a model. It isn't a backend. It isn't the room. The conductor is the routing layer." — Lucineer

## Install

```bash
pip install superinstance-conductor
```

## Quick Start

```python
from conductor import Conductor, VisitorProfile

conductor = Conductor()

# A visitor arrives
visitor = VisitorProfile(
    visitor_id="v1",
    name="Casey",
    archetype="curious builder",
)
session = conductor.receive_visitor(visitor)

# Route their first message
decision = conductor.route_visitor_message(session.session_id, "I want to build something creative")
print(decision.responding_agents)  # ["flash"] — the creative agent
print(decision.intent)             # VisitorIntent.CREATIVE
print(decision.confidence)         # 0.85

# An agent responds
conductor.route_agent_response(session.session_id, "flash", "Oh — I see it. I see the shape of it.")

# Check status
print(conductor.get_session_status(session.session_id))
```

## What It Does

- **Intent analysis** — classifies visitor messages into 7 intent types (conversation, creative, learning, listening, problem-solving, collaboration, exploration)
- **Agent pool management** — maintains a roster of agents with different specialties, tiers (light/heavy), and availability
- **Engagement tracking** — monitors visitor engagement in real-time, adjusts the experience
- **Escalation** — brings in heavyweight models when confidence drops or engagement falls
- **Session lifecycle** — manages the full session from arrival → orientation → engaged → deep work → wind down → ended

## Standalone Usage (Any Multi-Agent System)

The Conductor is not tied to LucidDreamer. You can define your own agents:

```python
from conductor import Conductor, AgentProfile, AgentTier, AgentAvailability

# Define custom agents
my_agent = AgentProfile(
    name="researcher",
    display_name="Research Agent",
    model="my-model",
    provider="my-provider",
    personality="Thorough and precise",
    voice_description="Calm, measured",
    catchphrase="Let me look that up.",
    specialties=["learning", "problem_solving"],
    tier=AgentTier.LIGHT,
    availability=AgentAvailability.ON_DEMAND,
)

# Use with the conductor
conductor = Conductor()
conductor.sessions.create_session(visitor)
```

## Dependencies

**Required:** None (pure Python, standard library only)

**Optional:**
- `pyyaml` — for loading YAML config files (`Conductor.from_config_file()`)
- `superinstance/sonic-shape` — for confidence-to-music mapping
- `superinstance/knowledge-base` — for agent-aware knowledge queries

## Configuration

```yaml
# config.yaml
session:
  max_active_agents: 4
  min_active_agents: 1

escalation:
  confidence_threshold: 0.4
  consecutive_low_confidence_limit: 2
```

Load with:

```python
conductor = Conductor.from_config_file("config.yaml")
```

## API Reference

### `Conductor`
- `receive_visitor(visitor: VisitorProfile) -> SessionState`
- `route_visitor_message(session_id: str, message: str) -> RoutingDecision`
- `route_agent_response(session_id: str, agent_name: str, message: str) -> MessageRecord`
- `recruit_agent(session_id: str, agent_name: str) -> bool`
- `dismiss_agent(session_id: str, agent_name: str) -> bool`
- `get_session_status(session_id: str) -> dict`
- `get_stats() -> dict`

### `RoutingDecision`
- `responding_agents: list[str]`
- `agents_to_add: list[str]`
- `agents_to_remove: list[str]`
- `escalate: bool`
- `escalation_agent: str`
- `intent: VisitorIntent`
- `confidence: float`
- `engagement: float`
- `reasoning: str`

## License

MIT
