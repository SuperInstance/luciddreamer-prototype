"""
swmidi_encoder.py — Encodes vessel state as SWMIDI-8 events.

SWMIDI-8 is the Slackwater wire format: every observation becomes an 8-byte
event on a shared 96 PPQ beat clock. Each byte carries meaning:

    Byte 0: Status    — event type (GPS, DEPTH, HEADING, ENGINE, etc.)
    Byte 1: Pitch     — normalized value (0-255)
    Byte 2: Velocity  — confidence / quality / freshness (0-255)
    Byte 3: ErrorMask — 8-bit friction bitfield (0x00 = flow)
    Byte 4: Tick      — beat clock position (96 PPQ, wraps at 255)
    Byte 5: Reserved  — future use / sub-type
    Byte 6: Data MSB  — high byte of 16-bit extended data
    Byte 7: Data LSB  — low byte of 16-bit extended data

The ErrorMask bitfield mirrors slackwater-rust:
    bit 0: SPATIAL     — position disagreement
    bit 1: TEMPORAL    — timing jitter / stale data
    bit 2: SEMANTIC    — interpretation conflict
    bit 3: SAFETY      — safety-critical condition
    bit 4: RESOURCE    — low resource (fuel, battery)
    bit 5: TOPOLOGY    — network / connectivity issue
    bit 6: AUTHORITY   — operator override / mode conflict
    bit 7: CONSISTENCY — self-consistency check failed

Usage:
    encoder = SWMIDIEncoder()
    events = encoder.encode_vessel_state(vessel_state)
    for event in events:
        print(event.to_bytes())
"""

from __future__ import annotations

import time
import struct
from dataclasses import dataclass, field
from enum import IntEnum, IntFlag
from typing import Optional, List, Tuple


# ─── Event Types (Status byte) ──────────────────────────────────────────────

class EventType(IntEnum):
    """SWMIDI event types for vessel telemetry."""
    GPS_POSITION = 0x01
    GPS_FIX_QUALITY = 0x02
    DEPTH = 0x03
    HEADING = 0x04
    SPEED = 0x05
    ENGINE = 0x06
    WATER_TEMP = 0x07
    SEA_STATE = 0x08
    TANK_LEVEL = 0x09
    BATTERY = 0x0A
    VESSEL_MODE = 0x0B
    COURSE = 0x0C
    ENVIRONMENT = 0x0D
    SYSTEM = 0x0F
    # Reserved for agent/conversation events (mirrors tensor-midi)
    AGENT_MESSAGE = 0x10
    AGENT_CONFIDENCE = 0x11
    FLOW_STATE = 0x12


# ─── Error Mask (mirrors slackwater-rust error_mask.rs) ─────────────────────

class ErrorMask(IntFlag):
    """8-bit friction bitfield. 0x00 = pure flow (no friction)."""
    NONE = 0x00
    SPATIAL = 1 << 0       # Position disagreement
    TEMPORAL = 1 << 1      # Timing jitter / stale data
    SEMANTIC = 1 << 2      # Interpretation conflict
    SAFETY = 1 << 3        # Safety-critical condition
    RESOURCE = 1 << 4      # Low resource (fuel, battery)
    TOPOLOGY = 1 << 5      # Network / connectivity issue
    AUTHORITY = 1 << 6     # Operator override / mode conflict
    CONSISTENCY = 1 << 7   # Self-consistency check failed


# ─── PPQ Constants ──────────────────────────────────────────────────────────

PPQ = 96  # Pulses per quarter note (standard MIDI)


# ─── SWMIDI Event ───────────────────────────────────────────────────────────

