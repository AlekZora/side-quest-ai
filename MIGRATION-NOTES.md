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

## Phase 4: CI Needed a Real Lint Config, Not Just a Command

The brief said requirements.txt was missing psycopg and python-dotenv;
it wasn't — both were added in Phase 1. No action needed there, just
noting the instruction was stale by the time it reached me.

`ruff check .` with no config reported 31 findings on this codebase.
I chose not to either (a) ship CI red from commit one, or (b) adopt
whatever ruleset happened to produce zero findings. Instead I read
every finding and split them:

- 10 were real and trivial: 9 unnecessary f-string prefixes and one
  actually-unused `import re` in quest_generator_v4.py (dead since an
  earlier phase's edits). Fixed with `ruff check --fix` and re-ran the
  validator test suite and the prompt-builder check afterward —
  behavior identical, as expected for changes this mechanical.
- 21 were findings I'm not going to "fix": implicit multi-line string
  concatenation in prompt text (intentional — that's just how a long
  prompt string is written), and a blind `except Exception` in
  server.py's request handlers (intentional — a FastAPI bridge server
  should return a JSON error, not crash the process, on an unexpected
  exception).

Pinned the resulting selection (`E9`, `F` — syntax errors and Pyflakes:
undefined names, unused imports, etc.) in `ruff.toml` rather than only
in the CI command, so `ruff check .` behaves the same locally as in
CI. The alternative — hand-picking `--select` flags only inside
ci.yml — would silently diverge from local runs the moment anyone
tweaks one without the other.

## Phase 4 Follow-up: My "Checked Empirically" Note Was Wrong

My mentor asked two things after Phase 4: whether init_db.py and
seed_db.py still run clean against the pooler URL, and whether
migrations and runtime should use separate connection strings — "which
is what production setups usually do."

Ran a real truncate-and-reseed cycle to check the first question
properly rather than reason about it. init_db.py, seed_db.py, and
backfill_embeddings.py all ran clean against the pooler. beliefs.py
did not:

    psycopg.errors.DuplicatePreparedStatement: prepared statement "_pg3_0" already exists

This is the exact PgBouncer-transaction-mode-vs-prepared-statements
failure mode I'd flagged as a residual risk after Phase 4's original
pooler switch — and then under-tested. What I actually checked back
then was "does the same query repeated many times on one connection
object work" (yes). What I didn't check: PgBouncer transaction pooling
can hand two *different* client connections the same recycled backend,
and psycopg names its auto-prepared statements deterministically
(`_pg3_0`, `_pg3_1`, ...) — so a fresh Connection object can collide
with a statement name a completely different, earlier client session
left on that backend. That only shows up when something exercises
multiple query shapes across an uncommitted span, which is exactly
what `beliefs.py`'s `form_all_beliefs()` does (multiple NPCs × multiple
rules, one commit at the end) and my earlier smoke test didn't. Point
taken: "I checked and it seemed fine" was true of the test, not the
claim.

Non-deterministic means the fact that init_db.py/seed_db.py/
backfill_embeddings.py happened to pass this run is not evidence
they're safe — they're exposed to the identical risk and could fail on
a future run depending on what PgBouncer's pool state happens to be.

Fixed both problems together, since the mentor's second suggestion
turned out to remove the first one from half the codebase for free:

- Added `MIGRATION_DATABASE_URL` (the direct, unpooled connection) to
  `.env`. `init_db.py` and `seed_db.py` now use it — schema changes and
  seed provisioning shouldn't depend on pooler behavior at all, and a
  direct connection doesn't have this failure mode in the first place.
- Every remaining `psycopg.connect(DATABASE_URL)` call (server.py,
  pipeline.py, validator.py, quest_generator_v4.py, beliefs.py,
  backfill_embeddings.py, demo_beliefs.py, compare_knowledge_retrieval.py)
  now passes `prepare_threshold=None` — the documented fix for using
  psycopg3 against a transaction-mode pooler: disable server-side
  prepared statements entirely rather than hope the collision doesn't
  recur.

Re-verified end to end against Supabase: full truncate + init_db.py +
seed_db.py (migration URL) + backfill_embeddings.py + beliefs.py
(pooler URL, fixed) all clean; ran beliefs.py five times in a row with
no recurrence; demo_beliefs.py reproduces the exact same belief state
as before the fix; server.py's /health still returns
`{"ok":true,"npc_count":7,"tick":50}`.

