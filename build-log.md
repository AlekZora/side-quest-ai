# Build Log — Side Quest AI System

## 2026-06-09

### Completed
- Step 1: Experience goal defined
  File: wiki/projects/game/experience-goal.md
- Step 2: Standalone quest generator built and tested
  File: wiki/projects/game/prototype/quest-generator-v1.py
  Result: passed specificity test on all 5 states
- Step 3: Minimum game state schema defined (5 fields)
  Files: game-state-schema.json, game-state-schema-reasoning.md
- Step 4: Minimum NPC schema defined (5 fields)
  Files: npc-schema.json, npc-schema-reasoning.md
  Validated: quest-generator-v2.py with Rook NPC passed 
  all tests including sim-to-feel gap
- GitHub repo: github.com/AlekZora/side-quest-ai (private)

### Current step
Step 5 — Three quest templates
(main quest escalation, NPC personal crisis, 
player-choice callback)

### Next session starts here
Build three quest templates in quest-templates.md
Then update quest-generator-v2.py to use them.

---

## 2026-06-09 (continued)

### Completed
- Step 5: Three quest templates defined
  File: wiki/projects/game/quest-templates.md
  Templates: Main Quest Escalation, NPC Personal Crisis, Player Choice Callback
  Each template includes: prompt text with placeholders, experience goal test,
  failure signal, and a filled example using a new NPC
  Schema gap surfaced: Template 3 requires player_history array — not in base
  5-field game state. Step 6 fact database must support this.
  New example NPCs created: Serge (courier), Daria (seamstress), Otto (gate contractor)

- Schema gap confirmed and documented: Template 3 requires player_history array.
  Updated files:
  - game-state-schema.json — player_history added as conditional 6th field
  - game-state-schema-reasoning.md — player_history confirmed under 
    "What would be gained with more"
- Template 4 added: World Texture
  No main quest connection. Emerges from NPC situation and stake alone.
  Defining structural feature: "what stays unresolved" beat — the NPC's
  deeper problem (stake) does not go away when the immediate need is met.
  New example NPC: Nadia the cartographer, one street short of completing
  a commission her career depends on.
  Template summary table updated to include Template 4.
  Next step updated: template parameter now includes "texture" routing.

### Current step
Step 6 — Update quest-generator-v2.py to accept a template parameter
(escalation | crisis | callback | texture) and route to the appropriate prompt.
Template 3 also requires game state to accept a player_history array.

### Next session starts here
Wire the four templates into quest-generator-v2.py.
Add template routing logic.
Add player_history support to game state for Template 3.
Test each template with its example NPC.

---

## 2026-06-09 (continued)

### Completed
- Step 6: quest-generator-v3.py built and tested
  File: wiki/projects/game/prototype/quest-generator-v3.py
  All four templates implemented and routed:
  - escalation     → Serge (Syndicate courier)
  - personal_crisis → Daria (alterations shop, husband detained)
  - callback        → Otto (gate checkpoint contractor)
  - world_texture   → Nadia (cartographer, restricted alley)
  NPC definitions embedded inline — no external file dependency.
  player_history array added to callback game state (3 past actions).
  Token budget: 700 insufficient (all four truncated); updated to 1200.

### Test results
All four templates produced correct quest types. Notable outputs:

Template 1 (escalation): Revelation confirmed. Serge reveals Elena is being
  traded to the Outer City administration, not simply held by the Syndicate.
  WHAT CHANGES: "rescue Elena from the Syndicate" becomes "determine what the
  Outer City wants with Elena and whether the resistance's silence was
  incompetence or strategy." Grounded in Serge's 11 months of urgency-code
  pattern observation.

Template 2 (personal_crisis): Stake landed. Crisis is Mikhail's enrollment
  pamphlet on the kitchen table — a statement, not a question. Model added
  branching resolution structure beyond the 5 required items. Flag for future
  iteration: may need to constrain to 5-item output only.

