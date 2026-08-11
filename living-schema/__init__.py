"""
LIVING SCHEMA — Schema-Driven Personality for LucidDreamer.AI

Hermes Track 1: The Living Schema

Each tile carries its own musical signature, its own tempo, its own personality wrap.
The schema IS the sheet music.

Modules:
    living_schema       — MusicalSignature, PersonalityWrap, LivingTile
    schema_to_music     — Translate personality → musical parameters
    personality_encoder — Extract personality from model behavior history
"""

from living_schema.living_schema import (
    MusicalSignature,
    PersonalityWrap,
    LivingTile,
    Alignment,
    generate_signature_from_personality,
)
from living_schema.schema_to_music import schema_to_music, SchemaMusicProfile
from living_schema.personality_encoder import (
    PersonalityEncoder,
    BehaviorSample,
    EncodedPersonality,
)

__all__ = [
    "MusicalSignature",
    "PersonalityWrap",
    "LivingTile",
    "Alignment",
    "generate_signature_from_personality",
    "schema_to_music",
    "SchemaMusicProfile",
    "PersonalityEncoder",
    "BehaviorSample",
    "EncodedPersonality",
]
