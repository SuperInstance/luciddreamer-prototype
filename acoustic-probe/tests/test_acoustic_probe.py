"""
tests/test_acoustic_probe.py — Tests for the Acoustic Probe modules.

Run with: python -m pytest tests/ -v
Or:       python -m unittest discover tests/
"""

import unittest
import math
import os
import sys
import tempfile

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telemetry_to_midi import (
    TelemetryToMIDI,
    MIDIPattern,
    MIDINote,
    rpm_to_bass_frequency,
    rpm_to_bass_midi_note,
    rpm_to_velocity,
    depth_to_harmony,
    depth_to_harmony_label,
    sea_state_to_rhythm,
    heading_to_pan,
    speed_to_tempo,
    speed_to_time_signature,
    pattern_to_midi_file,
)

from vessel_instrument import (
    VesselInstrument,
    VesselState,
    VesselMode,
    MusicalParameters,
)

from telemetry_simulator import (
    TelemetrySimulator,
    WeatherState,
    replay_telemetry,
)

from ship_to_song import ShipToSong, SongPrompt


# ═══════════════════════════════════════════════════════════════════════════
# TEST 1: RPM → Bass Frequency Mapping
# ═══════════════════════════════════════════════════════════════════════════

class TestRPMMapping(unittest.TestCase):
    """Engine RPM maps correctly to bass frequencies."""

    def test_rpm_to_bass_frequency_range(self):
        """RPM 0 → 55Hz (A1), RPM 3000 → 220Hz (A3)."""
        idle = rpm_to_bass_frequency(0)
        full = rpm_to_bass_frequency(3000)
        self.assertAlmostEqual(idle, 55.0, places=1,
                               msg="Idle RPM should produce ~55Hz")
        self.assertAlmostEqual(full, 220.0, places=1,
                               msg="Full RPM should produce ~220Hz")

    def test_rpm_to_bass_frequency_monotonic(self):
        """Higher RPM always produces higher frequency."""
        prev = 0
        for rpm in range(0, 3001, 100):
            freq = rpm_to_bass_frequency(rpm)
            self.assertGreater(freq, prev - 0.01,
                               f"Frequency should not decrease (rpm={rpm})")
            prev = freq

    def test_rpm_to_bass_midi_note_range(self):
        """MIDI notes stay within valid bass range."""
        low = rpm_to_bass_midi_note(0)
        high = rpm_to_bass_midi_note(3000)
        self.assertGreaterEqual(low, 20, "Bass MIDI note too low")
        self.assertLessEqual(high, 70, "Bass MIDI note too high for bass")

    def test_rpm_to_velocity(self):
        """Higher RPM → higher velocity."""
        idle_vel = rpm_to_velocity(0)
        full_vel = rpm_to_velocity(3000)
        self.assertGreater(full_vel, idle_vel,
                           "Full throttle should be louder than idle")
        self.assertGreaterEqual(idle_vel, 1, "Velocity should be at least 1")
        self.assertLessEqual(full_vel, 127, "Velocity should not exceed 127")


# ═══════════════════════════════════════════════════════════════════════════
# TEST 2: Depth → Harmony Mapping
# ═══════════════════════════════════════════════════════════════════════════

class TestDepthMapping(unittest.TestCase):
    """Depth maps correctly to harmonic complexity."""

    def test_shallow_depth_is_simple(self):
        """0-10 fathoms: root note only."""
        notes = depth_to_harmony(0, root_note=33)
        self.assertEqual(len(notes), 1,
                         "Zero depth should produce a single root note")
        self.assertEqual(notes[0], 33, "Root note should match")

    def test_deep_depth_is_complex(self):
        """95 fathoms: full chromatic fog."""
        notes = depth_to_harmony(95, root_note=33)
        self.assertGreater(len(notes), 5,
                           "Very deep water should produce many notes")

    def test_depth_monotonic_complexity(self):
        """Deeper water → more or equal harmonic notes (on average)."""
        import random
        random.seed(42)
        shallow_count = len(depth_to_harmony(5, root_note=33))
        deep_count = len(depth_to_harmony(85, root_note=33))
        self.assertGreaterEqual(deep_count, shallow_count,
                                "Deep water should have more harmonic content")

    def test_harmony_label_exists(self):
        """All depth values produce a human-readable label."""
        for depth in [0, 15, 30, 45, 60, 75, 88, 95, 100]:
            label = depth_to_harmony_label(depth)
            self.assertIsInstance(label, str)
            self.assertGreater(len(label), 5)


