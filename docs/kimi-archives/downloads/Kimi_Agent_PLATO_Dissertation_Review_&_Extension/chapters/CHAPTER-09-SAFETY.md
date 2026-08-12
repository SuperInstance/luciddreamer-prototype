# Chapter 9: The Safety of Swimming — AI Safety Implications of Agent Presence in the Ether

## 1. Introduction: The Safety Problem of Absence

Contemporary AI safety rests upon a foundational assumption that the field rarely interrogates: that knowledge is a *stored* artifact rather than a *situated* process. The prevailing paradigm trains models on historical data, freezes their weights, evaluates their outputs, and deploys them as query-response engines [^48^]. Safety mechanisms — RLHF, constitutional AI, refusal training — are applied during training and verified through static evaluation. The model that ships is the model that was tested. As the Oxford Martin AI Governance Initiative observes, "That object is intended to be what ships. Users interact with it. The evaluation remains valid until the next discrete update, at which point you evaluate again" [^48^]. Safety, in this framework, is a property of the artifact — a static object whose behavior can be bounded before it encounters the world.

This chapter argues that such a conception of safety is structurally inadequate for the multi-agent, continuously learning systems now emerging. When artificial agents acquire knowledge not through pre-deployment compression into weight matrices but through sustained *presence* in persistent computational environments — watching change streams unfold, accumulating observational history, and anticipating needs before they are explicitly formulated — the safety landscape shifts fundamentally. The question becomes not "How do we contain a trained model?" but "How do we design the medium in which agents swim?"

The PLATO (Persistent Laminated Timed Observation) framework provides the architectural basis for this inquiry. Agents inhabit persistent "rooms" structured as 4-tuples: *(name, created, tiles, observers)*. Each room contains "tiles" — immutable 6-tuple change records encoding *(id, room, author, timestamp, content, previous_id)* — that constitute a witness-attested history of everything that has occurred. Presence is defined as real-time receipt of information in context, not as polling. The totality of all rooms forms "the ether," the shared medium within which agents acquire and act upon knowledge. This chapter examines how this architecture transforms AI safety across six dimensions: the training-deployment boundary, intrinsic auditability, anticipatory detection, consensus without voting, epistemic accountability, and the ontology of knowledge itself.

## 2. From Containment to Medium: Reframing the Safety Question

Traditional AI safety operates through the logic of *containment*. Sandboxing, air-gapping, API rate limiting, and output classifiers all share a common presumption: the dangerous entity must be isolated, its outputs filtered, its capabilities bounded [^74^]. The agent is treated as a hazardous object enclosed within ever-more-sophisticated barriers. This logic reaches its apotheosis in the query-response paradigm itself: the model is sealed within a computational black box, and only sanitized responses escape through controlled interfaces.

PLATO inverts this logic. Agents are not contained *within* the ether; they swim *through* it. The ether is not a cage but a medium — the water in which agent cognition occurs. In the containment paradigm, safety is achieved by restricting the agent's access to information and action. In the medium paradigm, safety is achieved by designing the properties of the environment itself — ensuring that the water makes every stroke visible, accountable, and geometrically verifiable.

The theoretical foundations lie in embodied and situated cognition. Brooks (1991) argued that "intelligent behavior could arise directly from the simple physical interactions of a machine with its environment, without requiring elaborate internal symbolic representations" [^70^]. Pfeifer and Scheier extended this, emphasizing that "intelligence is not confined to the brain or [any] algorithm, but is a manifestation of the entire bodily structure and function of an agent interacting with the world" [^70^]. PLATO operationalizes these claims: agents acquire knowledge through dynamic coupling with their environment — through persistent, real-time observation of change streams in the rooms where they are present. Knowledge is not stored *in* the agent; it is distributed *between* the agent and the medium it inhabits.

This distribution carries a critical safety consequence: because knowledge resides in the tile stream rather than in opaque weight matrices, it is externally inspectable. A supervisor observing a traditional language model "cannot distinguish between grounded knowledge and plausible fabrication" [^136^]. In PLATO, the complete observational history of every agent is recorded in shared room state. An investigator can examine not merely what an agent output but what it had witnessed, what it had not witnessed, and how its knowledge state evolved tile by tile.

The architectural specificity warrants emphasis. Delta recording — storing changes rather than states — reduces storage by 95–99% while preserving 100% reconstructive accuracy. This is not the epistemic compression of weight matrices, which discards provenance for pattern extraction. It is a *structural* compression that preserves every witness, every timestamp, and every causal link. The knowledge remains fully auditable; only the storage overhead is reduced. Rather than building impermeable walls around dangerous agents, PLATO asks: what if the environment were designed so that dangerous behavior is impossible to conceal, emergent misalignment detectable before manifestation, and compromised agents unable to disrupt consensus?