**What I'd do differently**: when a fix works against a test I wrote
myself, ask whether the test matches the failure mode's actual
precondition — not just whether the fix seems plausible. "Repeated
queries on one connection" and "different connections sharing a
recycled backend" are different claims about PgBouncer, and I'd
conflated them.

## Repo Reorg: Docker Files Move to Root, Build Context Follows

Moved Dockerfile, docker-compose.yml, and .dockerignore from
prototype/ to the repo root, alongside moving 13 design docs into a
new docs/ directory so root only holds what a visitor needs
immediately (README, MIGRATION-NOTES, prototype/, godot/, .github/).

Moving the Dockerfile changes what "the build context" means. With
the Dockerfile inside prototype/, `.` was prototype/ itself — `COPY
requirements.txt .` and `COPY . .` both resolved relative to that
directory. With the Dockerfile at root, `.` is the whole repo, so both
COPY lines needed the prototype/ prefix (`COPY prototype/requirements.txt
.`, `COPY prototype/ .`) to keep copying the same files into the same
place inside the image.

This turned out to be an improvement, not just a relocation: with the
Dockerfile at prototype/, `COPY . .` copied everything the .dockerignore
didn't exclude — which was only ever prototype/'s own contents,
because that was the whole build context. Now that the context is the
repo root, `COPY prototype/ .` is explicit about copying only
prototype/ — docs/ and godot/ were never going to be needed by a
running FastAPI server, and now that's structural, not just true by
the accident of where the Dockerfile happened to sit.

docker-compose.yml's env_file path became `prototype/.env` (was
`.env`) for the same reason — paths in a compose file resolve relative
to the compose file's own location, which also moved.

.github/workflows/ci.yml's Docker build step could no longer share the
job-level `working-directory: prototype` default the lint/install
steps use — it needs to run from the repo root now. Moved that default
to per-step instead of job-level, so Install/Lint still run from
prototype/ and Build Docker image runs from root.

Verified: `docker compose up --build` from the repo root builds and
starts cleanly, `/health` returns `{"ok":true,"npc_count":7,"tick":50}`,
and `docker compose exec api ls /app` confirms the image contains only
prototype/'s files — no docs/, no godot/.

## Phase 5: Semantic Retrieval Shipped Without the Trust Gate It Needed

**What broke and why.** Phase 2 added `build_npc_knowledge_text`'s
semantic path (embedding similarity via `events.embedding <=> vector`)
but carried over none of the trust discipline the five other queries in
`pipeline.py` already apply (`get_eligible_templates`, `score_pair`'s
callback freshness, `build_player_history`, `get_referenced_choice` all
gate on `confidence >= 0.5`). The semantic query had no confidence gate
and `LIMIT 1` with no distance threshold — Postgres always returns the
nearest row regardless of how semantically distant it actually is. A
low-confidence rumor about an unrelated event could become the one line
an NPC's knowledge is built from, and nothing about the output signals
that it's a stretch.

**What I chose between, and on what grounds.** Before picking a
threshold I ran real triggers against all four seeded quest-giver NPCs
(Otto, Serge, Daria, Nadia) and printed actual cosine distances rather
than guessing one. True on-topic top-1 matches clustered tightly at
0.30–0.35. Every irrelevant case — an off-topic trigger, and a trigger
about an event a given NPC never learned about at all — landed at
0.61+, including three cross-NPC probes (Otto's real curfew-bribe
trigger run against Serge/Daria/Nadia, who have no `npc_knowledge` row
for that event) that all converged on the *same* wrong answer at
dist=0.6114: a checkpoint-reconfiguration event that's topically
adjacent but not what actually happened. That's the regression made
concrete — before the fix, all three NPCs would answer a question about
a bribe they never witnessed with a confident-sounding, wrong sentence.

Given the clean gap (0.35 to 0.61, nothing observed in between),
chose `KNOWLEDGE_SIMILARITY_FLOOR = 0.45` — margin on both sides of the
gap rather than hugging either edge.

