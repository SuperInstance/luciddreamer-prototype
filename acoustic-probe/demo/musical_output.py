#!/usr/bin/env python3
"""
musical_output.py — Converts FV Eileen telemetry to musical parameters in real-time.

Reads telemetry from the shared state file (or stdin) and outputs:
- Real-time musical parameter mapping (every 5s)
- MMX music generation prompts (every 30s)

Engine RPM → bass frequency
Depth → harmonic complexity
Sea state → rhythmic jitter
Speed → tempo
Heading → stereo pan

Usage:
    python3 musical_output.py                          # Reads shared state file
    python3 musical_output.py --input telemetry.jsonl  # Reads from file
    python3 musical_output.py --live                   # Reads stdin line-by-line
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from typing import Optional


# ─── Acoustic Probe Mapping Constants ───────────────────────────────────────
# These mirror the core acoustic-probe spec.

MIDI_NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Bass: RPM 0-3000 → frequency 55Hz (A1) to 220Hz (A3)
BASS_FREQ_MIN = 55.0
BASS_FREQ_MAX = 220.0

# Harmony tiers by depth (fathoms)
HARMONY_TIERS = [
    (10,  "Root drone",              "single sustained note"),
    (25,  "Root + fifth",            "open, anchored"),
    (40,  "Added octave",            "widening"),
    (55,  "Major 7th chord",         "complex, colorful"),
    (70,  "Minor 9th + 11th",        "tense, deep water"),
    (82,  "Chromatic clusters",      "dissonant, abyssal"),
    (100, "Full chromatic fog",      "dense, overwhelming"),
]

# Sea state → rhythm description
SEA_RHYTHM = {
    (0, 1):   ("steady 4/4",          "near-silent, barely pulsing"),
    (1, 2):   ("gentle swing",        "relaxed backbeat"),
    (2, 3):   ("light syncopation",   "off-beat 16ths"),
    (3, 4):   ("driving 8th notes",   "forward momentum"),
    (4, 5):   ("heavy syncopation",   "edges sharpening"),
    (5, 6):   ("polyrhythmic",        "competing pulses"),
    (6, 7):   ("near-chaotic",        "walls of rhythm"),
    (7, 8):   ("storm rhythm",        "overwhelming texture"),
    (8, 9):   ("total chaos",         "noise and pressure"),
}

# Vessel mode → musical genre
MODE_GENRE = {
    "departing": ("folk maritime building energy",  "upright bass, accordion, fiddle"),
    "transit":   ("motorik krautrock",               "repetitive bass, hi-hat, synth pulse"),
    "fishing":   ("modal jazz",                      "double bass, brushed drums, muted trumpet"),
    "returning": ("roots americana winding down",    "warm bass, fingerpicked guitar, harmonica"),
}


# ─── Core Mapping Functions ─────────────────────────────────────────────────

def rpm_to_bass_freq(rpm: float) -> float:
    """Map RPM (0-3000) to bass frequency (55-220 Hz) exponentially."""
    rpm = max(0.0, min(3000.0, rpm))
    ratio = rpm / 3000.0
    return BASS_FREQ_MIN * (BASS_FREQ_MAX / BASS_FREQ_MIN) ** ratio


def rpm_to_bass_note(rpm: float) -> tuple:
    """Returns (note_name, midi_note, frequency)."""
    freq = rpm_to_bass_freq(rpm)
    midi = round(69 + 12 * math.log2(freq / 440.0))
    midi = max(21, min(127, midi))
    name = f"{MIDI_NOTE_NAMES[midi % 12]}{midi // 12 - 1}"
    return name, midi, freq


def depth_to_harmony(depth: float) -> tuple:
    """Returns (label, description)."""
    for threshold, label, desc in HARMONY_TIERS:
        if depth < threshold:
            return label, desc
    return HARMONY_TIERS[-1][1], HARMONY_TIERS[-1][2]


def sea_state_to_rhythm(sea: float) -> tuple:
    """Returns (pattern_name, description)."""
    sea_int = max(0, min(9, int(round(sea))))
    for (lo, hi), (pattern, desc) in SEA_RHYTHM.items():
        if lo <= sea_int <= hi:
            return pattern, desc
    return SEA_RHYTHM[(8, 9)]


def speed_to_tempo(speed: float) -> float:
    """Map speed (knots) to BPM (60-160)."""
    return 60.0 + min(1.0, speed / 20.0) * 100.0


def speed_to_key(speed: float) -> str:
    """Vessel speed affects musical mode."""
    if speed < 3.0:
        return "minor"   # Slow = reflective
    elif speed > 8.0:
        return "mixolydian"  # Fast = driving, modal
    return "major"       # Medium = open


def heading_to_pan(heading: float) -> tuple:
    """Returns (pan_value, description)."""
    h = heading % 360.0
    if h <= 180:
        pan = int((h / 180.0) * 127)
    else:
        pan = int(((360.0 - h) / 180.0) * 127)
    if pan < 40:
        side = "hard left"
    elif pan < 55:
        side = "left"
    elif pan <= 80:
        side = "center"
    elif pan <= 100:
        side = "right"
    else:
        side = "hard right"
    return pan, side


# ─── Musical State ──────────────────────────────────────────────────────────

def compute_musical_state(tele: dict) -> dict:
    """Convert a telemetry dict into musical parameters."""
    rpm = tele.get("rpm", 0)
    depth = tele.get("depth_fathoms", tele.get("depth", 0))
    sea = tele.get("sea_state", 0)
    speed = tele.get("speed_knots", tele.get("speed", 0))
    heading = tele.get("heading", 0)
    phase = tele.get("phase", "transit")

    note_name, midi_note, freq = rpm_to_bass_note(rpm)
    harm_label, harm_desc = depth_to_harmony(depth)
    rhythm_pattern, rhythm_desc = sea_state_to_rhythm(sea)
    tempo = speed_to_tempo(speed)
    key_mode = speed_to_key(speed)
    pan_val, pan_desc = heading_to_pan(heading)

    # Root key from bass note
    root_note = MIDI_NOTE_NAMES[midi_note % 12]

    # Intensity
    intensity = min(1.0,
        (rpm / 3000.0) * 0.35 +
        (sea / 9.0) * 0.30 +
        min(1.0, depth / 100.0) * 0.15 +
        min(1.0, speed / 15.0) * 0.20
    )

    # Genre
    genre, instruments = MODE_GENRE.get(phase, MODE_GENRE["transit"])

    # Mood
    mood_map = {
        "departing": "optimistic, morning energy",
        "transit": "steadfast, hypnotic",
        "fishing": "contemplative, focused patience",
        "returning": "weary warmth, homeward",
    }
    mood = mood_map.get(phase, "neutral")

    # What the ship sounds like
    sound_desc = _vessel_sound(rpm, depth, sea, phase)

    return {
        "bass_note": note_name,
        "bass_midi": midi_note,
        "bass_frequency_hz": round(freq, 2),
        "root_key": root_note,
        "mode": key_mode,
        "key": f"{root_note} {key_mode}",
        "harmony_label": harm_label,
        "harmony_description": harm_desc,
        "rhythm_pattern": rhythm_pattern,
        "rhythm_description": rhythm_desc,
        "tempo_bpm": round(tempo, 1),
        "time_signature": "3/4" if speed < 3 else "6/8" if speed > 8 else "4/4",
        "pan": pan_val,
        "pan_description": pan_desc,
        "intensity": round(intensity, 3),
        "genre": genre,
        "instruments": instruments,
        "mood": mood,
        "vessel_sound": sound_desc,
        "phase": phase,
    }


def _vessel_sound(rpm, depth, sea, phase) -> str:
    """Human-readable description of what the ship sounds like right now."""
    parts = []

    # Engine sound
    if rpm < 700:
        parts.append("a low diesel idle, barely audible")
    elif rpm < 1200:
        parts.append("a steady engine hum")
    elif rpm < 1800:
        parts.append("a firm driving engine note")
    elif rpm < 2400:
        parts.append("a hard-working engine under load")
    else:
        parts.append("a hammering engine near full power")

    # Depth influence
    if depth < 15:
        parts.append("over shallow clicking water")
    elif depth < 40:
        parts.append("over mid-depth open water")
    elif depth < 65:
        parts.append("over deep green water")
    else:
        parts.append("over abyssal depth")

    # Sea influence
    if sea < 2:
        parts.append("on a glassy sea")
    elif sea < 4:
        parts.append("on a gentle chop")
    elif sea < 6:
        parts.append("in rough seas")
    else:
        parts.append("in heavy weather")

    return ", ".join(parts).capitalize()


# ─── MMX Prompt Generation ──────────────────────────────────────────────────

def generate_mmx_prompt(tele: dict, musical: dict, duration: int = 30) -> str:
    """Generate a text-to-music prompt for MMX based on current vessel state."""
    phase = tele.get("phase", "transit")
    rpm = tele.get("rpm", 0)
    depth = tele.get("depth_fathoms", tele.get("depth", 0))
    sea = tele.get("sea_state", 0)
    speed = tele.get("speed_knots", tele.get("speed", 0))

    tempo_desc = _tempo_word(musical["tempo_bpm"])
    bass_desc = _bass_word(rpm)
    sea_int = max(0, min(9, int(round(sea))))
    sea_word = SEA_RHYTHM.get((max(0, sea_int-1), sea_int), SEA_RHYTHM[(3, 4)])[1]

    prompt = (
        f"{musical['genre']} piece at {musical['tempo_bpm']:.0f} BPM, {tempo_desc}. "
        f"Fundamental bass at {musical['bass_note']} ({musical['bass_frequency_hz']:.0f}Hz), {bass_desc}. "
        f"Harmonic texture: {musical['harmony_description']}. "
        f"Depth {depth:.0f} fathoms. "
        f"Rhythmic feel: {sea_word}. Sea state {sea_int} Beaufort. "
        f"Instrumentation: {musical['instruments']}. "
        f"Mood: {musical['mood']}. "
        f"Energy level: {musical['intensity']:.0%}. "
        f"Key: {musical['key']}, {musical['time_signature']}. "
        f"Stereo: vessel heading {tele.get('heading', 0):.0f}°, positioned {musical['pan_description']}. "
    )

    # Phase-specific flavor
    if phase == "fishing":
        prompt += "The music should feel like patience rewarded — long tones with occasional active passages as gear works. "
    elif phase == "transit":
        prompt += "Hypnotic repetition. The engine is a heartbeat. The ocean scrolls past. "
    elif phase == "departing":
        prompt += "Optimistic energy. The harbor falls behind. Open water ahead. "
    elif phase == "returning":
        prompt += "Weariness and warmth. The catch is in the hold. Home lights on the horizon. "

    prompt += f"Duration: {duration} seconds. No vocals. Instrumental only."

    return prompt


def _tempo_word(bpm: float) -> str:
    if bpm < 70:   return "very slow, heavy"
    elif bpm < 90:  return "slow, deliberate"
    elif bpm < 110: return "moderate, steady"
    elif bpm < 130: return "driving, purposeful"
    elif bpm < 150: return "fast, urgent"
    return "very fast, intense"


def _bass_word(rpm: float) -> str:
    if rpm < 700:   return "deep idling drone, barely moving"
    elif rpm < 1200: return "low steady pulse, the engine breathing"
    elif rpm < 1800: return "firm driving bass, engine under load"
    elif rpm < 2400: return "heavy grinding bass, engine working hard"
    return "hammering bass, engine near redline"


# ─── Output ─────────────────────────────────────────────────────────────────

MUSICAL_STATE_FILE = os.path.join(os.path.dirname(__file__), "musical_state.json")
MMX_PROMPT_FILE = os.path.join(os.path.dirname(__file__), "mmx_prompt.txt")


def write_musical_state(musical: dict):
    """Write current musical state for the web UI."""
    with open(MUSICAL_STATE_FILE, "w") as f:
        json.dump(musical, f, indent=2)


def write_mmx_prompt(prompt: str):
    """Write current MMX prompt for external consumption."""
    with open(MMX_PROMPT_FILE, "w") as f:
        f.write(prompt)


# ─── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="FV Eileen — Telemetry to Musical Parameters"
    )
    parser.add_argument(
        "--input", "-i",
        help="Input JSONL telemetry file (default: read shared state file)",
        default=None,
    )
    parser.add_argument(
        "--live", action="store_true",
        help="Read telemetry from stdin (one JSON per line)",
    )
    parser.add_argument(
        "--interval", type=int, default=5,
        help="Polling interval in seconds for shared state mode (default: 5)",
    )
    parser.add_argument(
        "--prompt-interval", type=int, default=30,
        help="MMX prompt output interval in seconds (default: 30)",
    )
    args = parser.parse_args()

    shared_state = os.path.join(os.path.dirname(__file__), "telemetry.json")

    last_prompt_time = 0
    last_telemetry = None

    print(f"FV Eileen — Musical Output Converter", file=sys.stderr)
    print(f"  Input: {'stdin' if args.live else args.input or shared_state}", file=sys.stderr)
    print(f"  Musical state: {MUSICAL_STATE_FILE}", file=sys.stderr)
    print(f"  MMX prompts: {MMX_PROMPT_FILE}", file=sys.stderr)
    print(file=sys.stderr)

    if args.live:
        # Read from stdin
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                tele = json.loads(line)
            except json.JSONDecodeError:
                continue

            musical = compute_musical_state(tele)
            output = {**tele, "musical": musical}
            print(json.dumps(output))
            sys.stdout.flush()

            write_musical_state(musical)

            elapsed = tele.get("elapsed", 0)
            if elapsed - last_prompt_time >= args.prompt_interval:
                prompt = generate_mmx_prompt(tele, musical)
                write_mmx_prompt(prompt)
                print(f"[MMX PROMPT @ {elapsed:.0f}s] {prompt[:200]}...", file=sys.stderr)
                last_prompt_time = elapsed

    elif args.input:
        # Read from file
        with open(args.input) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    tele = json.loads(line)
                except json.JSONDecodeError:
                    continue

                musical = compute_musical_state(tele)
                output = {**tele, "musical": musical}
                print(json.dumps(output))
                sys.stdout.flush()

    else:
        # Poll shared state file
        print("Polling shared state file... (Ctrl+C to stop)", file=sys.stderr)
        while True:
            try:
                if os.path.exists(shared_state):
                    mtime = os.path.getmtime(shared_state)
                    with open(shared_state) as f:
                        try:
                            tele = json.load(f)
                        except json.JSONDecodeError:
                            tele = None

                    if tele and tele != last_telemetry:
                        last_telemetry = tele
                        musical = compute_musical_state(tele)
                        output = {**tele, "musical": musical}
                        print(json.dumps(output))
                        sys.stdout.flush()

                        write_musical_state(musical)

                        elapsed = tele.get("elapsed", 0)
                        if elapsed - last_prompt_time >= args.prompt_interval:
                            prompt = generate_mmx_prompt(tele, musical)
                            write_mmx_prompt(prompt)
                            print(f"\n[MMX PROMPT @ {elapsed:.0f}s]", file=sys.stderr)
                            print(f"  {prompt}", file=sys.stderr)
                            last_prompt_time = elapsed

                time.sleep(args.interval)

            except KeyboardInterrupt:
                print("\n[Musical output stopped]", file=sys.stderr)
                break


if __name__ == "__main__":
    main()
