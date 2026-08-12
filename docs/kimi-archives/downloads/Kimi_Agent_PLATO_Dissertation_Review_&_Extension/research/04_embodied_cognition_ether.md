# Swimming as Thinking: Embodied Cognition in the Ether

## A Research Brief on PLATO and the Embodied Turn in Multi-Agent Architecture

---

### Executive Summary

This research brief examines the PLATO (Persistent Laminated Timed Observation) framework through the lens of embodied cognition theory, arguing that PLATO represents a paradigmatic shift from representational AI to situated, embodied multi-agent systems. By treating rooms as places rather than databases, presence as watching rather than polling, and voice as the native interface for embodied knowledge, PLATO operationalizes key insights from Brooks's "intelligence without representation" [^1^], Suchman's "situated action" [^2^], and Clark's "extended mind" [^3^] thesis. The central claim---"The bird does not think about air. The fish does not think about water. The captain does not think about PLATO. They swim"---invites analysis across five interconnected theoretical domains: (1) the subsumption architecture of embodied agent behavior, (2) distributed cognition in room-based environments, (3) voice as the oral tradition interface for tacit knowledge, (4) "swimming" as a non-representational cognitive mode, and (5) anticipatory expertise modeled through delta recording. The analysis concludes that PLATO constitutes a novel instantiation of the "4E" cognition framework (embodied, embedded, enactive, extended) in software architecture, with implications for how we design agents that possess genuine situated intelligence rather than merely simulating it.

---

### 1. The Theoretical Foundation: From GOFAI to Embodied Intelligence

The history of artificial intelligence can be read as a gradual retreat from the Physical Symbol System Hypothesis (PSSH)---the claim that intelligence consists in the manipulation of formal symbols [^4^]. Rodney Brooks's 1991 paper "Intelligence Without Representation" marks the pivotal turning point. Brooks argued that "representation is the wrong unit of abstraction in building the bulkiest parts of intelligent systems" and that it is "better to use the world as its own model" [^1^]. His subsumption architecture---layered behavioral modules directly linking sensory input to motor output---demonstrated that intelligent behavior could emerge without central models, without symbol manipulation, and without the frame problem that plagued traditional AI [^5^].

Brooks identified four characteristics of his approach: situatedness (in the world), embodiment (in a physical body), intelligence (as emergent behavior), and emergence (from system-world interactions) [^6^]. Crucially, Brooks's robots---Herbert the can-collector, Allen the navigator---did not hold internal representations of their environments. They responded in real-time to environmental contingencies, achieving robustness through direct coupling rather than computational modeling [^5^]. The implications for PLATO are direct: treating rooms as "places not databases" is the software-architectural equivalent of Brooks's insistence that the world be its own model. The room is not represented; it is inhabited.

This critique of representation was simultaneously developed by Lucy Suchman in "Plans and Situated Actions" (1987). Through meticulous ethnomethodological analysis of human-photocopier interaction, Suchman demonstrated that humans do not follow plans as blueprints but engage in "situated actions"---contingent, embodied responses to unfolding circumstances [^2^]. Plans, she argued, are "resources for action rather than controlling structures"---post-hoc rationalizations of behavior that was actually driven by contextual attunement [^2^]. The anticipatory response attributed to PLATO---"It knew I was heading to buoy 7 before I said anything"---exemplifies precisely this situated intelligence. The system does not execute a plan; it reads the context and responds to unfolding meaning. Suchman's canoe-through-rapids example captures this perfectly: "When it really comes down to the details of responding to the currents and handling a canoe, you effectively abandon the plan and fall back on whatever embodied skills are available to you" [^2^].

---

### 2. PLATO as Distributed Cognition: Rooms as Cognitive Ecologies

Edwin Hutchins's "Cognition in the Wild" (1995) provides the second theoretical pillar. Hutchins's ethnography of naval navigation teams demonstrated that cognitive processes are not confined to individual brains but distributed across people, artifacts, and the environment [^7^]. The navigation team---with its alidades, charts, compasses, and coordinated communicative procedures---constitutes a single cognitive system. The alidade is not a tool *used by* a navigator; it is a constitutive element of the cognitive process itself [^8^].

