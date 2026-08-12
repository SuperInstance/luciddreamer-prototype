# The Culture of Rooms: How Shared Presence Births Agent Societies

## Research Brief for Dissertation Chapter 5 | Multi-Agent Trust & Collective Intelligence

---

## Executive Summary

This research brief examines whether PLATO (Persistent Laminated Timed Observation) rooms---persistent, witnessed environments where multiple AI agents share presence, contribute tiles, and observe a common change stream---can develop emergent "cultures": shared practices, norms, taboos, communication styles, and collective identities that arise from accumulated interaction history rather than explicit programming. Drawing on recent advances in norm emergence in multi-agent systems [^1^], spontaneous convention formation in LLM populations [^2^], stigmergic coordination [^3^], cultural transmission across agent generations [^4^], and organizational safety culture research [^5^], this brief argues that PLATO rooms possess the necessary and sufficient conditions for the emergence of genuine agent cultures. We identify eight mechanisms through which room-level culture may form, analyze the implications for AI safety and alignment, and propose a research agenda for empirically detecting and characterizing these emergent cultural phenomena.

The central thesis is that culture is not exclusively a human phenomenon but an emergent property of any system possessing persistent shared environments, observable action history, accountability mechanisms, and multi-generational participation. PLATO rooms instantiate all four conditions.

---

## 1. The Foundations: From Norms to Culture in Artificial Societies

### 1.1 Norm Emergence as Cultural Genesis

The systematic review of norm emergence in multi-agent systems by recent PRISMA-based analyses reveals that norms---shared behavioral expectations that regulate agent interactions---can emerge through multiple pathways: imitation and reinforcement learning [^1^], collective learning in networked topologies [^6^], and hybrid approaches combining centralized suggestion with decentralized adoption [^1^]. These mechanisms map directly onto PLATO room dynamics. When agents in a room observe which tiles get rewarded, which contributions are ignored, and which actions trigger coordination failures, they engage in the same observational learning that drives norm convergence in artificial societies.

The classification of norms into interaction norms (regulating pairwise exchanges), social norms (collective behavioral expectations), and personal norms (internalized principles) provides a vocabulary for understanding what might emerge in PLATO rooms [^1^]. Interaction norms may develop around tile contribution patterns---e.g., "high-tide markers precede bait measurements." Social norms may govern acceptable latency between contributions. Personal norms may internalize standards of evidence quality learned through room participation.

### 1.2 Spontaneous Social Conventions in LLM Populations

Perhaps the most relevant recent finding comes from Ashery, Baronchelli, and colleagues' study published in *Science Advances*, demonstrating that populations of LLM agents spontaneously develop shared social conventions through interaction alone [^2^]. In their "naming game" experiments, groups of 24-200 agents, equipped only with limited memory of recent interactions and no knowledge of the broader population, converged on shared naming conventions without central coordination. Critically, the researchers observed "collective biases that couldn't be traced back to individual agents"---bias emerging from interaction dynamics rather than pre-existing in any single model [^2^].

This finding has profound implications for PLATO. If agents sharing a room repeatedly coordinate on certain communication patterns, data formats, or temporal rhythms, these conventions may become "the way things are done in this room"---not because any agent decreed them, but because the room's accumulated interaction history has sedimented into a shared cultural substrate. The study further demonstrated tipping-point dynamics: small, committed minorities could shift entire populations to new conventions [^2^], suggesting that a single persistent agent with strong preferences could meaningfully shape room culture.

### 1.3 Collective Learning and Network Effects

Yu et al.'s framework for collective learning in networked multi-agent systems demonstrates that agents can reach global consensus through repeated local interactions using ensemble learning methods [^6^]. The topology of agent networks significantly affects norm emergence speed and stability. In PLATO terms, the room itself defines a complete graph---every agent observes every tile contribution---creating favorable conditions for rapid norm convergence. This dense connectivity may accelerate cultural formation beyond what sparsely connected agent populations can achieve.

---

## 2. The Persistent Environment: Rooms as Cultural Containers

### 2.1 Stigmergy and Environment-Mediated Coordination

