"""
pipeline.py — Phase A pre-generation candidate selection
Implements A1–A6 from fact-database-design.md.

Takes a trigger (player_action string + player location_id) and returns
the selected (NPC, template) pair plus an assembled game state dict
ready for the quest generator.
"""

import json
import os

import openai

MAIN_QUEST      = "Rescue Elena from the Syndicate"
PLAYER_ENTITY_ID = 6
COOLDOWN_WINDOW  = 5    # recent quest rows to check for NPC cooldown
EMBEDDING_MODEL  = "text-embedding-3-small"

_openai_client = None


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        _openai_client = openai.OpenAI()
    return _openai_client


def embed_text(text):
    """Embed text via OpenAI text-embedding-3-small (1536 dims)."""
    response = _get_openai_client().embeddings.create(model=EMBEDDING_MODEL, input=text)
    return response.data[0].embedding


def _vector_literal(embedding):
    return "[" + ",".join(str(x) for x in embedding) + "]"


# ── Helpers ───────────────────────────────────────────────────────────────

def get_current_tick(conn):
    row = conn.execute('SELECT MAX("when") FROM events').fetchone()
    return row[0] or 0


def get_player_location(conn):
    row = conn.execute("SELECT current_location_id FROM player WHERE id = 1").fetchone()
    return row[0] if row else None


# ── A2: Candidate enumeration ─────────────────────────────────────────────

def get_candidate_npcs(conn, player_location_id):
    """
    Return NPCs that are alive and co-located with the player.
    Adjacent-location traversal is deferred to Godot integration (V2);
    V1 uses same location only.
    """
    rows = conn.execute("""
        SELECT id, name, properties, location_id
        FROM entities
        WHERE type = 'npc'
          AND status = 'alive'
          AND location_id = %s
          AND id != %s
    """, (player_location_id, PLAYER_ENTITY_ID)).fetchall()

    return [
        {"id": r[0], "name": r[1], "properties": json.loads(r[2]), "location_id": r[3]}
        for r in rows
    ]


# ── A3: Template eligibility ──────────────────────────────────────────────

def get_eligible_templates(conn, npc):
    eligible = []
    npc_id = npc["id"]
    props  = npc["properties"]

    # escalation: NPC has documented knowledge with confidence >= 0.5
    has_knowledge = conn.execute("""
        SELECT COUNT(*) FROM npc_knowledge
        WHERE npc_id = %s AND confidence >= 0.5
    """, (npc_id,)).fetchone()[0]
    if has_knowledge:
        eligible.append("escalation")

    # personal_crisis: NPC has both situation and stake authored
    if props.get("situation") and props.get("stake"):
        eligible.append("personal_crisis")

    # callback: at least one high-significance player choice exists that
    # this NPC could know about (via npc_knowledge row, confidence >= 0.5)
    callback_row = conn.execute("""
        SELECT pc.event_id
        FROM player_choices pc
        JOIN npc_knowledge nk ON nk.event_id = pc.event_id
        WHERE pc.significance = 'high'
          AND pc.callback_used = 0
          AND nk.npc_id = %s
          AND nk.confidence >= 0.5
        LIMIT 1
    """, (npc_id,)).fetchone()
    if callback_row:
        eligible.append("callback")

    # world_texture: always eligible — it is the fallback texture template
    eligible.append("world_texture")

    return eligible


# ── A4: Soft constraint scoring ───────────────────────────────────────────

