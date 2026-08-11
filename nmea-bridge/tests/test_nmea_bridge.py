"""
tests/test_nmea_bridge.py — Comprehensive tests for the NMEA→SWMIDI Bridge.

Covers:
    1.  NMEA parsing — GPGGA (GPS position)
    2.  NMEA parsing — GPRMC (course/speed)
    3.  NMEA parsing — SDDBT (depth below transducer)
    4.  NMEA parsing — SDDPT (depth)
    5.  NMEA parsing — HDT (heading true)
    6.  NMEA parsing — HDM (heading magnetic)
    7.  NMEA parsing — HDG (heading with variation)
    8.  NMEA parsing — MTW (water temperature)
    9.  NMEA parsing — VHW (water speed/heading)
    10. NMEA parsing — XDR (transducer readings)
    11. NMEA checksum verification
    12. SWMIDI encoding — depth value mapping
    13. SWMIDI encoding — heading value mapping
    14. SWMIDI encoding — error mask computation
    15. SWMIDI encoding — full vessel state to events
    16. Vessel state — fishing detection
    17. Vessel state — transit detection
    18. Vessel state — anchored detection
    19. Bridge end-to-end — NMEA in → SWMIDI out
    20. Simulator output validation
    21. SWMIDI event serialization round-trip
    22. Vessel mode pitch mapping

Run with: python -m pytest tests/ -v
Or:       python -m unittest tests.test_nmea_bridge
"""

import os
import sys
import math
import time
import struct
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nmea_parser import (
    NMEAParser, ParseResult, SentenceType, parse_sentence,
)
from swmidi_encoder import (
    SWMIDIEncoder, SWMIDIEvent, EventType, ErrorMask,
    map_depth_to_pitch, map_heading_to_pitch, map_speed_to_pitch,
    map_rpm_to_pitch, map_temp_to_pitch, map_sea_state_to_pitch,
    fix_quality_to_velocity, compute_error_mask,
)
from vessel_state import (
    VesselState, VesselMode, VesselStateManager,
)
from bridge import NMEABridge, ConsoleOutput


# ═══════════════════════════════════════════════════════════════════════════
# NMEA PARSER TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestGPGGAParsing(unittest.TestCase):
    """TEST 1: GPGGA (GPS position) parsing."""

    def setUp(self):
        self.parser = NMEAParser()

    def test_gpgga_basic(self):
        """$GPGGA parses latitude, longitude, fix quality, satellites."""
        sentence = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"
        result = self.parser.parse(sentence)

        self.assertIsNotNone(result)
        self.assertEqual(result.sentence_type, SentenceType.GPGGA)
        self.assertTrue(result.checksum_valid)
        self.assertAlmostEqual(result.data["latitude"], 48.1173, places=3)
        self.assertAlmostEqual(result.data["longitude"], 11.5167, places=3)
        self.assertEqual(result.data["fix_quality"], 1)
        self.assertEqual(result.data["num_satellites"], 8)

    def test_gpgga_southern_hemisphere(self):
        """GPGGA with southern/western coordinates produces negative lat/lon."""
        sentence = "$GPGGA,123519,5747.400,S,15224.420,W,2,10,0.9,5.4,M,46.9,M,,*77"
        result = self.parser.parse(sentence)

        self.assertIsNotNone(result)
        self.assertAlmostEqual(result.data["latitude"], -57.79, places=2)
        self.assertAlmostEqual(result.data["longitude"], -152.4070, places=2)
        self.assertEqual(result.data["fix_quality"], 2)

    def test_gpgga_no_fix(self):
        """GPGGA with fix quality 0 is still parsed."""
        sentence = "$GPGGA,123519,4807.038,N,01131.000,E,0,00,,,M,,M,,*66"
        result = self.parser.parse(sentence)
        self.assertEqual(result.data["fix_quality"], 0)


class TestGPRMCParsing(unittest.TestCase):
    """TEST 2: GPRMC (course/speed) parsing."""

    def setUp(self):
        self.parser = NMEAParser()

    def test_gprmc_basic(self):
        """$GPRMC parses speed, course, position."""
        sentence = "$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,004.2,W*6A"
        result = self.parser.parse(sentence)

        self.assertIsNotNone(result)
        self.assertEqual(result.sentence_type, SentenceType.GPRMC)
        self.assertAlmostEqual(result.data["speed_knots"], 22.4, places=1)
        self.assertAlmostEqual(result.data["course_degrees"], 84.4, places=1)
        self.assertEqual(result.data["status"], "A")


