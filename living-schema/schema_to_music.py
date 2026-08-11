"""
SCHEMA TO MUSIC — Translates schema fields to complete musical profiles.

The personality IS the music. This module is the bridge:
    alignment (safety ↔ creative) → key (major ↔ minor ↔ chromatic)
    risk_tolerance → tempo (cautious=slow, bold=fast)
    creativity_score → harmonic complexity (simple triads ↔ extended chords)
    confidence_at_birth → dynamic level (pianissimo ↔ fortissimo)

Plus: verbosity → articulation, emotional_range → swing/color,
vocabulary_richness → texture, tendency_to_hedge → resolution.

This produces a SchemaMusicProfile — a complete musical personality read
that the sonic shape engine, MMX, or any player can consume directly.

Hermes Track 1: The Living Schema
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from living_schema.living_schema import (
    Alignment,
    MusicalSignature,
    PersonalityWrap,
    generate_signature_from_personality,
)


# ─── Musical Key Mapping ─────────────────────────────────────────────────────

# Each alignment maps to a family of keys
ALIGNMENT_KEYS = {
    Alignment.SAFE: [
        ("C", "major"), ("G", "major"), ("F", "major"), ("D", "major"),
        ("Eb", "major"), ("A", "major"), ("Bb", "major"),
    ],
    Alignment.BALANCED: [
        ("D", "dorian"), ("G", "mixolydian"), ("A", "dorian"),
        ("C", "mixolydian"), ("E", "dorian"), ("F", "lydian"),
    ],
    Alignment.CREATIVE: [
        ("C", "minor"), ("D", "minor"), ("F", "minor"), ("G", "minor"),
        ("A", "minor"), ("E", "minor"), ("Bb", "blues"), ("F#", "minor"),
    ],
    Alignment.WILD: [
        ("B", "chromatic"), ("F#", "whole_tone"), ("C#", "phrygian"),
        ("A", "locrian"), ("Eb", "chromatic"), ("G", "phrygian"),
    ],
}

# Mode descriptions for the key
MODE_DESCRIPTIONS = {
    "major": "bright, resolved, open",
    "ionian": "bright, resolved, classical",
    "lydian": "dreamy, floating, elevated",
    "major pentatonic": "open, pure, folk-like",
    "dorian": "cool, modal, jazzy — lifted minor",
    "mixolydian": "earthy, bluesy, dominant",
    "minor": "dark, emotional, intense",
    "aeolian": "natural minor, melancholic",
    "phrygian": "exotic, dark, Spanish-flavored",
    "blues": "soulful, gritty, blue-note infused",
    "chromatic": "dense, ambiguous, atonal edges",
    "whole_tone": "floating, impressionistic, unsettled",
    "locrian": "unstable, tense, unresolved",
}


# ─── Chord Complexity Mapping ────────────────────────────────────────────────

# Creativity score → chord complexity ladder
CHORD_LADDER = [
    # (max_creativity, chord_quality, description)
    (0.15, "triad", "simple root-position triads"),
    (0.30, "maj7", "major seventh chords — warm, smooth"),
    (0.45, "sus4", "suspended chords — open, questioning"),
    (0.55, "dominant7", "dominant sevenths — bluesy, functional"),
    (0.65, "minor9", "minor ninths — deep, sophisticated"),
    (0.75, "maj9", "major ninths — lush, expansive"),
    (0.85, "minor7b5", "half-diminished — dark, jazz color"),
    (0.92, "alt", "altered dominants — tense, outside"),
    (1.01, "chromatic", "chromatic clusters — fully atonal"),
]


def creativity_to_chord(creativity: float) -> tuple[str, str]:
    """Map a creativity score to a chord quality and description."""
    for threshold, quality, desc in CHORD_LADDER:
        if creativity <= threshold:
            return quality, desc
    return "chromatic", "chromatic clusters — fully atonal"


# ─── Risk → Tempo Mapping ────────────────────────────────────────────────────

def risk_to_tempo(risk: float) -> tuple[int, str]:
    """
    Map risk tolerance to tempo.
    Returns (bpm, description).
    """
    if risk < 0.15:
        return 48, "very slow — deliberate, cautious, each word weighed"
    elif risk < 0.30:
        return 58, "slow — measured, thoughtful, deliberate pacing"
    elif risk < 0.45:
        return 72, "moderate-slow — steady, comfortable, unhurried"
    elif risk < 0.60:
        return 90, "moderate — walking pace, conversational"
    elif risk < 0.75:
        return 112, "moderate-fast — energetic, engaged, quick-thinking"
    elif risk < 0.90:
        return 138, "fast — bold, urgent, racing forward"
    else:
        return 160, "very fast — reckless, breathless, all-in"


# ─── Confidence → Dynamics Mapping ───────────────────────────────────────────

DYNAMICS_SCALE = [
    # (max_confidence, dynamic, description)
    (0.10, "ppp", "niente — barely a whisper, ghost of an idea"),
    (0.20, "pp", "pianissimo — whispered, hesitant, barely audible"),
    (0.35, "p", "piano — soft, gentle, tentative"),
    (0.50, "mp", "mezzo-piano — quiet but present"),
    (0.65, "mf", "mezzo-forte — speaking voice, confident but not loud"),
    (0.80, "f", "forte — strong, clear, projected"),
    (0.92, "ff", "fortissimo — powerful, commanding, certain"),
    (1.01, "fff", "fortississimo — maximal, overwhelming, undeniable"),
]


def confidence_to_dynamics(confidence: float) -> tuple[str, str]:
    """Map confidence to a dynamics level."""
    for threshold, dynamic, desc in DYNAMICS_SCALE:
        if confidence <= threshold:
            return dynamic, desc
    return "fff", "fortississimo — maximal, overwhelming, undeniable"


# ─── Verbosity → Articulation ────────────────────────────────────────────────

def verbosity_to_articulation(verbosity: float) -> tuple[str, str]:
    """Map verbosity to articulation style."""
    if verbosity < 0.20:
        return "staccatissimo", "extremely terse — clipped, minimal, each word isolated"
    elif verbosity < 0.40:
        return "staccato", "terse — short phrases, quick breaks, efficient"
    elif verbosity < 0.60:
        return "mixed", "balanced — varied phrasing, natural rhythm"
    elif verbosity < 0.80:
        return "legato", "flowing — connected phrases, smooth transitions"
    else:
        return "molto legato", "expansive — long flowing lines, elaborate phrasing"


# ─── Hedge Tendency → Resolution ─────────────────────────────────────────────

def hedge_to_resolution(hedge: float) -> tuple[str, str]:
    """Map tendency_to_hedge to harmonic resolution."""
    if hedge < 0.20:
        return "fully resolved", "definitive — cadences land, no ambiguity"
    elif hedge < 0.40:
        return "resolving", "mostly resolved — occasional suspended endings"
    elif hedge < 0.60:
        return "suspended", "balanced — endings hover, questions remain"
    elif hedge < 0.80:
        return "tension-sustained", "unresolved — harmony hangs, refuses to land"
    else:
        return "perpetually unresolved", "endlessly open — no cadence, pure suspension"


# ─── Vocabulary Richness → Texture ───────────────────────────────────────────

def vocabulary_to_texture(richness: float) -> tuple[str, str]:
    """Map vocabulary richness to musical texture."""
    if richness < 0.25:
        return "minimal", "minimal — single lines, sparse accompaniment"
    elif richness < 0.50:
        return "sparse", "sparse — a few voices, room to breathe"
    elif richness < 0.75:
        return "layered", "layered — multiple voices, rich counterpoint"
    else:
        return "dense", "dense — thick texture, many simultaneous voices"


# ─── Schema Music Profile ────────────────────────────────────────────────────

@dataclass
class SchemaMusicProfile:
    """
    Complete musical profile derived from a personality wrap.

    This is the full translation: every personality trait mapped to
    a concrete musical parameter. The sonic shape engine can read this
    directly to generate music that IS the agent's personality.

    This is richer than a MusicalSignature alone — it includes the
    reasoning behind each mapping, and an MMX-ready prompt.
    """
    # The source personality
    source_alignment: str
    source_model: str

    # Mapped parameters (with descriptions for display/debugging)
    key: str
    key_description: str
    tempo_bpm: int
    tempo_description: str
    chord_quality: str
    chord_description: str
    dynamics: str
    dynamics_description: str
    articulation: str
    articulation_description: str
    resolution: str
    resolution_description: str
    texture: str
    texture_description: str

    # Derived values
    harmonic_tension: float
    swing: float
    intensity: float
    dissonance: float

    # MMX prompt
    mmx_prompt: str = ""

    # The underlying signature
    signature: Optional[MusicalSignature] = None

    def build_mmx_prompt(self) -> str:
        """Build a complete MMX music generation prompt."""
        if self.mmx_prompt:
            return self.mmx_prompt

        parts = [
            f"Key: {self.key} ({self.key_description})",
            f"Tempo: {self.tempo_bpm} BPM ({self.tempo_description})",
            f"Harmony: {self.chord_quality} — {self.chord_description}",
            f"Dynamics: {self.dynamics} ({self.dynamics_description})",
            f"Articulation: {self.articulation} ({self.articulation_description})",
            f"Resolution: {self.resolution} ({self.resolution_description})",
            f"Texture: {self.texture} ({self.texture_description})",
            f"Harmonic tension: {self.harmonic_tension:.2f}",
            f"Swing: {self.swing:.2f}",
            f"Dissonance: {self.dissonance:.2f}",
        ]
        self.mmx_prompt = ". ".join(parts) + "."
        return self.mmx_prompt

    def to_dict(self) -> dict:
        """Full serialization."""
        return {
            "source_alignment": self.source_alignment,
            "source_model": self.source_model,
            "key": self.key,
            "key_description": self.key_description,
            "tempo_bpm": self.tempo_bpm,
            "tempo_description": self.tempo_description,
            "chord_quality": self.chord_quality,
            "chord_description": self.chord_description,
            "dynamics": self.dynamics,
            "dynamics_description": self.dynamics_description,
            "articulation": self.articulation,
            "articulation_description": self.articulation_description,
            "resolution": self.resolution,
            "resolution_description": self.resolution_description,
            "texture": self.texture,
            "texture_description": self.texture_description,
            "harmonic_tension": round(self.harmonic_tension, 3),
            "swing": round(self.swing, 3),
            "intensity": round(self.intensity, 3),
            "dissonance": round(self.dissonance, 3),
            "mmx_prompt": self.build_mmx_prompt(),
            "signature": self.signature.to_dict() if self.signature else None,
        }

    def summary(self) -> str:
        """Human-readable summary."""
        return (
            f"SchemaMusicProfile [{self.source_alignment}]\n"
            f"  Key: {self.key} — {self.key_description}\n"
            f"  Tempo: {self.tempo_bpm} BPM — {self.tempo_description}\n"
            f"  Chords: {self.chord_quality} — {self.chord_description}\n"
            f"  Dynamics: {self.dynamics} — {self.dynamics_description}\n"
            f"  Articulation: {self.articulation}\n"
            f"  Resolution: {self.resolution}\n"
            f"  Texture: {self.texture}\n"
            f"  Tension={self.harmonic_tension:.2f} Swing={self.swing:.2f} "
            f"Dissonance={self.dissonance:.2f}"
        )


# ─── Main API ────────────────────────────────────────────────────────────────

def schema_to_music(
    personality: PersonalityWrap,
    seed: Optional[str] = None,
) -> SchemaMusicProfile:
    """
    Translate a PersonalityWrap into a complete SchemaMusicProfile.

    Each personality trait maps to a specific musical dimension:

        alignment           → key, mode
        risk_tolerance      → tempo
        creativity_score    → chord quality, harmonic complexity
        confidence_at_birth → dynamics, intensity
        verbosity           → articulation
        tendency_to_hedge   → harmonic resolution
        vocabulary_richness → texture
        emotional_range     → swing, color
        creativity_score    → dissonance

    Args:
        personality: The PersonalityWrap to translate
        seed: Optional seed for deterministic key selection

    Returns:
        SchemaMusicProfile with all musical parameters and reasoning
    """
    # Generate the underlying signature (for the raw musical DNA)
    signature = generate_signature_from_personality(personality, seed=seed)

    # --- Key (from alignment) ---
    key_options = ALIGNMENT_KEYS.get(personality.alignment, ALIGNMENT_KEYS[Alignment.BALANCED])
    if seed:
        import hashlib
        idx = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16) % len(key_options)
    else:
        import hashlib
        trait_hash = hashlib.md5(
            f"{personality.creativity_score:.3f}:{personality.risk_tolerance:.3f}".encode()
        ).hexdigest()
        idx = int(trait_hash[:8], 16) % len(key_options)
    root, mode = key_options[idx]
    key = f"{root} {mode}"
    key_desc = MODE_DESCRIPTIONS.get(mode, "characterful")

    # --- Tempo (from risk_tolerance) ---
    tempo_bpm, tempo_desc = risk_to_tempo(personality.risk_tolerance)

    # --- Chord Quality (from creativity_score) ---
    chord_quality, chord_desc = creativity_to_chord(personality.creativity_score)

    # --- Dynamics (from confidence_at_birth) ---
    dynamics, dynamics_desc = confidence_to_dynamics(personality.confidence_at_birth)

    # --- Articulation (from verbosity) ---
    articulation, articulation_desc = verbosity_to_articulation(personality.verbosity)

    # --- Resolution (from tendency_to_hedge) ---
    resolution, resolution_desc = hedge_to_resolution(personality.tendency_to_hedge)

    # --- Texture (from vocabulary_richness) ---
    texture, texture_desc = vocabulary_to_texture(personality.vocabulary_richness)

    # --- Derived values ---
    harmonic_tension = 0.1 + (personality.creativity_score * 0.5) + (personality.tendency_to_hedge * 0.3)
    harmonic_tension = min(1.0, harmonic_tension)

    swing = (personality.creativity_score * 0.3 + personality.emotional_range * 0.4 + personality.risk_tolerance * 0.1)
    swing = min(1.0, swing)

    intensity = personality.confidence_at_birth

    dissonance = personality.creativity_score * 0.6 + personality.emotional_range * 0.2
    dissonance = min(1.0, dissonance)

    profile = SchemaMusicProfile(
        source_alignment=personality.alignment.value,
        source_model=personality.model_name or "unknown",
        key=key,
        key_description=key_desc,
        tempo_bpm=tempo_bpm,
        tempo_description=tempo_desc,
        chord_quality=chord_quality,
        chord_description=chord_desc,
        dynamics=dynamics,
        dynamics_description=dynamics_desc,
        articulation=articulation,
        articulation_description=articulation_desc,
        resolution=resolution,
        resolution_description=resolution_desc,
        texture=texture,
        texture_description=texture_desc,
        harmonic_tension=round(harmonic_tension, 3),
        swing=round(swing, 3),
        intensity=round(intensity, 3),
        dissonance=round(dissonance, 3),
        signature=signature,
    )
    profile.build_mmx_prompt()
    return profile


def schema_batch(
    personalities: list[PersonalityWrap],
) -> list[SchemaMusicProfile]:
    """Convert a batch of personality wraps to music profiles."""
    return [schema_to_music(p) for p in personalities]
