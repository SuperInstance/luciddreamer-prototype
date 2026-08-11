"""
LucidDreamer Recursive Knowledge Base
======================================

A structured knowledge base that holds ideas, relationships, evolutions,
and contradictions — and grows smarter as we feed it.

Components:
    idea_schema       — Data structures (IdeaNode, SessionNode, ModelNode, etc.)
    knowledge_graph   — Graph layer (contradictions, convergence, orphans, lineage)
    vector_integration — Dual storage (local pickle + D1 + Vectorize)
    ingest_session    — Markdown extraction (Tap sessions, research docs → ideas)
    query             — Query CLI (contradictions, convergence, lineage, etc.)
    build_knowledge_base — One-shot builder that ingests all sources

Usage:
    from idea_schema import IdeaNode, IdeaType
    from knowledge_graph import KnowledgeGraph
    from vector_integration import KnowledgeBase

    kb = KnowledgeBase()
    kb.load()
    print(kb.summary())
"""
