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
