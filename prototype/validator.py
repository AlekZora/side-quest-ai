"""
validator.py — Phase C post-generation hard constraint checks (V1)
Implements C1, C3, C4, C5 from fact-database-design.md (rule-based only).
C6 (knowledge check), C7 (reward feasibility), C8 (narrative integrity)
are deferred to V2 and require an LLM judge.
"""

import json
import os
import re

PLAYER_ENTITY_ID = 6

# Words / partial-sequences that should NOT trigger C3 hallucination warnings.
# Covers game-world factions and abstract nouns that appear capitalised but are
# not tracked as entities in V1, common titles, and directional words.
# Uses "all words in the sequence must be safe to suppress" logic — a sequence
# like "Inspector Voss" is NOT suppressed because "Voss" is not safe.
SAFE_WORDS = {
    # Articles (appear Title-Case at sentence start or in multi-word sequences)
    "the", "a", "an",
    # Game-world factions and concepts not tracked as V1 entities
    "syndicate", "resistance", "administration", "guild",
    "elena",          # main quest subject — not a DB entity in V1
    # Directional / geographic qualifiers
    "outer", "inner", "eastern", "western", "northern", "southern", "central",
    # Roles and titles (appear before NPC names; the name itself still matters)
    "officer", "supervisor", "guard", "captain", "lieutenant",
    "inspector", "commissioner", "sergeant", "constable", "clerk",
    # Common world-building nouns that appear Title-Case in context
    "city", "district", "sector", "quarter", "holding", "facility",
    "gate", "checkpoint", "alley", "warehouse", "market", "stall",
    # Template section headers (numbered items begin with these)
    "why", "what", "how", "changes", "resolved", "recognition",
    "line", "unresolved", "stays", "cost", "costs", "emotional",
}

# ── C1: Structural parse ──────────────────────────────────────────────────

# Human-readable label for each numbered item per template,
# used to name missing items in failure messages.
ITEM_LABELS = {
    "escalation":      {1: "WHY",  2: "WHAT (task)",     3: "WHAT (costs)",
                        4: "WHAT (reveals)",              5: "WHAT CHANGES"},
    "personal_crisis": {1: "WHY",  2: "WHAT (crisis)",   3: "WHAT (needs)",
                        4: "WHAT (costs)",                5: "WHAT (emotional weight)"},
    "callback":        {1: "WHY",  2: "WHAT (observed)", 3: "WHAT (needs)",
                        4: "WHAT (costs)",                5: "RECOGNITION LINE"},
    "world_texture":   {1: "HOW",  2: "WHAT (situation)",3: "WHAT (needs)",
                        4: "WHAT (costs)",                5: "WHAT STAYS UNRESOLVED"},
}


def check_c1(quest_text, template_type):
    """
    Verify the quest output contains all 5 numbered items.
    Looks for '1.' through '5.' at the start of a line, allowing any
    combination of the markers Haiku actually emits around the number:
      1. WHY          ## 1. WHY        **1. WHY**
        1. WHY        ### **1.** WHY   ## **1.** WHY
    i.e. optional indent, optional ATX heading (# to ######), optional
    asterisks before and after the number.
    Returns (passed, reason).
    """
    labels  = ITEM_LABELS.get(template_type, {})
    missing = []
    for i in range(1, 6):
        if not re.search(rf'(?m)^[ \t]*(?:#{{1,6}}[ \t]*)?\**[ \t]*{i}\.\**(?:\s|$)',
                         quest_text):
            label = labels.get(i, str(i))
            missing.append(f"{i} ({label})")
    if missing:
        return False, f"structural_fault: missing item(s) — {', '.join(missing)}"
    return True, "ok"


# ── C3: Existence check ───────────────────────────────────────────────────

def get_entity_index(conn):
    """Return {name_lower: {id, name, status}} for all entities."""
    rows = conn.execute("SELECT id, name, status FROM entities").fetchall()
    return {r[1].lower(): {"id": r[0], "name": r[1], "status": r[2]} for r in rows}


