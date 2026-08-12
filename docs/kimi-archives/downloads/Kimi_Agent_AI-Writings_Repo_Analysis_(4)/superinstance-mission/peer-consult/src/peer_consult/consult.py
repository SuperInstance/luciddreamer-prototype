"""
ConsultationDirector — makes cast() a conversation.

Wraps a casting-call CastingDirector. For each role: the primary model
answers, a critic from the role's own fallback chain (different
VoiceCharacter family — counterpoint, no parallel octaves) attacks the
answer devil's-advocate style, and the semantic distance between answer
and critique decides the verdict.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

try:
    from casting_call import CastingDirector, ModelAtlas, ModelProfile, VoiceCharacter
except ImportError as exc:  # pragma: no cover - exercised only without the dep
    raise ImportError(
        "peer-consult requires casting-call. Install it for development with:\n"
        "    pip install -e /mnt/agents/repos/casting-call\n"
        "(or `pip install casting-call` once it is published)."
    ) from exc

try:  # public API first; fall back to the module-level chain
    from casting_call.casting import ROLE_FALLBACKS as _ROLE_FALLBACKS  # type: ignore[attr-defined]
except ImportError:
    try:
        from casting_call.casting import _ROLE_FALLBACKS  # canonical chain
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "peer-consult needs the role fallback chain from casting_call.casting "
            "(_ROLE_FALLBACKS). Your casting-call install does not provide it — "
            "reinstall with: pip install -e /mnt/agents/repos/casting-call"
        ) from exc

from peer_consult.backends import ModelBackend
from peer_consult.embeddings import Embedder, HashEmbedder, Zone, classify_zone, delta
from peer_consult.swmidi import (
    EVENT_CAST,
    EVENT_CONSULT,
    EVENT_VERDICT,
    FRICTION_SEMANTIC,
    PPQ,
    STATUS_NOTE_ON,
    encode_event,
    profile_channel,
)

SAFETY_ROLE = "safety_check"


class Verdict(str, Enum):
    """What the consultation concluded."""

    CONFIRM = "confirm"    # STALE band — redundant agreement
    REVISE = "revise"      # CREATIVE band (0.40–0.60) — productive divergence
    ESCALATE = "escalate"  # CHAOTIC band (>0.80) — route to safety_check model
    NOTE = "note"          # transitional bands — divergence noted, no action


VERDICT_FOR_ZONE: dict[Zone, Verdict] = {
    Zone.STALE: Verdict.CONFIRM,
    Zone.CREATIVE: Verdict.REVISE,
    Zone.CHAOTIC: Verdict.ESCALATE,
    Zone.TRANSITIONAL_LOW: Verdict.NOTE,
    Zone.TRANSITIONAL_HIGH: Verdict.NOTE,
}


@dataclass(frozen=True)
class Consultation:
    """One cast-with-consult round, fully recorded."""

    role: str
    primary_model: str
    critic_model: str
    primary_answer: str
    critique: str
    delta: float
    zone: Zone
    verdict: Verdict
    rationale: str
    swmidi: bytes


class BackendResolutionError(LookupError):
    """Raised when no backend is mapped for a cast model."""


class BackendResolver:
    """
    Maps atlas model names → ModelBackend.

    `mapping` holds the explicit overrides. An optional `factory` may
    synthesize a backend for names not in the mapping (return None to
    decline). Unknown models raise BackendResolutionError listing the
    known mappings.
    """

    def __init__(
        self,
        mapping: Optional[dict[str, ModelBackend]] = None,
        *,
        factory: Optional[Callable[[str], Optional[ModelBackend]]] = None,
    ):
        self._mapping: dict[str, ModelBackend] = dict(mapping or {})
        self._factory = factory

    def register(self, name: str, backend: ModelBackend) -> None:
        """Add or replace an explicit override."""
        self._mapping[name] = backend

    def with_overrides(self, **overrides: ModelBackend) -> "BackendResolver":
        """Return a new resolver with additional explicit overrides."""
        merged = dict(self._mapping)
        merged.update(overrides)
        return BackendResolver(merged, factory=self._factory)

    def known(self) -> list[str]:
        return sorted(self._mapping)

    def resolve(self, name: str) -> ModelBackend:
        if name in self._mapping:
            return self._mapping[name]
        if self._factory is not None:
            backend = self._factory(name)
            if backend is not None:
                return backend
        known = ", ".join(self.known()) or "(none)"
        raise BackendResolutionError(
            f"No backend mapped for model {name!r}. Known mappings: {known}. "
            f"Register one with BackendResolver.register({name!r}, backend) "
            f"or pass --ollama-model-map on the CLI."
        )


# Voice families: members of a family are timbral near-octaves, so pairing
# primary and critic inside one family would be parallel octaves.
_VOICE_FAMILY: dict[VoiceCharacter, str] = {
    VoiceCharacter.KURZWEIL: "kurzweil",
    VoiceCharacter.KURZWEIL_JR: "kurzweil",
    VoiceCharacter.ANALOG_SYNTH: "analog_synth",
    VoiceCharacter.ANALOG_SYNTH_PRO: "analog_synth",
}


def voice_family(voice: VoiceCharacter) -> str:
    """The counterpoint family of a VoiceCharacter."""
    return _VOICE_FAMILY.get(voice, voice.value)


def select_critic(
    atlas: ModelAtlas,
    role: str,
    primary: ModelProfile,
    *,
    cost_ceiling: Optional[float] = None,
) -> ModelProfile:
    """
    The critic = the next model in the role's fallback chain with a
    DIFFERENT VoiceCharacter family than the primary (counterpoint
    constraint — no parallel octaves).

    Falls back to the cheapest different-family model in the atlas when the
    chain offers none. Raises ValueError if no eligible critic exists.
    """
    primary_family = voice_family(primary.voice_character)

    def eligible(profile: Optional[ModelProfile]) -> bool:
        if profile is None or profile.name == primary.name:
            return False
        if cost_ceiling is not None and profile.cost_per_1k_tokens > cost_ceiling:
            return False
        return voice_family(profile.voice_character) != primary_family

    for name in _ROLE_FALLBACKS.get(role, []):
        candidate = atlas.get(name)
        if eligible(candidate):
            return candidate  # type: ignore[return-value]

    # Chain exhausted — scan the atlas, cheapest first, deterministic.
    rest = sorted(atlas.all(), key=lambda m: (m.cost_per_1k_tokens, m.name))
    for candidate in rest:
        if eligible(candidate):
            return candidate

    raise ValueError(
        f"No eligible critic for role {role!r}: every model shares the "
        f"{primary_family!r} voice family of {primary.name}"
        + (f" or exceeds the cost ceiling {cost_ceiling}." if cost_ceiling is not None else ".")
    )


_PRIMARY_PROMPT = """You are cast as the '{role}' model. Answer the task directly.

