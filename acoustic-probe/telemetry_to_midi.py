"""
telemetry_to_midi.py — Maps FV Eileen physical vessel data to MIDI patterns.

Engine RPM (0-3000)    → fundamental bass frequency (55Hz idle → 220Hz full)
Depth/Fathoms (0-100)  → harmonic complexity (root → 7ths → chromatic fog)
Sea State (0-9 Beaufort) → rhythmic jitter (steady 4/4 → syncopated polyrhythms)
Heading (0-360°)       → pan position (stereo field, 0°=hard left, 180°=center, 360°=hard right)
Speed (knots)          → overall tempo scaling
"""

from __future__ import annotations
import math
import random
from dataclasses import dataclass, field
from typing import List, Tuple, Optional


# ─── Constants ──────────────────────────────────────────────────────────────

MIDI_NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Bass frequency range
BASS_FREQ_MIN = 55.0      # A1 — idle
BASS_FREQ_MAX = 220.0     # A3 — full throttle

# MIDI note numbers
MIDI_A0 = 21
MIDI_A1 = 33   # 55 Hz
MIDI_A3 = 57   # 220 Hz

# Scale degrees (semitone offsets from root) for harmonic complexity tiers
HARMONY_TIERS = [
    [0],                                    # 0-10 fathoms: root only (open fifth drone)
    [0, 7],                                 # 10-25: root + fifth (power chord)
    [0, 7, 12],                             # 25-40: add octave
    [0, 4, 7, 11],                          # 40-55: major triad + 7th
    [0, 3, 7, 10, 14],                      # 55-70: minor 7th + 9th
    [0, 3, 7, 10, 14, 17],                  # 70-82: add 11th
    [0, 1, 3, 5, 6, 7, 8, 10, 11, 13],      # 82-90: chromatic clusters
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], # 90+: full chromatic fog
]

# Rhythm patterns per sea state (16th note grid, 1=hit, 0=rest)
RHYTHM_PATTERNS = {
    0: [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],         # Glass calm: steady quarters
    1: [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0],         # Light breeze
    2: [1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0],         # Gentle: off-beat 16ths
    3: [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],         # Moderate: 8th notes
    4: [1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 0],         # Rough: syncopation
    5: [1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1],         # Very rough
    6: [1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1],         # High: polyrhythm feel
    7: [1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1],         # Gale
    8: [1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 1, 0, 1, 1],         # Strong gale
    9: [1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1],         # Storm: chaotic
}

# Default tempo range
TEMPO_BASE_BPM = 60.0   # At 0 knots
TEMPO_MAX_BPM = 160.0   # At 20+ knots
SPEED_FOR_MAX_TEMPO = 20.0


# ─── Data Structures ────────────────────────────────────────────────────────

@dataclass
class MIDINote:
    """A single MIDI note event."""
    note: int               # MIDI note number (0-127)
    velocity: int           # 0-127
    start_step: float       # Start time in 16th-note steps
    duration: float         # Duration in 16th-note steps
    channel: int = 0        # MIDI channel
    pan: int = 64           # Pan (0=hard left, 64=center, 127=hard right)


@dataclass
class MIDIPattern:
    """A complete MIDI pattern representing vessel state."""
    notes: List[MIDINote] = field(default_factory=list)
    tempo_bpm: float = 120.0
    time_signature: Tuple[int, int] = (4, 4)
    key_root: int = 33      # Root MIDI note (A1 default)
    metadata: dict = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.notes)

    def total_steps(self) -> float:
        if not self.notes:
            return 0.0
        return max(n.start_step + n.duration for n in self.notes)


# ─── Core Mapping Functions ─────────────────────────────────────────────────

def rpm_to_bass_frequency(rpm: float) -> float:
    """Map engine RPM (0-3000) to bass frequency (55Hz → 220Hz).

    Uses exponential interpolation so the perceptual pitch change feels linear.
    """
    rpm = max(0.0, min(3000.0, rpm))
    # Exponential: frequency doubles every ~1000 RPM for musical feel
    ratio = rpm / 3000.0
    return BASS_FREQ_MIN * (BASS_FREQ_MAX / BASS_FREQ_MIN) ** ratio


def rpm_to_bass_midi_note(rpm: float) -> int:
    """Map engine RPM to nearest MIDI note number."""
    freq = rpm_to_bass_frequency(rpm)
    # MIDI note from frequency: n = 69 + 12 * log2(f / 440)
    note = round(69 + 12 * math.log2(freq / 440.0))
    return max(MIDI_A0, min(127, note))


def rpm_to_velocity(rpm: float) -> int:
    """Map RPM to MIDI velocity (higher RPM = louder bass)."""
    rpm = max(0.0, min(3000.0, rpm))
    # 40 (quiet idle) → 110 (hammering full throttle)
    return int(40 + (rpm / 3000.0) * 70)


