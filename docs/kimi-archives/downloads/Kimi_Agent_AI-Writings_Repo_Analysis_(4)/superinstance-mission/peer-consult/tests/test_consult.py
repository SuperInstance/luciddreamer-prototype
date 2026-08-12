"""
Offline tests for peer_consult.consult.

MockBackend + HashEmbedder only — no network, no Ollama. The engineered
answer/critique texts below were verified against HashEmbedder(dim=256);
SHA-256 token hashing keeps them identical on every machine.
"""

import pytest

from casting_call import CastingDirector, ModelAtlas, ModelProfile, VoiceCharacter

from peer_consult import (
    BackendResolutionError,
    BackendResolver,
    ConsultationDirector,
    HashEmbedder,
    MockBackend,
    Verdict,
    Zone,
    select_critic,
    voice_family,
)
from peer_consult.swmidi import FRICTION_SEMANTIC, decode_event


# ── Engineered texts (verified deltas against HashEmbedder) ─────────

def _toks(prefix, n):
    return " ".join(f"{prefix}word{i:02d}" for i in range(n))


def _pair(shared, a, c):
    shared_text = _toks("shared", shared)
    return f"{shared_text} {_toks('ans', a)}", f"{shared_text} {_toks('crit', c)}"


_IDENTICAL = "the quick brown fox jumps over the lazy dog near the tide"
TEXTS = {
    Zone.STALE: (_IDENTICAL, _IDENTICAL),                    # Δ = 0.0
    Zone.TRANSITIONAL_LOW: _pair(7, 3, 3),                   # Δ = 0.3
    Zone.CREATIVE: _pair(5, 5, 5),                           # Δ = 0.5
    Zone.TRANSITIONAL_HIGH: _pair(3, 7, 7),                  # Δ = 0.7
    Zone.CHAOTIC: (_toks("ans", 30), _toks("crit", 30)),     # Δ ≈ 0.90
}


def make_director(answer, critique, *, director=None):
    """A ConsultationDirector whose every model speaks the given lines."""

    def dispatch(prompt):
        # the critique prompt is the devil's-advocate one
        return critique if "devil" in prompt else answer

    resolver = BackendResolver(factory=lambda name: MockBackend(dispatch))
    return ConsultationDirector(director=director, resolver=resolver, embedder=HashEmbedder())


class SpyDirector(CastingDirector):
    """Records every role it is asked to cast."""

    def __init__(self, atlas):
        super().__init__(atlas)
        self.cast_roles: list[str] = []

    def cast(self, role, context=None):
        self.cast_roles.append(role)
        return super().cast(role, context)


# ── Verdict rules per zone band ──────────────────────────────────────

class TestVerdictPerZone:
    @pytest.mark.parametrize("zone,verdict", [
        (Zone.STALE, Verdict.CONFIRM),
        (Zone.TRANSITIONAL_LOW, Verdict.NOTE),
        (Zone.CREATIVE, Verdict.REVISE),
        (Zone.TRANSITIONAL_HIGH, Verdict.NOTE),
        (Zone.CHAOTIC, Verdict.ESCALATE),
    ])
    def test_zone_rules(self, zone, verdict):
        answer, critique = TEXTS[zone]
        consultation = make_director(answer, critique).cast_with_consult(
            "intent_parse", "plot tomorrow's passage"
        )
        assert consultation.zone is zone
        assert consultation.verdict is verdict
        assert consultation.primary_answer == answer
        assert consultation.critique == critique

    def test_stale_confirm_rationale(self):
        answer, critique = TEXTS[Zone.STALE]
        consultation = make_director(answer, critique).cast_with_consult("intent_parse", "t")
        assert consultation.delta == pytest.approx(0.0)
        assert "redundant agreement" in consultation.rationale

    def test_revise_merges_critics_objections(self):
        answer, critique = TEXTS[Zone.CREATIVE]
        consultation = make_director(answer, critique).cast_with_consult("intent_parse", "t")
        assert consultation.verdict is Verdict.REVISE
        assert critique.strip() in consultation.rationale

    def test_note_names_transitional_band(self):
        answer, critique = TEXTS[Zone.TRANSITIONAL_HIGH]
        consultation = make_director(answer, critique).cast_with_consult("intent_parse", "t")
        assert consultation.verdict is Verdict.NOTE
        assert "transitional" in consultation.rationale


