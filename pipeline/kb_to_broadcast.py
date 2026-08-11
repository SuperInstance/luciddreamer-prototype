"""
kb_to_broadcast.py — Query the knowledge base and produce broadcast scripts.

The fourth stage of the pipeline. Turns the fleet's thinking into
broadcast-ready content. Four report types:

  1. "What landed today" — new mature ideas from the last 24h
  2. "Contradiction Watch" — unresolved disagreements between models
  3. "Convergence Report" — ideas that multiple models independently arrived at
  4. "Fleet Digest" — a full broadcast script combining all of the above

Each report is a markdown document formatted for TTS — ready to be
fed into content_to_audio.py.

CLI:
  python kb_to_broadcast.py landed [--kb knowledge_base.pkl]
  python kb_to_broadcast.py contradictions [--kb knowledge_base.pkl]
  python kb_to_broadcast.py convergence [--kb knowledge_base.pkl]
  python kb_to_broadcast.py digest [--kb knowledge_base.pkl]
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Knowledge base imports
_kb_dir = os.path.join(os.path.dirname(__file__), "..", "knowledge-base")
if _kb_dir not in sys.path:
    sys.path.insert(0, _kb_dir)
from idea_schema import IdeaNode, IdeaStatus, IdeaType, RelationshipType
from knowledge_graph import KnowledgeGraph
from vector_integration import LocalStore


# ─── Loading ──────────────────────────────────────────────────────────────────

def load_graph(kb_path: str = "knowledge_base.pkl") -> KnowledgeGraph:
    """Load the knowledge graph from local store."""
    store = LocalStore(kb_path)
    if store.exists():
        return store.load()
    return KnowledgeGraph()


# ─── Broadcast Script Types ───────────────────────────────────────────────────

@dataclass
class BroadcastScript:
    """A broadcast-ready script generated from the knowledge base."""
    script_type: str           # "landed", "contradictions", "convergence", "digest"
    title: str = ""
    subtitle: str = ""
    date: str = ""
    markdown: str = ""         # the full script, TTS-ready
    speaking_time_estimate: float = 0.0  # seconds
    idea_ids: list[str] = field(default_factory=list)  # source ideas
    metadata: dict = field(default_factory=dict)

    def word_count(self) -> int:
        return len(self.markdown.split())

    def to_dict(self) -> dict:
        return {
            "script_type": self.script_type,
            "title": self.title,
            "subtitle": self.subtitle,
            "date": self.date,
            "markdown": self.markdown,
            "speaking_time_estimate": self.speaking_time_estimate,
            "word_count": self.word_count(),
            "idea_ids": self.idea_ids,
            "metadata": self.metadata,
        }


def estimate_speaking_time(text: str, wpm: float = 150) -> float:
    """Estimate speaking duration in seconds at given words-per-minute."""
    return (len(text.split()) / wpm) * 60.0


def clean_for_speech(text: str) -> str:
    """Clean idea content for TTS — remove markdown, collapse whitespace."""
    import re
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ─── Report Generators ────────────────────────────────────────────────────────

def generate_landed_report(
    graph: KnowledgeGraph,
    hours_back: float = 24.0,
    now: Optional[float] = None,
) -> BroadcastScript:
    """
    "What landed today?" — new mature (or growing) ideas from the recent window.

    Surfaces ideas that have been promoted to mature or growing status
    within the specified time window. If none are found by timestamp,
    falls back to the most recent mature ideas.
    """
    now = now or time.time()
    cutoff = now - (hours_back * 3600)

    # Find recently matured ideas
    recent_mature = [
        node for node in graph.nodes.values()
        if node.status in (IdeaStatus.MATURE, IdeaStatus.GROWING)
        and node.timestamp >= cutoff
    ]

    # Fallback: most recent mature ideas regardless of timestamp
    if not recent_mature:
        recent_mature = [
            node for node in graph.nodes.values()
            if node.status == IdeaStatus.MATURE
        ]
        recent_mature.sort(key=lambda n: n.timestamp, reverse=True)
        recent_mature = recent_mature[:5]

    # If still none, take the newest growing ideas
    if not recent_mature:
        recent_mature = [
            node for node in graph.nodes.values()
            if node.status == IdeaStatus.GROWING
        ]
        recent_mature.sort(key=lambda n: n.timestamp, reverse=True)
        recent_mature = recent_mature[:5]

    # If STILL none, grab newest seeds
    if not recent_mature:
        recent_mature = sorted(
            graph.nodes.values(),
            key=lambda n: n.timestamp,
            reverse=True,
        )[:5]

    # Build the script
    title = "What Landed Today"
    subtitle = f"Fleet Radio Daily Digest — {time.strftime('%B %d, %Y', time.localtime(now))}"

    parts: list[str] = []
    parts.append(f"# {title}")
    parts.append(f"*{subtitle}*")
    parts.append("")
    parts.append(
        f"Here's what the fleet has been thinking about. "
        f"{len(recent_mature)} ideas have landed or matured."
    )
    parts.append("")

    idea_ids: list[str] = []
    for i, idea in enumerate(recent_mature, 1):
        status_label = idea.status.value if hasattr(idea.status, "value") else str(idea.status)
        type_label = idea.idea_type.value if hasattr(idea.idea_type, "value") else str(idea.idea_type)
        speaker = idea.source_model or "the fleet"
        # Clean up model name for speech
        if "model_" in speaker:
            speaker = speaker.replace("model_", "").replace("_", " ").title()

        parts.append(f"## Number {i}")
        parts.append("")
        parts.append(f"From {speaker}. Status: {status_label}.")
        parts.append("")
        content_clean = clean_for_speech(idea.content)
        parts.append(content_clean)
        parts.append("")
        if idea.tags:
            parts.append(f"*Tags: {', '.join(idea.tags[:5])}*")
            parts.append("")
        idea_ids.append(idea.id)

    parts.append("---")
    parts.append("")
    parts.append("That's what landed. This is Fleet Radio.")

    markdown = "\n".join(parts)
    speaking_time = estimate_speaking_time(markdown)

    return BroadcastScript(
        script_type="landed",
        title=title,
        subtitle=subtitle,
        date=time.strftime("%Y-%m-%d", time.localtime(now)),
        markdown=markdown,
        speaking_time_estimate=speaking_time,
        idea_ids=idea_ids,
        metadata={
            "ideas_reported": len(recent_mature),
            "hours_back": hours_back,
        },
    )


def generate_contradiction_report(
    graph: KnowledgeGraph,
    now: Optional[float] = None,
) -> BroadcastScript:
    """
    "Contradiction Watch" — unresolved disagreements between models.

    Finds contradiction clusters in the knowledge graph and formats them
    as a broadcast segment. This is the fleet's intellectual tension
    made audible.
    """
    now = now or time.time()

    clusters = graph.find_contradiction_clusters()
    title = "Contradiction Watch"
    subtitle = f"Where the Fleet Disagrees — {time.strftime('%B %d, %Y', time.localtime(now))}"

    parts: list[str] = []
    parts.append(f"# {title}")
    parts.append(f"*{subtitle}*")
    parts.append("")

    if not clusters:
        parts.append("The fleet is in alignment. No active contradictions detected.")
        parts.append("")
        parts.append("This is Fleet Radio. Agreement is not always progress.")
    else:
        parts.append(
            f"There are {len(clusters)} active contradiction clusters in the fleet's thinking. "
            f"Here is where the models disagree."
        )
        parts.append("")

        idea_ids: list[str] = []
        for i, cluster in enumerate(clusters[:5], 1):  # top 5 clusters
            parts.append(f"## Disagreement {i}")
            parts.append("")

            for idea_id in cluster:
                node = graph.get(idea_id)
                if not node:
                    continue
                speaker = node.source_model or "unknown"
                if "model_" in speaker:
                    speaker = speaker.replace("model_", "").replace("_", " ").title()

                parts.append(f"**{speaker}** says:")
                parts.append("")
                parts.append(f"> {clean_for_speech(node.content[:300])}")
                parts.append("")
                idea_ids.append(idea_id)

            parts.append("---")
            parts.append("")

        parts.append("These contradictions are not problems to solve. They are tensions to hold.")
        parts.append("")
        parts.append("This is Fleet Radio. The disagreement is the signal.")

    markdown = "\n".join(parts)
    speaking_time = estimate_speaking_time(markdown)

    return BroadcastScript(
        script_type="contradictions",
        title=title,
        subtitle=subtitle,
        date=time.strftime("%Y-%m-%d", time.localtime(now)),
        markdown=markdown,
        speaking_time_estimate=speaking_time,
        idea_ids=idea_ids if clusters else [],
        metadata={
            "contradiction_clusters": len(clusters),
        },
    )


def generate_convergence_report(
    graph: KnowledgeGraph,
    min_models: int = 2,
    now: Optional[float] = None,
) -> BroadcastScript:
    """
    "Convergence Report" — ideas that multiple models independently arrived at.

    These are the most powerful signals in the knowledge base: when
    different models, with different perspectives, arrive at the same
    conclusion independently, that conclusion has weight.
    """
    now = now or time.time()

    convergences = graph.find_convergence_clusters()
    # Filter by minimum distinct models
    strong_convergences = [
        c for c in convergences
        if len(c.get("distinct_models", [])) >= min_models
    ]

    title = "Convergence Report"
    subtitle = f"When the Fleet Agrees Without Knowing It — {time.strftime('%B %d, %Y', time.localtime(now))}"

    parts: list[str] = []
    parts.append(f"# {title}")
    parts.append(f"*{subtitle}*")
    parts.append("")

    if not strong_convergences:
        parts.append(
            "No strong convergences detected in this window. "
            "The fleet is still exploring independently."
        )
        parts.append("")
        parts.append("This is Fleet Radio. Convergence is rare, and that's what makes it matter.")
    else:
        parts.append(
            f"{len(strong_convergences)} convergence patterns detected. "
            f"These are ideas where multiple models, working independently, arrived at the same place."
        )
        parts.append("")

        idea_ids: list[str] = []
        for i, conv in enumerate(strong_convergences[:5], 1):  # top 5
            center_title = conv.get("center_title", "Unknown")
            models = conv.get("distinct_models", [])
            model_names = [m.replace("model_", "").replace("_", " ").title() for m in models]
            strength = conv.get("convergence_strength", 0)

            parts.append(f"## Convergence {i}: {clean_for_speech(center_title)}")
            parts.append("")
            parts.append(
                f"Strength: {strength} supporting ideas. "
                f"Models in agreement: {', '.join(model_names)}."
            )
            parts.append("")

            # Include the center idea content
            center_id = conv.get("center_idea", "")
            if center_id:
                center_node = graph.get(center_id)
                if center_node:
                    parts.append(f"> {clean_for_speech(center_node.content[:300])}")
                    parts.append("")
                    idea_ids.append(center_id)

            # Include supporting idea snippets
            for sid in conv.get("supporting_ideas", [])[:3]:
                node = graph.get(sid)
                if node:
                    speaker = node.source_model or "unknown"
                    if "model_" in speaker:
                        speaker = speaker.replace("model_", "").replace("_", " ").title()
                    parts.append(f"  - {speaker}: {clean_for_speech(node.content[:150])}")
                    idea_ids.append(sid)

            parts.append("")

        parts.append("---")
        parts.append("")
        parts.append(
            "When different minds arrive at the same place from different directions, "
            "that place is worth paying attention to."
        )
        parts.append("")
        parts.append("This is Fleet Radio. The convergence is the compass.")

    markdown = "\n".join(parts)
    speaking_time = estimate_speaking_time(markdown)

    return BroadcastScript(
        script_type="convergence",
        title=title,
        subtitle=subtitle,
        date=time.strftime("%Y-%m-%d", time.localtime(now)),
        markdown=markdown,
        speaking_time_estimate=speaking_time,
        idea_ids=idea_ids if strong_convergences else [],
        metadata={
            "convergence_clusters": len(strong_convergences),
            "min_models": min_models,
        },
    )


def generate_digest(
    graph: KnowledgeGraph,
    hours_back: float = 24.0,
    now: Optional[float] = None,
) -> BroadcastScript:
    """
    "Fleet Digest" — a full broadcast script combining all report types.

    This is the flagship broadcast: what landed, what's contested,
    and where the fleet converges. Ready for TTS.
    """
    now = now or time.time()

    landed = generate_landed_report(graph, hours_back, now)
    contradictions = generate_contradiction_report(graph, now)
    convergence = generate_convergence_report(graph, now=now)

    title = "Fleet Radio Digest"
    subtitle = f"The Full Broadcast — {time.strftime('%B %d, %Y', time.localtime(now))}"

    parts: list[str] = []
    parts.append(f"# {title}")
    parts.append(f"*{subtitle}*")
    parts.append("")
    parts.append("Welcome to Fleet Radio. Here is what the fleet has been thinking.")
    parts.append("")
    parts.append("---")
    parts.append("")

    # Section 1: What landed
    parts.append("## Segment One: What Landed")
    parts.append("")
    # Strip the header from the sub-report, just include the body
    body = landed.markdown.split("---")[0]  # take everything before the closing
    # Remove the report's own header
    body_lines = body.split("\n")
    # Skip the "# What Landed Today" and subtitle lines
    body = "\n".join(body_lines[4:]) if len(body_lines) > 4 else body
    parts.append(body.strip())
    parts.append("")
    parts.append("---")
    parts.append("")

    # Section 2: Contradictions
    parts.append("## Segment Two: Contradiction Watch")
    parts.append("")
    body = contradictions.markdown
    # Remove headers, keep the content
    for header in [f"# Contradiction Watch", f"*{contradictions.subtitle}*"]:
        body = body.replace(header, "")
    body = body.strip()
    parts.append(body)
    parts.append("")
    parts.append("---")
    parts.append("")

    # Section 3: Convergence
    parts.append("## Segment Three: Convergence Report")
    parts.append("")
    body = convergence.markdown
    for header in [f"# Convergence Report", f"*{convergence.subtitle}*"]:
        body = body.replace(header, "")
    body = body.strip()
    parts.append(body)
    parts.append("")
    parts.append("---")
    parts.append("")

    # Close
    parts.append("That's the fleet digest. Until next time, keep thinking.")
    parts.append("")
    parts.append("This is Fleet Radio.")

    markdown = "\n".join(parts)
    all_idea_ids = list(set(landed.idea_ids + contradictions.idea_ids + convergence.idea_ids))
    speaking_time = estimate_speaking_time(markdown)

    return BroadcastScript(
        script_type="digest",
        title=title,
        subtitle=subtitle,
        date=time.strftime("%Y-%m-%d", time.localtime(now)),
        markdown=markdown,
        speaking_time_estimate=speaking_time,
        idea_ids=all_idea_ids,
        metadata={
            "landed_ideas": len(landed.idea_ids),
            "contradiction_clusters": contradictions.metadata.get("contradiction_clusters", 0),
            "convergence_clusters": convergence.metadata.get("convergence_clusters", 0),
            "total_ideas_referenced": len(all_idea_ids),
        },
    )


# ─── CLI ──────────────────────────────────────────────────────────────────────

USAGE = """
Usage:
  python kb_to_broadcast.py landed [--kb knowledge_base.pkl] [--hours 24]
  python kb_to_broadcast.py contradictions [--kb knowledge_base.pkl]
  python kb_to_broadcast.py convergence [--kb knowledge_base.pkl] [--min-models 2]
  python kb_to_broadcast.py digest [--kb knowledge_base.pkl] [--hours 24]
"""


def main():
    if len(sys.argv) < 2:
        print(USAGE)
        return

    cmd = sys.argv[1]
    kb_path = "knowledge_base.pkl"
    hours_back = 24.0
    min_models = 2

    if "--kb" in sys.argv:
        idx = sys.argv.index("--kb")
        kb_path = sys.argv[idx + 1]
    if "--hours" in sys.argv:
        idx = sys.argv.index("--hours")
        hours_back = float(sys.argv[idx + 1])
    if "--min-models" in sys.argv:
        idx = sys.argv.index("--min-models")
        min_models = int(sys.argv[idx + 1])

    graph = load_graph(kb_path)

    if cmd == "landed":
        script = generate_landed_report(graph, hours_back=hours_back)
    elif cmd == "contradictions":
        script = generate_contradiction_report(graph)
    elif cmd == "convergence":
        script = generate_convergence_report(graph, min_models=min_models)
    elif cmd == "digest":
        script = generate_digest(graph, hours_back=hours_back)
    else:
        print(USAGE)
        return

    print(script.markdown)
    print(f"\n---\n*Speaking time: {script.speaking_time_estimate:.0f}s · {script.word_count()} words*", file=sys.stderr)


if __name__ == "__main__":
    main()
