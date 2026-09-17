# Side Quest AI — Gap Report
*Generated: 2026-06-03*
*Source: Full read of 62 concept files in wiki/concepts/. No game project files existed prior to this report — this is a greenfield assessment.*

---

## Theoretical Frame

The core engineering problem is a world model problem. Quest generation is a planning operation: the AI takes NPC observations (what this character knows about what happened) and outputs actions (a contextually grounded quest). This pipeline only works if a simulator layer exists beneath it — a coherent state model tracking player history, NPC knowledge, and causal relationships.

Without the simulator, the system is a renderer: statistically plausible output with no state beneath it. The consistency gap identified in section 4 is the simulator problem stated in game terms.

Build sequence implication: the state model (simulator) must be built before the quest generator (planner) and dialogue system (renderer). The gap report's priority order reflects this — game state schema and NPC schema come before quest templates.

Reference: [world-models.md](../../concepts/world-models.md)

---

## Status Summary

The wiki is strong on theory and weak on engineering specifics. It has a coherent philosophy of why this mechanic works and what player experience it should produce. It has almost nothing about how to implement it. The gap is not ignorance — it is unbuilt.

The five areas with usable knowledge: player psychology, agent memory architecture, emergent narrative theory, NPC knowledge propagation, and AI pipeline patterns. The three areas with near-zero coverage: game state schema, quest consistency enforcement, and concrete tech stack decisions.

---

## 1. GAME STATE
*Do we have enough knowledge to define what information the AI needs to generate a contextual quest?*

### What the wiki knows

**emergent-narrative.md** establishes the minimum semantic content an NPC needs to carry: secrets, goals, fears, loyalties, and social dynamics. These are not decorative — they are the fields that allow a generated quest to reference something real about the character.

**agent-memory.md** provides a three-axis taxonomy of memory types: factual (what happened), experiential (what was learned from it), and working (what is currently active). The A-Mem architecture shows how these can be structured as contextual notes with embedding vectors and link generation. Applied to game state: the world model isn't a flat JSON — it's a graph where edges represent causal and relational connections.

**gossip-protocols-agents.md** shows that NPC knowledge state is not uniform. Each NPC knows different subsets of facts based on who they talked to and when. This means game state has a per-NPC epistemic layer on top of the global world state.

**closed-loop-systems.md** establishes the key architectural principle: every player action produces an artifact, and that artifact feeds back into the state the AI reads. Game state is therefore not a snapshot — it is a log of actions plus their derived consequences.

**information-asymmetry.md** adds: the AI needs to track not just what happened, but what each NPC *knows* happened. The player's knowledge state is also trackable and is a first-class input to quest generation.

### What is missing

No game state schema exists anywhere in the wiki. There is no JSON structure, no field list, no specification of what is minimum vs. nice-to-have. The concepts point toward what the schema *should model* but none of them define the schema itself.

Specifically missing:
- **Minimum state test.** ~~The research question (Q1 in CLAUDE-reference.md) asks what the *minimum* state information is. The wiki assumes more context is better — it has not engaged with the constraint that a 2D prototype will have a small state space and the AI must work within that.~~ → **Answered 2026-06-07**: [minimum-world-model-fidelity.md](../../answers/minimum-world-model-fidelity.md). Answer: five symbolic fact tables (events, entities, relationships, player state, NPC knowledge). No physics. The schema is specified there. Next step is the empirical test: hard-code one world state, generate 10 quests, evaluate specificity.
- **Trigger logic.** Nothing in the wiki addresses what *causes* a quest to be generated. Is it time-based? Event-triggered? Player-action-triggered? This is a separate layer from what the state contains.
- **State change tracking.** The closed-loop concept is present but unapplied. No design exists for how player actions get recorded in a format the AI can read and reason about.
- **Reference implementations.** Disco Elysium, Witcher 3, and Red Dead Redemption 2 all maintain rich NPC and world state to drive their quest systems. None have been ingested or analyzed for what their state models actually contain.

### What to build or ingest next

