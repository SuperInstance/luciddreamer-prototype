"""
ship_to_song.py — Combines vessel instrument state with MMX music generation.

Takes current telemetry state, generates an MMX music prompt from the vessel's
musical parameters, and outputs a short piece (30-60 seconds) that IS the
ship's current state as music.

When the engine labors, the bass drops.
When the depth changes, the chords shift.

Usage:
    from ship_to_song import ShipToSong
    from vessel_instrument import VesselInstrument, VesselMode

    vessel = VesselInstrument()
    vessel.update(rpm=1800, depth=40, sea_state=4, heading=180, speed=7.5)

    converter = ShipToSong()
    prompt = converter.generate_prompt(vessel.state)
    # Feed prompt to MMX: mmx music --prompt "..." --duration 45
"""

from __future__ import annotations
import json
import math
import subprocess
import os
from typing import Optional, Dict, List
from dataclasses import dataclass

from vessel_instrument import VesselInstrument, VesselState, VesselMode, MusicalParameters
from telemetry_to_midi import (
    MIDI_NOTE_NAMES,
    rpm_to_bass_frequency,
    rpm_to_bass_midi_note,
)


# ─── Mood / Genre Mapping ───────────────────────────────────────────────────

# Map vessel mode + conditions to musical genre/style
GENRE_MAP: Dict[str, Dict] = {
    "docked": {
        "genre": "ambient drone",
        "energy": "minimal",
        "instruments": ["sustained bass", "soft pads", "distant harbor sounds"],
        "emotion": "stillness before the day",
    },
    "departing": {
        "genre": "folk maritime with building energy",
        "energy": "rising",
        "instruments": ["upright bass", "accordion", "fiddle"],
        "emotion": "hopeful departure, morning light",
    },
    "transit": {
        "genre": "motorik krautrock",
        "energy": "driving steady",
        "instruments": ["repetitive bass", "hi-hat", "synth pulse"],
        "emotion": "endless forward motion",
    },
    "fishing": {
        "genre": "modal jazz",
        "energy": "focused, patient",
        "instruments": ["double bass", "brushed drums", "muted trumpet"],
        "emotion": "concentration, the line between water and work",
    },
    "hauling": {
        "genre": "industrial blues",
        "energy": "intense bursts",
        "instruments": ["distorted bass", "mechanical percussion", "slide guitar"],
        "emotion": "physical labor, winch pulling",
    },
    "returning": {
        "genre": "roots americana",
        "energy": "winding down",
        "instruments": ["warm bass", "fingerpicked guitar", "harmonica"],
        "emotion": "tired satisfaction, heading home",
    },
    "emergency": {
        "genre": "dark ambient with alarm tones",
        "energy": "high tension",
        "instruments": ["sub-bass", "dissonant strings", "alarm pulses"],
        "emotion": "danger, urgency",
    },
}

# Sea state modifiers
SEA_STATE_MODIFIERS: Dict[int, str] = {
    0: "glassy calm, near-silent, suspended in space",
    1: "gentle breeze, relaxed swing, warm reverb",
    2: "light chop, easy syncopation, open sound",
    3: "moderate breeze, steady groove, clear mix",
    4: "rough, tighter rhythms, edges sharper",
    5: "very rough, aggressive dynamics, distortion creeping in",
    6: "high sea, polyrhythmic tension, bass pressing hard",
    7: "gale, near-chaotic, walls of sound",
    8: "strong gale, overwhelming texture, drowning the melody",
    9: "storm, total chaos, noise and sub-frequency pressure",
}


# ─── Song Prompt Builder ────────────────────────────────────────────────────

@dataclass
class SongPrompt:
    """A generated music prompt for MMX (or any text-to-music model)."""
    prompt: str
    negative_prompt: str = ""
    duration_seconds: int = 45
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def __str__(self) -> str:
        return self.prompt


