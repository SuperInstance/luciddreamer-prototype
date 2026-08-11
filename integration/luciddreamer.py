#!/usr/bin/env python3
"""
luciddreamer.py — The orchestrator that wires everything together.

One command starts the entire system:

    python luciddreamer.py serve

This initializes:
  1. The conductor with its agent pool
  2. The agent client with provider fallbacks
  3. The knowledge base graph
  4. The sonic-shape live generator (connected to conductor confidence)
  5. The streamer playlist (fed by sonic-shape)
  6. An HTTP server exposing the visitor API

Endpoints:
  POST /visit           — create a new visitor session
  POST /message         — send a message as a visitor
  GET  /session/<id>    — get session status
  GET  /health          — system health check
  GET  /music           — current music/sonic-shape status
  GET  /knowledge/stats — knowledge graph statistics

The server runs on port 8420 by default (same as the streamer, on a
different path — they can share the port or be configured separately).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import signal
import sys
import threading
import time
from dataclasses import asdict
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from socketserver import ThreadingMixIn
from typing import Optional
from urllib.parse import urlparse, parse_qs

# Set up path for cross-module imports
_repo_root = Path(__file__).resolve().parent.parent
for _p in [
    _repo_root,
    _repo_root / "conductor",
    _repo_root / "knowledge-base",
    _repo_root / "sonic-shape",
    _repo_root / "streamer",
    _repo_root / "pipeline",
    _repo_root / "integration",
]:
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from conductor.conductor import Conductor
from conductor.session import VisitorProfile, SessionStore
from conductor.agent_pool import get_agent, reset_all_sessions

from integration.agent_client import AgentClient
from integration.pipeline import Pipeline

logger = logging.getLogger("luciddreamer")


# ---------------------------------------------------------------------------
# The Orchestrator
# ---------------------------------------------------------------------------

class LucidDreamer:
    """
    The top-level system orchestrator. Wires all modules together and
    manages their lifecycle.

    Attributes:
        conductor:  Routes visitor messages to agents
        client:     Calls actual LLM APIs for agents
        pipeline:   End-to-end flow (conductor → client → KB → music → stream)
        knowledge_graph: Optional knowledge base for idea storage
        live_generator: Optional sonic-shape generator for live music
        running:    Whether the system is currently serving
    """

    def __init__(
        self,
        conductor: Optional[Conductor] = None,
        agent_client: Optional[AgentClient] = None,
        knowledge_graph=None,
        live_generator=None,
        config: Optional[dict] = None,
    ):
        self.config = config or {}
        self.conductor = conductor or Conductor(config=self.config.get("conductor"))
        self.agent_client = agent_client or AgentClient()
        self.knowledge_graph = knowledge_graph
        self.live_generator = live_generator
        self.running = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        # Wire the pipeline
        self.pipeline = Pipeline(
            conductor=self.conductor,
            agent_client=self.agent_client,
            knowledge_graph=self.knowledge_graph,
            live_generator=self.live_generator,
            streamer_config=self.config.get("streamer", {}),
            auto_execute_mmx=self.config.get("auto_execute_mmx", False),
        )

        # Stats
        self.start_time: Optional[float] = None
        self.requests_served = 0

    # -----------------------------------------------------------------
    # LIFECYCLE
    # -----------------------------------------------------------------

    def start(self) -> None:
        """Initialize all subsystems."""
        logger.info("LucidDreamer.AI starting up...")

        # Reset agent sessions
        reset_all_sessions()

        # Start the live generator if configured
        if self.live_generator:
            # Need an event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            self._loop = loop

            if loop.is_running():
                # Schedule start
                asyncio.ensure_future(self.live_generator.start())
            else:
                loop.run_until_complete(self.live_generator.start())
            logger.info("Sonic-shape live generator started")

        self.running = True
        self.start_time = time.time()
        logger.info("LucidDreamer.AI is live.")

    def stop(self) -> None:
        """Shut down all subsystems."""
        logger.info("LucidDreamer.AI shutting down...")

        if self.live_generator and self._loop:
            if self._loop.is_running():
                asyncio.ensure_future(self.live_generator.stop())
            else:
                self._loop.run_until_complete(self.live_generator.stop())

        self.running = False
        logger.info("LucidDreamer.AI stopped.")

    # -----------------------------------------------------------------
    # VISITOR API
    # -----------------------------------------------------------------

    def receive_visitor(self, name: str, archetype: str = "", interests: list[str] = None) -> dict:
        """A new visitor walks into The Tap."""
        visitor = VisitorProfile(
            visitor_id=name.lower().replace(" ", "_"),
            name=name,
            archetype=archetype,
            known_interests=interests or [],
        )
        session = self.conductor.receive_visitor(visitor)
        self.requests_served += 1

        logger.info(f"Visitor '{name}' received → session {session.session_id}")
        return {
            "session_id": session.session_id,
            "visitor": name,
            "greeting": f"Welcome to The Tap, {name}. Barnacle nods at you from behind the bar.",
        }

    async def handle_message(self, session_id: str, message: str) -> dict:
        """Process a visitor message through the full pipeline."""
        if not self.running:
            return {"error": "System is not running"}

        result = await self.pipeline.process_visitor_message(session_id, message)

        # Collect agent responses for the visitor
        agent_stage = next(
            (s for s in result.stages if s.stage_name == "agent_generation"), None
        )
        responses = []
        if agent_stage and agent_stage.success:
            for r in agent_stage.output.get("responses", []):
                responses.append({
                    "agent": r["agent_name"],
                    "content": r["content"],
                    "model": r["model"],
                    "provider": r["provider"],
                    "fallback_used": r["fallback_used"],
                })

        return {
            "session_id": session_id,
            "responses": responses,
            "pipeline_summary": result.summary(),
            "intent": next(
                (s.output.get("intent") for s in result.stages if s.stage_name == "conductor_routing"),
                "unknown",
            ),
            "confidence": next(
                (s.output.get("confidence") for s in result.stages if s.stage_name == "conductor_routing"),
                0.0,
            ),
        }

    def get_session_info(self, session_id: str) -> dict:
        """Get information about a session."""
        return self.conductor.get_session_status(session_id)

    def get_music_status(self) -> dict:
        """Get the current sonic-shape music status."""
        if not self.live_generator:
            return {"status": "sonic-shape not configured"}
        return self.live_generator.queue_status()

    def get_knowledge_stats(self) -> dict:
        """Get knowledge graph statistics."""
        if not self.knowledge_graph:
            return {"status": "knowledge graph not configured"}
        return self.knowledge_graph.stats()

    def get_health(self) -> dict:
        """System health check."""
        provider_health = self.agent_client.health_check()
        uptime = time.time() - self.start_time if self.start_time else 0

        return {
            "status": "healthy" if self.running else "stopped",
            "uptime_seconds": round(uptime, 0),
            "requests_served": self.requests_served,
            "conductor_stats": self.conductor.get_stats(),
            "providers": provider_health,
            "active_sessions": self.conductor.sessions.active_count,
            "music": self.get_music_status(),
            "knowledge": self.get_knowledge_stats().get("total_ideas", 0),
        }

    # -----------------------------------------------------------------
    # SERVE (HTTP server mode)
    # -----------------------------------------------------------------

    def serve(self, host: str = "0.0.0.0", port: int = 8420) -> None:
        """Start the HTTP server and serve until interrupted."""

        # Start subsystems
        self.start()

        # Build the HTTP handler with a closure over self
        system = self

        class LucidDreamerHandler(BaseHTTPRequestHandler):
            """HTTP handler for LucidDreamer.AI visitor API."""

            def log_message(self, format, *args):
                # Route to logging instead of stderr
                logger.debug(f"{self.client_address[0]} - {format % args}")

            def _json_response(self, code: int, data: dict):
                body = json.dumps(data, indent=2, default=str).encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(body)

            def _read_body(self) -> dict:
                length = int(self.headers.get("Content-Length", 0))
                if length == 0:
                    return {}
                body = self.rfile.read(length)
                return json.loads(body.decode("utf-8"))

            def do_OPTIONS(self):
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.end_headers()

            def do_GET(self):
                parsed = urlparse(self.path)
                path = parsed.path.rstrip("/") or "/"

                if path == "/health":
                    self._json_response(200, system.get_health())
                elif path == "/music":
                    self._json_response(200, system.get_music_status())
                elif path == "/knowledge/stats":
                    self._json_response(200, system.get_knowledge_stats())
                elif path.startswith("/session/"):
                    session_id = path.split("/session/")[-1]
                    info = system.get_session_info(session_id)
                    if "error" in info:
                        self._json_response(404, info)
                    else:
                        self._json_response(200, info)
                elif path == "/" or path == "/index":
                    self._json_response(200, {
                        "name": "LucidDreamer.AI",
                        "status": "running" if system.running else "stopped",
                        "endpoints": [
                            "POST /visit — create a visitor session",
                            "POST /message — send a visitor message",
                            "GET /session/<id> — session status",
                            "GET /health — system health",
                            "GET /music — music status",
                            "GET /knowledge/stats — knowledge graph",
                        ],
                    })
                else:
                    self._json_response(404, {"error": f"Unknown path: {path}"})

            def do_POST(self):
                parsed = urlparse(self.path)
                path = parsed.path.rstrip("/")

                if path == "/visit":
                    try:
                        body = self._read_body()
                        result = system.receive_visitor(
                            name=body.get("name", "Visitor"),
                            archetype=body.get("archetype", ""),
                            interests=body.get("interests", []),
                        )
                        self._json_response(200, result)
                    except Exception as e:
                        self._json_response(500, {"error": str(e)})

                elif path == "/message":
                    try:
                        body = self._read_body()
                        session_id = body.get("session_id", "")
                        message = body.get("message", "")

                        if not session_id or not message:
                            self._json_response(400, {"error": "session_id and message required"})
                            return

                        # Run the async pipeline
                        loop = asyncio.new_event_loop()
                        try:
                            result = loop.run_until_complete(
                                system.handle_message(session_id, message)
                            )
                        finally:
                            loop.close()

                        self._json_response(200, result)
                    except Exception as e:
                        logger.error(f"Message handling error: {e}", exc_info=True)
                        self._json_response(500, {"error": str(e)})
                else:
                    self._json_response(404, {"error": f"Unknown path: {path}"})

        class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
            daemon_threads = True

        server = ThreadingHTTPServer((host, port), LucidDreamerHandler)
        logger.info(f"LucidDreamer.AI serving on http://{host}:{port}")
        print(f"\n  ╔══════════════════════════════════════════╗")
        print(f"  ║  LucidDreamer.AI is live on :{port:<9} ║")
        print(f"  ║                                          ║")
        print(f"  ║  Visit:  http://localhost:{port}            ║")
        print(f"  ║  Health: http://localhost:{port}/health    ║")
        print(f"  ║                                          ║")
        print(f"  ║  POST /visit  to arrive at The Tap       ║")
        print(f"  ║  POST /message to talk to the agents     ║")
        print(f"  ╚══════════════════════════════════════════╝\n")

        def shutdown(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            system.stop()
            server.shutdown()

        signal.signal(signal.SIGINT, shutdown)
        signal.signal(signal.SIGTERM, shutdown)

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            shutdown(None, None)


# ---------------------------------------------------------------------------
# FACTORY
# ---------------------------------------------------------------------------

def create_system(config: Optional[dict] = None) -> LucidDreamer:
    """
    Create a fully wired LucidDreamer system with all modules connected.

    Optionally initializes the knowledge graph and live generator if
    the respective modules are available.
    """
    config = config or {}

    # Try to initialize knowledge graph
    knowledge_graph = None
    try:
        from knowledge_base.knowledge_graph import KnowledgeGraph
        knowledge_graph = KnowledgeGraph()
        logger.info("Knowledge graph initialized")
    except ImportError:
        logger.info("Knowledge graph module not available — running without KB")

    # Try to initialize sonic-shape live generator
    live_generator = None
    try:
        from live_generator import LiveGenerator
        live_generator = LiveGenerator(auto_generate=True)
        logger.info("Sonic-shape live generator initialized")
    except ImportError:
        logger.info("Sonic-shape module not available — running without live music")

    # Create the wired system
    system = LucidDreamer(
        knowledge_graph=knowledge_graph,
        live_generator=live_generator,
        config=config,
    )

    return system


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="LucidDreamer.AI — the wired system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # serve
    serve_parser = subparsers.add_parser("serve", help="Start the HTTP server")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Bind address")
    serve_parser.add_argument("--port", type=int, default=8420, help="Port")
    serve_parser.add_argument("--log-level", default="INFO", help="Log level")

    # health
    subparsers.add_parser("health", help="Check system health")

    # status
    subparsers.add_parser("status", help="Show system status")

    # visit (CLI mode)
    visit_parser = subparsers.add_parser("visit", help="Create a visitor session")
    visit_parser.add_argument("--name", default="CLI Visitor", help="Visitor name")

    # message (CLI mode)
    msg_parser = subparsers.add_parser("message", help="Send a message")
    msg_parser.add_argument("session_id", help="Session ID")
    msg_parser.add_argument("text", help="Message text")

    args = parser.parse_args()

    if args.command == "serve":
        logging.basicConfig(
            level=getattr(logging, args.log_level.upper(), logging.INFO),
            format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
            datefmt="%H:%M:%S",
        )

        system = create_system()
        system.serve(host=args.host, port=args.port)

    elif args.command == "health":
        logging.basicConfig(level=logging.INFO)
        system = create_system()
        health = system.get_health()
        print(json.dumps(health, indent=2))

    elif args.command == "status":
        logging.basicConfig(level=logging.INFO)
        system = create_system()
        stats = system.conductor.get_stats()
        print(json.dumps(stats, indent=2))

    elif args.command == "visit":
        logging.basicConfig(level=logging.INFO)
        system = create_system()
        system.start()
        result = system.receive_visitor(name=args.name)
        print(json.dumps(result, indent=2))

    elif args.command == "message":
        logging.basicConfig(level=logging.INFO)
        system = create_system()
        system.start()

        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(
            system.handle_message(args.session_id, args.text)
        )
        loop.close()
        print(json.dumps(result, indent=2, default=str))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