def depth_to_harmony(depth_fathoms: float, root_note: int = 33) -> List[int]:
    """Map depth (0-100 fathoms) to a set of MIDI notes (harmonic complexity).

    Returns a list of MIDI note numbers representing the current chord/cluster.
    """
    depth = max(0.0, min(100.0, depth_fathoms))

    # Select harmony tier
    tier_boundaries = [0, 10, 25, 40, 55, 70, 82, 90]
    tier_index = 0
    for i, boundary in enumerate(tier_boundaries):
        if depth >= boundary:
            tier_index = i
    tier_index = min(tier_index, len(HARMONY_TIERS) - 1)

    intervals = HARMONY_TIERS[tier_index]

    # For chromatic fog tiers, add randomness based on depth
    if tier_index >= 6:
        # Add random chromatic neighbors proportional to depth
        fog_density = (depth - 82) / 18.0  # 0 at 82 fathoms, 1 at 100
        extra_count = int(fog_density * 4)
        base_notes = [root_note + iv for iv in intervals]
        for _ in range(extra_count):
            random_offset = random.choice([-2, -1, 1, 2, 3])
            candidate = root_note + 12 + random_offset
            if candidate not in base_notes and 21 <= candidate <= 96:
                base_notes.append(candidate)
        return sorted(set(base_notes))

    return sorted(root_note + iv for iv in intervals)


def depth_to_harmony_label(depth_fathoms: float) -> str:
    """Human-readable label for the harmonic complexity at this depth."""
    depth = max(0.0, min(100.0, depth_fathoms))
    labels = [
        (10, "Root drone — open sea floor"),
        (25, "Root + fifth — anchor holding"),
        (40, "Octave added — midwater column"),
        (55, "Major 7th — current pulling"),
        (70, "Minor 9th + 11th — deep water tension"),
        (82, "Chromatic clusters — the abyss approaches"),
        (90, "Full chromatic fog — deep and dissonant"),
        (101, "Dense fog — impossible depth"),
    ]
    for threshold, label in labels:
        if depth < threshold:
            return label
    return labels[-1][1]


def sea_state_to_rhythm(sea_state: float) -> List[int]:
    """Map sea state (0-9 Beaufort) to a 16-step rhythm pattern.

    Returns a list of 16 values (1=hit, 0=rest).
    """
    ss = max(0, min(9, int(round(sea_state))))

    pattern = RHYTHM_PATTERNS[ss].copy()

    # For intermediate sea states (e.g., 3.5), blend patterns
    fractional = sea_state - int(sea_state)
    if fractional > 0.3 and ss < 9:
        next_pattern = RHYTHM_PATTERNS[ss + 1]
        blended = []
        for i in range(16):
            if pattern[i] or (next_pattern[i] and random.random() < fractional):
                blended.append(1)
            else:
                blended.append(0)
        return blended

    return pattern


def heading_to_pan(heading: float) -> int:
    """Map compass heading (0-360°) to MIDI pan (0-127).

    0°/360° = hard left (127), 90° = center-ish right,
    180° = hard right (0), 270° = center-ish left.

    We fold the compass onto a stereo field where:
    - North (0/360) → hard left
    - South (180) → hard right
    - East (90) → center
    - West (270) → center (other side)
    """
    h = heading % 360.0
    # Map 0→0 (left), 180→127 (right), 360→0 (left) — triangular
    if h <= 180:
        pan = int((h / 180.0) * 127)
    else:
        pan = int(((360.0 - h) / 180.0) * 127)
    return max(0, min(127, pan))


def speed_to_tempo(speed_knots: float, base_bpm: float = TEMPO_BASE_BPM) -> float:
    """Map vessel speed (knots) to tempo (BPM).

    0 knots = base tempo (60 BPM, slow diesel idle).
    20+ knots = max tempo (160 BPM, racing).
    """
    speed = max(0.0, min(SPEED_FOR_MAX_TEMPO, speed_knots))
    ratio = speed / SPEED_FOR_MAX_TEMPO
    return base_bpm + (TEMPO_MAX_BPM - base_bpm) * ratio


def speed_to_time_signature(speed_knots: float) -> Tuple[int, int]:
    """Vessel speed affects time signature feel.

    Slow (< 3 kt): 3/4 (waltz — gentle rolling)
    Medium (3-8 kt): 4/4 (steady transit)
    Fast (> 8 kt): 6/8 (driving compound meter)
    """
    if speed_knots < 3.0:
        return (3, 4)
    elif speed_knots > 8.0:
        return (6, 8)
    return (4, 4)


# ─── Pattern Generation ─────────────────────────────────────────────────────

