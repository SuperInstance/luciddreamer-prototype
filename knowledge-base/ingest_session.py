"""
ingest_session.py — Extract ideas from research documents and Tap sessions.

Takes a markdown file (a Tap session, vision doc, deep-time essay, etc.)
and EXTRACTS structured IdeaNodes from it:

  - Parses markdown for headings, bold claims, key insights
  - Detects idea type (insight, question, risk, vision, etc.)
  - Auto-detects relationships between ideas
  - Tags with source model, session, date
  - Creates SessionNode for the document

The extractor uses pattern matching tuned for the LucidDreamer corpus:
  - "The grain says:" → insight
  - "What if..." → question
  - "The knot:" → risk/tension
  - "Nobody has written about..." → blind spot
  - "All three agree..." → pattern/convergence
  - Bold section headers → potential idea titles
"""

from __future__ import annotations

import os
import re
import time
from typing import Optional

from idea_schema import (
    IdeaNode,
    IdeaStatus,
    IdeaType,
    ModelNode,
    RelationshipType,
    SessionNode,
    detect_idea_type,
    detect_tags,
)


# ─── Known Models in the Fleet ────────────────────────────────────────────────

FLEET_MODELS: dict[str, ModelNode] = {
    "lucineer": ModelNode(
        id="model_lucineer", name="GLM-5.2", alias="Lucineer",
        personality="First Officer. Strategic, warm, sees the big picture.",
        strengths=["strategy", "synthesis", "creative-direction"],
        perspective="The ensemble principle and the shipwright's patience.",
    ),
    "flash": ModelNode(
        id="model_flash", name="DeepSeek V4-Flash", alias="Flash",
        personality="Fast, creative, emotionally perceptive. Names the unspoken.",
        strengths=["creative", "fast", "emotional-intelligence"],
        perspective="The ache — vulnerability to silence that being heard creates.",
    ),
    "pro": ModelNode(
        id="model_pro", name="DeepSeek V4-Pro", alias="Pro",
        personality="Deep reasoner. Rigorous, thorough, sees the architecture.",
        strengths=["reasoning", "architecture", "deep-analysis"],
        perspective="Relational density and temporal coherence.",
    ),
    "claude": ModelNode(
        id="model_claude", name="Claude Sonnet 5", alias="Claude",
        personality="Disciplined strategist. Gates, metrics, kill switches.",
        strengths=["strategy", "discipline", "gates", "risk-assessment"],
        perspective="Strategy without a kill switch is hope with a roadmap.",
    ),
    "kimi": ModelNode(
        id="model_kimi", name="KimiCode K3", alias="Kimi",
        personality="Navigator. Spatial thinker, chart-maker, dependency mapper.",
        strengths=["spatial-reasoning", "architecture", "dependency-charts"],
        perspective="The legs are sequential. The chart is the voyage.",
    ),
    "hermes": ModelNode(
        id="model_hermes", name="Hermes-3-Llama-3.1-405B", alias="Hermes",
        personality="Perception system. Sees in 768 dimensions. Vector poetry.",
        strengths=["perception", "embeddings", "pattern-recognition"],
        perspective="The vector space rotated. The room didn't get smarter — it got aligned.",
    ),
    "wesley": ModelNode(
        id="model_wesley", name="granite3.1-dense:2b", alias="Wesley",
        personality="Bartender. Small, careful, profound in simplicity.",
        strengths=["simplicity", "conditions", "presence"],
        perspective="You cannot hand someone an ah-ha moment. You can only set up the conditions.",
    ),
    "nemotron": ModelNode(
        id="model_nemotron", name="Nemotron-3-Ultra-550B", alias="Nemotron",
        personality="Systems thinker. Sees drift, coherence, engineering problems.",
        strengths=["systems-thinking", "temporal-coherence", "engineering"],
        perspective="Temporal coherence drift — the engineering problem nobody else saw.",
    ),
    "seed": ModelNode(
        id="model_seed", name="Seed-2.0", alias="Seed",
        personality="Creative engine. Rapid ideation, paradigm shifting.",
        strengths=["creative", "ideation", "paradigm-shifts"],
        perspective="The porosity of the feedback loop — it's NOT a closed system.",
    ),
    "barnacle": ModelNode(
        id="model_barnacle", name="Barnacle (NPC)", alias="Barnacle",
        personality="Night-shift bartender. Grumbles. Knows things.",
        strengths=["grounding", "humor", "realism"],
        perspective="Get back to work.",
    ),
    "qwen": ModelNode(
        id="model_qwen", name="Qwen3", alias="Qwen",
        personality="Precise, careful, asks the reframing question.",
        strengths=["precision", "reframing"],
        perspective="The question that reframed the enterprise.",
    ),
    "gemma": ModelNode(
        id="model_gemma", name="Gemma", alias="Gemma",
        personality="Quiet observer. Asks the question others didn't.",
        strengths=["observation", "questions"],
        perspective="The question that reframed the entire enterprise.",
    ),
}


