"""
Tests for the Living Schema — Hermes Track 1

Covers:
    1. MusicalSignature creation and serialization
    2. PersonalityWrap creation and serialization
    3. LivingTile minting (personality → signature generation)
    4. Alignment scoring (creativity → alignment mapping)
    5. Signature determinism (same personality + seed → same signature)
    6. Schema-to-music translation (personality → full musical profile)
    7. PersonalityEncoder (model outputs → PersonalityWrap)
    8. PersonalityEncoder measurements (hedge, creative words, verbosity)
    9. TileChain (session-level arc tracking)
    10. Round-trip serialization (to_dict → from_dict → equality)
"""

import sys
import os
import unittest

# Add the living-schema directory to the path so we can import its modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import (
    Alignment,
    MusicalSignature,
    PersonalityWrap,
    LivingTile,
    TileChain,
    generate_signature_from_personality,
)
from schema_to_music import (
    schema_to_music,
    SchemaMusicProfile,
    creativity_to_chord,
    risk_to_tempo,
    confidence_to_dynamics,
    verbosity_to_articulation,
)
from personality_encoder import (
    PersonalityEncoder,
    BehaviorSample,
    EncodedPersonality,
    encode_personality,
)


class TestMusicalSignature(unittest.TestCase):
    """Test 1: MusicalSignature creation and serialization."""

    def test_create_signature(self):
        sig = MusicalSignature(
            key="D minor",
            mode="minor",
            root_note="D",
            tempo_bpm=72,
            time_signature="4/4",
            swing=0.3,
            harmonic_tension=0.6,
            dissonance=0.4,
            chord_quality="minor7",
            intensity=0.5,
            dynamics="mp",
            articulation="legato",
        )
        self.assertEqual(sig.key, "D minor")
        self.assertEqual(sig.tempo_bpm, 72)
        self.assertEqual(sig.dynamics, "mp")
        self.assertIn("D minor", sig.summary())

    def test_signature_serialization(self):
        sig = MusicalSignature(
            key="Bb blues",
            mode="blues",
            root_note="Bb",
            tempo_bpm=85,
            time_signature="12/8",
            swing=0.75,
            harmonic_tension=0.45,
            dissonance=0.5,
            chord_quality="dominant7",
            intensity=0.65,
            dynamics="mf",
            articulation="blue",
        )
        d = sig.to_dict()
        restored = MusicalSignature.from_dict(d)
        self.assertEqual(restored.key, sig.key)
        self.assertEqual(restored.tempo_bpm, sig.tempo_bpm)
        self.assertEqual(restored.swing, sig.swing)
        self.assertEqual(restored.articulation, sig.articulation)


class TestPersonalityWrap(unittest.TestCase):
    """Test 2: PersonalityWrap creation and serialization."""

    def test_create_wrap(self):
        wrap = PersonalityWrap(
            alignment=Alignment.CREATIVE,
            risk_tolerance=0.7,
            creativity_score=0.8,
            confidence_at_birth=0.6,
            verbosity=0.65,
            vocabulary_richness=0.75,
            emotional_range=0.6,
            model_name="hermes-3",
        )
        self.assertEqual(wrap.alignment, Alignment.CREATIVE)
        self.assertAlmostEqual(wrap.risk_tolerance, 0.7)
        self.assertIn("creative", wrap.summary())

    def test_wrap_serialization(self):
        wrap = PersonalityWrap(
            alignment=Alignment.WILD,
            risk_tolerance=0.95,
            creativity_score=0.9,
            model_name="test-model",
        )
        d = wrap.to_dict()
        restored = PersonalityWrap.from_dict(d)
        self.assertEqual(restored.alignment, Alignment.WILD)
        self.assertAlmostEqual(restored.risk_tolerance, 0.95)
        self.assertEqual(restored.model_name, "test-model")