def lookup_entity(entity_index, noun):
    """
    Look up a proper-noun sequence in the entity index.
    Tries the noun as-is, then strips a leading article ('the', 'a', 'an')
    and tries again — handles 'The Syndicate Supply Manifest' → 'Syndicate Supply Manifest'.
    Returns the entity dict or None.
    """
    key = noun.lower()
    if key in entity_index:
        return entity_index[key]
    stripped = re.sub(r'^(?:the|a|an)\s+', '', key).strip()
    if stripped != key and stripped in entity_index:
        return entity_index[stripped]
    return None


# ATX markdown headings ("## 2. WHAT Otto Witnessed"). Header text is template
# scaffolding — it restates the prompt's own section labels — so the Title-Case
# words in it are not claims about the world and should not be entity candidates.
ATX_HEADING_RE = re.compile(r'(?m)^[ \t]*#{1,6}.*$')


def extract_proper_nouns(quest_text):
    """
    Extract Title-Case word sequences as candidates for entity references.
    Matches one or more consecutive words each starting with an uppercase letter
    followed by lowercase letters (min length 2 per word).

    ATX heading lines are blanked before matching (see ATX_HEADING_RE). Note
    this applies to every caller, C4 included: an entity named ONLY inside a
    heading is no longer state-checked either. Pass the raw text if a caller
    ever needs headings back.

    Words are joined with [ \\t]+ rather than \\s+ on purpose: \\s matches
    newlines, which glued the last word of a heading to the first word of the
    next paragraph ("Otto Needs\\n\\nOtto"). Those sequences can never resolve
    against the entity table, so they flagged as hallucinations on every run.

    Known limitation (per design doc §C2): over-matches sentence-start words
    (partly mitigated by SENTENCE_OPENERS below), under-matches lowercase
    entity references like 'the manifest'.
    V2 replaces this with a trained NER model.
    """
    body = ATX_HEADING_RE.sub("", quest_text)   # blank the line, keep line structure
    return set(re.findall(r'\b[A-Z][a-z]{1,}(?:[ \t]+[A-Z][a-z]{1,})*\b', body))


# Words that commonly open a sentence and get swept into the following
# capitalised word ("But Elena", "If Elena"). When a sequence starts with one,
# the opener is stripped and the remainder re-tested — so "But Elena" resolves
# to Elena, while "The Vaskov Ledger" still flags as "Vaskov Ledger".
# Heuristic only: a real fix needs the trained NER model queued for C3 in V2.
SENTENCE_OPENERS = {
    "but", "if", "once", "when", "and", "the", "this", "that",
    "after", "before", "now", "so", "then", "yet",
}


def strip_sentence_opener(noun):
    """
    If a multi-word sequence starts with a common sentence-opening word,
    return the sequence without it. Returns None when there is nothing to
    strip. Single pass — 'But The Manifest' yields 'The Manifest', and
    lookup_entity's own article stripping takes it from there.
    """
    words = noun.split()
    if len(words) > 1 and words[0].lower() in SENTENCE_OPENERS:
        return " ".join(words[1:])
    return None


def is_safe_sequence(noun, entity_index=None):
    """
    True if every word in the sequence is safe — either a known-safe word from
    SAFE_WORDS, or a word that resolves to an entity in the index. The second
    rule is what lets "What Otto" through: 'what' is scaffolding and 'Otto' is
    a real NPC, so the pair asserts nothing unverified.

    entity_index is optional so existing callers keep working; without it the
    check falls back to SAFE_WORDS alone.
    """
    index = entity_index or {}
    return all(w.lower() in SAFE_WORDS or w.lower() in index for w in noun.split())


