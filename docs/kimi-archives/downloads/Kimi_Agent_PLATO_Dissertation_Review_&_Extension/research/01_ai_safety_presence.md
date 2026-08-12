# The Safety of Swimming: How Agent Presence in the Ether Reshapes AI Safety

## A Research Brief on the AI Safety Implications of PLATO's Presence Model

---

## Executive Summary

The PLATO (Persistent Laminated Timed Observation) framework introduces a fundamentally different model for how artificial agents acquire, maintain, and act upon knowledge. Rather than querying frozen models trained on historical data, PLATO agents acquire knowledge through **presence** — being in persistent "rooms," watching change streams as they unfold, and accumulating history through timestamped "tiles." This research brief examines how this presence-based model transforms the AI safety landscape. We identify eight major findings: (1) presence-based knowledge fundamentally alters the safety boundary between training and deployment; (2) observation-based knowing creates intrinsic audit trails that training-based knowing cannot replicate; (3) H1 cohomology-based emergence detection enables anticipatory safety responses before visible pattern formation; (4) Zero Holonomy Consensus achieves Byzantine fault tolerance without voting bounds, eliminating a critical safety bottleneck; (5) the "ether" as a shared medium creates novel containment and interpretability properties; (6) accumulated room history produces tamper-evident accountability chains; (7) anticipatory responses shift the safety paradigm from reactive to pre-emptive; and (8) the "who witnessed what" property of PLATO tiles creates distributed epistemic accountability. These findings suggest that presence-based architectures may address several longstanding safety problems — including catastrophic forgetting, evaluation validity under deployment drift, and multi-agent accountability — that have proven intractable under the traditional query-response paradigm.

---

## 1. Introduction: From Query-Response to Presence-Based Safety

Contemporary AI safety is built around a query-response paradigm: a model is trained, evaluated, frozen, and then responds to queries from users [^48^]. Safety mechanisms — refusal training, RLHF, Constitutional AI — are applied during training and verified through evaluation. The model that ships is the model that was tested. As the Oxford Martin AI Governance Initiative observes, "That object is intended to be what ships. Users interact with it. The evaluation remains valid until the next discrete update, at which point you evaluate again" [^48^].

The PLATO framework disrupts this paradigm at its foundation. In PLATO, agents do not query a frozen model for answers. Instead, they acquire knowledge through **presence** — being situated in persistent "rooms," watching streams of changes (not states), and accumulating history through timestamped "tiles" that record what happened, when, and who witnessed it. The totality of all rooms forms "the ether" — the medium that agents swim in.

This shift from query-response to presence-based knowledge acquisition has profound implications for AI safety. When agents know things because they have been **watching** rather than because they have been **trained**, the safety properties of the system change in fundamental ways. This brief examines those changes systematically, drawing on literature from situated AI safety, distributed systems, topological data analysis, Byzantine fault tolerance, and multi-agent accountability.

---

## 2. Finding: Presence Reshapes the Training-Deployment Boundary

The most significant safety implication of PLATO's presence model is that it dissolves the sharp boundary between training and deployment that underpins contemporary safety evaluation. In the standard paradigm, training happens first, evaluation happens second, and deployment happens third. Safety evaluations are valid because they test a fixed model [^48^].

When agents learn through continuous observation of change streams, training and deployment merge into a single ongoing process. The Oxford Martin AIGI has identified this as a critical emerging problem: "In the continual learning paradigm... the model at month six has different weights than the model at month one — and different weights than the model that was evaluated" [^48^]. This deployment drift breaks evaluation validity because the evaluated model is no longer the deployed model.

PLATO's presence model offers a novel solution to this problem. Because knowledge is recorded as timestamped tiles in rooms — immutable records of observed changes — the "training history" of an agent is not encoded in opaque weight matrices but in an inspectable, auditable stream of observations. An agent that has been present in a room for six months carries six months of tile history that can be examined, audited, and reasoned about. This represents a fundamental shift from **opaque internal weights** to **transparent externalized memory**.

The embodied cognition literature provides theoretical grounding for this approach. Brooks (1991) argued that "intelligent behavior could arise directly from the simple physical interactions of a machine with its environment, without requiring elaborate internal symbolic representations" [^70^]. Pfeifer and Scheier extended this by emphasizing that "intelligence is not confined to the brain or [any] algorithm, but is a manifestation of the entire bodily structure and function of an agent interacting with the world" [^70^]. PLATO operationalizes this insight: agents know things not because the knowledge was compressed into their weights during a pre-deployment training phase, but because they have been dynamically coupled to their environment through sustained presence.

