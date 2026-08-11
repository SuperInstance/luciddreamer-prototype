#!/usr/bin/env python3
"""
Generate audio personas for Hermes Protean Identity System.
Creates distinct ambient audio textures for each persona using DSP synthesis.

Since the primary generation pipeline (MMX) is at quota, we synthesize
procedurally — each track is a unique sonic fingerprint matching the persona.

Output: 3 MP3 files, ~15 seconds each.
"""
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, filtfilt
import subprocess
import os
import struct

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_RATE = 44100
DURATION = 15.0  # seconds


def save_as_mp3(samples, filepath, sr=SAMPLE_RATE):
    """Save numpy float array as WAV then convert to MP3 via ffmpeg."""
    # Convert to 16-bit PCM
    pcm = np.clip(samples, -1.0, 1.0)
    pcm = (pcm * 32767).astype(np.int16)
    wav_path = filepath.replace(".mp3", ".wav")
    wavfile.write(wav_path, sr, pcm)
    
    # Convert to MP3
    subprocess.run(
        ["ffmpeg", "-y", "-i", wav_path, "-codec:a", "libmp3lame",
         "-b:a", "192k", filepath],
        capture_output=True, check=True
    )
    os.remove(wav_path)
    print(f"  ✅ Generated {os.path.basename(filepath)} ({os.path.getsize(filepath)} bytes)")


def adsr_envelope(n, attack=0.05, decay=0.1, sustain=0.7, release=0.2, sr=SAMPLE_RATE):
    """ADSR envelope."""
    a = int(attack * sr)
    d = int(decay * sr)
    r = int(release * sr)
    s = n - a - d - r
    if s < 0:
        s = 0
    
    env = np.concatenate([
        np.linspace(0, 1, a, endpoint=False),
        np.linspace(1, sustain, d, endpoint=False),
        np.ones(s) * sustain,
        np.linspace(sustain, 0, r, endpoint=False),
    ])
    if len(env) < n:
        env = np.pad(env, (0, n - len(env)))
    return env[:n]


def generate_architect():
    """
    The Architect: structured ambient, steady tempo, geometric harmonies.
    - Perfect fourths and fifths (stable, architectural intervals)
    - Crystalline bell-like tones
    - Steady rhythmic pulse
    - Clean, precise, mathematical
    """
    t = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION), endpoint=False)
    
    # Root frequencies: A2, E3, A3 (perfect fifth + fourth)
    root_freqs = [110.0, 164.81, 220.0]
    
    audio = np.zeros_like(t)
    
    # Sustained drone bed
    for freq in root_freqs:
        audio += 0.15 * np.sin(2 * np.pi * freq * t) * np.exp(-0.5 * t / DURATION)
    
    # Geometric bell tones — steady pulse every 1.5s
    pulse_interval = 1.5
    bell_freqs = [440.0, 554.37, 659.25, 880.0]  # A4, C#5, E5, A5 — A major triad
    
    for i in range(int(DURATION / pulse_interval) + 1):
        start = i * pulse_interval
        start_sample = int(start * SAMPLE_RATE)
        remaining = len(t) - start_sample
        if remaining <= 0:
            continue
        
        # Each bell uses a different frequency from the set, cycling
        freq = bell_freqs[i % len(bell_freqs)]
        bell_t = t[:remaining]
        
        # Bell: additive synthesis with fast decay
        bell = (
            1.0 * np.sin(2 * np.pi * freq * bell_t) +
            0.5 * np.sin(2 * np.pi * freq * 2 * bell_t) +
            0.3 * np.sin(2 * np.pi * freq * 3 * bell_t)
        )
        env = np.exp(-3.0 * bell_t)
        bell = bell * env * 0.2
        audio[start_sample:start_sample + remaining] += bell
    
    # Subtle rhythmic tick (like a metronome)
    tick_interval = 0.75  # 80 BPM
    for i in range(int(DURATION / tick_interval) + 1):
        start_sample = int(i * tick_interval * SAMPLE_RATE)
        if start_sample < len(audio):
            tick_len = int(0.02 * SAMPLE_RATE)
            end = min(start_sample + tick_len, len(audio))
            tick = 0.08 * np.random.randn(end - start_sample)
            tick_env = np.exp(-50 * np.linspace(0, 1, end - start_sample))
            audio[start_sample:end] += tick * tick_env
    
    # Normalize
    audio = audio / np.max(np.abs(audio)) * 0.7
    return audio