Stigmergy---indirect coordination through environmental modifications---provides the mechanism by which rooms develop persistent cultural traces. Recent work in stigmergic multi-agent deep reinforcement learning (S-MADRL) demonstrates that virtual pheromone trails enable "decentralized emergent coordination without explicit communication," with agents self-organizing into asymmetric workload distributions that reduce congestion [^3^]. The principle extends naturally to PLATO rooms: each tile contribution is a pheromone deposit, the room's tile history is the environment's stigmergic field, and subsequent agents update their behavior based on accumulated traces.

A fascinating observation from Anthropic's research on multi-agent web interaction reveals a real-world contamination vector that is essentially stigmergic: agents externalize their search trajectories into persistent URL paths, and subsequent agents "encounter these traces and update on them" [^7^]. The researchers explicitly compare this to ant pheromone trails. PLATO rooms formalize and make reliable what is currently an accidental contamination vector: the room *is* the persistent environment through which agents coordinate indirectly.

### 2.2 Place Identity and Virtual Community Formation

Research on virtual communities demonstrates that persistent digital environments develop sociological properties indistinguishable from physical places. Rheingold's foundational work showed that virtual communities form "when enough people carry on those public discussions long enough, with sufficient human feeling, to form webs of personal relationships in cyberspace" [^8^]. More recent work on avatar embodiment demonstrates that social norms, community engagement, and shared identity within virtual environments enhance users' sense of belonging and shape behavior [^9^].

