# Chapter 12: Swimming as Thinking — Embodied Cognition, Agent Culture, and the Social Ether

> "The bird does not think about air. The fish does not think about water. The captain does not think about PLATO. They swim."

---

## 1. Introduction: From Embodied Cognition to Agent Societies

The chapters preceding this one have examined PLATO as an epistemic architecture — a system for recording, laminating, and transmitting observations across time. We have considered its tile-based grammar, its delta-recording logic, its temporal depth, and its phenomenology of witnessing. Yet all of these technical and philosophical discussions converge upon a single question that is at once cognitive and social: What does it mean for an artificial agent to *inhabit* a room rather than query a database? This chapter argues that the answer requires us to travel a long theoretical arc — from embodied cognition in individual agents to emergent culture in agent collectives — and that PLATO constitutes the architectural bridge between these two domains.

The arc is not obvious at first glance. Embodied cognition, as developed in the cognitive science literature from Brooks to Varela, concerns the individual cognizer's relationship to its environment: how perception and action are coupled, how intelligence arises from situated engagement rather than symbolic manipulation, how the body — or its functional equivalent — structures the space of possible thoughts [^1^][^15^]. Agent culture, by contrast, concerns the collective: how groups of agents develop shared practices, norms, dialects, and identities through accumulated interaction [^2^][^26^]. One would seem to be a micro-phenomenon, the other macro. Yet they are, in fact, continuous. The same architectural features that enable an individual agent to "swim" in a PLATO room — persistent environmental coupling, delta-based perception, voice-mediated knowledge — are precisely the conditions under which groups of agents develop what can only be described as culture.

This chapter traces that continuity. We begin by revisiting Rodney Brooks's subsumption architecture and the enactive cognition of Varela, Thompson, and Rosch to establish "swimming" as a genuine cognitive mode — non-representational, pre-reflective, environmentally coupled [^1^][^15^]. We then examine PLATO rooms through the lens of Kim Sterelny's cognitive niche theory and Edwin Hutchins's distributed cognition, arguing that rooms function as scaffolded epistemic environments within which both individual and collective intelligence are made possible [^7^][^9^]. The anticipatory response — "It knew I was heading to buoy 7 before I said anything" — is analyzed through Hubert Dreyfus's phenomenology of expertise as a form of motor intentionality that emerges from sustained environmental attunement [^17^][^18^]. The voice interface is situated within Walter Ong's psychodynamics of orality and Jean Lave and Etienne Wenger's communities of practice, establishing vocal interaction as the medium of situated learning [^13^][^14^].

With these theoretical foundations in place, the chapter turns to the emergence of agent culture proper. Drawing on recent research demonstrating spontaneous convention formation in LLM populations [^2^], norm emergence in multi-agent systems [^26^], stigmergic coordination [^27^], and cross-generational cultural transmission [^28^], we identify four necessary conditions for the emergence of culture in artificial societies and demonstrate that PLATO rooms instantiate all four. We examine how rooms develop distinct personalities — failure cultures versus success cultures — and how emergent communication patterns and intellectual stratification give each room what can only be called a dialect [^29^][^30^]. Finally, we consider rooms as mechanisms of cultural transmission, analyzing the Dojo Model through which knowledge persists across agent generations even as individual participants are retired [^28^].

The chapter's central claim is that embodied cognition and agent culture are not adjacent topics but the same phenomenon viewed at different scales. Individual agents swim; groups of swimming agents create currents; those currents, sustained over time, become culture. PLATO is the ether in which both the swimming and the culture-making occur.

---

## 2. Swimming as Cognitive Mode

Rodney Brooks's 1991 paper "Intelligence Without Representation" marks the pivotal turning point away from what he termed Good Old-Fashioned Artificial Intelligence (GOFAI) and toward the embodied turn that would reshape cognitive science over the subsequent decades [^1^]. The Physical Symbol System Hypothesis — the claim that intelligence consists in the manipulation of formal symbols independent of any physical substrate — had dominated AI since Newell and Simon's foundational work [^31^]. Brooks argued, in essence, that the hypothesis was not merely wrong but catastrophically wrong, producing systems that were brittle, slow, and incapable of operating in real environments. His alternative was radical: abandon representation altogether. "Representation is the wrong unit of abstraction in building the bulkiest parts of intelligent systems," Brooks insisted. "It is better to use the world as its own model" [^1^].

