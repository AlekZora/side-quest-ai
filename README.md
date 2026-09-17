# Side Quest AI

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

What an NPC can say is bounded by what an NPC actually knows — and what
an NPC knows is positional, not universal. Otto knows what he personally
witnessed at the checkpoint and what someone told him; he does not know
what Daria knows two districts away unless a fact reaches him through a
specific, recorded channel. Every fact an NPC holds carries where it
came from (`channel` — witnessed, told_by, deduced, rumor) and how much
weight it should carry (`confidence`). Nothing here is tacit — the
opposite, in fact: everything an NPC knows or believes is explicit,
queryable, and traceable back to a specific event. What differs between
NPCs isn't how much goes unsaid, but who had access to what, and how
reliably it reached them.

## Architecture
 Renderer → Simulator → Planner

- **World state (Postgres + pgvector)** — the simulator layer (tracks
  what actually happened, who knows what, and what each NPC currently
  believes)
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
3. **Positional memory** — what an NPC knows is scoped to what
   they witnessed or were told, with provenance and confidence
   attached, and persists across sessions
4. **Design language** — craft vocabulary for AI-driven 
   narrative that doesn't yet exist

## Semantic Retrieval and Belief Formation

Two things built on top of the V1 fact database.

**Semantic retrieval.** The original retrieval matched an NPC's
knowledge of the triggering event by literal substring — it worked only
when the trigger text was close to a verbatim quote of the event text.
Events are now embedded (OpenAI `text-embedding-3-small`, 1536
dimensions, stored in `events.embedding` with an HNSW cosine index),
and retrieval ranks by similarity instead of string matching. The
permission boundary comes first, not the ranking: the query filters by
the `npc_knowledge` join *before* it ranks anything, so an NPC can only
ever retrieve events they actually hold a knowledge row for — never the
wider event table. Similarity decides which of an NPC's own memories is
most relevant; it never decides whether they're allowed to know it.

**Belief formation.** `npc_beliefs` holds conclusions, not facts —
generalizations across multiple known events that could turn out wrong.
Formation is rule-based, not model-based: each belief has a
confidence-weighted threshold over the `npc_knowledge` rows an NPC
holds (summed confidence, not count — a single witnessed fact outweighs
several rumors), and different beliefs need different amounts of
evidence to form (fear generalizes from less evidence than trust). When
a newly-learned event contradicts a held belief, its confidence is
reduced — halved, never zeroed, since one counter-example makes an NPC
uncertain, not converted. An NPC's incorrect belief persists undisturbed
if the correcting event never reaches them; belief state is per-NPC,
exactly like knowledge.

Both feed into the generation prompt, so the model writes from what a
specific NPC has actually seen and concluded — not from the full state
of the game world.

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
- Postgres (Supabase) with pgvector — fact database + embeddings
- OpenAI `text-embedding-3-small` — event embeddings for semantic retrieval
- FastAPI — HTTP server
- Docker + docker-compose — containerized service
- GitHub Actions — CI (lint + image build on every push)
- Godot 4.x — game engine (in progress)

## What Works Today / What's Next

**What works today**

- Full HTTP round trip: `GET /health`, `POST /generate-quest` — a quest
  that passes every hard constraint (C1 structure, C3 existence, C4
  state, C5 causation) and is written to Postgres as `validated`
- The Godot client makes the full call end to end: the player walks
  into an NPC's talk zone, presses E, and a generated, validated quest
  renders on screen
- Semantic retrieval of NPC knowledge (embeddings + cosine similarity,
  scoped to what the NPC actually knows)
- Rule-based belief formation with contradiction handling, fed into
  the generation prompt
- Relationship strength moves with quest outcomes (up on `validated`,
  down on `failed_validation`)
- Containerized (`docker compose up --build`) with CI running lint and
  an image build on every push

**What's next**

- Q6 experiment protocol — can players distinguish generated from
  handcrafted quests? (Step 8, the currently active step)
- R1–R4 recovery cascade for failed validations
- A trained NER model to replace C3's regex-based entity extraction
- 8+ additional NPCs
- The two-history Blackwater demo comparison below — not yet built

In Godot 4.7.1, the chain is Godot → HTTP → Python → Postgres → Claude →
validator → back to the engine canvas. The verified round trip returned
a quest that passed every hard constraint on the first attempt:

```
[bridge] POST http://localhost:8000/generate-quest
[bridge] HTTP status code: 200
[bridge] npc=Otto template=personal_crisis validation=passed attempts=1
[bridge]   attempt 1: failed=none retried=false — passed on attempt 1
```

## Repository Structure

All runnable code lives under `prototype/`.

