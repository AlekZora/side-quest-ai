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

**Intended demo design — not yet built.** The demo will run two 
pre-built player histories through the same NPC, producing two 
visibly different but equally grounded quests. The hero scene 
lands the emotional punch; the reprise proves the system is 
responding rather than scripted.

What exists today: the system generates one validated quest per 
trigger action, served over HTTP. The two-history comparison is 
the target, not current behaviour.

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
| FastAPI bridge (`/health`, `/generate-quest`) | ✅ Complete |
| Godot setup | ✅ Complete |
| Q6 experiment protocol | 🟡 Active |

The HTTP bridge is proven end to end: `GET /health` returns world state,
and `POST /generate-quest` returns a quest that passes every hard
constraint (C1 structure, C3 existence, C4 state, C5 causation) and is
written to the database as `validated`.

The Godot client makes the full call. In Godot 4.7.1, the player walks
into the NPC's talk zone, presses E, and the generated quest renders on
screen in the dialogue panel — Godot → HTTP → Python → SQLite → Claude →
validator → back to the engine canvas. The verified round trip returned
a quest that passed every hard constraint on the first attempt:

```
[bridge] POST http://localhost:8000/generate-quest
[bridge] HTTP status code: 200
[bridge] npc=Otto template=personal_crisis validation=passed attempts=1
[bridge]   attempt 1: failed=none retried=false — passed on attempt 1
```

Visuals are placeholder — coloured rectangles, no art. The engine client
is the transport proof, not the game.

## Repository Structure

All runnable code lives under `prototype/`.

```
├── prototype/
│   ├── server.py                # FastAPI bridge — /health, /generate-quest
│   ├── pipeline.py              # Phase A: NPC + template selection, game state
│   ├── quest_generator_v4.py    # generate_quest(): prompt → API → validate → write
│   ├── validator.py             # Hard-constraint validator (C1, C3, C4, C5)
│   ├── init_db.py               # Database initialization
│   ├── seed_db.py               # Database seeding (Blackwater world)
│   ├── test-states.json         # 5 validated game state inputs
│   └── requirements.txt         # Python dependencies
├── godot/                       # Godot 4.7.1 client (placeholder visuals)
│   ├── project.godot
│   ├── Main.tscn                # Player, NPC + talk zone, dialogue panel
│   └── Main.gd                  # Movement, interact, HTTP calls
├── fact-database-design.md      # Schema, constraints, validation pipeline
├── quest-templates.md           # The four quest templates
├── build-log.md                 # Chronological build log
└── README.md
```

`blackwater.db` is not in the repo — it is generated locally by
`init_db.py` + `seed_db.py`.

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
cd side-quest-ai/prototype

python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here

python init_db.py     # create blackwater.db
python seed_db.py     # seed the Blackwater world
python pipeline.py    # Phase A only — selection + game state, no API call
```

### Running the bridge

The game engine talks to Python over HTTP. From `prototype/`:

```bash
uvicorn server:app --port 8000
```

`ANTHROPIC_API_KEY` must be set in the shell running uvicorn —
`/generate-quest` makes a real Claude API call. Then, in a second
terminal:

```bash
curl http://localhost:8000/health

curl -X POST http://localhost:8000/generate-quest \
  -H "Content-Type: application/json" \
  -d '{"player_action": "Bribed the eastern gate guard to pass through after curfew"}'
```

`/health` is free — no API call, no tokens. `/generate-quest` returns the
quest text plus `validation_status`, `attempts`, and an `attempt_log`
recording why each draft was or was not retried.

## Running the demo

The engine client lives in `godot/`. Built and verified with Godot 4.7.1.

1. **Start the server.** From `prototype/`, with `ANTHROPIC_API_KEY` set
   in that shell:

   ```bash
   uvicorn server:app --port 8000
   ```

2. **Open the Godot project.** Point the Godot project manager at the
   `godot/` folder and let it import.

3. **Press play** (F5). The console prints the `/health` round trip
   immediately:

   ```
   [bridge] GET http://localhost:8000/health
   [bridge] HTTP status code: 200
   [bridge] response body: {"ok":true,"npc_count":7,"tick":50}
   ```

4. **Walk the blue square into the orange one** using the arrow keys.
   Inside the NPC's talk zone the dialogue panel shows `Press E to talk`.

5. **Press E.** The panel shows `...` while the request is in flight —
   expect 20–40 seconds, since this is a real Claude call and may retry
   once — then the generated quest renders in the panel.

If the panel shows `ERROR: ...`, the server is not running or not
reachable; the console carries the underlying result code. A quest can
render with `validation_status: failed_validation` — the console
`attempt_log` lines say which hard constraint failed on each draft.

## License

MIT
