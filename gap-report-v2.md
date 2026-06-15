# Side Quest AI — Gap Report v2
*Generated: 2026-06-15*
*Source: Full read of prototype/ (8 files), PROJECT-CONTEXT.md, build-log.md, fact-database-design.md, quest-templates.md, game-state-schema.json, npc-schema.json, experience-goal.md, and gap-report.md.*
*Previous report: gap-report.md (2026-06-03 — greenfield assessment, no code existed)*

---

## Status Summary

Steps 1–6 of the original 8-step priority order are complete. The prototype
stack is feature-complete for V1: game state schema, NPC schema, four quest
templates, SQLite fact database, pre-generation pipeline, hard constraint
validator, and end-to-end generation run all exist and have been tested.

The gap has shifted from theory-to-design to design-to-game. The system can
generate grounded, contextual quests from a database. It cannot yet deliver
them inside a game. Step 7 (Godot) is the next threshold.

Known V1 limitations are real but documented and bounded. None block Step 7.
The highest-risk open item is the absence of runtime state write-back — the
database is currently static seed data, not a live game state.

---

## 1. GAME STATE

*Original question: Do we have enough knowledge to define what information the
AI needs to generate a contextual quest?*

### COMPLETE

- **5-field game state schema** (`game-state-schema.json`): `main_quest`,
  `player_action`, `npc_name`, `npc_situation`, `npc_knowledge`. Validated
  against 5 test states with quest-generator-v1.py.
- **6th field `player_history`** (conditional, callback template only):
  surfaced by Template 3, confirmed as necessary, added to schema with
  reasoning in `game-state-schema-reasoning.md`.
- **SQLite fact database** (`blackwater.db`, 8 tables): the full world model
  exists as structured data. Entities, events, relationships, player singleton,
  player_choices, npc_knowledge, npc_beliefs (empty), quests.
- **Runtime game state assembly** (`pipeline.py`, A5): builds the 5/6-field
  game state dict from DB queries at trigger time. callback template gets
  `player_history` and `referenced_choice` automatically.
- **Minimum state test**: confirmed empirically. 5 fields + NPC definition is
  sufficient to generate quests that pass the specificity test. Token budget
  confirmed at 1200 minimum (700 in / 900 out average per template).

### PARTIAL

- **Trigger logic**: only player-action-based triggering is implemented. The
  design (fact-database-design.md §A1) also specifies scene-change and
  NPC-stake-threshold triggers. Neither is built. V1 trigger fires manually
  from a hardcoded string in `quest-generator-v4.py`.
- **State change tracking**: the tables exist and the schema supports it, but
  no runtime write-back is implemented. Every event, entity status change, and
  NPC knowledge update must be manually seeded. The DB is a snapshot, not a
  live log.
- **Adjacent-location queries**: `pipeline.py` A2 queries same-location NPCs
  only. The design calls for adjacent-location traversal as V2/Godot
  integration work. This limits the candidate pool to NPCs physically
  co-located with the player.

### STILL MISSING

- **Runtime event logging**: player actions need to write to the `events`
  table automatically. Without this, the callback template will exhaust its
  seeded choices and have nothing new to call back against.
- **In-game tick definition**: what advances the tick (player actions? scene
  changes? real time?) is unresolved. Deferred to Godot integration (Step 7).
  This affects cooldown, callback freshness, and deadline detection.
- **Godot → Python state bridge**: the DB must be readable and writable from
  Godot at runtime. No integration layer exists yet.

**Blocking step 8?** State write-back is partially blocking Q6: a playtest
with static seed data will exhaust variety quickly. Step 7 must include at
minimum a basic write-back path for player actions to the events table.

---

## 2. QUEST GENERATION

*Original question: Do we have enough knowledge to build the actual generation
pipeline? What approach — templates, free-form LLM, hybrid?*

### COMPLETE

- **All four template prompts** (`quest-templates.md`): escalation,
  personal_crisis, callback, world_texture. Each includes prompt text,
  experience-goal test, failure signal, and a filled example with a unique NPC.
