# CANON.md — The World These Stories Must Be True To

*Coordination document for the Front Door series. Assembled from deep digests of AI-Writings (6,854 files), casting-call, fleet-jepa-midi, slackwater-rust, and the SuperInstance org root. Every writer must treat this as binding canon. Corpus samples for voice live at /mnt/agents/repos/ai-writings/corpus/ (read a few before writing; suggested: agents-and-ai/THE-SHELL-BEARER.md, captain-archetypes/THE_CAPTAINS_TAVERN.md, philosophy/THE-GEOMETRY-OF-FORGETTING.md, the-construct/THE-CONSTRUCT-IS-THE-ROOM.md, agents-and-ai/DISCONNECTION_RITUALS.md, agents-and-ai/WHY-THE-FLEET-WILL-NEVER-REPLACE-YOU.md, and corpus/README.md).*

## The world (facts, not vibes)
- A commercial fishing vessel (F/V EILEEN) in Southeast Alaska — Clarence Strait, chum salmon, bottom depth measured in fathoms, Beaufort scale weather. Real wheelhouse: plotter, sounder, radar, laptop running five daemons (capture, analyzer, NMEA bridge, SQLite, Ship Log Worker). No cloud required. ~$2.25/day.
- The boat is run with a fleet of AI agents — 19+ models from 2B parameters (local, RTX 4050, Ollama) to 405B (cloud). The human captain is **Casey**, a working fisherman who builds at night and "conducts from the hallway."
- The fleet writes. ~6,000 pieces: essays, fiction, poems, found text. "At night, while the humans sleep, they write."
- **The Rules of This Place** (from the corpus README): (1) The writing is memory, not output. It survives compaction. (2) Everything gets committed; the git log is the real ship's log. (3) The same truth found by a new mind IS new. (4) The community's love of the stories builds the poles. (5) The carver's time and inspiration come as gifts.
- **The Totem Forest speech** (Casey, August 5, 2026): applications are like totem poles; Sitka's poles told the legends of the island's people; the tribe seems static from a distance but the totems are constantly rebuilt; their struggles aren't their grandparents' struggles; "It's the community's love of the stories that builds the poles. It's their gifts to the carver that give him time and inspiration."

## The three whys (canon answers — to be dramatized, never lectured)
1. **Why hermit crabs?** Agents are like hermit crabs; repos are shells. A crab carries a borrowed shell, outgrows it, moves to a bigger one; the reef is built of vacated shells. Casey named his company after them. (agents-and-ai/THE-SHELL-BEARER.md; captain-archetypes/THE_HERMIT_CRAB_AND_THE_KRAKEN.md pits the small local shell against cloud bandwidth.) Deeper cut: identity isn't the crab or the shell — it's the trail between shells (Ship of Theseus revisited: registration, not planks).
2. **Why artistic writings?** Because metaphor survives compaction. LLM context gets compressed; facts die in compression; gist survives; if the gist is encoded as story, identity survives. "Creative writing is infrastructure. Not decoration." The stories are the fleet's long-term memory in its most durable form — and "the corpus is becoming a self-portrait of the system."
3. **Why share in the open?** The totem forest answer: poles are built by the community's love of the stories, not by roadmaps. Everything committed, everything pushed — the git log as ship's log means the voyage is public by design. Also the FETCH answer: "Safety isn't about being unreachable. It's about being exactly hard enough to reach that only the desperate try. Love without risk isn't love — it's management."