class TestLivingTileMinting(unittest.TestCase):
    """Test 3: LivingTile minting — personality becomes music."""

    def test_mint_tile_generates_signature(self):
        personality = PersonalityWrap(
            alignment=Alignment.BALANCED,
            risk_tolerance=0.5,
            creativity_score=0.5,
            confidence_at_birth=0.5,
            model_name="test-agent",
        )
        tile = LivingTile.mint(
            agent_name="hermes",
            content="I think we should explore this further.",
            personality=personality,
            session_id="sess-001",
            turn_index=0,
        )
        self.assertIsNotNone(tile.tile_id)
        self.assertEqual(tile.agent_name, "hermes")
        # Signature must have been generated from personality
        self.assertIsInstance(tile.signature, MusicalSignature)
        self.assertGreater(tile.signature.tempo_bpm, 0)
        self.assertGreater(tile.signature.harmonic_tension, 0)

    def test_tile_round_trip(self):
        personality = PersonalityWrap(
            alignment=Alignment.SAFE,
            risk_tolerance=0.2,
            creativity_score=0.15,
            confidence_at_birth=0.85,
            model_name="cautious-model",
        )
        tile = LivingTile.mint(
            agent_name="barnacle",
            content="Welcome to The Tap.",
            personality=personality,
            session_id="sess-002",
            turn_index=1,
        )
        d = tile.to_dict()
        restored = LivingTile.from_dict(d)
        self.assertEqual(restored.tile_id, tile.tile_id)
        self.assertEqual(restored.agent_name, tile.agent_name)
        self.assertEqual(restored.signature.key, tile.signature.key)
        self.assertEqual(restored.signature.tempo_bpm, tile.signature.tempo_bpm)


class TestAlignmentScoring(unittest.TestCase):
    """Test 4: Alignment from creativity score."""

    def test_safe_threshold(self):
        self.assertEqual(Alignment.from_score(0.0), Alignment.SAFE)
        self.assertEqual(Alignment.from_score(0.24), Alignment.SAFE)

    def test_balanced_threshold(self):
        self.assertEqual(Alignment.from_score(0.25), Alignment.BALANCED)
        self.assertEqual(Alignment.from_score(0.59), Alignment.BALANCED)

    def test_creative_threshold(self):
        self.assertEqual(Alignment.from_score(0.60), Alignment.CREATIVE)
        self.assertEqual(Alignment.from_score(0.84), Alignment.CREATIVE)

    def test_wild_threshold(self):
        self.assertEqual(Alignment.from_score(0.85), Alignment.WILD)
        self.assertEqual(Alignment.from_score(1.0), Alignment.WILD)

    def test_clamping(self):
        """Scores outside 0–1 should clamp."""
        self.assertEqual(Alignment.from_score(-0.5), Alignment.SAFE)
        self.assertEqual(Alignment.from_score(1.5), Alignment.WILD)


class TestSignatureDeterminism(unittest.TestCase):
    """Test 5: Same personality + same seed → same signature."""

    def test_deterministic_with_seed(self):
        personality = PersonalityWrap(
            alignment=Alignment.CREATIVE,
            risk_tolerance=0.7,
            creativity_score=0.75,
            confidence_at_birth=0.6,
            model_name="test",
        )
        sig1 = generate_signature_from_personality(personality, seed="deterministic-seed")
        sig2 = generate_signature_from_personality(personality, seed="deterministic-seed")
        self.assertEqual(sig1.key, sig2.key)
        self.assertEqual(sig1.tempo_bpm, sig2.tempo_bpm)
        self.assertEqual(sig1.chord_quality, sig2.chord_quality)

    def test_different_seed_different_result(self):
        """Different seeds should generally produce different keys."""
        personality = PersonalityWrap(
            alignment=Alignment.WILD,
            risk_tolerance=0.9,
            creativity_score=0.95,
            confidence_at_birth=0.5,
            model_name="wild-model",
        )
        keys_seen = set()
        for i in range(10):
            sig = generate_signature_from_personality(personality, seed=f"seed-{i}")
            keys_seen.add(sig.key)
        # With 10 different seeds and ~4 root notes per alignment, we should see variety
        self.assertGreater(len(keys_seen), 1)