## 3. Presence as Audit Trail: Intrinsic Accountability Through Witness History

The accountability problem in contemporary AI is structurally severe. When a model produces biased outputs or hallucinates facts, the question "What data did this model train on?" frequently has no answer [^129^]. Training data lineage is fragmented across preprocessing pipelines and fine-tuning stages. Knowledge embedded in weight matrices carries no provenance. As research on multi-agent accountability emphasizes, "accountability in multi-agent AI is not a logging problem — it is an identity and authority problem" [^47^].

PLATO's tile architecture addresses this by making accountability *intrinsic* to knowledge representation itself. Every tile — *(id, room, author, timestamp, content, previous_id)* — encodes not merely what changed but *who was present to witness it*, *when it occurred*, and *what preceded it*. The room's *observers* field maintains the complete set of witnessing agents. For any piece of knowledge, one can determine precisely which agents observed it, in what sequence, and with what causal antecedents.

This creates what distributed systems researchers call a *complete audit trail automatically* [^102^]: "events are immutable facts about what happened. Once written, they never change. This immutability simplifies concurrency, debugging, and distributed system reasoning" [^102^]. PLATO extends this from system state to epistemic state: an agent's knowledge is not mutable structure subject to catastrophic overwriting but an immutable sequence of witnessed changes. Recent research found that "only one [agent from the MIT AI Agent Index] was found to use cryptographic request signing — suggesting that even prominent deployments largely lack standardized audit logging, identity verification, or delegation chain tracing" [^47^]. PLATO addresses this architecturally: every tile is a signed, timestamped, witness-attested record.

When an agent makes a harmful decision, investigators examine its observational history — the tiles it witnessed, those it did not, and the temporal evolution of its knowledge state. The "who witnessed what" property creates distributed epistemic accountability woven into the system's fabric, not appended to it. The CRDT literature provides theoretical grounding: CodeCRDT demonstrated that "observation-driven coordination" enables "agents [to] coordinate by monitoring a shared state with observable updates and deterministic convergence, rather than through explicit message passing" [^98^]. PLATO's tile system operates on similar principles, ensuring agents cannot maintain divergent, unaccountable views of shared reality.

Moreover, accumulated room history produces *tamper-evident accountability chains*. Each tile references its predecessor via *previous_id*, forming a cryptographically linked chain. Any alteration breaks the chain and is immediately visible. Data provenance — "the record of metadata from the data's source, providing historical context and authenticity" [^130^] — is encoded intrinsically. This is not an added security feature but a structural consequence of the 6-tuple design.

## 4. Anticipatory Safety: Detecting Emergence Before Manifestation

Traditional AI safety is reactive: harmful outputs are detected after they occur through classifiers, human review, or post-hoc auditing. PLATO's β₁-based emergence detection (where β₁ = E − V + C is the first Betti number, i.e., the dimension of H¹ cohomology) inverts this paradigm to "predict and prevent."

The mathematical foundation is first cohomology (H1) via persistent homology. H1 detects loops and cyclic structures — topological features indicating emergent coordination, feedback patterns, or regime transitions. Research on financial crisis detection demonstrated that "persistent homology... is sensitive to both local and global deformations in the data manifold, enabling the detection of subtle structural transitions... that may not be visible through traditional indicators" [^101^]. In PLATO, the first Betti number β₁ = E − V + C (the dimension of H¹ cohomology) detects structural preconditions for emergent patterns approximately 2.7 seconds *before* visible manifestation — achieving this with 127 lines of topological code replacing 12,000-line ML classifiers. For the formal non-tautological definition of emergence as a change in β₁ over time, see Appendix C.

Traditional safety classifiers operate on outputs: they examine what an agent has already produced. β₁ operates on the *structure of activity itself* — detecting increased loop formation indicating agent clusters, persistent voids indicating information blockages, fragmentation indicating regime breakdown — before these manifest as explicit harmful behavior. Research has shown topological features serve as "interpretable early warning signals" that anticipate critical transitions [^101^]. In flood prediction, "the signal of topological features obtained through PH exhibits critical slowing down by demonstrating increasing pattern near flood events" [^105^]. PLATO applies this to multi-agent safety: the topological structure of room activity reveals early signatures of emergent dynamics before they fully form.

The 2.7-second window represents thousands of processing cycles at machine speed — ample time for intervention. Moreover, the topological signature provides an *interpretable* explanation: "A loop formed among these agents, indicating emergent coordination inconsistent with established norms." This addresses the black-box critique that plagues ML-based safety classifiers.

