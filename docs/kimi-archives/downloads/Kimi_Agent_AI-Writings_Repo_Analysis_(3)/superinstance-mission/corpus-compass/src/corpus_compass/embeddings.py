"""Embedding interfaces for corpus-compass.

Offline-first: ``HashEmbedder`` is a deterministic token-hashing bag-of-words
embedder (same pattern as peer-consult's, but a small local copy — this package
has no dependency on peer-consult). ``OllamaEmbedder`` talks to a local Ollama
server via urllib and is only used when explicitly requested.

Vectors are stored in sqlite as float32 BLOBs using the ``array`` module
(numpy-free, per SPEC).
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import urllib.request
from array import array
from typing import Protocol, Sequence

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts; one vector per input text."""
        ...


def pack_vector(vec: Sequence[float]) -> bytes:
    """Pack a float vector into a float32 BLOB."""
    return array("f", vec).tobytes()


def unpack_vector(blob: bytes) -> array:
    """Unpack a float32 BLOB into an array of floats."""
    out = array("f")
    out.frombytes(blob)
    return out


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine similarity, stdlib-only."""
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (math.sqrt(na) * math.sqrt(nb))


class HashEmbedder:
    """Deterministic offline embedder: token hashing into a fixed dim,
    L2-normalized. Stable across runs and machines."""

    def __init__(self, dim: int = 256) -> None:
        if dim <= 0:
            raise ValueError("dim must be positive")
        self.dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]

    def _embed_one(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for tok in _TOKEN_RE.findall(text.lower()):
            digest = hashlib.blake2b(tok.encode("utf-8"), digest_size=8).digest()
            h = int.from_bytes(digest, "little")
            idx = h % self.dim
            sign = 1.0 if (h >> 63) & 1 == 0 else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(v * v for v in vec))
        if norm == 0.0:
            return vec
        return [v / norm for v in vec]


class OllamaEmbedder:
    """Ollama embeddings via the local HTTP API (no hard deps; urllib only).
    Only used when the user passes --ollama-embed."""

    def __init__(self, model: str = "nomic-embed-text",
                 host: str = "http://localhost:11434",
                 timeout: float = 60.0) -> None:
        self.model = model
        self.host = host.rstrip("/")
        self.timeout = timeout

    def embed(self, texts: list[str]) -> list[list[float]]:
        url = f"{self.host}/api/embed"
        payload = json.dumps({"model": self.model, "input": texts}).encode("utf-8")
        req = urllib.request.Request(
            url, data=payload, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return [list(map(float, v)) for v in data["embeddings"]]