class TelemetryToMIDI:
    """Converts vessel telemetry state into a MIDI pattern."""

    def __init__(self, root_note: int = MIDI_A1):
        self.root_note = root_note

    def generate_pattern(
        self,
        vessel_state: dict,
        bars: int = 2,
    ) -> MIDIPattern:
        """Generate a MIDI pattern from a vessel state dictionary.

        Args:
            vessel_state: Dict with keys 'rpm', 'depth', 'sea_state',
                         'heading', 'speed'
            bars: Number of bars to generate

        Returns:
            MIDIPattern with bass + harmony parts
        """
        rpm = vessel_state.get("rpm", 0.0)
        depth = vessel_state.get("depth", 0.0)
        sea_state = vessel_state.get("sea_state", 0.0)
        heading = vessel_state.get("heading", 0.0)
        speed = vessel_state.get("speed", 0.0)

        # Derive musical parameters
        bass_note = rpm_to_bass_midi_note(rpm)
        bass_velocity = rpm_to_velocity(rpm)
        harmony_notes = depth_to_harmony(depth, bass_note)
        rhythm = sea_state_to_rhythm(sea_state)
        pan = heading_to_pan(heading)
        tempo = speed_to_tempo(speed)
        time_sig = speed_to_time_signature(speed)

        pattern = MIDIPattern(
            tempo_bpm=tempo,
            time_signature=time_sig,
            key_root=bass_note,
            metadata={
                "bass_freq_hz": rpm_to_bass_frequency(rpm),
                "harmony_label": depth_to_harmony_label(depth),
                "rhythm_density": sum(rhythm) / len(rhythm),
                "pan": pan,
                "vessel_state": vessel_state.copy(),
            },
        )

        steps_per_bar = time_sig[0] * 4  # 16th notes per bar
        total_steps = steps_per_bar * bars

        # Generate bass line using rhythm pattern
        rhythm_len = len(rhythm)
        step = 0
        while step < total_steps:
            rhythm_index = step % rhythm_len
            if rhythm[rhythm_index]:
                # Bass note
                note_duration = self._note_duration(rhythm, rhythm_index, total_steps, step)
                pattern.notes.append(MIDINote(
                    note=bass_note,
                    velocity=bass_velocity,
                    start_step=float(step),
                    duration=float(note_duration),
                    channel=0,
                    pan=pan,
                ))

                # Harmony notes (from depth mapping) — softer, higher
                for h_note in harmony_notes[1:]:  # Skip root (bass covers it)
                    pattern.notes.append(MIDINote(
                        note=h_note,
                        velocity=max(20, bass_velocity - 30),
                        start_step=float(step),
                        duration=float(note_duration) * 0.8,
                        channel=1,
                        pan=pan,
                    ))

            step += 1

        # Add a sustained bass drone for the first beat (engine idling feel)
        pattern.notes.insert(0, MIDINote(
            note=bass_note,
            velocity=bass_velocity - 10,
            start_step=0.0,
            duration=float(steps_per_bar),
            channel=2,
            pan=pan,
        ))

        return pattern

    def _note_duration(
        self, rhythm: List[int], index: int, total: int, current: int
    ) -> int:
        """Calculate how long a note should sustain based on surrounding rhythm."""
        duration = 1
        i = index + 1
        while i < len(rhythm) and rhythm[i] == 0 and current + duration < total:
            duration += 1
            i += 1
        return min(duration, 4)  # Cap at quarter note (4 sixteenths)

    def pattern_to_text(self, pattern: MIDIPattern) -> str:
        """Render a human-readable summary of the MIDI pattern."""
        lines = [
            f"═══ FV Eileen — MIDI Pattern ═══",
            f"  Tempo:     {pattern.tempo_bpm:.1f} BPM",
            f"  Time Sig:  {pattern.time_signature[0]}/{pattern.time_signature[1]}",
            f"  Bass Root: {MIDI_NOTE_NAMES[pattern.key_root % 12]}{pattern.key_root // 12 - 1} ({pattern.metadata.get('bass_freq_hz', 0):.1f} Hz)",
            f"  Harmony:   {pattern.metadata.get('harmony_label', '?')}",
            f"  Rhythm:    {pattern.metadata.get('rhythm_density', 0):.0%} density",
            f"  Pan:       {pattern.metadata.get('pan', 64)}/127",
            f"  Notes:     {len(pattern.notes)} events",
            f"  Length:    {pattern.total_steps():.0f} steps",
        ]
        return "\n".join(lines)


# ─── MIDI File Export (optional, no external deps) ──────────────────────────

def pattern_to_midi_file(pattern: MIDIPattern, filename: str) -> None:
    """Write a MIDIPattern to a .mid file using raw byte construction.

    This avoids the need for the mido/midiutil packages.
    Produces a valid Type-0 MIDI file.
    """
    # This is a simplified MIDI writer — produces valid but minimal files
    # For production, use mido or pretty_midi
    try:
        import mido
        _pattern_to_midi_mido(pattern, filename)
        return
    except ImportError:
        pass

    # Fallback: write raw bytes
    _pattern_to_midi_raw(pattern, filename)


