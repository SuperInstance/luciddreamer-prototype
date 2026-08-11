"""corpus-compass: AI-Writings retrieval + self-indexing."""

from .digest import generate_digest
from .embeddings import Embedder, HashEmbedder, OllamaEmbedder
from .index import IndexStats, build_index, persona_for_path
from .search import SearchResult, search, vibe_search

__all__ = [
    "Embedder",
    "HashEmbedder",
    "IndexStats",
    "OllamaEmbedder",
    "SearchResult",
    "build_index",
    "generate_digest",
    "persona_for_path",
    "search",
    "vibe_search",
]
