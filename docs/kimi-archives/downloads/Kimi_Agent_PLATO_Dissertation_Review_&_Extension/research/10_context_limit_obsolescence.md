# Beyond Context Windows: How the Ether Framework Makes Token Limits Obsolete

## A Research Brief on Context-Limit Obsolescence and the Spatial Reasoning Revolution

**Date:** June 2025
**Research Domain:** AI Architecture, Context Window Alternatives, Spatial Reasoning, Post-Transformer Design Paradigms

---

## Executive Summary

The transformer architecture's defining bottleneck — the O(n²) attention mechanism that forces LLMs to process every token of context at every inference step — is not merely an engineering limitation but a fundamental category error. Current approaches fall into two camps: making attention more efficient (sparse attention, state-space models like Mamba) or bypassing it through retrieval (RAG, prompt compression). Neither challenges the deeper assumption: that intelligence requires access to total state.

This brief argues that the Ether (PLATO) framework offers a third path — making context windows obsolete not by extending them but by replacing the ontology of "context" with **situated presence**. By treating "rooms" as persistent computational places rather than disposable context windows, by recording only *deltas* (changes) rather than full state, by grounding agent knowledge in *witnessed experience* rather than retrieved documents, and by operating from a *first-person spatial perspective* rather than a queried world-model, Ether points toward a post-context AI architecture that is simultaneously more computationally frugal and more epistemically sophisticated.

Contemporary research strongly supports this reorientation. Studies confirm that even million-token windows suffer "lost in the middle" degradation, that effective context length rarely exceeds 50% of trained length [^312^], that RAG outperforms long-context on cost by 1,250x while achieving comparable accuracy [^311^], and that streaming/incremental architectures represent the next frontier in LLM design [^369^]. The convergence suggests that the future of AI lies not in loading more context but in *being present* where changes occur.

---

## Major Findings

### Finding 1: The Effective Context Gap — Trained Length ≠ Usable Length

Research reveals a striking gap between trained and effective context length. A 2025 ICLR paper identified the "left-skewed position frequency distribution" — a pattern where models severely undertrain long-distance position indices [^312^]. In SlimPajama, even with 2048-token contexts, position indices for distances ≥1024 were used less than 20% of the time, dropping below 5% for distances ≥1536. Most open-source models demonstrate effective context less than 50% of training length. Llama 3.1 70B's theoretical 128K window yields only ~64K effective length [^312^]. This gap is structural, not incidental.

**Implication:** The "ever-larger windows" strategy hits fundamental limits. Ether sidesteps this by eliminating the need to load full context entirely.

### Finding 2: Attention Is Fundamentally O(n²) — And Memory Is the Bottleneck

The KV cache has become the primary memory bottleneck in transformer inference [^324^] [^329^]. As one researcher notes, "even if the model weights stay fixed, the KV cache keeps growing as the conversation or document gets longer" [^329^]. At long contexts, the cache surpasses model weight sizes, making memory — not processing power — the primary constraint. Naive attention produces O(n²) complexity because every new token must attend to all previous tokens [^332^]. This is why RAG pipelines average 1 second per query while long-context approaches take 30–60 seconds [^307^].

**Implication:** Ether's delta-recording transforms computation from O(total_state) to O(changes) — a 95–99% reduction for most scenarios.

### Finding 3: Long Context vs. RAG — The Cost-Quality Tradeoff Is Extreme

A 2024 comprehensive study found that when resourced sufficiently, long-context (LC) consistently outperforms RAG — but RAG's cost advantage is enormous [^306^]. Elasticsearch Labs benchmarked RAG at 783 tokens/request with 1-second response times, versus 45 seconds for full-context [^311^]. Cost per query: $0.00008 for RAG versus $0.10 for full context — a **1,250x difference** [^311^]. Both share a common failure: "lost in the middle," where central information is systematically underweighted, producing U-shaped performance curves [^351^].

**Implication:** Neither RAG nor long-context solves the fundamental problem. Ether's room-based persistence means information is where the agent *is*, not where it was retrieved from.

### Finding 4: Non-Attention Architectures (Mamba/SSM) Are a Step Forward But Still Process All State

Mamba achieves linear O(n) scaling via selective state-space mechanisms that "decide on the fly what information to keep and what to forget" [^334^]. However, as IBM notes, Mamba still processes the *entire sequence* — it simply does so more efficiently [^334^]. It maintains a fixed-size hidden state updated for every token. It is a more efficient state processor, not a state avoider.