Template 3 (callback): Recognition line delivered.
  Exact output: "That woman three weeks ago — the one you told the guard had
  already paid. She hadn't."
  Experience goal test passed: the line names the past choice specifically
  without summarizing it flatly, and feels like being caught, not accused.

Template 4 (world_texture): World texture discipline held. No Syndicate
  connection in the output. "What stays unresolved" beat present: even after
  Nadia gets the map data, the guild master may not accept it if he learns she
  did not survey the street herself. Quest has nothing to do with Elena.

### Token stats (full run)
  Total: 3828 in / 4413 out
  Per-template input: 795 / 1012 / 1064 / 957
  Per-template output: 1091 / 1200 / 1124 / 998

### Current step
Step 7 — Godot setup

### Next session starts here
Begin Godot project setup.
Do not build more prototype features before Godot is running.

---

## 2026-06-09 (continued — step labeling correction + Step 6 design)

### Labeling correction
The previous entry mislabeled the quest-generator-v3.py routing work as
"Step 6" and forward-projected "Step 7 — Godot" as next. That was wrong.
The v3.py routing was the implementation half of Step 5 (templates).
The real Step 6 is the fact database and hard-constraint validator.
Step 7 (Godot) is gated on Step 6 completion.
PROJECT-CONTEXT.md was updated separately to reflect this.

### Completed
- Step 6 design document drafted (no code).
  File: wiki/projects/game/fact-database-design.md

  Document answers the five design questions:
  1. Schema — eight tables specified:
     - 5 core (events, entities, relationships, player, npc_knowledge)
     - 2 indexes (player_choices, quests)
     - 1 deferred to V2 (npc_beliefs)
     Each table has exact field definitions with reasoning.
  2. Hard constraints — 14 numbered constraints across 4 categories
     (existence, state, causation, narrative integrity, temporal).
     User's 4 base constraints incorporated and expanded.
     V1 vs V2 split called out — rule-based first, LLM judge later.
  3. Soft constraints — 10 weighted multipliers across 4 categories
     (pacing, relationship, template-specific, player state).
     V1 ships with 6, V2 adds the rest.
  4. Validation pipeline — three phases (trigger, generation, validation)
     with 15 numbered steps. Phase A is pre-generation candidate selection;
     Phase C is post-generation hard-constraint checks.
  5. Failure recovery — 4-step cascade R1–R4 ending in silent skip.
     Handcrafted fallback explicitly rejected (breaks experience goal
     contract).

  Open questions surfaced:
  - Gossip propagation cadence (timer vs interaction-triggered)
  - In-game tick definition (waits for Godot integration)
  - Entity extraction strategy for hard constraint C2
  - Stake threat detection requires LLM judge
  - Concurrency: serialize V1, parallel V2

### Current step
Step 6 implementation — build the SQLite schema and validator per the
design document. Follow the 8-step implementation order at the bottom
of fact-database-design.md.

### Next session starts here
1. SQLite schema migration script — create all 8 tables.
2. Seed data: convert Serge / Daria / Otto / Nadia from quest-templates.md
   into entities + relationships + npc_knowledge rows.
3. Pre-generation pipeline (Phase A of validation pipeline).
4. Rule-based hard constraint checks (C3, C4, C5).
5. quest-generator-v4.py that consumes from the DB instead of inline dicts.

Do NOT skip to Godot. Step 7 starts only after end-to-end test passes
with quests sourced from the DB.

---

## 2026-06-09 — End of Day

### Completed today
- Step 5: Four quest templates built and validated
- quest-generator-v3.py routing all four templates
- Step 6 design document completed (fact-database-design.md)
- Gossip propagation Open Question 1 resolved
- Ready to build SQLite migration script tomorrow

### Tomorrow starts here
Send to Claude Code: "Read PROJECT-CONTEXT.md and
build-log.md. We are ready to build Step 1 of Step 6
implementation: the SQLite schema migration script
(init_db.py). Follow the implementation order in
fact-database-design.md."

### Research done today
- Perplexity searches on SQLite game state, gossip
  propagation, spy/noir game settings
- Results saved to raw/articles/ for ingestion tomorrow