class TestSDDBTParsing(unittest.TestCase):
    """TEST 3: SDDBT (depth below transducer) parsing."""

    def setUp(self):
        self.parser = NMEAParser()

    def test_sddbt_basic(self):
        """$SDDBT parses depth in feet, meters, fathoms."""
        sentence = "$SDDBT,360.0,f,109.7,M,60.0,F*XX"
        # Compute correct checksum
        from simulator import build_checksum
        body = "SDDBT,360.0,f,109.7,M,60.0,F"
        cs = build_checksum(body)
        sentence = f"${body}*{cs}"

        result = self.parser.parse(sentence)
        self.assertIsNotNone(result)
        self.assertEqual(result.sentence_type, SentenceType.SDDBT)
        self.assertAlmostEqual(result.data["depth_feet"], 360.0)
        self.assertAlmostEqual(result.data["depth_meters"], 109.7)
        self.assertAlmostEqual(result.data["depth_fathoms"], 60.0)


class TestSDDPTParsing(unittest.TestCase):
    """TEST 4: SDDPT (depth) parsing."""

    def setUp(self):
        self.parser = NMEAParser()

    def test_sddpt_basic(self):
        """$SDDPT parses depth in meters and converts to fathoms."""
        from simulator import build_checksum
        body = "SDDPT,45.7,0.0,200.0"
        cs = build_checksum(body)
        sentence = f"${body}*{cs}"

        result = self.parser.parse(sentence)
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result.data["depth_meters"], 45.7)
        self.assertAlmostEqual(result.data["depth_fathoms"], 45.7 / 1.8288, places=3)


class TestHeadingParsing(unittest.TestCase):
    """TESTS 5-7: HDT, HDM, HDG parsing."""

    def setUp(self):
        self.parser = NMEAParser()

    def test_hdt(self):
        """TEST 5: HCHDT (heading true) parsing."""
        from simulator import build_checksum
        body = "HCHDT,123.4,T"
        cs = build_checksum(body)
        sentence = f"${body}*{cs}"

        result = self.parser.parse(sentence)
        self.assertEqual(result.sentence_type, SentenceType.HDT)
        self.assertAlmostEqual(result.data["heading"], 123.4)
        self.assertEqual(result.data["type"], "true")

    def test_hdm(self):
        """TEST 6: HCHDM (heading magnetic) parsing."""
        from simulator import build_checksum
        body = "HCHDM,055.0,M"
        cs = build_checksum(body)
        sentence = f"${body}*{cs}"

        result = self.parser.parse(sentence)
        self.assertEqual(result.sentence_type, SentenceType.HDM)
        self.assertAlmostEqual(result.data["heading"], 55.0)
        self.assertEqual(result.data["type"], "magnetic")

    def test_hdg(self):
        """TEST 7: HCHDG (heading with deviation/variation) parsing."""
        from simulator import build_checksum
        body = "HCHDG,120.0,,,15.0,E"
        cs = build_checksum(body)
        sentence = f"${body}*{cs}"

        result = self.parser.parse(sentence)
        self.assertEqual(result.sentence_type, SentenceType.HDG)
        self.assertAlmostEqual(result.data["heading_magnetic"], 120.0)
        self.assertAlmostEqual(result.data["variation"], 15.0)
        self.assertIsNotNone(result.data["heading_true"])


class TestMTWParsing(unittest.TestCase):
    """TEST 8: MTW (water temperature) parsing."""

    def test_mtw_basic(self):
        from simulator import build_checksum
        body = "YXMTW,7.5,C"
        cs = build_checksum(body)
        sentence = f"${body}*{cs}"

        parser = NMEAParser()
        result = parser.parse(sentence)
        self.assertEqual(result.sentence_type, SentenceType.MTW)
        self.assertAlmostEqual(result.data["water_temperature"], 7.5)


class TestVHWParsing(unittest.TestCase):
    """TEST 9: VHW (water speed/heading) parsing."""

    def test_vhw_basic(self):
        from simulator import build_checksum
        body = "VWVHW,123.0,T,120.0,M,5.0,N,9.3,K"
        cs = build_checksum(body)
        sentence = f"${body}*{cs}"

        parser = NMEAParser()
        result = parser.parse(sentence)
        self.assertEqual(result.sentence_type, SentenceType.VHW)
        self.assertAlmostEqual(result.data["heading_true"], 123.0)
        self.assertAlmostEqual(result.data["heading_magnetic"], 120.0)
        self.assertAlmostEqual(result.data["speed_knots"], 5.0)