class TestEscalate:
    def test_escalate_routes_to_safety_check_model(self):
        spy = SpyDirector(ModelAtlas.default())
        answer, critique = TEXTS[Zone.CHAOTIC]
        consultation = make_director(answer, critique, director=spy).cast_with_consult(
            "intent_parse", "t"
        )
        assert consultation.verdict is Verdict.ESCALATE
        # the safety_check role was cast, and its atlas model named
        assert "safety_check" in spy.cast_roles
        safety = spy.cast("safety_check")
        assert safety.name in consultation.rationale
        assert "safety_check" in consultation.rationale

    def test_chaotic_sets_semantic_friction_bit(self):
        answer, critique = TEXTS[Zone.CHAOTIC]
        consultation = make_director(answer, critique).cast_with_consult("intent_parse", "t")
        for offset in range(0, len(consultation.swmidi), 8):
            event = decode_event(consultation.swmidi[offset:offset + 8])
            assert event["error_mask"] & FRICTION_SEMANTIC

    def test_non_chaotic_has_clean_error_mask(self):
        answer, critique = TEXTS[Zone.CREATIVE]
        consultation = make_director(answer, critique).cast_with_consult("intent_parse", "t")
        for offset in range(0, len(consultation.swmidi), 8):
            event = decode_event(consultation.swmidi[offset:offset + 8])
            assert event["error_mask"] == 0


# ── Critic selection (counterpoint — no parallel octaves) ───────────

class TestCriticSelection:
    @pytest.mark.parametrize("role", [
        "intent_parse", "planning", "code_gen", "personality_wrap",
        "safety_check", "creative_ideation", "spatial_reasoning",
        "synthesis", "vision", "voice", "forced_perspective",
        "creative_nonfiction", "sensory_creative",
    ])
    def test_critic_differs_in_voice_family_for_every_role(self, role):
        atlas = ModelAtlas.default()
        director = CastingDirector(atlas)
        primary = director.cast(role)
        critic = select_critic(atlas, role, primary)
        assert critic.name != primary.name
        assert voice_family(critic.voice_character) != voice_family(primary.voice_character)

    def test_critic_comes_from_role_fallback_chain(self):
        atlas = ModelAtlas.default()
        primary = CastingDirector(atlas).cast("intent_parse")
        assert primary.name == "SEED_MINI"
        critic = select_critic(atlas, "intent_parse", primary)
        # SEED_MINI is skipped (same model); GLM_5_2 is the next chain entry
        # and a different family (versatile vs analog synth).
        assert critic.name == "GLM_5_2"

    def test_kurzweil_jr_counts_as_kurzweil_family(self):
        assert voice_family(VoiceCharacter.KURZWEIL) == voice_family(VoiceCharacter.KURZWEIL_JR)
        assert voice_family(VoiceCharacter.ANALOG_SYNTH) == voice_family(VoiceCharacter.ANALOG_SYNTH_PRO)

    def test_raises_when_no_different_family_exists(self):
        def profile(name, voice):
            return ModelProfile(
                name=name, provider="test", voice_character=voice,
                tempo_bpm=(40, 60), strengths=[], weaknesses=[],
                cost_per_1k_tokens=0.001, failure_modes="", channel=None,
            )
        atlas = ModelAtlas([
            profile("BIG_ORGAN", VoiceCharacter.KURZWEIL),
            profile("LITTLE_ORGAN", VoiceCharacter.KURZWEIL_JR),
        ])
        with pytest.raises(ValueError, match="No eligible critic"):
            select_critic(atlas, "intent_parse", atlas.get("BIG_ORGAN"))

    def test_consultation_uses_different_family_critic(self):
        answer, critique = TEXTS[Zone.CREATIVE]
        consultation = make_director(answer, critique).cast_with_consult("intent_parse", "t")
        atlas = ModelAtlas.default()
        primary = atlas.get(consultation.primary_model)
        critic = atlas.get(consultation.critic_model)
        assert voice_family(critic.voice_character) != voice_family(primary.voice_character)


# ── SWMIDI-8 events ──────────────────────────────────────────────────

