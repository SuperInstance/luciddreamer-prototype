# workspace.md — you own this file

## Goal: Design v2 of this agent loop — the sandboxed tool layer.
The Architect (you) gets shell tools in v2. We need: an allowlist of safe
commands, a human approval gate, and an audit log. Sketch concrete Python.
!note prefer concrete dataclasses and enums over loose dicts

# Conductor accepted this reflex completion:
```python
from enum import Enum

class Tool(Enum):
    LS = "ls"
    PYTEST = "pytest"
    GIT_STATUS = "git status"
```

!fix ALLOWED = ['ls', 'pytest', 'git status'] => class Tool(Enum): LS='ls'; PYTEST='pytest'
!step
# Conductor: one more — sketch the human approval gate now