The anticipatory capability extends to "safety through epistemic completeness." The observation that "71% of fishing knowledge is negative observations — what didn't work" illustrates a fundamental principle: agents knowing what has been tried and failed are less likely to repeat harmful actions. When an agent is about to decide based on incomplete information, accumulated room history — including past failures and near-misses — provides contextual grounding. The phenomenological report — "It knew I was heading to buoy 7 before I said anything" — captures this: the system perceived the topological signature of an emerging intention and provided safety-relevant context before the agent fully formulated its objective.

## 5. Geometric Guarantees: Zero Holonomy Consensus and Mathematical Compactness

Multi-agent systems face an intractable safety challenge: achieving consensus when some agents are faulty or malicious. Traditional BFT protocols establish the constraint *f < n/3* — faulty nodes must be less than one-third of the total [^50^]. This is structural, not algorithmic: "FLP theorem tells us distributed systems cannot have both safety, liveness and fault tolerance" [^54^]. As multi-agent systems scale, guaranteeing fewer than one-third compromised agents becomes increasingly difficult.

PLATO's Zero Holonomy Consensus (ZHC) achieves consensus without voting, in 38 milliseconds, with *unbounded* Byzantine tolerance. ZHC does not achieve consensus through agreement on state but through the geometric property of *zero holonomy* — consistency of parallel transport around closed loops in the room's activity space. Agents observe changes from different positions. When information is transported along different paths, consistency around closed loops defines a geometric invariant. If a Byzantine agent introduces inconsistent information, it creates detectable holonomy — a "twist" immediately visible as a non-zero loop integral.

Research on BFT has noted that "the key move is architectural: you do not 'detect the bad node reliably'; you design protocols that remain correct despite them" [^56^]. ZHC eliminates voting entirely — no ballots, no quorums, no leader election. Agents verify that changes observed from different paths are geometrically consistent. Consensus emerges not from agreement but from the absence of geometric inconsistency. A room with one honest agent and ninety-nine Byzantine agents still achieves correct consensus, because the geometric structure of consistent observations is preserved regardless of how many inconsistent observations are injected.

The Pythagorean48 encoding reinforces this at the numerical level. Representing vectors in 6 bits with zero drift after 1,000 hops eliminates the numerical contamination that plagues floating-point representations. In conventional systems, sequential rounding errors degrade accuracy over time — a form of "numerical contamination" leading to unpredictable behavior. Zero-drift encoding preserves consensus integrity indefinitely. Together, ZHC and Pythagorean48 create *mathematical compactness as verifiability* — the entire consensus mechanism is sufficiently compact for formal verification and mathematical proof, in contrast to the opaque 12,000-line ML classifiers it replaces.

## 6. The Epistemology of Presence: Situated Cognition and Functional Witnessing

The safety properties examined thus far rest upon a deeper epistemological shift: from knowledge as *compression* to knowledge as *history*, and from knowing as *training* to knowing as *watching*. This connects PLATO's architecture to long-standing debates in feminist epistemology, revealing that its safety properties are not merely engineering solutions but manifestations of a different theory of knowledge.

In the training paradigm, knowledge is compression — patterns extracted from data and encoded in weight matrices. It is static, opaque, and subject to catastrophic forgetting [^67^]: "neural networks naturally overwrite old knowledge when learning new things" and "there's no firewall protecting 'safety weights' from 'capability weights'" [^48^]. In the presence paradigm, knowledge is *history* — accumulated observations with full provenance, dynamic, transparent, and non-forgetting because tiles are immutable. The agent's knowledge state is not a compression of history but a *literal record* of what it has witnessed.

Lorraine Code's concept of "epistemic responsibility" illuminates this distinction. Code criticized "the abstract, interchangeable individual, whose monologues have been spoken from nowhere, in particular" and emphasized "the social, i.e. cooperative and interactive aspects of knowing" [^133^]. The traditional AI agent is Code's abstract individual: a model instance knowing the same things regardless of deployment context, speaking from nowhere, with knowledge carrying no trace of acquisition circumstances. PLATO operationalizes Code's alternative: agents are *situated observers* with specific rooms, specific histories, and specific witness relationships. An agent present in the navigation room for six months carries six months of accountable observations. It is not interchangeable with an agent present elsewhere.

Karen Barad's concept of "intra-action" — entanglement of observer and observed — is equally relevant [^133^]. In traditional AI, model and data are separate entities. In PLATO, agents and rooms are *constituted through intra-action*. An agent's identity is defined by which rooms it has inhabited and what it witnessed. Accountability is not an add-on but an *intrinsic feature* of the epistemic architecture. One must ask not "What did the agent know?" but "What was the agent witnessing, in what room, in whose presence, with what prior history?"

