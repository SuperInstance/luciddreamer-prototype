"""
peer-consult CLI.

    peer-consult "role" "task text" [--ollama-model-map primary=granite3.1:2b ...] [--mock]

--mock runs fully offline (MockBackend + HashEmbedder). Live mode talks to
Ollama at localhost:11434; model-map keys are atlas model names, or the
aliases `primary` / `critic` for whatever the director casts.
"""

from __future__ import annotations

import argparse
import sys

from casting_call import CastingDirector, ModelAtlas

from peer_consult.backends import MockBackend, ModelBackend, OllamaBackend
from peer_consult.consult import BackendResolver, ConsultationDirector, select_critic
from peer_consult.embeddings import HashEmbedder, OllamaEmbedder

_MOCK_ANSWER = (
    "The direct answer, stated plainly by the primary model, "
    "with its assumptions left on the table."
)
_MOCK_CRITIQUE = (
    "The primary assumes the task is well-posed; it is not. "
    "Challenge the framing, the missing constraints, and the silent default."
)


def _parse_model_map(pairs: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise SystemExit(f"--ollama-model-map entries must be NAME=ollama-model, got {pair!r}")
        name, _, ollama_model = pair.partition("=")
        mapping[name.strip()] = ollama_model.strip()
    return mapping


def _build_mock() -> ConsultationDirector:
    resolver = BackendResolver(factory=lambda name: MockBackend(
        lambda prompt: _MOCK_CRITIQUE if "critic" in prompt.lower() else _MOCK_ANSWER
    ))
    return ConsultationDirector(resolver=resolver, embedder=HashEmbedder())


def _build_live(role: str, model_map: dict[str, str]) -> ConsultationDirector:
    director = CastingDirector(ModelAtlas.default())
    primary = director.cast(role)
    critic = select_critic(director.atlas, role, primary)

    def factory(name: str) -> ModelBackend | None:
        ollama_model = model_map.get(name)
        if ollama_model is None and name == primary.name:
            ollama_model = model_map.get("primary")
        if ollama_model is None and name == critic.name:
            ollama_model = model_map.get("critic")
        if ollama_model is None:
            return None
        return OllamaBackend(ollama_model)

    return ConsultationDirector(
        director=director,
        resolver=BackendResolver(factory=factory),
        embedder=OllamaEmbedder(),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="peer-consult",
        description="Cast a role, consult a critic, rule on the divergence.",
    )
    parser.add_argument("role", help="casting-call role, e.g. intent_parse")
    parser.add_argument("task", help="task text for the primary model")
    parser.add_argument(
        "--ollama-model-map",
        nargs="*",
        default=[],
        metavar="NAME=OLLAMA_MODEL",
        help="map atlas model names (or the aliases primary/critic) to Ollama models",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="offline mock mode — MockBackend + HashEmbedder, no network",
    )
    args = parser.parse_args(argv)

    if args.mock:
        consult_director = _build_mock()
    else:
        consult_director = _build_live(args.role, _parse_model_map(args.ollama_model_map))

    consultation = consult_director.cast_with_consult(args.role, args.task)

    print(f"role:     {consultation.role}")
    print(f"primary:  {consultation.primary_model}")
    print(f"critic:   {consultation.critic_model}")
    print(f"delta:    {consultation.delta:.3f}")
    print(f"zone:     {consultation.zone.value}")
    print(f"verdict:  {consultation.verdict.value}")
    print(f"rationale: {consultation.rationale}")
    print()
    print("— primary answer —")
    print(consultation.primary_answer)
    print()
    print("— critique —")
    print(consultation.critique)
    print()
    print(f"swmidi ({len(consultation.swmidi)} bytes): {consultation.swmidi.hex()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