```
├── prototype/
│   ├── server.py                        # FastAPI bridge — /health, /generate-quest
│   ├── pipeline.py                      # Phase A: NPC + template selection, semantic
│   │                                     #   retrieval, belief lookup, game state assembly
│   ├── beliefs.py                       # Rule-based belief formation + contradiction
│   ├── quest_generator_v4.py            # generate_quest(): prompt → API → validate → write
│   ├── validator.py                     # Hard-constraint validator (C1, C3, C4, C5)
│   ├── schema.sql                       # Postgres DDL — enums, pgvector column, constraints
│   ├── init_db.py                       # Applies schema.sql (direct/migration connection)
│   ├── seed_db.py                       # Seeds the Blackwater world (direct/migration connection)
│   ├── backfill_embeddings.py           # Generates + stores event embeddings
│   ├── demo_beliefs.py                  # Demo: different NPCs hold different beliefs;
│   │                                     #   one belief shown before/after contradiction
│   ├── compare_knowledge_retrieval.py   # Keyword vs. semantic retrieval, side by side
│   ├── test-states.json                 # 5 validated game state inputs
│   └── requirements.txt                 # Python dependencies
├── godot/                       # Godot 4.7.1 client (placeholder visuals)
│   ├── project.godot
│   ├── Main.tscn                # Player, NPC + talk zone, dialogue panel
│   └── Main.gd                  # Movement, interact, HTTP calls
├── docs/                        # Design docs, schemas, planning, build log
│   ├── fact-database-design.md  # Schema, constraints, validation pipeline
│   ├── quest-templates.md       # The four quest templates
│   ├── build-log.md             # Chronological build log
│   └── ...
├── Dockerfile                   # Builds prototype/ into a runnable image
├── docker-compose.yml           # docker compose up --build
├── .github/workflows/ci.yml     # Lint + image build on every push
├── MIGRATION-NOTES.md           # What broke and why, what was chosen and on what
│                                 #   grounds, what I'd do differently
└── README.md
```

Postgres (Supabase) is the database — nothing is generated locally.
`prototype/.env` (gitignored) holds `DATABASE_URL`,
`MIGRATION_DATABASE_URL`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`.

## The Enterprise Connection

The architecture that prevents hallucination in this game is 
the same architecture that prevents hallucinated actions in 
enterprise AI agents.

- Fact database → company brain
- Constraint validator → grounding system  
- NPC schema → skills file
- The `npc_knowledge` join → **permission-scoped retrieval**. An
  enterprise agent must not retrieve what a given user isn't allowed to
  see. Here, the join that filters events down to "what this NPC
  actually knows" runs *before* anything gets ranked by similarity — it
  isn't a filter layered on top of retrieval, it's the boundary
  retrieval operates inside of.
- `channel` + `confidence` → **provenance-weighted confidence**. Where a
  fact came from determines how much weight it carries — a directly
  witnessed fact outweighs a rumor the same way a primary source should
  outweigh secondhand mention in an enterprise knowledge base. Beliefs
  built on that evidence inherit its uncertainty, and get revised — not
  deleted, revised — when better evidence arrives.

Same problem, different domain.

## Setup

Requires Docker (for the quickstart below) or Python 3 plus a Postgres
instance with the `vector` extension enabled, for a local run without
containers. This project runs on Supabase for both; the Docker image
pins Python 3.13.

### 1. Environment

```bash
git clone https://github.com/AlekZora/side-quest-ai
cd side-quest-ai
```

Create `prototype/.env`:

```bash
DATABASE_URL=postgresql://<pooled-connection-string>
MIGRATION_DATABASE_URL=postgresql://<direct-connection-string>
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
```

`DATABASE_URL` is the runtime connection — this project uses Supabase's
transaction pooler, since a plain direct connection can be IPv6-only
and unreachable from some networks and from inside a container.
`MIGRATION_DATABASE_URL` is the direct connection, used only by
`init_db.py` and `seed_db.py`: schema changes and seeding shouldn't
depend on pooler behavior.

### 2. Database

```bash
cd prototype
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

python init_db.py               # apply schema.sql
python seed_db.py               # seed the Blackwater world
python backfill_embeddings.py   # generate event embeddings
```

Each script is idempotent — re-running `init_db.py` or `seed_db.py` is
safe, and `backfill_embeddings.py` only embeds events that don't have
one yet.

```bash
python pipeline.py    # Phase A only — selection + game state, no API call
```

### Docker quickstart

From the repo root, with `prototype/.env` set up as above:

```bash
docker compose up --build
```

This builds the image — build context is the repo root, but only
`prototype/` is copied in — and starts the FastAPI service on `:8000`.
`DATABASE_URL`, `ANTHROPIC_API_KEY`, and `OPENAI_API_KEY` come from
`prototype/.env` at runtime; nothing is baked into the image.

```bash
curl http://localhost:8000/health
```

### Running the bridge

The game engine talks to Python over HTTP. From `prototype/` (or via
Docker, above):

```bash
uvicorn server:app --port 8000
```

`ANTHROPIC_API_KEY` is loaded from `prototype/.env` —
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

1. **Start the server.** From `prototype/`, with `prototype/.env` set
   up as in Setup:

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