@dataclass
class SWMIDIEvent:
    """A single 8-byte SWMIDI-8 event.

    The wire format for everything the vessel perceives and everything the
    agent fleet discusses. One clock, one format, one truth.
    """
    status: int       # EventType value
    pitch: int        # Normalized value (0-255)
    velocity: int     # Confidence / quality (0-255)
    error_mask: int   # ErrorMask bitfield (0-255)
    tick: int         # Beat clock position (0-255, wraps)
    reserved: int = 0 # Future use / sub-type
    data_msb: int = 0 # High byte of extended data
    data_lsb: int = 0 # Low byte of extended data

    def __post_init__(self):
        # Clamp all values to valid ranges
        self.status = max(0, min(255, int(self.status)))
        self.pitch = max(0, min(255, int(self.pitch)))
        self.velocity = max(0, min(255, int(self.velocity)))
        self.error_mask = max(0, min(255, int(self.error_mask)))
        self.tick = max(0, min(255, int(self.tick) % 256))
        self.reserved = max(0, min(255, int(self.reserved)))
        self.data_msb = max(0, min(255, int(self.data_msb)))
        self.data_lsb = max(0, min(255, int(self.data_lsb)))

    def to_bytes(self) -> bytes:
        """Serialize to 8 bytes."""
        return struct.pack(
            'BBBBBBBB',
            self.status, self.pitch, self.velocity, self.error_mask,
            self.tick, self.reserved, self.data_msb, self.data_lsb
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> 'SWMIDIEvent':
        """Deserialize from 8 bytes."""
        if len(data) < 8:
            raise ValueError(f"Need 8 bytes, got {len(data)}")
        status, pitch, velocity, error_mask, tick, reserved, d_msb, d_lsb = \
            struct.unpack('BBBBBBBB', data[:8])
        return cls(status, pitch, velocity, error_mask, tick, reserved, d_msb, d_lsb)

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "status_name": self._status_name(),
            "pitch": self.pitch,
            "velocity": self.velocity,
            "error_mask": self.error_mask,
            "error_flags": self._error_flags(),
            "tick": self.tick,
            "reserved": self.reserved,
            "data_16": (self.data_msb << 8) | self.data_lsb,
        }

    def _status_name(self) -> str:
        try:
            return EventType(self.status).name
        except ValueError:
            return f"UNKNOWN_0x{self.status:02X}"

    def _error_flags(self) -> list:
        flags = []
        for flag in ErrorMask:
            if flag == ErrorMask.NONE:
                continue
            if self.error_mask & flag:
                flags.append(flag.name)
        return flags

    def __repr__(self) -> str:
        return (
            f"SWMIDIEvent({self._status_name()}, "
            f"pitch={self.pitch}, vel={self.velocity}, "
            f"errors={self._error_flags() or 'FLOW'}, "
            f"tick={self.tick})"
        )


# ─── Value Mapping Helpers ──────────────────────────────────────────────────

def map_depth_to_pitch(depth_fathoms: float) -> int:
    """Map depth (0-200 fathoms) to pitch byte (0-255).

    0 fm → 0, 200 fm → 255. Linear with clamping.
    """
    return max(0, min(255, int(round(depth_fathoms / 200.0 * 255))))


def map_heading_to_pitch(heading_degrees: float) -> int:
    """Map heading (0-360°) to pitch byte (0-255).

    0° → 0, 360° → 255. ~1.41° per increment.
    """
    return max(0, min(255, int(round(heading_degrees / 360.0 * 255))))


def map_speed_to_pitch(speed_knots: float) -> int:
    """Map speed (0-25 kts) to pitch byte (0-255).

    0 kts → 0, 25 kts → 255. 0.1 kt resolution.
    """
    return max(0, min(255, int(round(speed_knots / 25.0 * 255))))


def map_rpm_to_pitch(rpm: float) -> int:
    """Map engine RPM (0-3000) to pitch byte (0-255)."""
    return max(0, min(255, int(round(rpm / 3000.0 * 255))))


def map_temp_to_pitch(temp_celsius: float) -> int:
    """Map water temperature (-5°C to 35°C) to pitch byte (0-255)."""
    clamped = max(-5.0, min(35.0, temp_celsius))
    return max(0, min(255, int(round((clamped + 5.0) / 40.0 * 255))))


def map_sea_state_to_pitch(sea_state: float) -> int:
    """Map Beaufort sea state (0-12) to pitch byte (0-255)."""
    return max(0, min(255, int(round(sea_state / 12.0 * 255))))


