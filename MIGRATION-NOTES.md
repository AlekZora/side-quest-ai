# Migration Notes

This is my systematic approach to build anything:
- What broke and why
- What I chose between, and on what grounds
- What I'd do differently

## Enum vs CHECK

I chose Postgres enums for knowledge channels, quest template types,
quest statuses, and entity types because these value sets are tied to
stable application logic and are unlikely to be renamed or removed.

I kept relationship types as a CHECK constraint because that vocabulary
is less settled and may change as the world model evolves.

## Identity Columns Need a Sequence Sync

SQLite's INTEGER PRIMARY KEY has no separate sequence object, so seeding
explicit ids (entities 1-13, events 1-3) never caused problems there.
Postgres identity columns do keep a sequence, and it doesn't know about
rows inserted with an explicit id — it only advances on default-value
inserts. Left alone, the first runtime insert that omits an id would
collide with a seeded row.

I added a sync step at the end of seeding that advances each sequence
to the current max id. I'd build that in from the start next time
rather than noticing it as a gap after the fact — any schema that mixes
explicit-id seed data with identity columns needs it.

## Enum Columns Need an Explicit Cast on Insert

psycopg sends bound string parameters as plain text, and Postgres
doesn't implicitly cast text to a custom enum type across the wire —
only literals written directly in the SQL get that resolution. Every
parameterized insert into an enum column (`entities.type`,
`npc_knowledge.channel`, `quests.template_type`, `quests.status`)
needed an explicit `%s::enum_type` cast on that placeholder, or the
insert fails with a type mismatch.

Same root cause killed `cursor.lastrowid` (psycopg has no equivalent —
switched to `INSERT ... RETURNING id`) and `conn.executemany()`
(psycopg's Connection doesn't have it — only Cursor does). None of
these are SQL differences; they're driver-API differences that a
straight `sqlite3` → `psycopg` swap won't surface until something
throws. I'd budget time for driver-parity checks up front instead of
finding them one insert at a time.

## Validator Issues Found During the First Live Generation (future fix)

Not migration bugs — pre-existing V1 validator behavior, surfaced when
I ran quest_generator_v4.py once against Postgres to test the write
path.

- C1: validator caught generation truncated by max_tokens.
  Current retry policy may not distinguish truncation from semantic
  validation failure. Future fix: failure-specific retry strategies.

- C3: heuristic entity detection produced false positives for
  sentence-opening capitalized words such as "Except" and "Whether".
  Current stopword-based approach will likely become brittle as
  generated language varies.

## Phase 2: Semantic Retrieval Replaces Keyword Matching

npc_knowledge holds no text of its own — it joins to events for that.
The old `build_npc_knowledge_text` matched the trigger against
`events.what` with `LIKE LOWER('%' + trigger[:30] + '%')`: a literal
substring test on the first 30 characters. That only ever worked when
the trigger was close to a verbatim quote of the event text.

I embedded `events.what` with OpenAI text-embedding-3-small (1536
dims, `events.embedding`, HNSW + cosine index) and added a second
`build_npc_knowledge_text` that embeds the trigger and ranks this
NPC's known events (filtered via the npc_knowledge join first, then
ranked by `<=>`) by similarity. Kept the original as
`build_npc_knowledge_text_keyword` for comparison.

Test: `"paid off the guard at the east checkpoint after dark"` against
Otto, who knows about the actual event `"Bribed the eastern gate guard
to pass through after curfew"` among three total.

- Keyword: no literal substring match, so it fell through to the
  three-most-recent-known-events fallback — the bribe event's text is
  in there, but only as the middle line of an undifferentiated
  three-event dump. Nothing about the output points at it specifically;
  it reads the same as noise.
- Semantic: matched the bribe event directly and returned only that
  one line — no fallback needed.

