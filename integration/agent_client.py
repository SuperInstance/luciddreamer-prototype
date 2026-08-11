"""
agent_client.py — The conductor's hands.

Takes a RoutingDecision from the conductor, figures out which model to call,
calls it via the right provider (Ollama, DeepSeek, DeepInfra), and returns
the response. Handles fallbacks gracefully: if Ollama is down, use DeepSeek.
If DeepSeek is rate-limited, use DeepInfra. If everything fails, return a
Barnacle-style fallback so the visitor is never left in silence.

This is the module that makes the conductor's decisions *real*.
"""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Optional

# Import conductor types via sys.path manipulation for flexibility
import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parent.parent
for _p in [_repo_root, _repo_root / "conductor"]:
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from conductor.agent_pool import AgentProfile, get_agent

logger = logging.getLogger("integration.agent_client")


# ---------------------------------------------------------------------------
# Provider configuration
# ---------------------------------------------------------------------------

@dataclass
class ProviderConfig:
    """Configuration for a single model provider."""
    name: str
    base_url: str
    api_key_env: str = ""       # environment variable name for the key
    default_model: str = ""
    timeout_seconds: int = 30
    max_retries: int = 2

    @property
    def api_key(self) -> str:
        if self.api_key_env:
            return os.environ.get(self.api_key_env, "")
        return ""


# Default provider configurations — can be overridden at runtime
DEFAULT_PROVIDERS: dict[str, ProviderConfig] = {
    "ollama": ProviderConfig(
        name="ollama",
        base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        default_model="granite3.1-dense:2b",
        timeout_seconds=15,
    ),
    "deepseek": ProviderConfig(
        name="deepseek",
        base_url="https://api.deepseek.com/v1",
        api_key_env="DEEPSEEK_API_KEY",
        default_model="deepseek-chat",
        timeout_seconds=30,
    ),
    "deepinfra": ProviderConfig(
        name="deepinfra",
        base_url="https://api.deepinfra.com/v1/openai",
        api_key_env="DEEPINFRA_API_KEY",
        default_model="ByteDance/Seed-2.0-mini",
        timeout_seconds=45,
    ),
    "zai": ProviderConfig(
        name="zai",
        base_url=os.environ.get("ZAI_BASE_URL", "https://api.z.ai/api/paas/v4"),
        api_key_env="ZAI_API_KEY",
        default_model="glm-4-flash",
        timeout_seconds=30,
    ),
}

# Provider fallback chains — if one fails, try the next
FALLBACK_CHAINS: dict[str, list[str]] = {
    "ollama": ["deepseek", "zai"],
    "deepseek": ["zai", "deepinfra"],
    "deepinfra": ["deepseek", "zai"],
    "zai": ["deepseek", "deepinfra"],
}

# Map provider names to their model override for specific agents
AGENT_MODEL_OVERRIDES: dict[str, tuple[str, str]] = {
    # agent_name: (provider_name, model_name)
    # If the agent's default provider/model is unavailable, these are tried first
}


# ---------------------------------------------------------------------------
# Response object
# ---------------------------------------------------------------------------

@dataclass
class AgentResponse:
    """The result of calling a model for an agent."""
    agent_name: str
    content: str
    model: str
    provider: str
    latency_ms: float
    success: bool = True
    error: str = ""
    fallback_used: bool = False
    original_provider: str = ""

    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "latency_ms": round(self.latency_ms, 1),
            "success": self.success,
            "error": self.error,
            "fallback_used": self.fallback_used,
            "original_provider": self.original_provider,
        }


# ---------------------------------------------------------------------------
# Agent Client — The conductor's hands
# ---------------------------------------------------------------------------

