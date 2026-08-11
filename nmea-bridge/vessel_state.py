"""
vessel_state.py — Maintains current vessel state from NMEA stream.

Holds the live state of the vessel, computes derived modes (fishing, transit,
anchored), and exposes musical parameters for the acoustic probe / sonic shape
engine. Agents can query this to know what the boat is doing.

Usage:
    state = VesselStateManager()
    state.update_from_nmea(parsed_sentence)
    print(state.current.mode)         # VesselMode.FISHING
    print(state.musical_parameters())  # MusicalParameters(...)
"""

from __future__ import annotations

import time
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any
from collections import deque


# ─── Vessel Mode ────────────────────────────────────────────────────────────

class VesselMode(Enum):
    """What the vessel is currently doing — derived from telemetry."""
    UNKNOWN = "unknown"
    DOCKED = "docked"
    DEPARTING = "departing"
    TRANSIT = "transit"
    FISHING = "fishing"
    HAULING = "hauling"
    RETURNING = "returning"
    ANCHORED = "anchored"
    EMERGENCY = "emergency"


# ─── Sea State (Beaufort scale) ─────────────────────────────────────────────

BEAUFORT_FROM_KNOTS = [
    (1, 0),    # Calm
    (3, 1),    # Light air
    (6, 2),    # Light breeze
    (10, 3),   # Gentle breeze
    (16, 4),   # Moderate breeze
    (21, 5),   # Fresh breeze
    (27, 6),   # Strong breeze
    (33, 7),   # Near gale
    (40, 8),   # Gale
    (47, 9),   # Strong gale
    (55, 10),  # Storm
    (100, 11), # Violent storm
    (999, 12), # Hurricane
]


def wind_to_beaufort(knots: float) -> float:
    """Approximate Beaufort sea state from wind speed in knots."""
    for threshold, beaufort in BEAUFORT_FROM_KNOTS:
        if knots <= threshold:
            return float(beaufort)
    return 12.0


# ─── Vessel State ───────────────────────────────────────────────────────────

@dataclass
class VesselState:
    """Snapshot of the vessel's physical state from NMEA instruments."""
    # Position
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    fix_quality: int = 0          # GPS fix quality (0=no fix, 1=GPS, 2=DGPS)

    # Motion
    heading: Optional[float] = None        # degrees true
    heading_magnetic: Optional[float] = None
    speed_over_ground: Optional[float] = None    # knots
    speed_through_water: Optional[float] = None  # knots
    course_over_ground: Optional[float] = None   # degrees

    # Environment
    depth: Optional[float] = None           # fathoms
    depth_meters: Optional[float] = None
    water_temperature: Optional[float] = None  # Celsius
    sea_state: float = 0.0                  # Beaufort (estimated)

    # Engine / Systems
    engine_rpm: Optional[float] = None
    tank_level: Optional[float] = None      # 0-100%
    battery_voltage: Optional[float] = None

    # Derived
    mode: VesselMode = VesselMode.UNKNOWN
    timestamp: float = field(default_factory=time.time)

    # Previous depth for fishing detection
    _prev_depth: Optional[float] = field(default=None, repr=False)

    @property
    def is_moving(self) -> bool:
        """Vessel is making way."""
        sog = self.speed_over_ground or 0.0
        return sog > 0.5

    @property
    def is_fishing(self) -> bool:
        return self.mode == VesselMode.FISHING

    @property
    def is_transit(self) -> bool:
        return self.mode == VesselMode.TRANSIT

    @property
    def is_anchored(self) -> bool:
        return self.mode == VesselMode.ANCHORED

    @property
    def engine_load(self) -> float:
        """0.0 (idle) to 1.0 (max load)."""
        if self.engine_rpm is None:
            return 0.0
        return min(1.0, self.engine_rpm / 2800.0)

    @property
    def position_valid(self) -> bool:
        return self.fix_quality > 0 and self.latitude is not None and self.longitude is not None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "fix_quality": self.fix_quality,
            "heading": self.heading,
            "speed_over_ground": self.speed_over_ground,
            "speed_through_water": self.speed_through_water,
            "depth": self.depth,
            "depth_meters": self.depth_meters,
            "water_temperature": self.water_temperature,
            "sea_state": self.sea_state,
            "engine_rpm": self.engine_rpm,
            "tank_level": self.tank_level,
            "battery_voltage": self.battery_voltage,
            "mode": self.mode.value,
            "timestamp": self.timestamp,
        }