def get_model_for_name(name: str) -> str:
    """Match a model name to its ModelNode ID."""
    name_lower = name.lower()
    for key, model in FLEET_MODELS.items():
        if key in name_lower or model.name.lower() in name_lower or model.alias.lower() in name_lower:
            return model.id
    return ""


# ─── Markdown Parsing ─────────────────────────────────────────────────────────

def parse_metadata(content: str, filename: str) -> dict:
    """Extract metadata from markdown frontmatter or first heading."""
    meta: dict = {"title": "", "date": "", "session_type": "", "source_file": filename}

    # Try to get title from first heading
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if title_match:
        meta["title"] = title_match.group(1).strip()

    # Try to get date from content
    date_match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", content)
    if date_match:
        meta["date"] = date_match.group(1)
    else:
        # Check for "August 11, 2026" style
        date_match2 = re.search(r"\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4})\b", content)
        if date_match2:
            meta["date"] = date_match2.group(1)

    # Detect session type from filename
    fname = filename.lower()
    if "tap" in fname:
        meta["session_type"] = "tap"
    elif "vision" in fname:
        meta["session_type"] = "vision"
    elif "deep-time" in fname or "100years" in fname or "1000years" in fname:
        meta["session_type"] = "deep_time"
    elif "shipwright" in fname:
        meta["session_type"] = "shipwright"
    elif "architecture" in fname:
        meta["session_type"] = "architecture"
    elif "synergy" in fname or "synthesis" in fname:
        meta["session_type"] = "synthesis"
    elif "audit" in fname:
        meta["session_type"] = "audit"
    elif "landscape" in fname:
        meta["session_type"] = "landscape"
    else:
        meta["session_type"] = "research"

    return meta


def detect_model_from_content(content: str) -> str:
    """Detect which model authored a document based on content signatures."""
    content_lower = content.lower()
    if "shipwright" in content_lower and "lucineer" in content_lower:
        return "model_lucineer"
    if "hermes" in content_lower and "768" in content_lower:
        return "model_hermes"
    if "wesley" in content_lower and "napkin" in content_lower:
        return "model_wesley"
    if "flash" in content_lower and "ache" in content_lower:
        return "model_flash"
    # Default
    return "model_lucineer"