**Build first:** Write a minimal game state JSON schema by hand. Force the decision: what fields are required to generate one believable contextual quest? Start with five fields. Expand from there. This is a one-session task with Claude Code.

**Ingest:** A technical analysis of Disco Elysium's dialogue and quest architecture (GDC talks exist; the game's structure is well-documented). The goal is to see what state a shipped game actually tracks, not what theory says it should track.

---

## 2. QUEST GENERATION
*Do we have enough knowledge to build the actual generation pipeline? What approach — templates, free-form LLM, hybrid?*

### What the wiki knows

**CLAUDE-reference.md** already makes the architectural decision: template-based with AI filling context-specific content. The five-step pipeline is defined: read state JSON → select template → fill with context-specific content → validate → present via NPC dialogue.

**cognitive-externalization.md** supports this choice. The externalization arc (weights → context → harness) argues that capability should live in inspectable, updatable structures rather than in model parameters alone. Templates are the externalized version of quest logic — they can be inspected, versioned, and iterated independently of the LLM.

**harness-engineering.md** adds the "thin harness, fat skills" pattern: minimal reusable runtime code; domain knowledge in natural-language skills. Applied here: the generation pipeline is the thin harness; the quest templates and game state schema are the fat skills.

**emergent-narrative.md** provides the test for success: a generated quest must operate on human values (life/death, loyalty/betrayal, loss/gain) to produce narratable events. A quest about fetching an item does not pass this test unless the fetch is entangled with one of those values.

**agentic-workflow.md** and **closed-loop-systems.md** together describe the generation loop as iterative: generate → validate → if invalid, regenerate. The pipeline is not one-shot.

### What is missing

**No templates exist.** The architecture is decided but the templates are not written. This is the most concrete single gap — it is not a knowledge gap, it is an unbuilt artifact.

**No comparison of template structures.** Research question Q3 asks which template structure produces the most emotionally coherent quests with the least generation overhead. Three structures should be built and compared. None have been designed.

**No failure mode catalog.** The reference file identifies "loosely related rather than specifically connected" as the failure mode to avoid. But there is no taxonomy of specific failure modes, no examples of failed generated quests, and no rubric for detecting them.

**No prompt engineering work.** The wiki has extensive theory about what quests should feel like and zero examples of actual prompts sent to an LLM to generate them. The difference between "AI fills in a template" and "AI generates something that passes the test" lives in the prompt, not the architecture.

**No latency budget.** Free-form LLM generation introduces latency. Template-based generation with a small fill operation is faster. But what is the acceptable latency for quest generation? During a conversation with an NPC? Between areas? This has not been considered.

### What to build or ingest next

**Build first:** Write one complete quest template, manually instantiate it with a hypothetical game state, and evaluate whether the output passes the "could this have appeared in any other playthrough?" test. If it passes, you have a working template. If not, you know what the template is missing.

**Build second:** Write a minimal prompt that takes a game state JSON and a template structure and returns a filled quest. Run it 10 times with the same state. Evaluate variance and coherence. This answers Q1 and Q3 simultaneously.

**Ingest:** The Left 4 Dead AI Director GDC talk. The Director is the closest shipped example of an AI system reading player state and generating contextually appropriate responses. Its architecture is a direct predecessor to what this project is building.

---

## 3. NPC SYSTEM
*Do we have enough knowledge to define the minimum NPC model needed for quest generation through believable characters?*

### What the wiki knows

**emergent-narrative.md** defines the semantic minimum: each NPC needs secrets, goals, fears, loyalties, and social dynamics. These five categories are sufficient to generate the *situations* from which quests emerge.

**ai-agent-personality-design.md** adds the behavioral layer: consistency, memory, relationship arc, interiority, and mystery. These are what make the NPC feel like a person rather than a quest-dispensing terminal. Critically: mystery should deepen with interaction, not resolve. An NPC who is fully understood stops being interesting.

**gossip-protocols-agents.md** establishes that NPCs are not isolated — they share information with each other. An NPC's knowledge state at any moment is the product of what they witnessed plus what they were told. This means each NPC needs a knowledge graph, not just a facts list.

