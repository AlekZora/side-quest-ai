# Side Quest AI

> *"We know more than we can tell."* — Michael Polanyi, 1966

A side quest generation system for 2D games. NPCs with defined 
situations generate contextually appropriate quests based on 
player history — grounded, emotionally consistent, and 
responsive to what the player actually did.

## The Problem

Good side quests are expensive to write and usually ignore 
the player's actual history. Generic filler breaks immersion. 
Large writing teams are out of reach for most studios.

**We don't replace world builders — we make them more powerful.**

## How It Works Differently

We treat hallucination as an architecture problem, not a 
model problem.

The LLM reads the game world but never invents it. Everything 
generated is validated against a fact database before it 
reaches the player. Humans author the characters and 
situations. The system generates the collisions between those 
characters and player history. The quest emerges from the 
collision — not from what the writer pre-planned.

This is the Stephen King method made mechanical: know your 
characters deeply, put them in situations, let the story 
emerge from who they are.

## Architecture
 Renderer → Simulator → Planner

- **World state JSON** — the simulator layer (tracks what 
  actually happened)
- **Quest generator** — the planner (reads world state, 
  never writes it)
- **Dialogue** — the renderer
- **Fact database + constraint validator** — ensures every 
  generated quest references only things that actually exist

## Four Problems Solved Simultaneously

1. **Grounding** — AI only references things that exist in 
   the game world
2. **Simulator layer** — world state tracks what actually 
   happened, not statistical plausibility
3. **Persistent memory** — NPC knowledge propagates through 
   a gossip network and persists across sessions
4. **Design language** — craft vocabulary for AI-driven 
   narrative that doesn't yet exist

## The Demo: Blackwater

A fog-bound port town where information is the only currency. 
The central character is the Scrivener — a public letter-writer 
through whom every secret in Blackwater passes.

Emotional register: *the dread of being known.*

The demo runs two pre-built player histories through the same 
NPC, producing two visibly different but equally grounded 
quests. The hero scene lands the emotional punch. The reprise 
proves the system is responding — not scripted.

## Tech Stack

- Python 3.x
- Claude Haiku (Anthropic) — generation
- SQLite — fact database
- FastAPI — HTTP server
- Godot 4.x — game engine (in progress)

## Project Status

| Step | Status |
|------|--------|
| Experience goal statement | ✅ Complete |
| Standalone generation test harness | ✅ Complete |
| Minimum game state schema | ✅ Complete |
| Minimum NPC schema | ✅ Complete |
| Four quest templates | ✅ Complete |
| Fact database + hard constraint validator | ✅ Complete |
| Godot setup | ⬜ In progress |
| Q6 experiment protocol | ⬜ Upcoming |

## Repository Structure

```
├── pipeline.py              # Main pipeline
├── quest-generator-v4.py    # Current generator (all 4 templates)
├── validator.py             # Hard-constraint validator
├── init_db.py               # Database initialization
├── seed_db.py               # Database seeding (Blackwater world)
├── blackwater.db            # SQLite fact database
├── test-states.json         # 5 validated game state inputs
└── requirements.txt         # Python dependencies
```

## The Enterprise Connection

The architecture that prevents hallucination in this game is 
the same architecture that prevents hallucinated actions in 
enterprise AI agents.

- Fact database → company brain
- Constraint validator → grounding system  
- NPC schema → skills file
- Gossip network → tacit knowledge propagation

Same problem, different domain.

## Setup

```bash
git clone https://github.com/AlekZora/side-quest-ai
cd side-quest-ai
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here
python init_db.py
python seed_db.py
python pipeline.py
```

## License

MIT