def check_c3(conn, quest_text):
    """
    C3: existence check.
    For each proper-noun sequence extracted from the quest text:
      1. If it resolves to a known entity (via lookup_entity): existence confirmed, skip.
      2. If all words are safe (articles, world-building terms): skip.
      3. If it is a single unknown word: skip — sentence-start words and gerunds
         produce too many false positives for single-word detection in V1.
         (V2 replaces this with a trained NER model.)
      4. If it starts with a sentence-opening word, strip it and re-run 1-3 on
         the remainder: "But Elena" is Elena, not an unknown entity.
      5. Multi-word unknown sequence not covered above: flag as potential
         hallucination. Where an opener was stripped, the remainder is what
         gets reported — that is the part that failed to resolve.
    Returns (passed, issues_list).
    """
    entity_index   = get_entity_index(conn)
    proper_nouns   = extract_proper_nouns(quest_text)
    hallucinations = []

    def unresolved(seq):
        """True if seq is a multi-word sequence that resolves to nothing known."""
        if lookup_entity(entity_index, seq) is not None:
            return False                     # known entity — existence confirmed
        if is_safe_sequence(seq, entity_index):
            return False                     # every word is scaffolding or a known entity
        if len(seq.split()) == 1:
            return False                     # single-word: too noisy in V1
        return True

    for noun in proper_nouns:
        if not unresolved(noun):
            continue

        # Sentence opener swept into the following capitalised word.
        remainder = strip_sentence_opener(noun)
        if remainder is not None:
            if unresolved(remainder):
                hallucinations.append(remainder)
            continue

        hallucinations.append(noun)          # multi-word unknown: potential hallucination

    issues = []
    if hallucinations:
        issues.append(
            f"potential hallucinated entities (not in DB): "
            f"{', '.join(sorted(hallucinations))}"
        )
    return len(issues) == 0, issues


# ── C4: State check ───────────────────────────────────────────────────────

def check_c4(conn, quest_text, npc_id):
    """
    C4: state check (hard failures) + deadline detection (warnings).
    Hard failures:
      - Quest giver must be alive.
      - Any known entity referenced in the text must not be dead or destroyed.
    Warnings (non-blocking):
      - Temporal deadline phrases detected; comparison to current tick
        requires in-game clock (deferred to Godot integration).
    Returns (passed, hard_issues, warnings).
    """
    hard_issues = []
    warnings    = []

    # Quest giver alive
    row = conn.execute(
        "SELECT name, status FROM entities WHERE id = %s", (npc_id,)
    ).fetchone()
    if not row:
        hard_issues.append(f"quest giver entity id={npc_id} not found in entities")
    elif row[1] != "alive":
        hard_issues.append(
            f"quest giver '{row[0]}' is not alive (status='{row[1]}')"
        )

    # Referenced known entities must not be dead or destroyed.
    # No safe-sequence filter: lookup_entity handles article stripping and we
    # want to catch every known entity regardless of whether its words are "safe".
    entity_index = get_entity_index(conn)
    seen = set()
    for noun in extract_proper_nouns(quest_text):
        entity = lookup_entity(entity_index, noun)
        if entity and entity["id"] not in seen:
            seen.add(entity["id"])
            if entity["status"] in ("dead", "destroyed"):
                hard_issues.append(
                    f"referenced entity '{entity['name']}' has "
                    f"status='{entity['status']}' at quest generation time"
                )

    # Deadline heuristic — flag but do not hard-fail in V1
    DEADLINE_RE = re.compile(
        r'\b(?:by|before)\s+(?:end of (?:shift|day)|tonight|tomorrow|morning|dawn|midnight)\b',
        re.IGNORECASE,
    )
    for m in DEADLINE_RE.finditer(quest_text):
        warnings.append(
            f"deadline phrase detected (tick comparison deferred): '{m.group(0)}'"
        )

    passed = len(hard_issues) == 0
    return passed, hard_issues, warnings


# ── C5: Causal check ─────────────────────────────────────────────────────

def check_c5(conn, template_type, referenced_choice_id):
    """
    C5: causal check.
    For callback template: verify referenced_choice_id is in player_choices
    with callback_used=0.
    General past-event text extraction (C5 §2) deferred to V2 (requires NER).
    Returns (passed, issues_list).
    """
    issues = []

    if template_type == "callback":
        if referenced_choice_id is None:
            issues.append(
                "callback template requires a referenced_choice_id but none provided"
            )
        else:
            row = conn.execute(
                "SELECT callback_used FROM player_choices WHERE event_id = %s",
                (referenced_choice_id,),
            ).fetchone()
            if not row:
                issues.append(
                    f"referenced_choice event_id={referenced_choice_id} "
                    f"not found in player_choices"
                )
            elif row[0] == 1:
                issues.append(
                    f"referenced_choice event_id={referenced_choice_id} "
                    f"already used as a callback (callback_used=1)"
                )

    return len(issues) == 0, issues


# ── Main validator ────────────────────────────────────────────────────────