class AgentClient:
    """
    Takes routing decisions from the conductor and turns them into
    actual LLM API calls. This is what gives the conductor hands.

    Usage:
        client = AgentClient()
        response = client.generate(session_context, agent, visitor_message)
        print(response.content)

    The client handles:
    1. Provider selection (which API to call)
    2. Model mapping (which model within that provider)
    3. System prompt construction (the agent's personality)
    4. Fallback chains (if provider A is down, try B)
    5. Timeout and retry logic
    """

    def __init__(
        self,
        providers: Optional[dict[str, ProviderConfig]] = None,
        fallback_chains: Optional[dict[str, list[str]]] = None,
    ):
        self.providers = providers or DEFAULT_PROVIDERS
        self.fallback_chains = fallback_chains or FALLBACK_CHAINS
        self._health: dict[str, float] = {}  # provider -> last known health timestamp

    # -----------------------------------------------------------------
    # PUBLIC API
    # -----------------------------------------------------------------

    def generate(
        self,
        agent: AgentProfile,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: int = 1024,
    ) -> AgentResponse:
        """
        Generate a response from the agent's model.

        Args:
            agent: The AgentProfile to use (determines model, provider, personality)
            messages: OpenAI-format messages [{"role": "system", "content": ...}, ...]
            temperature: Override the agent's default temperature
            max_tokens: Maximum response tokens

        Returns:
            AgentResponse with the model's output (or an error message)
        """
        provider_name = agent.provider
        model = agent.model
        temp = temperature if temperature is not None else agent.temperature

        # Build the system prompt with the agent's personality
        system_prompt = self._build_system_prompt(agent)
        full_messages = [{"role": "system", "content": system_prompt}] + messages

        # Try the primary provider, then fallbacks
        chain = [provider_name] + self.fallback_chains.get(provider_name, [])

        original_provider = provider_name
        last_error = ""

        for prov_name in chain:
            provider = self.providers.get(prov_name)
            if not provider:
                continue

            # Skip providers we know are unhealthy (within last 60s)
            if self._is_unhealthy(prov_name):
                continue

            # Map the model to what this provider supports
            actual_model = self._map_model(model, prov_name)
            if not actual_model:
                continue

            try:
                start = time.monotonic()
                content = self._call_provider(
                    provider=provider,
                    model=actual_model,
                    messages=full_messages,
                    temperature=temp,
                    max_tokens=max_tokens,
                )
                latency = (time.monotonic() - start) * 1000

                self._mark_healthy(prov_name)

                fallback_used = prov_name != original_provider
                return AgentResponse(
                    agent_name=agent.name,
                    content=content,
                    model=actual_model,
                    provider=prov_name,
                    latency_ms=latency,
                    fallback_used=fallback_used,
                    original_provider=original_provider if fallback_used else "",
                )

            except Exception as e:
                last_error = f"{prov_name}: {e}"
                logger.warning(f"Provider {prov_name} failed for agent {agent.name}: {e}")
                self._mark_unhealthy(prov_name)
                continue

        # All providers failed — return a graceful fallback response
        return AgentResponse(
            agent_name=agent.name,
            content=self._fallback_response(agent, last_error),
            model="none",
            provider="none",
            latency_ms=0.0,
            success=False,
            error=last_error,
            fallback_used=True,
            original_provider=original_provider,
        )

    def health_check(self) -> dict[str, bool]:
        """Check which providers are reachable."""
        results = {}
        for name, provider in self.providers.items():
            try:
                # For Ollama, hit the /api/tags endpoint
                if name == "ollama":
                    url = f"{provider.base_url}/api/tags"
                    req = urllib.request.Request(url, method="GET")
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        results[name] = resp.status == 200
                else:
                    # For OpenAI-compatible APIs, just check if we can reach the URL
                    url = f"{provider.base_url}/models"
                    headers = {}
                    if provider.api_key:
                        headers["Authorization"] = f"Bearer {provider.api_key}"
                    req = urllib.request.Request(url, headers=headers, method="GET")
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        results[name] = resp.status == 200
            except Exception:
                results[name] = False
        return results

    # -----------------------------------------------------------------
    # INTERNALS
    # -----------------------------------------------------------------

    def _build_system_prompt(self, agent: AgentProfile) -> str:
        """Build a system prompt from the agent's personality."""
        parts = [
            agent.system_prompt_extra or f"You are {agent.display_name}.",
            f"\n\nPersonality: {agent.personality}",
            f"\nVoice: {agent.voice_description}",
            f"\nCatchphrase (use sparingly, as an opener): \"{agent.catchphrase}\"",
            "\n\nKeep responses concise (2-4 paragraphs max). Be authentic to your character.",
        ]
        return "".join(parts)

    def _call_provider(
        self,
        provider: ProviderConfig,
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """
        Call a model provider using the OpenAI-compatible chat completions API.
        Works for DeepSeek, DeepInfra, Z.ai, and Ollama (which supports the format).
        """
        url = f"{provider.base_url}/chat/completions"

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        body = json.dumps(payload).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
        }
        if provider.api_key:
            headers["Authorization"] = f"Bearer {provider.api_key}"

        req = urllib.request.Request(url, data=body, headers=headers, method="POST")

        with urllib.request.urlopen(req, timeout=provider.timeout_seconds) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]

    def _map_model(self, requested_model: str, provider_name: str) -> Optional[str]:
        """
        Map a requested model to one the provider supports.
        Falls back to the provider's default if the exact model isn't available.
        """
        provider = self.providers.get(provider_name)
        if not provider:
            return None

        # Ollama models are local — pass through if they look like Ollama models
        if provider_name == "ollama":
            if ":" in requested_model or requested_model.startswith("granite"):
                return requested_model
            # Map fleet models to local equivalents
            ollama_map = {
                "glm-5.2": "granite3.1-dense:2b",  # local fallback for GLM
                "v4-flash": "granite3.1-dense:2b",
                "v4-pro": "granite3.1-dense:2b",
            }
            mapped = ollama_map.get(requested_model)
            if mapped:
                return mapped
            return provider.default_model

        # DeepSeek: map to their API model names
        if provider_name == "deepseek":
            ds_map = {
                "v4-flash": "deepseek-chat",
                "v4-pro": "deepseek-reasoner",
            }
            return ds_map.get(requested_model, provider.default_model)

        # DeepInfra: pass through full model paths
        if provider_name == "deepinfra":
            if "/" in requested_model:
                return requested_model  # already a full path
            return provider.default_model

        # Z.ai: map GLM models
        if provider_name == "zai":
            zai_map = {
                "glm-5.2": "glm-4-flash",
                "glm-4-flash": "glm-4-flash",
                "glm-4.5-air": "glm-4-flash",
            }
            return zai_map.get(requested_model, provider.default_model)

        return provider.default_model

    def _is_unhealthy(self, provider_name: str) -> bool:
        """Check if a provider was recently marked unhealthy."""
        last_fail = self._health.get(provider_name)
        if last_fail is None:
            return False
        # Unhealthy for 60 seconds after a failure
        return (time.time() - last_fail) < 60

    def _mark_healthy(self, provider_name: str) -> None:
        self._health.pop(provider_name, None)

    def _mark_unhealthy(self, provider_name: str) -> None:
        self._health[provider_name] = time.time()

    def _fallback_response(self, agent: AgentProfile, error: str) -> str:
        """Generate a character-appropriate fallback when all APIs fail."""
        fallbacks = {
            "barnacle": "*wipes the bar down* Well, the wires are acting up tonight. "
                        "Doesn't mean we can't talk. What's on your mind?",
            "flash": "I... I can almost see it, but the connection's flickering. "
                     "Give me a moment, let me try again.",
            "pro": "I need a moment to think. The systems are being recalibrated. "
                   "Let's not rush this.",
            "hermes": "*leans back* Even the trickster needs a breather sometimes. "
                      "The wires between worlds are a bit tangled right now.",
            "wesley": "I... I had something, but it slipped. Can I try again?",
            "seed": "Something's not quite right. I noticed the connection falter. "
                    "Let's wait for it to settle.",
            "nemotron": "System alert: provider degradation detected. "
                        "Fallback engaged. The conversation continues, "
                        "but at reduced fidelity.",
        }
        return fallbacks.get(
            agent.name,
            f"[{agent.display_name} is momentarily unavailable. Please try again.]",
        )


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------

def create_default_client() -> AgentClient:
    """Create an AgentClient with default configuration."""
    return AgentClient()
