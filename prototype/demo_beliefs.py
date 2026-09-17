"""
demo_beliefs.py — Phase 3 demo.

Part 1: same world, different NPCs — each holds different beliefs about
the player because each knows a different subset of events, through
different channels.

Part 2: contradiction — Otto's player_serves_the_syndicate belief shown
before vs after his knowledge includes the event that contradicts it.
"""

import os

import psycopg
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

import beliefs as bel

OTTO  = 9
SERGE = 7
DARIA = 8
NADIA = 10


def print_npc_beliefs(conn, npc_id, label):
    rows = conn.execute("""
        SELECT belief_text, confidence, contradicting_event_id
        FROM npc_beliefs WHERE npc_id = %s ORDER BY confidence DESC
    """, (npc_id,)).fetchall()

    print(f"{label}:")
    if not rows:
        print("  (no beliefs — insufficient evidence)")
    for belief_text, confidence, contradicting_event_id in rows:
        note = f"  [contradicted by event {contradicting_event_id}]" if contradicting_event_id else ""
        print(f"  confidence={confidence:.2f}  {belief_text}{note}")
    print()


def main():
    # prepare_threshold=None: DATABASE_URL is a PgBouncer transaction-mode
    # pooler connection, which can hand different client sessions the same
    # backend and collide on psycopg's auto-named prepared statements.
    conn = psycopg.connect(os.environ["DATABASE_URL"], prepare_threshold=None)
    current_tick = conn.execute('SELECT MAX("when") FROM events').fetchone()[0] or 0

    print("=" * 72)
    print("  PART 1 — different NPCs, different beliefs about the same player")
    print("=" * 72)
    print(
        "Otto directly witnessed the curfew bribe and was told about the manifest\n"
        "burning. Serge and Daria only heard about the manifest burning secondhand\n"
        "(told_by). Nadia only caught it as a rumor. None of them know about each\n"
        "other's evidence — each NPC's belief comes only from what reached them.\n"
    )

    bel.form_all_beliefs(conn, current_tick)  # ensure npc_beliefs reflects current knowledge

    print_npc_beliefs(conn, OTTO,  "Otto  (witnessed bribe, told_by manifest)")
    print_npc_beliefs(conn, SERGE, "Serge (told_by manifest only)")
    print_npc_beliefs(conn, DARIA, "Daria (told_by manifest only)")
    print_npc_beliefs(conn, NADIA, "Nadia (rumor of manifest only)")

    print("=" * 72)
    print("  PART 2 — contradiction: Otto, before vs after the manifest event")
    print("=" * 72)

    all_knowledge    = bel.get_npc_knowledge_rows(conn, OTTO)
    before_knowledge = [(eid, c) for eid, c in all_knowledge if eid != bel.EVT_MANIFEST_BURNED]
    rule = next(r for r in bel.BELIEF_RULES if r.key == "player_serves_the_syndicate")

    forms, confidence, contradicting = bel.evaluate_rule(rule, before_knowledge)
    print(f"\nBEFORE Otto's knowledge includes event {bel.EVT_MANIFEST_BURNED} (manifest burning):")
    print(f"  forms={forms}  confidence={confidence}  contradicting_event_id={contradicting}")

    forms, confidence, contradicting = bel.evaluate_rule(rule, all_knowledge)
    print("\nAFTER — Otto's real, full current knowledge:")
    print(f"  forms={forms}  confidence={confidence}  contradicting_event_id={contradicting}")

    conn.close()


if __name__ == "__main__":
    main()