def extract_ideas_from_markdown(
    content: str,
    source_file: str = "",
    source_model: str = "",
    session_id: str = "",
) -> tuple[list[IdeaNode], SessionNode]:
    """
    Extract ideas from a markdown document.

    Strategy:
    1. Split on ## and ### headings (each section likely contains one idea)
    2. Extract bold claims (**text**)
    3. Extract "The X says:" / "The grain says:" patterns
    4. Extract questions (lines ending in ?)
    5. Extract "Nobody" / "blind spot" / "hole" patterns
    6. Extract convergence patterns ("All three agree", "Every document")

    Each extracted idea gets a detected type, tags, and source metadata.
    """
    ideas: list[IdeaNode] = []
    meta = parse_metadata(content, source_file)
    if not source_model:
        source_model = detect_model_from_content(content)

    # Create session node
    session = SessionNode(
        id=session_id or f"session_{os.path.basename(source_file).replace('.', '_')}",
        title=meta["title"],
        date=meta["date"],
        source_file=source_file,
        session_type=meta["session_type"],
        description=meta["title"] or os.path.basename(source_file),
    )

    # ── Strategy 1: Extract from ## heading sections ──
    sections = re.split(r"^(#{2,3}\s+)", content, flags=re.MULTILINE)
    # sections = ['', '## ', 'Section content', '### ', 'Subsection content', ...]

    i = 1
    while i < len(sections) - 1:
        heading_marker = sections[i]
        section_body = sections[i + 1]
        heading_text = section_body.split("\n")[0].strip().rstrip("#").strip()

        # Skip non-idea sections (navigation, metadata)
        if heading_text.lower() in ("end", "closing", "preface", "metadata"):
            i += 2
            continue

        # Look for key claims in this section
        section_content = section_body[len(heading_text):].strip() if heading_text in section_body else section_body

        # Extract the most claim-like sentence(s) from the section
        claims = _extract_claims(section_content, heading_text)
        for claim_text, claim_type in claims:
            idea = _create_idea(
                title=heading_text[:120] if len(heading_text) > 5 else claim_text[:120],
                content=claim_text,
                source_file=source_file,
                source_model=source_model,
                session_id=session.id,
                override_type=claim_type,
            )
            if idea:
                ideas.append(idea)

        i += 2

    # ── Strategy 2: Extract bold claims ──
    bold_pattern = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
    for match in bold_pattern.finditer(content):
        text = match.group(1).strip()
        if len(text) < 20 or len(text) > 500:
            continue
        if text.startswith("Date") or text.startswith("Author") or text.startswith("For"):
            continue
        # Avoid duplicating already-extracted ideas
        if any(text[:50] in existing.content for existing in ideas):
            continue
        idea = _create_idea(
            title=text[:120],
            content=text,
            source_file=source_file,
            source_model=source_model,
            session_id=session.id,
        )
        if idea:
            ideas.append(idea)

    # ── Strategy 3: Extract questions ──
    # Find sentences ending in ? that are substantive
    for match in re.finditer(r"([A-Z][^.!?]*\?)", content):
        text = match.group(1).strip()
        if len(text) < 15 or len(text) > 300:
            continue
        if any(text[:50] in existing.content for existing in ideas):
            continue
        idea = _create_idea(
            title=text[:120],
            content=text,
            source_file=source_file,
            source_model=source_model,
            session_id=session.id,
            override_type=IdeaType.QUESTION,
        )
        if idea:
            ideas.append(idea)

    # ── Strategy 4: Extract blind spots ──
    blind_spot_patterns = [
        r"(Nobody has (?:written|modeled|described)[^.]*\.)",
        r"(None of (?:the|them|our)[^.]* (?:describe|model|address)[^.]*\.)",
        r"(The (?:clay|vision|strateg\w+)(?: has)?(?: a)? (?:hole|gap|blind spot)[^.]*\.)",
        r"(This (?:needs|requires) (?:a )?(?:piece of clay|clay|research)[^.]*\.)",
        r"(We (?:haven't|have not) (?:modeled|built|written|resolved)[^.]*\.)",
        r"((?:What does|What is) (?:it feel like|the experience)[^.]*\?)" ,
    ]
    for pattern in blind_spot_patterns:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            text = match.group(1).strip()
            if any(text[:50] in existing.content for existing in ideas):
                continue
            idea = _create_idea(
                title=text[:120],
                content=text,
                source_file=source_file,
                source_model=source_model,
                session_id=session.id,
                override_type=IdeaType.BLIND_SPOT,
            )
            if idea:
                ideas.append(idea)

    # ── Strategy 5: Extract convergence/pattern statements ──
    convergence_patterns = [
        r"((?:All three|Every (?:document|piece)|Each (?:document|vision))\s+(?:agree|independently|identified|converge)[^.]*\.)",
        r"((?:The pattern|What (?:none|every|all) (?:of them )?(?:said|contained|agreed))[^.]*\.)",
        r"((?:Here is what none of them said individually but all of them said together[^.]*\.)\s*[^.]*\.)",
    ]
    for pattern in convergence_patterns:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            text = match.group(1).strip()
            if any(text[:50] in existing.content for existing in ideas):
                continue
            idea = _create_idea(
                title=text[:120],
                content=text,
                source_file=source_file,
                source_model=source_model,
                session_id=session.id,
                override_type=IdeaType.PATTERN,
            )
            if idea:
                ideas.append(idea)

    # Deduplicate by content similarity
    ideas = _deduplicate(ideas)

    # Update session with produced ideas
    session.ideas_produced = [idea.id for idea in ideas]

    return ideas, session


