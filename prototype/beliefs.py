"""
beliefs.py — rule-based npc_beliefs formation (Phase 3).

npc_knowledge holds facts an NPC knows about specific events. A belief is
different: a generalization across multiple facts that could turn out
wrong — "the player is dangerous" is not a fact anyone witnessed, it's a
conclusion an NPC draws from facts they did witness. Formation here is
rule-based, not model-based, so every belief's confidence traces back to
specific event ids a specific NPC actually knows about via npc_knowledge —
that trace is the "provenance" the belief needs to be trustworthy as game
state.

Rules (see BELIEF_RULES below for the exact mapping to event ids):

  player_is_dangerous
    Support: deceiving a guard to free a detainee (EVT_WOMAN_AT_GATE),
    destroying Syndicate property (EVT_MANIFEST_BURNED). Low threshold —
    per the brief, "fear generalizes from less evidence than trust": a
    single told_by (confidence 0.8) is already enough.

  player_can_be_bought
    Support: the player using a bribe to get through a checkpoint
    (EVT_CURFEW_BRIBE). Higher threshold than danger — this is a specific
    claim about what moves the player, not just a threat-detection
    reflex, so a rumor alone (0.4) shouldn't be enough.

  player_serves_the_syndicate
    Support: the same bribe (EVT_CURFEW_BRIBE) — read paranoidly, as
    evidence the player operates comfortably inside Syndicate checkpoint
    infrastructure. Threshold is deliberately low: this is a suspicious,
    jump-to-conclusions belief, thin by design. (Contradiction wired in
    a later step — this is the rule used to demonstrate it.)

A fourth suggested belief, "player keeps their word", is not implemented:
nothing in the current world depicts the player making and keeping (or
breaking) a commitment, so there's no honest evidence to rule against.
Forcing a mapping onto an unrelated event would break the provenance
requirement this whole module exists to satisfy. See MIGRATION-NOTES.md.
"""

import os

import psycopg
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

PLAYER_ENTITY_ID = 6  # matches pipeline.PLAYER_ENTITY_ID

CONTRADICTION_FLOOR  = 0.15  # a counter-example makes an NPC uncertain, not converted
CONTRADICTION_FACTOR = 0.5   # confidence is halved, not zeroed, when contradicted

# Event ids duplicated from seed_db.py rather than imported — this module
# should be able to reason about belief provenance without depending on
# how the world happens to be seeded.
EVT_WOMAN_AT_GATE   = 1
EVT_CURFEW_BRIBE    = 2
EVT_MANIFEST_BURNED = 3


class BeliefRule:
    def __init__(self, key, belief_text, supporting_events, threshold,
                 contradicting_events=frozenset()):
        self.key = key
        self.belief_text = belief_text
        self.supporting_events = frozenset(supporting_events)
        self.threshold = threshold
        self.contradicting_events = frozenset(contradicting_events)


BELIEF_RULES = [
    BeliefRule(
        key="player_is_dangerous",
        belief_text=(
            "The player is dangerous — willing to deceive guards and destroy "
            "Syndicate property to get what they want."
        ),
        supporting_events={EVT_WOMAN_AT_GATE, EVT_MANIFEST_BURNED},
        threshold=0.7,
    ),
    BeliefRule(
        key="player_can_be_bought",
        belief_text=(
            "The player operates on money and favors — a bribe or a deal will move them."
        ),
        supporting_events={EVT_CURFEW_BRIBE},
        threshold=0.75,
    ),
    BeliefRule(
        key="player_serves_the_syndicate",
        belief_text="The player is embedded with the Syndicate, not against it.",
        supporting_events={EVT_CURFEW_BRIBE},
        threshold=0.35,
        contradicting_events={EVT_MANIFEST_BURNED},
    ),
]


