"""
SWMIDI-8 — the slackwater-rust wire format. 8 bytes, little-endian:

    [0] status      = (event-nibble << 4) | channel   (channel 0–15)
    [1] pitch       = event type, 0–127
    [2] velocity    = weight, 0–127
    [3] error_mask  = 8 friction bits
    [4:8] tick      = uint32 LE @ 96 PPQ

peer-consult emits three events per consultation: cast=1, consult=2,
verdict=3 on the primary model's atlas channel.

Status-nibble convention: we follow the slackwater EventType enum
(flux-core/src/swmidi.rs), where NoteOn = 0 and nibbles 5–15 are invalid,
NOT classic MIDI (where Note-On = 0x9).
"""

from __future__ import annotations

import struct

# Event types (carried in the pitch byte).
EVENT_CAST = 1
EVENT_CONSULT = 2
EVENT_VERDICT = 3

# Status nibbles — slackwater EventType (flux-core/src/swmidi.rs):
# NoteOn = 0, not classic MIDI's 0x9.
STATUS_NOTE_ON = 0x0

# Friction bits in the error_mask byte — per slackwater
# flux-core/src/error_mask.rs: SEMANTIC is bit 2 (0b0000_0100);
# 0b0010_0000 is TOPOLOGY there.
FRICTION_SEMANTIC = 0b0000_0100  # set when the zone is CHAOTIC

# Clock.
PPQ = 96

EVENT_SIZE = 8

_STRUCT = struct.Struct("<BBBBI")


def encode_event(status_type: int, channel: int, pitch: int, velocity: int, error_mask: int, tick: int) -> bytes:
    """
    Encode one SWMIDI-8 event (8 bytes little-endian).

    status byte = (status_type << 4) | (channel & 0x0F). pitch, velocity and
    error_mask are single bytes; tick is a uint32 at 96 PPQ.
    """
    if not 0 <= status_type <= 0x0F:
        raise ValueError(f"status_type must fit a nibble, got {status_type}")
    if not 0 <= channel <= 0x0F:
        raise ValueError(f"channel must be 0–15, got {channel}")
    for label, value in (("pitch", pitch), ("velocity", velocity)):
        if not 0 <= value <= 127:
            raise ValueError(f"{label} must be 0–127, got {value}")
    if not 0 <= error_mask <= 0xFF:
        raise ValueError(f"error_mask must fit a byte, got {error_mask}")
    if not 0 <= tick <= 0xFFFFFFFF:
        raise ValueError(f"tick must fit a uint32, got {tick}")
    status = (status_type << 4) | (channel & 0x0F)
    return _STRUCT.pack(status, pitch, velocity, error_mask, tick)


def decode_event(data: bytes) -> dict:
    """
    Decode one SWMIDI-8 event.

    Returns {'status_type', 'status', 'channel', 'pitch', 'velocity',
    'error_mask', 'tick'}.
    """
    if len(data) != EVENT_SIZE:
        raise ValueError(f"SWMIDI-8 events are exactly {EVENT_SIZE} bytes, got {len(data)}")
    status, pitch, velocity, error_mask, tick = _STRUCT.unpack(data)
    return {
        "status_type": (status >> 4) & 0x0F,
        "status": status,
        "channel": status & 0x0F,
        "pitch": pitch,
        "velocity": velocity,
        "error_mask": error_mask,
        "tick": tick,
    }


def profile_channel(profile) -> int:
    """
    SWMIDI channel for a casting-call ModelProfile.

    Models not on the pipeline bus (channel is None) transmit on channel 0.
    """
    channel = getattr(profile, "channel", None)
    if channel is None:
        return 0
    return int(channel) & 0x0F