# ═══════════════════════════════════════════════════════════════════════════
# TEST 3: Sea State → Rhythm Mapping
# ═══════════════════════════════════════════════════════════════════════════

class TestSeaStateMapping(unittest.TestCase):
    """Sea state maps correctly to rhythmic patterns."""

    def test_calm_sea_is_steady(self):
        """Sea state 0: regular quarter-note pattern."""
        rhythm = sea_state_to_rhythm(0)
        self.assertEqual(len(rhythm), 16, "Pattern should be 16 steps")
        # Calm = 4 hits on the beat
        self.assertEqual(sum(rhythm), 4, "Calm sea should have 4 hits")

    def test_storm_is_dense(self):
        """Sea state 9: dense, chaotic rhythm."""
        rhythm = sea_state_to_rhythm(9)
        self.assertGreater(sum(rhythm), 8,
                           "Storm should produce dense rhythm")

    def test_calm_denser_than_storm_is_false(self):
        """Calm sea is never denser than storm."""
        calm = sum(sea_state_to_rhythm(0))
        storm = sum(sea_state_to_rhythm(9))
        self.assertGreater(storm, calm,
                           "Storm should be denser than calm")

    def test_rhythm_length_always_16(self):
        """All sea states produce 16-step patterns."""
        for ss in range(10):
            rhythm = sea_state_to_rhythm(float(ss))
            self.assertEqual(len(rhythm), 16)


# ═══════════════════════════════════════════════════════════════════════════
# TEST 4: Heading → Pan Mapping
# ═══════════════════════════════════════════════════════════════════════════

class TestHeadingMapping(unittest.TestCase):
    """Heading maps correctly to stereo pan."""

    def test_north_is_hard_left(self):
        """Heading 0° → pan near 0 (hard left)."""
        pan = heading_to_pan(0)
        self.assertLess(pan, 10, "North should be hard left")

    def test_south_is_hard_right(self):
        """Heading 180° → pan near 127 (hard right)."""
        pan = heading_to_pan(180)
        self.assertGreater(pan, 118, "South should be hard right")

    def test_east_west_are_centered(self):
        """East (90°) and West (270°) are near center."""
        east = heading_to_pan(90)
        west = heading_to_pan(270)
        self.assertGreater(east, 40, "East should be center-right")
        self.assertLess(east, 90)
        self.assertGreater(west, 40, "West should be center-left")
        self.assertLess(west, 90)

    def test_pan_bounds(self):
        """Pan always in [0, 127]."""
        for heading in range(0, 361, 15):
            pan = heading_to_pan(heading)
            self.assertGreaterEqual(pan, 0)
            self.assertLessEqual(pan, 127)


# ═══════════════════════════════════════════════════════════════════════════
# TEST 5: Speed → Tempo Mapping
# ═══════════════════════════════════════════════════════════════════════════

class TestSpeedMapping(unittest.TestCase):
    """Speed maps correctly to tempo and time signature."""

    def test_zero_speed_is_base_tempo(self):
        """0 knots → base tempo (60 BPM)."""
        bpm = speed_to_tempo(0)
        self.assertAlmostEqual(bpm, 60.0, places=1)

    def test_max_speed_is_max_tempo(self):
        """20+ knots → max tempo (160 BPM)."""
        bpm = speed_to_tempo(20)
        self.assertAlmostEqual(bpm, 160.0, places=1)
        # Clamped
        bpm_clamped = speed_to_tempo(100)
        self.assertAlmostEqual(bpm_clamped, 160.0, places=1)

    def test_speed_to_time_signature(self):
        """Speed affects time signature."""
        self.assertEqual(speed_to_time_signature(1.0), (3, 4), "Slow = waltz")
        self.assertEqual(speed_to_time_signature(5.0), (4, 4), "Medium = common time")
        self.assertEqual(speed_to_time_signature(12.0), (6, 8), "Fast = compound")


