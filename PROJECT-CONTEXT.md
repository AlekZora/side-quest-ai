# Side Quest AI System — Project Context

## What we are building
A side quest AI system for a 2D game where NPCs with 
defined situations generate contextually appropriate 
quests based on player history. One product, not two 
separate paths. The game demo IS the studio pitch.

## The four problems we solve
1. Grounding — AI only generates quests referencing 
   things that actually exist in the game world
2. Simulator layer — world state tracks what actually 
   happened, not statistical plausibility
3. Persistent memory — NPC knowledge propagates through 
   gossip network, persists across session
4. Design language — inventing the craft vocabulary 
   for AI-driven narrative that doesn't exist yet

## Architecture
Renderer → Simulator → Planner stack.
Game state JSON is the simulator layer.
Quest generator is the planner.
Dialogue is the renderer.
LLM never touches world state directly — only reads it.

## Experience goal
"The player feels a moment of disorienting recognition: 
the world has been paying attention to their specific 
story, not the generic one, and an NPC is now speaking 
directly to it."

Test: player asks "how did they know that?"
Failure: player accepts quest without reading it.

## Setting direction (decided 2026-07-24)
World / content foundation: **Greek mythology.** The player is an 
original mortal — a "nobody" by mythic standards — living in the 
margins of the canonical myths. Famous hero-arcs (Heracles' labours, 
Jason's voyage, Theseus' road to Athens) run as fixed canonical 
backdrop; the AI generates the *player's* side quests around them. 
Recognition moment reframed: the mythic world notices someone it had 
no reason to notice.

Why it fits the system (structural, not aesthetic):
1. Myth corpus = ready-made relational world-model / consistent fact 
   DB. Anchor source: Apollodorus's *Library* (ingested 2026-07-23); 
   see wiki/concepts/genealogy-as-knowledge-graph.md.
2. Genre is natively variant-tolerant ("according to some… according 
   to others…") — generative variance reads as canon, not hallucination.
3. Myth's moral engine (xenia, hubris/nemesis, enforced oaths, delayed 
   divine consequence) already IS the experience goal.

Maps onto the "Key constraints" below: canonical hero-arcs = the fixed, 
human-authored main story; player side quests = the generated margin. 
Two-tier canon (immutable spine vs. mutable margin) → simulator holds 
canonical events as fixed facts; planner generates around them; 
validator must encode the canonical spine.

Top risks to manage: (1) tone / content curation — source is very dark, 
the LLM will drift there; lean stylized / mythic-abstract + curation 
layer. (2) Scope creep — scope the demo to ONE locale with one canonical 
arc as backdrop. Candidate locale (NOT locked): road from Troezen to 
Athens (Theseus's road-clearing chain).

Not yet locked: locale, player-character specifics, tone treatment. 
Does NOT change the current build step — still Step 7 (Godot). 
Full reasoning: wiki/decisions/decision-log.md (2026-07-24 entry).

## What has been built
- quest-generator-v1.py — working, tested on 5 states
- test-states.json — 5 validated game state variations
- requirements.txt
- GitHub repo: github.com/AlekZora/side-quest-ai (private)
- Experience goal: wiki/projects/game/experience-goal.md
- Gap report: wiki/projects/game/gap-report.md
- Project positioning: wiki/projects/game/project-positioning.md
- Game state schema: wiki/projects/game/game-state-schema.json
- Game state reasoning: wiki/projects/game/game-state-schema-reasoning.md
- NPC schema: wiki/projects/game/npc-schema.json
- NPC schema reasoning: wiki/projects/game/npc-schema-reasoning.md

## The gap report priority order — follow this exactly
1. ✅ Experience goal statement
2. ✅ Standalone generation test harness
3. ✅ Minimum game state schema — 5 fields
4. ✅ Minimum NPC schema — 5 fields
5. ✅ Four quest templates — COMPLETE
      File: wiki/projects/game/quest-templates.md
      quest-generator-v3.py routes all four templates
6. ✅ Fact database and hard-constraint validator — COMPLETE
      Files: init_db.py, seed_db.py, pipeline.py, validator.py,
             quest-generator-v4.py, blackwater.db
7. ⬜ Godot setup — NEXT
8. ⬜ Q6 experiment protocol

## Current step
Step 7 — Godot setup.
Do not build more prototype features before Godot is running.

## Known Issues

### V1 VALIDATOR ISSUES — fix before Q6 experiment (Step 8)
- C1: The C1 structural check regex handles **N.** (Markdown bold)
  but not ## N. (Markdown section headers). Model sometimes chooses
  the header format. Fix: extend regex to match `##?\s*` prefix OR
  add format constraint to quest generator prompt ("Use plain numbered
  list: 1. WHY ..."). Estimated: 10 minutes.

### V2 VALIDATOR ISSUES — fix before public demo
- C3: Heuristic proper-noun extractor (Title-Case regex) produces
  false positives for sentence-start words paired with entity names
  or safe words (e.g. "But Otto", "No Syndicate"). Fix: replace
  heuristic NER with a trained named entity recognition model.
  Estimated: 1-2 days.

## Key constraints
- Main story is human authored and fixed
- NPCs can respond to player history but cannot 
  resolve main story beats
- Constraint layer enforces what NPCs can promise
- World builders create characters and situations
- System generates collisions and quests

## Tech stack decided
- Python for prototype
- Claude Haiku API for generation
- SQLite for fact database (when built)
- Godot for game engine (step 7, not now)

## Files location
wiki/projects/game/ — all project files
wiki/projects/game/prototype/ — code files
wiki/concepts/ — theoretical foundation (62 concept pages)
wiki/projects/game/gap-report.md — source of truth for priorities