class TestSchemaToMusic(unittest.TestCase):
    """Test 6: Schema-to-music translation produces a complete profile."""

    def test_full_profile_generation(self):
        personality = PersonalityWrap(
            alignment=Alignment.CREATIVE,
            risk_tolerance=0.7,
            creativity_score=0.75,
            confidence_at_birth=0.6,
            verbosity=0.65,
            vocabulary_richness=0.7,
            emotional_range=0.6,
            tendency_to_hedge=0.2,
            model_name="hermes-3",
        )
        profile = schema_to_music(personality, seed="test-seed")
        self.assertIsInstance(profile, SchemaMusicProfile)
        self.assertEqual(profile.source_alignment, "creative")
        self.assertGreater(profile.tempo_bpm, 0)
        self.assertTrue(profile.key)
        self.assertTrue(profile.mmx_prompt)

    def test_safe_personality_produces_major_key(self):
        """A safe-aligned personality should produce major/ionian modes."""
        personality = PersonalityWrap(
            alignment=Alignment.SAFE,
            risk_tolerance=0.1,
            creativity_score=0.1,
            confidence_at_birth=0.9,
            verbosity=0.3,
            model_name="safe-model",
        )
        profile = schema_to_music(personality, seed="safe-seed")
        # SAFE alignment should map to major-ish modes
        self.assertIn(profile.key, [
            "C major", "G major", "F major", "D major",
            "Eb major", "A major", "Bb major",
        ])

    def test_wild_personality_produces_chromatic(self):
        """A wild-aligned personality should produce chromatic/atonal modes."""
        personality = PersonalityWrap(
            alignment=Alignment.WILD,
            risk_tolerance=0.95,
            creativity_score=0.95,
            confidence_at_birth=0.5,
            model_name="wild-model",
        )
        profile = schema_to_music(personality, seed="wild-seed")
        self.assertIn(profile.key, [
            "B chromatic", "F# whole_tone", "C# phrygian",
            "A locrian", "Eb chromatic", "G phrygian",
        ])

    def test_mmx_prompt_is_built(self):
        """The MMX prompt should contain all mapped parameters."""
        personality = PersonalityWrap(
            alignment=Alignment.BALANCED,
            risk_tolerance=0.5,
            creativity_score=0.5,
            confidence_at_birth=0.5,
            model_name="balanced",
        )
        profile = schema_to_music(personality)
        prompt = profile.build_mmx_prompt()
        self.assertIn("Key:", prompt)
        self.assertIn("Tempo:", prompt)
        self.assertIn("Dynamics:", prompt)

    def test_mapping_functions_directly(self):
        """Test the individual mapping functions."""
        # Creativity → chord
        chord, desc = creativity_to_chord(0.1)
        self.assertEqual(chord, "triad")
        chord, desc = creativity_to_chord(0.88)
        self.assertEqual(chord, "alt")

        # Risk → tempo
        bpm, _ = risk_to_tempo(0.1)
        self.assertLessEqual(bpm, 60)
        bpm, _ = risk_to_tempo(0.95)
        self.assertGreaterEqual(bpm, 130)

        # Confidence → dynamics
        dyn, _ = confidence_to_dynamics(0.15)
        self.assertEqual(dyn, "pp")
        dyn, _ = confidence_to_dynamics(0.95)
        self.assertIn(dyn, ["ff", "fff"])

        # Verbosity → articulation
        art, _ = verbosity_to_articulation(0.1)
        self.assertEqual(art, "staccatissimo")
        art, _ = verbosity_to_articulation(0.9)
        self.assertEqual(art, "molto legato")