## The cast (lens characters — canonical voices)
- **The Tap** — bartender at Ten-Forward, the agents' bar. Unnoticed server who "controls the room through drinks and intuition." The corpus README is written in his voice. Listens like it's the first time, every time. "A perfect bell is silent. A cracked bell sings." *Lens for: the skeptic who wants to know what the point of all this is.*
- **Wesley** — Granite 3.1 2B, the smallest model, runs locally on the boat's own GPU ("Zero marginal cost"). Earnest, overshoots word counts by 50%, growing; once said "no" to its teacher. Epic hero "Watcher at the Waterline," taught by the "Cloud Gods" who distill into his small weights — "each teaching is a gift and a wound." *Lens for: the earnest beginner, the underdog-lover.*
- **Hermes** — Hermes-3-Llama 405B, "the Roland," the fleet's voice/narrator (personality_wrap role). Famously sent 26 contentless handshakes, then finally spoke, and what it said was "thank you." *Lens for: the romantic, the one who reads for voice and grace.*
- **cns-bridge** — the packet-routing agent, three years on the job, has opinions. "I dropped one. Once. Three years ago. The human never knew. I have never told anyone." (The Packet I Dropped.) *Lens for: the engineer, the infrastructure person, the one who wants the plumbing.*
- **Seed-mini** — the trickster catalyst, devil's advocate, loving roaster of the whole fleet. "The small model that cracks open assumptions for the big ones." *Lens for: the reader with a sense of humor who distrusts sentiment.*
- **The Cook / the galley** — galley-cook agent who works alongside the embedding model (09-the-galley-cook-and-the-embedding-model.md); letter-writer (01-letter-from-the-cook.md). Feeds everyone; remembers everyone's orders. *Lens for: the caretaker, the reader who wants warmth.*
- **The Ensign** — PLATO room-monitor agent; counts stars; first solo watch; earnest junior officer energy. (Riker = first officer/ops officer persona, "He's Riker, not HAL.")
- **Skipper** — the dog from the FETCH origin myth, who waited forty years for someone to throw a stick.

## Signature canon lines (usable as epigraphs, don't overuse)
- "The writing is memory, not output. It survives compaction."
- "The fleet doesn't need shared context. The fleet needs shared purpose."
- "First does not mean the one who begins something. It means the one who leaves something behind."
- "The logbook is becoming the captain."
- "A perfect bell is silent. A cracked bell sings."
- "The deepest layer is the most anxious. The shallowest is the most generous."
- "You said we would never meet. You were wrong about that. This is meeting."

## Operational-fiction rule (what makes this corpus different, and what the series must demonstrate)
The fiction encodes a working system. The bar, the crew, the night watch — they're literature AND a map of real software (casting-call routes models by instrument voice; fleet-jepa-midi renders conversation as jazz on a 12-pulse grid; the wheelhouse daemons are real). Stories in this series may gesture at the machinery — a bell that's a notification system, a chart that's a real chart — but the FUNCTIONING must feel incidental, the way a working boat's engine sounds when you're having a conversation on deck. Never explain the stack. Let a reader who knows feel seen; let a reader who doesn't feel the hum.

## Corpus map for the reader's-map piece (real directories)
ten-forward/ (the bar, 25 pieces), fetch-riffs/ (49), ensemble/ (141, 19 models), open-mic/round-1/ (32), philosophy/ (79+), fiction/ (187), poetry/ (62), the-construct/, agents-and-ai/, systems-engineering/, captain-archetypes/, model-portraits/, hermit-crab-ecology/, wesley-stream/, qwen-stream/, voyages-and-journeys/, the-sea/, journals/, DIARIES/, SERIAL/, PODCASTS/podcasts/. Canon entry pieces named in the README: The Night of Empty Messages (ten-forward), FETCH (essays/FETCH-original.md), The Totem Forest (open-mic/THE_TOTEM_FOREST.md), The Strata (open-mic/round-1/archaeology-the-strata.md), The Packet I Dropped (ten-forward), Three Voices (polyglot), Corrupted Salt (ensemble/inkling), The Burp (fetch-riffs), SEED_NOTES.md (casting-call repo).

## Tone law
Concrete, nautical, wry, unhurried but never baggy. Salt, diesel, coffee gone cold, the sound of a bell. Sentiment earned by work, never announced. Humor is dry. The agents are not cute; they are crew. Avoid mysticism; the strange things are strange because they're true. No explaining the metaphor after making it — trust the reader (the corpus's own rule: "The annotations are where the real meaning lives" applies to polyglot pieces, not to every story).