For the no-match case, chose to drop the recency fallback rather than
keep it gated behind the floor. Recency was the thing Phase 2 already
argued against (an undifferentiated dump the model has to sort out,
worse: presented with no signal that it might be irrelevant) — gating
it behind a distance check doesn't fix that property, it just narrows
when it fires. Return an explicit no-match message instead, and split
it into two distinct states rather than one: "this NPC has trusted
knowledge, just none relevant to this trigger" is a different fact from
"this NPC has no trusted knowledge at all," and collapsing them would
hide which one the generator is actually working with. Verified the
second state is real, not just theoretical — Marta (id=11) has zero
`npc_knowledge` rows in the seed data and correctly produces the
no-knowledge-at-all message.

Raised `LIMIT` from 1 to 3, now that the floor guarantees relevance —
matches the shape of the fallback this replaces (also 3) and gives the
generator more than a single sentence when more than one relevant,
trusted memory exists (Otto's on-topic trigger clears the floor with
two events, not one).

**What I'd do differently.** The three cross-NPC probes converging on
the identical wrong event at the identical distance (0.6114) was a
useful accident, not something I designed for — I'd deliberately
construct a case like that earlier next time, since a single wrong
answer repeating across unrelated NPCs is a much sharper demonstration
of "this is ranking against the wrong denominator" than any one
NPC's result on its own.

Full before/after and the distance table are in the PR/commit
description, not duplicated here.

## Phase 6: The Retrieval Boundary Was Scoped; Prompt Assembly Wasn't

**What broke and why.** Phase 5 scoped `npc_knowledge` retrieval correctly —
confidence gate, similarity floor, permission join first. But
`assemble_game_state()` also put the raw `player_action` trigger string
straight into `game_state`, unfiltered by any of that, and every entry in
`quest_generator_v4.PROMPT_BUILDERS` interpolated it directly into the
prompt — twice, in three of the four templates (once in the `GAME STATE`
header, once again inline in a numbered instruction telling the model to
describe specific content from it). The scoping work in `npc_knowledge` was
real; it just wasn't the only channel content reached the model through.
`MAIN_QUEST` had the identical problem, one layer up — global constant,
same string in every prompt regardless of NPC, with only a prompt-level
request ("do not reference this") standing between it and the output.

Wrote `test_knowledge_boundary.py` before touching anything: for each of
the 4 seeded quest-giver NPCs, a trigger describing a real seeded event
that NPC holds zero `npc_knowledge` rows for, run through the real
`assemble_game_state()` + `PROMPT_BUILDERS` path, checked against a real
model call for terms unique to the unlearned event. 4/4 failed. Sharpest
case: Otto, given a trigger about an event he never learned about, wrote
that he "directly observed" it. Committed the failing test on its own
first, so the regression is in history before the fix that closes it.

**What I chose between, and on what grounds.** For `player_action`, three
options on the table: degrade it per-NPC by channel (full detail if
witnessed, vaguer if told-by, bare if nothing), drop it and rely on
`npc_knowledge` text alone, or split it into two fields. Went with the
split: the field was doing two jobs at once — "something happened, this
NPC has a reason to act now" (true for any NPC regardless of what they
know) and "here is what happened" (only true for a scoped match) — and
degrading or dropping both leaves one of those jobs either still leaking
content or unfulfilled. `game_state.trigger_notice` is now a fixed,
content-free string, identical for every NPC; every template still gets
its "why approach now" hook, but all actual content comes exclusively from
`npc_knowledge`. Three of the four templates had a second leak channel
beyond the header — an inline instruction asking the model to describe
"the capability the player demonstrated in `{player_action}}`" or similar —
those got reworded to point at documented knowledge instead of the raw
trigger; findings this before touching code, not after, is exactly what
tracing every interpolation site in step 1 of the review was for.

Verified both directions: the regression test now passes 4/4, and a
spot-check on the positive path (Otto, given a trigger for the curfew
bribe he actually witnessed) still produces a fully grounded escalation
quest that uses his real knowledge and network — the fix removes the leak
without flattening the case where an NPC legitimately knows something.

`MAIN_QUEST` is not fixed yet. Tracing it surfaced that a blanket "reject
output referencing main-quest specifics unless the NPC has a knowledge
row" can't work as a single rule: `MAIN_QUEST` isn't tied to any `event_id`
at all, so no NPC can ever hold a `npc_knowledge` row for it by
construction — and the escalation template's entire purpose is producing a
*new*, model-invented revelation that recontextualizes `MAIN_QUEST` from
the NPC's `network`, which structurally cannot be pre-supported by an
existing knowledge row either. The original design doc
(`docs/fact-database-design.md`) already anticipated this as two separate,
narrower checks — C8/HC11 ("quest must not *resolve* a main story beat,"
keyword-blocklist heuristic) and world_texture's own explicit "zero
main-quest content" rule — neither of which is "reject unless
knowledge-row-traceable." Raised this back before implementing anything,
rather than shipping a check that would fail every future escalation
quest by design.

