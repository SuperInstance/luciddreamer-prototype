# peer-consult

The peer consultation layer for [casting-call](../casting-call). Models don't
consult each other yet; this package makes `cast()` a conversation.

For each role, the **primary** model (cast by `CastingDirector`) answers the
task. A **critic** — the next model in the role's own fallback chain with a
*different* `VoiceCharacter` family (counterpoint constraint, no parallel
octaves) — attacks the answer devil's-advocate style. The semantic distance
Δ = 1 − cosine(answer, critique) lands in a zone band, and the band rules the
verdict:

| Zone              | Δ band      | Verdict   | Meaning                                   |
|-------------------|-------------|-----------|-------------------------------------------|
| STALE             | < 0.20      | CONFIRM   | redundant agreement                        |
| TRANSITIONAL_LOW  | 0.20–0.40   | NOTE      | mild divergence, noted                     |
| CREATIVE          | 0.40–0.60   | REVISE    | productive divergence; merge objections    |
| TRANSITIONAL_HIGH | 0.60–0.80   | NOTE      | strong divergence, noted                   |
| CHAOTIC           | > 0.80      | ESCALATE  | route to the `safety_check` role model     |

Every consultation also emits three **SWMIDI-8** events (8 bytes little-endian:
`[status, pitch, velocity, error_mask, tick u32 @96 PPQ]`): `cast=1`,
`consult=2`, `verdict=3` on the primary model's atlas channel. Velocity is
`round(confidence * 127)` with `confidence = 1 − Δ`; the SEMANTIC friction bit
(`0b00100000`) is set when the zone is CHAOTIC.

## Install

```bash
pip install -e /mnt/agents/repos/casting-call   # the dependency
pip install -e ./peer-consult
```

## Usage

```python
from peer_consult import (
    ConsultationDirector, BackendResolver,
    OllamaBackend, OllamaEmbedder,
)

resolver = BackendResolver({
    "SEED_MINI": OllamaBackend("granite3.1:2b"),
    "GLM_5_2": OllamaBackend("qwen:0.5b"),
})
director = ConsultationDirector(resolver=resolver, embedder=OllamaEmbedder())
consultation = director.cast_with_consult("intent_parse", "summarize the tide log")
print(consultation.verdict, consultation.rationale)
```

CLI:

```bash
peer-consult "intent_parse" "summarize the tide log" \
    --ollama-model-map primary=granite3.1:2b critic=qwen:0.5b
peer-consult "intent_parse" "summarize the tide log" --mock   # fully offline
```

## Run on the boat

The boat has 24 cores and no guaranteed uplink — run everything against local
Ollama at `localhost:11434`:

```bash
ollama pull granite3.1:2b qwen:0.5b nomic-embed-text
peer-consult "intent_parse" "plot tomorrow's passage" \
    --ollama-model-map primary=granite3.1:2b critic=qwen:0.5b
```

When the uplink is up, the cloud backends read their keys from the
environment — `DEEPINFRA_API_KEY` for `DeepInfraBackend` /
`DeepInfraEmbedder` (default embedding model `BAAI/bge-m3`),
`DEEPSEEK_API_KEY` for `DeepSeekBackend`:

```python
from peer_consult import DeepInfraBackend, DeepInfraEmbedder, DeepSeekBackend
resolver = BackendResolver({
    "SEED_MINI": DeepInfraBackend("ByteDance/Seed-mini"),   # DEEPINFRA_API_KEY
    "GLM_5_2": DeepSeekBackend(),                            # DEEPSEEK_API_KEY
})
director = ConsultationDirector(resolver=resolver, embedder=DeepInfraEmbedder())
```

No keys, no Ollama, no problem — **mock mode** runs the whole pipeline offline
(`MockBackend` + `HashEmbedder`), which is also exactly what the test suite
does:

```bash
peer-consult "intent_parse" "plot tomorrow's passage" --mock
python3 -m pytest -q    # green with zero network access
```
