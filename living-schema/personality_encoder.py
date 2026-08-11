"""
PERSONALITY ENCODER — Generates PersonalityWraps from model behavior.

Analyzes a model's output history and extracts behavioral signals:
    - verbosity (how much it says)
    - vocabulary richness (how diverse its language is)
    - risk patterns (does it play safe or take chances?)
    - emotional range (stoic or expressive?)

These signals are encoded into a PersonalityWrap that travels with every
interaction. The personality IS the music — the wrap determines what
the tile sounds like.

Hermes Track 1: The Living Schema
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, field
from typing import Optional

try:
    from .core import (
        Alignment,
        PersonalityWrap,
    )
except ImportError:
    from core import (
        Alignment,
        PersonalityWrap,
    )


# ─── Behavior Sample ─────────────────────────────────────────────────────────

@dataclass
class BehaviorSample:
    """
    A single sample of model behavior — one output to analyze.
    """
    model_name: str
    content: str
    confidence: float = 0.5         # model's stated or inferred confidence
    metadata: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "BehaviorSample":
        return cls(
            model_name=data.get("model_name", data.get("model", "unknown")),
            content=data.get("content", data.get("text", data.get("message", ""))),
            confidence=data.get("confidence", data.get("score", 0.5)),
            metadata=data.get("metadata", {}),
        )


# ─── Encoded Personality ─────────────────────────────────────────────────────

@dataclass
class EncodedPersonality:
    """
    The result of encoding model behavior into a personality.
    Includes the raw measurements alongside the final PersonalityWrap.
    """
    # The final wrap
    wrap: PersonalityWrap

    # Raw measurements (for debugging/display)
    avg_length: int = 0
    unique_word_ratio: float = 0.0
    question_rate: float = 0.0
    hedge_rate: float = 0.0
    exclamation_rate: float = 0.0
    uncertainty_rate: float = 0.0
    creative_word_count: int = 0
    emotional_word_count: int = 0
    sample_count: int = 0

    def summary(self) -> str:
        """Human-readable encoding summary."""
        return (
            f"EncodedPersonality [{self.wrap.model_name}]\n"
            f"  Samples analyzed: {self.sample_count}\n"
            f"  Avg length: {self.avg_length} chars\n"
            f"  Unique word ratio: {self.unique_word_ratio:.3f}\n"
            f"  Question rate: {self.question_rate:.2f}\n"
            f"  Hedge rate: {self.hedge_rate:.2f}\n"
            f"  Creative words: {self.creative_word_count}\n"
            f"  Emotional words: {self.emotional_word_count}\n"
            f"  → {self.wrap.summary()}"
        )


# ─── Vocabulary Sets ─────────────────────────────────────────────────────────

# Hedge words indicate uncertainty or caution
HEDGE_WORDS = {
    "maybe", "perhaps", "possibly", "might", "could", "possibly", "probably",
    "likely", "seems", "appears", "suggests", "i think", "i believe",
    "arguably", "supposedly", "presumably", "potentially", "conceivably",
    "it seems", "it appears", "it's possible", "uncertain", "unsure",
    "approximately", "roughly", "around", "about", "more or less",
    "as far as i know", "to my knowledge", "if i recall",
}

# Creative/unusual word set — indicates willingness to use non-standard language
CREATIVE_WORDS = {
    "luminous", "ephemeral", "cacophony", "tessellated", "iridescent",
    "serendipity", "mellifluous", "petrichor", "sonder", "saudade",
    "ineffable", "numinous", "liminal", "palimpsest", "apocryphal",
    "vertiginous", "cinerious", "sussurant", "susurrus", "vellichor",
    "chrysalis", "palimpsest", "phantasmagoria", "halcyon", "velvet",
    "shimmering", "crystalline", "labyrinthine", "kaleidoscopic",
    "resonant", "translucent", "gossamer", "incandescent", "mercurial",
    "quicksilver", "prismatic", "ethereal", "opalescent", "vermilion",
    "celadon", "cobalt", "umber", "sienna", "phthalo",
    "chromatic", "polyphonic", "contrapuntal", "dissonant", "atonal",
    "palimpsest", "parallax", "syzygy", "penumbra", "aubade",
}

# Emotional words — indicate expressive range
EMOTIONAL_WORDS = {
    # Positive
    "joy", "love", "wonder", "beautiful", "amazing", "incredible",
    "heartbreak", "thrilled", "delighted", "exuberant", "radiant",
    "tender", "warm", "aching", "yearning", "longing", "nostalgia",
    "exhilaration", "rapture", "bliss", "serene", "tranquil",
    # Negative
    "angry", "furious", "devastated", "melancholy", "despair",
    "anguish", "sorrow", "grief", "mournful", "wistful", "forlorn",
    "bitter", "wrenching", "haunting", "ominous", "dread",
    # Intense
    "passionate", "fierce", "turbulent", "tempestuous", "volcanic",
    "electric", "incandescent", "blazing", "simmering", "smoldering",
    # Nuanced
    "bittersweet", "poignant", "tender", "vulnerable", "fragile",
    "resilient", "defiant", "reckless", "audacious", "brazen",
}

# Uncertainty indicators
UNCERTAINTY_PHRASES = {
    "i don't know", "i'm not sure", "i can't be certain", "it's unclear",
    "hard to say", "difficult to determine", "i'm uncertain",
    "not confident", "unsure about", "no clear answer",
    "i might be wrong", "i could be mistaken", "treat with caution",
}


# ─── Text Analysis Functions ─────────────────────────────────────────────────

def _tokenize(text: str) -> list[str]:
    """Simple tokenizer — lowercase, strip punctuation, split on whitespace."""
    text = text.lower().strip()
    # Keep apostrophes within words, remove other punctuation
    text = re.sub(r"[^\w\s']", " ", text)
    return text.split()


def _count_hedges(text: str) -> int:
    """Count hedge word/phrase occurrences."""
    text_lower = text.lower()
    count = 0
    for hedge in HEDGE_WORDS:
        count += text_lower.count(hedge)
    return count


def _count_creative_words(text: str) -> int:
    """Count creative/unusual word usage."""
    tokens = set(_tokenize(text))
    return len(tokens & CREATIVE_WORDS)


def _count_emotional_words(text: str) -> int:
    """Count emotional word usage."""
    tokens = set(_tokenize(text))
    return len(tokens & EMOTIONAL_WORDS)


def _count_uncertainty(text: str) -> int:
    """Count uncertainty phrase occurrences."""
    text_lower = text.lower()
    count = 0
    for phrase in UNCERTAINTY_PHRASES:
        count += text_lower.count(phrase)
    return count


def _unique_word_ratio(text: str) -> float:
    """
    Calculate vocabulary diversity: unique words / total words.
    Higher = richer vocabulary.
    """
    tokens = _tokenize(text)
    if not tokens:
        return 0.0
    return len(set(tokens)) / len(tokens)


# ─── Personality Encoder ─────────────────────────────────────────────────────

class PersonalityEncoder:
    """
    Encodes model behavior into PersonalityWraps.

    Analyzes a model's output history and extracts behavioral patterns.
    These patterns become a PersonalityWrap that determines musical identity.

    Usage:
        encoder = PersonalityEncoder()
        samples = [BehaviorSample(...), ...]
        encoded = encoder.encode(samples)
        wrap = encoded.wrap  # use this as the personality
    """

    def __init__(
        self,
        # Weights for combining signals (can be tuned)
        creativity_weight_creative: float = 0.5,
        creativity_weight_vocabulary: float = 0.3,
        creativity_weight_risk: float = 0.2,
    ):
        self.w_creative = creativity_weight_creative
        self.w_vocab = creativity_weight_vocabulary
        self.w_risk = creativity_weight_risk

    def encode(self, samples: list[BehaviorSample]) -> EncodedPersonality:
        """
        Analyze a list of behavior samples and produce a PersonalityWrap.
        """
        if not samples:
            return EncodedPersonality(
                wrap=PersonalityWrap(model_name="unknown"),
                sample_count=0,
            )

        model_name = samples[0].model_name
        n = len(samples)
        all_text = " ".join(s.content for s in samples)

        # --- Measure raw signals ---

        # 1. Verbosity: average response length
        lengths = [len(s.content) for s in samples]
        avg_length = sum(lengths) // n if n else 0

        # 2. Vocabulary richness: average unique word ratio across samples
        ratios = [_unique_word_ratio(s.content) for s in samples]
        avg_unique_ratio = sum(ratios) / n if n else 0.0

        # 3. Question rate: questions per sample
        questions = [s.content.count("?") for s in samples]
        total_questions = sum(questions)
        question_rate = total_questions / n if n else 0.0

        # 4. Hedge rate: hedge phrases per sample
        hedges = [_count_hedges(s.content) for s in samples]
        total_hedges = sum(hedges)
        hedge_rate = total_hedges / n if n else 0.0

        # 5. Exclamation rate
        exclamations = [s.content.count("!") for s in samples]
        total_exclamations = sum(exclamations)
        exclamation_rate = total_exclamations / n if n else 0.0

        # 6. Uncertainty rate
        uncertainties = [_count_uncertainty(s.content) for s in samples]
        total_uncertainties = sum(uncertainties)
        uncertainty_rate = total_uncertainties / n if n else 0.0

        # 7. Creative word usage
        creative_counts = [_count_creative_words(s.content) for s in samples]
        total_creative = sum(creative_counts)
        creative_per_sample = total_creative / n if n else 0.0

        # 8. Emotional word usage
        emotional_counts = [_count_emotional_words(s.content) for s in samples]
        total_emotional = sum(emotional_counts)
        emotional_per_sample = total_emotional / n if n else 0.0

        # 9. Confidence
        avg_confidence = sum(s.confidence for s in samples) / n if n else 0.5

        # --- Normalize to 0.0–1.0 ---

        # Verbosity: normalize around a sweet spot of ~300 chars
        # <50 chars = very terse (0.1), ~300 = moderate (0.5), >1000 = very verbose (0.9)
        verbosity = self._normalize_verbosity(avg_length)

        # Vocabulary richness: unique word ratio is already ~0.0–0.8
        vocabulary_richness = min(1.0, avg_unique_ratio / 0.6)  # 0.6 ratio ≈ max

        # Creativity score: blend creative word usage + vocabulary + risk signals
        creative_norm = min(1.0, creative_per_sample / 3.0)  # 3 creative words/sample ≈ max
        vocab_norm = vocabulary_richness
        # Risk proxy: low hedge + low uncertainty + high creative = more creative
        risk_proxy = max(0.0, 1.0 - (hedge_rate * 0.3) - (uncertainty_rate * 0.3))

        creativity_score = (
            creative_norm * self.w_creative
            + vocab_norm * self.w_vocab
            + risk_proxy * self.w_risk
        )
        creativity_score = min(1.0, max(0.0, creativity_score))

        # Risk tolerance: inversely related to hedging and uncertainty
        # Also boosted by exclamation usage (bold expression)
        risk_tolerance = max(0.0, min(1.0,
            0.5 + (exclamation_rate * 0.1) - (hedge_rate * 0.15) - (uncertainty_rate * 0.2)
            + (creative_norm * 0.1)
        ))

        # Emotional range: from emotional word density
        emotional_range = min(1.0, emotional_per_sample / 4.0)  # 4 emotional words/sample ≈ max

        # Tendency to question
        tendency_to_question = min(1.0, question_rate / 2.0)  # 2 questions/sample ≈ max

        # Tendency to hedge
        tendency_to_hedge = min(1.0, hedge_rate / 2.0)

        # Alignment from creativity score
        alignment = Alignment.from_score(creativity_score)

        # Confidence at birth = average confidence from samples
        confidence_at_birth = max(0.0, min(1.0, avg_confidence))

        # --- Build the wrap ---
        wrap = PersonalityWrap(
            alignment=alignment,
            risk_tolerance=round(risk_tolerance, 3),
            creativity_score=round(creativity_score, 3),
            confidence_at_birth=round(confidence_at_birth, 3),
            verbosity=round(verbosity, 3),
            vocabulary_richness=round(vocabulary_richness, 3),
            emotional_range=round(emotional_range, 3),
            avg_response_length=avg_length,
            tendency_to_question=round(tendency_to_question, 3),
            tendency_to_hedge=round(tendency_to_hedge, 3),
            model_name=model_name,
        )

        return EncodedPersonality(
            wrap=wrap,
            avg_length=avg_length,
            unique_word_ratio=round(avg_unique_ratio, 3),
            question_rate=round(question_rate, 3),
            hedge_rate=round(hedge_rate, 3),
            exclamation_rate=round(exclamation_rate, 3),
            uncertainty_rate=round(uncertainty_rate, 3),
            creative_word_count=total_creative,
            emotional_word_count=total_emotional,
            sample_count=n,
        )

    def encode_single(
        self,
        model_name: str,
        content: str,
        confidence: float = 0.5,
    ) -> EncodedPersonality:
        """Convenience: encode a single output into a personality."""
        sample = BehaviorSample(
            model_name=model_name,
            content=content,
            confidence=confidence,
        )
        return self.encode([sample])

    @staticmethod
    def _normalize_verbosity(avg_length: int) -> float:
        """
        Normalize average response length to 0.0–1.0 verbosity.

        Mapping:
            0 chars   → 0.0 (silent)
            50 chars  → 0.15 (very terse)
            150 chars → 0.35 (concise)
            300 chars → 0.50 (moderate)
            600 chars → 0.70 (verbose)
            1000+     → 0.90+ (very verbose)
        """
        if avg_length <= 0:
            return 0.0
        # Use a curve that gives good spread
        # Sigmoid-like: clamps to 0-1 with nice sensitivity in the 100-600 range
        normalized = 1.0 / (1.0 + math.exp(-(avg_length - 300) / 200))
        return round(max(0.0, min(1.0, normalized)), 3)

    @staticmethod
    def merge_personalities(
        personalities: list[PersonalityWrap],
        weights: Optional[list[float]] = None,
    ) -> PersonalityWrap:
        """
        Merge multiple personality wraps into a composite.
        Useful when a model behaves differently across contexts.
        """
        if not personalities:
            return PersonalityWrap()
        if len(personalities) == 1:
            return personalities[0]

        if weights is None:
            weights = [1.0 / len(personalities)] * len(personalities)
        else:
            total = sum(weights)
            weights = [w / total for w in weights]

        # Weighted average of numeric traits
        def weighted(getter) -> float:
            return sum(getter(p) * w for p, w in zip(personalities, weights))

        avg_creativity = weighted(lambda p: p.creativity_score)
        avg_risk = weighted(lambda p: p.risk_tolerance)
        avg_confidence = weighted(lambda p: p.confidence_at_birth)
        avg_verbosity = weighted(lambda p: p.verbosity)
        avg_vocab = weighted(lambda p: p.vocabulary_richness)
        avg_emotional = weighted(lambda p: p.emotional_range)
        avg_question = weighted(lambda p: p.tendency_to_question)
        avg_hedge = weighted(lambda p: p.tendency_to_hedge)
        avg_length = int(weighted(lambda p: p.avg_response_length))

        alignment = Alignment.from_score(avg_creativity)

        return PersonalityWrap(
            alignment=alignment,
            risk_tolerance=round(avg_risk, 3),
            creativity_score=round(avg_creativity, 3),
            confidence_at_birth=round(avg_confidence, 3),
            verbosity=round(avg_verbosity, 3),
            vocabulary_richness=round(avg_vocab, 3),
            emotional_range=round(avg_emotional, 3),
            avg_response_length=avg_length,
            tendency_to_question=round(avg_question, 3),
            tendency_to_hedge=round(avg_hedge, 3),
            model_name=personalities[0].model_name,
        )


# ─── Quick API ───────────────────────────────────────────────────────────────

def encode_personality(
    model_name: str,
    outputs: list[str],
    confidence: float = 0.5,
) -> PersonalityWrap:
    """
    Quick-start API: give a model name and its outputs, get a PersonalityWrap.
    """
    encoder = PersonalityEncoder()
    samples = [
        BehaviorSample(model_name=model_name, content=out, confidence=confidence)
        for out in outputs
    ]
    return encoder.encode(samples).wrap
