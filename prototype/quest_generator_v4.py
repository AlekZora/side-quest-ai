"""
quest_generator_v4.py — End-to-end pipeline → generation → validation → DB write.

Flow:
  1. pipeline.run_pipeline()  — select NPC, template, assemble game state from DB
  2. load_npc_for_prompt()    — load NPC want/stake/network from entities table
  3. Route to correct prompt builder
  4. Call Claude Haiku API
  5. validator.validate()     — C1/C3/C4/C5 hard constraint checks
  6. write_quest()            — insert into quests table
  7. Print summary
"""

import json
import os
import re
import sqlite3
import sys

import anthropic

# Import pipeline and validator from the same directory
_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _DIR)
import pipeline as pipe
import validator as val

DB_PATH = os.path.join(_DIR, "blackwater.db")

client = anthropic.Anthropic()


# ── NPC loader ────────────────────────────────────────────────────────────────

def load_npc_for_prompt(conn, npc_id):
    """
    Load NPC name and properties from the entities table.
    Returns {name, situation, want, stake, network} for prompt builders.
    """
    row = conn.execute(
        "SELECT name, properties FROM entities WHERE id = ?", (npc_id,)
    ).fetchone()
    if not row:
        raise ValueError(f"NPC id={npc_id} not found in entities")
    name, props_json = row
    props = json.loads(props_json) if props_json else {}
    return {
        "name":      name,
        "situation": props.get("situation", ""),
        "want":      props.get("want", ""),
        "stake":     props.get("stake", ""),
        "network":   props.get("network", ""),
    }


# ── Referenced choice event_id (for C5 validation) ───────────────────────────

def get_referenced_choice_event_id(conn, npc_id):
    """
    Return the event_id of the most recent high-significance player choice
    this NPC knows about and has not yet used as a callback.
    Mirrors the logic in pipeline.get_referenced_choice().
    """
    row = conn.execute("""
        SELECT pc.event_id
        FROM player_choices pc
        JOIN events e ON e.id = pc.event_id
        JOIN npc_knowledge nk ON nk.event_id = pc.event_id
        WHERE pc.significance = 'high'
          AND pc.callback_used = 0
          AND nk.npc_id = ?
          AND nk.confidence >= 0.5
        ORDER BY e."when" DESC
        LIMIT 1
    """, (npc_id,)).fetchone()
    return row[0] if row else None


# ── DB write ──────────────────────────────────────────────────────────────────