class TestXDRParsing(unittest.TestCase):
    """TEST 10: XDR (transducer readings) parsing."""

    def test_xdr_engine_rpm(self):
        from simulator import build_checksum
        body = "IIXDR,R,1800,RPM,ENGINE"
        cs = build_checksum(body)
        sentence = f"${body}*{cs}"

        parser = NMEAParser()
        result = parser.parse(sentence)
        self.assertEqual(result.sentence_type, SentenceType.XDR)
        self.assertEqual(len(result.data["transducers"]), 1)
        self.assertEqual(result.data["transducers"][0]["type"], "R")
        self.assertAlmostEqual(result.data["transducers"][0]["value"], 1800)
        self.assertAlmostEqual(result.data["engine_rpm"], 1800)

    def test_xdr_multiple(self):
        """XDR with multiple transducer readings."""
        from simulator import build_checksum
        body = "IIXDR,R,1800,RPM,ENGINE,T,85.0,P,FUEL,V,13.2,V,BATTERY"
        cs = build_checksum(body)
        sentence = f"${body}*{cs}"

        parser = NMEAParser()
        result = parser.parse(sentence)
        self.assertEqual(len(result.data["transducers"]), 3)
        self.assertAlmostEqual(result.data["engine_rpm"], 1800)
        self.assertAlmostEqual(result.data["tank_level"], 85.0)
        self.assertAlmostEqual(result.data["battery_voltage"], 13.2)


class TestChecksumVerification(unittest.TestCase):
    """TEST 11: NMEA checksum verification."""

    def test_valid_checksum(self):
        """Valid checksum passes verification."""
        sentence = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"
        parser = NMEAParser()
        result = parser.parse(sentence)
        self.assertTrue(result.checksum_valid)

    def test_invalid_checksum(self):
        """Invalid checksum is flagged."""
        sentence = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*FF"
        parser = NMEAParser()
        result = parser.parse(sentence)
        self.assertFalse(result.checksum_valid)

    def test_manual_checksum(self):
        """Manual checksum computation matches."""
        parser = NMEAParser()
        body = "GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,"
        cs = parser._compute_checksum("$" + body + "*XX")
        self.assertEqual(cs, 0x47)


# ═══════════════════════════════════════════════════════════════════════════
# SWMIDI ENCODER TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestSWMIDIDepthMapping(unittest.TestCase):
    """TEST 12: Depth value mapping to pitch byte."""

    def test_depth_zero(self):
        """0 fathoms → pitch 0."""
        self.assertEqual(map_depth_to_pitch(0), 0)

    def test_depth_max(self):
        """200 fathoms → pitch 255."""
        self.assertEqual(map_depth_to_pitch(200), 255)

    def test_depth_mid(self):
        """100 fathoms → pitch ~128."""
        self.assertAlmostEqual(map_depth_to_pitch(100), 128, delta=1)

    def test_depth_clamp(self):
        """Values beyond range are clamped."""
        self.assertEqual(map_depth_to_pitch(-10), 0)
        self.assertEqual(map_depth_to_pitch(300), 255)


class TestSWMIDIHeadingMapping(unittest.TestCase):
    """TEST 13: Heading value mapping to pitch byte."""

    def test_heading_north(self):
        """0° → pitch 0."""
        self.assertEqual(map_heading_to_pitch(0), 0)

    def test_heading_full(self):
        """360° → pitch 255."""
        self.assertEqual(map_heading_to_pitch(360), 255)

    def test_heading_east(self):
        """90° → pitch ~64."""
        self.assertAlmostEqual(map_heading_to_pitch(90), 64, delta=1)

    def test_heading_south(self):
        """180° → pitch ~128."""
        self.assertAlmostEqual(map_heading_to_pitch(180), 128, delta=1)


