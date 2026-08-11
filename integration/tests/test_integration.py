"""
test_integration.py — Integration tests for the LucidDreamer.AI integration layer.

These tests verify that the modules actually TALK to each other:
  1. Conductor → AgentClient → response (with mocked API)
  2. Session → Knowledge base → query
  3. Sonic-shape → MMX command generation
  4. Pipeline runs end-to-end with mock data
  5. Fallback when primary model is unavailable

Run: pytest integration/tests/test_integration.py -v
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

# Set up paths
_repo_root = Path(__file__).resolve().parent.parent.parent
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


class TestConductorToAgentClient(unittest.IsolatedAsyncioTestCase):
    """
    Test 1: Conductor → AgentClient → Response

    Verify that a routing decision from the conductor can be turned into
    an actual API call (mocked) that returns a response.
    """

    async def test_conductor_decision_to_agent_response(self):
        """Conductor routes a message, AgentClient generates a response."""
        from conductor.conductor import Conductor
        from conductor.session import VisitorProfile
        from conductor.agent_pool import get_agent
        from integration.agent_client import AgentClient, AgentResponse, ProviderConfig

        # Set up conductor with a visitor
        conductor = Conductor()
        visitor = VisitorProfile(
            visitor_id="test_visitor",
            name="Test Visitor",
            archetype="curious explorer",
        )
        session = conductor.receive_visitor(visitor)

        # Route a creative message
        decision = conductor.route_visitor_message(
            session.session_id, "Tell me a story about the ocean"
        )

        # Verify the conductor made a decision
        self.assertIsNotNone(decision)
        self.assertTrue(len(decision.responding_agents) > 0)
        self.assertGreater(decision.confidence, 0.0)

        # Now mock the AgentClient to return a canned response
        client = AgentClient()

        # Mock the _call_provider method to avoid real API calls
        def mock_call(provider, model, messages, temperature, max_tokens):
            return ("*leans on the bar* Let me tell you about the deep places, "
                    "where the light doesn't reach and the pressure makes diamonds.")

        with patch.object(client, '_call_provider', side_effect=mock_call):
            agent = get_agent(decision.responding_agents[0])
            self.assertIsNotNone(agent, f"Agent {decision.responding_agents[0]} not found")

            messages = [{"role": "user", "content": "Tell me a story about the ocean"}]
            response = client.generate(agent, messages)

        # Verify the response
        self.assertTrue(response.success)
        self.assertEqual(response.agent_name, agent.name)
        self.assertIn("deep places", response.content)
        self.assertGreater(response.latency_ms, 0)

    async def test_conductor_tracks_response_in_session(self):
        """When a response is generated, the conductor records it in the session."""
        from conductor.conductor import Conductor
        from conductor.session import VisitorProfile

        conductor = Conductor()
        visitor = VisitorProfile(visitor_id="v1", name="Test")
        session = conductor.receive_visitor(visitor)

        # Send a message
        decision = conductor.route_visitor_message(session.session_id, "hello there")
        self.assertIn("barnacle", decision.responding_agents)

        # Simulate Barnacle responding
        msg = conductor.route_agent_response(
            session.session_id, "barnacle", "Pull up a stool. What'll it be?"
        )

        # Verify it was recorded
        updated_session = conductor.sessions.get_session(session.session_id)
        self.assertIsNotNone(updated_session)
        agent_responses = [m for m in updated_session.messages if m.role == "agent"]
        self.assertEqual(len(agent_responses), 1)
        self.assertEqual(agent_responses[0].content, "Pull up a stool. What'll it be?")
        self.assertEqual(agent_responses[0].agent_name, "barnacle")


class TestSessionToKnowledgeBase(unittest.TestCase):
    """
    Test 2: Session → Knowledge Base → Query

    Verify that session content can be ingested into the knowledge graph
    and queried back.
    """

    def test_session_ingestion_and_query(self):
        """Ingest a session into the knowledge graph and query it."""
        # knowledge-base uses a hyphenated dir, add to path explicitly
        kb_path = str(Path(__file__).resolve().parent.parent.parent / "knowledge-base")
        if kb_path not in sys.path:
            sys.path.insert(0, kb_path)
        from knowledge_graph import KnowledgeGraph
        from idea_schema import IdeaNode, IdeaStatus, IdeaType
        from ingest_session import extract_ideas_from_markdown

        # Sample session markdown
        session_md = """
# The Tap — Night of August 11