def write_quest(conn, npc_id, template_type, status, quest_text,
                referenced_event_id, current_tick, validation_log):
    cursor = conn.execute("""
        INSERT INTO quests
            (npc_id, template_type, status, generated_text,
             referenced_event_id, created_at, validation_log)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (npc_id, template_type, status, quest_text,
          referenced_event_id, current_tick, validation_log))
    if template_type == "callback" and referenced_event_id is not None and status == "validated":
        conn.execute(
            "UPDATE player_choices SET callback_used = 1 WHERE event_id = ?",
            (referenced_event_id,)
        )
    conn.commit()
    return cursor.lastrowid


# ── Prompt builders (sourced from quest-generator-v3.py) ─────────────────────

def build_escalation_prompt(gs, npc):
    return f"""You are a quest designer for a narrative RPG.

GAME STATE:
  Main quest: {gs['main_quest']}
  Player's last action: {gs['player_action']}
  Current situation: {gs['npc_situation']}
  How {npc['name']} learned of the player's action: {gs['npc_knowledge']}

NPC — {npc['name']}:
  Who they are: {npc['situation']}
  What they want: {npc['want']}
  What they stand to lose: {npc['stake']}
  Who they know / what they have access to: {npc['network']}

Generate a main quest escalation quest where {npc['name']} approaches the player.
The task is a means to a revelation — the reveal is the reward, not the errand.

Include exactly these five things:

1. WHY {npc['name']} is approaching the player right now — connect the player's
   action to {npc['name']}'s current situation. The player's action is what makes
   {npc['name']} willing to risk this conversation. Be specific about the connection.

2. WHAT {npc['name']} needs from the player — a concrete task that uses the kind
   of capability the player demonstrated in {gs['player_action']}.

3. WHAT it costs the player to help — time, resources, exposure, or moral weight.
   Must be real, not a token errand.

4. WHAT {npc['name']} reveals after the task is complete — must come from their
   actual network access, not invented sources. This revelation must recontextualize
   something specific about {gs['main_quest']} that the player thought they
   understood. Do not invent information the NPC could not plausibly have.

5. WHAT CHANGES — one sentence on how the player's understanding of
   {gs['main_quest']} is different after this reveal than before.

Keep it grounded and specific. The revelation must be something only {npc['name']}
could know through their specific network. This quest must not make sense for a
player who did anything other than {gs['player_action']}."""


def build_personal_crisis_prompt(gs, npc):
    return f"""You are a quest designer for a narrative RPG.

GAME STATE:
  Main quest: {gs['main_quest']}
  Player's last action: {gs['player_action']}
  Current situation: {gs['npc_situation']}
  How {npc['name']} learned of the player's action: {gs['npc_knowledge']}

NPC — {npc['name']}:
  Who they are: {npc['situation']}
  What they want: {npc['want']}
  What they stand to lose: {npc['stake']}
  Who they know / what they have access to: {npc['network']}

Generate an NPC personal crisis quest where {npc['name']} approaches the player.
The quest must emerge entirely from {npc['name']}'s situation and stake.
The main quest is background context only — do not make it the emotional center.

Include exactly these five things:

1. WHY {npc['name']} is approaching the player specifically — the player's action
   is what established the trust or created the specific need. {npc['name']} is not
   approaching because the player is the hero. They are approaching because of
   what {gs['player_action']} revealed about what kind of person the player is.
   Name the quality the player demonstrated that made {npc['name']} choose them.

2. WHAT the crisis is — derive it directly from {npc['stake']}. What is actively
   threatening what {npc['name']} stands to lose, and why is it happening now?
   The crisis must be concrete, not atmospheric.

3. WHAT {npc['name']} needs from the player — a specific ask that reflects both
   their want and what their stake makes them unwilling or unable to do themselves.
   Do not make this an errand. It should require something most people would not offer.

4. WHAT it costs the player to help — must be real. Not time or gold: exposure,
   a relationship, a future option foreclosed.

5. WHAT the emotional weight of the quest is — one sentence naming exactly what
   {npc['name']} is actually protecting and what it would mean to lose it. This
   is not the objective. It is the reason the objective matters to a person.

Keep it grounded and specific. {npc['name']}'s ask must be shaped by what they
stand to lose, not by what would be useful to the player. This quest should
produce the player reaction: "I'm helping because of who she is, not because
of the main quest.\""""


def build_callback_prompt(gs, npc):
    history_lines = "\n".join([
        f"  {i + 1}. {entry['action']}. {entry['context']}"
        for i, entry in enumerate(gs["player_history"])
    ])
    ref = gs["referenced_choice"]

    return f"""You are a quest designer for a narrative RPG.

GAME STATE:
  Main quest: {gs['main_quest']}
  Player's most recent action: {gs['player_action']}
  Current situation: {gs['npc_situation']}
  How {npc['name']} knows of the player's recent action: {gs['npc_knowledge']}

PLAYER HISTORY (oldest first):
{history_lines}

REFERENCED PAST CHOICE (the reason for this approach):
  Choice: {ref['action']}
  When and where: {ref['context']}

NPC — {npc['name']}:
  Who they are: {npc['situation']}
  What they want: {npc['want']}
  What they stand to lose: {npc['stake']}
  Who they know / what they have access to: {npc['network']}

Generate a player-choice callback quest where {npc['name']} approaches the player
because of the referenced past choice — not because of the most recent action.
The most recent action is only what created the opening to approach now.

Include exactly these five things:

1. WHY {npc['name']} is approaching now — something in the current situation has
   surfaced the past choice. Explain what made this the moment to act, and why
   the past choice is the actual reason. These are two different things. Be
   explicit about both.

2. WHAT {npc['name']} observed or learned about the referenced choice — how they
   witnessed it, what channel it reached them through, and what they concluded
   about the player from it. Their knowledge must be plausible given their network.

3. WHAT {npc['name']} needs — something that only a player who made that past
   choice would credibly do again, or would be trusted to do. The ask must
   connect to what the past choice revealed about the player's values.

4. WHAT it costs the player to help — must be real, not token.

5. THE RECOGNITION LINE — one exact line of dialogue that {npc['name']} says
   that proves they were watching when the player thought no one was. This is
   the moment the experience goal lands or fails. The line must name the past
   choice specifically enough to trigger recall without summarizing it flatly.
   It should feel like being caught — not accused, caught.

Keep it grounded and specific. The past choice is the reason for the approach.
The player should feel retroactive recognition: the world was tracking something
they did before they knew the world was watching."""


def build_world_texture_prompt(gs, npc):
    return f"""You are a quest designer for a narrative RPG.

GAME STATE:
  Main quest: {gs['main_quest']}
  Player's last action: {gs['player_action']}
  Current situation: {gs['npc_situation']}
  How {npc['name']} learned of the player's action: {gs['npc_knowledge']}

NPC — {npc['name']}:
  Who they are: {npc['situation']}
  What they want: {npc['want']}
  What they stand to lose: {npc['stake']}
  Who they know / what they have access to: {npc['network']}

Generate a world texture quest where {npc['name']} approaches the player.
This quest has no connection to {gs['main_quest']}.
Do not reference {gs['main_quest']} in the quest output.
Do not provide intel about the main story.
Do not escalate any stakes beyond {npc['name']}'s personal situation.

The player's action reached {npc['name']} through the world — that is the only
required connection. The quest is entirely about {npc['name']}'s life.

Include exactly these five things:

1. HOW the player's action reached {npc['name']} — through what specific channel,
   and what {npc['name']} concluded from it. This should feel incidental, not
   fated. The action is why {npc['name']} knows to approach this specific person.
   It is not why the quest exists.

2. WHAT {npc['name']}'s actual situation is — not a summary, but what it feels
   like from the inside. What {npc['name']} is dealing with right now, in concrete
   terms. This is the emotional center of the quest. It must be interesting
   without any reference to the main story.

3. WHAT {npc['name']} needs from the player — specific and shaped by their want.
   Must connect to the kind of capability the player demonstrated in
   {gs['player_action']}.

4. WHAT it costs the player to help — real cost, not a token errand.

5. WHAT STAYS UNRESOLVED — after the player helps, what is still true about
   {npc['name']}'s situation. The deeper problem — what they stand to lose —
   does not go away when the immediate need is met. Name it in one sentence.
   This is what makes the world feel inhabited rather than designed.

Keep it grounded and specific. This quest should feel like it would exist in
this world regardless of the main story. The player's instinct after accepting
should be: "this has nothing to do with my main objective — I'm just helping
someone.\""""


PROMPT_BUILDERS = {
    "escalation":     build_escalation_prompt,
    "personal_crisis": build_personal_crisis_prompt,
    "callback":       build_callback_prompt,
    "world_texture":  build_world_texture_prompt,
}


# ── Generation ────────────────────────────────────────────────────────────────

# A retry re-samples the *same* prompt, so it can only help when the failure
# depends on what the model happened to write. C3 (hallucinated entity) and C4
# (referenced a dead/destroyed entity) are that kind of failure — a different
# draft may simply not name the offending thing. C1 (missing numbered items)
# and C5 (callback bookkeeping) are not: C1 is a formatting mismatch that
# reproduces, and C5 is decided by DB state that no re-sample can change.
#
# Checks not listed here are treated as non-retryable — the conservative
# default, since spending another API call on an unknown failure mode is the
# expensive way to be wrong. Add C6/C7/C8 here once the LLM judge lands and
# their sampling behaviour is known.
RETRYABLE_CHECKS = {"C3", "C4"}


def generate_quest(conn, pipeline_result, max_attempts=2):
    """
    Generate, validate, and persist one quest from a pipeline result.

    Runs prompt → API → validate, retrying only when validation failed *and*
    every failing check is in RETRYABLE_CHECKS, up to max_attempts times. The
    prompt is unchanged between attempts — a retry is a fresh sample, not a
    repair. Only the final attempt is written to the quests table (one row per
    call), so a caller passing max_attempts=1 gets exactly the pre-refactor
    behaviour.

    Returns:
      quest_text      — text of the final attempt
      npc_id/npc_name/template — echoed from the pipeline result
      passed          — validation result of the final attempt
      attempts        — number of API calls made
      retry_reason    — final-decision summary, i.e. attempt_log[-1]["reason"]
      attempt_log     — one record per attempt: {attempt, failed, retried, reason}.
                        retry_reason alone is lossy: "attempts: 2" with reason
                        "no retry" is accurate but hides that attempt 1 failed a
                        retryable check and attempt 2 failed a blocking one.
      failed_checks   — sorted check IDs that failed on the final attempt
      validation_log  — JSON string as written to quests.validation_log
      quest_row_id    — quests.id of the written row (None if nothing was written)
      validation      — full validator.validate() result of the final attempt
      input_tokens / output_tokens — usage of the final attempt
    """
    npc_id     = pipeline_result["npc_id"]
    npc_name   = pipeline_result["npc_name"]
    template   = pipeline_result["template"]
    game_state = pipeline_result["game_state"]

    npc     = load_npc_for_prompt(conn, npc_id)
    builder = PROMPT_BUILDERS[template]
    prompt  = builder(game_state, npc)

    # Stable across attempts: callback_used is only flipped by write_quest,
    # which runs once, after the loop.
    referenced_event_id = None
    if template == "callback":
        referenced_event_id = get_referenced_choice_event_id(conn, npc_id)

    current_tick = pipe.get_current_tick(conn)

    attempts    = 0
    attempt_log = []
    while True:
        attempts += 1
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}],
        )
        quest_text = message.content[0].text
        in_tok     = message.usage.input_tokens
        out_tok    = message.usage.output_tokens

        vr = val.validate(
            conn, quest_text, npc_id, template,
            referenced_choice_id=referenced_event_id,
        )

        failed_checks = sorted({f["check"] for f in vr["failures"]})
        blocking      = [c for c in failed_checks if c not in RETRYABLE_CHECKS]

        if vr["passed"]:
            retried, reason = False, f"no retry needed — passed on attempt {attempts}"
        elif blocking:
            retried, reason = False, (
                f"no retry — {', '.join(blocking)} "
                f"cannot be fixed by re-sampling an unchanged prompt"
            )
        elif attempts >= max_attempts:
            retried, reason = False, (
                f"retry budget spent after {attempts} attempt(s) — "
                f"{', '.join(failed_checks)} still failing"
            )
        else:
            retried, reason = True, (
                f"retrying after attempt {attempts} — "
                f"{', '.join(failed_checks)} may pass on a different draft"
            )

        attempt_log.append({
            "attempt": attempts,
            "failed":  failed_checks,
            "retried": retried,
            "reason":  reason,
        })

        if not retried:
            retry_reason = reason       # final decision, summarising the trail
            break

    db_status    = "validated" if vr["passed"] else "failed_validation"
    quest_row_id = write_quest(
        conn, npc_id, template, db_status, quest_text,
        referenced_event_id, current_tick, vr["validation_log"],
    )

    return {
        "quest_text":     quest_text,
        "npc_id":         npc_id,
        "npc_name":       npc_name,
        "template":       template,
        "passed":         vr["passed"],
        "attempts":       attempts,
        "retry_reason":   retry_reason,
        "attempt_log":    attempt_log,
        "failed_checks":  failed_checks,
        "validation_log": vr["validation_log"],
        "quest_row_id":   quest_row_id,
        # Extras the CLI needs to print; safe for other callers to ignore.
        "validation":     vr,
        "input_tokens":   in_tok,
        "output_tokens":  out_tok,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    trigger_action     = "Bribed the eastern gate guard to pass through after curfew"
    player_location_id = pipe.get_player_location(conn)
    current_tick       = pipe.get_current_tick(conn)

    loc_name = conn.execute(
        "SELECT name FROM entities WHERE id = ?", (player_location_id,)
    ).fetchone()[0]

    print("=" * 62)
    print("  QUEST GENERATOR V4 — end-to-end run")
    print("=" * 62)
    print(f"  Trigger:         {trigger_action}")
    print(f"  Player location: {loc_name} (id={player_location_id})")
    print(f"  Current tick:    {current_tick}")
    print()

    # ── Step 1: Pipeline ─────────────────────────────────────────────────────

    result, status = pipe.run_pipeline(conn, trigger_action, player_location_id)

    if result is None:
        print(f"Pipeline returned None — {status}")
        conn.close()
        return

    npc_id    = result["npc_id"]
    npc_name  = result["npc_name"]
    template  = result["template"]
    score     = result["score"]
    breakdown = result["breakdown"]

    print(f"  Selected NPC:    {npc_name}")
    print(f"  Template:        {template}")
    print(f"  Score:           {score}")
    print()
    print("  Soft constraint breakdown:")
    for k, v in breakdown.items():
        print(f"    {k:<24} {v}")
    print()
    print("  All (NPC, template) scores:")
    for (n, t), d in sorted(result["all_scores"].items(), key=lambda x: -x[1]["score"]):
        print(f"    {n:<12} {t:<18} {d['score']}")
    print()

    # ── Steps 2-6: Generate, validate, write ─────────────────────────────────
    #
    # max_attempts=1 keeps the CLI on the original single-shot path — no retry
    # on validation failure, so the "recovery cascade" note below still marks
    # the R1 gap. Other callers (Godot bridge) get retries via the default.

    print("  Calling Claude Haiku...")
    gen = generate_quest(conn, result, max_attempts=1)

    quest_text = gen["quest_text"]
    in_tok     = gen["input_tokens"]
    out_tok    = gen["output_tokens"]
    vr         = gen["validation"]
    quest_id   = gen["quest_row_id"]
    db_status  = "validated" if gen["passed"] else "failed_validation"

    print(f"  Tokens: {in_tok} in / {out_tok} out")
    print()
    print("─" * 62)
    print(f"  GENERATED QUEST — {npc_name} / {template}")
    print("─" * 62)
    print(quest_text)
    print()

    # ── Step 7: Print result ─────────────────────────────────────────────────

    print("─" * 62)
    print(f"  VALIDATION — {'PASS' if vr['passed'] else 'FAIL'}")
    print("─" * 62)
    print(f"  Checks run : {', '.join(vr['checks_run'])}")

    if vr["failures"]:
        print("  Failures:")
        for f in vr["failures"]:
            print(f"    [{f['check']}] {f['reason']}")

    if vr["warnings"]:
        print("  Warnings:")
        for w in vr["warnings"]:
            print(f"    [{w['check']}] {w['reason']}")

    if vr["passed"] and not vr["warnings"]:
        print("  All checks passed.")

    if not vr["passed"]:
        print()
        print("  Recovery cascade would fire here — R1 deferred")

    print()
    print("─" * 62)
    print(f"  SUMMARY")
    print("─" * 62)
    print(f"  Quest written to DB (id={quest_id}, status='{db_status}')")
    print(f"  NPC:       {npc_name}  (id={npc_id})")
    print(f"  Template:  {template}")
    print(f"  Score:     {score}")
    print(f"  Tokens:    {in_tok} in / {out_tok} out")
    print(f"  Validated: {'yes' if vr['passed'] else 'no'}")
    if vr["warnings"]:
        print(f"  Warnings:  {len(vr['warnings'])}")
    print()

    conn.close()


if __name__ == "__main__":
    main()