# ═══════════════════════════════════════════════════════════════════════════
# TEST 6: Vessel Instrument
# ═══════════════════════════════════════════════════════════════════════════

class TestVesselInstrument(unittest.TestCase):
    """The VesselInstrument class works as a virtual instrument."""

    def test_update_and_state(self):
        """Updating vessel state stores correct values."""
        vessel = VesselInstrument()
        vessel.update(rpm=1500, depth=30, sea_state=3, heading=90, speed=6.0)
        self.assertEqual(vessel.state.rpm, 1500)
        self.assertEqual(vessel.state.depth, 30)
        self.assertEqual(vessel.state.sea_state, 3)
        self.assertEqual(vessel.state.heading, 90)
        self.assertEqual(vessel.state.speed, 6.0)

    def test_rpm_clamping(self):
        """RPM is clamped to [0, 3000]."""
        vessel = VesselInstrument()
        vessel.update(rpm=5000)
        self.assertEqual(vessel.state.rpm, 3000, "RPM should clamp at 3000")
        vessel.update(rpm=-500)
        self.assertEqual(vessel.state.rpm, 0, "RPM should clamp at 0")

    def test_heading_wraps_360(self):
        """Heading wraps around 360°."""
        vessel = VesselInstrument()
        vessel.update(heading=370)
        self.assertAlmostEqual(vessel.state.heading, 10.0, places=1)

    def test_get_musical_parameters(self):
        """Musical parameters are correctly derived from vessel state."""
        vessel = VesselInstrument()
        vessel.update(rpm=1800, depth=40, sea_state=4, heading=180, speed=7.5)
        params = vessel.get_musical_parameters()
        self.assertIsInstance(params, MusicalParameters)
        self.assertGreater(params.bass_frequency, 55.0)
        self.assertLess(params.bass_frequency, 220.0)
        self.assertGreater(params.tempo_bpm, 60.0)
        self.assertIsInstance(params.harmony_notes, list)
        self.assertGreater(len(params.harmony_notes), 0)

    def test_play_generates_pattern(self):
        """play() returns a MIDIPattern with notes."""
        vessel = VesselInstrument()
        vessel.update(rpm=1500, depth=30, sea_state=3, heading=90, speed=5.0)
        pattern = vessel.play(bars=2)
        self.assertIsInstance(pattern, MIDIPattern)
        self.assertGreater(len(pattern.notes), 0, "Pattern should have notes")

    def test_mode_detection(self):
        """Auto mode detection works for common states."""
        vessel = VesselInstrument()
        # Docked
        vessel.update(rpm=50, depth=2, speed=0.1, sea_state=0)
        self.assertEqual(vessel.state.mode, VesselMode.DOCKED)
        # Transit
        vessel.update(rpm=2200, depth=40, speed=8.0, sea_state=2)
        self.assertEqual(vessel.state.mode, VesselMode.TRANSIT)

    def test_listener_fires(self):
        """Listeners are notified on state update."""
        vessel = VesselInstrument()
        received = []
        vessel.add_listener(lambda state: received.append(state.rpm))
        vessel.update(rpm=1200)
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0], 1200)

    def test_trend_analysis(self):
        """Trend analysis detects changes."""
        vessel = VesselInstrument()
        vessel.update(rpm=800, depth=20)
        vessel.update(rpm=1200, depth=25)
        vessel.update(rpm=1800, depth=35)
        trend = vessel.get_trend()
        self.assertTrue(trend["rpm_rising"], "RPM should be trending up")
        self.assertTrue(trend["deepening"], "Depth should be increasing")


# ═══════════════════════════════════════════════════════════════════════════
# TEST 7: Telemetry Simulator
# ═══════════════════════════════════════════════════════════════════════════