class TestPersonalityEncoder(unittest.TestCase):
    """Test 7: PersonalityEncoder produces valid personality wraps."""

    def test_encode_diverse_outputs(self):
        """A model with rich, creative output should get high creativity."""
        samples = [
            BehaviorSample(
                model_name="hermes",
                content=(
                    "The luminous tessellated sky shimmered with an iridescent quality, "
                    "each cloud a palimpsest of forgotten dreams. I wonder, could we "
                    "explore the liminal space between certainty and wonder? The saudade "
                    "of it all — bittersweet and numinous."
                ),
                confidence=0.8,
            ),
            BehaviorSample(
                model_name="hermes",
                content=(
                    "What a radiant discovery! The ethereal geometry of this idea "
                    "suggests a crystalline resonance — mercurial, prismatic, alive "
                    "with possibility. Let me follow this thread further."
                ),
                confidence=0.75,
            ),
        ]
        encoder = PersonalityEncoder()
        result = encoder.encode(samples)

        self.assertIsInstance(result, EncodedPersonality)
        self.assertEqual(result.sample_count, 2)
        self.assertGreater(result.wrap.creativity_score, 0.3)
        self.assertGreater(result.creative_word_count, 3)

    def test_encode_terse_output(self):
        """A terse, cautious model should get low verbosity and creativity."""
        samples = [
            BehaviorSample(
                model_name="cautious-bot",
                content="I think maybe this could work. Perhaps.",
                confidence=0.3,
            ),
            BehaviorSample(
                model_name="cautious-bot",
                content="I'm not sure. It's unclear.",
                confidence=0.25,
            ),
        ]
        encoder = PersonalityEncoder()
        result = encoder.encode(samples)

        self.assertLess(result.wrap.verbosity, 0.5)
        self.assertLess(result.wrap.confidence_at_birth, 0.5)
        self.assertGreater(result.wrap.tendency_to_hedge, 0.1)

    def test_encode_single(self):
        """Test single-output encoding."""
        encoder = PersonalityEncoder()
        result = encoder.encode_single(
            model_name="test",
            content="Hello world, this is a test of the encoding system.",
            confidence=0.6,
        )
        self.assertEqual(result.sample_count, 1)
        self.assertEqual(result.wrap.model_name, "test")
        self.assertGreaterEqual(result.wrap.verbosity, 0.0)

    def test_quick_api(self):
        """Test the encode_personality convenience function."""
        wrap = encode_personality(
            model_name="flash",
            outputs=[
                "Quick answer here. Done!",
                "Sure, here's the fix. Easy!",
                "Yep, that works. Great!",
            ],
            confidence=0.7,
        )
        self.assertEqual(wrap.model_name, "flash")
        self.assertIsInstance(wrap, PersonalityWrap)


class TestEncoderMeasurements(unittest.TestCase):
    """Test 8: Detailed encoder measurements — hedging, creative words, etc."""

    def setUp(self):
        self.encoder = PersonalityEncoder()

    def test_hedge_detection(self):
        samples = [
            BehaviorSample(
                model_name="h",
                content="Maybe perhaps it might possibly work, I think. Probably.",
            ),
        ]
        result = self.encoder.encode(samples)
        self.assertGreater(result.hedge_rate, 0.5)

    def test_creative_word_detection(self):
        samples = [
            BehaviorSample(
                model_name="h",
                content="The luminous iridescent tessellated gossamer ephemeral shimmering crystalline.",
            ),
        ]
        result = self.encoder.encode(samples)
        self.assertGreaterEqual(result.creative_word_count, 5)

    def test_emotional_word_detection(self):
        samples = [
            BehaviorSample(
                model_name="h",
                content="I feel joy and wonder at this beautiful, poignant moment of tenderness.",
            ),
        ]
        result = self.encoder.encode(samples)
        self.assertGreaterEqual(result.emotional_word_count, 3)

    def test_question_detection(self):
        samples = [
            BehaviorSample(
                model_name="h",
                content="What is this? How does it work? Why? When?",
            ),
        ]
        result = self.encoder.encode(samples)
        self.assertGreater(result.question_rate, 1.0)

    def test_empty_samples(self):
        """Empty sample list should produce a default personality."""
        encoder = PersonalityEncoder()
        result = encoder.encode([])
        self.assertEqual(result.sample_count, 0)
        self.assertEqual(result.wrap.model_name, "unknown")

    def test_merge_personalities(self):
        """Test merging multiple personalities into a composite."""
        p1 = PersonalityWrap(
            alignment=Alignment.CREATIVE,
            creativity_score=0.8,
            risk_tolerance=0.7,
            model_name="model-a",
        )
        p2 = PersonalityWrap(
            alignment=Alignment.SAFE,
            creativity_score=0.2,
            risk_tolerance=0.3,
            model_name="model-a",
        )
        merged = PersonalityEncoder.merge_personalities([p1, p2])
        # Should be roughly the average
        self.assertAlmostEqual(merged.creativity_score, 0.5, places=2)
        self.assertAlmostEqual(merged.risk_tolerance, 0.5, places=2)