def score_pair(conn, npc, template, current_tick):
    """
    Score one (NPC, template) pair. Returns (score, breakdown_dict).
    All multipliers start at 1.0; each constraint multiplies the running score.
    V1 ships: cooldown, variety, trust, callback_freshness, template_affinity, stake_activation, quest_load.
    """
    score      = 1.0
    breakdown  = {}
    npc_id     = npc["id"]
    props      = npc["properties"]

    # NPC cooldown — penalise if this NPC appears in the last COOLDOWN_WINDOW quests
    recent_count = conn.execute("""
        SELECT COUNT(*) FROM (
            SELECT npc_id FROM quests ORDER BY id DESC LIMIT %s
        ) t WHERE t.npc_id = %s
    """, (COOLDOWN_WINDOW, npc_id)).fetchone()[0]
    cooldown = 0.2 if recent_count > 0 else 1.0
    score   *= cooldown
    breakdown["npc_cooldown"] = cooldown

    # Template variety — penalise same template as the most recent quest
    last_template = conn.execute(
        "SELECT template_type FROM quests ORDER BY id DESC LIMIT 1"
    ).fetchone()
    variety = 0.6 if (last_template and last_template[0] == template) else 1.0
    score  *= variety
    breakdown["template_variety"] = variety

    # Trust gradient — check relationship NPC → player
    rel = conn.execute("""
        SELECT type, strength FROM relationships
        WHERE from_id = %s AND to_id = %s
    """, (npc_id, PLAYER_ENTITY_ID)).fetchone()
    if rel:
        rel_type, strength = rel
        if rel_type == "trusts" and strength is not None:
            trust = 1.0 + (strength * 0.5)
        elif rel_type == "distrusts" and strength is not None:
            trust = max(0.1, 1.0 - abs(strength) * 0.3)
        else:
            trust = 1.0
    else:
        trust = 1.0
    score *= trust
    breakdown["trust_gradient"] = round(trust, 3)

    # Callback freshness — decay based on age of best candidate choice
    # Only applies to callback template; other templates unaffected
    if template == "callback":
        best_tick = conn.execute("""
            SELECT e."when"
            FROM player_choices pc
            JOIN events e ON e.id = pc.event_id
            JOIN npc_knowledge nk ON nk.event_id = pc.event_id
            WHERE pc.significance = 'high'
              AND pc.callback_used = 0
              AND nk.npc_id = %s
              AND nk.confidence >= 0.5
            ORDER BY e."when" DESC
            LIMIT 1
        """, (npc_id,)).fetchone()
        if best_tick:
            age = current_tick - best_tick[0]
            freshness = 1.0 if age <= 10 else (0.7 if age <= 30 else 0.4)
        else:
            freshness = 0.0
        score *= freshness
        breakdown["callback_freshness"] = freshness
    else:
        breakdown["callback_freshness"] = "-"

    # Template affinity — bonus when NPC was authored for this template type
    affinity      = props.get("template_affinity")
    affinity_mult = 1.3 if affinity == template else 1.0
    score        *= affinity_mult
    breakdown["template_affinity"] = affinity_mult

    # Stake activation — V1: always 1.0
    # V2 expansion: detect whether a recent event threatened the NPC's stake referent
    breakdown["stake_activation"] = 1.0

    # Quest load — penalise all candidates if player already has 3+ active quests
    active = conn.execute("""
        SELECT COUNT(*) FROM quests WHERE status IN ('offered', 'accepted')
    """).fetchone()[0]
    load   = 0.5 if active >= 3 else 1.0
    score *= load
    breakdown["quest_load"] = load

    return round(score, 4), breakdown


def select_best_pair(conn, candidates, current_tick):
    """
    Score every eligible (NPC, template) pair and return the top scorer.
    Ties broken by iteration order (escalation > personal_crisis > callback > world_texture);
    within that, first candidate NPC wins. Design doc tie-break (least recently used)
    deferred to V2 when the quests table has enough history to be meaningful.
    """
    best_score = -1
    best       = None
    all_scores = {}

    for npc in candidates:
        templates = get_eligible_templates(conn, npc)
        for template in templates:
            score, breakdown = score_pair(conn, npc, template, current_tick)
            all_scores[(npc["name"], template)] = {"score": score, "breakdown": breakdown}
            if score > best_score:
                best_score = score
                best = (npc, template, score, breakdown)

    return best, all_scores


# ── A5: Game state assembly ───────────────────────────────────────────────

def build_npc_knowledge_text_keyword(conn, npc_id, trigger_action):
    """
    Build the npc_knowledge string for the game state.
    Prioritises knowledge of the triggering event, matched by a raw substring
    LIKE against the first 30 characters of the trigger; falls back to most
    recent knowledge. Kept alongside build_npc_knowledge_text (semantic) for
    comparison — see compare_knowledge_retrieval.py.
    """
    # Try to find knowledge of an event that matches the trigger
    trigger_rows = conn.execute("""
        SELECT e.what, k.channel, k.confidence
        FROM npc_knowledge k
        JOIN events e ON e.id = k.event_id
        WHERE k.npc_id = %s
          AND LOWER(e.what) LIKE LOWER(%s)
        ORDER BY e."when" DESC
        LIMIT 1
    """, (npc_id, f"%{trigger_action[:30]}%")).fetchall()

    # Fall back to three most recent knowledge rows
    recent_rows = conn.execute("""
        SELECT e.what, k.channel, k.confidence
        FROM npc_knowledge k
        JOIN events e ON e.id = k.event_id
        WHERE k.npc_id = %s
        ORDER BY e."when" DESC
        LIMIT 3
    """, (npc_id,)).fetchall()

    rows = trigger_rows if trigger_rows else recent_rows
    if not rows:
        return "No documented knowledge of recent events."

    parts = []
    for what, channel, conf in rows:
        parts.append(f"Learned via {channel} (confidence {conf:.1f}): {what}.")
    return " ".join(parts)


