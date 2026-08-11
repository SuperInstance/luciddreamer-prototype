#!/usr/bin/env python3
"""
Tests for the Protean Identity State Machine
=============================================
5+ tests covering mode→persona mapping, transitions, auto-detection,
manifest loading, and edge cases.

Run: python -m pytest tests/ -v
  or: python tests/test_identity.py
"""

import os
import sys
import time
import json
import tempfile
from pathlib import Path

# Make the module importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from identity_state_machine import (
    ProteanStateMachine,
    OperationalMode,
    Persona,
    MODE_TO_PERSONA,
    PERSONA_TO_MODES,
    TransitionState,
)


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def make_psm(manifest_path=None, transition_duration_override=0.0):
    """Create a PSM with zero-duration transitions for testing."""
    psm = ProteanStateMachine(manifest_path=manifest_path)
    return psm


# ---------------------------------------------------------------------------
# TEST 1: Mode → Persona mapping correctness
# ---------------------------------------------------------------------------

def test_mode_to_persona_mapping():
    """Every operational mode maps to the correct persona."""
    # Architect modes
    for mode in [OperationalMode.ANALYZING, OperationalMode.PLANNING,
                 OperationalMode.DEBUGGING, OperationalMode.STRUCTURING]:
        assert MODE_TO_PERSONA[mode] == Persona.ARCHITECT, \
            f"{mode.value} should map to ARCHITECT"
    
    # Jester modes
    for mode in [OperationalMode.CREATING, OperationalMode.IMPROVISING,
                 OperationalMode.BRAINSTORMING, OperationalMode.PLAYING]:
        assert MODE_TO_PERSONA[mode] == Persona.JESTER, \
            f"{mode.value} should map to JESTER"
    
    # Navigator modes
    for mode in [OperationalMode.PERCEIVING, OperationalMode.MENTORING,
                 OperationalMode.REFLECTING, OperationalMode.LISTENING,
                 OperationalMode.IDLE]:
        assert MODE_TO_PERSONA[mode] == Persona.NAVIGATOR, \
            f"{mode.value} should map to NAVIGATOR"
    
    # All 13 modes have mappings
    assert len(MODE_TO_PERSONA) == 13, f"Expected 13 modes, got {len(MODE_TO_PERSONA)}"
    print("✅ test_mode_to_persona_mapping passed")


# ---------------------------------------------------------------------------
# TEST 2: State machine transitions between personas
# ---------------------------------------------------------------------------

def test_state_transitions():
    """PSM correctly transitions between personas when mode changes."""
    psm = make_psm()
    
    # Starts in IDLE → NAVIGATOR
    assert psm.current_persona == Persona.NAVIGATOR
    assert psm.current_mode == OperationalMode.IDLE
    
    # Switch to an Architect mode
    psm.set_mode(OperationalMode.ANALYZING)
    assert psm.current_persona == Persona.ARCHITECT
    assert psm.previous_persona == Persona.NAVIGATOR
    assert psm.is_transitioning  # should be in transition
    
    # Complete the transition
    time.sleep(0.01)
    psm.update()  # may or may not complete depending on duration
    # Force completion by waiting
    if psm._transition:
        psm._transition.duration = 0.0
        psm.update()
    assert not psm.is_transitioning
    
    # Switch to a Jester mode
    psm.set_mode(OperationalMode.CREATING)
    assert psm.current_persona == Persona.JESTER
    assert psm.previous_persona == Persona.ARCHITECT
    
    # Switch to Navigator mode
    psm.set_mode(OperationalMode.REFLECTING)
    assert psm.current_persona == Persona.NAVIGATOR
    assert psm.previous_persona == Persona.JESTER
    
    # Same-persona mode switch does NOT transition
    psm.set_mode(OperationalMode.LISTENING)
    assert psm.current_persona == Persona.NAVIGATOR
    assert psm.previous_persona == Persona.JESTER  # unchanged
    
    print("✅ test_state_transitions passed")