def validate(conn, quest_text, npc_id, template_type, referenced_choice_id=None):
    """
    Run all V1 checks against a generated quest text.
    Returns a result dict suitable for logging to the quests table.

    Fields:
      passed          — True only if all hard-constraint checks pass
      checks_run      — list of check IDs executed
      failures        — list of {check, reason} for hard failures
      warnings        — list of {check, reason} for soft issues
      validation_log  — JSON string for quests.validation_log column
    """
    checks_run = []
    failures   = []
    warnings   = []
    detail     = {}

    # C1 — structural parse
    checks_run.append("C1")
    ok, reason = check_c1(quest_text, template_type)
    detail["C1"] = {"passed": ok, "detail": reason}
    if not ok:
        failures.append({"check": "C1", "reason": reason})

    # C3 — existence check
    checks_run.append("C3")
    ok, issues = check_c3(conn, quest_text)
    detail["C3"] = {"passed": ok, "detail": issues}
    for issue in issues:
        failures.append({"check": "C3", "reason": issue})

    # C4 — state check
    checks_run.append("C4")
    ok, hard_issues, soft_warnings = check_c4(conn, quest_text, npc_id)
    detail["C4"] = {"passed": ok, "hard": hard_issues, "warnings": soft_warnings}
    for issue in hard_issues:
        failures.append({"check": "C4", "reason": issue})
    for w in soft_warnings:
        warnings.append({"check": "C4", "reason": w})

    # C5 — causal check
    checks_run.append("C5")
    ok, issues = check_c5(conn, template_type, referenced_choice_id)
    detail["C5"] = {"passed": ok, "detail": issues}
    for issue in issues:
        failures.append({"check": "C5", "reason": issue})

    passed = len(failures) == 0
    validation_log = json.dumps({
        "checks_run": checks_run,
        "detail":     detail,
        "failures":   failures,
        "warnings":   warnings,
        "deferred":   ["C6 (knowledge check)", "C7 (reward feasibility)",
                       "C8 (narrative integrity)"],
    }, indent=2)

    return {
        "passed":          passed,
        "checks_run":      checks_run,
        "failures":        failures,
        "warnings":        warnings,
        "validation_log":  validation_log,
    }


# ── Test ──────────────────────────────────────────────────────────────────
#
# Quest text approximates what quest-generator-v3.py produces for an Otto /
# escalation run. The Step 5 test used Otto for callback; this escalation text
# is modelled on the Serge escalation output from the same session (build-log
# entry 2026-06-09: "Serge reveals Elena is being traded to the Outer City
# administration"). Otto's network is his gate ledger, so the revelation here
# comes from gate passage records — grounded in Otto's actual access.

OTTO_ESCALATION_QUEST = """
**1. WHY OTTO IS APPROACHING THE PLAYER NOW**

The Syndicate supervisor came to the Eastern Gate Checkpoint this morning to review Otto's flagging quota and mentioned someone had destroyed a supply manifest — the first time Otto has heard the player described in an official context. In two years of watching people move through the gate, Otto has learned one thing: when a record gets destroyed, someone is about to be moved before the next record can be made. The player just burned the manifest. The next transfer out of the district is scheduled before end of shift. Otto has the passenger list in his ledger.

**2. WHAT OTTO NEEDS FROM THE PLAYER**

Otto needs the player to intercept a sealed packet addressed to the Northern District Office before it is logged at the checkpoint desk. The packet contains a transfer authorisation. If it is logged, the transfer becomes an official record the player cannot interfere with. If it disappears before logging, the transfer has no paper trail — and Otto gains leverage with his supervisor by reporting the packet as stolen by the same person who burned the manifest, satisfying his quota without identifying anyone.

**3. WHAT IT COSTS THE PLAYER**

The packet is currently in transit through the checkpoint. Intercepting it means entering the holding area before Otto can clear it — which means being inside the checkpoint during active lockdown hours with no legitimate papers. Anyone caught inside the holding area during lockdown is automatically detained for questioning. The player would be in the exact location the supervisor is searching for the manifest thief.

**4. WHAT OTTO REVEALS**

The transfer authorisation in the packet is not for an unnamed detainee. The destination is not the Holding Facility. The routing code on the packet matches the code Otto has seen twice before — both times before a prisoner was transferred to Outer City administration custody and never re-entered his gate records. Elena is already out of Syndicate hands. The resistance is planning a rescue from a facility that no longer holds her.

**5. WHAT CHANGES**

The mission to rescue Elena from the Syndicate holding facility was already obsolete before the manifest was burned — she is in Outer City custody, and the Syndicate's record destruction is not concealment of her location but concealment of the transfer handoff itself.
"""

