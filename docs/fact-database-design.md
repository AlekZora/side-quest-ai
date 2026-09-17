# Fact Database & Hard-Constraint Validator — Design
*Created: 2026-06-09*

Design document for Step 6 of the gap report. Specifies the schema for the
fact database, the hard and soft constraints the validator must enforce, the
sequence of checks a generated quest passes through, and what happens when
validation fails.

This is a design document. No code yet. The implementation order at the bottom
defines what gets built first.

---

## Architectural Frame

The fact database is the simulator layer of the
**Renderer → Simulator → Planner** stack named in PROJECT-CONTEXT.md.

- **Planner** = the quest generator (LLM). Stateless. Reads, never writes.
- **Simulator** = this fact database. Authoritative state. Tracks what actually
  happened, what exists, who knows what.
- **Renderer** = the dialogue system (Stage 2). Surfaces planner output as
  in-character speech.

The validator sits between Simulator and Planner. It does two jobs:

1. **Pre-generation**: assembles the game state JSON the planner reads, and
   picks which NPC and template to use based on soft constraints.
2. **Post-generation**: checks the planner's output against the simulator. A
   generated quest that contradicts the database is rejected before it reaches
   the renderer.

This separation is what enforces the design language commitment in
PROJECT-CONTEXT.md: *"LLM never touches world state directly — only reads it."*
The validator is what makes that guarantee real.

Tech stack: SQLite for the database (decided in PROJECT-CONTEXT.md). Python
glue layer. NPC static definitions (situation, want, stake, network) stay in
JSON files maintained by the world builder; their dynamic state (alive/dead,
location, knowledge) lives in SQLite.

---

## 1. SCHEMA

Five tables as named in the gap report, plus three secondary tables to support
the validator: `quests`, `player_choices`, `npc_beliefs`. The gap report's
five are the core; the three secondary tables are the joinable indexes that
make the validator's queries efficient.

All `id` fields are integer primary keys unless noted. All `when` and
`*_at` fields are in-game time, monotonically increasing integer ticks — not
wall-clock time. Wall-clock would tie quest generation to player session
length, which is the wrong unit.

---

### 1.1 `events`

The append-only log of everything that has happened. This is the closed-loop
artifact from `closed-loop-systems.md` — every player action and world event
becomes a row here, and these rows are what subsequent quests reference.

```
events
  id              INTEGER PRIMARY KEY
  type            TEXT     -- enum: player_action | npc_action | world_event
  what            TEXT     -- human-readable description (feeds LLM prompt)
  when            INTEGER  -- in-game tick
  location_id     INTEGER  -- FK → entities.id (where it happened)
  actor_id        INTEGER  -- FK → entities.id ("player" for player actions)
  witnesses       TEXT     -- JSON array of entity_ids who directly observed
  significance    TEXT     -- enum: high | medium | low (filters player_history)
  consequences    TEXT     -- JSON array of event_ids caused by this event
```

**Reasoning.**
- `witnesses` drives gossip propagation: rows in `npc_knowledge` get created
  for every witness automatically when an event is logged. Anyone not in
  `witnesses` only learns through gossip.
- `significance` is what `quest-templates.md` Template 3 needs to select
  callback-worthy past choices. Only `high` events populate `player_history`
  in the game state JSON. Bribing a guard at the gate is `medium`; letting a
  detained woman go without paying is `high`.
- `consequences` is the causal chain. When `manifest_burned` triggers a
  Syndicate lockdown event, the lockdown's `consequences` field points back
  to the burn. This is what lets the validator answer "was this caused by
  what the player did?" without re-running the world.
- Append-only. Events are never modified or deleted. State changes are new
  events.

---

### 1.2 `entities`

Everything that exists in the world: NPCs, locations, items, documents. The
single most important field is `status` — this is what the "quest giver must
be alive" hard constraint checks.

```
entities
  id              INTEGER PRIMARY KEY
  type            TEXT     -- enum: npc | location | item | document
  name            TEXT     -- display name
  status          TEXT     -- enum: alive | dead | destroyed | missing | intact
  location_id     INTEGER  -- FK → entities.id (current location; NULL for locations)
  owner_id        INTEGER  -- FK → entities.id (NULL for NPCs and locations)
  properties      TEXT     -- JSON blob (type-specific)
  created_at      INTEGER  -- in-game tick (when added to world)
  last_changed_at INTEGER  -- in-game tick (last status/location/owner change)
```