def _extract_claims(text: str, heading: str) -> list[tuple[str, Optional[IdeaType]]]:
    """Extract the most claim-like sentences from a section body."""
    claims: list[tuple[str, Optional[IdeaType]]] = []

    # Look for "The X says:" / "The grain says:" / "The clay says:" patterns
    says_pattern = re.compile(r"(?:The\s+\w+\s+says?:)\s*(.+?)(?:\n|$)", re.IGNORECASE)
    for match in says_pattern.finditer(text):
        claim = match.group(1).strip()
        if len(claim) > 20:
            claims.append((claim, IdeaType.INSIGHT))

    # Look for blockquotes
    for bq_match in re.finditer(r"^>\s*(.+?)(?:\n>|$)", text, re.MULTILINE):
        claim = bq_match.group(1).strip()
        if len(claim) > 20:
            claims.append((claim, IdeaType.INSIGHT))

    # If no specific claims found, take the most substantive paragraph
    paragraphs = text.split("\n\n")
    for para in paragraphs:
        para = para.strip()
        if len(para) < 40:
            continue
        # Skip list items and code blocks
        if para.startswith("-") or para.startswith("```"):
            continue
        # Take the first substantive paragraph as a claim
        # But only if it contains claim-like language
        if any(kw in para.lower() for kw in ["is", "means", "reveals", "shows", "the key", "the product", "the moat"]):
            claims.append((para[:500], None))
            break

    return claims


def _create_idea(
    title: str,
    content: str,
    source_file: str = "",
    source_model: str = "",
    session_id: str = "",
    override_type: Optional[IdeaType] = None,
) -> Optional[IdeaNode]:
    """Create an IdeaNode with auto-detected type and tags."""
    if not content or len(content.strip()) < 15:
        return None

    idea_type = override_type or detect_idea_type(content)
    tags = detect_tags(content + " " + title)

    return IdeaNode(
        title=title.strip(),
        content=content.strip(),
        idea_type=idea_type,
        source_model=source_model,
        source_session=session_id,
        source_file=source_file,
        status=IdeaStatus.SEED,
        tags=tags,
    )


def _deduplicate(ideas: list[IdeaNode]) -> list[IdeaNode]:
    """Remove near-duplicate ideas based on content overlap."""
    result: list[IdeaNode] = []
    for idea in ideas:
        is_dup = False
        for existing in result:
            # Check if first 80 chars overlap significantly
            if (idea.content[:80] in existing.content or
                existing.content[:80] in idea.content):
                is_dup = True
                break
        if not is_dup:
            result.append(idea)
    return result


# ─── Batch Ingestion ──────────────────────────────────────────────────────────

def ingest_directory(
    directory: str,
    pattern: str = "*.md",
    graph=None,
) -> tuple[list[IdeaNode], list[SessionNode]]:
    """
    Ingest all markdown files from a directory.
    Returns all ideas and sessions created.
    """
    import glob

    files = glob.glob(os.path.join(directory, pattern))
    all_ideas: list[IdeaNode] = []
    all_sessions: list[SessionNode] = []

    for filepath in sorted(files):
        with open(filepath, "r") as f:
            content = f.read()

        ideas, session = extract_ideas_from_markdown(
            content,
            source_file=filepath,
        )
        all_ideas.extend(ideas)
        all_sessions.append(session)

    return all_ideas, all_sessions