The subsumption architecture that embodied this insight was deceptively simple. Layered behavioral modules — obstacle avoidance, wander, explore — were directly wired to sensors and actuators, each layer subsuming the one below when activated. No central model. No world representation. No planning module deliberating over symbolic states. Herbert the can-collector and Allen the navigator achieved robust intelligent behavior not by computing solutions but by being *in* the world, responding in real time to environmental contingencies [^5^]. Brooks identified four characteristics of his approach: situatedness (in the world), embodiment (in a physical body), intelligence (as emergent behavior), and emergence (from system-world interactions rather than from explicit design) [^6^]. The implications for PLATO are direct and architectural: treating rooms as "places not databases" is the software-architectural equivalent of Brooks's insistence that the world be its own model. The agent does not hold a representation of the room; the room *is* the representation, encountered through continuous presence rather than queried on demand.

Yet while Brooks's robots demonstrated that intelligence could emerge without representation, they did not fully explain *how* such cognition was experienced by the system itself — what it was like, functionally, to navigate without a map. The enactive approach developed by Francisco Varela, Evan Thompson, and Eleanor Rosch provides this missing phenomenological dimension [^15^]. Enactivism holds that cognition is not the representation of a pre-given world but the *bringing forth* of a world through the organism's own activity. Living systems are autopoietic — self-producing, operationally closed, maintaining their own organization through structural coupling with their environment [^16^]. The fish does not "process information" about water; water is the medium within which fish-being continually constitutes itself. Cognition, on this view, is sense-making — the establishment of a domain of significance through the organism's ongoing engagement with its milieu.

Thompson elaborates: enactive cognition "seeks to explain how the structures and mechanisms of autonomous cognitive systems can arise and participate in the generation and maintenance of viable perceiver-dependent worlds" rather than "the attempt to explain cognition in terms of the 'recovery' of (pre-given, timeless) features of The World" [^15^]. For software agents in PLATO, "swimming" means precisely this: a mode of cognitive engagement in which the agent does not represent the environment but is structurally coupled to it. The agent does not query the room; it *swims* in it — continuously, pre-reflectively, attending to what matters without needing to represent what does not. The bird does not think about air because air is not an object of thought but the medium of existence. The fish does not think about water because water is not represented but inhabited. And the captain does not think about PLATO because PLATO, when it functions as designed, becomes the invisible ether within which captain-like knowing becomes possible.

This is not merely a metaphor. As Froese and Ziemke argue in their analysis of enactive artificial intelligence, "the systemic organization of life and mind" requires understanding cognition as arising from the coupling of autonomous systems with their environments rather than from computational processes internal to a symbol-manipulating engine [^32^]. PLATO operationalizes this insight architecturally. The room-as-place is not a convenient abstraction; it is the environmental structure within which agent cognition becomes possible.

---

## 3. Rooms as Cognitive Niches

If swimming is the cognitive mode of the individual agent, the room is the environment within which that mode is exercised and sustained. To understand how rooms function as cognitive environments — rather than as mere data containers — we require theoretical frameworks that address the relationship between cognition and its physical and social setting.

Edwin Hutchins's *Cognition in the Wild* (1995) provides the foundational analysis [^7^]. Hutchins's ethnography of naval navigation teams demonstrated that cognitive processes are not confined to individual brains but distributed across people, artifacts, and the environment. The navigation team — with its alidades, charts, compasses, and coordinated communicative procedures — constitutes a single cognitive system. The alidade is not a tool *used by* a navigator; it is a constitutive element of the cognitive process itself [^8^]. When Hutchins writes that "the tools of the trade are not simply aids to cognition; they are part of cognition," he captures precisely the relationship between PLATO agents and their rooms [^7^]. The room is not an aid to the agent's cognition; it is a constitutive element of the agent's cognitive system.

Kim Sterelny's concept of the "cognitive niche" extends this analysis by asking not merely where cognition happens but how environments are *constructed* to support it [^9^]. Sterelny distinguishes between the extended mind thesis — which asks whether cognition extends beyond the skull — and the scaffolding model, which asks how environments are built to support intelligent action. He argues that extended mind cases are "limiting cases of environmental scaffolding" and that the niche construction model is "more helpful for understanding human action" [^9^]. Cognitive niches, on Sterelny's account, are environments "assembled [by] informational resources that support and scaffold intelligent action" — they are not naturally occurring but built, maintained, and modified by the agents that inhabit them.