**Reasoning.**
- `status` is intentionally an enum with explicit values rather than a
  boolean. Dead and missing are different for quest purposes: a dead NPC
  can't give quests; a missing one can be the *subject* of a quest.
- `properties` JSON holds type-specific data. For NPCs this includes the
  static authored fields from `npc-schema.json` (situation, want, stake,
  network). For items it holds weight, value, fungibility. Keeping this as
  a JSON blob avoids 4+ specialized tables; the validator never queries
  into `properties`, only into the dynamic state columns.
- World-builder authoring stays in NPC JSON files. Those are loaded into
  this table at startup. Edits in-game write back to the table, not the file.
- `last_changed_at` lets the validator detect stale facts. If an event in
  the quest text references "the eastern guard," and the eastern guard was
  killed at tick 240, and the quest was generated at tick 245, the validator
  flags the stale reference.

---

### 1.3 `relationships`

Edges between entities. NPC↔NPC, NPC↔location, NPC↔item. This is what
`gossip-protocols-agents.md` calls the social graph. It also carries trust
gradients that drive soft constraints.

```
relationships
  id              INTEGER PRIMARY KEY
  from_id         INTEGER  -- FK → entities.id
  to_id           INTEGER  -- FK → entities.id
  type            TEXT     -- enum: knows | trusts | distrusts | allied | opposed
                           --       | related | employed_by | owns | located_at
  strength        REAL     -- -1.0 to 1.0; NULL for non-graded types
  established_at  INTEGER  -- FK → events.id (provenance for this relationship)
  last_changed_at INTEGER  -- in-game tick
```

**Reasoning.**
- `strength` is what soft constraints multiply against. Otto's trust toward
  the player after the woman-at-the-gate event might be +0.6. That's a
  positive multiplier on his probability of approaching the player with a
  quest. Daria's husband-officer relationship might be `distrusts, -0.9`.
- `established_at` is the provenance pattern from `holographic-vulnerability.md`.
  Every relationship is traceable to the event that created it. The validator
  uses this to answer "why does this NPC trust the player?" — required for
  Template 3 callback validation where the NPC's trust must be grounded in
  a specific past event.
- Directed graph. Trust is not symmetric. The player may not even know an
  NPC has formed an opinion of them.

---

### 1.4 `player`

The player's state. Singleton (one row). Most fields are scalar; for
queryable lists (choices, quests), separate tables exist below.

```
player
  id                    INTEGER PRIMARY KEY  -- always 1
  current_location_id   INTEGER              -- FK → entities.id
  current_situation     TEXT                 -- short text, regenerated by triggers
  inventory             TEXT                 -- JSON array of entity_ids
  visited_locations     TEXT                 -- JSON array of entity_ids
  known_facts           TEXT                 -- JSON array of event_ids
  reputation_by_faction TEXT                 -- JSON: {faction_name: float}
```

**Reasoning.**
- `known_facts` is the player's epistemic state — what the player has
  actually been told or witnessed. Used by the escalation template: the
  validator checks that the revelation the NPC offers is something the
  player does *not* already know. Revealing known facts is a quest failure
  mode worse than generic — it's empty.
- `reputation_by_faction` is intentionally JSON not a separate table. There
  are ~5-10 factions max in a scoped demo. The complexity of a normalized
  table isn't justified.
- `current_situation` is a freeform text field that triggers regenerate
  based on recent events. It's what the world builder writes when the
  player walks into a new scene. The LLM reads this; the validator doesn't.

---

### 1.5 `player_choices`

Normalized index into `events` for queries the validator runs frequently.
Specifically powers Template 3's `player_history` array.

```
player_choices
  event_id        INTEGER  -- FK → events.id
  significance    TEXT     -- enum: high | medium | low
  callback_used   BOOLEAN  -- has this choice been the subject of a callback quest?
```

**Reasoning.**
- Indexing this lets the validator query the player's high-significance
  history in O(log n) without scanning all events.
- `callback_used` prevents the same past choice from being called back
  twice. After Otto's quest about the woman at the gate, that event is
  marked used; no other NPC can call it back unless the world builder
  explicitly enables multi-callbacks.

---

### 1.6 `npc_knowledge`

Per-NPC epistemic state. The grounding constraint from the experience goal
lives here: an NPC can only reference what they actually know. Generated
quests fail validation if the NPC's claimed knowledge has no supporting row.

