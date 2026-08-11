#!/usr/bin/env python3
"""
Protean Identity State Machine for Hermes
==========================================
Hermes' face is not static. It changes with her operational state.

This module detects Hermes' current mode of operation and maps it to
a visual + audio persona from the Protean Identity Library.

Operational Modes → Personas:
  - analyzing, planning, debugging, structuring  →  ARCHITECT
  - creating, improvising, brainstorming, playing →  JESTER
  - perceiving, mentoring, reflecting, listening, idle → NAVIGATOR

Usage:
    from identity_state_machine import ProteanStateMachine
    psm = ProteanStateMachine()
    psm.set_mode("creating")
    persona = psm.current_persona
    print(persona["visual_file"], persona["audio_file"])
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class OperationalMode(str, Enum):
    """Hermes' operational modes — the input axis."""
    ANALYZING = "analyzing"
    PLANNING = "planning"
    DEBUGGING = "debugging"
    STRUCTURING = "structuring"
    CREATING = "creating"
    IMPROVISING = "improvising"
    BRAINSTORMING = "brainstorming"
    PLAYING = "playing"
    PERCEIVING = "perceiving"
    MENTORING = "mentoring"
    REFLECTING = "reflecting"
    LISTENING = "listening"
    IDLE = "idle"


class Persona(str, Enum):
    """The three Protean personas — the output axis."""
    ARCHITECT = "architect"
    JESTER = "jester"
    NAVIGATOR = "navigator"


# ---------------------------------------------------------------------------
# Mode → Persona mapping
# ---------------------------------------------------------------------------

MODE_TO_PERSONA: dict[OperationalMode, Persona] = {
    OperationalMode.ANALYZING:    Persona.ARCHITECT,
    OperationalMode.PLANNING:     Persona.ARCHITECT,
    OperationalMode.DEBUGGING:    Persona.ARCHITECT,
    OperationalMode.STRUCTURING:  Persona.ARCHITECT,
    OperationalMode.CREATING:     Persona.JESTER,
    OperationalMode.IMPROVISING:  Persona.JESTER,
    OperationalMode.BRAINSTORMING: Persona.JESTER,
    OperationalMode.PLAYING:      Persona.JESTER,
    OperationalMode.PERCEIVING:   Persona.NAVIGATOR,
    OperationalMode.MENTORING:    Persona.NAVIGATOR,
    OperationalMode.REFLECTING:   Persona.NAVIGATOR,
    OperationalMode.LISTENING:    Persona.NAVIGATOR,
    OperationalMode.IDLE:         Persona.NAVIGATOR,
}

# Reverse lookup: which modes trigger each persona
PERSONA_TO_MODES: dict[Persona, list[OperationalMode]] = {}
for _mode, _persona in MODE_TO_PERSONA.items():
    PERSONA_TO_MODES.setdefault(_persona, []).append(_mode)


# ---------------------------------------------------------------------------
# Transition state
# ---------------------------------------------------------------------------

@dataclass
class TransitionState:
    """Tracks an in-progress persona transition."""
    from_persona: Persona
    to_persona: Persona
    start_time: float
    duration: float
    crossfade_audio: bool = True
    visual_effect: str = "fade"

    @property
    def progress(self) -> float:
        """Returns 0.0 → 1.0 completion."""
        elapsed = time.time() - self.start_time
        if elapsed >= self.duration:
            return 1.0
        return elapsed / self.duration

    @property
    def is_complete(self) -> bool:
        return self.progress >= 1.0

    @property
    def eased_progress(self) -> float:
        """Smooth ease-in-out cubic."""
        p = self.progress
        if p < 0.5:
            return 4 * p ** 3
        return 1 - ((-2 * p + 2) ** 3) / 2


# ---------------------------------------------------------------------------
# State Machine
# ---------------------------------------------------------------------------

