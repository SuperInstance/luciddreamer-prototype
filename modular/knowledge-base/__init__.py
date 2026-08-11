# Knowledge Base package entry point
import sys
import os

_src = os.path.join(os.path.dirname(__file__), "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from idea_schema import (
    IdeaNode,
    IdeaType,
    IdeaStatus,
    RelationshipType,
    Connection,
    RelationshipEdge,
    ModelNode,
    SessionNode,
    detect_idea_type,
    detect_tags,
)
from knowledge_graph import KnowledgeGraph
from vector_integration import KnowledgeBase, LocalStore, D1Store, VectorizeStore, embed_text, embed_idea

__version__ = "0.1.0"
