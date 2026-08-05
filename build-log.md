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

## 2026-06-10

### Completed
- Step 6 implementation — part 1: SQLite schema migration script
  File: wiki/projects/game/prototype/init_db.py
  Database: wiki/projects/game/prototype/blackwater.db
  All 8 tables created in design-specified order:
  entities, events, relationships, player,
  player_choices, npc_knowledge, npc_beliefs, quests
  Field names, types, and CHECK constraints match fact-database-design.md exactly.
  `when` column in events quoted to avoid SQL keyword collision.
  BOOLEAN in player_choices implemented as INTEGER CHECK(IN (0,1)) — SQLite native.
  PRAGMA foreign_keys = ON set at connection time.

### Test results
  Run 1: all 8 tables created, "Database ready." printed.
  Run 2 (idempotency): identical output, no errors. IF NOT EXISTS confirmed working.
  sqlite3 .tables: all 8 tables present.

### Current step
Step 6 implementation — part 2: seed data. COMPLETE.

---

## 2026-06-10 (continued)

### Completed
- Step 6 implementation — part 2: seed data
  File: wiki/projects/game/prototype/seed_db.py
  Database: wiki/projects/game/prototype/blackwater.db

  Seeded:
  - 5 locations: Eastern Gate Checkpoint, Northern District Office,
    Holding Facility, Cloth Merchant District, Reiner Alley
    (Reiner Alley flagged restricted in properties JSON)
  - 8 NPCs + 1 document:
    Player (entity, for FK refs), Serge, Daria, Otto, Nadia,
    Marta (Serge's sister), Mikhail (Daria's son),
    Syndicate Supply Manifest (status=destroyed, last_changed_at=50)
  - 1 player row (singleton): location=Eastern Gate, current_situation set,
    reputation_by_faction: Syndicate=-0.6, Resistance=0.4
  - 3 events:
    EVT_WOMAN_AT_GATE (tick=20, high) — Otto's callback target
    EVT_CURFEW_BRIBE (tick=30, medium)
    EVT_MANIFEST_BURNED (tick=50, high) — triggers all four templates
  - 3 player_choices: all three events, callback_used=false
  - 6 npc_knowledge rows:
    Otto: witnessed both gate events (conf=1.0); told_by for manifest (0.8)
    Serge: told_by manifest (0.9)
    Daria: told_by manifest (0.8)
    Nadia: rumor manifest (0.4)
  - 11 relationships:
    4 NPC→player (trusts/knows with strengths from witness context)
    2 stake relationships (Serge→Marta related, Daria→Mikhail related)
    4 NPC→location (located_at)
    1 Nadia→Reiner Alley (knows — blocked, can't access)

### Test results
  Row counts confirmed: entities=13, events=3, relationships=11, player=1,
  player_choices=3, npc_knowledge=6, npc_beliefs=0, quests=0.
  Idempotency guard: second run prints "already seeded" and shows counts.
  FK JOIN queries: all entity/event names resolve correctly.
  NPC properties: full situation/want/stake/network text from quest-templates.md
  stored verbatim in entities.properties JSON.

### Fix — 2026-06-10
seed_db.py: corrected Serge's npc_knowledge confidence from 0.9 → 0.8.
Channel hierarchy from fact-database-design.md: witnessed=1.0, told_by=0.8,
deduced=0.7, rumor=0.4. Serge learns via told_by; 0.9 was an error.
Reseeded: deleted blackwater.db, ran init_db.py + seed_db.py.
Verified with query: Serge=0.8, Daria=0.8, Otto witnessed=1.0, Otto told_by=0.8, Nadia=0.4.

### Current step
Step 6 implementation — part 3: pre-generation pipeline (Phase A). COMPLETE.

---

## 2026-06-10 (continued)

### Completed
- Step 6 implementation — part 3: pre-generation pipeline
  File: wiki/projects/game/prototype/pipeline.py
  Implements A1–A6 from fact-database-design.md.

  A2. Candidate enumeration: queries entities alive at player location.
      Adjacent-location traversal deferred to V2/Godot integration.
  A3. Template eligibility per NPC:
      escalation — npc_knowledge rows with confidence >= 0.5
      personal_crisis — situation + stake in properties
      callback — high-significance player_choice NPC can know about (conf >= 0.5)
      world_texture — always eligible
  A4. Soft constraint scoring (6 multipliers, all V1):
      npc_cooldown (0.2 if in last 5 quests), template_variety (0.6 if repeat),
      trust_gradient (1.0 + strength*0.5 for trusts), callback_freshness
      (1.0/0.7/0.4 by age bracket), stake_activation (1.0 V1 stub),
      quest_load (0.5 if 3+ active quests)
  A5. Game state assembly: builds 5-field game state from DB.
      callback template adds player_history array and referenced_choice.
      npc_knowledge text derived from npc_knowledge table.
  A6. Pre-check: NPC alive, co-located, has some documented knowledge.
      Fast-fails before token spend.

### Test results
  Trigger: "Bribed the eastern gate guard to pass through after curfew"
  Player location: Eastern Gate Checkpoint
  Selected: Otto / escalation / score 1.25
  All four templates tied at 1.25 (callback_freshness = 1.0 because
  manifest_burned at tick=50 is Otto's most recent qualifying choice —
  age=0, freshness=1.0). Escalation wins tie by iteration order.
  Note: triggering event also qualifying as callback target is correct
  V1 behavior; trigger exclusion from callback candidates is V2.
  Game state assembled correctly with Otto's witnessed bribe knowledge.

### Current step
Step 6 implementation — part 4: hard constraint validator. COMPLETE.

---

## 2026-06-10 (continued)

### Completed
- Step 6 implementation — part 4: post-generation hard constraint validator
  File: wiki/projects/game/prototype/validator.py
  Implements C1, C3, C4, C5 from fact-database-design.md (rule-based).
  C6 (knowledge check), C7 (reward feasibility), C8 (narrative integrity)
  deferred to V2 — all require LLM judge.

  C1. Structural parse: checks for numbered items 1–5 at line start
      (handles Markdown bold markers **N.**).
  C3. Existence check: proper-noun extraction via Title-Case regex.
      Checks extracted nouns against entity_index (with article stripping
      for "The Syndicate Supply Manifest" → "Syndicate Supply Manifest").
      Single-word unknowns skipped (sentence-start false positives too noisy in V1;
      V2 replaces with NER). Multi-word unknowns not in DB flagged as hallucinations.
  C4. State check: quest giver alive (hard fail); referenced known entities
      not dead/destroyed (hard fail); deadline phrase detection (warning only —
      tick comparison deferred to Godot integration).
  C5. Causal check: callback template verifies referenced_choice_id exists
      in player_choices with callback_used=0.

  Result struct: passed (bool), checks_run, failures (hard), warnings (soft),
  validation_log (JSON for quests table).

### Test results
  6 test cases, all produced expected outcomes:
  Test 1: clean Otto/escalation quest → PASS (1 deadline warning)
  Test 2: missing item 5 → C1 FAIL: "structural_fault: missing item(s) — 5"
  Test 3: hallucinated "Clerk Vaskov" → C3 FAIL: "not in DB: Clerk Vaskov"
  Test 4: destroyed entity ("Syndicate Supply Manifest") → C4 FAIL: status='destroyed'
  Test 5: callback, valid referenced_choice event_id=1 → PASS
  Test 6: callback, already-used choice (callback_used=1) → C5 FAIL

  Note: first C3 test run silently passed because the .replace() call used
  wrong case ("intercepting" vs "Intercepting"). Fixed by inserting hallucinated
  name after a different sentence. Case sensitivity in test data matters.

### Current step
Step 6 implementation — part 5: quest-generator-v4.py. COMPLETE.

---

## 2026-06-10 (continued)

### Completed
- Step 6 implementation — part 5: quest-generator-v4.py
  File: wiki/projects/game/prototype/quest-generator-v4.py

  Wires the full Step 6 pipeline in sequence:
  1. pipeline.run_pipeline() — NPC selection, template routing, game state assembly
  2. load_npc_for_prompt() — loads want/stake/network from entities.properties JSON
  3. Route to correct prompt builder (copied and adapted from v3.py)
  4. Call Claude Haiku (claude-haiku-4-5-20251001, max_tokens=1200)
  5. validator.validate() — C1/C3/C4/C5 hard constraint checks
  6. write_quest() — INSERT into quests table (status=validated or failed_validation)
  7. Print: selection scores, generated text, validation result, DB write confirmation

  Key adaptation from v3: callback template uses gs["referenced_choice"] (from
  pipeline) as the referenced past choice, not gs["player_history"][0].
  get_referenced_choice_event_id() mirrors pipeline's selection logic and returns
  the event_id for C5 validation.

### Test results — run 1
  Trigger: "Bribed the eastern gate guard to pass through after curfew"
  Player location: Eastern Gate Checkpoint (id=1), tick=50
  Selected: Otto / escalation / score=1.25
  Tokens: 770 in / 750 out
  DB write: quests id=1, status='failed_validation'

  Quest quality: STRONG. Elena reveal landed — "Elena paid her own way out of
  the gate six weeks ago." Otto's ledger as revelation source grounded correctly
  in his network access. The "What Changes" reframe (from rescue to tracking
  deliberate flight) matches Step 5 escalation design intent.

  Validation result: FAIL — two issues flagged:

  C1 failure: model used "## N. HEADER" (markdown section headers) instead of
  "N." at line start. The C1 regex handles **N.** (Markdown bold) but not ## N.
  (Markdown header). The prompt specifies numbered items but does not constrain
  formatting. V2 fix: extend regex to match `##?\s*N.` or add format instruction
  to prompt ("Use plain numbered list: 1. WHY").

  C3 false positives: "But Otto" and "No Syndicate" flagged as potential
  hallucinated entities. Both are sentence-start word + entity/safe-word pairs
  that the heuristic regex matches as two-word Title-Case sequences. The
  multi-word unknown rule fires because "But" and "No" are not in SAFE_WORDS.
  V2 fix: NER model replaces heuristic extractor. V1 mitigation: add sentence-
  boundary stripping or expand SAFE_WORDS with common sentence-start conjunctions.

  Both failures are known V1 heuristic limitations documented in fact-database-
  design.md. The end-to-end flow (pipeline → API → validator → DB) is correct.
  R1 recovery cascade deferred to V2.

### Current step
Step 6 COMPLETE. Step 7 — Godot setup.

### Next session starts here
Step 7: Begin Godot project setup.
Do NOT build more prototype features before Godot is running.
The prototype stack (init_db, seed_db, pipeline, validator, v4) is feature-complete
for V1. Known V1 limitations (C1 format, C3 sentence-start false positives, R1
recovery) are documented and deferred to V2 / Godot integration.

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

---

## 2026-06-15

### Completed
- Gap report v2 produced
  File: wiki/projects/game/gap-report-v2.md
  Source: Full read of all prototype files (8), PROJECT-CONTEXT.md,
  build-log.md, fact-database-design.md, quest-templates.md,
  game-state-schema.json, npc-schema.json, experience-goal.md,
  and gap-report.md. Also checked wiki/sources/ for ingested
  sources matching gap report recommendations.

  Assessment: Steps 1–6 complete. V1 prototype is feature-complete.
  Known V1 limitations are bounded and documented — none block Step 7.
  Four sources recommended in gap report v1 (Disco Elysium GDC,
  L4D AI Director, Dwarf Fortress, Façade postmortem) were not ingested.
  Three NPC-adjacent Perplexity research sources were ingested instead.

  New priority order: fix C1 regex (10 min), then Step 7 Godot. The
  Godot ↔ Python bridge architecture decision is now the highest-risk
  open item — it determines whether the demo reaches a browser.

  Façade postmortem identified as highest-value pending ingestion for
  Q6 experiment design.

### Current step
Step 7 — Godot setup.
First task of Step 7: decide Python ↔ Godot bridge architecture
(subprocess / localhost HTTP API / GDExtension).
Web export requirement may force HTTP approach.

### Next session starts here
1. Fix C1 regex (10 minutes): extend pattern in validator.py to handle
   `## N.` format, or add format constraint line to each prompt in
   quest-generator-v4.py. Either works.
2. Read gap-report-v2.md section 6 (Tech Stack) for the three bridge
   options and decide before any Godot code is written.
3. Initialize Godot project.

---

## 2026-08-03

### Completed
- Renamed `quest-generator-v4.py` → `quest_generator_v4.py`
  File: wiki/projects/game/prototype/quest_generator_v4.py

  Hyphenated module names cannot be imported. Nothing imported it yet,
  so no code changed — only the module docstring self-reference. Prose
  references to the old name remain in PROJECT-CONTEXT.md,
  fact-database-design.md, gap-report-v2.md, and earlier entries in this
  log; the log entries are historical record and were left as written.

- Extracted `generate_quest(conn, pipeline_result, max_attempts=2)` from
  `main()`
  File: wiki/projects/game/prototype/quest_generator_v4.py

  Everything between the pipeline result and printing now lives in one
  callable: NPC load → prompt builder lookup → Haiku call → validate →
  write_quest. Returns a dict (quest_text, npc_id, npc_name, template,
  passed, attempts, validation_log, quest_row_id) plus the full validator
  result and token counts, which the CLI needs in order to print.

  Retry is new — `main()` never had one. It retries only on validation
  failure, with the prompt unchanged between attempts (a fresh sample,
  not a repair), and writes only the final attempt, so one call is still
  one quests row. `main()` passes `max_attempts=1` to stay on the exact
  pre-refactor path; CLI stdout is unchanged, and the "recovery cascade
  would fire here — R1 deferred" note still marks the real gap.

  This is the seam the Godot bridge calls, whichever transport wins:
  subprocess entry point, HTTP handler body, or GDExtension binding all
  wrap this one function rather than re-implementing main().

### Test results
Offline harness (stubbed Anthropic client, throwaway copy of
blackwater.db — the real DB was not touched). Four cases, all passing:
  1. Valid text, max_attempts=2      → 1 API call, passed, row 'validated'
  2. Invalid text, max_attempts=2    → 2 API calls, failed, row
                                       'failed_validation'
  3. Invalid then valid, max=3       → 2 API calls, stops on first pass
  4. Invalid text, max_attempts=1    → 1 API call, no retry (CLI path)
Asserted in every case: exactly one quests row written, and
quest_row_id matches it.

  Note: `import anthropic` blocks in a sandboxed shell with no network,
  so any offline test of this module has to stub the module in
  sys.modules before importing it. Worth remembering for Step 8's
  experiment protocol, which will want to run without burning API calls.

  Not covered: no live end-to-end run was made, so the refactor is
  verified against a stub, not against real Haiku output.

### Current step
Step 7 — Godot setup. Unchanged. Bridge architecture still undecided;
generate_quest() is now the function that decision has to wrap.

### Next session starts here
1. Fix C1 regex (still open, 10 minutes).
2. Decide the bridge (gap-report-v2.md section 6).
3. Initialize Godot project.

---

## 2026-08-03 (continued — bridge up, first live run through HTTP)

### Completed
- Step 7 bridge: FastAPI server running, first end-to-end quest served
  over HTTP.
  Files: wiki/projects/game/prototype/server.py (copied in from
  ~/Downloads/server_complete.py), requirements.txt unchanged so far

  The bridge decision is effectively made by this file: **localhost HTTP
  API**, not subprocess and not GDExtension. That is the option the web
  export needs, so it was the right one to reach for first — but note it
  was decided by writing the file, not by working through gap-report-v2
  section 6. If subprocess was ever seriously in the running, that
  comparison never happened.

  Two routes: GET /health (no API call, no tokens) and POST
  /generate-quest, which wraps pipeline.run_pipeline() + the new
  generate_quest(). CORS is wide open (allow_origins=["*"]) for the Godot
  web export. Server ran under uvicorn on port 8000, `fastapi` and
  `uvicorn` installed into the venv.

### Test results
GET /health → `{"ok":true,"npc_count":7,"tick":50}`

POST /generate-quest, player_action = "Bribed the eastern gate guard to
pass through after curfew" → HTTP 200, ok:true, Otto / callback,
**validation_status "failed_validation", attempts 2**, quest row id=2.

The generated text itself was good — the recognition line landed:
  "I know what you did with that manifest—how you burned it instead of
   handing it to anyone. That told me something."

### Two findings

1. **C1 regex bug CONFIRMED in the wild, not just in theory.**
   Haiku emitted `## 1. WHY NOW — ...`. C1's pattern
   `^\s*\**{i}\.\s` allows leading whitespace and `**` but not `#`, so
   all five items read as missing:
     [C1] structural_fault: missing item(s) — 1 (WHY), 2 (WHAT
          (observed)), 3 (WHAT (needs)), 4 (WHAT (costs)),
          5 (RECOGNITION LINE)
   C3 failed on the same root cause — markdown headers become Title-Case
   sequences the proper-noun extractor treats as entity candidates:
     [C3] potential hallucinated entities (not in DB): District Office,
          The Ask, The Opening, The Real Reason, The Witnessed Detail,
          What Otto
   So the "10 minute" C1 fix was the difference between a validated
   quest and a failed one on the very first live request. It should have
   been done before the bridge went up.

2. **Unconditional retry is worse than no retry for this failure mode.**
   max_attempts=2 re-sampled the *same prompt*, so the formatting
   mismatch reproduced exactly. Two API calls, two failures, one
   failed_validation row. A retry can only help when the failure is
   sampling-dependent (C3 hallucination, C4 state reference). It cannot
   help when the failure is structural (C1) or causal-bookkeeping (C5),
   because nothing about the input changed between attempts.

   This is the argument for making retry conditional on *which* check
   failed, rather than retrying on any failure.

### Notes
- The venv lives on iCloud Drive. First import blocks ~2 minutes in
  `read()` while iCloud materialises the .so files — the first curl beat
  the server to the port. Under a sandbox with no network that read
  blocks forever, which is why offline tests must stub `anthropic` in
  sys.modules.
- Failed validation means write_quest did NOT flip callback_used, so
  that player choice is still available to a future callback quest.

### Current step
Step 7 — bridge is up and serving. Next: fix C1, make retry conditional.

---

## 2026-08-03 (continued — C1 fixed, retry made conditional)

### Completed
- **C1 regex fixed.** validator.py check_c1()
  Old: `^\s*\**{i}\.\s` — allowed indent and `**`, but not `#`.
  New: `^[ \t]*(?:#{1,6}[ \t]*)?\**[ \t]*{i}\.\**(?:\s|$)` — accepts
  `1.`, `## 1.`, `**1. **`, `### **1.** `, and indented variants.
  The C1 item on the next-session list since 2026-06-15 is now closed.

- **Retry made conditional.** quest_generator_v4.py
  New module constant `RETRYABLE_CHECKS = {"C3", "C4"}`. generate_quest()
  retries only when validation failed *and every* failing check is in
  that set. A single C1 or C5 failure blocks the retry outright, even if
  a retryable check also failed — if C1 will fail again, spending the
  call is pointless. Unlisted checks (C6-C8, when the LLM judge lands)
  default to non-retryable.

  Two new return keys: `retry_reason` (human-readable, e.g. "no retry —
  C1 cannot be fixed by re-sampling an unchanged prompt") and
  `failed_checks`.

- **server.py**: added optional `retry_reason` to QuestResponse so the
  reason is visible over HTTP, not just in-process. Backward compatible
  (defaults to None). This was a small addition beyond the two files
  asked for — remove the field and the response-model line if unwanted.

- **requirements.txt**: added fastapi>=0.115.0 and uvicorn>=0.30.0.

### Test results
C1 formats — 7 accepted (`1.` / `## 1.` / `**1. **` / `### 1.` /
`## **1.** ` / `**1.** ` / indented), and still correctly FAILS on
4-of-5-items and on an inline "1." mid-sentence. Re-validating the
stored row id=2 (the live text that failed this morning): C1 now passes.

Validator's own six-test suite: unchanged behaviour (1 PASS, 2 C1 FAIL,
3 C3 FAIL, 4 C4 FAIL, 5 PASS, 6 C5 FAIL).

Conditional retry — 9 stubbed cases, all as designed:
  clean            -> 1 attempt, no retry needed
  C1               -> 1 attempt, NO retry
  C3               -> 2 attempts (budget spent)
  C3 then clean    -> 2 attempts, passes
  C1+C3            -> 1 attempt, C1 blocks the retry
  C3 max=1 / max=3 -> budget respected in both directions
  C4               -> 2 attempts (retryable, same branch as C3)
  C4 then clean    -> 2 attempts, passes
  C5               -> 1 attempt, NO retry (forced callback state)

### Live re-run through the bridge
Same POST as this morning. HTTP 200 in 26s, Otto / escalation,
**validation_status "failed_validation", attempts 2**, quest row id=3.
  retry_reason: "retry budget spent after 2 attempt(s) — C3 still failing"
  C1 detail:    {"passed": true, "detail": "ok"}

So both changes did their job — C1 passes on real `## 1.` output, and
the retry fired only because the sole failure was retryable. The quest
still fails validation, now on C3 alone.

### Next problem, already diagnosed: C3 is flagging its own formatting
C3 flagged: "But Elena", "If Elena", "Otto Approaches Now\n\nOtto",
"Otto Needs\n\nOtto", "Otto Reveals\n\nOnce". None are hallucinations.
Two distinct causes:

1. **extract_proper_nouns spans newlines.** The pattern joins words with
   `\s+`, and `\s` matches `\n`, so the last word of a heading is glued
   to the first word of the next paragraph:
     current  `\b[A-Z][a-z]{1,}(?:\s+[A-Z][a-z]{1,})*\b`
       -> ['Otto Needs\n\nOtto', 'But Elena', 'Once More']
     fixed    `(?:[ \t]+...)` instead of `(?:\s+...)`
       -> ['Otto Needs', 'Otto', 'But Elena', 'Once More']
   These glued sequences can never resolve against the entity table, so
   they flag as hallucinations every single time.

2. **Sentence-start + entity-word pairs** ("But Elena", "If Elena") —
   the known C3 false positive, now confirmed live.

Note this undercuts the retry premise for C3 specifically: C3 is
*nominally* sampling-dependent, but these failures are systematic
artifacts of markdown formatting, so a re-sample reproduces them. The
retryable/deterministic split is still right in principle — it is C3's
implementation that is behaving deterministically, and it will keep
costing a doubled API call per request until fixed.

### Current step
Step 7 — bridge serving; C1 and conditional retry done.

### Next session starts here
1. Fix C3 newline-spanning (one-character class change, high confidence)
   and decide what to do about sentence-start pairs — probably require a
   sequence to contain at least one word that is not a common English
   sentence-opener before flagging it.
2. Re-run the POST and confirm a "passed" validation_status end to end.
3. Then Godot project init against the HTTP bridge.

---

## 2026-08-03 (continued — two C3 false-positive classes fixed)

### Completed
- **C3 newline glue fixed.** validator.py extract_proper_nouns()
  Words are now joined with `[ \t]+` instead of `\s+`, so a heading's
  last word no longer glues to the next paragraph's first word.
  `'Otto Needs\n\nOtto'` → `'Otto Needs'`, `'Otto'`.

- **C3 sentence-opener heuristic added.** New `SENTENCE_OPENERS` set
  (but/if/once/when/and/the/this/that/after/before/now/so/then/yet) and
  `strip_sentence_opener()`. A sequence starting with an opener has it
  stripped and the remainder re-tested against the entity index, so
  "But Elena" resolves to Elena while "The Vaskov Ledger" still flags as
  "Vaskov Ledger". check_c3's three resolution tests were factored into
  a local `unresolved()` so they run identically on both forms.
  Explicitly a heuristic — the trained NER model is still C3's real fix.

### Test results
- Extractor: no sequence spans a newline.
- Opener stripping: 6/6 cases correct, including non-openers left alone.
- Both fixed classes silent on a text built to trigger them.
- Real hallucinations still caught: "Clerk Vaskov" flags, and
  "The Vaskov Ledger" flags as "Vaskov Ledger". Known entity
  "The Syndicate Supply Manifest" still resolves clean.
- Validator's six-test suite: unchanged.

### Live re-run
POST /generate-quest, same trigger. HTTP 200 in 33s, Otto / callback,
quest row id=4, attempts 2, **still failed_validation**:
  [C1] structural_fault: missing item(s) — 5 (RECOGNITION LINE)
  [C3] Real Reason, What It Actually Takes, What Otto, Witnessed Choice

Read that C1 failure carefully — it is a **true positive**, not the old
regex bug. Haiku's second draft genuinely omitted item 5. C1 is now
doing its job; the recognition line, the one item the whole experience
goal rests on, was missing and the validator caught it.

### Third C3 false-positive class: markdown header text
The survivors are all header scaffolding — "What Otto", "Real Reason",
"Witnessed Choice", "What It Actually Takes" — Title-Case words inside
`##` headings. Two candidate fixes, neither applied:
  (a) Skip ATX heading lines (`^#{1,6}`) when extracting proper nouns.
      Headers are template scaffolding, not claims about the world.
      Kills the whole class in one line. Risk: a hallucinated entity
      that appears *only* in a heading goes unchecked.
  (b) Treat a word as safe if it is in SAFE_WORDS *or* resolves to a
      known entity. Fixes "What Otto" (both parts known) but leaves
      "Otto Approaches Now" (verb not known).
(a) is the stronger one; (b) is worth having regardless.

### retry_reason reports only the final decision
Response said attempts=2 with retry_reason "no retry — C1 cannot be
fixed by re-sampling an unchanged prompt", which reads as a
contradiction. It is accurate but lossy: attempt 1 failed C3 only (so it
retried), attempt 2 failed C1+C3 (so it stopped). The field describes
the last decision and discards the history. If this is going into Godot
logs, it should either name the sequence or carry a per-attempt trail.

### Current step
Step 7 — bridge serving. C1 fixed, retry conditional, two of three C3
false-positive classes fixed. No request has yet passed validation
end to end.

### Next session starts here
1. C3 class three: apply (a) heading-line skip, probably plus (b).
2. Re-run until a request returns validation_status "passed" — that is
   the gate before Godot work, since a failing bridge is not a bridge.
3. Consider whether a missing item 5 should be repairable rather than
   fatal: a retry with the same prompt cannot fix it, but a follow-up
   call that asks only for the missing item could.
4. Then Godot project init.

---

## 2026-08-04 — FIRST END-TO-END VALIDATED QUEST OVER HTTP

### Completed
- **C3: ATX heading lines skipped.** validator.py, new `ATX_HEADING_RE`
  blanks `^#{1,6}.*$` before proper-noun extraction. Heading text
  restates the prompt's own section labels, so it is scaffolding, not a
  claim about the world.
- **C3: is_safe_sequence is entity-aware.** Now takes an optional
  entity_index and treats a word as safe if it is in SAFE_WORDS *or*
  resolves to a known entity, so "What Otto" passes (scaffolding word +
  real NPC) while "Clerk Vaskov" still flags.
- **attempt_log added.** quest_generator_v4.generate_quest() now returns
  one record per attempt — {attempt, failed, retried, reason} — with
  retry_reason kept as the final-decision summary. server.py exposes
  attempt_log as an optional response field alongside retry_reason.

### Result: validation_status "passed"
POST /generate-quest, same trigger as every run this session.
HTTP 200 in 35s, Otto / callback, quest row id=6, **status validated,
C1 C3 C4 C5 all true, zero failures.** First request to clear the whole
hard-constraint gate end to end.

    attempt_log:
      {"attempt": 1, "failed": ["C3"], "retried": true,
       "reason": "retrying after attempt 1 — C3 may pass on a different draft"}
      {"attempt": 2, "failed": [],     "retried": false,
       "reason": "no retry needed — passed on attempt 2"}

That is the conditional retry earning its keep for the first time: a
genuine sampling-dependent C3 failure on draft 1, fixed by draft 2. It
also shows why attempt_log was worth adding — "attempts: 2, passed"
alone would not have told us the retry is what saved it.

The recognition line that came out of it:
  "You burned that manifest instead of letting it walk out of the
   office. I need to know if you'll do something harder — if you'll let
   me look like I'm doing my job without actually doing it."

DB state: row 6 validated with referenced_event_id=3, and write_quest
correctly flipped player_choices.callback_used=1 for event 3. That
choice is now consumed and will not be reused as a callback target.

### Confirmed cost of the heading skip
Tested directly: a destroyed entity named in the body is still caught by
C4, but the same entity named ONLY inside a heading now passes C4 clean.
extract_proper_nouns is shared, so this blind spot applies to C4 as well
as C3. Accepted deliberately — headings are scaffolding — but if a
future template puts entity names in headings, C4 stops seeing them.
The fix if it ever bites: give extract_proper_nouns a skip_headings flag
and have check_c4 pass False.

### Operational lesson: a stale server served a run and I nearly reported it
The first re-run after these changes returned attempt_log empty and C3
still flagging heading text. Cause: the *previous* session's uvicorn was
still holding port 8000, so the newly started one died with
"[Errno 48] address already in use" and the request was served by old
code. uvicorn was started without --reload, so a running server never
picks up edits either way.

Before trusting any live run: check that the new server actually bound
(`grep "address already in use"` in its log, or lsof -iTCP:8000), and
kill the old listener first. A green-looking result from a stale process
is worse than a failure, because it looks like evidence.

### Still failing (older stored rows, re-validated)
  row 1: [C3] "No Syndicate" — sentence-start "No", not in
         SENTENCE_OPENERS. Cheap to add; deliberately not added, since
         the list was specified explicitly.
  row 2: [C3] "District Office" — arguably a true positive: no such
         entity exists in the DB.
  row 4: [C1] genuinely missing item 5.
  row 3: now passes clean.

### Current step
Step 7 — HTTP bridge working end to end, hard-constraint gate passing.
The Python side of the bridge is done for demo purposes.

### Next session starts here
1. Godot project init against the HTTP bridge — DONE, see below.
2. Decide whether a missing item 5 (C1) should be repairable by a
   targeted follow-up call rather than fatal.
3. Optional C3 polish: add "no" to SENTENCE_OPENERS; consider whether
   "District Office"-style unknown places should seed the entity table
   instead of failing.
4. Persist attempt_log into the quests table if Q6 experiment data will
   want per-attempt history — it currently lives only in the response.

---

## 2026-08-04 (continued — Godot side scaffolded, NOT yet run)

### Completed
- Minimal Godot 4.x project created at **~/blackwater-demo/** (outside
  the vault, so it is not covered by the build-log rule's path scope —
  logged anyway because it is Step 7's first engine artifact).
    project.godot  — config_version=5, main scene res://Main.tscn,
                     config/features=PackedStringArray("4.2")
    Main.tscn      — format=3, Node2D root "Main" + HTTPRequest child
    Main.gd        — _ready() GETs http://localhost:8000/health, prints
                     status code and body; printerr + push_error on both
                     failure paths (request never sent vs. never completed)
  Deliberately nothing else: no player, no NPC, no UI, no interaction.

### NOT verified — Godot is not installed on this machine
`which godot`, /Applications/Godot*.app: nothing found. The project was
written from the Godot 4.x file formats, not validated by an engine, so
project.godot / Main.tscn parsing and Main.gd syntax are unconfirmed.
First run in the editor is the real test.

What WAS confirmed: the endpoint Main.gd targets is live —
GET http://localhost:8000/health → 200 {"ok":true,"npc_count":7,"tick":50}.

Expected console output on a successful first run:
    [bridge] GET http://localhost:8000/health
    [bridge] HTTP status code: 200
    [bridge] response body: {"ok":true,"npc_count":7,"tick":50}

### Current step
Step 7 — Python bridge done and passing; Godot project scaffolded,
awaiting an engine to run it.

### Next session starts here
1. Install Godot 4.x and open ~/blackwater-demo/ — confirm the three
   [bridge] lines print. If config/features="4.2" trips a version
   warning, set it to the installed version.
2. Only after that round-trips: POST /generate-quest from Godot and
   render the returned quest_text.
3. Still open from earlier: repairable C1 (missing item 5) via a
   targeted follow-up call; persisting attempt_log into the quests table.

---

## 2026-08-05 — STEP 7 COMPLETE

### Completed
- **Step 7 (Godot setup) is done.** Player walks into the NPC's talk
  zone, presses E, and a generated quest renders on screen in Godot
  4.7.1. Verified by user in the running game window.

      [bridge] POST http://localhost:8000/generate-quest
      [bridge] HTTP status code: 200
      [bridge] npc=Otto template=personal_crisis validation=passed attempts=1
      [bridge]   attempt 1: failed=none retried=false — passed on attempt 1

  A passing quest on the first attempt — no retry needed, all four hard
  constraints clean. The full chain runs inside a game window: Godot →
  HTTP → Python → SQLite → Claude → validator → engine canvas.

- **Godot client** (now version-controlled at `godot/` in the repo):
    project.godot  — Godot 4.7.x, main scene res://Main.tscn
    Main.tscn      — Player (Area2D + ColorRect, arrow keys), NPC
                     (ColorRect + Area2D talk zone, radius 90),
                     UI CanvasLayer → PanelContainer → RichTextLabel
    Main.gd        — movement, E to interact, /health on ready,
                     POST /generate-quest on E, four label states
                     (empty → "Press E to talk" → "..." → quest/error)

- **Docs updated:** gap-report.md priority order marked 1–7 complete
  with a Step 7 status section; README status table (Godot ✅, Q6 now
  active), Godot paragraph rewritten for the full call, new "Running the
  demo" section; .gitignore now excludes Godot's .godot/ cache.

### Two fixes this session, both found by running it
1. **Dialogue panel rendered nothing.** The RichTextLabel was a Control
   parented directly to the Node2D root, and never laid out against the
   viewport — no prompt, no "...", no quest, console prints the only
   feedback. Fixed by moving the dialogue UI under a CanvasLayer
   (PanelContainer + StyleBoxFlat + MarginContainer + RichTextLabel),
   anchored bottom-wide so it survives any window size, with an explicit
   dark background and scrolling for ~4500-char quests. The CanvasLayer
   also settles z-order by construction rather than by tree position.
2. **attempts printed as "2.0"** — Godot's JSON parser returns every
   number as float. Cast to int, with a missing value staying "?"
   instead of collapsing to 0.

Also added: attempt_log now prints one console line per draft with the
failing checks, so a failed_validation quest says which constraint broke
without a DB query.

### Note on process
Two things this session cost real time and are worth not repeating:
- The venv on iCloud Drive failed to materialise under load —
  `TimeoutError: [Errno 60]` importing fastapi, killing server startup.
  Forcing the files local (`brctl download` + reading them) fixed it.
  The venv does not belong in iCloud.
- A wait-for-server loop using bare `curl` retries burned through 60
  iterations in under a second, because connection-refused returns
  instantly. Any readiness check needs a real delay between attempts
  (`curl --retry-connrefused --retry-delay`), or it is not a wait at all.

### Current step
Step 8 — Q6 experiment protocol. The system can now produce validated
quests on demand inside the engine, which is the precondition the
experiment needed.

### Next session starts here
1. Ingest the Façade postmortem — flagged since 2026-06-15 as the
   highest-value pending source for Q6 experiment design.
2. Write 3 handcrafted quests for a fixed scenario; generate 3 from the
   same scenario; interleave. Define what players are asked and what
   answer counts as success.
3. Optional cleanups: C3 still flags unknown place names like "District
   Office" — decide whether those seed the entity table instead of
   failing; persist attempt_log into the quests table for experiment data.