# Variant with a hallucinated entity not in the DB.
# Inserts after a sentence that is definitely in the clean text.
OTTO_ESCALATION_HALLUCINATED = OTTO_ESCALATION_QUEST.replace(
    "The packet is currently in transit through the checkpoint.",
    "The packet is currently in transit through the checkpoint. Clerk Vaskov is holding it at the desk.",
)

# Variant with a destroyed entity referenced as active
OTTO_ESCALATION_DESTROYED = OTTO_ESCALATION_QUEST.replace(
    "someone had destroyed a supply manifest",
    "the Syndicate Supply Manifest had been destroyed"
).replace(
    "The packet contains a transfer authorisation.",
    "The Syndicate Supply Manifest was last seen at the checkpoint. The packet contains a transfer authorisation."
)

# Variant missing item 5
OTTO_ESCALATION_MISSING_5 = re.sub(
    r'\*\*5\..*',
    '',
    OTTO_ESCALATION_QUEST,
    flags=re.DOTALL,
)


def print_result(label, result):
    status = "PASS" if result["passed"] else "FAIL"
    print(f"\n{'─' * 56}")
    print(f"  {label}  [{status}]")
    print(f"{'─' * 56}")
    print(f"  Checks run : {', '.join(result['checks_run'])}")
    if result["failures"]:
        print("  Failures:")
        for f in result["failures"]:
            print(f"    [{f['check']}] {f['reason']}")
    if result["warnings"]:
        print("  Warnings:")
        for w in result["warnings"]:
            print(f"    [{w['check']}] {w['reason']}")
    if result["passed"] and not result["warnings"]:
        print("  All checks passed.")


if __name__ == "__main__":
    import psycopg
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
    conn = psycopg.connect(os.environ["DATABASE_URL"])

    ENT_OTTO = 9  # entity id from seed_db.py

    print("=== Validator test — Otto / escalation ===")

    # Test 1: clean quest — should pass all checks
    r = validate(conn, OTTO_ESCALATION_QUEST, ENT_OTTO, "escalation")
    print_result("Test 1: clean quest (expect PASS)", r)

    # Test 2: missing item 5 — should fail C1
    r = validate(conn, OTTO_ESCALATION_MISSING_5, ENT_OTTO, "escalation")
    print_result("Test 2: missing item 5 (expect C1 FAIL)", r)

    # Test 3: hallucinated entity 'Vaskov' — should fail C3
    r = validate(conn, OTTO_ESCALATION_HALLUCINATED, ENT_OTTO, "escalation")
    print_result("Test 3: hallucinated entity 'Vaskov' (expect C3 FAIL)", r)

    # Test 4: destroyed entity referenced — should fail C4
    r = validate(conn, OTTO_ESCALATION_DESTROYED, ENT_OTTO, "escalation")
    print_result("Test 4: destroyed entity referenced (expect C4 FAIL)", r)

    # Test 5: callback with valid referenced_choice_id — should pass C5
    r = validate(conn, OTTO_ESCALATION_QUEST, ENT_OTTO, "callback",
                 referenced_choice_id=1)  # EVT_WOMAN_AT_GATE, callback_used=0
    print_result("Test 5: callback with valid choice id=1 (expect PASS)", r)

    # Test 6: callback with already-used choice — should fail C5
    # Temporarily mark event 1 as used, test, then restore
    conn.execute("UPDATE player_choices SET callback_used=1 WHERE event_id=1")
    r = validate(conn, OTTO_ESCALATION_QUEST, ENT_OTTO, "callback",
                 referenced_choice_id=1)
    print_result("Test 6: callback with used choice (expect C5 FAIL)", r)
    conn.execute("UPDATE player_choices SET callback_used=0 WHERE event_id=1")
    conn.commit()

    print()
    conn.close()
