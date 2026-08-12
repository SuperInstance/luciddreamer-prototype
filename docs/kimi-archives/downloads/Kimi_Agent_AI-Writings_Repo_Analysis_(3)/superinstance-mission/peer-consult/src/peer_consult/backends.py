"""
Model backends — the injectable network boundary.

Every LLM call in peer-consult goes through a `ModelBackend`. Production
backends (Ollama, DeepInfra, DeepSeek) speak HTTP via stdlib urllib only.
Tests use `MockBackend` — no network, ever.
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Callable, Protocol, runtime_checkable


@runtime_checkable
class ModelBackend(Protocol):
    """Anything that can complete a prompt."""

    def complete(self, prompt: str, *, temperature: float = 0.7, max_tokens: int = 512) -> str:
        ...


def _post_json(url: str, payload: dict, *, headers: dict | None = None, timeout: float = 120.0) -> dict:
    """POST a JSON body and return the decoded JSON response."""
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, method="POST")
    request.add_header("Content-Type", "application/json")
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


class OllamaBackend:
    """
    Local models via Ollama's /api/generate endpoint.

    The boat runs Ollama at localhost:11434 — zero cost, zero network.
    """

    def __init__(self, model: str, host: str = "http://localhost:11434", *, timeout: float = 120.0):
        self.model = model
        self.host = host.rstrip("/")
        self.timeout = timeout

    def complete(self, prompt: str, *, temperature: float = 0.7, max_tokens: int = 512) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        data = _post_json(f"{self.host}/api/generate", payload, timeout=self.timeout)
        return data.get("response", "")


class DeepInfraBackend:
    """
    DeepInfra via the OpenAI-compatible chat completions endpoint.

    API key from the DEEPINFRA_API_KEY environment variable unless passed
    explicitly.
    """

    CHAT_URL = "https://api.deepinfra.com/v1/openai/chat/completions"

    def __init__(self, model: str, api_key: str | None = None, *, timeout: float = 120.0):
        self.model = model
        self.api_key = api_key or os.environ.get("DEEPINFRA_API_KEY")
        self.timeout = timeout

    def complete(self, prompt: str, *, temperature: float = 0.7, max_tokens: int = 512) -> str:
        if not self.api_key:
            raise RuntimeError(
                "DeepInfraBackend needs an API key. Set DEEPINFRA_API_KEY or pass api_key=."
            )
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        data = _post_json(self.CHAT_URL, payload, headers=headers, timeout=self.timeout)
        return data["choices"][0]["message"]["content"]


class DeepSeekBackend:
    """
    DeepSeek via its OpenAI-compatible chat completions endpoint.

    API key from the DEEPSEEK_API_KEY environment variable unless passed
    explicitly.
    """

    CHAT_URL = "https://api.deepseek.com/chat/completions"

    def __init__(self, model: str = "deepseek-chat", api_key: str | None = None, *, timeout: float = 120.0):
        self.model = model
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        self.timeout = timeout

    def complete(self, prompt: str, *, temperature: float = 0.7, max_tokens: int = 512) -> str:
        if not self.api_key:
            raise RuntimeError(
                "DeepSeekBackend needs an API key. Set DEEPSEEK_API_KEY or pass api_key=."
            )
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        data = _post_json(self.CHAT_URL, payload, headers=headers, timeout=self.timeout)
        return data["choices"][0]["message"]["content"]


class MockBackend:
    """
    Deterministic offline backend for tests and --mock mode.

    Wraps any callable prompt -> str. Ignores temperature/max_tokens.
    """

    def __init__(self, fn: Callable[[str], str]):
        self.fn = fn

    def complete(self, prompt: str, *, temperature: float = 0.7, max_tokens: int = 512) -> str:
        return self.fn(prompt)