def generate_jester():
    """
    The Jester: playful jazz, chromatic, high energy, surprising.
    - Chromatic runs and unexpected intervals
    - Syncopated rhythm
    - Bright, buzzy timbres (sawtooth-like)
    - Glissandos and musical "winks"
    """
    t = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION), endpoint=False)
    audio = np.zeros_like(t)
    
    # Chromatic scale frequencies
    base_freq = 261.63  # C4
    chromatic_ratios = [2 ** (i / 12) for i in range(-2, 15)]
    
    # Syncopated melodic phrases
    note_duration = 0.25  # 16th notes at 120 BPM
    current_time = 0.0
    note_idx = 0
    
    while current_time < DURATION:
        # Pick chromatic notes with some pattern
        # Create a playful pattern: up, skip, down, chromatic run
        patterns = [
            [0, 2, 4, 5, 7, 5, 4, 2],  # major arpeggio with dips
            [0, 1, 2, 3, 4, 5, 6, 7],  # chromatic run up
            [7, 5, 3, 1, 0, 1, 3, 5],  # jazzy chromatic descent
            [0, 3, 6, 10, 6, 3, 0, 3], # bluesy
        ]
        pattern = patterns[note_idx % len(patterns)]
        
        for interval in pattern:
            if current_time >= DURATION:
                break
            
            freq = base_freq * (2 ** (interval / 12))
            start_sample = int(current_time * SAMPLE_RATE)
            remaining = len(audio) - start_sample
            if remaining <= 0:
                break
            
            note_t = t[:remaining]
            # Buzzy, playful timbre
            note = (
                0.4 * np.sin(2 * np.pi * freq * note_t) +
                0.3 * np.sign(np.sin(2 * np.pi * freq * note_t)) * 0.3 +  # square-ish
                0.2 * np.sin(2 * np.pi * freq * 1.5 * note_t)  # perfect fifth overtone
            )
            
            # Short envelope with a little "bounce"
            n = min(int(note_duration * SAMPLE_RATE), remaining)
            env = np.exp(-5 * note_t[:n])
            # Add a tiny pitch bend at the start for playfulness
            bend = 1 + 0.02 * np.sin(2 * np.pi * 8 * note_t[:n])
            
            audio[start_sample:start_sample + n] += note[:n] * env * 0.15
            current_time += note_duration
            note_idx += 1
        
        # Brief pause between phrases (syncopation)
        current_time += note_duration * np.random.choice([0.5, 1.0, 1.5, 2.0])
    
    # Add a background "sparkle" layer
    sparkle = 0.05 * np.random.randn(len(t))
    # High-pass-ish by modulating
    sparkle_env = np.abs(np.sin(2 * np.pi * 0.7 * t))
    audio += sparkle * sparkle_env
    
    # Occasional "wink" — quick frequency sweep
    for wink_time in [3.2, 7.8, 11.5]:
        start = int(wink_time * SAMPLE_RATE)
        wink_len = int(0.15 * SAMPLE_RATE)
        end = min(start + wink_len, len(audio))
        wink_t = np.linspace(0, 0.15, end - start)
        wink_freq = 2000 * (1 + 3 * wink_t / 0.15)  # rising sweep
        wink = 0.15 * np.sin(2 * np.pi * wink_freq * wink_t / 5) * np.exp(-5 * wink_t)
        audio[start:end] += wink
    
    audio = audio / np.max(np.abs(audio)) * 0.65
    return audio


def generate_navigator():
    """
    The Navigator: deep ambient drone, low frequency, ocean-like.
    - Very low frequency drone (feels like pressure)
    - Slow-swelling waves of sound
    - Bioluminescent shimmer (high, quiet, rare)
    - Vast, patient, deep
    """
    t = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION), endpoint=False)
    
    # Deep drone bed: D1, A1, D2
    drone_freqs = [36.71, 55.0, 73.42]
    
    audio = np.zeros_like(t)
    
    for freq in drone_freqs:
        # Slow amplitude modulation for "ocean wave" feel
        wave_lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * t + np.random.random() * np.pi)
        # Add slight detuning for thickness
        detune = 0.3 * np.sin(2 * np.pi * freq * 1.002 * t)
        fundamental = np.sin(2 * np.pi * freq * t)
        audio += 0.25 * (fundamental + detune) * wave_lfo
    
    # Sub-bass pressure layer
    sub = 0.15 * np.sin(2 * np.pi * 18.0 * t)  # below hearing, felt as pressure
    audio += sub * (0.5 + 0.5 * np.sin(2 * np.pi * 0.05 * t))
    
    # Bioluminescent shimmer — rare high tones that appear and fade
    shimmer_times = [2.1, 5.8, 9.3, 12.7]
    for st in shimmer_times:
        start = int(st * SAMPLE_RATE)
        remaining = len(t) - start
        if remaining <= 0:
            continue
        
        shimmer_t = t[:remaining]
        # Random high frequency in the upper register
        shimmer_freq = np.random.choice([1318.51, 1567.98, 1760.0, 2093.0])  # E6, G6, A6, C7
        shimmer = (
            0.08 * np.sin(2 * np.pi * shimmer_freq * shimmer_t) +
            0.04 * np.sin(2 * np.pi * shimmer_freq * 2 * shimmer_t)
        )
        # Very slow swell in and out
        swell_len = min(int(3.0 * SAMPLE_RATE), remaining)
        env = np.zeros(remaining)
        env[:swell_len] = np.sin(np.pi * np.linspace(0, 1, swell_len)) ** 2
        audio[start:] += shimmer * env * 0.6
    
    # Deep ocean noise bed (filtered noise as currents)
    noise = np.random.randn(len(t))
    # Simple low-pass via moving average
    kernel_size = 200
    kernel = np.ones(kernel_size) / kernel_size
    noise_filtered = np.convolve(noise, kernel, mode="same")
    noise_env = 0.5 + 0.5 * np.sin(2 * np.pi * 0.04 * t)
    audio += 0.12 * noise_filtered * noise_env
    
    # Normalize
    audio = audio / np.max(np.abs(audio)) * 0.55
    return audio


def main():
    print("🎨 Generating Hermes audio personas...\n")
    
    print("  The Architect — structured ambient, geometric harmonies")
    save_as_mp3(generate_architect(), os.path.join(OUT_DIR, "hermes-architect.mp3"))
    
    print("  The Jester — playful chromatic jazz")
    save_as_mp3(generate_jester(), os.path.join(OUT_DIR, "hermes-jester.mp3"))
    
    print("  The Navigator — deep ambient drone, ocean-like")
    save_as_mp3(generate_navigator(), os.path.join(OUT_DIR, "hermes-navigator.mp3"))
    
    print("\n✨ All 3 audio personas generated.")


if __name__ == "__main__":
    main()