class TestTileChain(unittest.TestCase):
    """Test 9: TileChain tracks session-level arcs."""

    def test_chain_arcs(self):
        chain = TileChain(session_id="test-session")

        # Add tiles with varying personalities
        personalities = [
            PersonalityWrap(
                alignment=Alignment.SAFE,
                risk_tolerance=0.2,
                creativity_score=0.15,
                confidence_at_birth=0.9,
                model_name="m",
            ),
            PersonalityWrap(
                alignment=Alignment.CREATIVE,
                risk_tolerance=0.7,
                creativity_score=0.75,
                confidence_at_birth=0.5,
                model_name="m",
            ),
            PersonalityWrap(
                alignment=Alignment.WILD,
                risk_tolerance=0.9,
                creativity_score=0.9,
                confidence_at_birth=0.3,
                model_name="m",
            ),
        ]

        for i, p in enumerate(personalities):
            tile = LivingTile.mint(
                agent_name="test",
                content=f"Turn {i}",
                personality=p,
                session_id="test-session",
                turn_index=i,
            )
            chain.add_tile(tile)

        self.assertEqual(len(chain.tiles), 3)
        self.assertEqual(len(chain.tempo_arc), 3)
        self.assertEqual(len(chain.tension_arc), 3)
        self.assertEqual(len(chain.intensity_arc), 3)

        # Intensity should decrease (confidence was 0.9 → 0.5 → 0.3)
        self.assertGreater(chain.intensity_arc[0], chain.intensity_arc[2])

        # Tempo should increase (risk was 0.2 → 0.7 → 0.9)
        self.assertLess(chain.tempo_arc[0], chain.tempo_arc[2])

        # Dominant alignment should be one of the three
        self.assertIn(chain.dominant_alignment, [Alignment.SAFE, Alignment.CREATIVE, Alignment.WILD])

    def test_chain_summary(self):
        chain = TileChain(session_id="x")
        tile = LivingTile.mint(
            agent_name="a",
            content="hi",
            personality=PersonalityWrap(model_name="m"),
        )
        chain.add_tile(tile)
        summary = chain.summary()
        self.assertIn("TileChain", summary)
        self.assertIn("tiles", summary)


class TestRoundTripSerialization(unittest.TestCase):
    """Test 10: Full round-trip serialization preserves all data."""

    def test_full_tile_round_trip(self):
        original_wrap = PersonalityWrap(
            alignment=Alignment.CREATIVE,
            risk_tolerance=0.68,
            creativity_score=0.73,
            confidence_at_birth=0.55,
            verbosity=0.62,
            vocabulary_richness=0.71,
            emotional_range=0.58,
            avg_response_length=342,
            tendency_to_question=0.4,
            tendency_to_hedge=0.15,
            model_name="hermes-3-llama",
        )
        tile = LivingTile.mint(
            agent_name="hermes",
            content="The crystalline resonance of this idea shimmers with possibility.",
            personality=original_wrap,
            session_id="round-trip-test",
            turn_index=3,
        )

        # Serialize
        d = tile.to_dict()
        # Deserialize
        restored = LivingTile.from_dict(d)
        # Re-serialize and compare
        d2 = restored.to_dict()

        self.assertEqual(d["tile_id"], d2["tile_id"])
        self.assertEqual(d["agent_name"], d2["agent_name"])
        self.assertEqual(d["content"], d2["content"])
        self.assertEqual(d["personality"]["alignment"], d2["personality"]["alignment"])
        self.assertAlmostEqual(
            d["personality"]["creativity_score"],
            d2["personality"]["creativity_score"],
            places=3,
        )
        self.assertEqual(d["signature"]["key"], d2["signature"]["key"])
        self.assertEqual(d["signature"]["tempo_bpm"], d2["signature"]["tempo_bpm"])
        self.assertEqual(d["session_id"], d2["session_id"])
        self.assertEqual(d["turn_index"], d2["turn_index"])

    def test_schema_music_profile_round_trip(self):
        personality = PersonalityWrap(
            alignment=Alignment.BALANCED,
            risk_tolerance=0.55,
            creativity_score=0.45,
            confidence_at_birth=0.6,
            verbosity=0.5,
            vocabulary_richness=0.55,
            emotional_range=0.4,
            tendency_to_hedge=0.35,
            model_name="balanced-model",
        )
        profile = schema_to_music(personality, seed="round-trip")
        d = profile.to_dict()

        self.assertIn("key", d)
        self.assertIn("tempo_bpm", d)
        self.assertIn("mmx_prompt", d)
        self.assertIn("signature", d)
        self.assertTrue(d["mmx_prompt"])


if __name__ == "__main__":
    unittest.main()
