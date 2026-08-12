"""
peer-consult — the peer consultation layer for casting-call.

Models don't consult each other in casting-call; this package makes cast()
a conversation. The primary model answers, a critic from the role's own
fallback chain (different VoiceCharacter family — no parallel octaves)
attacks the answer, and the semantic distance between them rules the
verdict: CONFIRM, REVISE, ESCALATE, or NOTE.

    >>> from peer_consult import ConsultationDirector, BackendResolver, MockBackend, HashEmbedder
    >>> resolver = BackendResolver(factory=lambda name: MockBackend(lambda p: "answer"))
    >>> director = ConsultationDirector(resolver=resolver, embedder=HashEmbedder())
    >>> consultation = director.cast_with_consult("intent_parse", "summarize the tide log")
    >>> consultation.verdict.value
    'confirm'
"""

from peer_consult.backends import (
    DeepInfraBackend,
    DeepSeekBackend,
    MockBackend,
    ModelBackend,
    OllamaBackend,
)
from peer_consult.consult import (
    BackendResolutionError,
    BackendResolver,
    Consultation,
    ConsultationDirector,
    Verdict,
    select_critic,
    voice_family,
)
from peer_consult.embeddings import (
    DeepInfraEmbedder,
    Embedder,
    HashEmbedder,
    OllamaEmbedder,
    Zone,
    classify_zone,
    delta,
)
from peer_consult.swmidi import (
    EVENT_CAST,
    EVENT_CONSULT,
    EVENT_VERDICT,
    FRICTION_SEMANTIC,
    PPQ,
    STATUS_NOTE_ON,
    decode_event,
    encode_event,
    profile_channel,
)

__all__ = [
    # backends
    "ModelBackend",
    "OllamaBackend",
    "DeepInfraBackend",
    "DeepSeekBackend",
    "MockBackend",
    # embeddings
    "Embedder",
    "HashEmbedder",
    "OllamaEmbedder",
    "DeepInfraEmbedder",
    "Zone",
    "classify_zone",
    "delta",
    # consult
    "Consultation",
    "ConsultationDirector",
    "BackendResolver",
    "BackendResolutionError",
    "Verdict",
    "select_critic",
    "voice_family",
    # swmidi
    "encode_event",
    "decode_event",
    "profile_channel",
    "EVENT_CAST",
    "EVENT_CONSULT",
    "EVENT_VERDICT",
    "STATUS_NOTE_ON",
    "FRICTION_SEMANTIC",
    "PPQ",
]

__version__ = "0.1.0"