def map_latitude_to_data(lat: float) -> Tuple[int, int]:
    """Map latitude (-90 to 90) to 16-bit data (MSB, LSB).

    Uses offset binary: -90 → 0, +90 → 65535.
    """
    clamped = max(-90.0, min(90.0, lat))
    raw = int(round((clamped + 90.0) / 180.0 * 65535))
    return (raw >> 8) & 0xFF, raw & 0xFF


def map_longitude_to_data(lon: float) -> Tuple[int, int]:
    """Map longitude (-180 to 180) to 16-bit data (MSB, LSB).

    Uses offset binary: -180 → 0, +180 → 65535.
    """
    clamped = max(-180.0, min(180.0, lon))
    raw = int(round((clamped + 180.0) / 360.0 * 65535))
    return (raw >> 8) & 0xFF, raw & 0xFF


def fix_quality_to_velocity(fix_quality: int) -> int:
    """Map GPS fix quality to velocity (confidence) byte.

    0=invalid→0, 1=GPS→128, 2=DGPS→192, 3=PPS→224,
    4=RTK→240, 6=estimated→64, 8=sim→96
    """
    mapping = {0: 0, 1: 128, 2: 192, 3: 224, 4: 240, 5: 232,
               6: 64, 7: 160, 8: 96}
    return mapping.get(fix_quality, 0)


def compute_error_mask(
    stale: bool = False,
    low_resource: bool = False,
    safety: bool = False,
    inconsistent: bool = False,
    spatial_disagree: bool = False,
    topology_issue: bool = False,
    authority_override: bool = False,
    semantic_conflict: bool = False,
) -> int:
    """Compute error mask byte from boolean conditions."""
    mask = ErrorMask.NONE
    if spatial_disagree:
        mask |= ErrorMask.SPATIAL
    if stale:
        mask |= ErrorMask.TEMPORAL
    if semantic_conflict:
        mask |= ErrorMask.SEMANTIC
    if safety:
        mask |= ErrorMask.SAFETY
    if low_resource:
        mask |= ErrorMask.RESOURCE
    if topology_issue:
        mask |= ErrorMask.TOPOLOGY
    if authority_override:
        mask |= ErrorMask.AUTHORITY
    if inconsistent:
        mask |= ErrorMask.CONSISTENCY
    return int(mask)


# ─── SWMIDI Encoder ─────────────────────────────────────────────────────────