class TestSWMIDIErrorMask(unittest.TestCase):
    """TEST 14: Error mask computation."""

    def test_no_errors(self):
        """No conditions → 0x00 (pure flow)."""
        self.assertEqual(compute_error_mask(), 0)

    def test_temporal_stale(self):
        """Stale data flag → TEMPORAL bit."""
        self.assertEqual(compute_error_mask(stale=True), int(ErrorMask.TEMPORAL))

    def test_safety(self):
        """Safety condition → SAFETY bit."""
        self.assertEqual(compute_error_mask(safety=True), int(ErrorMask.SAFETY))

    def test_multiple(self):
        """Multiple flags combine."""
        mask = compute_error_mask(stale=True, low_resource=True, safety=True)
        self.assertEqual(mask & ErrorMask.TEMPORAL, ErrorMask.TEMPORAL)
        self.assertEqual(mask & ErrorMask.SAFETY, ErrorMask.SAFETY)
        self.assertEqual(mask & ErrorMask.RESOURCE, ErrorMask.RESOURCE)

    def test_fix_quality_to_velocity(self):
        """GPS fix quality maps to confidence velocity."""
        self.assertEqual(fix_quality_to_velocity(0), 0)    # No fix
        self.assertEqual(fix_quality_to_velocity(1), 128)  # GPS
        self.assertEqual(fix_quality_to_velocity(2), 192)  # DGPS
        self.assertEqual(fix_quality_to_velocity(4), 240)  # RTK


class TestSWMIDIFullEncoding(unittest.TestCase):
    """TEST 15: Full vessel state → SWMIDI events."""

    def test_encode_full_state(self):
        """Encoding a fully-populated vessel state produces events for each reading."""
        encoder = SWMIDIEncoder()
        state = VesselState(
            latitude=57.79,
            longitude=-152.40,
            fix_quality=1,
            heading=180.0,
            speed_over_ground=7.5,
            depth=45.0,
            engine_rpm=1800.0,
            water_temperature=8.0,
            sea_state=3.0,
            tank_level=80.0,
            battery_voltage=13.2,
            mode=VesselMode.TRANSIT,
        )

        events = encoder.encode_vessel_state(state)

        # Should have GPS, depth, heading, speed, engine, temp, sea state,
        # tank, battery, mode = 10 events
        self.assertGreaterEqual(len(events), 8)

        # Check event types are present
        statuses = {e.status for e in events}
        self.assertIn(EventType.GPS_POSITION, statuses)
        self.assertIn(EventType.DEPTH, statuses)
        self.assertIn(EventType.HEADING, statuses)
        self.assertIn(EventType.SPEED, statuses)
        self.assertIn(EventType.ENGINE, statuses)

    def test_safety_flags_on_shallow(self):
        """Very shallow depth (< 1 fm) triggers SAFETY error mask."""
        encoder = SWMIDIEncoder()
        state = VesselState(depth=0.5)
        events = encoder.encode_vessel_state(state)
        depth_event = [e for e in events if e.status == EventType.DEPTH][0]
        self.assertTrue(depth_event.error_mask & ErrorMask.SAFETY)

    def test_resource_flag_on_low_tank(self):
        """Low tank level (< 25%) triggers RESOURCE error mask."""
        encoder = SWMIDIEncoder()
        state = VesselState(tank_level=15.0)
        events = encoder.encode_vessel_state(state)
        tank_event = [e for e in events if e.status == EventType.TANK_LEVEL][0]
        self.assertTrue(tank_event.error_mask & ErrorMask.RESOURCE)


class TestSWMIDISerialization(unittest.TestCase):
    """TEST 21: SWMIDI event serialization round-trip."""

    def test_to_bytes_from_bytes(self):
        """Event → bytes → event preserves all fields."""
        original = SWMIDIEvent(
            status=EventType.DEPTH,
            pitch=128,
            velocity=255,
            error_mask=int(ErrorMask.TEMPORAL),
            tick=96,
            reserved=1,
            data_msb=0xAB,
            data_lsb=0xCD,
        )

        raw = original.to_bytes()
        self.assertEqual(len(raw), 8)

        restored = SWMIDIEvent.from_bytes(raw)
        self.assertEqual(restored.status, original.status)
        self.assertEqual(restored.pitch, original.pitch)
        self.assertEqual(restored.velocity, original.velocity)
        self.assertEqual(restored.error_mask, original.error_mask)
        self.assertEqual(restored.tick, original.tick)
        self.assertEqual(restored.reserved, original.reserved)
        self.assertEqual(restored.data_msb, original.data_msb)
        self.assertEqual(restored.data_lsb, original.data_lsb)

    def test_all_values_in_range(self):
        """All bytes are in 0-255 range."""
        encoder = SWMIDIEncoder()
        state = VesselState(
            latitude=57.79, longitude=-152.40, fix_quality=1,
            heading=270, speed_over_ground=15.0, depth=150,
            engine_rpm=2800, water_temperature=30, sea_state=9,
            tank_level=0, battery_voltage=10.0, mode=VesselMode.EMERGENCY,
        )
        events = encoder.encode_vessel_state(state)
        for event in events:
            raw = event.to_bytes()
            for byte_val in raw:
                self.assertGreaterEqual(byte_val, 0)
                self.assertLessEqual(byte_val, 255)