# ─── Musical Parameters ─────────────────────────────────────────────────────

@dataclass
class MusicalParameters:
    """Musical parameters derived from vessel state.

    Feeds into the acoustic probe's telemetry_to_midi and the sonic shape
    engine's harmonic dictionary.
    """
    bass_note: int = 33              # MIDI note for engine RPM
    bass_frequency: float = 55.0     # Hz
    bass_velocity: int = 40          # 0-127
    harmony_notes: List[int] = field(default_factory=list)
    harmony_label: str = "Root drone"
    rhythm_density: float = 0.25     # 0-1
    pan: int = 64                    # 0=hard left, 64=center, 127=hard right
    tempo_bpm: float = 60.0
    mood: str = "neutral"
    intensity: float = 0.0           # 0-1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bass_note": self.bass_note,
            "bass_frequency_hz": round(self.bass_frequency, 2),
            "bass_velocity": self.bass_velocity,
            "harmony_notes": self.harmony_notes,
            "harmony_label": self.harmony_label,
            "rhythm_density": round(self.rhythm_density, 3),
            "pan": self.pan,
            "tempo_bpm": round(self.tempo_bpm, 1),
            "mood": self.mood,
            "intensity": round(self.intensity, 3),
        }


# ─── Harmony / Music Mapping (mirrors acoustic-probe patterns) ──────────────

# Depth → harmonic complexity tiers (fathoms)
HARMONY_TIERS = [
    (10,  [0],                                    "Root drone"),
    (25,  [0, 7],                                  "Open fifth"),
    (40,  [0, 7, 12],                              "Octave power"),
    (55,  [0, 4, 7, 11],                           "Major 7th"),
    (70,  [0, 3, 7, 10, 14],                       "Minor 9th"),
    (82,  [0, 3, 7, 10, 14, 17],                   "Minor 11th"),
    (90,  [0, 1, 3, 5, 6, 7, 8, 10, 11, 13],       "Chromatic clusters"),
    (999, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],  "Full chromatic fog"),
]

# Sea state → rhythm density
SEA_STATE_DENSITY = {
    0: 0.25, 1: 0.3125, 2: 0.375, 3: 0.5, 4: 0.5625,
    5: 0.625, 6: 0.6875, 7: 0.75, 8: 0.8125, 9: 0.875,
}


def rpm_to_bass_midi(rpm: float) -> int:
    """Map engine RPM to a MIDI note (A1=33 at idle → A3=57 at full)."""
    clamped = max(0.0, min(2800.0, rpm))
    t = clamped / 2800.0
    return round(33 + t * (57 - 33))


def rpm_to_bass_freq(rpm: float) -> float:
    """Map engine RPM to bass frequency (55Hz → 220Hz, exponential)."""
    clamped = max(0.0, min(2800.0, rpm))
    t = clamped / 2800.0
    return 55.0 * (220.0 / 55.0) ** t


def depth_to_harmony(depth_fathoms: float) -> tuple:
    """Map depth to harmonic intervals and label."""
    for threshold, intervals, label in HARMONY_TIERS:
        if depth_fathoms <= threshold:
            return intervals, label
    return HARMONY_TIERS[-1][1], HARMONY_TIERS[-1][2]


def heading_to_pan(heading: float) -> int:
    """Map heading to pan (0°=left, 180°=center, 360°=right)."""
    return int(round((heading % 360.0) / 360.0 * 127))


def speed_to_tempo(speed_kts: float) -> float:
    """Map speed to tempo (0 kts → 60 BPM, 20+ kts → 160 BPM)."""
    t = min(1.0, max(0.0, speed_kts / 20.0))
    return 60.0 + t * (160.0 - 60.0)


# ─── State Manager ──────────────────────────────────────────────────────────

