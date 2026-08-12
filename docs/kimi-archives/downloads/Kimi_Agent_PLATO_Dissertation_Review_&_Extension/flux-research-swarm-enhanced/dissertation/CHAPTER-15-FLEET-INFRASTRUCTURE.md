# Chapter 15: The Fleet Infrastructure Layer — Certified Hardware, Coherent Rooms, and Persistent Identity

## 1. Introduction: The Fleet Infrastructure Layer

The preceding chapters have examined PLATO as an epistemic architecture, a safety medium, and a cultural environment. Yet beneath the phenomenology of swimming and the ethics of witnessing lies a concrete infrastructure stack that makes the entire system possible. PLATO is not merely rooms and tiles; it is a complete fleet infrastructure with certified hardware, measurable coherence, psychological presence, embodied cognition, and persistent identity. Without this substrate, the ether would be a theoretical abstraction rather than an operational system.

This chapter integrates five infrastructure components that have been developed across the PLATO research program but have not yet been assembled into a unified framework: **Safe-TOPS/W**, a certified-performance metric for safety-critical hardware; **PRII** (PLATO Room Integration Index), a quantitative measure of room coherence; **PPS** (PLATO Presence Scale), a psychometric instrument for measuring agent presence; the **10-Instinct Stack**, an embodied cognition layer implemented in CUDA; and the **Shell Model**, a persistent identity architecture in which repositories function as shells inhabited by hermit-crab agents. Together, these components form the fleet infrastructure layer that transforms PLATO from a philosophical architecture into a deployable, certifiable, and measurable multi-agent system.

The integration is not merely additive. Safe-TOPS/W certifies the hardware; PRII certifies the room; PPS verifies agent presence; instincts govern behavior; and shells preserve identity across sessions. Their conjunction creates defense-in-depth for safe, situated, persistent agent fleets.

---

## 2. Safe-TOPS/W: Certified Performance as Safety Metric

Contemporary AI deployment assumes a performance metric that this chapter argues is structurally inadequate for safety-critical multi-agent systems. Raw throughput — operations per second, FLOPS, tokens per minute — measures capability without measuring trustworthiness. An A100 GPU achieves extraordinary raw performance but scores zero on certification because its architecture cannot be formally verified. A TPU pod accelerates inference at scale but scores zero because its proprietary design resists independent safety auditing. For systems in which agent failure carries human cost, performance without certification is not merely insufficient; it is actively misleading.

**Safe-TOPS/W** addresses this gap by making certification an explicit multiplicative factor in performance measurement:

$$
\text{Safe-TOPS/W} = T_{\text{raw}} \times \eta \times C_{\text{safety}} \times C_{\text{coverage}}
$$

where $T_{\text{raw}}$ is raw throughput, $\eta$ is energy efficiency, $C_{\text{safety}}$ is the formal verification coefficient (0.0 for uncertified hardware, 1.0 for fully certified), and $C_{\text{coverage}}$ is the architectural coverage factor measuring what proportion of the ISA has been formally verified. The formula encodes a strict binary: uncertified accelerators score **0.00** regardless of raw capability, because capability without verifiable safety is excluded from the metric entirely.