- **Template routing** (`quest-generator-v3.py`, v4.py): accepts template
  parameter and routes to correct prompt builder. All four tested and passing.
- **End-to-end generation pipeline** (`quest-generator-v4.py`): pipeline →
  load NPC → build prompt → call Haiku → validate → write to DB. One command
  produces a quest and logs it.
- **Token budget confirmed**: 700 budget caused truncation on all four
  templates. 1200 is the confirmed minimum. Average run: 3828 in / 4413 out
  across all four templates in one session.
- **Latency data**: 3–5 seconds per call. Acceptable for pre-queued
  generation; synchronous in-dialogue generation would require threading
  (V2 scope).
- **Template quality validated**: recognition line test passed on callback
  template ("That woman three weeks ago — the one you told the guard had
  already paid. She hadn't."). Escalation revelation landed (Elena in Outer
  City custody, not Syndicate). World texture discipline held (no main quest
  connection). Stake beat present in personal crisis.

### PARTIAL

- **C1 regex incomplete**: the structural check handles `**N.**` (bold) but
  not `## N.` (markdown header). Model sometimes uses the header format,
  causing a false failure. Fix: extend regex with `(?:#{1,2}\s*)?` prefix or
  add format constraint to prompts. Estimated: 10 minutes. Not yet done.
- **Recovery cascade R1–R4 designed but not implemented**: the four-step
  failure recovery (retry with constraint → same NPC different template →
  different NPC → skip) exists in `fact-database-design.md §5` but has no
  code. Every current failure writes to DB as `failed_validation` and exits.
- **Single scenario tested**: all end-to-end runs use the same seeded
  scenario (Eastern Gate Checkpoint, trigger = manifest burned). Template
  variety is validated but input variety is not.

### STILL MISSING

- **R1–R4 recovery cascade**: the most significant unbuilt piece of the
  generation system. Without it, a failed validation produces no quest rather
  than an automatically corrected one.
- **Async generation thread**: generation must run off the main thread to
  avoid blocking gameplay. This is V2 scope (post-Godot), but the architecture
  must accommodate it from Step 7 onward.
- **Multiple scenario testing**: the four templates have only been tested
  against the Blackwater seed data. They need testing against varied locations,
  NPCs, and trigger actions before Q6.
- **Prompt format constraint**: a single line added to each prompt
  ("Use plain numbered list: 1. WHY") would eliminate the C1 false failures
  without the regex change. Either fix is trivial; neither has been applied.

**Blocking?** R1–R4 is not blocking Step 7 (Godot setup) but is blocking
a clean Q6 experiment — failed validations that should recover will instead
produce no quest, distorting the playtest signal. Fix before Q6.

---

## 3. NPC SYSTEM

*Original question: Do we have enough knowledge to define the minimum NPC
model needed for quest generation through believable characters?*

### COMPLETE

- **5-field NPC schema** (`npc-schema.json`): name, situation, want, stake,
  network. Validated by generating grounded quests through all four NPCs.
  Stake field confirmed as the sim-to-feel bridge — it is what makes Template
  2 produce emotional weight rather than task logistics.
- **Four production-quality NPCs**: Serge (courier), Daria (seamstress/
  alterations), Otto (gate checkpoint contractor), Nadia (cartographer). Each
  fully authored across all five fields with specific, concrete detail.
- **NPC data in SQLite** (`seed_db.py`): all four NPCs seeded into entities
  table with properties JSON holding their full authored definitions. Two
  dependency NPCs (Marta, Mikhail) also present.
- **Per-NPC epistemic state** (`npc_knowledge` table): 6 rows across four NPCs
  with channel (witnessed/told_by/rumor) and confidence (1.0/0.8/0.4).
  Confidence hierarchy validated: Otto witnessed=1.0, Serge told_by=0.8,
  Nadia rumor=0.4.
- **Relationship graph** (`relationships` table): 11 relationships across
  trusts/knows/related/located_at types with strength values. Pipeline uses
  trust gradient as soft constraint multiplier.