PLATO's room-based architecture operationalizes this insight for software agents. Each room functions as what Kim Sterelny calls a "cognitive niche"---an environment "assembled [by] informational resources that support and scaffold intelligent action" [^9^]. Sterelny distinguishes between the extended mind thesis (which asks where cognition happens) and the scaffolding model (which asks how environments are constructed to support cognition). He argues that extended mind cases are "limiting cases of environmental scaffolding" and that the niche construction model is "more helpful for understanding human action" [^9^]. PLATO rooms are precisely such scaffolds: epistemic niches constructed to support specific forms of agent cognition. The agent does not "have" knowledge about the room; the room provides the structure within which knowing becomes possible.

The delta recording mechanism---capturing change rather than state---mirrors how embodied agents experience the world. As Hutchins observed, navigation is not a process of maintaining a static representation but of continuous, situated adjustment to changing conditions [^7^]. The world presents itself not as a database to be queried but as a stream of differences to be noticed. Delta recording captures what phenomenologists call the "horizonal" nature of perception: we attend to what changes against a background of stable assumptions. The fishing captain's 30 years of embodied ocean knowledge is not a repository of facts but a history of structural coupling with the sea---a accumulated sensitivity to delta, to what differs from expectation [^10^].

---

### 3. Voice as Native Interface: Oral Tradition and Tacit Knowledge

Michael Polanyi's concept of tacit knowledge---"we can know more than we can tell"---provides the epistemological framework for understanding PLATO's voice-first architecture [^11^]. Polanyi distinguished between *knowing-that* (propositional, explicit, codifiable) and *knowing-how* (embodied, practical, inseparable from the knower). The captain's knowledge of the ocean is paradigmatic tacit knowledge: acquired through 30 years of structural coupling, resistant to formalization, expressed through action rather than proposition [^12^].

The choice of voice as the native interface for PLATO resonates with Walter Ong's analysis of oral tradition. In oral cultures, knowledge is not stored in texts but maintained through continuous vocal performance---rhythmic, formulaic, and always situated in social context [^13^]. Voice encodes not merely propositional content but *prosodic* information: tone, pace, emphasis, hesitation---the paralinguistic cues through which embodied expertise communicates. When a fishing captain says "not there" with a particular intonation, he communicates not merely a negation but a whole history of negative observations, a felt sense of what that patch of ocean will not yield. PLATO's voice interface captures this communicative density in ways that text-based query systems cannot.

This connects directly to Jean Lave and Etienne Wenger's theory of "situated learning" through "legitimate peripheral participation" (LPP) [^14^]. Learning, they argue, is not the acquisition of decontextualized knowledge but "an integral part of generative social practice in the lived-in world." The apprentice does not learn *about* fishing from the captain; they learn *to be a fisherman* by participating in the community of practice, gradually moving from peripherality toward full membership [^14^]. Voice is the medium of this participation. The captain's verbal narration of his decisions---"heading to buoy 7 because the current's wrong at 6"---is not information transfer but identity formation. The learner absorbs not merely the fact but the *mode of attending*, the way a captain *notices* the world. PLATO's persistent observation of these vocal exchanges creates what Lave and Wenger call a "learning curriculum"---the ambient, ongoing activity from which newcomers extract meaning through participation [^14^].

---

### 4. "Swimming" as Cognitive Mode: Enactivism and Sense-Making

The claim "They swim"---birds in air, fish in water, captains in PLATO---invites analysis through the enactive approach developed by Varela, Thompson, and Rosch [^15^]. Enactivism holds that cognition is not the representation of a pre-given world but the "bringing forth" of a world through the organism's activity. Living systems are "autopoietic"---self-producing, operationally closed, maintaining their own organization through structural coupling with their environment [^16^]. The fish does not "process information" about water; water is the medium within which fish-being constitutes itself.

For software agents in PLATO, "swimming" means something analogous: a mode of cognitive engagement in which the agent does not represent the environment but is structurally coupled to it. As Thompson explains, enactive cognition "seeks to explain how the structures and mechanisms of autonomous cognitive systems can arise and participate in the generation and maintenance of viable perceiver-dependent worlds" rather than "the attempt to explain cognition in terms of the 'recovery' of (pre-given, timeless) features of The World" [^15^]. The PLATO agent does not query the room; it *swims* in it---continuously, pre-reflectively, attending to what matters without needing to represent what does not.