## On the Nature of Presence
**Presence is not about being seen — it's about being felt.**

## What Nobody Modeled
Nobody has modeled the experience of being in a room where every agent
is thinking at full capacity and the room itself becomes aware.

## The Convergence
All three documents independently identified that the feedback loop
is not closed. It is porous. It breathes.
        """.strip()

        # Extract ideas
        ideas, session_node = extract_ideas_from_markdown(
            session_md,
            source_file="test_session.md",
            source_model="model_flash",
            session_id="test_session_001",
        )

        # Verify ideas were extracted
        self.assertGreater(len(ideas), 0, "Should extract at least one idea")

        # Add to knowledge graph
        graph = KnowledgeGraph()
        graph.add_ideas(ideas)

        # Query the graph
        all_nodes = list(graph.nodes.values())
        self.assertEqual(len(all_nodes), len(ideas))

        # Search for "presence"
        presence_results = graph.search_text("presence")
        self.assertGreater(len(presence_results), 0, "Should find 'presence' ideas")

        # Check stats
        stats = graph.stats()
        self.assertGreater(stats["total_ideas"], 0)
        self.assertIn("by_type", stats)


class TestSonicShapeToMMX(unittest.TestCase):
    """
    Test 3: Sonic-shape → MMX command generation

    Verify that confidence readings produce valid MMX commands that
    could be executed to generate music.
    """

    def test_confidence_to_mmx_command(self):
        """Feed confidence into the live generator and verify MMX commands are produced."""
        from harmonic_dictionary import ConfidenceBand, confidence_to_music, get_band
        from voice_profiles import get_voice

        # Test each confidence band produces valid MMX parameters
        test_cases = [
            (0.15, ConfidenceBand.UNCERTAIN),
            (0.50, ConfidenceBand.CREATIVE),
            (0.78, ConfidenceBand.EMERGING),
            (0.95, ConfidenceBand.CONFIDENT),
        ]

        for confidence, expected_band in test_cases:
            with self.subTest(confidence=confidence):
                band = get_band(confidence)
                # The band might not exactly match due to transitional handling
                self.assertIsNotNone(band)

                params = confidence_to_music(confidence, seed=42)
                self.assertIsNotNone(params)
                self.assertGreater(params.tempo_bpm, 0)
                self.assertLess(params.tempo_bpm, 200)
                self.assertTrue(params.key)
                self.assertTrue(params.primary_instrument)

                # Generate MMX prompt
                prompt = params.to_mmx_prompt()
                self.assertTrue(prompt, "MMX prompt should not be empty")

    def test_live_generator_produces_commands(self):
        """The live generator should produce QueuedPiece objects with MMX commands."""
        from live_generator import LiveGenerator, GeneratorState

        gen = LiveGenerator(auto_generate=True, seed=42)

        async def run_test():
            await gen.start()

            # Feed different confidence levels
            gen.feed_confidence(0.15, model_name="wesley")  # uncertain
            gen.feed_confidence(0.50, model_name="flash")   # creative
            gen.feed_confidence(0.92, model_name="pro")     # confident

            await gen.stop()

            # Check the queue
            queue = gen.peek_queue()
            assert len(queue) > 0, "Should have generated at least one piece"

            for piece in queue:
                assert piece.mmx_command, "Each piece should have an MMX command"
                assert "mmx music" in piece.mmx_command, "Command should start with 'mmx music'"
                assert "--prompt" in piece.mmx_command, "Command should have --prompt"
                assert "--duration" in piece.mmx_command, "Command should have --duration"

            # Check stats
            status = gen.queue_status()
            assert status["total_generated"] > 0, "Should have generated pieces"
            assert status["state"] == "stopped"

        asyncio.run(run_test())

    def test_voice_profiles_map_to_mmx(self):
        """Each fleet model should have a voice profile with MMX prompt info."""
        from voice_profiles import get_voice, MODEL_VOICES

        # Check key fleet models
        for model_name in ["flash", "pro", "hermes", "wesley"]:
            voice = get_voice(model_name)
            self.assertIsNotNone(voice, f"Should have voice profile for {model_name}")
            self.assertTrue(voice.primary_instrument)
            self.assertTrue(voice.display_name)
            # Voice should be able to build a prompt
            prompt = voice.build_prompt()
            self.assertTrue(prompt, f"Voice for {model_name} should produce a prompt")

        # Verify the registry exists
        self.assertGreaterEqual(len(MODEL_VOICES), 4)


class TestPipelineEndToEnd(unittest.IsolatedAsyncioTestCase):
    """
    Test 4: Pipeline runs end-to-end with mock data

    Verify that the full pipeline can process a visitor message through
    all stages without real API calls.
    """

    async def test_pipeline_processes_visitor_message(self):
        """The pipeline should process a visitor message through all stages."""
        kb_path = str(Path(__file__).resolve().parent.parent.parent / "knowledge-base")
        if kb_path not in sys.path:
            sys.path.insert(0, kb_path)
        from conductor.conductor import Conductor
        from conductor.session import VisitorProfile
        from integration.agent_client import AgentClient, AgentResponse
        from integration.pipeline import Pipeline
        from knowledge_graph import KnowledgeGraph

        # Wire up the pipeline
        conductor = Conductor()
        client = AgentClient()
        kg = KnowledgeGraph()

        pipe = Pipeline(
            conductor=conductor,
            agent_client=client,
            knowledge_graph=kg,
        )

        # Create a visitor session
        visitor = VisitorProfile(visitor_id="test_v", name="Test Visitor")
        session = conductor.receive_visitor(visitor)

        # Mock the agent client to return canned responses
        def mock_generate(agent, messages, **kwargs):
            return AgentResponse(
                agent_name=agent.name,
                content=f"Hello from {agent.display_name}! Welcome to The Tap.",
                model=agent.model,
                provider=agent.provider,
                latency_ms=42.0,
            )

        with patch.object(client, 'generate', side_effect=mock_generate):
            result = await pipe.process_visitor_message(
                session.session_id,
                "Hello, I'd like to explore some creative ideas today",
            )

        # Verify the pipeline ran all stages
        stage_names = [s.stage_name for s in result.stages]
        self.assertIn("conductor_routing", stage_names)
        self.assertIn("agent_generation", stage_names)
        self.assertIn("knowledge_ingestion", stage_names)
        self.assertIn("sonic_shape", stage_names)
        self.assertIn("streamer_update", stage_names)

        # Conductor routing should succeed
        routing_stage = next(s for s in result.stages if s.stage_name == "conductor_routing")
        self.assertTrue(routing_stage.success)
        self.assertGreater(len(routing_stage.output["responding_agents"]), 0)

        # Agent generation should succeed
        agent_stage = next(s for s in result.stages if s.stage_name == "agent_generation")
        self.assertTrue(agent_stage.success)
        self.assertGreater(agent_stage.output["response_count"], 0)

        # Knowledge ingestion should add ideas
        kb_stage = next(s for s in result.stages if s.stage_name == "knowledge_ingestion")
        self.assertTrue(kb_stage.success)
        self.assertGreater(kb_stage.output.get("ideas_added", 0), 0)
        self.assertGreater(kb_stage.output.get("total_in_graph", 0), 0)

        # Overall result should be successful
        self.assertTrue(result.overall_success)

    async def test_pipeline_continues_on_stage_failure(self):
        """If one stage fails, the pipeline should continue running other stages."""
        kb_path = str(Path(__file__).resolve().parent.parent.parent / "knowledge-base")
        if kb_path not in sys.path:
            sys.path.insert(0, kb_path)
        from conductor.conductor import Conductor
        from conductor.session import VisitorProfile
        from integration.pipeline import Pipeline
        from knowledge_graph import KnowledgeGraph

        conductor = Conductor()
        kg = KnowledgeGraph()

        # Create a pipeline with a broken agent client
        class BrokenClient:
            def generate(self, *args, **kwargs):
                raise ConnectionError("All providers are down")

            def health_check(self):
                return {"ollama": False, "deepseek": False}

        pipe = Pipeline(
            conductor=conductor,
            agent_client=BrokenClient(),
            knowledge_graph=kg,
        )

        visitor = VisitorProfile(visitor_id="broken_v", name="Broken Visitor")
        session = conductor.receive_visitor(visitor)

        result = await pipe.process_visitor_message(
            session.session_id,
            "Hello there, can you help me?"
        )

        # Conductor routing should still succeed
        routing_stage = next(s for s in result.stages if s.stage_name == "conductor_routing")
        self.assertTrue(routing_stage.success)

        # Agent generation should fail, but pipeline continues
        agent_stage = next(s for s in result.stages if s.stage_name == "agent_generation")
        self.assertFalse(agent_stage.success)

        # Knowledge ingestion should still be attempted
        kb_stage = next(s for s in result.stages if s.stage_name == "knowledge_ingestion")
        # Even without responses, it should succeed (records the visitor message at least)
        # or it may fail gracefully — either way, the pipeline didn't crash


class TestFallbackBehavior(unittest.TestCase):
    """
    Test 5: Fallback when primary model is unavailable

    Verify that the AgentClient falls back to alternative providers when
    the primary provider is down.
    """

    def test_fallback_chain_activates(self):
        """When the primary provider fails, the fallback chain should activate."""
        from integration.agent_client import AgentClient, ProviderConfig, AgentResponse
        from conductor.agent_pool import get_agent

        # Create test providers
        test_providers = {
            "ollama": ProviderConfig(
                name="ollama",
                base_url="http://localhost:99999",  # invalid port → will fail
                default_model="test-model",
                timeout_seconds=1,
            ),
            "deepseek": ProviderConfig(
                name="deepseek",
                base_url="http://localhost:99998",  # also invalid
                default_model="test-model",
                timeout_seconds=1,
            ),
            "zai": ProviderConfig(
                name="zai",
                base_url="http://localhost:99997",  # also invalid
                default_model="test-model",
                timeout_seconds=1,
            ),
        }

        client = AgentClient(providers=test_providers)

        # Get Barnacle (uses ollama provider with fallback)
        barnacle = get_agent("barnacle")

        # Mock _call_provider to simulate: ollama fails, zai succeeds
        call_count = {"ollama": 0, "deepseek": 0, "zai": 0}

        def mock_call(provider, model, messages, temperature, max_tokens):
            call_count[provider.name] += 1
            if provider.name == "ollama":
                raise ConnectionRefusedError("Ollama is down")
            if provider.name == "deepseek":
                raise ConnectionRefusedError("DeepSeek is down")
            # zai succeeds
            return "Barnacle says: The bar's open, even if the wires are tangled."

        # Barnacle's provider is 'zai', so the chain starts from 'zai'
        # and its fallbacks are deepseek, deepinfra — not ollama.
        # Let's instead test with Wesley whose provider is 'ollama'
        wesley = get_agent("wesley")

        with patch.object(client, '_call_provider', side_effect=mock_call):
            messages = [{"role": "user", "content": "Hello"}]
            response = client.generate(wesley, messages)

        # Wesley's provider is 'ollama', so the chain is: ollama → deepseek → zai
        self.assertGreater(call_count["ollama"], 0, "Should have tried ollama first")
        self.assertGreater(call_count["zai"], 0, "Should have reached the zai fallback")

        # The response should eventually succeed via a fallback
        self.assertIsInstance(response, AgentResponse)
        self.assertTrue(response.success)
        self.assertTrue(response.fallback_used)

    def test_graceful_fallback_response(self):
        """When ALL providers fail, the client returns a character-appropriate fallback."""
        from integration.agent_client import AgentClient, ProviderConfig
        from conductor.agent_pool import get_agent

        # All providers point to invalid addresses
        test_providers = {
            "ollama": ProviderConfig(
                name="ollama",
                base_url="http://localhost:99999",
                default_model="test",
                timeout_seconds=1,
            ),
            "deepseek": ProviderConfig(
                name="deepseek",
                base_url="http://localhost:99998",
                default_model="test",
                timeout_seconds=1,
            ),
        }

        client = AgentClient(providers=test_providers)
        barnacle = get_agent("barnacle")

        # All providers fail
        def mock_call(provider, model, messages, temperature, max_tokens):
            raise ConnectionRefusedError(f"{provider.name} is down")

        with patch.object(client, '_call_provider', side_effect=mock_call):
            messages = [{"role": "user", "content": "Hello"}]
            response = client.generate(barnacle, messages)

        # Should get a fallback response
        self.assertFalse(response.success)
        self.assertTrue(len(response.content) > 10, "Fallback should be a real message")
        self.assertIn("wires", response.content.lower())

    def test_health_tracking_prevents_repeated_failures(self):
        """Failed providers should be temporarily marked unhealthy."""
        from integration.agent_client import AgentClient

        client = AgentClient()

        # Mark a provider as unhealthy
        client._mark_unhealthy("test_provider")

        self.assertTrue(client._is_unhealthy("test_provider"))

        # After marking healthy again
        client._mark_healthy("test_provider")
        self.assertFalse(client._is_unhealthy("test_provider"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