def build_npc_knowledge_text(conn, npc_id, trigger_action):
    """
    Build the npc_knowledge string for the game state.
    Prioritises knowledge of the triggering event, matched by embedding
    similarity (cosine distance) against events.embedding; falls back to
    most recent knowledge when the NPC has no embedded events to rank
    (embedding column NULL — backfill not run, or the event predates it).

    Filters by the npc_knowledge join first (this NPC's known events only),
    then ranks the result by similarity — never ranks across events the NPC
    doesn't actually know about.
    """
    trigger_embedding = _vector_literal(embed_text(trigger_action))

    # Try to find the known event closest in meaning to the trigger
    trigger_rows = conn.execute("""
        SELECT e.what, k.channel, k.confidence
        FROM npc_knowledge k
        JOIN events e ON e.id = k.event_id
        WHERE k.npc_id = %s
          AND e.embedding IS NOT NULL
        ORDER BY e.embedding <=> %s::vector
        LIMIT 1
    """, (npc_id, trigger_embedding)).fetchall()

    # Fall back to three most recent knowledge rows
    recent_rows = conn.execute("""
        SELECT e.what, k.channel, k.confidence
        FROM npc_knowledge k
        JOIN events e ON e.id = k.event_id
        WHERE k.npc_id = %s
        ORDER BY e."when" DESC
        LIMIT 3
    """, (npc_id,)).fetchall()

    rows = trigger_rows if trigger_rows else recent_rows
    if not rows:
        return "No documented knowledge of recent events."

    parts = []
    for what, channel, conf in rows:
        parts.append(f"Learned via {channel} (confidence {conf:.1f}): {what}.")
    return " ".join(parts)


def build_player_history(conn, npc_id, current_tick):
    """
    Build the player_history array for the callback template.
    Includes up to 3 high-significance choices (oldest first) that this NPC
    could plausibly know about via their npc_knowledge rows.
    """
    rows = conn.execute("""
        SELECT e.what, e."when", e.location_id, l.name AS loc_name,
               nk.channel, nk.confidence
        FROM player_choices pc
        JOIN events e ON e.id = pc.event_id
        JOIN npc_knowledge nk ON nk.event_id = pc.event_id
        LEFT JOIN entities l ON l.id = e.location_id
        WHERE pc.significance = 'high'
          AND pc.callback_used = 0
          AND nk.npc_id = %s
          AND nk.confidence >= 0.5
        ORDER BY e."when" ASC
        LIMIT 3
    """, (npc_id,)).fetchall()

    history = []
    for what, tick, loc_id, loc_name, channel, conf in rows:
        age_ticks = current_tick - tick
        loc_str = f" at {loc_name}" if loc_name else ""
        context = (
            f"{age_ticks} ticks ago{loc_str}. "
            f"Observed by this NPC via {channel} (confidence {conf:.1f})."
        )
        history.append({"action": what, "context": context})
    return history


def get_referenced_choice(conn, npc_id, current_tick):
    """
    Select the single best past choice for a callback — most recent high-significance
    event this NPC witnessed or was told about, not yet used as a callback.
    """
    row = conn.execute("""
        SELECT e.what, e."when", l.name AS loc_name, nk.channel, nk.confidence
        FROM player_choices pc
        JOIN events e ON e.id = pc.event_id
        JOIN npc_knowledge nk ON nk.event_id = pc.event_id
        LEFT JOIN entities l ON l.id = e.location_id
        WHERE pc.significance = 'high'
          AND pc.callback_used = 0
          AND nk.npc_id = %s
          AND nk.confidence >= 0.5
        ORDER BY e."when" DESC
        LIMIT 1
    """, (npc_id,)).fetchone()
    if not row:
        return None
    what, tick, loc_name, channel, conf = row
    age_ticks = current_tick - tick
    loc_str = f" at {loc_name}" if loc_name else ""
    return {
        "action": what,
        "context": (
            f"{age_ticks} ticks ago{loc_str}. "
            f"This NPC observed it via {channel} (confidence {conf:.1f}). "
            f"The player did not know they were being watched."
        ),
    }


def build_npc_beliefs_text(conn, npc_id):
    """
    Build the npc_beliefs string for the game state — this NPC's current
    conclusions about the player, as formed by beliefs.py's rule-based
    pass. A belief with a contradicting_event_id is flagged as held with
    some uncertainty; it isn't dropped, since the NPC still holds it.
    """
    rows = conn.execute("""
        SELECT belief_text, confidence, contradicting_event_id
        FROM npc_beliefs
        WHERE npc_id = %s
        ORDER BY confidence DESC
    """, (npc_id,)).fetchall()

    if not rows:
        return "No settled beliefs about the player yet."

    parts = []
    for belief_text, confidence, contradicting_event_id in rows:
        note = " (has since seen something that complicates this)" if contradicting_event_id else ""
        parts.append(f"{belief_text} (confidence {confidence:.2f}){note}")
    return " ".join(parts)