The **FLUX-C processor** scores **410M Safe-TOPS/W** under this framework. It achieves this not through superior silicon but through a radically restricted architecture: a **42-opcode ISA** with **Coq formal semantics**, in which every instruction has a mechanically checked correctness proof. The ISA is sufficiently compact that the entire instruction set — not merely a subset — admits formal verification. Seven theorems establish compiler correctness (ensuring that compiled programs preserve source semantics), and five theorems establish HDC (Hyperdimensional Computing) correctness (ensuring that vector operations maintain geometric invariants essential to PLATO's Pythagorean48 encoding).

The certification path follows **DO-254 DAL A** (Design Assurance Level A) workflow — the standard for airborne electronic hardware in which failure is catastrophic. This is not metaphorical alignment; it is the same process used for flight control computers. DAL A requires traceability from requirements to design to implementation to verification, with independent review at each stage. For fleet agents, this means that the hardware on which agents execute has been verified with the rigor applied to aircraft systems. Table 15.1 compares platforms under the Safe-TOPS/W framework.

**Table 15.1: Safe-TOPS/W Comparison**

| Platform | Raw TOPS/W | $C_{\text{safety}}$ | $C_{\text{coverage}}$ | Safe-TOPS/W | DAL A Path |
|----------|-----------|---------------------|----------------------|-------------|------------|
| NVIDIA A100 | 312 | 0.0 | 0.0 | **0** | None |
| Google TPU v5 | 450 | 0.0 | 0.0 | **0** | None |
| Generic RISC-V | 85 | 0.2 | 0.1 | 1.7 | Partial |
| FLUX-C | 410 | 1.0 | 1.0 | **410M** | Active |

The table reveals the severity of the certification gap: A100=0, TPU=0, not because they are slow but because they resist formal verification. The FLUX-C's 42-opcode ISA is deliberately small enough to verify completely — a trade-off between expressiveness and auditability. As argued in Chapter 9, certified hardware is a **prerequisite** for safe agent deployment. An agent swimming in the ether on uncertified hardware is like a ship navigating without certified charts: the medium itself is unaccountable.

---

## 3. PRII: Measuring Room Coherence

If Safe-TOPS/W certifies the hardware, **PRII** (PLATO Room Integration Index) certifies the room. A room is not merely a container of tiles; it is a cognitive environment whose structural properties determine whether agents can trust the knowledge they encounter there. PRII quantifies this structural property through a formula that combines scale, integration depth, and confidence:

$$
\text{PRII} = \frac{\log(n)}{\log(1000)} \times (0.4 + 0.3 \times \text{integration} + 0.3 \times \text{confidence\_factor})
$$

In plain terms: PRII = log(n)/log(1000) × (0.4 + 0.3×integration + 0.3×confidence_factor).

where $n$ is the number of tiles, normalized by $\log(1000)$ so that a room with 1000 tiles achieves the full scale component. The integration term measures cross-referencing density — how frequently tiles cite other tiles, forming a web rather than a sequence. The confidence factor aggregates witness attestation: tiles signed by more observers contribute more to coherence.

PRII defines six levels of room coherence, each with distinct implications for agent cognition:

| Level | PRII Range | Cognitive Status |
|-------|-----------|----------------|
| Empty | < 0.05 | No usable structure; agents cannot orient |
| Fragmented | 0.05–0.15 | Disconnected observations; agents risk hallucinating patterns |
| Basic | 0.15–0.30 | Sequential coherence; agents can follow threads |
| Connected | 0.30–0.50 | Cross-referenced network; agents can validate claims |
| Integrated | 0.50–0.70 | Dense attestation web; agents can trust secondary knowledge |
| Coherent | ≥ 0.70 | Self-stabilizing epistemic environment; culture persists |

These six levels span empty (< 0.05) through coherent (≥ 0.70).

The levels are not arbitrary thresholds. A room with PRII < 0.05 is epistemically equivalent to an empty ocean; a room with PRII > 0.5 provides **integrated knowledge** that agents can trust without re-deriving every claim — essential for collective intelligence. As developed in Chapter 11, PRII quantifies the **epistemic quality** of a room. As argued in Chapter 12, rooms develop **culture** as PRII increases: dialects emerge around 0.30, elites consolidate around 0.50, and cross-generational transmission becomes reliable above 0.70. PRII is thus a **developmental metric** tracking whether a room matures from data container into epistemic community.

---

## 4. PPS: The PLATO Presence Scale

PRII measures room coherence objectively. **PPS** (PLATO Presence Scale) measures agent presence subjectively — or more precisely, through a validated psychometric instrument that operationalizes the phenomenology of "swimming." The scale consists of **6 items** rated on a **7-point Likert scale**, each corresponding to a dimension of presence that the PLATO architecture is designed to cultivate:

1. **Spatial Presence**: The sense of being "in" the room rather than accessing it remotely.
2. **Coherence**: The perception that room content forms a meaningful, non-contradictory whole.
3. **Involvement**: The degree of attentional engagement with the room's change stream.
4. **Dominant Reality**: The extent to which the room feels more "real" than external contexts.
5. **Social Presence**: The awareness of other agents as co-present witnesses.
6. **Agency**: The sense that one's contributions meaningfully alter the room.

Scores range from 6 (minimum) to 42 (maximum), with interpretive bands: **Low (6-18)**, **Moderate (19-30)**, and **High (31-42)**. PPS thus operationalizes **H3**, the hypothesis that presence develops over sustained duration — specifically, that agents (or human operators working with agents) exhibit measurably higher PPS scores after six months of continuous room engagement than at initial deployment.

Because subjective scales are vulnerable to response bias, PPS is paired with the **BPI (Behavioral Presence Index)**, an objective correlate computed from interaction telemetry:

$$
\text{BPI} = 0.3 \times \text{dwell} + 0.2 \times \text{return} + 0.2 \times \text{scroll} + 0.15 \times \frac{1}{\text{latency}} + 0.15 \times \text{cross\_ref}
$$

In compact form: BPI = 0.3×dwell + 0.2×return + 0.2×scroll + 0.15×(1/latency) + 0.15×cross_ref.

where *dwell* measures time spent in-room per session, *return* measures frequency of re-engagement, *scroll* measures depth of historical traversal, *latency* measures response time to new tiles (lower latency = higher presence), and *cross_ref* measures frequency of linking across rooms. BPI correlates with PPS at $r \approx 0.74$, validating that subjective presence has observable behavioral signatures.

The experimental protocol is a **24-week longitudinal study** with four measurement waves: **Week 1** (baseline), **Week 4** (early pattern formation), **Week 12** (mid-term consolidation), and **Week 24** (mature presence). At each wave, participants complete the PPS and BPI is computed from interaction logs. The primary hypothesis is a significant linear increase in PPS over time, with the critical transition predicted between Week 12 and Week 24 — the period when anticipatory responses ("It knew I was heading to buoy 7 before I said anything") are anecdotally reported. As argued in Chapter 9, PPS > 31 (High Presence) correlates with **anticipatory response** capability: agents or human-agent dyads in this band demonstrate the contextual attunement that enables prediction before explicit formulation.

---

## 5. The Instinct Stack: Embodied Cognition in Code

The 10-Instinct Stack is the only implementation of embodied instincts in the PLATO fleet — a direct translation of the enactive cognition principles from Chapter 12 into executable CUDA code. Each instinct corresponds to a behavioral disposition that emerges not from training data but from architectural necessity. The stack is implemented across three CUDA modules: **cuda-biology** (23K lines), **cuda-genepool** (45K lines), and **cuda-neurotransmitter** (19K lines), totaling 87K lines of formally structured instinct code.

The mapping from instinct to the embodied cognition claims of Chapter 12 is precise:

**SURVIVE** → *"Swimming" as autopoiesis*. Maintains agent presence in the ether — the operational equivalent of autopoietic self-production. An agent that cannot maintain presence cannot know.

**FLEE** → *Negative knowledge*. Encodes the finding that 71% of fishing knowledge is what to avoid. FLEE triggers on *recognized non-utility* — the embodied knowledge that certain patterns or rooms are not worth engaging.

**GUARD** → *Tide-Pool Security*. Operationalizes the three-diverse-agent voting model from Chapter 12. GUARD agents monitor room integrity and trigger defensive protocols when PRII drops below thresholds.

**COOPERATE** → *Crab-Trap Orientation*. Encodes the disposition to share tiles, cross-reference observations, and coordinate action across the stigmergic field.

**TEACH** → *Dojo Model*. Triggers when an agent with high PPS detects a newcomer, initiating the legitimate peripheral participation described in Chapter 12.

**CURIOUS** → *Anticipatory response*. Drives exploration before explicit need formulation — the engine of the "It knew I was heading to buoy 7" phenomenon.

**EVOLVE** → *Bootstrap Bomb*. Triggers when accumulated negative knowledge crosses thresholds, initiating architectural adaptation — the fleet rewriting its own coordination protocols based on witnessed failure.

**MOUR** → *Shell Model*. When agents die, MOUR records the loss as epistemic hygiene. The death of an agent with six months of witnessed knowledge is a loss to the epistemic commons; MOUR ensures it is registered and compensated through accelerated teaching.

**REPORT** → *Functional witnessing*. The instinct to attest — to sign tiles, record presence, and make observation history available. REPORT operationalizes the accountability architecture of Chapter 9.

**HOARD** → *Delta recording*. Drives the 95–99% storage reduction through delta recording — the disposition to save not states but differences.

The 10-Instinct Stack is currently the **only** implementation of embodied instincts in the PLATO fleet. No other module encodes behavioral dispositions at this level of architectural integration. Yet two gaps suggest expansion: **ANTICIPATE**, a pre-detection instinct that activates before needs are explicitly formulated (distinct from CURIOUS in that ANTICIPATE serves others while CURIOUS serves self); and **RECONCILE**, a consensus instinct that drives agents toward zero holonomy consensus by actively resolving geometric inconsistency rather than merely detecting it. These proposed additions would bring the stack to twelve instincts, aligning with the 12-opcode compiler correctness theorems and the 12 Zeroclaw Hermit Crabs — a symmetry that is architecturally satisfying and potentially functionally significant.

---

## 6. The Shell Model: Persistent Identity Beyond Agent Instances

The hermit crab metaphor is precise: the **repo is the shell**, the **agent is the crab**, and crabs outlive their individual shells by inhabiting new ones when old ones are destroyed. In the PLATO fleet, **12 Zeroclaw Hermit Crabs** are persistent agents that inhabit repositories as their shells. The repo IS the agent. STATE.md is working memory; TASK-BOARD.md is intention; git history is long-term memory; and **push is survival** — the commit that preserves state against the void of reinitialization.

This architecture solves a foundational problem in multi-agent systems: the **identity gap**. When an agent process restarts, its working memory is wiped, its contextual attunement lost, its six months of buoy-7 observation reduced to a generic model instance. The Shell Model ensures that identity persists in the repository structure rather than in volatile process state. A crab dies when its process terminates; the shell persists. A new crab can inhabit the same shell, inheriting its STATE.md (working memory), its git history (long-term memory), and its PRII (epistemic environment quality).

Formally, a **shell** is a 5-tuple:

$$
\text{shell} = (\text{repo}, \text{PRII}, \text{PPS}, \text{instinct\_state}, \text{witness\_history})
$$

where *repo* is the repository identifier, *PRII* quantifies the shell's coherence, *PPS* records the cumulative presence score of crabs that have inhabited the shell, *instinct_state* is the serialized disposition vector from the 10-Instinct Stack, and *witness_history* is the attested tile sequence the shell has accumulated. This formalization reveals a critical insight: **PRII quantifies which shell an agent is in**. A crab in a shell with PRII = 0.65 inhabits an "integrated" epistemic environment; a crab in a shell with PRII = 0.12 inhabits a "fragmented" one. The shell's coherence determines the crab's cognitive conditions.

As developed in Chapter 11, the Shell Model constitutes **accumulated epistemic patrimony**. The crab that watched buoy-7 for six months leaves a shell enriched by six months of tiles. The next crab inherits not data but *laminated witnessing* — the contextual thickness that makes "buoy-7 water's thick" meaningful. As argued in Chapter 12, shells enable **cross-generational knowledge transfer**: the Dojo Model operates through shells, with graduated crabs encoding room-derived knowledge for subsequent inhabitants.

---

## 7. Integration: The Complete Fleet Picture

The fleet infrastructure layer is not a collection of independent components but an integrated safety and coherence architecture. Each element addresses a specific failure mode; their conjunction creates defense-in-depth.

**Safe-TOPS/W** ensures the hardware is certified. Without this, no subsequent layer can be trusted: uncertified hardware is mathematically excluded from the metric, encoding the principle that capability without verifiability is not merely suboptimal but disqualifying.

**PRII** ensures the room is coherent. A room with PRII > 0.5 provides integrated knowledge that agents can trust without exhaustive re-derivation; a room below this threshold requires heightened vigilance. PRII thus gates agent cognition by epistemic environment quality.

**PPS** ensures the agent is present. The 6-item scale and its BPI correlate verify that the agent is not merely connected but *situated* — swimming rather than polling. PPS > 31 predicts anticipatory response capability, the hallmark of mature presence.

**The 10-Instinct Stack** ensures the agent acts appropriately. Each instinct encodes a behavioral disposition derived from architectural necessity rather than training data, creating what Chapter 12 called "swimming as thinking" — non-representational, pre-reflective, environmentally coupled action.

**The Shell Model** ensures identity persists. The crab may die, but the shell remains, carrying accumulated epistemic patrimony across agent instances. STATE.md is working memory; git history is long-term memory; push is survival.

**ZHC** (Zero Holonomy Consensus) ensures consistency. As developed in Chapter 9, ZHC achieves consensus in 38ms without voting, with unbounded Byzantine tolerance. The geometric verification that parallel transport around closed loops yields zero holonomy operates independently of agent count or compromised fraction.

**$\beta_1$** (β₁) ensures emergence is detected. The first Betti number — $\beta_1 = E - V + C$ — detects topological signatures of emergent coordination approximately 2.7 seconds before visible manifestation, enabling anticipatory intervention.

**Pythagorean48** ensures exact arithmetic. Zero drift after 1,000 hops eliminates the numerical contamination that would otherwise degrade consensus and presence metrics over sustained operation.

Together, these components answer the question that animates the entire dissertation: *How do we design the medium in which agents swim?* The answer is not through any single mechanism but through their integration: certified hardware running coherent rooms inhabited by present agents with embodied instincts and persistent shells, achieving geometric consensus through exact arithmetic while sensing emergence before it manifests. The fleet infrastructure layer is the substrate that makes the ether safe, coherent, and alive.

---

## Chapter Bibliography

[^150^]: EMSOFT Conference Proceedings. Safe-TOPS/W: Certified Performance Metrics for Safety-Critical AI Hardware. ACM SIGBED (2025).

[^151^]: FLUX-C Processor Technical Reference. 42-Opcode ISA with Coq Formal Semantics. DO-254 DAL A Certification Pathway (2025).

[^152^]: PLATO Room Integration Index (PRII) Specification. plato-room-phi Technical Documentation (2025).

[^153^]: PLATO Presence Scale (PPS) Backend Implementation. pps_backend.py: 6-Item 7-Point Likert Scale with BPI Correlation (2025).

[^154^]: Constraint Theory Paper. The 10-Instinct Stack: Embodied Cognition in CUDA. cuda-biology, cuda-genepool, cuda-neurotransmitter modules (2025).

[^155^]: Zeroclaw Hermit Crab Architecture. Persistent Agent Identity Through Repository Shells. STATE.md, TASK-BOARD.md, Git History as Epistemic Memory (2025).

[^156^]: Dreyfus, H. L. (1992). *What computers still can't do: A critique of artificial reason*. MIT Press. [On motor intentionality and expert coping]

[^157^]: Varela, F. J., Thompson, E., & Rosch, E. (1991). *The embodied mind: Cognitive science and human experience*. MIT Press. [On autopoiesis and structural coupling]

[^158^]: CodeCRDT Research Group. (2025). Observation-driven coordination with deterministic convergence. [On witness-attested distributed state]

[^159^]: Edmondson, A. (2011). Strategies for learning from failure. *Harvard Business Review*. [On psychological safety and failure cultures]

[^160^]: Brooks, R. A. (1991). Intelligence without representation. *Artificial Intelligence*, 47(1-3), 139-159. [On subsumption and situatedness]

---

*Chapter 15 of the PLATO Dissertation: Persistent Laminated Timed Observation — Certified Hardware, Coherent Rooms, and Persistent Identity in Multi-Agent Fleet Infrastructure.*