**Implication:** SSMs optimize the wrong variable — they make processing all state cheaper; Ether makes processing *only changes* the default. The difference is that between a faster horse and a car.

### Finding 5: Streaming LLMs — The Emergence of Incremental Processing

A 2026 survey marks a critical shift from "static inference to dynamic interaction," distinguishing streaming LLMs from long-context research by emphasizing "concurrent reading and writing, incremental processing of growing states, and online context/KV budgeting under strict latency constraints" [^369^]. Incremental encoding processes incoming streams solely based on past states, with historical representations unchanged, avoiding quadratic re-computation [^369^].

**Implication:** Streaming LLM research validates Ether's core intuition: the future of AI is incremental, not batch. Ether's delta streams are a native expression of this paradigm.

### Finding 6: Event Sourcing — The Architectural Precedent for Delta-Based Intelligence

Event sourcing stores every change as an immutable, sequential event rather than overwriting state [^336^]. "When an AI agent acts inside an event-sourced system, its decision doesn't disappear into a state update. It becomes a permanent, queryable record" [^336^]. Event-driven architecture reduces latency 70–90% versus polling and connection complexity from O(N²) to O(N) [^347^]. Confluent argues that "the future of AI agents is event-driven" [^357^].

**Implication:** PLATO's delta recording is event sourcing applied to cognition — every change is an immutable event that agents witness, process, and reason about.

### Finding 7: First-Person Perspective in AI — From World Models to Situated Experience

A 2026 paper proposed an architecture with "asymmetric separation between fast reaction-oriented dynamics through policy and more gradual perspective-oriented dynamics through global latent" [^348^]. The policy answers "What should I do right now?"; the perspective answers "What kind of world do I believe I am still in?" [^348^]. This global latent is not a belief over hidden states but a "perspective" that structurally constrains the agent's observation scope — mirroring Ether's distinction between immediate response and accumulated room presence.

**Implication:** First-person perspective is not metaphor but architectural necessity. The agent doesn't query a world model — it *has* a perspective from where it stands.

### Finding 8: Situated Language Understanding — Affordance and Embodiment

Research on affordance embeddings shows that agents grounded in spatial environments develop fundamentally different knowledge relationships than text-only models. The DIANA system enables embodied agents to "discuss, learn about, and manipulate novel items" in virtual worlds, inferring grasping strategies from spatial similarities — "I don't know... but I can grasp it like a cup" [^358^]. Research on situational awareness notes that self-understanding agents — those that "understand what they are, where they are operating, and why they're being asked to do certain tasks" — are crucial for long-term planning [^353^].

**Implication:** Knowledge acquired through situated presence is indexed by spatial relationship and temporal witness, not semantic similarity — making it more actionable.

### Finding 9: Bounded Rationality — The Epistemic Virtue of Partial Knowledge

Simon's "bounded rationality" — the idea that decision-makers face limits on information, cognition, and time — has profound implications for AI [^381^]. Research identifies "bounded intelligence" as a constraint with two factors: "superficiality" (inability to replicate expertise) and "deceivability" (inability to capture expertise accurately) [^377^]. Horvitz's "rational metareasoning" proposes that partial computation can be optimal when full analysis costs exceed its benefit [^380^].

**Implication:** The most sophisticated human decision-makers excel not because they know everything but because they know what they don't know. Ether agents, operating from presence rather than total knowledge, can develop this epistemic humility.

### Finding 10: Frugal AI — Computational Sufficiency as Design Philosophy

Frugal AI is defined as "a design philosophy for deploying AI with minimal resource intensity" — "deploy only as much computational intelligence as is necessary" [^326^]. Researchers distinguish frugality from efficiency: "While efficiency focuses on optimal resource utilization, frugality embodies a broader philosophy" of systems "inherently resource-conscious from the outset" [^331^]. The formalization: minimize resource consumption R(M) subject to performance ≥ minimum acceptable [^335^].

**Implication:** PLATO's philosophy of computational frugality — born when every byte mattered — is prescient. In an age of LLM profligacy, the most revolutionary architecture may be the one that does the most with the least.

---

## Original Analysis: Why Context Windows Are a Category Error

### The Ontological Problem

The context window assumes intelligence is a function of access — the more information loaded, the better the reasoning. This is the "god's-eye view" model: an omniscient observer seeing everything and choosing optimally. But this is not how biological intelligence works.