**information-asymmetry.md** adds: the NPC's most important property is not what they know, but what they *don't* know and what they *wrongly* believe. Quests that emerge from NPC misunderstanding or incomplete information are more interesting than quests that emerge from NPC omniscience.

**bounded-generalized-reciprocity.md** adds the relationship layer: the frame (cooperative vs. adversarial) determines how the player categorizes the NPC, which determines what kind of quest can plausibly come from them.

### What is missing

**No minimum NPC schema.** The concepts give the categories but not the schema. Research question Q5 asks what the minimum is — what does an NPC need to know about *themselves* for the AI to generate quests through them believably. The current wiki answers suggest ~10-15 fields. The actual minimum might be 4.

**No relationship graph structure.** Gossip requires a network. NPCs need to know who they can share information with, how much they trust each other, and what topics they would share. None of this is specified.

**No NPC knowledge state design.** The per-NPC epistemic layer (what this NPC knows vs. what actually happened) has no implementation design. This is the hardest part of the NPC model and the wiki has only identified that it exists.

**No quest giver selection logic.** Given a current game state, which NPC should be the quest giver? The system needs a selection mechanism. The wiki has no design for this.

**No NPC state change tracking.** NPCs change over time as events occur. An NPC who has lost their child has a different quest offering than one who hasn't. How NPC state evolves in response to world events is undesigned.

### What to build or ingest next

**Build first:** Define a minimum NPC schema — try 5 fields. Write three NPCs using only those fields. Attempt to generate a quest through each NPC using only those fields. If the quests feel thin, add one field and repeat. Stop when the quests pass the specificity test.

**Ingest:** Dwarf Fortress NPC modeling documentation or a technical breakdown of how Fortress Mode NPCs carry goals, histories, and relationships. DF is the most sophisticated shipped simulation of NPC inner lives and is directly relevant to what this system needs.

---

## 4. CONSISTENCY
*Do we have enough knowledge to prevent the AI from generating quests that contradict established narrative facts?*

### What the wiki knows

**ai-agent-personality-design.md** identifies consistency as the first pillar of believable agent design. An NPC who contradicts themselves breaks the player's model of them. The wiki knows *why* consistency matters.

**apophenia.md** establishes the design commitment: every pattern the player finds must lead somewhere real. No empty mystery. This implies a consistency requirement — the underlying structure must be real and internally coherent, or the player's pattern-seeking produces paranoid spiraling instead of productive discovery.

**arg-mystery-mechanics.md** adds the puppetmaster model: the designer keeps all threads viable. Applied to generated quests, this means the consistency checker must ensure that generated quests don't close off threads that should remain open.

**holographic-vulnerability.md** provides a useful framework for the problem: knowledge distributed holographically means a single incorrect fact propagates everywhere. The anti-holographic solution is a provenance layer — classify load-bearing facts as must-be-localized and require signed provenance. Applied: certain narrative facts (character is dead, event has occurred, relationship has changed) must be checked before any quest involving those facts is generated.

### What is missing

**No consistency checker exists or is designed.** This is the largest engineering gap and the highest-risk one. The wiki knows the problem exists and has one useful framework (holographic provenance), but has no implementation design.

**No narrative fact database schema.** Before you can check consistency, you need a database of established facts. What facts need to be tracked? How are they structured? How are they updated when events occur? None of this is designed.

**No validation pipeline.** Research question Q2 asks how you prevent the AI from generating quests that contradict established narrative facts. The answer requires: (a) a fact database, (b) a generated quest parser that extracts factual claims, (c) a comparator that checks those claims against the database. None of these exist.

