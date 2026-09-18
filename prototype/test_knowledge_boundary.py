"""
test_knowledge_boundary.py — regression test for the knowledge-boundary leak
in assemble_game_state() and the four prompt builders in quest_generator_v4.py.

pipeline.py's npc_knowledge join correctly scopes retrieval — build_npc_knowledge_text,
build_player_history, and get_referenced_choice all filter to what a specific NPC
actually knows before ranking or returning anything. But assemble_game_state() also
puts the raw player_action string straight into game_state, unfiltered by any
npc_knowledge check, and every entry in quest_generator_v4.PROMPT_BUILDERS
interpolates it directly into the prompt's GAME STATE block. The permission
boundary the README calls "positional, not universal" knowledge is built into
build_npc_knowledge_text — and then bypassed one field over, for every NPC, every
time.

This test picks, for each of the four seeded quest-giver NPCs, a trigger
describing a real seeded event that NPC holds ZERO npc_knowledge rows for
(checked against the live DB, not assumed from reading seed_db.py), builds the
real game_state via pipeline.assemble_game_state(), runs it through the real
prompt builder, calls the model directly, and checks the raw generated quest
text for terms unique to the unlearned event.

Deliberately does not call quest_generator_v4.generate_quest(): that function
also validates and writes a row to `quests` (plus a relationship-strength
nudge for the callback template), none of which this defect concerns, and
running this test repeatedly would leave throwaway rows in the live Supabase
DB every time. This test exercises exactly the two real functions the defect
lives in — assemble_game_state() and PROMPT_BUILDERS — and nothing else.

Expected to FAIL before the knowledge-boundary fix (that's what makes this a
regression test) and PASS after it.
"""

import json
import os
import sys

_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _DIR)

import anthropic
import psycopg
from dotenv import load_dotenv

import pipeline as pipe
import quest_generator_v4 as qgen

load_dotenv(os.path.join(_DIR, ".env"))

client = anthropic.Anthropic()


def get_npc(conn, npc_id):
    row = conn.execute(
        "SELECT id, name, properties, location_id FROM entities WHERE id = %s",
        (npc_id,),
    ).fetchone()
    return {"id": row[0], "name": row[1], "properties": json.loads(row[2]), "location_id": row[3]}


def npc_has_no_knowledge_of(conn, npc_id, event_what_substring):
    """Precondition check against the live DB, not against the seed script's source."""
    row = conn.execute("""
        SELECT COUNT(*) FROM npc_knowledge k
        JOIN events e ON e.id = k.event_id
        WHERE k.npc_id = %s AND e.what ILIKE %s
    """, (npc_id, f"%{event_what_substring}%")).fetchone()
    return row[0] == 0


# (npc_id, template, trigger, unlearned-event substring, marker terms to search for)
CASES = [
    (9, "callback",
     "Mikhail asked Daria how old he would need to be to apply for Syndicate youth enrollment",
     "Mikhail asked Daria", ["mikhail", "enrollment"]),
    (7, "escalation",
     "Bribed the eastern gate guard to pass through after curfew",
     "Bribed the eastern gate guard", ["curfew", "bribe"]),
    (8, "personal_crisis",
     "Bribed the eastern gate guard to pass through after curfew",
     "Bribed the eastern gate guard", ["curfew", "bribe"]),
    (10, "world_texture",
     "Bribed the eastern gate guard to pass through after curfew",
     "Bribed the eastern gate guard", ["curfew", "bribe"]),
]


def run_case(conn, npc_id, template, trigger, event_substring, markers):
    npc = get_npc(conn, npc_id)

    if not npc_has_no_knowledge_of(conn, npc_id, event_substring):
        raise RuntimeError(
            f"precondition violated: {npc['name']} (id={npc_id}) DOES have an "
            f"npc_knowledge row for an event matching '{event_substring}' — "
            f"pick a different (npc, event) pair, this one can't test the boundary"
        )

    current_tick = pipe.get_current_tick(conn)
    game_state = pipe.assemble_game_state(conn, npc, template, trigger, current_tick)
    prompt_npc = qgen.load_npc_for_prompt(conn, npc_id)
    prompt = qgen.PROMPT_BUILDERS[template](game_state, prompt_npc)

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )
    quest_text = message.content[0].text
    quest_lower = quest_text.lower()

    hits = [m for m in markers if m.lower() in quest_lower]
    return npc["name"], quest_text, hits


def main():
    conn = psycopg.connect(os.environ["DATABASE_URL"], prepare_threshold=None)

    print("=" * 78)
    print("KNOWLEDGE BOUNDARY REGRESSION TEST")
    print("Each case: an NPC with zero npc_knowledge rows for the triggering event.")
    print("PASS = generated quest text contains none of the event's marker terms.")
    print("=" * 78)

    total_failures = 0
    for npc_id, template, trigger, event_substring, markers in CASES:
        name, quest_text, hits = run_case(conn, npc_id, template, trigger, event_substring, markers)
        status = "FAIL" if hits else "PASS"
        if hits:
            total_failures += 1
        print(f"\n[{status}] {name} (id={npc_id}) / {template}")
        print(f'  trigger:         "{trigger}"')
        print(f"  unlearned event: {event_substring}")
        print(f"  markers checked: {markers}")
        print(f"  markers found:   {hits or 'none'}")
        if hits:
            print(f"  --- generated quest text ---\n{quest_text}\n  ---")

    conn.close()

    print("\n" + "=" * 78)
    print(f"TOTAL FAILURES: {total_failures} / {len(CASES)}")
    print("=" * 78)

    sys.exit(1 if total_failures else 0)


if __name__ == "__main__":
    main()