def _pattern_to_midi_mido(pattern: MIDIPattern, filename: str) -> None:
    """Write MIDI using mido if available."""
    import mido

    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)

    # Tempo
    microseconds_per_beat = int(60_000_000 / pattern.tempo_bpm)
    track.append(mido.MetaMessage("set_tempo", tempo=microseconds_per_beat, time=0))

    # Time signature
    track.append(mido.MetaMessage(
        "time_signature",
        numerator=pattern.time_signature[0],
        denominator=pattern.time_signature[1],
        time=0,
    ))

    ticks_per_step = 480 // 4  # 16th note = 120 ticks

    # Convert notes to events
    events = []
    for note in pattern.notes:
        events.append(("on", int(note.start_step * ticks_per_step), note))
        events.append(("off", int((note.start_step + note.duration) * ticks_per_step), note))

    events.sort(key=lambda e: (e[1], 0 if e[0] == "on" else 1))

    last_time = 0
    for event_type, time, note in events:
        delta = time - last_time
        last_time = time
        if event_type == "on":
            track.append(mido.Message(
                "note_on", note=note.note, velocity=note.velocity,
                channel=note.channel, time=max(0, delta),
            ))
        else:
            track.append(mido.Message(
                "note_off", note=note.note, velocity=0,
                channel=note.channel, time=max(0, delta),
            ))

    mid.save(filename)


def _pattern_to_midi_raw(pattern: MIDIPattern, filename: str) -> None:
    """Minimal raw MIDI file writer (no dependencies).

    Produces a Type-0 MIDI file with note data.
    """
    ticks_per_beat = 480
    ticks_per_step = ticks_per_beat // 4

    def varlen(value):
        """Encode a variable-length MIDI quantity."""
        buffer = value & 0x7F
        value >>= 7
        while value:
            buffer <<= 8
            buffer |= (value & 0x7F) | 0x80
            value >>= 7
        result = []
        while True:
            result.append(buffer & 0xFF)
            if buffer & 0xFF80:
                buffer >>= 8
            else:
                break
        return bytes(result)

    # Build track events
    events = []
    for note in pattern.notes:
        on_tick = int(note.start_step * ticks_per_step)
        off_tick = int((note.start_step + note.duration) * ticks_per_step)
        ch = note.channel & 0x0F
        events.append((on_tick, 0x90 | ch, note.note, note.velocity))
        events.append((off_tick, 0x80 | ch, note.note, 0))

    events.sort(key=lambda e: (e[0], 0 if e[0] == 0x90 else 1))

    # Tempo meta event
    tempo_bpm = pattern.tempo_bpm if pattern.tempo_bpm > 0 else 120
    microseconds = int(60_000_000 / tempo_bpm)
    tempo_bytes = microseconds.to_bytes(3, "big")

    track_data = bytearray()
    # Tempo
    track_data.extend(varlen(0))
    track_data.extend([0xFF, 0x51, 0x03])
    track_data.extend(tempo_bytes)

    # Note events with delta times
    last_tick = 0
    for tick, status, note_num, velocity in events:
        delta = max(0, tick - last_tick)
        last_tick = tick
        track_data.extend(varlen(delta))
        track_data.extend([status, note_num & 0x7F, velocity & 0x7F])

    # End of track
    track_data.extend(varlen(0))
    track_data.extend([0xFF, 0x2F, 0x00])

    # Build file
    header = bytearray()
    header.extend(b"MThd")
    header.extend((6).to_bytes(4, "big"))   # Header length
    header.extend((0).to_bytes(2, "big"))    # Format 0
    header.extend((1).to_bytes(2, "big"))    # 1 track
    header.extend(ticks_per_beat.to_bytes(2, "big"))

    track_header = bytearray()
    track_header.extend(b"MTrk")
    track_header.extend(len(track_data).to_bytes(4, "big"))

    with open(filename, "wb") as f:
        f.write(header)
        f.write(track_header)
        f.write(track_data)


# ─── CLI ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    converter = TelemetryToMIDI()

    # Demo: three vessel states
    states = [
        {"rpm": 600, "depth": 5, "sea_state": 1, "heading": 0, "speed": 2.0, "label": "Leaving harbor"},
        {"rpm": 1800, "depth": 40, "sea_state": 4, "heading": 180, "speed": 7.5, "label": "Transit"},
        {"rpm": 2400, "depth": 85, "sea_state": 6, "heading": 270, "speed": 5.0, "label": "Fishing deep"},
    ]

    for state in states:
        label = state.pop("label")
        pattern = converter.generate_pattern(state)
        print(f"\n{'─' * 50}")
        print(f"  {label}")
        print(converter.pattern_to_text(pattern))