def assemble_game_state(conn, npc, template, player_action, current_tick):
    props  = npc["properties"]
    npc_id = npc["id"]

    game_state = {
        "main_quest":    MAIN_QUEST,
        "player_action": player_action,
        "npc_name":      npc["name"],
        "npc_situation": props.get("situation", ""),
        "npc_knowledge": build_npc_knowledge_text(conn, npc_id, player_action),
        "npc_beliefs":   build_npc_beliefs_text(conn, npc_id),
    }

    if template == "callback":
        game_state["player_history"]    = build_player_history(conn, npc_id, current_tick)
        game_state["referenced_choice"] = get_referenced_choice(conn, npc_id, current_tick)

    return game_state


# ── A6: Pre-generation hard check ────────────────────────────────────────

def pre_check(conn, npc, player_location_id):
    """
    Verify NPC is still alive and co-located with the player before spending tokens.
    Returns (True, "ok") or (False, reason_string).
    """
    row = conn.execute(
        "SELECT status, location_id FROM entities WHERE id = %s", (npc["id"],)
    ).fetchone()

    if not row:
        return False, f"NPC id={npc['id']} not found in entities"
    if row[0] != "alive":
        return False, f"{npc['name']} is not alive (status={row[0]})"
    if row[1] != player_location_id:
        npc_loc = conn.execute(
            "SELECT name FROM entities WHERE id = %s", (row[1],)
        ).fetchone()
        loc_name = npc_loc[0] if npc_loc else f"id={row[1]}"
        return False, f"{npc['name']} is at {loc_name}, not at player location"

    has_knowledge = conn.execute(
        "SELECT COUNT(*) FROM npc_knowledge WHERE npc_id = %s", (npc["id"],)
    ).fetchone()[0]
    if not has_knowledge:
        return False, f"{npc['name']} has no documented knowledge of any events"

    return True, "ok"


# ── Main pipeline entry point ─────────────────────────────────────────────

def run_pipeline(conn, player_action: str, player_location_id: int):
    """
    Run Phase A. Returns (result_dict, status_string).
    result_dict is None on failure.
    """
    current_tick = get_current_tick(conn)

    # A2
    candidates = get_candidate_npcs(conn, player_location_id)
    if not candidates:
        return None, "No candidate NPCs at player location"

    # A3 + A4
    best, all_scores = select_best_pair(conn, candidates, current_tick)
    if not best:
        return None, "No eligible (NPC, template) pairs found"

    npc, template, score, breakdown = best

    # A6 pre-check (fast fail before A5 assembly)
    ok, reason = pre_check(conn, npc, player_location_id)
    if not ok:
        return None, f"Pre-check failed: {reason}"

    # A5
    game_state = assemble_game_state(conn, npc, template, player_action, current_tick)

    return {
        "npc_id":     npc["id"],
        "npc_name":   npc["name"],
        "template":   template,
        "score":      score,
        "breakdown":  breakdown,
        "all_scores": all_scores,
        "game_state": game_state,
    }, "ok"


# ── Test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import psycopg
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
    # prepare_threshold=None: DATABASE_URL is a PgBouncer transaction-mode
    # pooler connection, which can hand different client sessions the same
    # backend and collide on psycopg's auto-named prepared statements.
    conn = psycopg.connect(os.environ["DATABASE_URL"], prepare_threshold=None)

    player_location_id = get_player_location(conn)  # reads from player table
    trigger_action     = "Bribed the eastern gate guard to pass through after curfew"

    loc_name = conn.execute(
        "SELECT name FROM entities WHERE id = %s", (player_location_id,)
    ).fetchone()[0]

    print("=== Pipeline test ===")
    print(f"Trigger:         {trigger_action}")
    print(f"Player location: {loc_name} (id={player_location_id})\n")

    result, status = run_pipeline(conn, trigger_action, player_location_id)

    if result is None:
        print(f"Pipeline returned None — {status}")
    else:
        print(f"Selected NPC:  {result['npc_name']}")
        print(f"Template:      {result['template']}")
        print(f"Score:         {result['score']}")

        print("\nScore breakdown:")
        for k, v in result["breakdown"].items():
            print(f"  {k:<22} {v}")

        print("\nAll (NPC, template) scores:")
        sorted_scores = sorted(
            result["all_scores"].items(), key=lambda x: -x[1]["score"]
        )
        for (npc_name, tmpl), data in sorted_scores:
            print(f"  {npc_name:<12} {tmpl:<18} {data['score']}")

        print("\nGame state:")
        print(json.dumps(result["game_state"], indent=2))

    conn.close()