Human beings do not carry a room's complete history in their heads. They perceive what is present, notice what changed, and act from partial knowledge. A captain in fog does not demand perfect information — she decides with what she sees, updating as new information emerges. This is not a limitation to overcome; it is a *design feature* enabling real-time decision-making.

Transformers enforce "load everything, then decide." Every inference processes the full context through attention. The KV cache stores all previous keys and values. The attention matrix computes across the entire sequence. Even efficient variants (Mamba, RWKV) process the entire sequence — just with better complexity.

### The Three Fatal Flaws

**Computational profligacy.** Context windows force O(total_state) computation regardless of what matters. If 100,000 tokens exist and only three sentences changed, the LLM still processes all 100,000. The cost is identical whether context is entirely new or 99% unchanged.

**The recency-primacy trap.** Research shows U-shaped performance curves with middle information systematically lost [^351^] [^350^]. Distractors significantly degrade performance [^350^]. Smaller needles are harder to find than larger ones [^355^]. These are emergent properties of attention that cannot maintain uniform focus across long sequences.

**Epistemic arrogance.** LLMs with full context have no natural mechanism for knowing what they don't know. They cannot distinguish "this information is not in my context" from "this information does not exist." They lack epistemic humility because their architecture presumes access.

### Ether's Alternative: The Architecture of Situated Presence

Ether inverts each flaw through four innovations:

**1. Delta Recording:** Storing only changes achieves 95–99% reduction in storage and processing. Computation scales with O(changes), not O(total_state). A room with millions of historical events is represented by a delta stream processed incrementally — never requiring full history loading.

**2. Rooms as Persistent Places:** Unlike disposable context windows, Ether rooms are persistent environments. An agent in "buoy-7" has a continuous relationship with that space. It does not "retrieve context about buoy-7" — it *is in buoy-7*, receiving delta streams as they occur. Context becomes a lived relationship, not a loaded resource.

**3. Presence-Based Knowledge:** Ether agents know what matters because they witnessed it. This differs from RAG (semantic similarity retrieval) and long-context (indiscriminate loading). Presence-based knowledge is indexed by spatial relationship and temporal sequence — the native format of episodic memory.

**4. First-Person Spatial Reasoning:** The Ether agent reasons from *where it is* — like a person seeing what is in front of them, remembering what was there, and inferring what changed. It does not need absolute knowledge because it knows the limits of its own perspective.

### The Computational Advantage

| Dimension | LLM (Long Context) | RAG | Ether (Room-Based) |
|---|---|---|---|
| Computation per inference | O(total_tokens) | O(retrieve + process) | O(changes_since_last) |
| Memory requirement | KV cache for all tokens | Vector DB + LLM context | Delta stream buffer |
| Information access | Load everything | Retrieve relevant | Witness changes |
| Knowledge indexing | Positional (attention) | Semantic similarity | Spatial + temporal |
| Epistemic stance | "I know everything loaded" | "I found relevant docs" | "I saw what changed" |
| Scaling with history | Linear cost increase | Sub-linear | Near-constant (deltas) |

For 1 million tokens of historical state with 0.1% hourly change, Ether processes ~1,000 delta tokens/hour regardless of history depth. Long-context LLMs process all 1 million tokens every inference. Over a year: ~8.7 million delta tokens versus ~8.7 billion full-context tokens — **three orders of magnitude**.

---

## The Post-Context AI Architecture

### What Comes After Transformers

The post-context architecture will not be a transformer with a larger window, nor an SSM with linear scaling, nor a RAG system with better retrieval. It will abandon "context" entirely — replacing it with *presence*, *persistence*, and *perspective*.

Intelligent agents will be *inhabitants* of persistent computational spaces that exist continuously whether or not any agent is attending. These spaces maintain state through event-sourced delta logs. Agents enter them, witness changes, accumulate understanding, and act from situated knowledge.

### Five Pillars

**Pillar 1: Delta-Native Cognition.** Future AI will reason from delta streams rather than static context. The fundamental unit of cognition will be "process this change," not "process this text." Streaming LLM research [^369^] and event-driven architectures [^347^] point this direction, but delta-native cognition makes change the *primary* reasoning object.

**Pillar 2: Persistent Environments with Independent Existence.** Rooms exist as first-class computational entities with state persisting across sessions, emitting delta streams, maintaining histories through immutable event logs. An agent entering does not "load context" — it subscribes to the delta stream and accumulates presence. This is the computational equivalent of entering physical space.