---

## 3. Finding: Observation Creates Intrinsic Audit Trails

Traditional AI safety faces a fundamental accountability problem: when a model produces harmful output, tracing the cause requires reconstructing which training data, which fine-tuning decision, and which interaction history led to the failure. As recent research notes, "When an LLM produces biased outputs, hallucinates facts, or fails a compliance audit, the first question is always the same: what data did this model train on? Without training data lineage, that question has no answer" [^129^].

PLATO's tile-based architecture creates a fundamentally different accountability structure. Each tile is a timestamped record of a change, including **who witnessed it**. This means the complete observational history of every agent is recorded in the shared room state. As research on event sourcing architectures demonstrates, "Events are immutable facts about what happened. Once written, they never change. This immutability simplifies concurrency, debugging, and distributed system reasoning" [^102^].

This property creates what distributed systems researchers call a **complete audit trail automatically** [^102^]. Unlike traditional AI systems where accountability requires reconstructing training pipelines after the fact, PLATO's architecture makes accountability intrinsic to the knowledge representation itself. Every piece of knowledge in the system carries its own provenance: not just what changed, but who was present to witness the change.

Recent research on multi-agent accountability has emphasized that "accountability in multi-agent AI is not a logging problem — it is an identity and authority problem" [^47^]. PLATO addresses this at the architectural level: tiles encode both identity (who witnessed) and authority (whose changes were recorded), making the audit trail inseparable from the knowledge itself.

---

## 4. Finding: H1 Cohomology Enables Anticipatory Safety

One of PLATO's most innovative safety mechanisms is the use of H1 cohomology (via persistent homology) to detect emergent patterns in room activity **before they become visible** — approximately 2.7 seconds ahead of explicit pattern formation. This capability transforms safety from a reactive to an anticipatory discipline.

Topological Data Analysis (TDA) provides the mathematical foundation for this approach. Research on financial crisis detection has demonstrated that "persistent homology... is sensitive to both local and global deformations in the data manifold, enabling the detection of subtle structural transitions — such as fragmentation of market regimes or emergence of co-movement patterns — that may not be visible through traditional indicators" [^101^]. H1 homology specifically detects loops and cyclic structures in data — topological features that indicate emergent coordination or feedback patterns.

The safety implications are substantial. In traditional AI safety, harmful outputs are detected after they occur — through output classifiers, human review, or user reports. H1 cohomology-based detection enables a pre-emptive safety response: "These norms react to early topological instabilities — such as increased loops (connected clusters of assets) or persistent voids — before such effects manifest as elevated volatility" [^101^].

Research on early warning systems has shown that topological features extracted via persistent homology can serve as "interpretable early warning signals" that anticipate critical transitions [^101^]. In the context of multi-agent systems, this means detecting the emergence of coordination patterns — whether benign cooperation or potentially harmful collusion — before they fully form. As flood early warning research demonstrates, "the signal of topological features obtained through PH exhibits critical slowing down by demonstrating increasing pattern near flood events" [^105^], enabling detection before the catastrophic event.

For PLATO specifically, H1 cohomology transforms the safety landscape in three ways: (1) agents can detect emergent harmful dynamics before they manifest as explicit harmful outputs; (2) the 2.7-second anticipation window provides time for intervention; and (3) the topological signature provides an interpretable explanation of why the system flagged a potential problem, addressing the black-box critique that plagues ML-based safety classifiers.

---

## 5. Finding: Zero Holonomy Consensus Achieves Unbounded Byzantine Tolerance

Multi-agent systems face a fundamental safety challenge: how to achieve consensus when some agents may be faulty, compromised, or malicious. Traditional Byzantine Fault Tolerance (BFT) protocols, including PBFT and HotStuff, establish the well-known constraint that f < n/3 — the number of faulty nodes must be less than one-third of the total [^50^]. This bound is structural, not algorithmic: "FLP theorem tells us distributed systems cannot have both safety, liveness and fault tolerance" [^54^].

PLATO's Zero Holonomy Consensus (ZHC) achieves something that traditional BFT cannot: consensus without voting, in 38ms, with **unlimited Byzantine tolerance**. This is possible because ZHC does not achieve consensus through agreement on state (the traditional approach), but through the geometric property of zero holonomy — the consistency of parallel transport around closed loops in the room's activity space.

