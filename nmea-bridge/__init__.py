"""
NMEA→SWMIDI Bridge — The thing that makes the boat a robot.

Connects real NMEA 0183 vessel instruments to the SWMIDI-8 wire format,
the sonic shape engine, the conductor, and the agent fleet.

Modules:
    nmea_parser    — Parses standard NMEA 0183 sentences
    swmidi_encoder — Encodes vessel state as SWMIDI-8 events
    vessel_state   — Maintains current vessel state, computes derived modes
    bridge         — Main bridge process (NMEA in → SWMIDI out)
    simulator      — Simulates a full fishing trip for testing
"""

from nmea_parser import NMEAParser, ParseResult, SentenceType, parse_sentence
from swmidi_encoder import (
    SWMIDIEncoder, SWMIDIEvent, EventType, ErrorMask,
    map_depth_to_pitch, map_heading_to_pitch, map_speed_to_pitch,
    map_rpm_to_pitch, map_temp_to_pitch, map_sea_state_to_pitch,
    fix_quality_to_velocity, compute_error_mask,
)
from vessel_state import (
    VesselState, VesselMode, VesselStateManager, MusicalParameters,
)