class TestTelemetrySimulator(unittest.TestCase):
    """The telemetry simulator produces realistic vessel data."""

    def test_trip_generates_states(self):
        """A fishing trip yields multiple VesselState objects."""
        sim = TelemetrySimulator(seed=42)
        states = list(sim.run_fishing_trip(duration_hours=2, step_minutes=30))
        self.assertEqual(len(states), 4, "2hr/30min = 4 steps")
        for state in states:
            self.assertIsInstance(state, VesselState)

    def test_trip_progresses_through_phases(self):
        """A full trip includes departing, transit, fishing, returning."""
        sim = TelemetrySimulator(seed=42)
        states = list(sim.run_fishing_trip(duration_hours=8, step_minutes=15))
        modes = [s.mode for s in states]
        # Should see at least departing, transit, and fishing
        self.assertIn(VesselMode.DEPARTING, modes + [VesselMode.DOCKED],
                      "Trip should include departing phase")
        self.assertIn(VesselMode.FISHING, modes,
                      "Trip should include fishing phase")

    def test_fishing_states_are_in_deep_water(self):
        """Fishing phase has deep water."""
        sim = TelemetrySimulator(seed=42)
        states = list(sim.run_fishing_trip(duration_hours=8, step_minutes=10))
        fishing_states = [s for s in states if s.mode in (VesselMode.FISHING, VesselMode.HAULING)]
        if fishing_states:
            avg_depth = sum(s.depth for s in fishing_states) / len(fishing_states)
            self.assertGreater(avg_depth, 20, "Fishing should be in deep water")

    def test_rpm_stays_in_valid_range(self):
        """RPM never exceeds 3000 or goes negative."""
        sim = TelemetrySimulator(seed=42)
        for state in sim.run_fishing_trip(duration_hours=8, step_minutes=30):
            self.assertGreaterEqual(state.rpm, 0, "RPM must be non-negative")
            self.assertLessEqual(state.rpm, 3500, "RPM should stay reasonable")

    def test_weather_varies(self):
        """Sea state changes during the simulation."""
        sim = TelemetrySimulator(seed=123)
        states = list(sim.run_fishing_trip(duration_hours=12, step_minutes=30))
        sea_states = [s.sea_state for s in states]
        # At least some variation over 12 hours
        self.assertGreater(max(sea_states) - min(sea_states), 0.1,
                           "Sea state should vary during trip")

    def test_replay_telemetry(self):
        """Replay function processes historical records."""
        records = [
            {"rpm": 800, "depth": 10, "speed": 3, "heading": 90, "sea_state": 2, "timestamp": 1},
            {"rpm": 1800, "depth": 40, "speed": 7, "heading": 180, "sea_state": 3, "timestamp": 2},
            {"rpm": 900, "depth": 60, "speed": 2, "heading": 270, "sea_state": 4, "timestamp": 3},
        ]
        states = list(replay_telemetry(records))
        self.assertEqual(len(states), 3)
        self.assertEqual(states[0].rpm, 800)
        self.assertEqual(states[2].depth, 60)


# ═══════════════════════════════════════════════════════════════════════════
# TEST 8: Ship to Song
# ═══════════════════════════════════════════════════════════════════════════