# ---------------------------------------------------------------------------
# TEST 3: Auto-detection from context signals
# ---------------------------------------------------------------------------

def test_auto_detection():
    """detect_mode_from_context correctly infers mode from signals."""
    # Idle detection
    assert ProteanStateMachine.detect_mode_from_context({"idle_seconds": 120}) == OperationalMode.IDLE
    
    # Task type mapping
    assert ProteanStateMachine.detect_mode_from_context({"task_type": "debug this code"}) == OperationalMode.DEBUGGING
    assert ProteanStateMachine.detect_mode_from_context({"task_type": "write a poem"}) == OperationalMode.CREATING
    assert ProteanStateMachine.detect_mode_from_context({"task_type": "teach me algebra"}) == OperationalMode.MENTORING
    assert ProteanStateMachine.detect_mode_from_context({"task_type": "plan the sprint"}) == OperationalMode.PLANNING
    
    # Activity string
    assert ProteanStateMachine.detect_mode_from_context({"activity": "brainstorming ideas"}) == OperationalMode.BRAINSTORMING
    assert ProteanStateMachine.detect_mode_from_context({"activity": "playing a game"}) == OperationalMode.PLAYING
    
    # Signal heuristics
    assert ProteanStateMachine.detect_mode_from_context({
        "error_rate": 0.5
    }) == OperationalMode.DEBUGGING
    
    assert ProteanStateMachine.detect_mode_from_context({
        "tokens_per_minute": 1500
    }) == OperationalMode.CREATING
    
    assert ProteanStateMachine.detect_mode_from_context({
        "user_engaged": False
    }) == OperationalMode.PERCEIVING
    
    # Default fallback
    assert ProteanStateMachine.detect_mode_from_context({}) == OperationalMode.LISTENING
    
    print("✅ test_auto_detection passed")


# ---------------------------------------------------------------------------
# TEST 4: Manifest loading and persona data
# ---------------------------------------------------------------------------

def test_manifest_and_persona_data():
    """PSM loads the manifest and returns correct persona data."""
    manifest_path = str(Path(__file__).parent.parent / "identity_manifest.json")
    psm = make_psm(manifest_path=manifest_path)
    
    # Manifest was loaded
    assert len(psm._manifest) > 0
    assert "personas" in psm._manifest
    
    # Get architect data
    arch = psm.get_persona_data(Persona.ARCHITECT)
    assert arch["name"] == "The Architect"
    assert "visual_file" in arch
    assert "audio_file" in arch
    assert "hermes-architect" in arch["visual_file"]
    assert "hermes-architect" in arch["audio_file"]
    assert "analyzing" in arch["trigger_modes"]
    assert len(arch["description"]) > 50
    
    # Get jester data
    jest = psm.get_persona_data(Persona.JESTER)
    assert jest["name"] == "The Jester"
    assert jest["energy_level"] == 0.95
    
    # Get navigator data
    nav = psm.get_persona_data(Persona.NAVIGATOR)
    assert nav["name"] == "The Navigator"
    assert nav["energy_level"] == 0.25
    
    # Active assets for current persona
    psm.set_mode(OperationalMode.CREATING)
    assets = psm.get_active_assets()
    assert "hermes-jester" in assets["visual"]
    assert "hermes-jester" in assets["audio"]
    
    print("✅ test_manifest_and_persona_data passed")


# ---------------------------------------------------------------------------
# TEST 5: Transition states and smooth interpolation
# ---------------------------------------------------------------------------