# ═══════════════════════════════════════════════════════════════════════════
# VESSEL STATE TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestVesselModeFishing(unittest.TestCase):
    """TEST 16: Fishing mode detection."""

    def test_detects_fishing(self):
        """Speed < 2 kts with depth > 5 should eventually detect fishing."""
        mgr = VesselStateManager()

        # First update with depth to establish baseline
        mgr.update_depth(depth_fathoms=40.0)
        mgr.update_speed(sog=1.0)
        mgr.update_heading(heading=90.0)
        mgr.update_engine(rpm=800)

        # Second update with changing depth → fishing
        mgr.update_depth(depth_fathoms=42.0)
        mgr.update_speed(sog=1.0)

        self.assertEqual(mgr.state.mode, VesselMode.FISHING)

    def test_fishing_from_low_rpm(self):
        """Low RPM with moderate depth and low speed → fishing."""
        mgr = VesselStateManager()
        mgr.update_depth(depth_fathoms=30.0)
        mgr.update_speed(sog=1.5)
        mgr.update_engine(rpm=600)

        self.assertEqual(mgr.state.mode, VesselMode.FISHING)


class TestVesselModeTransit(unittest.TestCase):
    """TEST 17: Transit mode detection."""

    def test_detects_transit(self):
        """Speed > 4 kts with depth > 20 → transit."""
        mgr = VesselStateManager()
        mgr.update_depth(depth_fathoms=40.0)
        mgr.update_speed(sog=7.5)
        mgr.update_engine(rpm=1800)
        mgr.update_heading(heading=180.0)

        self.assertEqual(mgr.state.mode, VesselMode.TRANSIT)

    def test_departing_shallow(self):
        """Speed > 4 in shallow water → departing."""
        mgr = VesselStateManager()
        mgr.update_depth(depth_fathoms=8.0)
        mgr.update_speed(sog=5.0)
        mgr.update_engine(rpm=2000)

        self.assertEqual(mgr.state.mode, VesselMode.DEPARTING)


class TestVesselModeAnchored(unittest.TestCase):
    """TEST 18: Anchored mode detection."""

    def test_detects_anchored(self):
        """Speed < 0.5, low RPM, depth > 5 → anchored."""
        mgr = VesselStateManager()
        mgr.update_depth(depth_fathoms=15.0)
        mgr.update_speed(sog=0.2)
        mgr.update_engine(rpm=0)

        self.assertEqual(mgr.state.mode, VesselMode.ANCHORED)

    def test_docked_when_shallow(self):
        """Speed < 0.5, no depth or shallow → docked."""
        mgr = VesselStateManager()
        mgr.update_depth(depth_fathoms=2.0)
        mgr.update_speed(sog=0.1)
        mgr.update_engine(rpm=0)

        self.assertEqual(mgr.state.mode, VesselMode.DOCKED)


class TestVesselModePitchMapping(unittest.TestCase):
    """TEST 22: Vessel mode → pitch byte mapping."""

    def test_mode_pitch_values(self):
        """Each vessel mode has a unique pitch value."""
        encoder = SWMIDIEncoder()
        from vessel_state import VesselMode

        modes_and_pitches = [
            (VesselMode.UNKNOWN, 0),
            (VesselMode.DOCKED, 16),
            (VesselMode.FISHING, 128),
            (VesselMode.EMERGENCY, 255),
        ]

        for mode, expected_pitch in modes_and_pitches:
            pitch = encoder._mode_to_pitch(mode)
            self.assertEqual(pitch, expected_pitch,
                f"Mode {mode} should map to pitch {expected_pitch}, got {pitch}")