- **Quest giver selection logic** (`pipeline.py` A3–A4): template eligibility
  check + soft constraint scoring selects the best (NPC, template) pair per
  trigger. Outputs ranked scores for all candidates.

### PARTIAL

- **Gossip propagation designed but not wired**: the design specifies
  scene-change triggering with 20-tick window, proximity-gated propagation,
  and social-graph gating (facts-database-design.md, Open Question 1 resolved).
  No code implements this. NPC knowledge currently reflects only the seed state.
- **NPC state change tracking**: entities table has `status` and
  `last_changed_at` fields. No runtime writes update them. If an NPC dies
  during play, the DB won't know until manually updated.
- **Stake activation scoring**: `pipeline.py` A4 has `stake_activation = 1.0`
  (V1 stub). The actual logic — detect whether a recent event threatened the
  NPC's stake referent — requires an LLM judge reading the stake text. Deferred
  to V2.

### STILL MISSING

- **More NPCs**: four NPCs cover the demo scenario but a playable Godot build
  will need 8–12 authored NPCs to avoid the player meeting the same four
  characters every run. Each new NPC requires authored situation/want/stake/
  network plus seeding into the DB.
- **npc_beliefs table**: exists in schema (empty). False-belief quest
  generation is V2 — an NPC who wrongly believes the player is a Syndicate
  informant is a rich mechanic but requires careful authoring.
- **Player declined this NPC** soft constraint: designed in §3 but not
  implemented. Without it, a player who skips Daria's quest will keep getting
  offers from her.

**Blocking?** Gossip propagation is partially blocking the Q6 experiment —
without it, the callback template will only fire on events the NPC directly
witnessed (seeded data), which limits variety. It is not blocking Godot setup.

---

## 4. CONSISTENCY

*Original question: Do we have enough knowledge to prevent the AI from
generating quests that contradict established narrative facts?*

### COMPLETE

- **Hard constraint validator** (`validator.py`): C1 (structural), C3
  (existence), C4 (state), C5 (causal) implemented and tested.
- **Six test cases all produce correct outcomes**: clean quest passes; missing
  item 5 fails C1; hallucinated "Clerk Vaskov" fails C3; destroyed entity
  referenced fails C4; valid callback choice passes C5; already-used callback
  fails C5.
- **Entity index with article stripping**: `lookup_entity()` strips leading
  articles ("The Syndicate Supply Manifest" → "Syndicate Supply Manifest")
  before DB lookup. Prevents false-positive hallucination flags on correctly
  referenced entities.
- **Validation log written to DB**: every quest (passing and failing) writes
  a JSON validation log to `quests.validation_log`. This is the data that
  will drive prompt tuning.
- **Soft vs. hard constraint distinction**: fully designed and implemented.
  Deadlines are warnings (C4 non-blocking); destroyed entities are hard failures.

### PARTIAL

- **C3 false positives (V1 known issue)**: heuristic Title-Case regex
  over-matches sentence-start words paired with entity/safe-word sequences
  ("But Otto", "No Syndicate"). Currently mitigated by SAFE_WORDS set and
  single-word skip rule, but multi-word sentence-start + entity sequences
  still fire. V2 fix: replace regex with trained NER model. Current workaround:
  documented and accepted as V1 behavior.
- **C1 format gap (V1 known issue)**: regex matches `**N.**` but not
  `## N.` Model used header format in one run, producing a false C1 failure
  on a quality quest. 10-minute fix; not yet applied.
- **C6 knowledge check deferred**: verifying that every NPC claim is supported
  by a `npc_knowledge` row requires LLM judge for paraphrased claims. V1
  skips this entirely. This is the constraint most directly tied to the
  grounding guarantee — its absence means a technically passing quest could
  still have the NPC reference knowledge they couldn't have.
- **C8 narrative integrity deferred**: keyword blocklist approach only. LLM
  judge needed to catch paraphrased main quest resolution.

