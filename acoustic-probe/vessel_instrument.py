"""
vessel_instrument.py — The FV Eileen as a playable virtual instrument.

Maintains current vessel state and exposes it as musical parameters.
Can be "played" by the sonic shape engine or any MIDI consumer.

Usage:
    vessel = VesselInstrument()
    vessel.update(rpm=1800, depth=40, sea_state=3, heading=180, speed=7.5)
    params = vessel.get_musical_parameters()
    pattern = vessel.play(bars=4)
"""

from __future__ import annotations
import time
import math
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from enum import Enum

from telemetry_to_midi import (
    TelemetryToMIDI,
    MIDIPattern,
    rpm_to_bass_frequency,
    rpm_to_bass_midi_note,
    rpm_to_velocity,
    depth_to_harmony,
    depth_to_harmony_label,
    sea_state_to_rhythm,
    heading_to_pan,
    speed_to_tempo,
    speed_to_time_signature,
    MIDI_NOTE_NAMES,
)


# ─── Vessel State ───────────────────────────────────────────────────────────

class VesselMode(Enum):
    """What the FV Eileen is currently doing."""
    DOCKED = "docked"
    DEPARTING = "departing"
    TRANSIT = "transit"
    ARRIVING = "arriving"       # Arrived at fishing ground
    FISHING = "fishing"
    HAULING = "hauling"         # Hauling gear
    RETURNING = "returning"
    ANCHORED = "anchored"
    EMERGENCY = "emergency"


@dataclass
class VesselState:
    """Snapshot of the FV Eileen's physical state."""
    rpm: float = 0.0              # Engine RPM (0-3000)
    depth: float = 0.0            # Water depth in fathoms (0-100+)
    sea_state: float = 0.0        # Beaufort sea state (0-9)
    heading: float = 0.0          # Compass heading (0-360°)
    speed: float = 0.0            # Speed over ground in knots
    latitude: float = 57.79       # Approximate position
    longitude: float = -152.40    # Kodiak area
    timestamp: float = field(default_factory=time.time)
    mode: VesselMode = VesselMode.DOCKED

    # Derived properties (computed on read)
    @property
    def engine_load(self) -> float:
        """0.0 (idle) to 1.0 (max load)."""
        return min(1.0, self.rpm / 3000.0)

    @property
    def is_moving(self) -> bool:
        return self.speed > 0.5

    @property
    def is_fishing(self) -> bool:
        return self.mode == VesselMode.FISHING

    @property
    def is_in_deep_water(self) -> bool:
        return self.depth > 50.0

    @property
    def is_rough(self) -> bool:
        return self.sea_state >= 5.0

    def to_dict(self) -> dict:
        return {
            "rpm": self.rpm,
            "depth": self.depth,
            "sea_state": self.sea_state,
            "heading": self.heading,
            "speed": self.speed,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timestamp": self.timestamp,
            "mode": self.mode.value,
            "engine_load": self.engine_load,
        }


# ─── Musical Parameters ─────────────────────────────────────────────────────

@dataclass
class MusicalParameters:
    """The vessel's current musical identity."""
    bass_note: int = 33           # MIDI note
    bass_frequency: float = 55.0  # Hz
    bass_velocity: int = 40       # 0-127
    harmony_notes: List[int] = field(default_factory=list)
    harmony_label: str = "Root drone"
    rhythm_pattern: List[int] = field(default_factory=lambda: [1, 0, 0, 0] * 4)
    rhythm_density: float = 0.25
    pan: int = 64
    tempo_bpm: float = 60.0
    time_signature: tuple = (4, 4)
    mood: str = "neutral"         # Emotional descriptor
    intensity: float = 0.0        # 0-1 overall energy

    def to_dict(self) -> dict:
        return {
            "bass_note": self.bass_note,
            "bass_note_name": f"{MIDI_NOTE_NAMES[self.bass_note % 12]}{self.bass_note // 12 - 1}",
            "bass_frequency_hz": round(self.bass_frequency, 2),
            "bass_velocity": self.bass_velocity,
            "harmony_notes": self.harmony_notes,
            "harmony_label": self.harmony_label,
            "rhythm_density": round(self.rhythm_density, 3),
            "pan": self.pan,
            "tempo_bpm": round(self.tempo_bpm, 1),
            "time_signature": f"{self.time_signature[0]}/{self.time_signature[1]}",
            "mood": self.mood,
            "intensity": round(self.intensity, 3),
        }


# ─── The Vessel Instrument ──────────────────────────────────────────────────