Worth being precise about what this proves, since Otto only knows 3
events total: the keyword fallback happened to include the right event
here by coincidence of dataset size, not because it identified
anything. With a larger knowledge base the fallback wouldn't
necessarily include it at all. The real, generalizable result is
specificity — semantic retrieval names the one relevant fact; keyword
matching either finds a literal quote or hands back everything recent
and lets the model sort it out.

## Confirmed With a Larger World (18 events, Otto knows 10)

The 3-event world above was too small to show a real miss — noted at
the time. Expanded to 18 events with each of Serge/Daria/Otto/Nadia
knowing 8-10, spread across witnessed/told_by/rumor with varied
confidence and learned_at, written as plausible world content rather
than tuned toward either retrieval method.

Same trigger and NPC as before. Otto's actual matching memory (the
curfew bribe, tick 30) is now his 4th-most-recent known event out of
10 — one place outside the keyword fallback's `LIMIT 3`:

- Keyword: no substring match, fell back to the 3 most recent by
  tick — the manifest burning (50), a supply-shortage rumor (39), and
  a *different* bribery event, a merchant paying off a guard (35).
  That last one is a near-miss by topic, not by content — it reads
  plausible next to the trigger and is wrong. The actual curfew-bribe
  memory doesn't appear at all.
- Semantic: matched the curfew-bribe event directly, no fallback
  needed.

This is the result the first test couldn't produce: keyword retrieval
doesn't just fail to specify — at this size it actively surfaces a
wrong, topically-similar answer ahead of the right one. That's a worse
failure mode than "diluted in a dump," and it's the one that would
actually mislead a quest generator working from `npc_knowledge`.

## Phase 3: npc_beliefs — Conclusions, Not Facts

npc_knowledge holds facts an NPC knows about specific events.
npc_beliefs holds something different: a generalization across facts
that could turn out wrong. I built this rule-based rather than
model-based, on purpose — a belief's confidence has to trace back to
specific event ids a specific NPC actually knows, or "the NPC believes
X" is just an LLM asserting something ungrounded with extra steps.

**Rules (`beliefs.py`), 3 not the suggested 4.** Dropped "player keeps
their word" — nothing in the current world depicts the player making
and keeping a commitment, and I'd rather ship 3 honest rules than 4
where one is a forced mapping onto unrelated evidence. The 3:

- `player_is_dangerous` — supported by the woman-at-the-gate deception
  and the manifest burning. Threshold 0.7: low, because per the brief
  "fear generalizes from less evidence than trust" — a single told_by
  (0.8) already clears it.
- `player_can_be_bought` — supported only by the curfew bribe.
  Threshold 0.75: higher, because this is a specific character claim,
  not a threat reflex — a rumor alone shouldn't be enough.
- `player_serves_the_syndicate` — also from the curfew bribe, read
  paranoidly (comfortable inside Syndicate checkpoint infrastructure =
  maybe embedded). Threshold 0.35: deliberately thin. This is the
  belief built to be wrong.

**Confidence is the summed support, capped at 1.0** — `npc_beliefs`
has a CHECK(confidence <= 1.0) and summed confidence across events can
exceed 1 easily, so capping is the schema constraint talking, not a
design choice I'd defend beyond that.

**Contradiction is binary, not graded.** When a rule has
`contradicting_events` and the NPC's own knowledge includes one, I
halve the confidence (floor 0.15, never zero) and set
`contradicting_event_id` — regardless of how strong the contradicting
evidence is. `player_serves_the_syndicate` is contradicted by the
manifest burning (destroying Syndicate property is the opposite of
serving it). I chose halve-not-scale because "one counter-example
makes an NPC uncertain, not converted" reads as a statement about
*kind* of change, not magnitude — grading the penalty by contradicting
confidence would imply the system can tell how *thoroughly* wrong a
belief is, which it can't from one contradicting fact.

