"""
Embeddings and semantic distance — the batten-spline layer.

Δ semantic distance = 1 − cosine on L2-normalized embeddings. Zones:
STALE <0.20, TRANSITIONAL_LOW 0.20–0.40, CREATIVE 0.40–0.60,
TRANSITIONAL_HIGH 0.60–0.80, CHAOTIC >0.80.

`HashEmbedder` is fully offline and deterministic — it is the only
embedder the test suite uses.
"""

from __future__ import annotations

import hashlib
import math
import os
import re
from enum import Enum
from typing import Protocol, runtime_checkable

from peer_consult.backends import _post_json


@runtime_checkable
class Embedder(Protocol):
    """Anything that turns texts into vectors."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        ...


class Zone(str, Enum):
    """Semantic-distance zones (batten-spline bands)."""

    STALE = "stale"                          # < 0.20 — redundant agreement
    TRANSITIONAL_LOW = "transitional_low"    # 0.20–0.40
    CREATIVE = "creative"                    # 0.40–0.60 — productive divergence
    TRANSITIONAL_HIGH = "transitional_high"  # 0.60–0.80
    CHAOTIC = "chaotic"                      # > 0.80 — escalate


# Zone band edges (see SPEC research context — binding).
STALE_MAX = 0.20
TRANSITIONAL_LOW_MAX = 0.40
CREATIVE_MAX = 0.60
TRANSITIONAL_HIGH_MAX = 0.80


def classify_zone(d: float) -> Zone:
    """Map a semantic distance to its zone band."""
    if d < STALE_MAX:
        return Zone.STALE
    if d < TRANSITIONAL_LOW_MAX:
        return Zone.TRANSITIONAL_LOW
    if d <= CREATIVE_MAX:
        return Zone.CREATIVE
    if d <= TRANSITIONAL_HIGH_MAX:
        return Zone.TRANSITIONAL_HIGH
    return Zone.CHAOTIC


def _l2_normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0.0:
        return list(vec)
    return [x / norm for x in vec]


def delta(a: list[float], b: list[float]) -> float:
    """
    Semantic distance: 1 − cosine(a, b).

    Inputs are expected L2-normalized, but the cosine is computed
    defensively. A zero vector is maximally distant from everything (Δ = 1).
    """
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 1.0
    dot = sum(x * y for x, y in zip(a, b))
    cosine = dot / (norm_a * norm_b)
    cosine = max(-1.0, min(1.0, cosine))  # float drift guard
    return 1.0 - cosine


_TOKEN_RE = re.compile(r"[a-z0-9]+")


class HashEmbedder:
    """
    Deterministic token-hashing bag-of-words embedder. OFFLINE.

    Each lowercase alphanumeric token is hashed (SHA-256, so no PYTHONHASHSEED
    nondeterminism) into one of `dim` buckets; the count vector is then
    L2-normalized. Identical texts → identical vectors → Δ = 0.
    """

    def __init__(self, dim: int = 256):
        if dim <= 0:
            raise ValueError("dim must be positive")
        self.dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for token in _TOKEN_RE.findall(text.lower()):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:4], "little") % self.dim
            vec[bucket] += 1.0
        return _l2_normalize(vec)


class OllamaEmbedder:
    """Local embeddings via Ollama's /api/embeddings endpoint."""

    def __init__(self, model: str = "nomic-embed-text", host: str = "http://localhost:11434", *, timeout: float = 120.0):
        self.model = model
        self.host = host.rstrip("/")
        self.timeout = timeout

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            payload = {"model": self.model, "prompt": text}
            data = _post_json(f"{self.host}/api/embeddings", payload, timeout=self.timeout)
            vectors.append(_l2_normalize([float(x) for x in data["embedding"]]))
        return vectors


class DeepInfraEmbedder:
    """
    DeepInfra embeddings via the OpenAI-compatible endpoint.

    Default model BAAI/bge-m3. API key from DEEPINFRA_API_KEY unless passed
    explicitly.
    """

    EMBED_URL = "https://api.deepinfra.com/v1/openai/embeddings"

    def __init__(self, model: str = "BAAI/bge-m3", api_key: str | None = None, *, timeout: float = 120.0):
        self.model = model
        self.api_key = api_key or os.environ.get("DEEPINFRA_API_KEY")
        self.timeout = timeout

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not self.api_key:
            raise RuntimeError(
                "DeepInfraEmbedder needs an API key. Set DEEPINFRA_API_KEY or pass api_key=."
            )
        payload = {"model": self.model, "input": texts}
        headers = {"Authorization": f"Bearer {self.api_key}"}
        data = _post_json(self.EMBED_URL, payload, headers=headers, timeout=self.timeout)
        rows = sorted(data["data"], key=lambda row: row["index"])
        return [_l2_normalize([float(x) for x in row["embedding"]]) for row in rows]
