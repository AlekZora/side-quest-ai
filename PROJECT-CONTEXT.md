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