**Idempotency needed a real schema change**: added
`UNIQUE(npc_id, belief_text)` to `npc_beliefs` so the formation pass
can `ON CONFLICT ... DO UPDATE` instead of hand-rolling exists-then-
update logic. Confirmed empirically against Supabase that a repeated
`ADD CONSTRAINT` raises `duplicate_table` (42P07), not
`duplicate_object` like the enum-type guards — would have guessed
wrong and shipped a DO-block that doesn't actually guard anything.

**Demo result** (`demo_beliefs.py`), unforced — this is just what the
seeded evidence produces:

| NPC   | Evidence                        | Beliefs formed |
|-------|----------------------------------|----------------|
| Otto  | witnessed bribe, told_by manifest | dangerous=1.00, can_be_bought=1.00, serves_syndicate=0.50 (contradicted by event 3) |
| Serge | told_by manifest only             | dangerous=0.80 |
| Daria | told_by manifest only              | dangerous=0.80 |
| Nadia | rumor of manifest only             | none — 0.4 < 0.7 threshold |

Same player, same world, four different belief states, purely from who
learned what and through which channel. Contradiction before/after
(simulated by evaluating Otto's belief on his knowledge with vs.
without the manifest-burning event, since in the static seed data both
facts arrived at once): confidence 1.00 -> 0.50, `contradicting_event_id`
None -> 3.

**Fed into generation**: `pipeline.assemble_game_state` now includes
`npc_beliefs` text; all 4 prompt builders in `quest_generator_v4.py`
get a "What {npc} believes about the player" line. Verified without
spending API tokens — checked the assembled game state directly and
called all 4 `PROMPT_BUILDERS` with a synthetic game state.

**Relationship strength now moves on quest outcomes**
(`update_relationship_from_outcome`, called from `write_quest`):
+0.1 on `validated`, -0.05 on `failed_validation`, capped to [-1, 1].
Asymmetric on purpose — a failed validation is a generation defect,
not the player betraying anyone, so it should cost less than a
validated quest earns. Verified by calling `write_quest()` directly
(no API call): Otto's trust went 0.5 -> 0.6 -> 0.55.

**What I'd do differently**: the contradiction-before/after demo had
to simulate "before" by filtering out one event from Otto's real
knowledge, because the seed data gives him both the supporting and
contradicting event at once — there's no real temporal "before" state
in a statically-seeded world. If a later phase adds events arriving
over time instead of all at once, the formation pass (already a full
recompute from current knowledge, not a delta) will show real
before/after without needing a demo script to fake it.

## Phase 4: Direct Connection Is IPv6-Only, and That Breaks in Docker

Containerizing surfaced something the host environment never would:
`db.ttabdjmrginsgtagroor.supabase.co` (the "direct connection" host
DATABASE_URL had pointed at since Phase 1) resolves to an IPv6 address
only — no A record at all. My host machine has IPv6 egress, so every
script ran fine against it for three phases. Docker Desktop's default
bridge network doesn't route IPv6 out, so the containerized server hit
`Network is unreachable` on its very first query — a failure mode with
zero connection to anything I'd changed in that phase.

Switched DATABASE_URL to Supabase's transaction pooler
(`aws-1-eu-west-1.pooler.supabase.com:6543`, user
`postgres.ttabdjmrginsgtagroor`) — IPv4, and also the connection type
Supabase actually recommends for anything that isn't a long-running
server with a stable outbound path, which a container fleet isn't.

That raised a second question I didn't want to leave unchecked: PgBouncer
in transaction-pooling mode is known to break psycopg's server-side
prepared statements, since a pooled connection can be handed a
different backend process between transactions while the client still
thinks a statement is prepared on the old one. Tested both realistic
shapes this codebase actually uses — the same query repeated many times
within one open transaction (matches a single request's pipeline run),
and the same query repeated across multiple explicit commits on one
connection object (matches backfill_embeddings.py and beliefs.py's
loops) — and both held up with no errors. Not exhaustive, but enough
to ship without adding `prepare_threshold=None` everywhere pre-emptively.
Worth re-checking if a future change introduces a genuinely long-lived,
high-repeat connection (an app-level connection pool, say).