Task: {task}
"""

_CRITIC_PROMPT = """You are the critic — the devil's advocate. Challenge the assumptions in \
the answer below. Do not agree by default: find the weakest assumption and attack it. \
Be specific, be brief.

Role: {role}
Task: {task}

{primary_model}'s answer:
\"\"\"
{answer}
\"\"\"

Your critique:
"""


class ConsultationDirector:
    """
    Wraps a CastingDirector and turns cast() into a conversation.

    Constructor-injected: a CastingDirector (default: fresh director over
    the default atlas), a BackendResolver mapping model names to backends,
    and an Embedder (default: offline HashEmbedder).
    """

    def __init__(
        self,
        director: Optional[CastingDirector] = None,
        resolver: Optional[BackendResolver] = None,
        embedder: Optional[Embedder] = None,
    ):
        self.director = director or CastingDirector(ModelAtlas.default())
        self.resolver = resolver or BackendResolver()
        self.embedder = embedder or HashEmbedder()

    def cast_with_consult(
        self,
        role: str,
        task: str,
        *,
        context: Optional[dict] = None,
        max_cost: Optional[float] = None,
    ) -> Consultation:
        """
        Cast a role, get the primary's answer, consult a critic, and rule
        on the divergence.

        Steps: cast → answer → critique → Δ → zone → verdict → SWMIDI-8
        (cast=1, consult=2, verdict=3 on the primary's atlas channel).
        """
        ctx = dict(context or {})
        if max_cost is not None:
            ctx["cost_ceiling"] = max_cost

        # a. Cast primary; pick the critic from the role's fallback chain.
        primary = self.director.cast(role, ctx)
        critic = select_critic(
            self.director.atlas, role, primary, cost_ceiling=ctx.get("cost_ceiling")
        )

        # b. Primary answers; critic challenges devil's-advocate style.
        primary_backend = self.resolver.resolve(primary.name)
        critic_backend = self.resolver.resolve(critic.name)
        answer = primary_backend.complete(
            _PRIMARY_PROMPT.format(role=role, task=task),
            temperature=primary.temperature,
        )
        critique = critic_backend.complete(
            _CRITIC_PROMPT.format(role=role, task=task, primary_model=primary.name, answer=answer),
            temperature=critic.temperature,
        )

        # c. Δ → zone → verdict.
        vec_answer, vec_critique = self.embedder.embed([answer, critique])
        d = delta(vec_answer, vec_critique)
        zone = classify_zone(d)
        verdict = VERDICT_FOR_ZONE[zone]
        rationale = self._rationale(verdict, zone, d, critique)

        # d. SWMIDI-8: cast=1, consult=2, verdict=3 on the primary's channel.
        swmidi = self._encode_events(primary, d, zone)

        return Consultation(
            role=role,
            primary_model=primary.name,
            critic_model=critic.name,
            primary_answer=answer,
            critique=critique,
            delta=d,
            zone=zone,
            verdict=verdict,
            rationale=rationale,
            swmidi=swmidi,
        )

    def _rationale(self, verdict: Verdict, zone: Zone, d: float, critique: str) -> str:
        if verdict is Verdict.CONFIRM:
            return (
                f"STALE band (Δ={d:.3f}): the critic converged on the primary's "
                f"answer — redundant agreement. Confirmed."
            )
        if verdict is Verdict.REVISE:
            return (
                f"CREATIVE band (Δ={d:.3f}): productive divergence. Revise by merging "
                f"the critic's objections: {critique.strip()}"
            )
        if verdict is Verdict.ESCALATE:
            safety = self.director.cast(SAFETY_ROLE)
            return (
                f"CHAOTIC band (Δ={d:.3f}): divergence beyond safe disagreement. "
                f"Escalating to {safety.name} (the {SAFETY_ROLE} role model per atlas)."
            )
        return (
            f"{zone.value} band (Δ={d:.3f}): transitional divergence noted; "
            f"no action required."
        )

    @staticmethod
    def _encode_events(primary: ModelProfile, d: float, zone: Zone) -> bytes:
        channel = profile_channel(primary)
        confidence = 1.0 - d
        velocity = max(0, min(127, round(confidence * 127)))
        error_mask = FRICTION_SEMANTIC if zone is Zone.CHAOTIC else 0
        events = (
            (EVENT_CAST, 0),
            (EVENT_CONSULT, PPQ),
            (EVENT_VERDICT, 2 * PPQ),
        )
        return b"".join(
            encode_event(STATUS_NOTE_ON, channel, pitch, velocity, error_mask, tick)
            for pitch, tick in events
        )