class ShipToSong:
    """Converts vessel state into music generation prompts."""

    def __init__(self):
        self.vessel = VesselInstrument()

    def generate_prompt(
        self,
        vessel_state: VesselState,
        duration_seconds: int = 45,
        extra_context: str = "",
    ) -> SongPrompt:
        """Generate a text-to-music prompt from vessel telemetry.

        The prompt captures the ship's current state as music:
        - Engine RPM → bass character
        - Depth → harmonic complexity
        - Sea state → rhythmic intensity
        - Heading → stereo placement
        - Speed → tempo
        """
        self.vessel.state = vessel_state
        params = self.vessel.get_musical_parameters()
        mode_key = vessel_state.mode.value

        # Get genre mapping
        genre_info = GENRE_MAP.get(mode_key, GENRE_MAP["transit"])

        # Get sea state modifier
        sea_level = int(min(9, max(0, round(vessel_state.sea_state))))
        sea_modifier = SEA_STATE_MODIFIERS.get(sea_level, "")

        # Build prompt components
        bass_note_name = MIDI_NOTE_NAMES[params.bass_note % 12] + str(params.bass_note // 12 - 1)
        bass_freq = params.bass_frequency

        # Tempo description
        tempo_word = self._tempo_descriptor(params.tempo_bpm)

        # Harmony description
        harmony_desc = params.harmony_label

        # Mood
        mood = params.mood

        # Build the prompt
        prompt_parts = []

        # Core description
        prompt_parts.append(
            f"{genre_info['genre']} piece at {params.tempo_bpm:.0f} BPM, {tempo_word}. "
            f"Fundamental bass at {bass_note_name} ({bass_freq:.0f}Hz), "
            f"{self._bass_descriptor(vessel_state.rpm)}."
        )

        # Harmony from depth
        prompt_parts.append(
            f"Harmonic texture: {harmony_desc.lower()}. "
            f"Water depth is {vessel_state.depth:.0f} fathoms."
        )

        # Rhythm from sea state
        prompt_parts.append(
            f"Rhythmic feel: {sea_modifier}. "
            f"Sea state {sea_level} Beaufort."
        )

        # Instruments
        instruments = genre_info["instruments"]
        prompt_parts.append(
            f"Instrumentation: {', '.join(instruments)}."
        )

        # Emotion / vessel mood
        prompt_parts.append(
            f"Mood: {genre_info['emotion']}. Currently {mood}."
        )

        # Intensity
        intensity_pct = params.intensity
        intensity_desc = self._intensity_descriptor(intensity_pct)
        prompt_parts.append(f"Energy level: {intensity_desc} ({intensity_pct:.0%}).")

        # Pan / spatial
        pan_side = "left" if params.pan < 50 else "right" if params.pan > 78 else "centered"
        prompt_parts.append(
            f"Stereo image: vessel heading {vessel_state.heading:.0f}°, "
            f"sound positioned {pan_side}."
        )

        # Mode-specific flavor
        if mode_key == "fishing":
            prompt_parts.append(
                "The music should feel like patience rewarded — "
                "long tones with occasional active passages as gear works."
            )
        elif mode_key == "hauling":
            prompt_parts.append(
                "Industrial weight. Mechanical sounds of winches and cables "
                "woven into the rhythm."
            )
        elif mode_key == "transit":
            prompt_parts.append(
                "Hypnotic repetition. The engine is a heartbeat. "
                "The ocean scrolls past."
            )
        elif mode_key == "departing":
            prompt_parts.append(
                "Optimistic energy. The harbor falls behind. Open water ahead."
            )
        elif mode_key == "returning":
            prompt_parts.append(
                "Weariness and warmth. The catch is in the hold. "
                "Home lights on the horizon."
            )

        # Extra context
        if extra_context:
            prompt_parts.append(extra_context)

        # Duration
        prompt_parts.append(
            f"Duration: {duration_seconds} seconds. "
            f"No vocals. Instrumental only."
        )

        prompt = " ".join(prompt_parts)

        # Negative prompt
        negative = (
            "vocals, lyrics, singing, voice, speech, "
            "optimistic pop, dance beat, electronic dance music, "
            "cliché sea shanty, cartoon pirate music"
        )

        return SongPrompt(
            prompt=prompt,
            negative_prompt=negative,
            duration_seconds=duration_seconds,
            metadata={
                "vessel_mode": mode_key,
                "bass_note": bass_note_name,
                "bass_frequency_hz": bass_freq,
                "tempo_bpm": params.tempo_bpm,
                "time_signature": f"{params.time_signature[0]}/{params.time_signature[1]}",
                "harmony_label": harmony_desc,
                "mood": mood,
                "intensity": params.intensity,
                "sea_state": vessel_state.sea_state,
                "depth_fathoms": vessel_state.depth,
                "rpm": vessel_state.rpm,
                "speed_knots": vessel_state.speed,
                "heading": vessel_state.heading,
                "musical_parameters": params.to_dict(),
            },
        )

    def _tempo_descriptor(self, bpm: float) -> str:
        if bpm < 70:
            return "very slow, heavy"
        elif bpm < 90:
            return "slow, deliberate"
        elif bpm < 110:
            return "moderate, steady"
        elif bpm < 130:
            return "driving, purposeful"
        elif bpm < 150:
            return "fast, urgent"
        return "very fast, intense"

    def _bass_descriptor(self, rpm: float) -> str:
        if rpm < 700:
            return "deep idling drone, barely moving"
        elif rpm < 1200:
            return "low steady pulse, the engine breathing"
        elif rpm < 1800:
            return "firm driving bass, engine under load"
        elif rpm < 2400:
            return "heavy grinding bass, engine working hard"
        return "hammering bass, engine near redline"

    def _intensity_descriptor(self, intensity: float) -> str:
        if intensity < 0.15:
            return "minimal, barely there"
        elif intensity < 0.3:
            return "low, contemplative"
        elif intensity < 0.5:
            return "moderate, engaged"
        elif intensity < 0.7:
            return "high, pressing"
        return "maximum, overwhelming"

    # ── MMX Integration ──

    def generate_with_mmx(
        self,
        vessel_state: VesselState,
        output_path: str,
        duration_seconds: int = 45,
        mmx_path: str = "mmx",
    ) -> Dict:
        """Generate music using MMX CLI from the vessel state.

        This calls the MMX music generation tool. Returns metadata about the
        generation.
        """
        song = self.generate_prompt(vessel_state, duration_seconds)

        # Build MMX command
        cmd = [
            mmx_path,
            "music",
            "--prompt", song.prompt,
            "--duration", str(duration_seconds),
            "--output", output_path,
        ]

        result = {
            "command": " ".join(cmd),
            "prompt": song.prompt,
            "metadata": song.metadata,
            "output_path": output_path,
            "success": False,
        }

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 min max
            )
            result["stdout"] = proc.stdout
            result["stderr"] = proc.stderr
            result["returncode"] = proc.returncode
            result["success"] = proc.returncode == 0
        except FileNotFoundError:
            result["error"] = f"MMX not found at {mmx_path}"
        except subprocess.TimeoutExpired:
            result["error"] = "MMX generation timed out"

        return result

    def batch_generate(
        self,
        vessel_states: List[VesselState],
        output_dir: str,
        duration_seconds: int = 30,
        mmx_path: str = "mmx",
    ) -> List[Dict]:
        """Generate music for a sequence of vessel states (e.g., a full trip).

        Each state produces one short piece. Together they form a sonic
        journal of the voyage.
        """
        os.makedirs(output_dir, exist_ok=True)
        results = []

        for i, state in enumerate(vessel_states):
            filename = f"track_{i:03d}_{state.mode.value}.mp3"
            output_path = os.path.join(output_dir, filename)
            result = self.generate_with_mmx(
                state, output_path, duration_seconds, mmx_path
            )
            result["track_number"] = i
            results.append(result)

        # Save manifest
        manifest_path = os.path.join(output_dir, "manifest.json")
        with open(manifest_path, "w") as f:
            json.dump(results, f, indent=2)

        return results

    # ── Musical State Report ──

    def state_report(self, vessel_state: VesselState) -> str:
        """Human-readable report of how the vessel translates to music."""
        song = self.generate_prompt(vessel_state)
        params = self.vessel.get_musical_parameters()

        lines = [
            "═══ FV Eileen → Music Translation ═══",
            "",
            f"  Mode:       {vessel_state.mode.value}",
            f"  Engine:     {vessel_state.rpm:.0f} RPM → bass at {params.bass_frequency:.1f} Hz "
            f"({MIDI_NOTE_NAMES[params.bass_note % 12]}{params.bass_note // 12 - 1})",
            f"  Depth:      {vessel_state.depth:.0f} fathoms → {params.harmony_label}",
            f"  Sea State:  {vessel_state.sea_state:.1f} → "
            f"{params.rhythm_density:.0%} rhythm density",
            f"  Heading:    {vessel_state.heading:.0f}° → pan {params.pan}/127",
            f"  Speed:      {vessel_state.speed:.1f} kt → {params.tempo_bpm:.1f} BPM, "
            f"{params.time_signature[0]}/{params.time_signature[1]}",
            f"  Mood:       {params.mood}",
            f"  Intensity:  {params.intensity:.0%}",
            "",
            "─── Generated Prompt ───",
            "",
            song.prompt,
        ]

        return "\n".join(lines)