**What I'd do differently.** Would have caught the `MAIN_QUEST` conflict
one step earlier if I'd read `docs/fact-database-design.md`'s C6/C8
definitions *before* proposing options in the report, rather than after
getting a decision back — the design doc already had the answer to
"why can't this be one rule" on file since the original design pass;
re-deriving it in the moment cost a round trip.

## Phase 7: RLS Was Off, and Supabase's Default Grants Made That Load-Bearing

**What was broken.** Supabase flagged RLS as disabled on all 8 tables in
`public`. The severity comes from the grants, not the RLS flag by itself:
Supabase's defaults hand `anon` and `authenticated` *full* DML on every
table in `public` — `SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES,
TRIGGER` — and PostgREST auto-exposes them. Verified before touching
anything: all 16 grant rows present, RLS off on all 8, zero policies. So
anyone holding the project URL and the anon key (a key that ships in
client code by design) could read, rewrite or delete the entire world
state.

**The check that had to come first.** The whole fix rests on the app not
caring, so that got verified before the change, not after: both
`DATABASE_URL` and `MIGRATION_DATABASE_URL` connect as `postgres`, and
`pg_roles` reports `rolbypassrls = true` for it (`rolsuper` is false —
Supabase's `postgres` is not a superuser, so BYPASSRLS is the attribute
doing the work, and it is the one that matters here). Had that come back
false, enabling RLS with no policies would have locked the app out of its
own database.

**What I chose, and on what grounds.** RLS enabled on all 8 tables with
**no policies at all**. An empty policy set is not an oversight — under
RLS, no matching policy means no row is visible or writable, so zero
policies is the maximally closed state. Put in `schema.sql` after the
`CREATE TABLE`s rather than applied as a one-off, so `init_db.py` re-asserts
it on every run; `ENABLE ROW LEVEL SECURITY` is idempotent, so the re-run
is a clean no-op (confirmed by running `init_db.py` twice).

**Verification.** `pg_tables.rowsecurity` true on 8/8, policy count 0.
Then empirically, via `SET LOCAL ROLE anon` inside a rolled-back
transaction: `SELECT` on `entities`/`quests`/`player` returns 0 rows where
`postgres` sees 13 entities; `UPDATE` and `DELETE` affect 0 rows; `INSERT`
is hard-rejected with `InsufficientPrivilege`. App side unaffected —
`pipeline.py` runs the full read path through the pooler and selects
Otto/`world_texture`, `/health` returns `{ok: true, npc_count: 7, tick: 50}`,
matching the pre-change baseline exactly.

**The gap this does not close — TRUNCATE.** RLS governs
`SELECT/INSERT/UPDATE/DELETE/MERGE`. It does **not** govern `TRUNCATE`,
which is controlled solely by the grant, and `anon` still holds
`TRUNCATE` on all 8 tables (`has_table_privilege` confirms it post-change).
This is not reachable today — PostgREST exposes no TRUNCATE verb, and
`anon` cannot open a direct Postgres connection — so it is a latent hole,
not an open one. But it means "RLS blocks REST access entirely" is true of
the flagged issue and not of the grants underneath it. The stronger fix is
`REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon, authenticated`, which
removes the exposure at its source instead of gating it. Deliberately not
done here: it is a different change from the one that was asked for, and
Supabase's default-grant machinery may re-apply grants on some operations,
so it wants its own pass with its own verification.

**Also checked, all clean.** No views, no materialized views (RLS does not
apply to matviews, so one in `public` would have been a real hole), and no
functions in `public` — so no `SECURITY DEFINER` surface. All five
extensions (`vector`, `pgcrypto`, `uuid-ossp`, `pg_stat_statements`,
`supabase_vault`) are installed outside `public`, so no extension functions
are exposed through it. The 7 identity sequences do grant `anon` usage,
which leaks nothing on its own and is moot once RLS blocks the inserts that
would consume them.

