"""
Offline tests for peer_consult.backends.

MockBackend only completes prompts; the network backends are exercised just
far enough to prove they fail fast without an API key (before any socket is
opened).
"""

import pytest

from peer_consult.backends import (
    DeepInfraBackend,
    DeepSeekBackend,
    MockBackend,
    ModelBackend,
    OllamaBackend,
)


class TestMockBackend:
    def test_returns_fn_output(self):
        backend = MockBackend(lambda prompt: f"echo:{prompt}")
        assert backend.complete("hello") == "echo:hello"

    def test_accepts_generation_kwargs(self):
        backend = MockBackend(lambda prompt: "ok")
        assert backend.complete("hello", temperature=0.1, max_tokens=8) == "ok"

    def test_satisfies_protocol(self):
        assert isinstance(MockBackend(str), ModelBackend)


class TestNetworkBackendsFailFastOffline:
    def test_deepinfra_requires_api_key(self, monkeypatch):
        monkeypatch.delenv("DEEPINFRA_API_KEY", raising=False)
        backend = DeepInfraBackend("some/model")
        with pytest.raises(RuntimeError, match="DEEPINFRA_API_KEY"):
            backend.complete("hello")

    def test_deepseek_requires_api_key(self, monkeypatch):
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        backend = DeepSeekBackend()
        with pytest.raises(RuntimeError, match="DEEPSEEK_API_KEY"):
            backend.complete("hello")

    def test_explicit_api_key_is_accepted(self, monkeypatch):
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        assert DeepSeekBackend(api_key="sk-test").api_key == "sk-test"
        assert DeepInfraBackend("m", api_key="k").api_key == "k"

    def test_ollama_defaults(self):
        backend = OllamaBackend("granite3.1:2b")
        assert backend.host == "http://localhost:11434"
        assert backend.model == "granite3.1:2b"