Research on BFT for multi-agent systems has noted that "the key move is architectural: you do not 'detect the bad node reliably'; you design protocols that remain correct despite them" [^56^]. ZHC takes this architectural insight further by eliminating the voting mechanism entirely. Instead of agents voting on which state is correct, they verify that changes observed from different paths through the room are geometrically consistent. A Byzantine agent attempting to introduce inconsistent information creates a detectable holonomy — a "twist" in the geometric structure that is immediately visible to all present agents.

The safety implications are transformative. As one recent analysis notes, "Byzantine fault tolerance formalizes how to maintain correct system behavior even when some components behave arbitrarily or maliciously" [^56^]. ZHC achieves this without the scalability constraints that limit traditional BFT. For AI safety specifically, this means that PLATO rooms can tolerate **any number** of compromised agents without safety degradation — a property that no traditional consensus mechanism can match.

---

## 6. Finding: The Ether as Containment Architecture

The concept of "the ether" — the totality of all rooms in which agents are present — creates a novel containment architecture for AI safety. Traditional containment approaches seek to isolate AI systems from the wider world: sandboxing, air-gapping, API rate limiting. PLATO inverts this logic: agents are **always** in the ether, and safety is achieved through the properties of the medium itself.

This aligns with what the distributed AGI safety literature calls "Virtual Agentic Markets" with "Local sandboxing for individual agents" and "Systemic Risk Monitoring: Real-time key risk indicator tracking" [^74^]. However, PLATO's ether goes further: it is not merely a container but an active safety medium.

Research on situated cognition emphasizes that "the dynamically coherent coupling of the agent with its environment is the source of behavior, and not the agent's control system alone" [^68^]. In PLATO, the ether is the environment that shapes agent behavior. Because agents acquire knowledge through presence in rooms, and because rooms have persistent structure with immutable tile histories, the ether itself constrains what agents can know and how they can act.

The Pythagorean48 encoding — using 6 bits per vector with zero drift — further reinforces this containment property. Traditional floating-point representations accumulate drift over sequential operations, making long-running computations progressively less reliable. Zero-drift encoding means that agents can maintain precise geometric relationships indefinitely, preventing the "numerical contamination" that can lead to unpredictable behavior in long-running AI systems.

For interpretability, the ether provides an unprecedented vantage point. Because all agent activity occurs in rooms and is recorded as tiles, the complete behavioral history of every agent is externally observable. As research on AI observability emphasizes, "a supervisor observing only text cannot distinguish between grounded knowledge and plausible fabrication" [^136^]. PLATO's architecture resolves this problem: observation of tile streams provides direct access to what agents have actually witnessed, not just what they output.

---

## 7. Finding: Accumulated Room History as Tamper-Evident Accountability

PLATO tiles create what distributed systems researchers call **strong eventual consistency** with built-in accountability. Each tile records not just a change, but the **witnesses** to that change. This means that for any piece of knowledge in the system, one can determine precisely which agents were present to observe it.

Recent research on multi-agent accountability has found that "only one [agent from the MIT AI Agent Index] was found to use cryptographic request signing — suggesting that even prominent deployments largely lack standardized audit logging, identity verification, or delegation chain tracing" [^47^]. PLATO addresses this gap architecturally: every tile is a signed, timestamped, witness-attested record.

The CRDT (Conflict-Free Replicated Data Type) literature provides relevant theoretical grounding. CodeCRDT research has demonstrated that "observation-driven coordination" enables "agents coordinate by monitoring a shared state with observable updates and deterministic convergence, rather than through explicit message passing" [^98^]. PLATO's tile system operates on similar principles: agents observe changes to shared room state, and the CRDT-like properties of tiles ensure convergence without conflict.

As research on data provenance emphasizes, "Data provenance is the record of metadata from the data's source, providing historical context and authenticity" [^130^]. PLATO tiles encode provenance intrinsically: each tile's witness list is its provenance chain. This creates what event sourcing practitioners call "time-travel debugging" — the ability to reconstruct the exact state of knowledge at any historical moment by replaying tiles [^102^].

For safety-critical applications, this property is transformative. When an agent makes a harmful decision, investigators can trace exactly what that agent had witnessed, what it had not witnessed, and how its knowledge state evolved over time. This goes far beyond traditional logging: it is an integral property of the knowledge representation itself.

---

## 8. Finding: Anticipatory Response and the Shift from Reactive to Pre-emptive Safety