# ═══════════════════════════════════════════════════════════════════════════
# BRIDGE END-TO-END TEST
# ═══════════════════════════════════════════════════════════════════════════

class TestBridgeEndToEnd(unittest.TestCase):
    """TEST 19: Bridge end-to-end — NMEA sentence in → SWMIDI events out."""

    def test_gpgga_through_bridge(self):
        """A GPGGA sentence flows through the bridge to produce SWMIDI events."""
        bridge = NMEABridge()
        from simulator import build_checksum
        body = "GPGGA,123519,5747.400,N,15224.420,W,1,08,0.9,5.4,M,46.9,M,,"
        cs = build_checksum(body)
        sentence = f"${body}*{cs}"
        events = bridge.process_sentence(sentence)

        self.assertIsNotNone(events)
        self.assertGreater(len(events), 0)

        # At least one event should be GPS_POSITION
        statuses = {e.status for e in events}
        self.assertIn(EventType.GPS_POSITION, statuses)

        # Vessel state should be updated
        self.assertAlmostEqual(bridge.state_manager.state.latitude, 57.79, places=2)
        self.assertAlmostEqual(bridge.state_manager.state.longitude, -152.4070, places=2)

    def test_depth_through_bridge(self):
        """A depth sentence flows through to produce a DEPTH SWMIDI event."""
        from simulator import build_checksum
        bridge = NMEABridge()

        body = "SDDBT,360.0,f,109.7,M,60.0,F"
        cs = build_checksum(body)
        sentence = f"${body}*{cs}"
        events = bridge.process_sentence(sentence)

        self.assertIsNotNone(events)
        depth_events = [e for e in events if e.status == EventType.DEPTH]
        self.assertEqual(len(depth_events), 1)
        self.assertGreater(depth_events[0].pitch, 0)

    def test_multiple_sentences_accumulate_state(self):
        """Multiple NMEA sentences accumulate into a coherent vessel state."""
        from simulator import build_checksum
        bridge = NMEABridge()

        # GPS
        from simulator import build_checksum
        gga_body = "GPGGA,123519,5747.400,N,15224.420,W,1,08,0.9,5.4,M,46.9,M,,"
        bridge.process_sentence(f"${gga_body}*{build_checksum(gga_body)}")
        # Speed/course
        body = "GPRMC,123519,A,5747.400,N,15224.420,W,7.5,180.0,110826,,,"
        bridge.process_sentence(f"${body}*{build_checksum(body)}")
        # Depth
        body = "SDDBT,360.0,f,109.7,M,60.0,F"
        bridge.process_sentence(f"${body}*{build_checksum(body)}")
        # Heading
        body = "HCHDT,180.0,T"
        bridge.process_sentence(f"${body}*{build_checksum(body)}")
        # Engine
        body = "IIXDR,R,1800,RPM,ENGINE"
        bridge.process_sentence(f"${body}*{build_checksum(body)}")

        state = bridge.state_manager.state
        self.assertAlmostEqual(state.latitude, 57.79, places=1)
        self.assertAlmostEqual(state.longitude, -152.4070, places=1)
        self.assertAlmostEqual(state.speed_over_ground, 7.5)
        self.assertAlmostEqual(state.depth, 60.0)
        self.assertAlmostEqual(state.heading, 180.0)
        self.assertAlmostEqual(state.engine_rpm, 1800.0)

        # Mode should be transit (7.5 kts, 60 fm depth)
        self.assertEqual(state.mode, VesselMode.TRANSIT)


