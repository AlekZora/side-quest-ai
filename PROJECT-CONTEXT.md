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
5. ⬜ Three quest templates (main quest escalation, 
      NPC personal crisis, player-choice callback) — CURRENT STEP
6. ⬜ Fact database and hard-constraint validator
7. ⬜ Godot setup
8. ⬜ Q6 experiment protocol

## Current step
Step 5 — write three quest templates.
Do not go to Godot yet.
Do not ask "game path vs AI system path" — it is one product.

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