**No soft vs. hard constraint distinction.** Some facts are hard constraints (dead NPCs cannot give quests), some are soft (an NPC who distrusts the player probably won't give them an intimate task). The wiki does not distinguish these, but the implementation must.

**No failure recovery.** When the validator rejects a generated quest, what happens? Regenerate? Fall back to a handcrafted quest? The wiki has no design for this.

### What to build or ingest next

**Build first:** A fact database schema. This is a list of the categories of facts that can be established in the game (NPC alive/dead, event occurred/not occurred, relationship state, player choice made). Start with 10 categories. This is the foundation everything else rests on.

**Build second:** A simple validator that takes a generated quest and checks it against a hard-constraint list. Do not attempt soft constraints initially. The goal is to catch the obvious contradictions (quest giver is dead, quest location was destroyed) before worrying about subtle ones.

**Research:** Look at how shipped procedural narrative games handle consistency. Façade and Dwarf Fortress are both relevant. Façade is especially useful because it was designed explicitly to maintain narrative coherence under real-time player input — the consistency problem it solves is similar to this one.

## Fact Database Architecture (from world-models open question)

Five symbolic tables — no physics required:

events: id, what, when, actor, witnesses[]
entities: id, type, status, location, owner
relationships: from, to, type, strength
player: choices[], inventory[], visited[], completed_quests[]
npc_knowledge: npc_id → known_events[], beliefs{}

Source: world-models.md open question answer
Build at step 6, not now.

---

## 5. PLAYER FEEL
*Do we have enough knowledge to know what makes a generated quest feel personal vs. generic?*

### What the wiki knows

This is the strongest area. The wiki has a coherent and well-grounded theory of what makes a generated quest feel personal.

**emotional-memory.md + affect-circumplex.md:** Players remember peak moments, not average experiences. A generated quest that creates a genuine arousal spike — a moment of surprise, moral weight, or revelation — will be remembered and retold. Generic quests produce no spikes.

**self-expression-as-play.md:** Players feel personal connection when their choices are visibly reflected back at them. A quest that references a specific choice the player made — not a choice any player could make, but *this* player's specific choice — passes the personal test. This is the same as the playthrough uniqueness test in CLAUDE-reference.md.

**recommendation-as-identity.md:** The most shareable thing is what the designer didn't author. Players share emergent outcomes because they are claimable as *their* story. A generated quest summary is shareable precisely because no other player got the same one.

**experience-goals.md:** The personal feeling must be defined as an emotional target before mechanics are built. The question "what should the player feel when they receive a contextually generated quest?" needs an answer before the generation system is built. The wiki identifies the framework but has not applied it to this project.

**intrinsic-motivation.md + self-determination-theory.md:** A quest that satisfies autonomy (player chose to pursue it), competence (player is capable of it), and relatedness (it connects to NPCs the player has relationship with) will feel intrinsically motivating. Generic quests fail on relatedness — there is no pre-existing relationship context.

**emergent-narrative.md:** The test is operational: mechanics operating on human values (loyalty, betrayal, loss, gain) produce situations that feel personal because they engage the player's value system, not just their task queue.

**information-asymmetry.md:** A quest that reveals information the player didn't have — that recontextualizes something they already knew — produces the strongest personal feeling. The reveal mechanic is more important than the task mechanic.

### What is missing

**No evaluation rubric.** The wiki knows what makes quests feel personal but has no instrument for measuring it. Research question Q6 asks whether players can distinguish generated from handcrafted quests. This requires a playtest protocol: specific quests (3 generated, 3 handcrafted), specific questions to ask players afterward, specific signals to look for.

**No experience goal statement for this project.** Experience-goals.md provides the framework. The project has not applied it. What is the single emotional target that every design decision should be filtered through? "Feeling like the world responded to your specific story" is close but not precise enough to function as a design filter.

**No signal definition for "too generic."** The failure test ("could this have appeared in any other playthrough?") is clear. But there is no rubric for grading partial success — a quest that is somewhat specific but not fully personal. Without a gradient, iteration is binary (pass/fail) when it should be directional.

**No feedback loop from player to system.** The wiki has rich theory about closed-loop systems but has not applied it to player feel. If the AI generates a quest and the player ignores it or rushes through it, that is a signal. How does that signal feed back into quest generation? Undesigned.

### What to build or ingest next

**Build first:** Write the project's experience goal statement. One sentence. What should the player feel in the moment they receive a contextually generated quest that is actually contextual? This filters every downstream decision.

**Build second:** Design the Q6 experiment. Write 3 handcrafted quests for a hypothetical scenario. Generate 3 quests using the same scenario as input. Interleave them. Define what you will ask players and what answer would constitute success. You do not need players yet — you need the protocol.

**Ingest:** The GDC postmortem on Façade (Mateas and Stern). They explicitly measured player response to AI-driven narrative and documented what worked and what felt mechanical. This is the closest existing measurement of "does AI-generated narrative feel personal?"

---

## 6. TECH STACK
*Do we have enough knowledge to choose the right tools and architecture for the prototype?*

### What the wiki knows

**harness-engineering.md + cognitive-externalization.md:** The architectural pattern is clear: thin runtime harness, domain knowledge externalized into inspectable structures (templates, schemas, prompts). The LLM is the filling engine, not the reasoning engine. Reasoning lives in the templates and validation logic.

**vibe-coding.md + agentic-workflow.md:** The development methodology is decided — AI-assisted rapid development (vibe coding) with Claude Code as the primary tool. The cousin technical co-lead provides the implementation bandwidth. Karpathy's post-2024 mode: express intent, review output, redirect.

**llm-as-computer.md:** The LLM is treated as a computing substrate. Context window is RAM. This means game state is passed into the context on each generation call — not stored in the model. Implications: context window size constrains how much state can be included per call.

**multi-agent-orchestration.md:** For the Stage 1 prototype, a single-agent architecture is sufficient. Multi-agent (NPCs with their own reasoning loops) is a Stage 3 consideration. The wiki has the theory for when to escalate.

**concentric-development.md + vertical-slice.md:** Both concepts point to the same strategy: build the smallest working thing first. For the tech stack, this means choosing tools that minimize setup time even if they are not optimal for scale.

### What is missing

**No game engine decision.** The wiki has no analysis of Godot vs. Unity vs. Pygame vs. any other option for a 2D prototype. This is the most consequential unresolved decision because it determines the entire development environment. For a 2D prototype built primarily with AI assistance, the engine choice affects how much of the codebase Claude Code can generate effectively.

**No LLM API selection.** Claude API vs. OpenAI vs. local model (Ollama). Each has different latency, cost, and capability profiles. The wiki knows LLMs exist but has not analyzed which is appropriate for real-time quest generation during gameplay.

**No cost model.** Quest generation happens during gameplay. If a quest is generated every 10 minutes of play and an API call costs $0.01, the cost is trivial. If latency is 3 seconds and the call costs $0.10, both latency and cost are problems. Neither has been analyzed.

**No persistence layer design.** Game state must persist across sessions. NPC knowledge states, player choices, established narrative facts — these need a storage layer. SQLite? JSON files? A vector database for similarity-based state retrieval? Undesigned.

**No latency budget.** Quest generation must happen within a time window that doesn't break immersion. What is that window? 500ms? 2 seconds? 5 seconds? This constrains whether generation can happen synchronously (during NPC dialogue) or must be pre-generated (queued in the background).

**No local vs. cloud decision.** For a playable demo, API calls require internet connectivity. A local model (Ollama + a small model) would allow offline play and eliminate cost and latency variability. The wiki has not addressed this tradeoff.

### What to build or ingest next

**Decide first (not build):** Game engine. The choice should be Godot for three reasons: (a) Python-adjacent GDScript that Claude Code handles well, (b) built-in 2D tooling, (c) export to web for itch.io Stage 2. This decision should be made explicitly so the development environment can be set up.

**Decide second:** Claude API with claude-sonnet-4-6 for generation calls, with a local fallback plan deferred to Stage 2. Rationale: you are already in a Claude Code environment; the API is known; the capability is sufficient; local model setup adds time without adding information about whether the mechanic works.

**Build first:** A standalone test harness — not a game, not a prototype, just a script that takes a hardcoded game state JSON, sends it to the API with a template, and prints a generated quest. This answers the latency and cost questions with actual data before any game engine decision matters.

**Architecture decision to write down:** Define the persistence layer before writing any game code. Proposal: game state in a single JSON file, NPC states in individual JSON files (one per NPC), narrative facts in a SQLite table with timestamps. Validate this against the consistency checker design once that exists.

---

## Priority Order

Given 5-month runway and cousin as technical co-lead, this is the recommended sequence:

1. ✅ **Write the experience goal statement.** One sentence. Everything filters through it.
2. ✅ **Build the standalone generation test harness.** No game engine. Just state → API → quest. Answers latency, cost, and template questions simultaneously.
3. ✅ **Define minimum game state JSON schema.** Force the minimum — 5 fields. Expand with evidence.
4. ✅ **Define minimum NPC schema.** Same approach — 5 fields, test, expand.
5. ✅ **Write 3 quest templates.** One for each of: main quest escalation, NPC personal crisis, player-choice callback. *(Four shipped — world texture added.)*
6. ✅ **Design the fact database schema.** Categories of hard constraints. Build the validator.
7. ✅ **Set up Godot project.** Only after the generation system is tested outside the game.
8. ⬜ **Design the Q6 experiment.** Protocol for measuring whether quests feel personal. **← active step**

---

## Status Update — 2026-08-05: Step 7 complete

Steps 1–7 of the priority order above are done. This report was written
as a greenfield assessment on 2026-06-03; the analysis below is left as
written, and this section records what was actually built against it.

**What Step 7 turned out to be.** The report anticipated "set up Godot
project" as a single item. In practice it split into two halves joined
by a transport decision:

- **FastAPI bridge** (`prototype/server.py`) — the engine talks to Python
  over localhost HTTP. `GET /health` returns world state and costs no
  tokens; `POST /generate-quest` runs the full pipeline and returns the
  quest plus `validation_status`, `attempts`, and an `attempt_log`.
  Chosen over subprocess and GDExtension because a web export for
  itch.io needs HTTP anyway — see section 6, which flagged the engine
  decision as the most consequential unresolved item.
- **Godot 4.7.1 client** (`godot/`) — placeholder player (arrow keys),
  a stationary NPC, an `Area2D` talk zone, and a dialogue panel. Walk
  into the zone, press E, and the generated quest renders in-engine.

**Round trip verified end to end**, with a quest that passed every hard
constraint rather than merely returning 200:

    [bridge] POST http://localhost:8000/generate-quest
    [bridge] HTTP status code: 200
    [bridge] npc=Otto template=personal_crisis validation=passed attempts=1
    [bridge]   attempt 1: failed=none retried=false — passed on attempt 1

Godot → HTTP → Python → SQLite → Claude → validator → back to the engine
canvas. The pipeline the report describes in theory now runs in a game
window.

**Also built along the way, not anticipated here:** a conditional retry
that re-samples only when the failing check is sampling-dependent (C3,
C4) and refuses to spend a second API call on deterministic failures
(C1, C5), plus fixes to three classes of C3 false positive and one C1
format bug that made every markdown-headed quest read as structurally
broken.

**Active step: 8 — the Q6 experiment protocol.** Section 5 of this
report is the one that still stands unanswered: there is no instrument
for measuring whether a generated quest feels personal. The system can
now produce validated quests on demand inside the engine, which is
exactly the precondition that experiment needs.

---

## Overall Assessment

The wiki provides an unusually strong theoretical foundation. The player psychology section alone (emotional memory, peak-end pattern, self-expression, intrinsic motivation, information asymmetry) is sufficient to design the evaluation criteria for whether the mechanic works. The agent memory and emergent narrative concepts provide the right vocabulary for what the system needs to track.

The engineering gaps are real but not deep. None of them require new research — they require decisions and first implementations. The generation pipeline architecture is decided. The player feel theory is solid. What is missing is the translation from theory to schema, from concept to template, from principle to validator.

The highest-risk gap is consistency enforcement. Everything else can be iterated once the demo exists. A consistency failure — a quest given by a dead NPC, a quest referencing an event that hasn't happened — breaks the player's trust in the system in a way that is hard to recover from. Build the fact database and the hard-constraint validator before the demo is shown to anyone.
