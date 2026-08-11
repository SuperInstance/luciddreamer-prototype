"""Hermes Protean Identity System — dynamic avatar state machine."""
from identity_state_machine import (
    ProteanStateMachine,
    OperationalMode,
    Persona,
    MODE_TO_PERSONA,
    PERSONA_TO_MODES,
    TransitionState,
)

__all__ = [
    "ProteanStateMachine",
    "OperationalMode",
    "Persona",
    "MODE_TO_PERSONA",
    "PERSONA_TO_MODES",
    "TransitionState",
]