### STILL MISSING

- **R1–R4 recovery cascade**: validator rejects quests; nothing retries. Every
  validation failure is a dead end until recovery is implemented.
- **callback_used flag write-back**: when a callback quest is accepted by the
  player, `player_choices.callback_used` should flip to 1. No runtime path
  exists to do this. Currently, the same choice could be called back
  repeatedly across sessions.
- **NER model for C3**: replacing the heuristic extractor is a 1–2 day task
  that must happen before any public-facing demo. The current false-positive
  rate would produce noise that confuses the failure analytics.

**Blocking?** The known C1 and C3 issues are not blocking Step 7 — they are
documented limitations that don't affect quest quality, only validation
accuracy. Fix C1 first (10 min) to clean up the logs. C3/NER is pre-demo,
not pre-Godot.

---

## 5. PLAYER FEEL

*Original question: Do we have enough knowledge to know what makes a generated
quest feel personal vs. generic?*

### COMPLETE

- **Experience goal statement**: "The player feels a moment of disorienting
  recognition: the world has been paying attention to their specific story,
  not the generic one, and an NPC is now speaking directly to it." Written,
  filed in `experience-goal.md`, used as the design filter for all template
  evaluation.
- **Three observable success tests defined**: player stops and reads carefully;
  player describes NPC's reason not just the task when asked "what happened";
  player asks "how did they know that?"
- **Three observable failure signals defined**: player accepts without reading;
  player describes only the objective; player expresses confusion about why
  this NPC approached them.
- **Recognition line test passed**: the callback template produced "That woman
  three weeks ago — the one you told the guard had already paid. She hadn't."
  This is the experience goal landing in a single line.
- **Template-level feel targets differentiated**: each template has its own
  experience goal test and failure signal, specified in `quest-templates.md`.
  Templates produce distinct emotional registers (revelation / stake absorption
  / retroactive recognition / world aliveness).

### PARTIAL

- **Q6 experiment protocol designed but not formalized**: the original gap
  report described what a Q6 experiment would test (3 handcrafted quests vs.
  3 generated, interleaved, specific questions). No formal protocol document
  exists. Still in design phase.