```
npc_knowledge
  id              INTEGER PRIMARY KEY
  npc_id          INTEGER  -- FK → entities.id (must be type=npc)
  event_id        INTEGER  -- FK → events.id
  channel         TEXT     -- enum: witnessed | told_by | deduced | rumor
  source_npc_id   INTEGER  -- FK → entities.id (NULL if witnessed or deduced)
  confidence      REAL     -- 0.0 to 1.0
  learned_at      INTEGER  -- in-game tick when this NPC came to know
```

**Reasoning.**
- This is the simulator-level truth behind the `npc_knowledge` field in the
  game state schema. The schema field is human-readable text ("Heard someone
  bribed the eastern guard"). This table is the structured fact behind it.
- `channel` is the grounding constraint enumerated. The validator checks
  that the channel is plausible: an NPC can't have `witnessed` an event whose
  `location_id` is across the city from where they were.
- `source_npc_id` is the gossip chain. Otto told Daria; Daria's row references
  Otto. This is what powers gossip-propagation reasoning.
- `confidence` decays with channel: witnessed=1.0, told_by=0.8, deduced=0.7,
  rumor=0.4. The LLM can be told to express uncertainty proportional to
  confidence. Below ~0.3, the NPC shouldn't reference the fact at all.

---

### 1.7 `npc_beliefs` *(deferred to validator V2)*

NPCs can be wrong. An NPC might believe the player is a Syndicate informant
even though they aren't. From `information-asymmetry.md`, this is one of the
richest quest sources.

```
npc_beliefs
  id                      INTEGER PRIMARY KEY
  npc_id                  INTEGER
  belief_text             TEXT     -- what the NPC believes
  confidence              REAL
  contradicting_event_id  INTEGER  -- the event that would disprove (NULL if none)
  formed_at               INTEGER  -- when this belief crystallized
```

**Defer to V2.** False beliefs are a powerful narrative mechanic but require
careful authoring. For Step 6 V1, the validator only enforces that NPCs
reference *known* facts. Beliefs as quest material is a Stage 2 expansion.

---

### 1.8 `quests`

Generated quests, including ones that failed validation (for logging) and ones
that were declined by the player.

```
quests
  id                    INTEGER PRIMARY KEY
  npc_id                INTEGER  -- giver
  template_type         TEXT     -- escalation | personal_crisis | callback | world_texture
  status                TEXT     -- generated | validated | offered | accepted
                                 -- | completed | declined | failed_validation
  generated_text        TEXT     -- the raw LLM output
  referenced_event_id   INTEGER  -- callback target (NULL for non-callback)
  created_at            INTEGER
  validation_log        TEXT     -- JSON: which checks ran, which failed
```

**Reasoning.**
- All generated quests are logged, including ones that failed validation.
  This is the data that funds prompt tuning. Without it, you cannot tell
  whether a template is producing generic output or whether a specific NPC's
  knowledge graph is too thin to support contextual generation.
- `status` distinguishes `failed_validation` from `declined`. Both don't
  reach the player; the difference matters for analytics.
- `validation_log` is JSON storing the exact validator output. This is what
  the failure recovery cascade reads to decide the next attempt.

---

## 2. HARD CONSTRAINTS

A hard constraint blocks the quest from reaching the player. The user's four
are correct and form the base. The full V1 list:

**Existence**
1. **Quest giver must be alive.** `entities.status = 'alive'` at quest creation
   time. *(User-provided.)*
2. **Quest location must exist.** Every location referenced in the quest text
   must resolve to an `entities` row with `type = 'location'`. *(User-provided.)*
3. **Quest cannot reference entities that don't exist.** Every named person,
   place, item, or document must appear in `entities`. No invented characters.
4. **Quest giver must match a real NPC.** The `npc_id` on the generated quest
   must resolve to an `entities` row with `type = 'npc'`. The generator can't
   produce a quest from "a Syndicate officer" without that officer being a
   tracked entity.

**State**
5. **Quest reward must be owned by or accessible to the giver.** Items
   promised must either be `owner_id = npc_id` or reachable via the NPC's
   `network` field. Information promised must be supported by the NPC's
   `npc_knowledge` rows. *(User-provided, expanded.)*
6. **Quest giver must be in proximity to the player.** Either co-located,
   or the quest must explain a plausible meeting (note left, message sent).
   Hard block on "Daria walks up to the player" if Daria is across the city.
7. **Referenced relationships must exist.** If the quest claims "your friend
   the apothecary," that friendship must be a row in `relationships`.

**Causation**
8. **Referenced event must have actually occurred.** Every past event the
   NPC references must be a row in `events`. No hallucinated history.
   *(User-provided.)*
9. **Callback templates: the referenced past choice must be in `player_choices`
   with `significance = 'high'`.** And it must not have `callback_used = true`
   already.
10. **NPC's knowledge claim must be supported by `npc_knowledge`.** If the
    quest says "Serge knows about the manifest burning," there must be an
    `npc_knowledge` row for (Serge, manifest_burned_event) with a plausible
    channel. Hallucinated knowledge channels are the failure mode this catches.

**Narrative integrity**
11. **Quest must not resolve a main story beat.** From the
    PROJECT-CONTEXT.md constraint: NPCs cannot resolve the main quest. A
    quest that says "and then we rescue Elena" is hard-rejected. The validator
    needs an LLM judge for this check — pure rule-based detection misses
    paraphrases. *(Mark as V2 if LLM judge isn't ready; V1 uses keyword
    blocklist as a coarse heuristic.)*
12. **Quest must not contradict an already-completed quest.** If an active
    quest will be invalidated by accepting this one, hard-reject.
13. **Quest must not duplicate an active quest from the same NPC.** One
    active quest per NPC at a time.

**Temporal**
14. **Quest's stated deadlines must be in the future.** If the quest text
    says "by tomorrow night" and in-game time has already passed tomorrow
    night, reject. Mostly a sanity check for generator drift.

The list will grow as failure modes are discovered. Constraints 1–4, 8, 9,
12, 13, 14 are rule-based and run in milliseconds. Constraints 5, 6, 7, 10,
11 are harder and need either richer entity extraction or an LLM judge —
they constitute validator V2 work.

---

## 3. SOFT CONSTRAINTS

Soft constraints reduce probability but never block. Implementation: each
candidate `(NPC, template)` pair gets a base score of 1.0; each applicable
soft constraint multiplies the score. The selector picks the top-scoring
pair to generate from.

These are applied **pre-generation**, not post. They influence which quest
gets attempted, not whether a generated quest survives.

**Pacing (variety)**
- **NPC cooldown.** Same NPC issued a quest within the last N events:
  multiply by 0.2. Prevents one NPC from dominating the session.
- **Template variety.** Same template type as the last quest: multiply by
  0.6. Forces rotation across the four templates so the player doesn't see
  three consecutive callbacks.

**Relationship**
- **Trust gradient.** If `relationships(npc → player).type = 'trusts'`,
  multiply by `1.0 + (strength × 0.5)`. Distrust reduces probability but
  doesn't kill it — distrust can produce reluctant quests too (Template 2).
- **Player declined this NPC before.** Multiply by 0.5. The NPC notices.
- **Faction reputation.** If the NPC is aligned with a faction the player
  has poor reputation with, multiply by 0.7.

**Template-specific**
- **Callback freshness.** Probability of `callback` template decays with
  the age of the candidate `referenced_choice`. Choice from last session:
  1.0. From three sessions ago: 0.5. From the first hour of play: 0.2.
  Older choices feel stale; recent ones feel sharper.
- **Stake activation boost.** If the NPC's `stake` has been threatened by a
  recent event (the stake's referent entity changed status, or a related
  entity did), multiply by 1.5. This biases the system toward Template 2
  when the NPC's emotional core is actively under pressure.
- **World texture saturation.** If the last 3 quests were `world_texture`,
  multiply this template's score by 0.3. World texture should feel like
  punctuation, not the through-line.

**Player state**
- **Quest load.** If the player already has 3+ active quests, multiply all
  candidates by 0.5. Reduces overload.
- **Player attention.** If the player has recently skipped quest text without
  reading (signal from the renderer), multiply by 0.7. The system is asking
  too often.

V1 ships with NPC cooldown, template variety, trust gradient, callback
freshness, stake activation, and quest load. The other four are V2 once the
analytics are wired up to detect player-side signals.

---

## 4. VALIDATION PIPELINE

A generated quest passes through three phases: **trigger**, **generation**,
**validation**. Each has internal steps.

### Phase A — Trigger and pre-generation

```
A1. Trigger fires.
    Source: player action logged | scene change | NPC stake threshold crossed
    | timer tick.

A2. Candidate enumeration.
    Query entities where type='npc' AND status='alive' AND
    location_id IN (player's current location, adjacent locations).
    Returns ~3-10 NPCs.

A3. Per-candidate template eligibility.
    For each NPC, determine which templates could plausibly fire:
    - escalation: NPC.network must include an entity related to main_quest
    - personal_crisis: NPC.stake must reference a still-alive entity
    - callback: there must exist a player_choices row with significance='high'
                and callback_used=false, observable by this NPC via npc_knowledge
    - world_texture: always eligible (this is its function — fallback texture)

A4. Soft constraint scoring.
    For each eligible (NPC, template) pair, compute score per §3.
    Pick the top pair. If multiple tie within 5%, pick by NPC who hasn't
    been used recently.

A5. Game state assembly.
    Build the input JSON for the LLM:
    - For callback: include player_history (filtered to significance='high')
      and select referenced_choice (the chosen player_choices row).
    - For escalation/personal_crisis/world_texture: standard 5-field game state.

A6. Hard constraints — pre-check.
    Before calling the LLM, verify the NPC is alive, in proximity, and has
    knowledge of the triggering player action. Fail-fast: no point spending
    tokens if the basic state has already changed since enumeration.
```

### Phase B — Generation

```
B1. LLM call.
    Template-routed prompt → quest text. max_tokens >= 1200 (confirmed in
    build-log.md). Cost and latency logged.
```

### Phase C — Post-generation validation

```
C1. Structural parse.
    Confirm the output contains the 5 required items for the template.
    Failure → structural fault. Go to recovery §5.

C2. Entity extraction.
    Parse the text for proper nouns and reified entities (people, places,
    items, documents). Use a small NER pass (rule-based for V1; LLM judge
    for V2).

C3. Existence check (HC1, HC2, HC3, HC4).
    Every extracted entity must be in `entities`. The NPC giver must match.
    Any unresolved entity = hallucination. Reject.

C4. State check (HC1, HC6, HC14).
    Quest giver alive. Giver in proximity to player. All referenced entities
    in compatible states (not dead/destroyed). Deadlines in the future.
    Reject if any fails.

C5. Causal check (HC8, HC9).
    Every past event referenced must be in `events`. For callback templates,
    the referenced_choice must match the chosen player_choices row.

C6. Knowledge check (HC10).
    Every claim made by the NPC about events or other entities must be
    supported by a row in `npc_knowledge` for that NPC. This is the
    grounding-constraint enforcement that powers the experience goal.
    V1: rule-based (extract claims as event references; check rows exist).
    V2: LLM judge for paraphrased knowledge claims.

C7. Reward feasibility (HC5).
    Items must be owned by giver or accessible via network.
    Information must be in npc_knowledge with confidence ≥ 0.5.
    V1: simple field checks. V2: LLM judge.

C8. Narrative integrity (HC11, HC12, HC13).
    Quest doesn't resolve main story. No active-quest collision. No duplicate
    quests from the same NPC.
    V1: keyword blocklist for main_quest resolution + DB joins for collisions.
    V2: LLM judge for paraphrased main quest resolution.

C9. Decision.
    All checks pass → write quest row with status='validated' → offer to player.
    Any check fails → go to recovery §5.
```

Easy checks (C1, C3, C4, C5, C8 partial) run in milliseconds against SQLite.
Hard checks (C6, C7, C8 LLM-judge) add a separate LLM call costing ~50% of
the generation call. For V1, only run the LLM judge if rule-based checks pass
but a confidence threshold is in question.

---

## 5. FAILURE RECOVERY

When a quest fails validation, the recovery cascade tries up to three
alternatives before silently skipping the trigger. Pure handcrafted fallback
is rejected as an option — it would break the contract with the player that
quests are contextual.

```
R1. Same NPC, same template, constrained retry.
    Re-call the LLM with the failure reason injected into the prompt:
      "The previous attempt failed validation because: [reason].
       Specifically, do not reference [hallucinated entity / unsupported claim].
       Generate again with these constraints."
    Applies to: structural failures (C1), single hallucinated entity (C3),
    minor knowledge gap (C6 single missing row).
    Limit: 1 retry per (NPC, template) pair per trigger.

R2. Same NPC, different template.
    If R1 fails or the failure is template-specific (e.g., escalation's
    revelation claim can't be supported by this NPC's network), pick the
    next-best-scoring template for the same NPC from the §3 scoring.
    Limit: 1 attempt.

R3. Different NPC, recompute template.
    Drop to the next-best candidate NPC from §A2. Recompute soft constraint
    scoring. Generate.
    Limit: 1 attempt.

R4. Skip.
    No quest produced for this trigger. The world continues. The next trigger
    will fire later (next player action, next scene change).
    Log the failure with full context: triggering event, candidate NPC list,
    each attempt's quest text, each failure reason.
```

**Why not handcrafted fallback?** The whole experience goal is recognition —
the world responding to the player's specific story. A handcrafted fallback
would either be generic (failing the experience goal) or surprisingly
specific to *some* situation that doesn't match the player's (failing the
trust contract). A silent skip is honest: sometimes the world has nothing
to say to the player right now.

**Pacing budget.** Total wall-clock for one trigger: B1 takes ~3-5s; C-phase
adds <100ms (rule-based); recovery R1-R3 could add up to 3 more LLM calls
worth ~10-15s. That's too long for synchronous in-game generation. **The
generation must run on a separate thread** while the player keeps moving;
when validated, the quest is queued for the next NPC interaction. This is
a Stage 2 architecture concern but the design should accommodate it now.

**Failure analytics.** Every failure logged to `quests` table with
`status='failed_validation'`. Weekly review of failure modes drives prompt
tuning and template refinement. Persistent failure on a specific NPC means
their static definition (situation, want, stake, network) is too thin to
support contextual generation — they need a richer entity graph or they
should be marked inactive.

---

## V1 vs V2 Scope Summary

**V1 (Step 6 implementation):**
- 5 core tables + `quests`, `player_choices`
- Hard constraints: 1, 2, 3, 4, 8, 9, 12, 13, 14 (rule-based)
- Hard constraints 5, 6, 7, 10, 11 with coarse heuristics
- Soft constraints: NPC cooldown, template variety, trust gradient,
  callback freshness, stake activation, quest load
- Recovery: R1, R2, R3, R4 cascade. No LLM-judge retries.

**V2 (Stage 2 expansion):**
- `npc_beliefs` table and false-belief quest generation
- LLM judge for paraphrased main quest resolution check
- LLM judge for knowledge support check
- Remaining soft constraints (declined-before, faction reputation, world
  texture saturation, player attention)
- Async generation thread with pre-queued quest pool

---

## Open Questions

1. **Gossip propagation cadence.** *(RESOLVED)*
   Gossip propagates at scene change. When the player moves to a new
   location, for each event in the last 20 ticks, any NPC with a
   `relationships` row to a witness and who is in an adjacent location gets
   an `npc_knowledge` row created automatically:
   ```
   channel    = 'told_by'
   source_npc_id = the witness NPC's entity_id
   confidence = 0.6
   learned_at = current_tick
   ```
   This means gossip is: bounded (last 20 ticks only), proximity-gated
   (adjacent locations, not across the city), and social-graph-gated
   (relationship to a witness must exist — strangers don't gossip to each
   other). The scene-change trigger fits the Godot integration point
   naturally: scene change is already a discrete event. Timer-based gossip
   is deferred to V2.

2. **In-game tick definition.** What advances the tick? Real-time elapsed?
   Number of player actions? Scene changes? Affects how cooldowns and
   freshness decay work. Defer until first integration with Godot.

3. **Entity extraction implementation.** Step C2 needs an NER pass. Pure
   regex over capitalized names misses lowercase items ("the manifest") and
   over-matches generic words. V1: rely on the LLM judge for fuzzy cases.
   V2: small fine-tuned classifier.

4. **Stake threat detection (soft constraint).** "NPC's stake has been
   threatened by a recent event" requires detecting that an event's actors
   or location intersect with the NPC's `stake` field. This needs an LLM
   judge to read the stake text and identify referent entities. Cheap to
   run once per NPC at startup; cache results.

5. **Concurrency.** If two triggers fire simultaneously, do we generate
   two quests in parallel? V1 says no — serialize. V2 might allow parallel
   generation against an immutable snapshot of the DB.

---

## Implementation Order (Step 6 build sequence)

Once this design is approved, build in this order:

1. SQLite schema migration script — creates all 8 tables.
2. Seed data: convert the 4 example NPCs from `quest-templates.md`
   (Serge, Daria, Otto, Nadia) into `entities` + `relationships` +
   `npc_knowledge` rows. Convert the player history Otto callbacks against
   into `events` + `player_choices`.
3. Pre-generation pipeline: A1–A6 (Phase A above).
4. Hard constraint checks C3, C4, C5 (existence, state, causal — all
   rule-based).
5. Wire `quest-generator-v3.py` to consume from this pipeline instead of
   inline NPC dicts. Rename to `quest-generator-v4.py`.
6. Recovery cascade R1–R4.
7. Soft constraint scoring per §3.
8. Run end-to-end test: trigger a quest from a seeded event; verify all
   four templates still produce the outputs from the Step 5 test, now
   sourced from the DB rather than inline.

Step 7 (Godot) does not start until step 8 above passes.