class VesselInstrument:
    """The FV Eileen as a virtual instrument.

    Ingests telemetry, maintains state, and outputs musical parameters.
    Can be played standalone or connected to the sonic shape engine.
    """

    def __init__(self, name: str = "FV Eileen"):
        self.name = name
        self.state = VesselState()
        self._midi_converter = TelemetryToMIDI()
        self._history: List[VesselState] = []
        self._max_history = 100
        self._listeners: List[callable] = []

    # ── State Management ──

    def update(
        self,
        rpm: Optional[float] = None,
        depth: Optional[float] = None,
        sea_state: Optional[float] = None,
        heading: Optional[float] = None,
        speed: Optional[float] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        mode: Optional[VesselMode] = None,
    ) -> VesselState:
        """Update vessel state with new telemetry. Returns the new state."""
        # Archive previous state
        self._archive_state()

        if rpm is not None:
            self.state.rpm = max(0.0, min(3000.0, rpm))
        if depth is not None:
            self.state.depth = max(0.0, depth)
        if sea_state is not None:
            self.state.sea_state = max(0.0, min(9.0, sea_state))
        if heading is not None:
            self.state.heading = heading % 360.0
        if speed is not None:
            self.state.speed = max(0.0, speed)
        if latitude is not None:
            self.state.latitude = latitude
        if longitude is not None:
            self.state.longitude = longitude
        if mode is not None:
            self.state.mode = mode

        self.state.timestamp = time.time()

        # Auto-detect mode if not specified
        if mode is None:
            self.state.mode = self._detect_mode()

        # Notify listeners
        for listener in self._listeners:
            listener(self.state)

        return self.state

    def update_from_dict(self, data: dict) -> VesselState:
        """Update from a telemetry dictionary."""
        mode = None
        if "mode" in data:
            try:
                mode = VesselMode(data["mode"])
            except ValueError:
                pass

        return self.update(
            rpm=data.get("rpm"),
            depth=data.get("depth"),
            sea_state=data.get("sea_state"),
            heading=data.get("heading"),
            speed=data.get("speed"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            mode=mode,
        )

    def _archive_state(self):
        """Keep a rolling history of past states."""
        import copy
        self._history.append(copy.deepcopy(self.state))
        if len(self._history) > self._max_history:
            self._history.pop(0)

    def _detect_mode(self) -> VesselMode:
        """Heuristic mode detection from current state."""
        s = self.state
        if s.rpm < 100 and s.speed < 0.5:
            if s.depth < 5:
                return VesselMode.DOCKED
            return VesselMode.ANCHORED
        if s.rpm > 2000 and s.speed > 6.0:
            if s.depth > 20:
                return VesselMode.TRANSIT
            return VesselMode.DEPARTING
        if s.rpm < 800 and s.speed < 3.0 and s.depth > 10:
            return VesselMode.FISHING
        if 800 <= s.rpm <= 1600 and 3.0 <= s.speed <= 6.0:
            if s.depth < 10:
                return VesselMode.RETURNING
            return VesselMode.FISHING
        return self.state.mode

    # ── Musical Output ──

    def get_musical_parameters(self) -> MusicalParameters:
        """Convert current vessel state to musical parameters."""
        s = self.state
        bass_note = rpm_to_bass_midi_note(s.rpm)
        harmony = depth_to_harmony(s.depth, bass_note)
        rhythm = sea_state_to_rhythm(s.sea_state)

        params = MusicalParameters(
            bass_note=bass_note,
            bass_frequency=rpm_to_bass_frequency(s.rpm),
            bass_velocity=rpm_to_velocity(s.rpm),
            harmony_notes=harmony,
            harmony_label=depth_to_harmony_label(s.depth),
            rhythm_pattern=rhythm,
            rhythm_density=sum(rhythm) / len(rhythm),
            pan=heading_to_pan(s.heading),
            tempo_bpm=speed_to_tempo(s.speed),
            time_signature=speed_to_time_signature(s.speed),
            mood=self._compute_mood(),
            intensity=self._compute_intensity(),
        )
        return params

    def play(self, bars: int = 4) -> MIDIPattern:
        """Generate a MIDI pattern from current state."""
        return self._midi_converter.generate_pattern(
            self.state.to_dict(), bars=bars
        )

    # ── Emotional / Expressive ──

    def _compute_mood(self) -> str:
        """Derive an emotional descriptor from vessel state."""
        s = self.state
        if s.mode == VesselMode.EMERGENCY:
            return "urgent"
        if s.sea_state >= 7:
            return "turbulent"
        if s.is_fishing and s.depth > 50:
            return "contemplative"
        if s.is_fishing:
            return "focused"
        if s.mode == VesselMode.DEPARTING:
            return "optimistic"
        if s.mode == VesselMode.RETURNING:
            return "weary"
        if s.mode == VesselMode.TRANSIT:
            return "steadfast"
        if s.mode == VesselMode.DOCKED:
            return "restful"
        if s.mode == VesselMode.ANCHORED:
            return "patient"
        return "neutral"

    def _compute_intensity(self) -> float:
        """Overall musical intensity (0-1)."""
        s = self.state
        engine_component = s.engine_load * 0.4
        sea_component = (s.sea_state / 9.0) * 0.3
        depth_component = min(1.0, s.depth / 100.0) * 0.15
        speed_component = min(1.0, s.speed / 15.0) * 0.15
        return engine_component + sea_component + depth_component + speed_component

    # ── Trend Analysis ──

    def get_trend(self, samples: int = 5) -> dict:
        """Analyze recent trends in vessel state."""
        if len(self._history) < 2:
            return {"stable": True}

        recent = self._history[-samples:]
        current = self.state

        rpm_trend = current.rpm - recent[0].rpm if recent else 0
        depth_trend = current.depth - recent[0].depth if recent else 0
        sea_trend = current.sea_state - recent[0].sea_state if recent else 0
        speed_trend = current.speed - recent[0].speed if recent else 0

        return {
            "rpm_change": rpm_trend,
            "depth_change": depth_trend,
            "sea_state_change": sea_trend,
            "speed_change": speed_trend,
            "rpm_rising": rpm_trend > 100,
            "rpm_falling": rpm_trend < -100,
            "deepening": depth_trend > 5,
            "shallowing": depth_trend < -5,
            "roughening": sea_trend > 0.5,
            "calming": sea_trend < -0.5,
            "stable": abs(rpm_trend) < 50 and abs(depth_trend) < 2,
        }

    # ── Listener Pattern ──

    def add_listener(self, callback: callable):
        """Register a callback called on each state update."""
        self._listeners.append(callback)

    def remove_listener(self, callback: callable):
        if callback in self._listeners:
            self._listeners.remove(callback)

    # ── Status ──

    def status(self) -> str:
        """Human-readable status of the vessel as an instrument."""
        params = self.get_musical_parameters()
        s = self.state
        lines = [
            f"═══ {self.name} — Vessel Instrument Status ═══",
            f"  Mode:       {s.mode.value}",
            f"  Engine:     {s.rpm:.0f} RPM ({s.engine_load:.0%} load)",
            f"  Speed:      {s.speed:.1f} knots",
            f"  Heading:    {s.heading:.0f}°",
            f"  Depth:      {s.depth:.0f} fathoms",
            f"  Sea State:  {s.sea_state:.1f} Beaufort",
            f"  Position:   {s.latitude:.4f}, {s.longitude:.4f}",
            f"  ──────────────────────────────",
            f"  Bass:       {MIDI_NOTE_NAMES[params.bass_note % 12]}{params.bass_note // 12 - 1} ({params.bass_frequency:.1f} Hz)",
            f"  Tempo:      {params.tempo_bpm:.1f} BPM",
            f"  Mood:       {params.mood}",
            f"  Intensity:  {params.intensity:.0%}",
            f"  Harmony:    {params.harmony_label}",
            f"  Pan:        {params.pan}/127",
        ]

        trend = self.get_trend()
        if not trend.get("stable", True):
            trend_parts = []
            if trend.get("rpm_rising"):
                trend_parts.append("engine climbing")
            if trend.get("rpm_falling"):
                trend_parts.append("engine laboring")
            if trend.get("deepening"):
                trend_parts.append("going deeper")
            if trend.get("shallowing"):
                trend_parts.append("rising bottom")
            if trend.get("roughening"):
                trend_parts.append("seas building")
            if trend.get("calming"):
                trend_parts.append("seas calming")
            if trend_parts:
                lines.append(f"  Trend:      {', '.join(trend_parts)}")

        return "\n".join(lines)


# ─── CLI ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    vessel = VesselInstrument()

    # Simulate updating vessel state
    print("Updating FV Eileen telemetry...\n")

    vessel.update(rpm=800, depth=10, sea_state=2, heading=90, speed=3.5, mode=VesselMode.DEPARTING)
    print(vessel.status())
    print()

    params = vessel.get_musical_parameters()
    print("Musical parameters:")
    for k, v in params.to_dict().items():
        print(f"  {k}: {v}")

    print(f"\nPlaying 2-bar pattern:")
    pattern = vessel.play(bars=2)
    print(vessel._midi_converter.pattern_to_text(pattern))