- **Gradient rubric absent**: the pass/fail test ("could this have appeared
  in any other playthrough?") is clear but binary. No rubric exists for grading
  partial success — a quest that is somewhat specific but not fully personal.
  Without a gradient, iteration is difficult.

### STILL MISSING

- **Formal Q6 protocol document**: the specific quests (handcrafted versions),
  the interleaving order, the post-quest questions, and the success threshold
  need to be written down before participants are recruited.
- **Playtest participants**: the Q6 experiment needs players who haven't seen
  the system before. None have been recruited. This is Step 8 work.
- **Player feedback loop to generation system**: the design calls for reducing
  the probability of quest generation when the player skips quest text (the
  "player attention" soft constraint). No mechanism to detect text-skip exists
  yet — this requires Godot integration to observe player behavior.
- **In-game feel test**: the experience goal can only be fully validated in
  a running game. The prototype is a terminal script. The feel cannot be
  tested until Godot is running and quests are delivered through NPC dialogue.

**Blocking?** The formal Q6 protocol is blocking Q6 (Step 8) but not
Godot setup (Step 7). Write the protocol during or after Godot setup, before
recruiting players.

---

## 6. TECH STACK

*Original question: Do we have enough knowledge to choose the right tools
and architecture for the prototype?*

### COMPLETE

- **Python prototype stack**: working. All five files (`init_db.py`,
  `seed_db.py`, `pipeline.py`, `validator.py`, `quest-generator-v4.py`)
  are independent, importable, and tested. venv and requirements.txt present.
- **Claude Haiku API**: `claude-haiku-4-5-20251001` confirmed. SDK
  (`anthropic`) wired. API key working. Cost and latency data gathered
  from real runs.
- **SQLite**: `blackwater.db` populated with all seed data. 8 tables, FK
  constraints enforced, PRAGMA foreign_keys = ON set at connection time.
  Idempotency guards on init and seed.
- **Game engine decided**: Godot. Rationale documented in gap report v1
  (GDScript ≈ Python-adjacent, built-in 2D, web export for itch.io). Not
  yet set up.
- **Persistence layer design complete**: static NPC definitions in entities
  table (populated from `seed_db.py`); dynamic state in SQLite; JSON for
  config. Runtime write-back path exists in design; not yet implemented.
- **Cost model validated**: one full 4-template run = 3828 in / 4413 out
  tokens on Haiku. At current Haiku pricing this is under $0.01 per full run.
  Single-template generation averages ~$0.001. Cost is not a constraint at
  prototype scale.

### PARTIAL

- **Godot project not yet initialized**: the engine is decided but no `.godot`
  project, no scenes, no scripts exist. Step 7 starts from zero.
- **Python ↔ Godot bridge not designed**: the pipeline is pure Python. Godot
  needs to call it (or an equivalent) at runtime. Three options: subprocess
  call from GDScript (simplest), GDExtension (most integrated, most complex),
  HTTP API on localhost (most portable). This architectural decision needs
  to be made in Step 7.
- **Runtime state write-back not implemented**: the DB is currently write-once
  (seeded). Events, entity status changes, player location, and NPC knowledge
  updates all need a write path that fires during gameplay.

### STILL MISSING

- **Godot ↔ Python integration layer**: the single most consequential
  unresolved decision. Without it, the working Python pipeline cannot be
  reached from inside the game.
- **Web export configuration**: for itch.io demo. Godot supports HTML5 export;
  Python subprocess calls do not work in a browser. This may force the HTTP
  API approach for the bridge, or require the generator to run server-side.
  Needs explicit decision before Godot UI work begins.
- **Async generation**: quests currently generate synchronously (3–5s
  blocking). During gameplay, generation should queue in the background and
  surface when the player next interacts with an NPC. Architecture must
  accommodate this from Step 7 even if the async logic is added in V2.

**Blocking?** The Godot ↔ Python bridge decision is the first task of Step 7.
Everything else in Step 7 depends on it. The web export / async question
should be answered at the same time to avoid building the wrong bridge.

---

## Ingestion Recommendations — Status

The original gap report recommended four specific sources for ingestion.
Assessment of what was actually ingested:

| Recommended source | Status |
|---|---|
| Disco Elysium GDC dialogue/quest architecture talk | NOT INGESTED |
| Left 4 Dead AI Director GDC talk | NOT INGESTED |
| Dwarf Fortress NPC modeling docs / technical breakdown | NOT INGESTED |
| Façade GDC postmortem (Mateas and Stern) | NOT INGESTED |

**What was ingested instead** (NPC/generation-adjacent sources):
- `wiki/sources/ai-npc-unsolved-problem-perplexity.md` — research on the
  open problem space of AI NPCs
- `wiki/sources/npc-grounding-architecture-perplexity.md` — grounding
  architecture research
- `wiki/sources/llm-reasoner-automated-planner-npc.md` — LLM-as-planner
  for NPC systems

These cover adjacent conceptual territory but do not provide what the
original recommendations would have provided: concrete architectural
decisions from shipped games (what state Disco Elysium actually tracks;
how the L4D Director reads player pacing; how Dwarf Fortress manages NPC
knowledge graphs; how Façade measured player response to AI narrative).

**Revised ingestion priority**: the four original recommendations remain
worth ingesting, but their urgency has shifted. Steps 1–6 were built
without them and the prototype works. The most useful ingestion now is
not "what should we build?" (answered) but "how do we make it better?"
The Façade postmortem is the highest-value source: it is the only existing
measurement of whether players can distinguish AI-generated narrative from
handcrafted narrative — directly relevant to Q6 design.

---

## Revised Priority Order

The original 8-step order is now 6 steps complete. The remaining work
is a different shape than the original steps — it is integration and
validation work, not architecture work.

### Immediate (before Step 7 begins)

0. **Fix C1 regex** (10 minutes). Extend the pattern to handle `## N.`
   header format, or add a format constraint line to each prompt. Either
   works. Do this before any Godot work so the logs are clean.

### Step 7 — Godot setup and integration

1. **Decide the Python ↔ Godot bridge architecture.** Three options:
   subprocess call (simplest, breaks on web export), localhost HTTP API
   (portable, works on web if generator runs server-side), GDExtension
   (most integrated, most complex). Web export requirement may force HTTP.
   Decide before writing any Godot code.

2. **Initialize Godot project.** Minimal 2D scene: player character,
   NPC sprite, dialogue box. No quest system yet — just a player who can
   walk and click NPCs to trigger dialogue.

3. **Wire the bridge.** Connect the Godot NPC interaction event to the
   Python pipeline. Single call: player interacts with NPC → pipeline
   selects (NPC, template) → generates quest → returns quest text to
   Godot → dialogue box displays it.

4. **Implement event write-back.** When the player takes any significant
   action (crosses a checkpoint, uses an item, makes a moral choice),
   write an events row to the DB. This is the minimum needed to make
   the callback template work across more than the seeded events.

5. **Define the in-game tick.** Decide what increments the tick (player
   actions, scene changes, or a hybrid). Wire it to the events table.
   This unlocks cooldown, freshness decay, and deadline detection.

6. **Wire gossip propagation.** On scene change: for each NPC in the
   new location with a relationship to a witness of a recent event, create
   an `npc_knowledge` row. This is the mechanism that makes the world feel
   connected across player sessions.

### Step 8 — Q6 experiment

7. **Write the formal Q6 protocol document.** Three handcrafted quests
   for the Blackwater scenario. Three generated quests from the same
   scenario (pick the best from a batch of 10). Interleaving order.
   Post-quest questions. Success threshold. Ingest Façade postmortem
   first to inform the question design.

8. **Run the Q6 experiment.** Minimum 3 participants who haven't seen
   the system. Collect responses against the protocol. Evaluate.

### V2 (post-Q6, informed by experiment data)

9. **R1–R4 recovery cascade.** Build only after Q6 identifies which
   failure mode is most common. Building recovery before knowing the
   failure distribution risks optimizing the wrong path.

10. **NER model for C3.** Replace heuristic extractor before any public
    demo. 1–2 days; schedule after Q6 is complete and before itch.io
    submission.

11. **Async generation thread.** Pre-queue quests during scene traversal
    so delivery is instant during NPC dialogue. Architecture concern for
    V2; Godot integration in Step 7 should be designed to accommodate it.

12. **Author 8+ additional NPCs.** Each needs full authored definitions
    and DB seeding. This is ongoing world-building work that can run in
    parallel with any technical step.

---

## Overall Assessment

The original gap report said the engineering gaps were "real but not deep"
and required decisions and first implementations rather than new research.
That assessment was correct. Every gap has been closed at the design and
prototype level in the six weeks since the report.

The system now does what it was designed to do: read a world state, select
the best NPC and template, assemble a grounded game state, generate a
contextual quest, validate it against hard constraints, and write the result
to a database. The recognition line test passed. The experience goal is not
a hypothesis anymore — it is a tested claim about what the callback template
produces when the inputs are right.

The new gap is a different kind: the prototype exists on the command line
and the experience goal requires a player inside a world. Step 7 is the
translation from "this works" to "this feels like a game." That translation
is shorter than building the system was, but it has its own risks — the
bridge architecture decision is the single most consequential unresolved
question in the project, and it determines whether the demo can reach a
browser for itch.io.

The original highest-risk item was consistency enforcement. That risk is now
managed — the validator exists, the known V1 limitations are bounded and
documented, and the failure modes that matter most (dead quest givers,
hallucinated entities, reused callbacks) are caught. The new highest-risk
item is the Python ↔ Godot integration: if the bridge is wrong, the prototype
cannot become a game. Decide it first.