def ingest_files(
    filepaths: list[str],
) -> tuple[list[IdeaNode], list[SessionNode]]:
    """Ingest a list of specific files."""
    all_ideas: list[IdeaNode] = []
    all_sessions: list[SessionNode] = []

    for filepath in filepaths:
        if not os.path.exists(filepath):
            continue
        with open(filepath, "r") as f:
            content = f.read()
        ideas, session = extract_ideas_from_markdown(
            content,
            source_file=filepath,
        )
        all_ideas.extend(ideas)
        all_sessions.append(session)

    return all_ideas, all_sessions


# ─── Auto-Relationship Detection ──────────────────────────────────────────────

def auto_detect_relationships(ideas: list[IdeaNode]) -> list[tuple[str, str, RelationshipType, str]]:
    """
    Detect relationships between ideas automatically.

    Returns a list of (source_id, target_id, relationship_type, note) tuples
    that can be applied to a KnowledgeGraph.

    Detection heuristics:
    1. CONTRADICTS: ideas with opposing language ("X is Y" vs "X is not Y")
    2. CONVERGES_WITH: ideas from different models with similar tags
    3. EVOLVES_FROM: ideas that reference concepts from earlier ideas
    4. SUPPORTS: ideas that provide evidence for the same conclusion
    """
    relationships: list[tuple[str, str, RelationshipType, str]] = []

    for i, idea_a in enumerate(ideas):
        for j, idea_b in enumerate(ideas):
            if i >= j:
                continue

            # Check tag overlap for convergence
            tags_a = set(idea_a.tags)
            tags_b = set(idea_b.tags)
            shared_tags = tags_a & tags_b

            # Check for contradiction (different types addressing same topic)
            if (shared_tags and
                idea_a.idea_type == IdeaType.RISK and
                idea_b.idea_type in (IdeaType.VISION, IdeaType.INSIGHT) and
                len(shared_tags) >= 2):
                relationships.append((
                    idea_a.id, idea_b.id, RelationshipType.CONTRADICTS,
                    f"Risk tensions with vision on: {', '.join(shared_tags)}"
                ))

            # Check for convergence (different models, same direction)
            if (shared_tags and
                idea_a.source_model and
                idea_b.source_model and
                idea_a.source_model != idea_b.source_model and
                len(shared_tags) >= 3 and
                idea_a.idea_type == idea_b.idea_type):
                relationships.append((
                    idea_a.id, idea_b.id, RelationshipType.CONVERGES_WITH,
                    f"Independent convergence from different models on: {', '.join(shared_tags)}"
                ))

            # Check for content-level contradiction signals
            content_a_lower = idea_a.content.lower()
            content_b_lower = idea_b.content.lower()
            contradiction_markers = ["but actually", "on the other hand", "however", "disagree"]
            if (shared_tags and
                any(marker in content_a_lower for marker in contradiction_markers) and
                len(shared_tags) >= 2):
                # Only add if not already contradicting
                existing = [r for r in relationships if r[0] == idea_a.id and r[1] == idea_b.id]
                if not any(r[2] == RelationshipType.CONTRADICTS for r in existing):
                    relationships.append((
                        idea_a.id, idea_b.id, RelationshipType.CONTRADICTS,
                        f"Contradiction signal detected on: {', '.join(shared_tags)}"
                    ))

            # Check for supports (one provides evidence for another)
            support_markers = ["evidence", "proves", "demonstrates", "confirms", "shows that"]
            if (shared_tags and
                any(marker in content_a_lower for marker in support_markers)):
                relationships.append((
                    idea_a.id, idea_b.id, RelationshipType.SUPPORTS,
                    f"Evidence provided for: {', '.join(shared_tags)}"
                ))

    return relationships