class TestShipToSong(unittest.TestCase):
    """Ship-to-song conversion produces valid music prompts."""

    def test_generate_prompt_fishing(self):
        """Fishing state produces a fishing-appropriate prompt."""
        converter = ShipToSong()
        state = VesselState(
            rpm=900, depth=60, sea_state=3, heading=180, speed=2.5,
            mode=VesselMode.FISHING,
        )
        song = converter.generate_prompt(state, duration_seconds=45)
        self.assertIsInstance(song, SongPrompt)
        self.assertGreater(len(song.prompt), 50, "Prompt should be substantial")
        self.assertIn("bass", song.prompt.lower(), "Prompt should mention bass")
        self.assertIn("fathom", song.prompt.lower(), "Prompt should mention depth")
        self.assertEqual(song.duration_seconds, 45)

    def test_prompt_changes_with_state(self):
        """Different vessel states produce different prompts."""
        converter = ShipToSong()
        calm_state = VesselState(
            rpm=500, depth=2, sea_state=0, heading=0, speed=0.5,
            mode=VesselMode.DOCKED,
        )
        rough_state = VesselState(
            rpm=2500, depth=85, sea_state=8, heading=180, speed=9.0,
            mode=VesselMode.TRANSIT,
        )
        calm_song = converter.generate_prompt(calm_state)
        rough_song = converter.generate_prompt(rough_state)
        self.assertNotEqual(calm_song.prompt, rough_song.prompt,
                            "Different states should produce different prompts")
        # Rough state should mention higher tempo
        self.assertIn(str(int(rough_song.metadata["tempo_bpm"])), rough_song.prompt)

    def test_negative_prompt_excludes_vocals(self):
        """Negative prompt always excludes vocals."""
        converter = ShipToSong()
        state = VesselState(rpm=1000, depth=20, sea_state=2, heading=90, speed=4.0)
        song = converter.generate_prompt(state)
        self.assertIn("vocals", song.negative_prompt)
        self.assertIn("singing", song.negative_prompt)

    def test_state_report_readable(self):
        """State report produces readable output."""
        converter = ShipToSong()
        state = VesselState(
            rpm=1200, depth=35, sea_state=3, heading=135, speed=5.0,
            mode=VesselMode.TRANSIT,
        )
        report = converter.state_report(state)
        self.assertIsInstance(report, str)
        self.assertIn("RPM", report)
        self.assertIn("fathom", report.lower())
        self.assertIn("BPM", report)

    def test_metadata_contains_musical_params(self):
        """Song metadata includes full musical parameters."""
        converter = ShipToSong()
        state = VesselState(
            rpm=1500, depth=40, sea_state=4, heading=225, speed=6.5,
            mode=VesselMode.FISHING,
        )
        song = converter.generate_prompt(state)
        self.assertIn("bass_note", song.metadata)
        self.assertIn("tempo_bpm", song.metadata)
        self.assertIn("harmony_label", song.metadata)
        self.assertIn("musical_parameters", song.metadata)

    def test_mode_specific_flavor(self):
        """Each mode adds specific atmospheric text."""
        converter = ShipToSong()
        fishing = converter.generate_prompt(VesselState(
            rpm=900, depth=50, sea_state=2, speed=2, heading=45,
            mode=VesselMode.FISHING))
        transit = converter.generate_prompt(VesselState(
            rpm=2200, depth=30, sea_state=3, speed=8, heading=180,
            mode=VesselMode.TRANSIT))

        self.assertIn("patience", fishing.prompt.lower(),
                      "Fishing prompt should mention patience")
        self.assertIn("hypnotic", transit.prompt.lower(),
                      "Transit prompt should mention hypnotic repetition")


# ═══════════════════════════════════════════════════════════════════════════
# TEST 9: MIDI Pattern Generation & File Export
# ═══════════════════════════════════════════════════════════════════════════