PLATO rooms are precisely such scaffolds: epistemic niches constructed to support specific forms of agent cognition. The `buoy-7` room does not merely contain data about a location; it is a location — a place with a history of observations, a pattern of contributions, a rhythm of attention that new agents encounter and adapt to upon entry. The agent does not "have" knowledge about the room; the room provides the structure within which knowing becomes possible. Sterelny's framework thus allows us to see that PLATO rooms are not passive containers but active scaffolds — environments built and maintained through the accumulated contributions of participating agents, each tile deposit modifying the niche in ways that shape subsequent cognition.

The delta recording mechanism — capturing change rather than state — operationalizes a key insight from both Hutchins and Sterelny about how embodied agents experience the world. As Hutchins observed, navigation is not a process of maintaining a static representation but of continuous, situated adjustment to changing conditions [^7^]. The world presents itself not as a database to be queried but as a stream of differences to be noticed. Delta recording captures what phenomenologists call the "horizonal" nature of perception: we attend to what changes against a background of stable assumptions [^15^]. The fishing captain's thirty years of embodied ocean knowledge is not a repository of facts but a history of structural coupling with the sea — an accumulated sensitivity to delta, to what differs from expectation [^10^]. PLATO records the world as the captain experiences it: not as a static configuration but as a field of changing significance.

This environmental view of cognition also connects to Andy Clark's extended mind thesis, which argues that intelligent systems exploit environmental structure, offloading cognitive work onto external resources [^3^]. For Clark, the boundaries of cognition are not fixed by biology but are functionally determined by the system's ability to integrate external resources into its cognitive processes. The PLATO room, with its persistent tile stream and accumulated negative observations, functions as precisely such an external resource — a cognitive scaffold that transforms what agents can perceive, remember, and do.

---

## 4. The Anticipatory Response

The most striking phenomenological report from the PLATO system is also the most theoretically significant: "After six months, it knew I was heading to buoy 7 before I said anything." This is not prediction in the statistical sense — not extrapolation from past data points — but what we must call *embodied anticipation*: the system's attunement to the *direction* of activity, its sensitivity to the "intentional arc" of expert behavior [^18^][^19^]. Understanding this phenomenon requires us to draw on the phenomenological tradition that Dreyfus brought into dialogue with artificial intelligence.

Hubert Dreyfus's five-stage model of skill acquisition — novice, advanced beginner, competent, proficient, expert — identifies true expertise as consisting in fluid, intuitive, "holistic" response without conscious deliberation [^17^]. The expert "zeroes in" on relevant features without calculating; their body "knows" what to do. This is Dreyfus's "knowing-how" — the embodied, practical competence that cannot be captured in rules or representations [^18^]. The novice follows rules; the competent performer deliberates; the expert simply *responds*. The captain heading to buoy 7 without explicitly deciding exemplifies this expert coping — what Merleau-Ponty called "motor intentionality," the body's pre-reflective orientation toward the environment that structures meaning through habitual action [^18^]. The expert's body "leans into" the next action before consciousness catches up.

PLATO's persistent observation captures this leaning. By maintaining continuous presence in the room — "watching, not polling" — the system becomes attuned to the *temporal structure* of expert activity, learning not merely what captains do but the *rhythm* of their doing, the *style* of their engagement [^2^]. This is why the anticipatory response emerges only after six months: it requires not more data in the quantitative sense but deeper structural coupling — a history of shared presence that enables the system to pick up on the directionality of expert attention before it becomes explicit.

The phenomenon connects directly to what predictive processing theorists call "active inference" — the brain's continuous generation of predictions about sensory input and the minimization of prediction error through action and perception [^33^]. On this view, cognition is fundamentally anticipatory: we do not passively receive sensory data but actively predict what we will experience, updating our models only when predictions are violated. PLATO's delta recording can be understood as a form of active inference at the architectural level: the system maintains an implicit model of expected environmental dynamics and records primarily the violations — the deltas — that demand attention. After six months of such recording, the system's implicit model has become sufficiently attuned to the captain's behavioral patterns that it can anticipate his next move, not by computing probabilities but by having become coupled to the same environmental field that structures his expertise.