class SWMIDIEncoder:
    """Encodes vessel state as a stream of SWMIDI-8 events.

    Each call to encode_vessel_state() produces a list of events
    representing the current vessel state, suitable for broadcast
    to the sonic shape engine, the conductor, and the knowledge base.
    """

    def __init__(self, start_tick: int = 0):
        self._tick = start_tick % 256

    def advance_tick(self, pulses: int = 1) -> int:
        """Advance the beat clock."""
        self._tick = (self._tick + pulses) % 256
        return self._tick

    @property
    def current_tick(self) -> int:
        return self._tick

    def encode_vessel_state(self, state, error_mask: int = 0) -> List[SWMIDIEvent]:
        """Encode a VesselState into a list of SWMIDI events.

        Args:
            state: vessel_state.VesselState instance
            error_mask: Optional global error mask applied to all events

        Returns:
            List of SWMIDIEvent, one per reading.
        """
        events = []
        tick = self._tick

        # GPS position
        if state.latitude is not None and state.longitude is not None:
            lat_msb, lat_lsb = map_latitude_to_data(state.latitude)
            # Encode longitude in reserved+data for position events
            lon_msb, lon_lsb = map_longitude_to_data(state.longitude)
            events.append(SWMIDIEvent(
                status=EventType.GPS_POSITION,
                pitch=lat_msb,           # Latitude high byte
                velocity=fix_quality_to_velocity(state.fix_quality),
                error_mask=error_mask,
                tick=tick,
                reserved=lat_lsb,        # Latitude low byte
                data_msb=lon_msb,        # Longitude high byte
                data_lsb=lon_lsb,        # Longitude low byte
            ))

        # Depth
        if state.depth is not None:
            err = error_mask
            if state.depth < 1.0:
                err |= ErrorMask.SAFETY  # Very shallow — safety flag
            events.append(SWMIDIEvent(
                status=EventType.DEPTH,
                pitch=map_depth_to_pitch(state.depth),
                velocity=255,  # Sensor present and healthy
                error_mask=err,
                tick=tick,
            ))

        # Heading
        if state.heading is not None:
            events.append(SWMIDIEvent(
                status=EventType.HEADING,
                pitch=map_heading_to_pitch(state.heading),
                velocity=255,
                error_mask=error_mask,
                tick=tick,
            ))

        # Speed
        if state.speed_over_ground is not None:
            events.append(SWMIDIEvent(
                status=EventType.SPEED,
                pitch=map_speed_to_pitch(state.speed_over_ground),
                velocity=255,
                error_mask=error_mask,
                tick=tick,
            ))

        # Engine RPM
        if state.engine_rpm is not None:
            err = error_mask
            if state.engine_rpm > 2600:
                err |= ErrorMask.SAFETY  # High RPM
            events.append(SWMIDIEvent(
                status=EventType.ENGINE,
                pitch=map_rpm_to_pitch(state.engine_rpm),
                velocity=255,
                error_mask=err,
                tick=tick,
            ))

        # Water temperature
        if state.water_temperature is not None:
            events.append(SWMIDIEvent(
                status=EventType.WATER_TEMP,
                pitch=map_temp_to_pitch(state.water_temperature),
                velocity=255,
                error_mask=error_mask,
                tick=tick,
            ))

        # Sea state
        if state.sea_state > 0:
            err = error_mask
            if state.sea_state >= 7:
                err |= ErrorMask.SAFETY
            events.append(SWMIDIEvent(
                status=EventType.SEA_STATE,
                pitch=map_sea_state_to_pitch(state.sea_state),
                velocity=255,
                error_mask=err,
                tick=tick,
            ))

        # Tank level
        if state.tank_level is not None:
            err = error_mask
            if state.tank_level < 25:
                err |= ErrorMask.RESOURCE
            events.append(SWMIDIEvent(
                status=EventType.TANK_LEVEL,
                pitch=max(0, min(255, int(round(state.tank_level / 100.0 * 255)))),
                velocity=255,
                error_mask=err,
                tick=tick,
            ))

        # Battery voltage
        if state.battery_voltage is not None:
            err = error_mask
            if state.battery_voltage < 11.5:
                err |= ErrorMask.RESOURCE
            events.append(SWMIDIEvent(
                status=EventType.BATTERY,
                pitch=max(0, min(255, int(round(state.battery_voltage / 16.0 * 255)))),
                velocity=255,
                error_mask=err,
                tick=tick,
            ))

        # Vessel mode
        events.append(SWMIDIEvent(
            status=EventType.VESSEL_MODE,
            pitch=self._mode_to_pitch(state.mode),
            velocity=255,
            error_mask=error_mask,
            tick=tick,
        ))

        return events

    @staticmethod
    def _mode_to_pitch(mode) -> int:
        """Map vessel mode to a pitch byte."""
        from vessel_state import VesselMode
        mapping = {
            VesselMode.UNKNOWN: 0,
            VesselMode.DOCKED: 16,
            VesselMode.DEPARTING: 48,
            VesselMode.TRANSIT: 80,
            VesselMode.FISHING: 128,
            VesselMode.HAULING: 160,
            VesselMode.RETURNING: 192,
            VesselMode.ANCHORED: 224,
            VesselMode.EMERGENCY: 255,
        }
        return mapping.get(mode, 0)

    def encode_raw(self, status: int, pitch: int, velocity: int = 255,
                   error_mask: int = 0, data_16: int = 0) -> SWMIDIEvent:
        """Encode a raw event with explicit values."""
        event = SWMIDIEvent(
            status=status,
            pitch=pitch,
            velocity=velocity,
            error_mask=error_mask,
            tick=self._tick,
            data_msb=(data_16 >> 8) & 0xFF,
            data_lsb=data_16 & 0xFF,
        )
        return event