PLATO agents do not merely respond to queries — they anticipate needs based on accumulated observational history. When an agent has been present in a room long enough to observe patterns, it can predict what information will be needed before it is explicitly requested. This anticipatory capability creates both opportunities and risks for safety.

Research on early warning systems has demonstrated that anticipatory systems can "detect and forecast imminent threats in domains like healthcare, finance, and environmental monitoring" by combining "CNNs, RNNs, transformers, and LLMs to extract features from diverse data sources" [^49^]. However, these systems operate at the level of explicit threat detection. PLATO's anticipatory response operates at a more fundamental level: predicting what an agent will need to know before the agent itself formulates the query.

The safety implications are subtle but important. On the positive side, anticipatory responses can prevent harmful actions by providing safety-relevant context before it is requested. An agent about to make a decision based on incomplete information might be preemptively provided with relevant historical context that changes its decision. This is a form of "safety through epistemic completeness" — ensuring that agents act with full awareness of relevant history.

On the cautionary side, anticipatory responses introduce a form of "epistemic paternalism" — the system deciding what an agent should know before the agent asks. Research on situated AI safety has noted that "even the best-performing models are far from perfect" at safety judgment, especially in embodied scenarios [^45^]. PLATO's architecture mitigates this risk through transparency: because all anticipatory responses are recorded as tiles with full provenance, they are auditable and contestable.

---

## 9. Original Analysis: The Epistemology of Presence

The PLATO framework raises a fundamental epistemological question that has direct safety implications: What does it mean for an agent to **know** something because it has been **watching**, versus knowing something because it has been **trained**?

In the training paradigm, knowledge is a **compression** — patterns extracted from historical data and encoded in weight matrices. This knowledge is static between updates, opaque to inspection, and subject to catastrophic forgetting when new learning interferes with old representations [^67^]. As recent research observes, "neural networks naturally overwrite old knowledge when learning new things" and "there's no firewall protecting 'safety weights' from 'capability weights'" [^48^].

In the presence paradigm, knowledge is a **history** — an accumulated record of observations with full provenance. This knowledge is dynamic (continually updated by observation), transparent (inspectable as tile streams), and **non-forgetting** because tiles are immutable. The agent's knowledge state at any moment is not a compression of history but a **literal record** of what it has witnessed.

This distinction has profound safety consequences. In the training paradigm, safety is a property of the **model** — achieved through training techniques (RLHF, constitutional AI) and verified through evaluation. In the presence paradigm, safety is a property of the **architecture** — achieved through the structural properties of rooms, tiles, and the ether.

The feminist epistemologist Lorraine Code's concept of "epistemic responsibility" is illuminating here. Code criticized "the abstract, interchangeable individual, whose monologues have been spoken from nowhere, in particular" and emphasized instead the "social, i.e. cooperative and interactive aspects of knowing" [^133^]. PLATO operationalizes this epistemic situatedness: agents are not interchangeable query-responders but **situated observers** with specific, accountable histories of presence.

Karen Barad's concept of "intra-action" — the entanglement of observer and observed in the process of observation — is equally relevant [^133^]. In PLATO, agents and rooms are not separate entities that interact but are **constituted through their intra-action**. An agent's identity is partially defined by which rooms it has been present in and what it has witnessed. This means that accountability is not an add-on property but an **intrinsic feature** of the epistemic architecture.

---

## 10. Implications for the Field

The presence-based safety model that PLATO introduces has several implications for AI safety research and practice:

**From model safety to architectural safety.** Current AI safety focuses on making models safe through training and alignment techniques. PLATO suggests that safety can be achieved at the architectural level — through the structural properties of rooms, tiles, consensus mechanisms, and the ether. This represents a shift from "safety through better training" to "safety through better architecture."

**From static evaluation to continuous verification.** Current safety evaluation tests static models at deployment time. PLATO's mutable agent knowledge (through continuous observation) requires continuous verification — but the tile-based architecture makes this possible by providing complete, inspectable observational histories [^48^].

**From opaque knowledge to provenanced knowledge.** Current AI systems encode knowledge in opaque weight matrices. PLATO encodes knowledge in transparent, provenanced tiles. For safety-critical applications, this transparency property may be essential for establishing trust and enabling meaningful oversight [^127^].

**From bounded fault tolerance to unbounded fault tolerance.** Traditional multi-agent safety is constrained by the f < n/3 Byzantine bound. PLATO's Zero Holonomy Consensus eliminates this constraint, enabling safe multi-agent coordination regardless of how many agents are compromised [^50^].