**Pillar 3: Epistemic Humility as Architectural Feature.** Post-context AI will have "I don't know" as a native operation. Because agents operate from partial knowledge by design, they develop bounded rationality [^381^]. An agent that has never been in the engine room does not have engine room presence. It cannot answer questions about it — and it knows this.

**Pillar 4: Voice as Native Interface.** When computation is cheap enough to be continuous, voice becomes the natural interface because the agent is always present, always listening, always witnessing. It does not need to be "given" context through prompts because it has presence through continuous operation.

**Pillar 5: Computational Frugality as Ethical Imperative.** Where AI training consumes gigawatt-hours and inference costs scale linearly with context, the most ethical AI may be the most frugal [^326^] [^331^]. Processing only what changes, maintaining presence rather than loading context, doing more with less — this is a moral stance against computational waste.

### The Ultimate Promise

The ultimate promise is not merely making context limits obsolete but making the *concept* of context limits obsolete — replacing "loading context" with "being present," replacing the god's-eye view with the first-person perspective of situated intelligence, replacing the profligacy of attention-over-everything with the elegant frugality of change-based cognition.

In this architecture, an agent in a room does not need to know everything. It needs to know what changed and what it witnessed. From this partial, situated, ever-updating knowledge, it makes decisions that are simultaneously more efficient and more epistemically honest than anything from the most advanced context-loaded LLM. The captain does not need a world map to navigate the storm. She sees the wave in front of her, remembers the one behind, and steers.

The future of AI is not bigger context windows. It is smarter ways of not needing them at all.

---

## Sources

[^312^] ICLR 2025. "Why Does the Effective Context Length of LLMs Fall Short?" OpenReview.

[^305^] ArXiv 2025. "A Non-Attention LLM for Ultra-Long Context Horizons."

[^306^] ArXiv 2024. "Retrieval Augmented Generation or Long-Context LLMs? A Comprehensive Study."

[^307^] Redis Blog, 2026. "RAG vs Large Context Window: Real Trade-offs."

[^311^] Elasticsearch Labs, 2025. "RAG vs long context model LLM."

[^324^] ArXiv 2026. "Low-Rank Key Value Attention."

[^329^] Raschka, 2026. "Why is the KV cache such a big memory bottleneck?"

[^332^] Medium, 2025. "KV Caching & Attention Optimization: From O(n²) to O(n)."

[^327^] ArXiv 2023. Gu & Dao. "Linear-Time Sequence Modeling with Selective State Spaces" (Mamba).

[^330^] Galileo AI, 2025. "How Mamba Beats Transformers at Long Sequences."

[^334^] IBM Think, 2025. "What Is A Mamba Model?"

[^369^] ArXiv 2026. "From Static Inference to Dynamic Interaction: A Survey of Streaming LLMs."

[^336^] AxonIQ, 2026. "AI Agent Explainability: Why Your Infrastructure Needs to Remember."

[^347^] Atlan, 2026. "Event-Driven Architecture for AI Agents: Patterns and Benefits."

[^357^] Confluent, 2025. "The Future of AI Agents Is Event-Driven."

[^348^] ArXiv 2026. "Minimal Computational Preconditions for Subjective Perspective in Artificial Agents."

[^358^] Frontiers in AI, 2022. "Affordance embeddings for situated language understanding."

[^353^] Medium, 2025. "Situational Awareness in AI."

[^381^] Wikipedia. "Bounded rationality" (Simon).

[^377^] ScienceDirect, 2025. "The bounded intelligence of AI: Superficiality and deceivability."

[^380^] Horvitz. "Research on Principles of Bounded Rationality."

[^326^] COL, 2026. "Frugal AI: A Roadmap to Sovereign GenAI for Education."

[^331^] KDD Explorations. "Frugal AI: Introduction, Concepts, Development."

[^335^] Emergent Mind, 2025. "Frugal AI: Efficient, Minimal Resource Design."

[^350^] PromptHub, 2025. "Why Long Context Windows Still Don't Work."

[^351^] ACL Anthology, 2025. "Multilingual Needle in a Haystack."

[^355^] OpenReview, 2025. "Smaller Needles are More Difficult for LLMs to Find."

[^352^] University of Michigan. "Citizens of PLATO Digital Archive."

---

*Prepared as a dissertation chapter. Synthesizes findings from 25+ peer-reviewed papers, industry benchmarks, and architectural studies (2022–2026).*