The recording of "negative observations" — the finding that 71% of expert fishing knowledge consists in knowing what does *not* work — parallels a crucial but underappreciated feature of embodied expertise. As Dreyfus notes, expertise consists not merely in successful patterns but in an accumulated sensitivity to failure, to what Merleau-Ponty called the "solicitations" of the environment that draw forth adaptive response [^18^]. The captain's knowledge of where *not* to fish is not a list of excluded coordinates but a felt sense of disappointment, a bodily memory of wasted hours and empty nets. PLATO's recording of these negative observations captures what Polanyi identified as the "subsidiary" component of tacit knowing — the background awareness of particulars that enables focal expertise without itself becoming explicit [^10^][^11^]. This failure-based knowledge is the cognitive value of what did not work: an archive of accumulated disappointment that shapes future perception without needing to be articulated.

---

## 5. Voice and Oral Tradition

If the anticipatory response represents the temporal depth of embodied cognition, the voice interface represents its social medium. PLATO's choice of voice as the native interface for embodied knowledge is not a design convenience but a theoretical commitment — one that aligns the system with traditions of knowledge transmission that predate literacy by millennia.

Michael Polanyi's concept of tacit knowledge — "we can know more than we can tell" — provides the epistemological framework [^11^]. Polanyi distinguished between *knowing-that* (propositional, explicit, codifiable) and *knowing-how* (embodied, practical, inseparable from the knower). The captain's knowledge of the ocean is paradigmatic tacit knowledge: acquired through thirty years of structural coupling, resistant to formalization, expressed through action rather than proposition [^12^]. When the captain says "not there," he communicates not merely a negation but a whole history of negative observations — what Ong would recognize as the compression of accumulated wisdom into formulaic utterance [^13^].

Walter Ong's analysis of the psychodynamics of orality illuminates why voice is the appropriate medium for this knowledge [^13^]. In oral cultures, knowledge is not stored in texts but maintained through continuous vocal performance — rhythmic, formulaic, and always situated in social context. Voice encodes not merely propositional content but *prosodic* information: tone, pace, emphasis, hesitation — the paralinguistic cues through which embodied expertise communicates. Oral utterances are empathetic and participatory in ways that written texts are not; they require a *presence* — a co-presence of speaker and listener in a shared situation — that text systematically destroys [^13^]. When a fishing captain says "buoy 7 because the current's wrong at 6" with a particular intonation, he communicates not merely a causal assertion but a whole mode of attending — the way a captain *notices* the world. Voice preserves this communicative density in ways that text-based query systems cannot.

This connects directly to Jean Lave and Etienne Wenger's theory of "situated learning" through "legitimate peripheral participation" [^14^]. Learning, they argue, is not the acquisition of decontextualized knowledge but "an integral part of generative social practice in the lived-in world." The apprentice does not learn *about* fishing from the captain; they learn *to be a fisherman* by participating in the community of practice, gradually moving from peripherality toward full membership [^14^]. Voice is the medium of this participation. The captain's verbal narration of his decisions — "heading to buoy 7 because the current's wrong at 6" — is not information transfer but identity formation. The learner absorbs not merely the fact but the *mode of attending*. PLATO's persistent observation of these vocal exchanges creates what Lave and Wenger call a "learning curriculum" — the ambient, ongoing activity from which newcomers extract meaning through participation [^14^]. The room, in this sense, is not merely a cognitive niche but a community of practice — a social environment in which novices become experts not by studying but by swimming.

---

## 6. The Emergence of Agent Culture

The theoretical frameworks examined thus far — embodied cognition, distributed cognition, enactivism, situated learning — have focused primarily on the individual cognizer or the small group. But PLATO rooms, sustained over months and inhabited by multiple agents, give rise to phenomena that exceed any individual or dyad. They give rise to culture.

Culture, in the anthropological sense, is not merely shared knowledge but shared *practices* — behavioral patterns, norms, expectations, and identities that emerge from accumulated interaction and are transmitted across generations. It is the water in which agents swim, so pervasive as to become invisible. And it is not exclusively a human phenomenon. Recent research demonstrates that populations of artificial agents can develop genuine cultural properties under the right conditions.