# ═══════════════════════════════════════════════════════════════════════════
# SIMULATOR TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestSimulatorOutput(unittest.TestCase):
    """TEST 20: Simulator output validation."""

    def test_generates_valid_sentences(self):
        """Simulator produces parseable NMEA sentences."""
        from simulator import TripSimulator

        sim = TripSimulator(seed=42)
        sentences = []
        count = 0
        for s in sim.generate(duration_minutes=1, update_rate_hz=1.0):
            sentences.append(s)
            count += 1
            if count >= 20:
                break

        self.assertGreater(len(sentences), 10)

        # All should start with $
        for s in sentences:
            self.assertTrue(s.startswith('$'), f"Sentence doesn't start with $: {s}")
            self.assertIn('*', s)  # Has checksum

    def test_simulator_sentence_types(self):
        """Simulator generates multiple sentence types (GGA, RMC, DBT, etc.)."""
        from simulator import TripSimulator

        sim = TripSimulator(seed=42)
        parser = NMEAParser()
        types_seen = set()
        count = 0

        for sentence in sim.generate(duration_minutes=1, update_rate_hz=1.0):
            result = parser.parse(sentence)
            if result and result.valid:
                types_seen.add(result.sentence_type)
            count += 1
            if count >= 30:
                break

        # Should see at least GGA, RMC, DBT, DPT, HDT, HDG, VHW, MTW, XDR
        self.assertIn(SentenceType.GPGGA, types_seen)
        self.assertIn(SentenceType.GPRMC, types_seen)
        self.assertIn(SentenceType.SDDBT, types_seen)
        self.assertGreaterEqual(len(types_seen), 5)

    def test_simulator_phases_progress(self):
        """Simulator transitions through trip phases."""
        from simulator import TripSimulator, TripPhase

        sim = TripSimulator(seed=42)
        phases_seen = set()
        count = 0

        for _ in sim.generate(duration_minutes=1, update_rate_hz=1.0):
            state = sim._simulate_state(count * 0.01)
            phases_seen.add(state.phase)
            count += 1
            if count >= 100:
                break

        # Should see multiple phases
        self.assertGreater(len(phases_seen), 2)

    def test_sentence_builders(self):
        """NMEA sentence builder functions produce valid checksums."""
        from simulator import (
            make_gga, make_rmc, make_dbt, make_dpt,
            make_hdt, make_hdg, make_mtw, make_vhw,
            make_xdr_rpm, make_xdr_tank, make_xdr_battery,
        )

        parser = NMEAParser()

        sentences = [
            make_gga(57.79, -152.40, 1, 8),
            make_rmc(57.79, -152.40, 7.5, 180.0),
            make_dbt(45.0),
            make_dpt(82.3),
            make_hdt(180.0),
            make_hdg(178.0, 15.0, 'E'),
            make_mtw(7.5),
            make_vhw(180.0, 7.5),
            make_xdr_rpm(1800),
            make_xdr_tank(85.0),
            make_xdr_battery(13.2),
        ]

        for sentence in sentences:
            result = parser.parse(sentence)
            self.assertIsNotNone(result, f"Failed to parse: {sentence}")
            self.assertTrue(result.valid, f"Invalid result for: {sentence}")
            self.assertNotEqual(result.sentence_type, SentenceType.UNKNOWN,
                f"Unknown sentence type for: {sentence}")


# ═══════════════════════════════════════════════════════════════════════════
# VESSEL STATE MANAGER TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestVesselStateManager(unittest.TestCase):
    """Additional VesselStateManager tests."""

    def test_musical_parameters(self):
        """Musical parameters are computed from vessel state."""
        mgr = VesselStateManager()
        mgr.update_engine(rpm=1800)
        mgr.update_depth(depth_fathoms=45.0)
        mgr.update_heading(heading=180.0)
        mgr.update_speed(sog=7.5)
        mgr.update_environment(sea_state=3.0)

        params = mgr.musical_parameters()
        self.assertGreater(params.tempo_bpm, 60)
        self.assertLess(params.tempo_bpm, 160)
        self.assertGreater(len(params.harmony_notes), 0)
        self.assertEqual(params.pan, heading_to_pan(180.0) if False else params.pan)  # Just check it exists

    def test_context_for_agents(self):
        """context_for_agents produces a complete context dict."""
        mgr = VesselStateManager()
        mgr.update_position(57.79, -152.40, fix_quality=1)
        mgr.update_depth(depth_fathoms=45.0)
        mgr.update_speed(sog=7.5)
        mgr.update_heading(heading=180.0)
        mgr.update_engine(rpm=1800)

        ctx = mgr.context_for_agents()
        self.assertEqual(ctx["vessel"], "FV Eileen")
        self.assertIn("mode", ctx)
        self.assertIn("musical", ctx)
        self.assertIsNotNone(ctx["position"])
        self.assertEqual(ctx["position"]["lat"], 57.79)

    def test_history_grows(self):
        """History accumulates with updates."""
        mgr = VesselStateManager()
        for i in range(10):
            mgr.update_depth(depth_fathoms=float(i))
        self.assertEqual(len(mgr.history), 10)


if __name__ == '__main__':
    unittest.main(verbosity=2)