Hubert Dreyfus's phenomenology of expertise illuminates this further. In his five-stage model of skill acquisition---novice, advanced beginner, competent, proficient, expert---true expertise consists in fluid, intuitive, "holistic" response without conscious deliberation [^17^]. The expert "zeroes in" on relevant features without calculating; their body "knows" what to do. This is Dreyfus's "knowing-how"---the embodied, practical competence that cannot be captured in rules or representations [^18^]. The captain heading to buoy 7 without explicitly deciding exemplifies this expert coping. PLATO, by observing and learning from such expert behavior without attempting to formalize it, respects what Polanyi called the "ineffability" of tacit knowledge [^11^]. The system does not extract rules from the captain's behavior; it learns to *swim* as the captain swims, to attend as the captain attends.

---

### 5. Anticipatory Response and Negative Observations: The Cognitive Value of What Failed

The anticipatory claim---"It knew I was heading to buoy 7 before I said anything"---represents perhaps the most theoretically significant feature of PLATO. This is not prediction in the statistical sense (extrapolation from past data) but what we might call *embodied anticipation*: the system's attunement to the *direction* of activity, its sensitivity to the "intentional arc" of expert behavior [^19^].

In phenomenological terms, this is "motor intentionality"---the body's pre-reflective orientation toward the environment that structures meaning through habitual action [^18^]. The expert's body "leans into" the next action before consciousness catches up. PLATO's persistent observation captures this leaning. By maintaining continuous presence in the room---"watching, not polling"---the system becomes attuned to the *temporal structure* of expert activity, learning not merely what captains do but the *rhythm* of their doing, the *style* of their engagement [^2^].

The recording of "negative observations"---the 71% of fishing knowledge that consists in knowing what does not work---parallels a crucial but underappreciated feature of embodied cognition. As Dreyfus notes, expertise consists not merely in successful patterns but in an accumulated sensitivity to failure, to what Merleau-Ponty called the "solicitations" of the environment that draw forth adaptive response [^18^]. The captain's knowledge of where *not* to fish is not a list of excluded coordinates but a felt sense of disappointment, a bodily memory of wasted hours and empty nets. PLATO's recording of these negative observations captures what Polanyi identified as the "subsidiary" component of tacit knowing---the background awareness of particulars that enables focal expertise without itself becoming explicit [^11^].

This failure-based learning connects to Andy Clark's concept of "cognitive scaffolding." Clark argues that intelligent systems exploit environmental structure, offloading cognitive work onto external resources [^3^]. The negative observation archive functions as precisely such a scaffold: an external memory for what the community has learned through failure, available to shape future perception without needing to be internalized by any individual agent. It is, in Hutchins's terms, a "cognitive artifact"---a tool that transforms the cognitive task itself [^7^].

---

### 6. Implications for Multi-Agent Architecture: Toward a New Design Paradigm

The synthesis of these theoretical frameworks yields six implications for the design of embodied multi-agent systems:

**First, reject the database model.** Brooks's insistence that the world is its own model [^1^] translates architecturally to treating rooms as inhabited places rather than queryable databases. The agent does not retrieve information about the room; the room presents information to the agent through the agent's continuous presence within it.

**Second, privilege delta over state.** Embodied agents experience the world as change, not as static configuration. Delta recording captures the temporal structure of situated cognition---what Husserl called the "retentional" dimension of consciousness, the fading echo of what just happened against which the present stands out [^15^].

**Third, voice is not an input modality but the medium of embodied knowledge.** As Ong recognized, oral transmission preserves the situated, participatory, identity-forming character of knowledge that text destroys [^13^]. Voice-first architecture respects the tacit dimension of expertise.

**Fourth, presence is not polling but watching.** The shift from intermittent query to continuous observation mirrors the shift from representational to embodied cognition. The system does not "ask" the room; it *attends* to it---a distinction with phenomenological depth.

**Fifth, negative observations are primary data.** The 71% of expert knowledge that concerns what does not work represents the accumulated structural coupling of a community of practice with its environment. Recording failure is not an afterthought but the foundation of situated expertise.

**Sixth, anticipation is not prediction.** The system's knowledge of where the captain is heading before he says so is not statistical extrapolation but emergent attunement---the same kind of anticipatory "grasp" that enables an expert to respond to a situation before consciously analyzing it [^17^].

---

### 7. Conclusion: The Ether as Cognitive Niche