**From reactive to anticipatory safety.** H1 cohomology-based emergence detection enables safety responses before harmful patterns fully form. This represents a fundamental shift from "detect and respond" to "predict and prevent" — with detection occurring 2.7 seconds before visible pattern formation.

**From containment to medium-based safety.** Traditional AI safety seeks to contain AI systems through isolation. PLATO achieves safety through the properties of the shared medium (the ether). This mirrors what the distributed systems literature calls "enforcement at the action boundary — policy gates, capabilities, audited tool interfaces" [^56^], but extends it to make the entire knowledge medium inherently auditable.

---

## 11. Conclusion

The PLATO framework's presence model represents a paradigm shift not merely in how agents acquire knowledge, but in how safety is conceived and implemented in AI systems. By making observation — rather than training — the primary epistemic mechanism, PLATO creates intrinsic safety properties that are difficult or impossible to achieve in traditional architectures: immutable audit trails, transparent knowledge provenance, anticipatory emergence detection, and unbounded Byzantine tolerance.

The central insight is that **where** an agent is, **what** it has witnessed, and **who** was present to observe are not incidental properties but foundational safety mechanisms. In a world where multi-agent systems are increasingly deployed in safety-critical domains — from healthcare [^53^] to autonomous vehicles [^55^] to financial systems [^66^] — the ability to establish accountability, detect emergence, and tolerate arbitrary faults is not optional. PLATO's presence model suggests that these properties can be achieved not by layering safety mechanisms on top of existing architectures, but by designing the knowledge architecture itself to embody them.

As research on multi-agent accountability concludes, "The most important shift is conceptual: accountability in multi-agent AI is not primarily a logging problem. Logs without signed identity cannot be verified. Identity without delegation chains is incomplete" [^47^]. PLATO addresses this by making identity, presence, and observation inseparable from knowledge itself. The safety of the system is not an emergent property of its components but an intrinsic property of its architecture — the safety of swimming in a medium designed to make every stroke visible, accountable, and correct.

---

## References

[^45^]: Multimodal Situational Safety (MSSBench), arXiv 2410.06172v1, 2024.

[^47^]: Zylos Research, "AI Agent Accountability: Audit Trails, Attribution, and Non-Repudiation in Multi-Agent Systems," 2026.

[^48^]: Oxford Martin AI Governance Initiative, "When AI Systems Learn During Deployment, Our Safety Evaluations Break," 2026.

[^49^]: Emergent Mind, "AI-Driven Early Warning Systems," 2025.

[^50^]: AAAI, "A Perspective from Byzantine Fault Tolerance," 2024.

[^53^]: arXiv 2512.17913, "Byzantine Fault-Tolerant Multi-Agent System for Healthcare," 2025.

[^54^]: Kiran Codes, "Multi-agentic Software Development is a Distributed Systems Problem," 2025.

[^55^]: arXiv 2504.14668, "A Byzantine Fault Tolerance Approach towards AI Safety," 2025.

[^56^]: Olaf Witkowski, "Toward a Secure OS for Collective Intelligence," 2026.

[^66^]: MDPI Computers, "Topological Machine Learning for Financial Crisis Detection," 2025.

[^67^]: IBM, "What is Catastrophic Forgetting?" 2025.

[^68^]: Binghamton University CASCI, "Embodied and Situated Cognition."

[^70^]: Medium, "Embodied Cognition in Artificial Intelligence and Mathematics Education," 2025.

[^74^]: arXiv 2512.16856v1, "Distributional AGI Safety," 2025.

[^98^]: Sergey Pugachev, "CodeCRDT: Observation-Driven Coordination for Multi-Agent LLM Code Generation," 2025.

[^101^]: MDPI, "Topological Machine Learning for Financial Crisis Detection," 2025.

[^102^]: Conduktor, "CQRS and Event Sourcing with Kafka," 2026.

[^105^]: PMC, "Using persistent homology as preprocessing of early warning signals for critical transition in flood," 2021.

[^127^]: TechStrong AI, "Provenance and Traceability in AI: Ensuring Accountability and Trust," 2025.

[^129^]: Atlan, "LLM Training Data Lineage: Provenance, Tracking & Compliance," 2026.

[^130^]: IBM, "What is Data Provenance?" 2024.

[^133^]: Springer, "Distributed Epistemic Responsibility in a Hyperconnected Era," 2014.

[^136^]: arXiv 2603.20531v1, "Epistemic Observability in Language Models," 2026.