# ─── CLI ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from telemetry_simulator import TelemetrySimulator

    converter = ShipToSong()
    sim = TelemetrySimulator(seed=42)

    print("═══ FV Eileen — Ship to Song ═══\n")

    # Generate prompts for different vessel states
    states = [
        VesselState(rpm=600, depth=3, sea_state=1, heading=90, speed=1.5, mode=VesselMode.DOCKED),
        VesselState(rpm=1800, depth=25, sea_state=3, heading=180, speed=7.5, mode=VesselMode.DEPARTING),
        VesselState(rpm=2400, depth=50, sea_state=4, heading=225, speed=8.0, mode=VesselMode.TRANSIT),
        VesselState(rpm=900, depth=75, sea_state=3, heading=45, speed=2.5, mode=VesselMode.FISHING),
        VesselState(rpm=1600, depth=80, sea_state=5, heading=270, speed=1.0, mode=VesselMode.HAULING),
        VesselState(rpm=1400, depth=10, sea_state=2, heading=315, speed=5.5, mode=VesselMode.RETURNING),
    ]

    for state in states:
        print(converter.state_report(state))
        print(f"\n{'─' * 60}\n")

    # Show a sample prompt in full
    print("\n═══ Sample Full Prompt (Fishing) ═══\n")
    fishing_state = states[3]
    song = converter.generate_prompt(fishing_state, duration_seconds=45)
    print(f"Prompt:\n  {song.prompt}")
    print(f"\nNegative:\n  {song.negative_prompt}")
    print(f"\nDuration: {song.duration_seconds}s")
    print(f"\nMetadata: {json.dumps(song.metadata, indent=2)}")