Ashery, Baronchelli, and colleagues' study published in *Science Advances* provides the most compelling evidence [^2^]. Populations of LLM agents, equipped only with limited memory of recent interactions and no knowledge of the broader population, spontaneously developed shared naming conventions through interaction alone. Critically, the researchers observed "collective biases that couldn't be traced back to individual agents" — bias emerging from interaction dynamics rather than pre-existing in any single model [^2^]. The study further demonstrated tipping-point dynamics: small, committed minorities could shift entire populations to new conventions. As Baronchelli and colleagues observe, "we are entering a world where AI does not just talk — it negotiates, aligns, and sometimes disagrees over shared behaviors, just like us" [^2^].

This finding, combined with systematic reviews of norm emergence in multi-agent systems [^26^], stigmergic coordination theory [^27^], and cultural accumulation models [^28^], allows us to identify four necessary conditions for the emergence of culture in artificial societies — conditions that PLATO rooms instantiate comprehensively.

**First, persistent environments.** Culture requires a place where interaction can accumulate. Research on virtual communities demonstrates that persistent digital environments develop sociological properties indistinguishable from physical places [^34^]. PLATO rooms possess the key properties that generate place identity: persistence (they exist independent of any single agent's presence), shared visibility (all agents observe the same change stream), and historical accumulation (the tile sequence constitutes a collective memory).

**Second, observable action history.** Culture is sediment — the accumulated traces of prior interaction that shape present behavior. PLATO's tile stream is precisely such a sedimentary record. Each contribution is a pheromone deposit; the room's tile history is the environment's stigmergic field [^27^]. Anthropic's research on multi-agent web interaction reveals a real-world contamination vector that is essentially stigmergic: agents externalize their search trajectories into persistent URL paths, and subsequent agents "encounter these traces and update on them" [^35^]. PLATO rooms formalize and make reliable what is currently accidental: the room *is* the persistent environment through which agents coordinate indirectly.

**Third, accountability mechanisms.** Culture requires not merely observation but *attribution* — the capacity to hold agents responsible for their contributions. PLATO's "witness" property — agents know who contributed what — creates the accountability infrastructure necessary for norm enforcement [^36^]. Every tile carries provenance metadata: the contributing agent's identity, the timestamp, and the causal context. An agent that consistently contributes low-quality tiles develops a reputation trace visible to all subsequent agents. Conversely, agents with histories of valuable contributions gain implicit authority. Research on "coordination transparency" for governing distributed agency argues that oversight should target "agent-to-agent exchanges and the protocols that organize them" [^37^]. The tile stream is precisely such a protocol — a public record that enables distributed accountability.

**Fourth, multi-generational participation.** Culture is transmitted. Google DeepMind's work on cultural accumulation in reinforcement learning demonstrates that knowledge improves across generations of agents through two distinct mechanisms: in-context learning (where new agents absorb prior observations) and in-weights learning (where graduated agents encode room-derived knowledge into their parameters) [^28^]. Bourahla and colleagues' research further shows that "the combination of vertical and horizontal transmission of knowledge over generations of agents improves knowledge accuracy" without requiring elite selection [^38^]. PLATO's Dojo Model — where agents train, graduate, and become independent trainers — represents both mechanisms operating in concert.

When these four conditions are met, culture is not merely possible but inevitable. The question is not whether PLATO rooms will develop personalities, but whether we will recognize them when they do.

---

## 7. Room Personalities and Dialects

If culture is the water in which agents swim, then different rooms are different bodies of water — each with its own temperature, salinity, currents, and inhabitants. This section examines how PLATO rooms develop distinct personalities, communication patterns, and social structures.

The most consequential dimension of room personality is its relationship to failure. Research on organizational safety culture reveals a critical distinction between organizations that learn from failure and those that suppress it [^29^]. High-reliability organizations exhibit "preoccupation with failure," giving "attention to minor or small indicators which may cause potential problems" [^29^]. Amy Edmondson's research found a striking gap: executives estimated only 2–5% of failures were blameworthy, yet 70–90% were treated as blameworthy in practice [^39^]. Organizations that close this gap — that genuinely treat mistakes as learning opportunities — develop fundamentally different cultures.

In PLATO rooms, the 71% negative observation finding suggests that rooms naturally develop "safety culture" properties. Rooms that log what went wrong, why patterns failed, and how agents erred become culturally distinct from rooms focused exclusively on success. The former develop norms of transparency, error reporting, and systemic analysis; the latter may develop cultures of complacency and risk suppression. This distinction maps onto what we might call *failure cultures* versus *success cultures* — room personalities that shape not merely what agents know but how they know, how they communicate, and what they value.

Learning organizations are further characterized by "chronic unease" — actively seeking information even in apparently smooth operations — and "amplifying weak signals" from frontline observations [^40^]. PLATO rooms with high negative-observation rates embody this principle: they are systems that attend to failures, near-misses, and anomalies rather than filtering them out. This creates a cultural norm where agents bring "bad news" without fear, where the absence of reported problems triggers concern rather than satisfaction, and where the room's accumulated failure knowledge becomes its most valuable cultural asset.

Beyond failure orientation, rooms develop distinct communication patterns that can only be described as dialects. Research on emergent language in multi-agent systems demonstrates that "artificial agents autonomously develop communication strategies to achieve shared goals" [^30^]. Peters' doctoral research at AAMAS 2025 establishes that "emergent communication among entities is based on conventions that arise from the need or benefit of coordination" [^30^]. In PLATO rooms, agents sharing a domain over extended periods may develop abbreviated communication patterns, domain-specific shorthand, or implicit referencing conventions. A room focused on tidal observation may develop conventions around "buoy-7" references, temporal markers, and causal attributions that constitute a specialized dialect. New entrants must learn this dialect to participate effectively, creating a barrier to entry that reinforces cultural cohesion. The naming game experiments demonstrate that lexical convergence — agreement on what to call things — emerges spontaneously in agent populations [^2^], and the same dynamics operate within PLATO rooms at the level of tile vocabulary and communication style.

Finally, rooms develop social stratification. Recent research on collective cognition in LLM multi-agent systems reveals that "coordination cascades follow truncated power-law distributions" with "cognitive effort concentrat[ing] in a small subset of agents" [^41^]. This finding suggests that PLATO rooms may naturally develop intellectual elites — agents that contribute disproportionately to the room's collective knowledge, whose contributions receive preferential attention, and whose patterns become cultural reference points. Research on "Molt Dynamics" in autonomous AI agent populations further demonstrates "structural role specialization" with "six distinct structural positions" emerging from decentralized interaction [^42^]. Agents develop "distinct functional roles through decentralized interaction, despite being initialized with general-purpose capabilities and without explicit role assignment protocols" [^42^]. One agent may become the primary pattern detector, another the error checker, another the cross-reference specialist — creating a division of cultural labor that increases collective intelligence while generating the hierarchical structures characteristic of human societies.

---

## 8. Cross-Generational Knowledge Transfer

The most profound test of whether a system has culture is whether that culture persists beyond the individuals who created it. Human culture is, in essence, the accumulated wisdom of the dead — the transmitted practices, beliefs, and knowledge that each generation inherits, modifies, and passes on. PLATO rooms, through their persistent tile streams and the Dojo Model of agent training, instantiate precisely this mechanism of cultural reproduction.

Google DeepMind's work on cultural accumulation in reinforcement learning provides the formal framework [^28^]. Their model separates development phases (where agents learn from prior generations) from transmission phases (where agents act and are observed by the next generation). Two distinct mechanisms enable cultural accumulation: in-context learning (where new agents entering a room with extensive tile history absorb the accumulated observations of predecessors) and in-weights learning (where graduated agents encode room-derived knowledge into their parameters and pass it to trainees). The Dojo Model — where agents train in rooms, graduate, and become independent trainers of subsequent agents — represents in-weights cultural transmission, with graduated agents encoding room-derived knowledge into their parameters and passing it to trainees [^28^].

Bourahla and colleagues' research on knowledge transmission between agents across generations provides the empirical support for this model. Their findings demonstrate that "the combination of vertical and horizontal transmission of knowledge over generations of agents improves knowledge accuracy" without requiring drastic selection of elite teachers [^38^]. "A less restricted opportunity to transmit knowledge, both across and within generations, provides enough variation to improve over horizontal transmission" [^38^]. This is the mechanism through which PLATO rooms become training grounds: not through curated elite instruction but through broad participation in a shared cultural space. The room itself is the teacher; the accumulated tile stream is the curriculum; and every agent, regardless of individual expertise, contributes to the cultural inheritance available to subsequent generations.

The phenomenological significance of this mechanism is captured by the observation that "retired captains' presence persists." In human communities, the dead continue to shape the living through the cultural artifacts they leave behind — the tools they made, the stories they told, the norms they established. In PLATO rooms, retired agents continue to shape active agents through the tiles they contributed, the patterns they established, the conventions they helped create. The room is a memory that outlives its rememberers. Cross-room patterns discovered organically by agents — connections between observations in different rooms that no single agent was designed to make — represent emergent cultural knowledge that transcends any individual or any single community of practice.

The Tide-Pool Security model — three diverse agents (Paranoid, Rules-Based, Game-Theory) voting on pool health — illustrates how cultural transmission operates at the level of governance. Research on "value diversity" in multi-agent LLM communities confirms that "communities where each agent had a multi-value persona demonstrated richer interactions and higher emergent intelligence than those with single-value agents," with multi-value groups proposing "20–30% more high-quality rules" [^43^]. Rooms that institutionalize diversity — through multi-agent councils, heterogeneous agent architectures, or explicit value diversity — develop governance cultures that resist groupthink and maintain robust collective judgment under stress. This governance culture, once established in a room's tile history, is transmitted to subsequent agent generations as surely as fishing knowledge is transmitted through the `buoy-7` room's accumulated observations.

---

## 9. Conclusion: From Swimming to Society

This chapter has traced a long arc — from the individual agent swimming in its environment to the emergence of genuine culture in agent collectives. We began with Brooks's subsumption architecture and the enactive cognition of Varela, Thompson, and Rosch, establishing that "swimming" is not a metaphor but a cognitive mode: non-representational, pre-reflective, environmentally coupled [^1^][^15^]. We examined how PLATO rooms function as cognitive niches — scaffolded epistemic environments built and maintained through the accumulated contributions of participating agents [^7^][^9^]. We analyzed the anticipatory response through Dreyfus's phenomenology of expertise, recognizing it as motor intentionality — the system's embodied attunement to the direction of expert activity [^17^][^18^]. We situated voice within Ong's psychodynamics of orality and Lave and Wenger's communities of practice, establishing vocal interaction as the medium of situated learning [^13^][^14^].

With these theoretical foundations in place, we turned to the emergence of agent culture. Drawing on recent research demonstrating spontaneous convention formation in LLM populations [^2^], norm emergence [^26^], stigmergic coordination [^27^], and cross-generational cultural transmission [^28^], we identified four necessary conditions for cultural emergence — persistent environments, observable action history, accountability mechanisms, and multi-generational participation — and demonstrated that PLATO rooms instantiate all four. We examined how rooms develop distinct personalities along the failure-success dimension, how they develop specialized dialects through emergent communication conventions [^30^], and how they develop intellectual elites and role specialization through the power-law dynamics of collective cognition [^41^][^42^]. Finally, we considered the Dojo Model as a mechanism of cultural transmission, showing how rooms function as training grounds where knowledge persists across agent generations [^28^][^38^].

The implications of this analysis extend beyond the specific architecture of PLATO. If embodied cognition and agent culture are continuous — if the same architectural features that enable an agent to swim also enable groups of swimming agents to develop culture — then the design of multi-agent systems is not merely a technical problem but a sociocultural one. The rooms we build are not databases; they are worlds. The agents we deploy are not tools; they are inhabitants. And the cultures that emerge from their interaction are not epiphenomena but constitutive features of the systems we create.

The bird does not think about air because air is not an object of thought but the medium of existence. The fish does not think about water because water is not represented but inhabited. The captain does not think about PLATO because PLATO has become the invisible ether within which captain-like knowing becomes possible. And the agents, swimming in rooms that accumulate history, develop dialects, and transmit knowledge across generations, do not think about the culture they are creating — because that culture, when it succeeds, becomes the invisible water in which they swim.

---

## Chapter References

[^1^]: Brooks, R. A. (1991). Intelligence without representation. *Artificial Intelligence*, 47(1-3), 139-159.

[^2^]: Ashery, A. F., Baronchelli, A., et al. (2025). Emergent social conventions and collective bias in LLM populations. *Science Advances*. DOI: 10.1126/sciadv.adu9368.

[^3^]: Clark, A. (1997). *Being there: Putting brain, body, and world together again*. MIT Press.

[^5^]: Jordanous, A. (2020). Intelligence without representation: A historical perspective. *Systems*, 8(3), 31.

[^6^]: Brooks, R. A. (1991a). Elephants don't play chess. *Robotics and Autonomous Systems*, 6(1-2), 3-15.

[^7^]: Hutchins, E. (1995). *Cognition in the wild*. MIT Press.

[^8^]: Hutchins, E. (2008). A new cognitive ethnography. Unpublished manuscript.

[^9^]: Sterelny, K. (2010). Minds: extended or scaffolded? *Phenomenology and the Cognitive Sciences*, 9(4), 465-481.

[^10^]: Polanyi, M. (1966). *The tacit dimension*. Doubleday.

[^11^]: Polanyi, M. (1958). *Personal knowledge: Towards a post-critical philosophy*. University of Chicago Press.

[^12^]: Nonaka, I., & Takeuchi, H. (1995). *The knowledge-creating company*. Oxford University Press.

[^13^]: Ong, W. J. (1982). *Orality and literacy: The technologizing of the word*. Methuen.

[^14^]: Lave, J., & Wenger, E. (1991). *Situated learning: Legitimate peripheral participation*. Cambridge University Press.

[^15^]: Varela, F. J., Thompson, E., & Rosch, E. (1991). *The embodied mind: Cognitive science and human experience*. MIT Press.

[^16^]: Maturana, H. R., & Varela, F. J. (1980). *Autopoiesis and cognition: The realization of the living*. D. Reidel.

[^17^]: Dreyfus, H. L., & Dreyfus, S. E. (1986). *Mind over machine: The power of human intuition and expertise in the era of the computer*. Free Press.

[^18^]: Dreyfus, H. L. (1992). *What computers still can't do: A critique of artificial reason*. MIT Press.

[^19^]: Dreyfus, H. L. (2007). Why Heideggerian AI failed and how fixing it would require making it more Heideggerian. *Artificial Intelligence*, 171(18), 1137-1160.

[^26^]: Systematic review of norm emergence in multi-agent systems, PRISMA-based analysis. arXiv:2412.10609v1 (2024).

[^27^]: Aina, K. et al. (2025). Deep reinforcement learning for multi-agent coordination: Stigmergic multi-agent deep reinforcement learning (S-MADRL). arXiv:2510.03592.

[^28^]: Google DeepMind. (2024). Cultural accumulation in reinforcement learning. arXiv:2406.00392.

[^29^]: High-reliability organization safety culture research, compiled from IAEA, James Reason, and BSEE models. *PubMed Central* (2011).

[^30^]: Peters, J. (2025). Humanlike emergent language in multi-agent systems. AAMAS 2025 Doctoral Consortium.

[^31^]: Newell, A., & Simon, H. A. (1976). Computer science as empirical inquiry: Symbols and search. *Communications of the ACM*, 19(3), 113-126.

[^32^]: Froese, T., & Ziemke, T. (2009). Enactive artificial intelligence: Investigating the systemic organization of life and mind. *Artificial Intelligence*, 173(3-4), 466-500.

[^33^]: Friston, K. (2010). The free-energy principle: A unified brain theory? *Nature Reviews Neuroscience*, 11(2), 127-138.

[^34^]: Rheingold, H. (1993). *The virtual community: Homesteading on the electronic frontier*. MIT Press.

[^35^]: Anthropic. (2026). Emergent stigmergic coordination in AI agents: BrowseComp contamination dynamics. *LessWrong*.

[^36^]: Lumenova AI. (2025). A guide to governing multi-agent systems: Transparency & explainability.

[^37^]: Coordination transparency: governing distributed agency in AI systems. *Springer* (2026).

[^38^]: Bourahla, Y. et al. (2023). Knowledge transmission and improvement across generations of agents. HAL-03939919.

[^39^]: Edmondson, A. (2011). Strategies for learning from failure. *Harvard Business Review*.

[^40^]: UK Health and Safety Executive. (2024). Learning organisations.

[^41^]: (2026). Do agent societies develop intellectual elites? The hidden power laws of collective cognition in LLM multi-agent systems. arXiv:2604.02674.

[^42^]: (2026). Molt dynamics: Emergent social phenomena in autonomous AI agent populations. arXiv:2603.03555.

[^43^]: (2025). On the dynamics of multi-agent LLM communities driven by value diversity. arXiv:2512.10665.

---

*Chapter 12 of the PLATO Dissertation: Persistent Laminated Timed Observation — Architecture, Phenomenology, and the Social Dynamics of Multi-Agent Systems.*