def test_transition_states():
    """TransitionState correctly tracks progress and eased interpolation."""
    # Create a transition with known duration
    ts = TransitionState(
        from_persona=Persona.NAVIGATOR,
        to_persona=Persona.JESTER,
        start_time=time.time(),
        duration=1.0,
    )
    
    # At start: progress ~0
    assert ts.progress < 0.1
    assert not ts.is_complete
    assert ts.eased_progress < 0.1  # ease-in-out starts slow
    
    # Simulate mid-transition
    ts.start_time = time.time() - 0.5  # halfway
    assert 0.4 < ts.progress < 0.6
    assert 0.4 < ts.eased_progress < 0.6
    
    # Simulate completion
    ts.start_time = time.time() - 2.0  # well past duration
    assert ts.progress == 1.0
    assert ts.is_complete
    assert ts.eased_progress == 1.0
    
    # Test eased curve: midpoint of ease-in-out cubic ≈ 0.5
    ts2 = TransitionState(
        from_persona=Persona.ARCHITECT,
        to_persona=Persona.NAVIGATOR,
        start_time=time.time() - 0.5,
        duration=1.0,
    )
    assert abs(ts2.eased_progress - 0.5) < 0.01  # eased midpoint should be ~0.5
    
    print("✅ test_transition_states passed")


# ---------------------------------------------------------------------------
# TEST 6: Transition assets for crossfading
# ---------------------------------------------------------------------------

def test_transition_assets():
    """get_transition_assets returns correct from/to during a transition."""
    manifest_path = str(Path(__file__).parent.parent / "identity_manifest.json")
    psm = make_psm(manifest_path=manifest_path)
    
    # Not transitioning → None
    assert psm.get_transition_assets() is None
    
    # Trigger a transition
    psm.set_mode(OperationalMode.ANALYZING)  # NAVIGATOR → ARCHITECT
    assert psm.is_transitioning
    
    assets = psm.get_transition_assets()
    assert assets is not None
    assert "hermes-navigator" in assets["from_visual"]
    assert "hermes-architect" in assets["to_visual"]
    assert "from_audio" in assets
    assert "to_audio" in assets
    assert 0.0 <= assets["progress"] <= 1.0
    assert "effect" in assets
    
    print("✅ test_transition_assets passed")


# ---------------------------------------------------------------------------
# TEST 7: History tracking
# ---------------------------------------------------------------------------

def test_history_tracking():
    """PSM tracks mode and persona history."""
    psm = make_psm()
    
    # Clear initial state history
    psm._mode_history.clear()
    psm._persona_history.clear()
    
    psm.set_mode(OperationalMode.ANALYZING)
    psm.set_mode(OperationalMode.STRUCTURING)  # same persona, no transition
    psm.set_mode(OperationalMode.CREATING)
    psm.set_mode(OperationalMode.REFLECTING)
    
    # Mode history records every set_mode call
    assert len(psm.mode_history) == 4
    
    # Persona history only records actual transitions
    assert len(psm.persona_history) == 3  # ARCHITECT, JESTER, NAVIGATOR
    
    # Verify order
    personas = [p for _, p in psm.persona_history]
    assert personas == [Persona.ARCHITECT, Persona.JESTER, Persona.NAVIGATOR]
    
    print("✅ test_history_tracking passed")


# ---------------------------------------------------------------------------
# TEST 8: Status snapshot
# ---------------------------------------------------------------------------

def test_status_snapshot():
    """status() returns a complete, well-structured snapshot."""
    psm = make_psm()
    psm.set_mode(OperationalMode.IMPROVISING)
    
    status = psm.status()
    
    assert status["current_mode"] == "improvising"
    assert status["current_persona"] == "jester"
    assert "is_transitioning" in status
    assert "transition_progress" in status
    assert "active_assets" in status
    assert "persona_data" in status
    assert status["persona_data"]["name"] == "The Jester"
    
    print("✅ test_status_snapshot passed")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n🧪 Running Protean Identity Tests\n" + "=" * 50)
    test_mode_to_persona_mapping()
    test_state_transitions()
    test_auto_detection()
    test_manifest_and_persona_data()
    test_transition_states()
    test_transition_assets()
    test_history_tracking()
    test_status_snapshot()
    print("\n" + "=" * 50)
    print(f"🎉 All 8 tests passed!\n")
