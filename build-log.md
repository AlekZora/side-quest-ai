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
