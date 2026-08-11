"""
pipeline.py — The end-to-end LucidDreamer.AI flow.

This is the pipe that carries a visitor from arrival to live stream:

    Tap session → Knowledge base ingestion → Ghost compression
                → TTS generation → Streamer playlist → Live stream → Player

Each stage calls the next. If a stage fails, the pipeline logs the error
and continues — one stage failing doesn't kill the whole flow. The music
keeps playing. The visitor is never left in silence.

Usage:
    from integration.pipeline import Pipeline
    pipe = Pipeline()
    await pipe.run_session(session_id, visitor_message)

Or the full automated flow:
    pipe = Pipeline()
    await pipe.run_full_flow(session_log_markdown_path="session.md")
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Path setup for cross-module imports
_repo_root = Path(__file__).resolve().parent.parent
for _p in [
    _repo_root,
    _repo_root / "conductor",
    _repo_root / "knowledge-base",
    _repo_root / "sonic-shape",
    _repo_root / "streamer",
    _repo_root / "pipeline",
]:
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from conductor.conductor import Conductor, RoutingDecision
from conductor.session import SessionState, VisitorProfile, VisitorIntent
from conductor.agent_pool import AgentProfile, get_agent

from integration.agent_client import AgentClient, AgentResponse

logger = logging.getLogger("integration.pipeline")


# ---------------------------------------------------------------------------
# Pipeline stage result
# ---------------------------------------------------------------------------

@dataclass
class StageResult:
    """Result of a single pipeline stage."""
    stage_name: str
    success: bool
    output: dict = field(default_factory=dict)
    error: str = ""
    duration_ms: float = 0.0


@dataclass
class PipelineResult:
    """Result of a full pipeline run."""
    stages: list[StageResult] = field(default_factory=list)
    session_id: str = ""
    overall_success: bool = True

    @property
    def failed_stages(self) -> list[StageResult]:
        return [s for s in self.stages if not s.success]

    def summary(self) -> str:
        lines = [f"Pipeline Result (session {self.session_id}):"]
        for stage in self.stages:
            status = "✅" if stage.success else "❌"
            lines.append(f"  {status} {stage.stage_name} ({stage.duration_ms:.0f}ms)")
            if not stage.success and stage.error:
                lines.append(f"      Error: {stage.error}")
        if self.overall_success:
            lines.append("  Overall: ✅ SUCCESS")
        else:
            lines.append(f"  Overall: ⚠️  {len(self.failed_stages)} stage(s) failed")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# The Pipeline
# ---------------------------------------------------------------------------

class Pipeline:
    """
    The end-to-end LucidDreamer.AI pipeline.

    Connects:
    1. Conductor → routes visitor message, picks agents
    2. AgentClient → calls actual models, gets responses
    3. Knowledge Base → ingests session insights, allows agent queries
    4. Sonic-Shape → converts confidence to music parameters
    5. Streamer → builds playlist, generates HLS stream

    Each step is independent: if sonic-shape fails, the conversation
    still works. If the streamer fails, knowledge is still recorded.
    """

    def __init__(
        self,
        conductor: Optional[Conductor] = None,
        agent_client: Optional[AgentClient] = None,
        knowledge_graph=None,
        live_generator=None,
        streamer_config: Optional[dict] = None,
        auto_execute_mmx: bool = False,  # don't run mmx by default
    ):
        self.conductor = conductor or Conductor()
        self.agent_client = agent_client or AgentClient()
        self.knowledge_graph = knowledge_graph  # KnowledgeGraph or None
        self.live_generator = live_generator    # LiveGenerator or None
        self.streamer_config = streamer_config or {}
        self.auto_execute_mmx = auto_execute_mmx

        # Track active sessions for the pipeline
        self._active_flows: dict[str, PipelineResult] = {}

    # -----------------------------------------------------------------
    # VISITOR INTERACTION (the main loop)
    # -----------------------------------------------------------------

    async def process_visitor_message(
        self,
        session_id: str,
        message: str,
    ) -> PipelineResult:
        """
        Process a single visitor message through the full pipeline.

        This is the primary entry point for real-time interaction.

        Steps:
        1. Conductor routes the message → RoutingDecision
        2. AgentClient calls models for each responding agent → responses
        3. Knowledge base ingests the exchange → ideas extracted
        4. Sonic-shape converts confidence to music → MMX commands
        5. (Optional) Streamer receives new audio → playlist update

        Returns a PipelineResult with details from each stage.
        """
        result = PipelineResult(session_id=session_id)
        start_total = time.monotonic()

        # ── Stage 1: Conductor routing ──────────────────────────────
        stage_start = time.monotonic()
        try:
            decision = self.conductor.route_visitor_message(session_id, message)
            result.stages.append(StageResult(
                stage_name="conductor_routing",
                success=True,
                output={
                    "responding_agents": decision.responding_agents,
                    "intent": decision.intent.value,
                    "confidence": decision.confidence,
                    "escalate": decision.escalate,
                    "reasoning": decision.reasoning,
                },
                duration_ms=(time.monotonic() - stage_start) * 1000,
            ))
        except Exception as e:
            logger.error(f"Conductor routing failed: {e}", exc_info=True)
            result.stages.append(StageResult(
                stage_name="conductor_routing",
                success=False,
                error=str(e),
                duration_ms=(time.monotonic() - stage_start) * 1000,
            ))
            result.overall_success = False
            # If the conductor fails, we can't continue — visitor gets nothing
            return result

        # ── Stage 2: Agent response generation ──────────────────────
        stage_start = time.monotonic()
        responses: list[AgentResponse] = []
        try:
            # Build conversation context from session
            session = self.conductor.sessions.get_session(session_id)
            messages = self._build_context_messages(session) if session else []

            for agent_name in decision.responding_agents:
                agent = get_agent(agent_name)
                if not agent:
                    logger.warning(f"Agent '{agent_name}' not found in pool")
                    continue

                # Add the escalation agent if needed
                if decision.escalate and decision.escalation_agent == agent_name:
                    pass  # already in the responding list

                # Build messages for this specific agent
                agent_messages = messages + [{"role": "user", "content": message}]

                response = self.agent_client.generate(agent, agent_messages)
                responses.append(response)

                # Record the response in the session
                if session and response.success:
                    self.conductor.route_agent_response(
                        session_id, agent_name, response.content
                    )

            result.stages.append(StageResult(
                stage_name="agent_generation",
                success=all(r.success for r in responses) if responses else False,
                output={
                    "responses": [r.to_dict() for r in responses],
                    "response_count": len(responses),
                },
                duration_ms=(time.monotonic() - stage_start) * 1000,
            ))
        except Exception as e:
            logger.error(f"Agent generation failed: {e}", exc_info=True)
            result.stages.append(StageResult(
                stage_name="agent_generation",
                success=False,
                error=str(e),
                duration_ms=(time.monotonic() - stage_start) * 1000,
            ))
            result.overall_success = False

        # ── Stage 3: Knowledge base ingestion ──────────────────────
        stage_start = time.monotonic()
        try:
            kb_result = self._ingest_into_knowledge_base(
                session_id, message, responses, decision
            )
            result.stages.append(StageResult(
                stage_name="knowledge_ingestion",
                success=True,
                output=kb_result,
                duration_ms=(time.monotonic() - stage_start) * 1000,
            ))
        except Exception as e:
            logger.warning(f"Knowledge ingestion failed (non-fatal): {e}")
            result.stages.append(StageResult(
                stage_name="knowledge_ingestion",
                success=False,
                error=str(e),
                duration_ms=(time.monotonic() - stage_start) * 1000,
            ))
            # Non-fatal — don't set overall_success to False

        # ── Stage 4: Sonic-shape music generation ───────────────────
        stage_start = time.monotonic()
        try:
            music_result = self._feed_sonic_shape(decision, responses)
            result.stages.append(StageResult(
                stage_name="sonic_shape",
                success=True,
                output=music_result,
                duration_ms=(time.monotonic() - stage_start) * 1000,
            ))
        except Exception as e:
            logger.warning(f"Sonic-shape failed (non-fatal): {e}")
            result.stages.append(StageResult(
                stage_name="sonic_shape",
                success=False,
                error=str(e),
                duration_ms=(time.monotonic() - stage_start) * 1000,
            ))

        # ── Stage 5: Streamer update ────────────────────────────────
        stage_start = time.monotonic()
        try:
            stream_result = self._update_streamer(decision, responses)
            result.stages.append(StageResult(
                stage_name="streamer_update",
                success=True,
                output=stream_result,
                duration_ms=(time.monotonic() - stage_start) * 1000,
            ))
        except Exception as e:
            logger.warning(f"Streamer update failed (non-fatal): {e}")
            result.stages.append(StageResult(
                stage_name="streamer_update",
                success=False,
                error=str(e),
                duration_ms=(time.monotonic() - stage_start) * 1000,
            ))

        total_ms = (time.monotonic() - start_total) * 1000
        logger.info(
            f"Pipeline processed message for session {session_id} in {total_ms:.0f}ms "
            f"({len(result.stages)} stages, {len(result.failed_stages)} failed)"
        )

        return result

    # -----------------------------------------------------------------
    # FULL FLOW — session log → knowledge → audio → stream
    # -----------------------------------------------------------------

    async def run_full_flow(
        self,
        session_log_path: Optional[str] = None,
        session_content: Optional[str] = None,
        session_id: str = "",
    ) -> PipelineResult:
        """
        Run the complete offline pipeline:
        1. Parse a session log
        2. Extract ideas into the knowledge base
        3. Generate music from confidence patterns
        4. Queue audio for the streamer

        This is for batch processing of recorded sessions, not live interaction.
        """
        result = PipelineResult(session_id=session_id or "batch_flow")

        # ── Load session content ────────────────────────────────────
        if session_log_path:
            with open(session_log_path) as f:
                session_content = f.read()
        if not session_content:
            result.overall_success = False
            result.stages.append(StageResult(
                stage_name="load_session",
                success=False,
                error="No session content provided",
            ))
            return result

        # ── Stage 1: Knowledge base ingestion ───────────────────────
        stage_start = time.monotonic()
        try:
            from knowledge_base.ingest_session import extract_ideas_from_markdown
            ideas, session_node = extract_ideas_from_markdown(
                session_content,
                source_file=session_log_path or "inline",
                session_id=session_id,
            )

            if self.knowledge_graph:
                self.knowledge_graph.add_ideas(ideas)

            result.stages.append(StageResult(
                stage_name="kb_ingestion",
                success=True,
                output={
                    "ideas_extracted": len(ideas),
                    "session_title": session_node.title,
                    "session_type": session_node.session_type,
                },
                duration_ms=(time.monotonic() - stage_start) * 1000,
            ))
        except Exception as e:
            result.stages.append(StageResult(
                stage_name="kb_ingestion",
                success=False,
                error=str(e),
                duration_ms=(time.monotonic() - stage_start) * 1000,
            ))
            result.overall_success = False

        # ── Stage 2: Ghost compression / summarization ──────────────
        stage_start = time.monotonic()
        try:
            ghost = self._compress_to_ghost(session_content)
            result.stages.append(StageResult(
                stage_name="ghost_compression",
                success=True,
                output={"ghost_length": len(ghost), "preview": ghost[:200]},
                duration_ms=(time.monotonic() - stage_start) * 1000,
            ))
        except Exception as e:
            result.stages.append(StageResult(
                stage_name="ghost_compression",
                success=False,
                error=str(e),
                duration_ms=(time.monotonic() - stage_start) * 1000,
            ))

        # ── Stage 3: TTS / audio generation ─────────────────────────
        stage_start = time.monotonic()
        try:
            audio_result = await self._generate_audio(ghost, session_id)
            result.stages.append(StageResult(
                stage_name="tts_generation",
                success=True,
                output=audio_result,
                duration_ms=(time.monotonic() - stage_start) * 1000,
            ))
        except Exception as e:
            result.stages.append(StageResult(
                stage_name="tts_generation",
                success=False,
                error=str(e),
                duration_ms=(time.monotonic() - stage_start) * 1000,
            ))

        # ── Stage 4: Sonic-shape from session ───────────────────────
        stage_start = time.monotonic()
        try:
            music_result = self._generate_session_music(session_content)
            result.stages.append(StageResult(
                stage_name="sonic_shape_music",
                success=True,
                output=music_result,
                duration_ms=(time.monotonic() - stage_start) * 1000,
            ))
        except Exception as e:
            result.stages.append(StageResult(
                stage_name="sonic_shape_music",
                success=False,
                error=str(e),
                duration_ms=(time.monotonic() - stage_start) * 1000,
            ))

        # ── Stage 5: Streamer playlist update ───────────────────────
        stage_start = time.monotonic()
        try:
            playlist_result = self._build_streamer_entry(music_result if 'music_result' in dir() else {})
            result.stages.append(StageResult(
                stage_name="streamer_playlist",
                success=True,
                output=playlist_result,
                duration_ms=(time.monotonic() - stage_start) * 1000,
            ))
        except Exception as e:
            result.stages.append(StageResult(
                stage_name="streamer_playlist",
                success=False,
                error=str(e),
                duration_ms=(time.monotonic() - stage_start) * 1000,
            ))

        return result

    # -----------------------------------------------------------------
    # INTERNAL HELPERS
    # -----------------------------------------------------------------

    def _build_context_messages(self, session: SessionState) -> list[dict[str, str]]:
        """Build OpenAI-format message context from session history."""
        messages = []
        # Include up to last 10 messages for context
        for msg in session.messages[-10:]:
            if msg.role == "visitor":
                messages.append({"role": "user", "content": msg.content})
            elif msg.role == "agent":
                messages.append({"role": "assistant", "content": msg.content})
            elif msg.role == "system":
                messages.append({"role": "system", "content": msg.content})
        return messages

    def _ingest_into_knowledge_base(
        self,
        session_id: str,
        visitor_message: str,
        responses: list[AgentResponse],
        decision: RoutingDecision,
    ) -> dict:
        """Ingest the current exchange into the knowledge base."""
        if not self.knowledge_graph:
            return {"skipped": "no knowledge graph configured"}

        # knowledge-base uses a hyphenated dir; import from the path-adjusted location
        try:
            from idea_schema import (
                IdeaNode, IdeaStatus, IdeaType,
            )
        except ImportError:
            return {"skipped": "idea_schema module not available"}

        ideas_added = 0

        # Extract the visitor's message as a potential idea
        if len(visitor_message) > 30:
            visitor_idea = IdeaNode(
                title=visitor_message[:120],
                content=visitor_message,
                idea_type=IdeaType.QUESTION if "?" in visitor_message else IdeaType.INSIGHT,
                source_model="visitor",
                source_session=session_id,
                status=IdeaStatus.SEED,
                tags=[decision.intent.value] if decision.intent != VisitorIntent.UNKNOWN else [],
            )
            self.knowledge_graph.add_idea(visitor_idea)
            ideas_added += 1

        # Extract key insights from agent responses
        for response in responses:
            if not response.success or len(response.content) < 30:
                continue

            # Simple extraction: treat each paragraph as a potential idea
            paragraphs = [p.strip() for p in response.content.split("\n\n") if len(p.strip()) > 40]
            for para in paragraphs[:3]:  # max 3 per agent
                idea = IdeaNode(
                    title=para[:120],
                    content=para,
                    idea_type=IdeaType.INSIGHT,
                    source_model=response.model,
                    source_session=session_id,
                    status=IdeaStatus.SEED,
                    tags=[response.agent_name, decision.intent.value] if decision.intent != VisitorIntent.UNKNOWN else [response.agent_name],
                )
                self.knowledge_graph.add_idea(idea)
                ideas_added += 1

        return {
            "ideas_added": ideas_added,
            "total_in_graph": len(self.knowledge_graph.nodes),
        }

    def _feed_sonic_shape(
        self,
        decision: RoutingDecision,
        responses: list[AgentResponse],
    ) -> dict:
        """Feed the session's confidence into the sonic-shape live generator."""
        if not self.live_generator:
            return {
                "skipped": "no live generator configured",
                "confidence": decision.confidence,
            }

        # Feed the confidence reading
        model_name = responses[0].model if responses else "unknown"
        self.live_generator.feed_confidence(
            confidence=decision.confidence,
            model_name=model_name,
        )

        # Check the queue
        queue = self.live_generator.peek_queue()

        return {
            "confidence": decision.confidence,
            "band": self.live_generator.current_band.value if self.live_generator.current_band else None,
            "queue_length": len(queue),
            "queue_status": self.live_generator.queue_status(),
            "next_piece": str(queue[0]) if queue else None,
        }

    def _update_streamer(
        self,
        decision: RoutingDecision,
        responses: list[AgentResponse],
    ) -> dict:
        """Update the streamer playlist based on pipeline activity."""
        # For now, just report what would happen
        # In full deployment, this would push audio files to the streamer's audio dir
        return {
            "status": "notified",
            "confidence": decision.confidence,
            "would_adapt_music": decision.confidence < 0.4 or decision.confidence > 0.7,
            "note": "Streamer receives music from sonic-shape via MMX output directory",
        }

    def _compress_to_ghost(self, content: str) -> str:
        """
        Compress a full session into a ghost — a tight, punchy summary
        suitable for TTS narration. Keeps the best lines, drops the rest.
        """
        lines = content.split("\n")
        ghost_lines: list[str] = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Keep headings, bold claims, and substantial paragraphs
            if line.startswith("#"):
                ghost_lines.append(line.lstrip("#").strip())
            elif line.startswith("**") and line.endswith("**"):
                ghost_lines.append(line.strip("*").strip())
            elif len(line) > 80 and not line.startswith("|") and not line.startswith("-"):
                ghost_lines.append(line[:500])

        # Cap at ~3000 chars for TTS (roughly 4-5 minutes of speech)
        ghost = "\n\n".join(ghost_lines[:40])
        if len(ghost) > 3000:
            ghost = ghost[:3000] + "..."
        return ghost

    async def _generate_audio(self, ghost: str, session_id: str) -> dict:
        """Generate TTS audio from the ghost text."""
        # Check if we have TTS capabilities
        try:
            # Try pipeline's content_to_audio module
            from content_to_audio import text_to_speech_ollama
            output_path = f"/tmp/luciddreamer_tts_{session_id}.mp3"
            text_to_speech_ollama(ghost, output_path)
            return {
                "audio_path": output_path,
                "duration_estimate": len(ghost) / 15,  # ~15 chars/sec for TTS
            }
        except ImportError:
            return {
                "skipped": "content_to_audio module not available",
                "ghost_length": len(ghost),
            }
        except Exception as e:
            return {
                "error": str(e),
                "ghost_length": len(ghost),
            }

    def _generate_session_music(self, session_content: str) -> dict:
        """Generate music parameters from a session log using sonic-shape."""
        try:
            from session_to_music import session_to_score
            score = session_to_score(session_content)
            return {
                "movements": len(score.movements),
                "emotional_arc": [m.emotion.value for m in score.movements],
                "tempo_range": (
                    min(m.params.tempo_bpm for m in score.movements) if score.movements else 0,
                    max(m.params.tempo_bpm for m in score.movements) if score.movements else 0,
                ),
            }
        except ImportError:
            return {"skipped": "session_to_music module not available"}
        except Exception as e:
            return {"error": str(e)}

    def _build_streamer_entry(self, music_result: dict) -> dict:
        """Build a streamer playlist entry from music generation results."""
        if not music_result:
            return {"status": "no music data"}

        return {
            "entry_type": "session_music",
            "movements": music_result.get("movements", 0),
            "status": "queued for streamer",
        }
