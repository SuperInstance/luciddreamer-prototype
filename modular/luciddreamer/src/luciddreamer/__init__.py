"""
LucidDreamer.AI — Meta-Package Assembly Layer

The one-command install that wires all modules together.
Each module is independently usable. This just connects them.

    pip install superinstance-luciddreamer
    from luciddreamer import LucidDreamer
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("luciddreamer")


@dataclass
class LucidDreamerConfig:
    """Configuration for the full LucidDreamer stack."""
    audio_dir: str = ""
    port: int = 8420

    # Module configs (passed through to each module)
    conductor_config: dict = field(default_factory=dict)
    streamer_config: dict = field(default_factory=dict)
    kb_config: dict = field(default_factory=dict)
    sonic_config: dict = field(default_factory=dict)

    # Feature flags
    enable_conductor: bool = True
    enable_streamer: bool = True
    enable_knowledge_base: bool = True
    enable_sonic_shape: bool = True


class LucidDreamer:
    """
    The full LucidDreamer.AI stack, auto-assembled.

    Usage:
        ld = LucidDreamer(audio_dir="/path/to/audio")
        session = ld.conductor.receive_visitor(visitor)
        decision = ld.conductor.route_visitor_message(session.session_id, "Hello")
    """

    def __init__(
        self,
        audio_dir: str = "",
        port: int = 8420,
        conductor_config: Optional[dict] = None,
        streamer_config: Optional[dict] = None,
        kb_config: Optional[dict] = None,
        sonic_config: Optional[dict] = None,
        enable_conductor: bool = True,
        enable_streamer: bool = True,
        enable_knowledge_base: bool = True,
        enable_sonic_shape: bool = True,
    ):
        self.config = LucidDreamerConfig(
            audio_dir=audio_dir,
            port=port,
            conductor_config=conductor_config or {},
            streamer_config=streamer_config or {},
            kb_config=kb_config or {},
            sonic_config=sonic_config or {},
            enable_conductor=enable_conductor,
            enable_streamer=enable_streamer,
            enable_knowledge_base=enable_knowledge_base,
            enable_sonic_shape=enable_sonic_shape,
        )

        self._conductor = None
        self._streamer = None
        self._knowledge_base = None
        self._sonic_shape = None

        self._assemble()

    def _assemble(self) -> None:
        """Wire all modules together with sensible defaults."""
        logger.info("Assembling LucidDreamer.AI stack...")

        if self.config.enable_conductor:
            self._init_conductor()

        if self.config.enable_knowledge_base:
            self._init_knowledge_base()

        if self.config.enable_sonic_shape:
            self._init_sonic_shape()

        if self.config.enable_streamer:
            self._init_streamer()

        logger.info("LucidDreamer.AI ready.")

    def _init_conductor(self) -> None:
        """Initialize the routing layer."""
        try:
            from conductor import Conductor
            self._conductor = Conductor(
                config=self.config.conductor_config or None,
            )
            logger.info("  ✓ Conductor ready")
        except ImportError:
            logger.warning("  ✗ Conductor not available (pip install superinstance-conductor)")

    def _init_streamer(self) -> None:
        """Initialize the audio streaming muxer."""
        try:
            from streamer import Muxer, MuxerConfig, Playlist, Scheduler
            self._streamer = {
                "muxer": Muxer(),
                "playlist": None,
                "scheduler": None,
            }
            if self.config.audio_dir:
                self._streamer["playlist"] = Playlist(audio_dir=self.config.audio_dir)
                self._streamer["scheduler"] = Scheduler(
                    playlist=self._streamer["playlist"]
                )
            logger.info("  ✓ Streamer ready")
        except ImportError:
            logger.warning("  ✗ Streamer not available (pip install superinstance-streamer)")

    def _init_knowledge_base(self) -> None:
        """Initialize the knowledge base."""
        try:
            from knowledge_base import KnowledgeBase
            local_path = self.config.kb_config.get("local_path", "knowledge_base.pkl")
            self._knowledge_base = KnowledgeBase(local_path=local_path)
            logger.info("  ✓ Knowledge base ready")
        except ImportError:
            logger.warning("  ✗ Knowledge base not available (pip install superinstance-knowledge-base)")

    def _init_sonic_shape(self) -> None:
        """Initialize the sonic shape engine."""
        try:
            from sonic_shape import confidence_to_music, LiveGenerator
            self._sonic_shape = {
                "confidence_to_music": confidence_to_music,
                "generator": LiveGenerator(
                    auto_generate=self.config.sonic_config.get("auto_generate", True),
                ),
            }
            logger.info("  ✓ Sonic shape ready")
        except ImportError:
            logger.warning("  ✗ Sonic shape not available (pip install superinstance-sonic-shape)")

    # ── Module Access ──────────────────────────────────────

    @property
    def conductor(self):
        """The routing layer. Routes visitors to agents."""
        if self._conductor is None:
            raise RuntimeError("Conductor not enabled or not installed")
        return self._conductor

    @property
    def streamer(self):
        """The audio streaming muxer. Dict with muxer, playlist, scheduler."""
        if self._streamer is None:
            raise RuntimeError("Streamer not enabled or not installed")
        return self._streamer

    @property
    def knowledge_base(self):
        """The recursive idea graph."""
        if self._knowledge_base is None:
            raise RuntimeError("Knowledge base not enabled or not installed")
        return self._knowledge_base

    @property
    def sonic_shape(self):
        """The confidence-to-music engine. Dict with confidence_to_music, generator."""
        if self._sonic_shape is None:
            raise RuntimeError("Sonic shape not enabled or not installed")
        return self._sonic_shape

    # ── Integration ────────────────────────────────────────

    def route_and_score(
        self,
        session_id: str,
        message: str,
    ):
        """
        Route a visitor message and generate a musical score from the session.
        This is the LucidDreamer signature flow: conversation becomes music.
        """
        decision = self.conductor.route_visitor_message(session_id, message)

        score = None
        if self._sonic_shape and decision.confidence is not None:
            params = self._sonic_shape["confidence_to_music"](
                decision.confidence,
                emotion=None,
            )
            score = params

        return decision, score

    def ingest_session_to_kb(self, session_id: str) -> None:
        """Ingest a completed session into the knowledge base."""
        if not self._knowledge_base:
            return

        session = self.conductor.sessions.get_session(session_id)
        if not session:
            return

        # Extract ideas from the session messages
        from knowledge_base import IdeaNode, IdeaType, detect_idea_type, detect_tags
        for msg in session.messages:
            if msg.role == "agent" and msg.content:
                idea = IdeaNode(
                    title=msg.content[:80],
                    content=msg.content,
                    idea_type=detect_idea_type(msg.content),
                    source_model=msg.agent_name,
                    source_session=session_id,
                    tags=detect_tags(msg.content),
                )
                self._knowledge_base.add_idea(idea)

        self._knowledge_base.save()

    def status(self) -> dict:
        """Return the status of all modules."""
        return {
            "conductor": "active" if self._conductor else "disabled",
            "streamer": "active" if self._streamer else "disabled",
            "knowledge_base": "active" if self._knowledge_base else "disabled",
            "sonic_shape": "active" if self._sonic_shape else "disabled",
        }