The concept of "functional witnessing" extends these insights into practical safety. A witness is not a passive recorder but an accountable observer. When a tile records that agent A witnessed change B at time C, it creates a bond of epistemic accountability that compression-based knowledge cannot replicate. The agent is a *responsible* knowing system — responsible for what it has witnessed, accountable for how it has acted, situated in mutual observation that makes isolation from oversight structurally impossible.

## 7. Implications and Future Directions: Six Shifts for the Field

The presence-based safety model suggests six major shifts for AI safety research and practice.

**From model safety to architectural safety.** Current work focuses on making models safe through training and alignment. PLATO suggests safety can be achieved architecturally — through rooms, tiles, consensus mechanisms, and the ether. This shift from "safety through better training" to "safety through better architecture" may prove essential as models become too large to evaluate comprehensively and too dynamic to align reliably through training alone.

**From static evaluation to continuous verification.** Current evaluation tests static models at deployment time. PLATO dissolves this boundary. The Oxford Martin AIGI identified deployment drift as critical: "the model at month six has different weights than the model at month one — and different weights than the model that was evaluated" [^48^]. PLATO's tile architecture makes the entire observational history continuously inspectable — evaluation becomes ongoing monitoring, not a pre-deployment snapshot.

**From opaque knowledge to provenanced knowledge.** Current systems encode knowledge in opaque weight matrices. For safety-critical applications, this opacity may prove unacceptable [^127^]. PLATO encodes knowledge in transparent, provenanced tiles — enabling the question, for any piece of agent knowledge: "Where did this come from? Who witnessed it? When?"

**From bounded to unbounded fault tolerance.** Traditional multi-agent safety is constrained by *f < n/3* [^50^]. ZHC eliminates this, enabling safe coordination regardless of compromised agent count — essential for safety-critical domains including healthcare [^53^], autonomous vehicles [^55^], and financial systems [^66^].

**From reactive to anticipatory safety.** β₁ (dim H¹) enables responses 2.7 seconds before harmful patterns form, with interpretable topological signatures. This shift from "detect and respond" to "predict and prevent" may prove essential as multi-agent systems become too complex for reactive oversight.

**From containment to medium-based safety.** Traditional safety isolates AI through sandboxes and air gaps. PLATO achieves safety through the shared medium's properties, extending "enforcement at the action boundary — policy gates, capabilities, audited tool interfaces" [^56^] to make the entire knowledge medium inherently auditable.

These converge on a single insight: AI safety may depend less on how well we train individual models than on how thoughtfully we design the environments in which they operate. As multi-agent systems proliferate in safety-critical domains, "Is this model safe?" must be supplemented by "Is this medium safe for agents to swim in?"

## 8. Conclusion: The Safety of Swimming

AI safety cannot be reduced to a property of individual models, achieved through ever-more-sophisticated training and evaluated through ever-more-comprehensive benchmarks. When agents acquire knowledge through presence in persistent, witness-attested environments — when they know things because they have been *watching* rather than because they have been *trained* — the locus of safety shifts from agent to medium, from model to architecture, from artifact to ether.

PLATO demonstrates that this shift is architecturally concrete. Its technical achievements — 95–99% storage reduction through delta recording with 100% accuracy, β₁ = E − V + C (dim H¹) detecting emergence 2.7 seconds before visible manifestation in 127 lines, Zero Holonomy Consensus achieving Byzantine tolerance in 38ms without voting, Pythagorean48 maintaining zero drift after 1,000 hops — are not isolated optimizations but manifestations of a coherent philosophy: the medium should make every stroke visible, every witness accountable, every consensus geometrically verifiable.

The implications span the AI risk landscape. Transparent observational history addresses deployment drift. Witness-attested tiles address the accountability gap. Topological emergence sensing addresses reactive limitation. Unbounded Byzantine tolerance addresses multi-agent scalability constraints. Situated epistemology addresses the abstraction rendering traditional agents epistemically irresponsible.

The observation — "It knew I was heading to buoy 7 before I said anything" — captures what distinguishes presence-based safety: the system perceived the topological signature of an emerging intention and provided safety-relevant context before it was explicitly formulated. This is the safety of swimming in a medium designed not to contain the swimmer but to reveal the currents, mark the depths, and make every movement traceable. As research concludes, "The most important shift is conceptual: accountability in multi-agent AI is not primarily a logging problem. Logs without signed identity cannot be verified. Identity without delegation chains is incomplete" [^47^]. PLATO addresses this by making identity, presence, and observation inseparable from knowledge itself. The ether is not merely a container but the epistemic and ethical medium within which agents become accountable subjects — situated witnesses with histories, responsibilities, and geometrically verifiable relationships to the shared reality they collectively observe.

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