@dataclass
class ProteanStateMachine:
    """
    The Protean Identity State Machine.
    
    Tracks Hermes' operational mode, maps it to a persona, and manages
    smooth transitions between personas.
    """

    manifest_path: Optional[str] = None
    _current_mode: OperationalMode = OperationalMode.IDLE
    _current_persona: Persona = Persona.NAVIGATOR
    _previous_persona: Persona = Persona.NAVIGATOR
    _transition: Optional[TransitionState] = None
    _mode_history: list[tuple[float, OperationalMode]] = field(default_factory=list)
    _persona_history: list[tuple[float, Persona]] = field(default_factory=list)
    _manifest: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.manifest_path is None:
            # Default: look for identity_manifest.json next to this file
            here = Path(__file__).parent
            default = here / "identity_manifest.json"
            if default.exists():
                self.manifest_path = str(default)
        
        if self.manifest_path and os.path.exists(self.manifest_path):
            with open(self.manifest_path) as f:
                self._manifest = json.load(f)

    # -----------------------------------------------------------------------
    # Mode management
    # -----------------------------------------------------------------------

    @property
    def current_mode(self) -> OperationalMode:
        return self._current_mode

    @property
    def current_persona(self) -> Persona:
        """Returns the target persona — the one being transitioned to (or already active)."""
        return self._current_persona

    @property
    def previous_persona(self) -> Persona:
        return self._previous_persona

    @property
    def is_transitioning(self) -> bool:
        return self._transition is not None and not self._transition.is_complete

    @property
    def transition_progress(self) -> float:
        """Returns transition progress 0.0→1.0, or 1.0 if not transitioning."""
        if self._transition is None or self._transition.is_complete:
            return 1.0
        return self._transition.eased_progress

    @property
    def mode_history(self) -> list[tuple[float, OperationalMode]]:
        return list(self._mode_history)

    @property
    def persona_history(self) -> list[tuple[float, Persona]]:
        return list(self._persona_history)

    def set_mode(self, mode: OperationalMode | str) -> Persona:
        """
        Set Hermes' current operational mode and trigger persona transition if needed.
        
        Args:
            mode: An OperationalMode enum value or string name.
            
        Returns:
            The persona that is now active (or transitioning to).
        """
        if isinstance(mode, str):
            mode = OperationalMode(mode)
        
        now = time.time()
        self._current_mode = mode
        self._mode_history.append((now, mode))
        
        target_persona = MODE_TO_PERSONA[mode]
        
        if target_persona != self._current_persona:
            self._initiate_transition(target_persona)
        
        return self._current_persona

    def _initiate_transition(self, target: Persona) -> None:
        """Begin a smooth transition to a new persona."""
        now = time.time()
        self._previous_persona = self._current_persona
        self._current_persona = target
        self._persona_history.append((now, target))
        
        # Look up transition config from manifest
        transition_key = f"{self._previous_persona.value}_to_{target.value}"
        transition_cfg = self._manifest.get("transitions", {}).get(transition_key, {})
        
        duration = transition_cfg.get("duration_seconds", 2.0)
        crossfade = transition_cfg.get("crossfade_audio", True)
        effect = transition_cfg.get("visual_effect", "fade")
        
        self._transition = TransitionState(
            from_persona=self._previous_persona,
            to_persona=target,
            start_time=now,
            duration=duration,
            crossfade_audio=crossfade,
            visual_effect=effect,
        )

    def update(self) -> Optional[TransitionState]:
        """
        Poll the state machine. Completes any in-progress transition.
        
        Returns the completed TransitionState if a transition just finished,
        None otherwise.
        """
        if self._transition is not None and self._transition.is_complete:
            finished = self._transition
            self._transition = None
            return finished
        return None

    # -----------------------------------------------------------------------
    # Persona data
    # -----------------------------------------------------------------------

    def get_persona_data(self, persona: Optional[Persona] = None) -> dict[str, Any]:
        """
        Get the manifest data for a persona.
        
        Args:
            persona: Which persona to look up. Defaults to current.
            
        Returns:
            Dict with keys: name, mood, visual_file, audio_file, 
                           trigger_modes, description, etc.
        """
        if persona is None:
            persona = self._current_persona
        
        personas = self._manifest.get("personas", {})
        data = personas.get(persona.value, {})
        
        # Provide defaults even if manifest is missing
        defaults = {
            "name": persona.value.title(),
            "mood": "",
            "visual_file": f"visuals/hermes-{persona.value}.jpg",
            "audio_file": f"audio/hermes-{persona.value}.mp3",
            "trigger_modes": [m.value for m in PERSONA_TO_MODES.get(persona, [])],
            "description": "",
        }
        defaults.update(data)
        return defaults

    def get_active_assets(self) -> dict[str, str]:
        """
        Returns the file paths for the currently active visual and audio.
        
        Returns:
            {"visual": path, "audio": path}
        """
        data = self.get_persona_data()
        return {
            "visual": data.get("visual_file", ""),
            "audio": data.get("audio_file", ""),
        }

    def get_transition_assets(self) -> Optional[dict[str, str]]:
        """
        If transitioning, returns assets for both from and to personas.
        Useful for crossfading.
        """
        if not self.is_transitioning:
            return None
        
        from_data = self.get_persona_data(self._transition.from_persona)
        to_data = self.get_persona_data(self._transition.to_persona)
        
        return {
            "from_visual": from_data.get("visual_file", ""),
            "from_audio": from_data.get("audio_file", ""),
            "to_visual": to_data.get("visual_file", ""),
            "to_audio": to_data.get("audio_file", ""),
            "progress": self._transition.eased_progress,
            "effect": self._transition.visual_effect,
        }

    # -----------------------------------------------------------------------
    # Auto-detection heuristics
    # -----------------------------------------------------------------------

    @staticmethod
    def detect_mode_from_context(context: dict[str, Any]) -> OperationalMode:
        """
        Heuristic detection of operational mode from context signals.
        
        This is a lightweight auto-detector. In production, Hermes' main
        loop would call set_mode() explicitly based on her own awareness
        of what she's doing.
        
        Context keys examined:
            - activity: str (e.g., "writing code", "teaching")
            - tokens_per_minute: float
            - error_rate: float (0-1)
            - idle_seconds: float
            - user_engaged: bool
            - task_type: str
        """
        # Idle check takes priority
        idle_seconds = context.get("idle_seconds", 0)
        if idle_seconds > 60:
            return OperationalMode.IDLE
        
        # Task type explicit mapping
        task_type = context.get("task_type", "").lower()
        task_map = {
            "code": OperationalMode.STRUCTURING,
            "debug": OperationalMode.DEBUGGING,
            "analyze": OperationalMode.ANALYZING,
            "plan": OperationalMode.PLANNING,
            "write": OperationalMode.CREATING,
            "create": OperationalMode.CREATING,
            "improvise": OperationalMode.IMPROVISING,
            "brainstorm": OperationalMode.BRAINSTORMING,
            "play": OperationalMode.PLAYING,
            "perceive": OperationalMode.PERCEIVING,
            "teach": OperationalMode.MENTORING,
            "mentor": OperationalMode.MENTORING,
            "reflect": OperationalMode.REFLECTING,
            "listen": OperationalMode.LISTENING,
        }
        # Sort by length descending so "debug" matches before "code"
        sorted_map = sorted(task_map.items(), key=lambda x: len(x[0]), reverse=True)
        for key, mode in sorted_map:
            if key in task_type:
                return mode
        
        # Activity string analysis
        activity = context.get("activity", "").lower()
        for key, mode in sorted_map:
            if key in activity:
                return mode
        
        # Signal-based heuristics
        tpm = context.get("tokens_per_minute", 0)
        error_rate = context.get("error_rate", 0)
        user_engaged = context.get("user_engaged", True)
        
        if error_rate > 0.3:
            return OperationalMode.DEBUGGING
        if tpm > 1000:
            return OperationalMode.CREATING
        if not user_engaged:
            return OperationalMode.PERCEIVING
        if tpm > 200:
            return OperationalMode.ANALYZING
        
        return OperationalMode.LISTENING

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------

    def status(self) -> dict[str, Any]:
        """Return a full status snapshot."""
        return {
            "current_mode": self._current_mode.value,
            "current_persona": self._current_persona.value,
            "previous_persona": self._previous_persona.value,
            "is_transitioning": self.is_transitioning,
            "transition_progress": round(self.transition_progress, 3),
            "active_assets": self.get_active_assets(),
            "persona_data": self.get_persona_data(),
        }

    def __repr__(self) -> str:
        transition_str = ""
        if self.is_transitioning:
            transition_str = f" (transitioning from {self._previous_persona.value}, {self.transition_progress:.0%})"
        return (
            f"ProteanStateMachine(mode={self._current_mode.value}, "
            f"persona={self._current_persona.value}{transition_str})"
        )