class TestMIDIPatternGeneration(unittest.TestCase):
    """MIDI pattern generation and file export work correctly."""

    def test_generate_pattern_basic(self):
        """TelemetryToMIDI generates a pattern from vessel state."""
        converter = TelemetryToMIDI()
        state = {"rpm": 1500, "depth": 30, "sea_state": 3, "heading": 90, "speed": 5.0}
        pattern = converter.generate_pattern(state, bars=2)
        self.assertIsInstance(pattern, MIDIPattern)
        self.assertGreater(len(pattern.notes), 0)
        self.assertGreater(pattern.tempo_bpm, 0)

    def test_pattern_metadata_populated(self):
        """Pattern metadata includes derived musical info."""
        converter = TelemetryToMIDI()
        state = {"rpm": 1200, "depth": 45, "sea_state": 4, "heading": 180, "speed": 6.0}
        pattern = converter.generate_pattern(state, bars=1)
        self.assertIn("bass_freq_hz", pattern.metadata)
        self.assertIn("harmony_label", pattern.metadata)
        self.assertIn("vessel_state", pattern.metadata)

    def test_midi_file_export(self):
        """Pattern can be written to a .mid file."""
        converter = TelemetryToMIDI()
        state = {"rpm": 1800, "depth": 40, "sea_state": 3, "heading": 90, "speed": 7.0}
        pattern = converter.generate_pattern(state, bars=2)

        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as f:
            filename = f.name

        try:
            pattern_to_midi_file(pattern, filename)
            self.assertTrue(os.path.exists(filename))
            self.assertGreater(os.path.getsize(filename), 20,
                               "MIDI file should have content")
            # Check MIDI header
            with open(filename, "rb") as f:
                header = f.read(4)
                self.assertEqual(header, b"MThd", "File should start with MIDI header")
        finally:
            if os.path.exists(filename):
                os.unlink(filename)

    def test_pattern_text_output(self):
        """Pattern text output is readable."""
        converter = TelemetryToMIDI()
        state = {"rpm": 1000, "depth": 25, "sea_state": 2, "heading": 45, "speed": 4.0}
        pattern = converter.generate_pattern(state, bars=1)
        text = converter.pattern_to_text(pattern)
        self.assertIsInstance(text, str)
        self.assertIn("BPM", text)
        self.assertIn("Hz", text)


# ═══════════════════════════════════════════════════════════════════════════
# TEST 10: Integration — Full Pipeline
# ═══════════════════════════════════════════════════════════════════════════

class TestIntegration(unittest.TestCase):
    """Full pipeline: simulator → vessel instrument → MIDI + song prompt."""

    def test_simulated_trip_to_music(self):
        """A simulated trip produces valid music at every step."""
        sim = TelemetrySimulator(seed=42)
        vessel = VesselInstrument()
        converter = TelemetryToMIDI()
        song_gen = ShipToSong()

        states = list(sim.run_fishing_trip(duration_hours=4, step_minutes=30))

        self.assertGreater(len(states), 0)

        for state in states:
            # Update vessel
            vessel.state = state
            vessel.state.mode = state.mode

            # Get musical parameters
            params = vessel.get_musical_parameters()
            self.assertGreater(params.tempo_bpm, 0)
            self.assertGreater(len(params.harmony_notes), 0)

            # Generate MIDI pattern
            pattern = converter.generate_pattern(state.to_dict(), bars=1)
            self.assertGreater(len(pattern.notes), 0)

            # Generate song prompt
            song = song_gen.generate_prompt(state, duration_seconds=30)
            self.assertGreater(len(song.prompt), 100)

    def test_engine_labor_bass_drops(self):
        """When engine labors (high RPM, low speed), bass frequency is high."""
        vessel = VesselInstrument()
        # Engine under heavy load: high RPM but low speed (trawling/fighting gear)
        vessel.update(rpm=2500, depth=60, sea_state=5, heading=45, speed=1.5,
                      mode=VesselMode.HAULING)
        params = vessel.get_musical_parameters()
        # High RPM = high bass frequency (engine screaming)
        self.assertGreater(params.bass_frequency, 150,
                           "High RPM should produce high bass frequency")

    def test_depth_change_shifts_chords(self):
        """Moving from shallow to deep water increases harmonic complexity."""
        vessel = VesselInstrument()
        song_gen = ShipToSong()

        # Shallow — simple harmony
        vessel.update(rpm=1200, depth=5, sea_state=2, heading=90, speed=5)
        shallow_song = song_gen.generate_prompt(vessel.state)
        shallow_notes = vessel.get_musical_parameters().harmony_notes

        # Deep — complex harmony
        vessel.update(depth=85)
        deep_song = song_gen.generate_prompt(vessel.state)
        deep_notes = vessel.get_musical_parameters().harmony_notes

        self.assertGreater(len(deep_notes), len(shallow_notes),
                           "Deeper water should produce more harmony notes")
        self.assertNotEqual(shallow_song.prompt, deep_song.prompt)


if __name__ == "__main__":
    unittest.main()