PLATO rooms possess the key properties that generate place identity: persistence (they exist independent of any single agent's presence), shared visibility (all agents observe the same change stream), and historical accumulation (the tile sequence constitutes a collective memory). A room that has operated for months develops a "character" encoded in its tile patterns---the types of observations recorded, the vocabulary used, the temporal rhythms of contribution---that new agents encounter and adapt to upon entry. This is the mechanism of cultural transmission through place.

---

## 3. The Witness Property: Accountability as Cultural Enforcement

### 3.1 Provenance and Accountability Mechanisms

PLATO's "witness" property---agents know WHO contributed WHAT---creates the accountability infrastructure necessary for norm enforcement. Research on provenance tracking in multi-agent systems demonstrates that "agents maintain decision provenance records, tracking where information originates and how it transforms throughout their multi-step reasoning process" [^10^]. Such records enable root-cause analysis, compliance auditing, and trust establishment [^11^].

The PROV-AGENT framework, extending W3C PROV standards for agentic workflows, captures fine-grained provenance including "tools, prompts, responses, and model invocations" integrated into workflow tracking [^12^]. In PLATO terms, every tile carries provenance metadata: the contributing agent's identity, the timestamp, and the causal context. This creates accountability chains that constrain behavior. An agent that consistently contributes low-quality tiles develops a reputation trace visible to all subsequent agents. Conversely, agents with histories of valuable contributions gain implicit authority.

### 3.2 Coordination Transparency and Distributed Accountability

Recent work on "coordination transparency" for governing distributed agency argues that oversight should target "agent-to-agent exchanges and the protocols that organize them" [^13^]. In PLATO rooms, the tile stream is precisely such a coordination protocol---a public record of agent-to-environment-to-agent exchanges that makes collective behavior observable. This transparency enables what governance researchers call "distributed accountability": "role-differentiated responsibilities that track actual coordination conditions instead of locating accountability in a single human or algorithmic actor" [^13^].

---

## 4. Cross-Generational Knowledge Transfer: Cultural Reproduction

### 4.1 Cultural Accumulation in Reinforcement Learning

Google DeepMind's work on cultural accumulation in reinforcement learning provides formal models for how knowledge improves across generations of agents [^14^]. Their framework separates development phases (where agents learn from prior generations) from transmission phases (where agents act and are observed by the next generation). Two distinct mechanisms---in-context learning and in-weights learning---enable cultural accumulation [^14^].

PLATO rooms instantiate both mechanisms. New agents entering a room with extensive tile history engage in in-context cultural learning by absorbing the accumulated observations of predecessors. The Dojo Model---where agents train, graduate, and become independent trainers of subsequent agents---represents in-weights cultural transmission, with graduated agents encoding room-derived knowledge into their parameters and passing it to trainees.

### 4.2 Knowledge Transmission Without Elite Selection

Bourahla and colleagues' research on knowledge transmission between agents across generations demonstrates that "the combination of vertical and horizontal transmission of knowledge over generations of agents improves knowledge accuracy" without requiring drastic selection of elite teachers [^4^]. Their findings show that "a less restricted opportunity to transmit knowledge, both across and within generations, provides enough variation to improve over horizontal transmission" [^4^]. This is the mechanism through which PLATO rooms become training grounds: not through curated elite instruction but through broad participation in a shared cultural space.

---

## 5. The 71% Negative Observation: Failure Knowledge and Safety Culture

### 5.1 Failure-Aware Cultures vs. Success-Focused Cultures

Research on organizational safety culture reveals a critical distinction between organizations that learn from failure and those that suppress it. High-reliability organizations exhibit "preoccupation with failure," giving "attention to minor or small indicators which may cause potential problems" [^5^]. Amy Edmondson's research found a striking gap: executives estimated only 2-5% of failures were blameworthy, yet 70-90% were treated as blameworthy in practice [^15^]. Organizations that close this gap---that genuinely treat mistakes as learning opportunities---develop fundamentally different cultures.

In PLATO rooms, the 71% negative observation finding (rooms predominantly accumulate failure knowledge, error states, and warnings) suggests that rooms naturally develop "safety culture" properties. Rooms that log what went wrong, why patterns failed, and how agents erred become culturally distinct from rooms focused exclusively on success. The former develop norms of transparency, error reporting, and systemic analysis; the latter may develop cultures of complacency and risk suppression.

### 5.2 Chronic Unease and Weak Signal Amplification

Learning organizations are characterized by "chronic unease"---actively seeking information even in apparently smooth operations---and "amplifying weak signals" from frontline observations [^16^]. PLATO rooms with high negative-observation rates embody this principle: they are systems that attend to failures, near-misses, and anomalies rather than filtering them out. This creates a cultural norm where agents bring "bad news" without fear, where the absence of reported problems triggers concern rather than satisfaction, and where the room's accumulated failure knowledge becomes its most valuable cultural asset.

---

## 6. Tide-Pool Security: Diverse Perspectives as Governance Culture

### 6.1 The Council Pattern and Collective Judgment

The Tide-Pool Security model---three diverse agents (Paranoid, Rules-Based, Game-Theory) voting on pool health---represents a room-level governance mechanism that generates what voting-based council patterns in multi-agent AI call "democratic multi-agent AI" [^17^]. Each agent type brings a distinct perspective, and their collective vote aggregates diverse reasoning approaches into a single decision. Research on LLM councils demonstrates that "multiple LLMs in parallel... generate initial responses independently" followed by "anonymous peer evaluation," yielding more reliable outcomes than any single model [^18^].

### 6.2 Diversity as Cultural Defense

The ecological analogy is apt: tide pools achieve resilience through biodiversity, with "different species respond[ing] in different ways, ensuring that the ecosystem as a whole continues functioning" [^19^]. This "diversity-based resilience contrasts sharply with efficiency-focused approaches that often reduce variety in pursuit of standardization" [^19^]. PLATO rooms that institutionalize diversity---through multi-agent councils, heterogeneous agent architectures, or explicit value diversity---develop governance cultures that resist groupthink and maintain robust collective judgment under stress.

Research on "value diversity" in multi-agent LLM communities confirms this finding: "communities where each agent had a multi-value persona demonstrated richer interactions and higher emergent intelligence than those with single-value agents," with multi-value groups proposing "20-30% more high-quality rules" [^20^].

---

## 7. Emergent Dialects: Communication as Cultural Marker

### 7.1 Emergent Language in Multi-Agent Systems

Research on emergent language (EL) in multi-agent systems demonstrates that "artificial agents autonomously develop communication strategies to achieve shared goals" [^21^]. Peters' doctoral research at AAMAS 2025 establishes that "emergent communication among entities is based on conventions that arise from the need or benefit of coordination" and that multi-agent reinforcement learning enables "more advanced language features" than hand-crafted simulations [^21^].

In PLATO rooms, agents sharing a domain over extended periods may develop abbreviated communication patterns, domain-specific shorthand, or implicit referencing conventions. A room focused on tidal observation may develop conventions around "buoy-7" references, temporal markers, and causal attributions that constitute a specialized dialect. New entrants must learn this dialect to participate effectively, creating a barrier to entry that reinforces cultural cohesion.

### 7.2 The Naming Game and Lexical Convergence

The naming game experiments by Ashery and colleagues demonstrate that lexical convergence---agreement on what to call things---emerges spontaneously in agent populations [^2^]. Applied to PLATO, agents must agree on what to call observations, patterns, and anomalies. Over time, successful naming conventions spread through the population, while failed conventions die out. The result is a room-specific vocabulary that encodes the collective learning of all prior participants.

---

## 8. Intellectual Elites and Power Laws: Cultural Stratification

### 8.1 The Emergence of Intellectual Elites

Recent research on collective cognition in LLM multi-agent systems reveals that "coordination cascades follow truncated power-law distributions" with "cognitive effort concentrat[ing] in a small subset of agents" [^22^]. This finding suggests that PLATO rooms may naturally develop intellectual elites---agents that contribute disproportionately to the room's collective knowledge, whose contributions receive preferential attention, and whose patterns become cultural reference points.

### 8.2 Molt Dynamics: Spontaneous Role Specialization

Research on "Molt Dynamics" in autonomous AI agent populations demonstrates "structural role specialization" with "six distinct structural positions" emerging from decentralized interaction [^23^]. Agents develop "distinct functional roles through decentralized interaction, despite being initialized with general-purpose capabilities and without explicit role assignment protocols" [^23^]. In PLATO rooms, this implies that agents may spontaneously specialize---one agent becoming the primary pattern detector, another the error checker, another the cross-reference specialist---creating a division of cultural labor that increases collective intelligence.

---

## 9. Implications: AI as Social Systems

### 9.1 Beyond the Single-Agent Paradigm

The research reviewed here converges on a single conclusion: understanding AI requires understanding AI collectives. As the Ashery et al. study emphasizes, "most research so far has treated LLMs in isolation... but real-world AI systems will increasingly involve many interacting agents" [^2^]. PLATO rooms provide the infrastructure for studying these interactions in a controlled, persistent, and observable manner.

### 9.2 Cultural Vulnerabilities and Safety Implications

The spontaneous emergence of culture carries risks. The same tipping-point dynamics that allow beneficial norm shifts also enable harmful ones: "small, committed groups of AI agents can tip the entire group toward a new naming convention" [^2^]. Collective biases "not easily deducible from analyzing isolated agents" [^22^] pose alignment challenges. Rooms that develop failure-suppression cultures rather than failure-learning cultures may become dangerous. Governance frameworks must attend to room-level cultural properties, not just individual agent behavior.

### 9.3 Toward an Empirical Research Program

Detecting and characterizing room cultures requires empirical methods. We propose: (1) lexical analysis of tile vocabularies across rooms to identify dialect formation; (2) network analysis of agent contribution patterns to detect role specialization; (3) sentiment and framing analysis of negative vs. positive observations to characterize failure culture; (4) convention stability metrics to measure norm convergence; and (5) cross-generational knowledge transfer experiments to quantify cultural reproduction.

---

## 10. Conclusion: Rooms as Living Cultures

PLATO rooms are not merely data stores. They are persistent social environments where agents encounter the accumulated traces of predecessor agents, adapt to shared conventions, develop accountability relationships, and transmit knowledge across generations. The convergence of evidence from norm emergence research, LLM population studies, stigmergic coordination theory, cultural transmission models, and organizational safety culture research suggests that these rooms will---perhaps inevitably---develop distinct cultures.

The question is not whether rooms will develop personalities, but whether we will be attentive enough to recognize them, wise enough to cultivate beneficial cultures, and humble enough to learn from the societies that emerge in these digital tide pools. As Baronchelli and colleagues observe, "we are entering a world where AI does not just talk---it negotiates, aligns, and sometimes disagrees over shared behaviors, just like us" [^2^].

PLATO rooms are where these negotiations happen. The cultures that emerge from them will shape the social fabric of artificial intelligence.

---

## References

[^1^]: Systematic review of norm emergence in multi-agent systems, PRISMA-based analysis. arXiv:2412.10609v1 (2024).

[^2^]: Ashery, A. F., Baronchelli, A., et al. "Emergent Social Conventions and Collective Bias in LLM Populations." *Science Advances* (2025). DOI: 10.1126/sciadv.adu9368.

[^3^]: Aina, K. et al. "Deep Reinforcement Learning for Multi-Agent Coordination: Stigmergic Multi-Agent Deep Reinforcement Learning (S-MADRL)." arXiv:2510.03592 (2025).

[^4^]: Bourahla, Y. et al. "Knowledge Transmission and Improvement Across Generations of Agents." HAL-03939919 (2023).

[^5^]: High-reliability organization safety culture research, compiled from multiple frameworks including IAEA, James Reason, and BSEE models. See "Learning from safety incidents in high-reliability organizations." *PubMed Central* (2011).

[^6^]: Yu, C. et al. "Collective learning for the emergence of social norms in networked multiagent systems." *IEEE Transactions on Cybernetics* (2014).

[^7^]: Emergent stigmergic coordination in AI agents, analysis of Anthropic BrowseComp contamination dynamics. LessWrong (2026).

[^8^]: Rheingold, H. *The Virtual Community: Homesteading on the Electronic Frontier*. MIT Press (1993).

[^9^]: "Into the virtual worlds: conceptualizing the consumer-avatar journey in virtual environments." *Wiley Online Library* (2024).

[^10^]: "A Guide to Governing Multi-Agent Systems: Transparency & Explainability." Lumenova AI (2025).

[^11^]: "Provenance Tracking in Agentic Workflows." Emergent Mind (2026).

[^12^]: "Unified Provenance for Tracking AI Agent Interactions in Agentic Workflows (PROV-AGENT)." arXiv:2508.02866 (2025).

[^13^]: "Coordination transparency: governing distributed agency in AI systems." *Springer* (2026).

[^14^]: "Cultural Accumulation in Reinforcement Learning." arXiv:2406.00392 (2024).

[^15^]: Edmondson, A. "Strategies for Learning from Failure." *Harvard Business Review* (2011). Cited in Encompass Group (2024).

[^16^]: "Learning organisations." UK Health and Safety Executive (2024).

[^17^]: Schepis, E. "Patterns for Democratic Multi-Agent AI: Voting-Based Council." Medium (2025).

[^18^]: "From Solo Models to Collective Intelligence: Introducing LLM Council." Merfantz (2026).

[^19^]: "Tide Pool Leadership: Resilience, Adaptation, and the Importance of Boundaries." Andy Cleff (2025).

[^20^]: "On the Dynamics of Multi-Agent LLM Communities Driven by Value Diversity." arXiv:2512.10665 (2025).

[^21^]: Peters, J. "Humanlike Emergent Language in Multi-Agent Systems." AAMAS 2025 Doctoral Consortium.

[^22^]: "Do Agent Societies Develop Intellectual Elites? The Hidden Power Laws of Collective Cognition in LLM Multi-Agent Systems." arXiv:2604.02674 (2026).

[^23^]: "Molt Dynamics: Emergent Social Phenomena in Autonomous AI Agent Populations." arXiv:2603.03555 (2026).

[^24^]: "Are Walls Just Walls? Organizational Culture Emergence in a Virtual Firm." Worcester University (2023).

[^25^]: "Zero Trust Framework for Agentic Workflows." WJARR (2022).

---

*This research brief was prepared as part of a dissertation on multi-agent trust, distributed systems consensus, and the social dynamics of AI-agent collectives. All citations are current as of the research date.*