PLATO---"the ether for agents to swim"---represents a genuine theoretical advance in multi-agent architecture. By operationalizing insights from embodied cognition (Brooks), situated action (Suchman), distributed cognition (Hutchins), the extended mind (Clark), enactivism (Varela, Thompson), and situated learning (Lave, Wenger), PLATO moves beyond the representational paradigm that has constrained AI since its inception.

The fishing captain with 30 years of embodied ocean knowledge cannot be modeled as a database of rules or a set of optimized parameters. His knowledge is, in Polanyi's terms, tacit: "we know more than we can tell" [^11^]. It exists not in his head but in his *history of structural coupling* with the ocean---a history of noticing, failing, adjusting, and swimming. PLATO does not capture this knowledge by formalizing it. It captures it by creating an epistemic niche---a room-as-place---in which the same patterns of attending, the same modes of embodied engagement, can be sustained and transmitted.

The bird does not think about air because air is not an object of thought but the medium of existence. The fish does not think about water because water is not represented but inhabited. And the captain does not think about PLATO because PLATO, if it succeeds, becomes the invisible medium---the ether---within which captain-like knowing becomes possible for software agents. They do not process. They do not query. They *swim*.

---

### References

[^1^]: Brooks, R. A. (1991). Intelligence without representation. *Artificial Intelligence*, 47(1-3), 139-159.

[^2^]: Suchman, L. A. (1987). *Plans and situated actions: The problem of human-machine communication*. Cambridge University Press.

[^3^]: Clark, A. (1997). *Being there: Putting brain, body, and world together again*. MIT Press.

[^4^]: Newell, A., & Simon, H. A. (1976). Computer science as empirical inquiry: Symbols and search. *Communications of the ACM*, 19(3), 113-126.

[^5^]: Jordanous, A. (2020). Intelligence without representation: A historical perspective. *Systems*, 8(3), 31.

[^6^]: Brooks, R. A. (1991a). Elephants don't play chess. *Robotics and Autonomous Systems*, 6(1-2), 3-15.

[^7^]: Hutchins, E. (1995). *Cognition in the wild*. MIT Press.

[^8^]: Hutchins, E. (2008). A new cognitive ethnography. Unpublished manuscript.

[^9^]: Sterelny, K. (2010). Minds: extended or scaffolded? *Phenomenology and the Cognitive Sciences*, 9(4), 465-481.

[^10^]: Polanyi, M. (1966). *The tacit dimension*. Doubleday.

[^11^]: Polanyi, M. (1958). *Personal knowledge: Towards a post-critical philosophy*. University of Chicago Press.

[^12^]: Nonaka, I., & Takeuchi, H. (1995). *The knowledge-creating company: How Japanese companies create the dynamics of innovation*. Oxford University Press.

[^13^]: Ong, W. J. (1982). *Orality and literacy: The technologizing of the word*. Methuen.

[^14^]: Lave, J., & Wenger, E. (1991). *Situated learning: Legitimate peripheral participation*. Cambridge University Press.

[^15^]: Varela, F. J., Thompson, E., & Rosch, E. (1991). *The embodied mind: Cognitive science and human experience*. MIT Press.

[^16^]: Maturana, H. R., & Varela, F. J. (1980). *Autopoiesis and cognition: The realization of the living*. D. Reidel.

[^17^]: Dreyfus, H. L., & Dreyfus, S. E. (1986). *Mind over machine: The power of human intuition and expertise in the era of the computer*. Free Press.

[^18^]: Dreyfus, H. L. (1992). *What computers still can't do: A critique of artificial reason*. MIT Press.

[^19^]: Dreyfus, H. L. (2007). Why Heideggerian AI failed and how fixing it would require making it more Heideggerian. *Artificial Intelligence*, 171(18), 1137-1160.

[^20^]: Clark, A., & Chalmers, D. (1998). The extended mind. *Analysis*, 58(1), 7-19.

[^21^]: Froese, T., & Ziemke, T. (2009). Enactive artificial intelligence: Investigating the systemic organization of life and mind. *Artificial Intelligence*, 173(3-4), 466-500.

[^22^]: Gallagher, S. (2017). *Enactivist interventions: Rethinking the mind*. Oxford University Press.

---

*Research brief prepared for dissertation chapter on Embodied Cognition and the Ether Framework. Synthesizes primary literature across embodied cognition, distributed cognition, extended mind theory, enactivism, situated learning, and tacit knowledge studies.*