def evaluate_rule(rule, knowledge_rows):
    """
    knowledge_rows: iterable of (event_id, confidence) — everything one NPC
    knows via npc_knowledge, regardless of channel (channel is already
    baked into each row's confidence value).

    Returns (forms, confidence, contradicting_event_id). forms is False
    (confidence/contradicting_event_id both None) when summed support
    doesn't clear the rule's threshold — nothing to contradict if the
    belief never formed in the first place.

    Contradiction only looks at events THIS NPC's own knowledge_rows
    contain: an NPC whose knowledge never includes the contradicting
    event keeps their wrong belief at full confidence, because as far as
    their own evidence goes, nothing corrects it.
    """
    knowledge_rows = list(knowledge_rows)

    support_sum = sum(c for eid, c in knowledge_rows if eid in rule.supporting_events)
    if support_sum < rule.threshold:
        return False, None, None

    base_confidence = min(1.0, support_sum)

    contradicting = [(eid, c) for eid, c in knowledge_rows if eid in rule.contradicting_events]
    if contradicting:
        confidence = max(CONTRADICTION_FLOOR, base_confidence * CONTRADICTION_FACTOR)
        contradicting_event_id = contradicting[0][0]
    else:
        confidence = base_confidence
        contradicting_event_id = None

    return True, confidence, contradicting_event_id


def get_npc_knowledge_rows(conn, npc_id):
    """(event_id, confidence) pairs for every event this NPC knows about."""
    rows = conn.execute(
        "SELECT event_id, confidence FROM npc_knowledge WHERE npc_id = %s",
        (npc_id,),
    ).fetchall()
    return [(r[0], r[1]) for r in rows]


def form_beliefs_for_npc(conn, npc_id, current_tick, knowledge_rows=None):
    """
    Evaluate every rule for one NPC and upsert npc_beliefs accordingly.
    Idempotent via ON CONFLICT (npc_id, belief_text) — re-running recomputes
    from this NPC's current full npc_knowledge rather than applying a delta,
    so a belief that no longer clears threshold (shouldn't happen with
    append-only knowledge, but keeps this a true "current state" pass) is
    deleted rather than left stale.

    knowledge_rows lets a caller supply an already-fetched/filtered view
    instead of hitting the DB — used by demo_beliefs.py to simulate "before
    this NPC learned event X" without touching real data.

    Returns a list of (rule.key, forms, confidence, contradicting_event_id).
    """
    if knowledge_rows is None:
        knowledge_rows = get_npc_knowledge_rows(conn, npc_id)

    results = []
    for rule in BELIEF_RULES:
        forms, confidence, contradicting_event_id = evaluate_rule(rule, knowledge_rows)
        if forms:
            conn.execute("""
                INSERT INTO npc_beliefs (npc_id, belief_text, confidence, contradicting_event_id, formed_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (npc_id, belief_text) DO UPDATE SET
                    confidence = EXCLUDED.confidence,
                    contradicting_event_id = EXCLUDED.contradicting_event_id,
                    formed_at = EXCLUDED.formed_at
            """, (npc_id, rule.belief_text, confidence, contradicting_event_id, current_tick))
        else:
            conn.execute(
                "DELETE FROM npc_beliefs WHERE npc_id = %s AND belief_text = %s",
                (npc_id, rule.belief_text),
            )
        results.append((rule.key, forms, confidence, contradicting_event_id))
    return results


def form_all_beliefs(conn, current_tick):
    """Run the formation pass for every alive NPC except the player."""
    npc_ids = [r[0] for r in conn.execute(
        "SELECT id FROM entities WHERE type = 'npc' AND status = 'alive' AND id != %s",
        (PLAYER_ENTITY_ID,),
    ).fetchall()]

    all_results = {}
    for npc_id in npc_ids:
        all_results[npc_id] = form_beliefs_for_npc(conn, npc_id, current_tick)
    conn.commit()
    return all_results


if __name__ == "__main__":
    conn = psycopg.connect(os.environ["DATABASE_URL"])

    current_tick = conn.execute('SELECT MAX("when") FROM events').fetchone()[0] or 0
    results = form_all_beliefs(conn, current_tick)

    names = dict(conn.execute("SELECT id, name FROM entities").fetchall())

    print(f"Formation pass at tick {current_tick}\n")
    for npc_id, rule_results in results.items():
        print(f"{names[npc_id]} (id={npc_id}):")
        formed_any = False
        for key, forms, confidence, contradicting_event_id in rule_results:
            if forms:
                formed_any = True
                note = f", contradicted by event {contradicting_event_id}" if contradicting_event_id else ""
                print(f"  [{key}] confidence={confidence:.2f}{note}")
        if not formed_any:
            print("  (no beliefs cleared threshold)")
        print()

    conn.close()