class VesselStateManager:
    """Maintains and updates vessel state from NMEA data.

    Computes derived mode (fishing, transit, etc.) and musical parameters.
    Keeps a rolling history for trend detection.
    """

    HISTORY_SIZE = 120  # Keep last 120 state updates

    def __init__(self, name: str = "FV Eileen"):
        self.name = name
        self.state = VesselState()
        self.history: deque = deque(maxlen=self.HISTORY_SIZE)
        self._listeners: List[callable] = []

    def update_position(self, lat: float, lon: float, fix_quality: int = 1):
        """Update GPS position."""
        self.state.latitude = lat
        self.state.longitude = lon
        self.state.fix_quality = fix_quality
        self._tick()

    def update_heading(self, heading: float, magnetic: bool = False):
        """Update vessel heading."""
        if magnetic:
            self.state.heading_magnetic = heading % 360.0
        else:
            self.state.heading = heading % 360.0
        self._tick()

    def update_speed(self, sog: Optional[float] = None, stw: Optional[float] = None):
        """Update speed over ground and/or through water."""
        if sog is not None:
            self.state.speed_over_ground = max(0.0, sog)
        if stw is not None:
            self.state.speed_through_water = max(0.0, stw)
        self._tick()

    def update_depth(self, depth_fathoms: Optional[float] = None,
                     depth_meters: Optional[float] = None):
        """Update water depth."""
        if depth_fathoms is not None:
            self.state.depth = max(0.0, depth_fathoms)
            self.state.depth_meters = self.state.depth * 1.8288
        elif depth_meters is not None:
            self.state.depth_meters = max(0.0, depth_meters)
            self.state.depth = depth_meters / 1.8288
        self._tick()

    def update_course(self, cog: float):
        """Update course over ground."""
        self.state.course_over_ground = cog % 360.0
        self._tick()

    def update_engine(self, rpm: Optional[float] = None,
                      tank_level: Optional[float] = None,
                      battery_voltage: Optional[float] = None):
        """Update engine/system readings."""
        if rpm is not None:
            self.state.engine_rpm = max(0.0, rpm)
        if tank_level is not None:
            self.state.tank_level = max(0.0, min(100.0, tank_level))
        if battery_voltage is not None:
            self.state.battery_voltage = battery_voltage
        self._tick()

    def update_environment(self, water_temp: Optional[float] = None,
                           sea_state: Optional[float] = None,
                           wind_speed_kts: Optional[float] = None):
        """Update environmental sensors."""
        if water_temp is not None:
            self.state.water_temperature = water_temp
        if sea_state is not None:
            self.state.sea_state = max(0.0, min(12.0, sea_state))
        if wind_speed_kts is not None:
            self.state.sea_state = wind_to_beaufort(wind_speed_kts)
        self._tick()

    def update_from_dict(self, data: Dict[str, Any]):
        """Bulk update from a dictionary."""
        if "latitude" in data and "longitude" in data:
            self.update_position(data["latitude"], data["longitude"],
                                 data.get("fix_quality", 1))
        if "heading" in data:
            self.update_heading(data["heading"])
        if "speed_over_ground" in data:
            self.update_speed(sog=data["speed_over_ground"])
        if "depth" in data:
            self.update_depth(depth_fathoms=data["depth"])
        elif "depth_meters" in data:
            self.update_depth(depth_meters=data["depth_meters"])
        if "engine_rpm" in data:
            self.update_engine(rpm=data["engine_rpm"])
        if "water_temperature" in data:
            self.update_environment(water_temp=data["water_temperature"])
        if "sea_state" in data:
            self.update_environment(sea_state=data["sea_state"])

    def _tick(self):
        """Called after any update — recompute derived state."""
        self.state.timestamp = time.time()
        self._detect_mode()
        self._archive()

    def _detect_mode(self):
        """Heuristic mode detection from current telemetry.

        Rules (checked in priority order):
        - ANCHORED: speed < 0.5 kts, very shallow or no engine
        - FISHING: speed < 2 kts AND depth > 5 fm AND depth changing
        - TRANSIT: speed > 4 kts
        - DEPARTING: speed 0.5-4, heading away from shallow
        - RETURNING: speed 0.5-4, heading toward shallow
        - DOCKED: no movement, no depth or very shallow
        """
        s = self.state
        sog = s.speed_over_ground or 0.0
        rpm = s.engine_rpm or 0.0
        depth = s.depth or 0.0

        # Track depth changes for fishing detection
        depth_changing = False
        if s._prev_depth is not None and s.depth is not None:
            depth_changing = abs(s.depth - s._prev_depth) > 0.5

        # Update previous depth
        if s.depth is not None:
            s._prev_depth = s.depth

        # Mode detection
        if sog < 0.5 and rpm < 100:
            if depth < 5 or s.depth is None:
                s.mode = VesselMode.DOCKED
            else:
                s.mode = VesselMode.ANCHORED
        elif sog < 2.0 and depth > 5.0 and (depth_changing or rpm < 1000):
            s.mode = VesselMode.FISHING
        elif sog > 4.0:
            if depth > 20:
                s.mode = VesselMode.TRANSIT
            else:
                s.mode = VesselMode.DEPARTING
        elif 0.5 <= sog <= 4.0:
            if depth < 10:
                s.mode = VesselMode.RETURNING
            elif rpm < 1000:
                s.mode = VesselMode.FISHING
            else:
                s.mode = VesselMode.TRANSIT
        else:
            # Speed between 2 and 4 with deeper water
            if rpm < 800:
                s.mode = VesselMode.FISHING
            else:
                s.mode = VesselMode.TRANSIT

    def _archive(self):
        """Keep rolling history."""
        import copy
        self.history.append(copy.copy(self.state))

    def add_listener(self, callback: callable):
        """Register a callback called on each state update."""
        self._listeners.append(callback)

    def _notify(self):
        for cb in self._listeners:
            try:
                cb(self.state)
            except Exception:
                pass

    def musical_parameters(self) -> MusicalParameters:
        """Convert current vessel state to musical parameters.

        Mirrors the acoustic-probe's VesselInstrument mapping so the
        NMEA bridge produces the same musical language.
        """
        s = self.state
        rpm = s.engine_rpm or 0.0
        depth = s.depth or 0.0
        heading = s.heading or 0.0
        speed = s.speed_over_ground or 0.0
        sea = s.sea_state

        bass_note = rpm_to_bass_midi(rpm)
        harmony, label = depth_to_harmony(depth)
        rhythm_density = SEA_STATE_DENSITY.get(int(sea), 0.25)

        # Build harmony notes relative to bass note
        harmony_notes = [bass_note + h for h in harmony]

        params = MusicalParameters(
            bass_note=bass_note,
            bass_frequency=rpm_to_bass_freq(rpm),
            bass_velocity=int(40 + (rpm / 2800.0) * 60),
            harmony_notes=harmony_notes,
            harmony_label=label,
            rhythm_density=rhythm_density,
            pan=heading_to_pan(heading),
            tempo_bpm=speed_to_tempo(speed),
            mood=self._compute_mood(),
            intensity=self._compute_intensity(),
        )
        return params

    def _compute_mood(self) -> str:
        s = self.state
        if s.mode == VesselMode.EMERGENCY:
            return "urgent"
        if s.sea_state >= 7:
            return "turbulent"
        if s.mode == VesselMode.FISHING and (s.depth or 0) > 50:
            return "contemplative"
        if s.mode == VesselMode.FISHING:
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
        """Overall energy 0-1 from engine load + speed + sea state."""
        s = self.state
        load = s.engine_load
        speed_norm = min(1.0, (s.speed_over_ground or 0.0) / 15.0)
        sea_norm = min(1.0, s.sea_state / 9.0)
        return round((load * 0.4 + speed_norm * 0.3 + sea_norm * 0.3), 3)

    def context_for_agents(self) -> Dict[str, Any]:
        """Produce a context dict for the conductor/agent fleet.

        This is what agents see to know what the boat is doing.
        """
        s = self.state
        return {
            "vessel": self.name,
            "mode": s.mode.value,
            "is_moving": s.is_moving,
            "is_fishing": s.is_fishing,
            "position": {
                "lat": s.latitude,
                "lon": s.longitude,
                "valid": s.position_valid,
            } if s.position_valid else None,
            "heading": s.heading,
            "speed_sog": s.speed_over_ground,
            "speed_stw": s.speed_through_water,
            "depth_fathoms": s.depth,
            "depth_meters": s.depth_meters,
            "water_temp_c": s.water_temperature,
            "sea_state_beaufort": s.sea_state,
            "engine_rpm": s.engine_rpm,
            "engine_load": round(s.engine_load, 2),
            "tank_level_pct": s.tank_level,
            "musical": self.musical_parameters().to_dict(),
            "timestamp": s.timestamp,
        }