class TestSwmidiEvents:
    def test_three_events_cast_consult_verdict(self):
        answer, critique = TEXTS[Zone.CREATIVE]
        consultation = make_director(answer, critique).cast_with_consult("intent_parse", "t")
        assert len(consultation.swmidi) == 24
        events = [
            decode_event(consultation.swmidi[i:i + 8]) for i in range(0, 24, 8)
        ]
        assert [e["pitch"] for e in events] == [1, 2, 3]  # cast, consult, verdict
        assert [e["tick"] for e in events] == [0, 96, 192]

    def test_events_on_primary_atlas_channel(self):
        answer, critique = TEXTS[Zone.CREATIVE]
        consultation = make_director(answer, critique).cast_with_consult("intent_parse", "t")
        primary = ModelAtlas.default().get(consultation.primary_model)
        for offset in range(0, len(consultation.swmidi), 8):
            assert decode_event(consultation.swmidi[offset:offset + 8])["channel"] == primary.channel

    def test_velocity_is_confidence(self):
        answer, critique = TEXTS[Zone.CREATIVE]
        consultation = make_director(answer, critique).cast_with_consult("intent_parse", "t")
        expected = round((1.0 - consultation.delta) * 127)
        for offset in range(0, len(consultation.swmidi), 8):
            assert decode_event(consultation.swmidi[offset:offset + 8])["velocity"] == expected

    def test_full_confidence_gives_velocity_127(self):
        answer, critique = TEXTS[Zone.STALE]
        consultation = make_director(answer, critique).cast_with_consult("intent_parse", "t")
        assert decode_event(consultation.swmidi[:8])["velocity"] == 127


# ── Cost ceiling ─────────────────────────────────────────────────────

class TestCostCeiling:
    def test_max_cost_respected_for_primary_and_critic(self):
        atlas = ModelAtlas.default()
        answer, critique = TEXTS[Zone.CREATIVE]
        consultation = make_director(answer, critique).cast_with_consult(
            "code_gen", "write a tide table parser", max_cost=0.0004
        )
        # QWEN3_CODER (0.0005) is over the ceiling; DEEPSEEK_V4_FLASH (0.0002) casts.
        assert consultation.primary_model == "DEEPSEEK_V4_FLASH"
        assert atlas.get(consultation.primary_model).cost_per_1k_tokens <= 0.0004
        assert atlas.get(consultation.critic_model).cost_per_1k_tokens <= 0.0004

    def test_context_cost_ceiling_also_respected(self):
        atlas = ModelAtlas.default()
        answer, critique = TEXTS[Zone.CREATIVE]
        consultation = make_director(answer, critique).cast_with_consult(
            "code_gen", "t", context={"cost_ceiling": 0.0004}
        )
        assert atlas.get(consultation.primary_model).cost_per_1k_tokens <= 0.0004


# ── BackendResolver ──────────────────────────────────────────────────

class TestBackendResolver:
    def test_unknown_model_error_lists_known_mappings(self):
        resolver = BackendResolver({"SEED_MINI": MockBackend(str), "GLM_5_2": MockBackend(str)})
        with pytest.raises(BackendResolutionError) as excinfo:
            resolver.resolve("NEMOTRON_ULTRA")
        message = str(excinfo.value)
        assert "NEMOTRON_ULTRA" in message
        assert "SEED_MINI" in message and "GLM_5_2" in message

    def test_unmapped_director_raises_clear_error(self):
        director = ConsultationDirector(resolver=BackendResolver(), embedder=HashEmbedder())
        with pytest.raises(BackendResolutionError, match="SEED_MINI"):
            director.cast_with_consult("intent_parse", "t")

    def test_register_and_with_overrides(self):
        resolver = BackendResolver()
        resolver.register("SEED_MINI", MockBackend(lambda p: "a"))
        assert resolver.resolve("SEED_MINI").complete("x") == "a"
        richer = resolver.with_overrides(GLM_5_2=MockBackend(lambda p: "b"))
        assert richer.resolve("GLM_5_2").complete("x") == "b"
        with pytest.raises(BackendResolutionError):
            resolver.resolve("GLM_5_2")  # original unchanged


# ── Determinism ──────────────────────────────────────────────────────

class TestDeterminism:
    def test_same_inputs_same_consultation(self):
        answer, critique = TEXTS[Zone.CREATIVE]
        first = make_director(answer, critique).cast_with_consult("intent_parse", "tide log")
        second = make_director(answer, critique).cast_with_consult("intent_parse", "tide log")
        assert first == second
        assert first.swmidi == second.swmidi
