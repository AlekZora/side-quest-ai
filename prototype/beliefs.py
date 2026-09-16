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

# Event ids duplicated from seed_db.py rather than imported — this module
# should be able to reason about belief provenance without depending on
# how the world happens to be seeded.
EVT_WOMAN_AT_GATE   = 1
EVT_CURFEW_BRIBE    = 2
EVT_MANIFEST_BURNED = 3


class BeliefRule:
    def __init__(self, key, belief_text, supporting_events, threshold):
        self.key = key
        self.belief_text = belief_text
        self.supporting_events = frozenset(supporting_events)
        self.threshold = threshold


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
    ),
]
