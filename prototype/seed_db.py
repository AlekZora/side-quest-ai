import json
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blackwater.db")

# Entity IDs — explicit so relationships and FK refs are readable
LOC_EASTERN_GATE        = 1
LOC_NORTHERN_DISTRICT   = 2
LOC_HOLDING_FACILITY    = 3
LOC_CLOTH_MERCHANT      = 4
LOC_REINER_ALLEY        = 5
ENT_PLAYER              = 6
ENT_SERGE               = 7
ENT_DARIA               = 8
ENT_OTTO                = 9
ENT_NADIA               = 10
ENT_MARTA               = 11   # Serge's sister — referenced in stake
ENT_MIKHAIL             = 12   # Daria's son — referenced in stake
ENT_SUPPLY_MANIFEST     = 13   # destroyed at tick 50

# Event IDs
EVT_WOMAN_AT_GATE       = 1    # tick 20 — Otto's callback target (high)
EVT_CURFEW_BRIBE        = 2    # tick 30 — medium significance
EVT_MANIFEST_BURNED     = 3    # tick 50 — high, triggers all four NPCs


def already_seeded(conn):
    return conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0] > 0


def seed_locations(conn):
    rows = [
        (LOC_EASTERN_GATE,      "location", "Eastern Gate Checkpoint",  "intact", None, None,
         json.dumps({}), 0, 0),
        (LOC_NORTHERN_DISTRICT, "location", "Northern District Office",  "intact", None, None,
         json.dumps({}), 0, 0),
        (LOC_HOLDING_FACILITY,  "location", "Holding Facility",          "intact", None, None,
         json.dumps({}), 0, 0),
        (LOC_CLOTH_MERCHANT,    "location", "Cloth Merchant District",   "intact", None, None,
         json.dumps({}), 0, 0),
        (LOC_REINER_ALLEY,      "location", "Reiner Alley",              "intact", None, None,
         json.dumps({
             "restricted": True,
             "reason": "Reclassified after checkpoint reconfiguration. Reason unknown."
         }), 0, 0),
    ]
    conn.executemany(
        "INSERT INTO entities (id, type, name, status, location_id, owner_id, properties, created_at, last_changed_at)"
        " VALUES (?,?,?,?,?,?,?,?,?)",
        rows
    )
    conn.commit()
    print("  5 locations.")


def seed_npcs(conn):
    rows = [
        # Player entity — needed so events.actor_id and relationships can FK to it
        (ENT_PLAYER, "npc", "Player", "alive", LOC_EASTERN_GATE, None,
         json.dumps({}), 0, 0),

        (ENT_SERGE, "npc", "Serge", "alive", LOC_NORTHERN_DISTRICT, None,
         json.dumps({
             "situation": (
                 "Syndicate courier. Routes sealed packets between the three district "
                 "administrative offices and the holding facility. Has done this for eleven "
                 "months — long enough to know every urgency code, every routing pattern, "
                 "and which destinations mean someone is not coming back."
             ),
             "want": (
                 "Complete his current shift without being stopped at a checkpoint. He is "
                 "carrying a packet addressed to the holding facility stamped with an urgency "
                 "code he has seen only twice before, both times before a prisoner disappeared "
                 "from the official record."
             ),
             "stake": (
                 "His sister Marta co-signed his hiring paperwork when he applied for the "
                 "courier position. She vouched for him without knowing who he had become in "
                 "the year before. If Serge is identified as a resistance contact, the "
                 "investigation works backward through his file and reaches her signature. "
                 "She would be held accountable for someone she no longer recognizes."
             ),
             "network": (
                 "Handles sealed routing packets for all three district supervisors. Knows "
                 "the timing, destination, and urgency classification of every inter-office "
                 "communication — urgency codes are stamped on the outside of each packet. "
                 "Has memorized which code combinations precede prisoner transfers versus "
                 "standard administrative actions, based on eleven months of pattern observation."
             ),
             "template_affinity": "escalation",
         }), 0, 0),

        (ENT_DARIA, "npc", "Daria", "alive", LOC_CLOTH_MERCHANT, None,
         json.dumps({
             "situation": (
                 "Runs a small alterations shop two streets from the cloth merchant's "
                 "warehouse. Has been altering Syndicate uniforms for junior officers for "
                 "three years — the only steady work she could get after her husband was "
                 "detained. She does not know if he is alive."
             ),
             "want": (
                 "Find out what happened to her husband after his initial detention. She was "
                 "told he was transferred to a labor assignment outside the district. The "
                 "officer who told her was reassigned six months later and the paperwork "
                 "trail went cold. She has been trying to find another officer who touched "
                 "his file."
             ),
             "stake": (
                 "Her son Mikhail is twelve. Three months ago he stopped asking about his "
                 "father. Last week he asked her how old you have to be to apply for Syndicate "
                 "youth enrollment. She has not answered him. If she cannot find out what "
                 "happened to her husband — if she cannot give Mikhail a true account of who "
                 "his father was and what was done to him — she will watch her son become the "
                 "kind of person who took him."
             ),
             "network": (
                 "Alters uniforms for approximately twenty Syndicate junior officers on a "
                 "rotating basis. Knows which officers are newly transferred into the district "
                 "(new uniform adjustments), which are being promoted (rank insignia changes), "
                 "and which have recently attended disciplinary hearings (dress uniform "
                 "alterations ordered on short notice, paid in cash). Has seen three years "
                 "of officer rotation patterns."
             ),
             "template_affinity": "personal_crisis",
         }), 0, 0),

        (ENT_OTTO, "npc", "Otto", "alive", LOC_EASTERN_GATE, None,
         json.dumps({
             "situation": (
                 "Runs the eastern gate checkpoint's unofficial holding room — a converted "
                 "storage space where people flagged at the gate wait while their papers are "
                 "reviewed. He is not Syndicate; he is contracted. He sees everyone who gets "
                 "stopped, everyone who gets waved through, and everyone who pays to avoid both."
             ),
             "want": (
                 "Get his contract renewed for another six months. His supervisor has told him "
                 "the renewal depends on flagging more resistance contacts — the quota has "
                 "increased and he is behind. He does not want to flag anyone. He is trying "
                 "to find another way to satisfy the number."
             ),
             "stake": (
                 "His wife runs a small food stall inside the gate. The stall license is "
                 "attached to his contract — if his contract ends, the license ends with it. "
                 "She built the stall over four years. He has not told her the renewal is in "
                 "question because he does not know how to explain that he is the reason it "
                 "might not happen."
             ),
             "network": (
                 "Sees every person who passes through the eastern gate checkpoint — who gets "
                 "stopped, who gets waved through, who pays the guard directly, and who is "
                 "carrying something they would prefer not to have inspected. Has two years of "
                 "observational records kept in a personal ledger he has never shown anyone."
             ),
             "template_affinity": "callback",
         }), 0, 0),

        (ENT_NADIA, "npc", "Nadia", "alive", LOC_CLOTH_MERCHANT, None,
         json.dumps({
             "situation": (
                 "Cartographer on commission from the eastern merchant guild. She has been "
                 "hired to update the district map after the recent guard checkpoint "
                 "reconfiguration — new routes, new restricted zones, new administrative "
                 "boundaries. She is three weeks into a six-week commission and one street "
                 "short of completing the eastern section."
             ),
             "want": (
                 "Walk down Reiner Alley with her instruments and finish the survey. The alley "
                 "was reclassified as restricted after the reconfiguration. She does not know "
                 "why. She has been turned away at the entry checkpoint twice. She needs either "
                 "access or someone who can tell her what changed."
             ),
             "stake": (
                 "Her apprenticeship with the guild ends in eight weeks. The commission was "
                 "supposed to be her exit credential — proof of completed work for the guild "
                 "master's reference letter. He is the only person in the city qualified to "
                 "vouch for her cartography, because her previous mentor died before her "
                 "apprenticeship concluded. She has not told the guild master that she cannot "
                 "complete the commission. She goes back to the alley checkpoint every other "
                 "day because she does not know what else to do."
             ),
             "network": (
                 "Has mapped seven of the nine eastern district sections over three weeks — "
                 "knows the current layout of every public street, courtyard, and passage in "
                 "the district except the restricted alley. Has spoken with checkpoint guards, "
                 "shop owners, and market stall operators while surveying. Knows which streets "
                 "have changed since the last official map."
             ),
             "template_affinity": "world_texture",
         }), 0, 0),

        # Supporting NPCs: referenced in stakes but not quest givers
        (ENT_MARTA, "npc", "Marta", "alive", LOC_NORTHERN_DISTRICT, None,
         json.dumps({
             "note": "Serge's sister. Co-signed his Syndicate courier application paperwork."
         }), 0, 0),

        (ENT_MIKHAIL, "npc", "Mikhail", "alive", LOC_CLOTH_MERCHANT, None,
         json.dumps({
             "note": "Daria's son, age 12. Recently expressed interest in Syndicate youth enrollment."
         }), 0, 0),
    ]
    conn.executemany(
        "INSERT INTO entities (id, type, name, status, location_id, owner_id, properties, created_at, last_changed_at)"
        " VALUES (?,?,?,?,?,?,?,?,?)",
        rows
    )

    # Document: supply manifest — already destroyed when seed runs
    conn.execute(
        "INSERT INTO entities (id, type, name, status, location_id, owner_id, properties, created_at, last_changed_at)"
        " VALUES (?,?,?,?,?,?,?,?,?)",
        (ENT_SUPPLY_MANIFEST, "document", "Syndicate Supply Manifest", "destroyed",
         LOC_NORTHERN_DISTRICT, None,
         json.dumps({"note": "District supply manifest. Burned by player at tick 50."}),
         0, 50)
    )
    conn.commit()
    print("  8 NPCs + 1 document.")


def seed_player(conn):
    conn.execute(
        "INSERT INTO player (id, current_location_id, current_situation, inventory,"
        " visited_locations, known_facts, reputation_by_faction) VALUES (?,?,?,?,?,?,?)",
        (
            1,
            LOC_EASTERN_GATE,
            "Known to have destroyed a Syndicate supply manifest this morning. District is on heightened alert.",
            json.dumps([]),
            json.dumps([LOC_EASTERN_GATE, LOC_NORTHERN_DISTRICT]),
            json.dumps([EVT_MANIFEST_BURNED]),
            json.dumps({"Syndicate": -0.6, "Resistance": 0.4}),
        )
    )
    conn.commit()
    print("  1 player row.")


def seed_events(conn):
    rows = [
        (
            EVT_WOMAN_AT_GATE, "player_action",
            "Let a detained woman go at the eastern gate without collecting the standard"
            " release fee, telling the guard she had already paid",
            20,                             # tick — three weeks ago
            LOC_EASTERN_GATE,
            ENT_PLAYER,
            json.dumps([ENT_OTTO]),         # Otto was in the holding room
            "high",
            json.dumps([]),
        ),
        (
            EVT_CURFEW_BRIBE, "player_action",
            "Bribed the eastern gate guard to pass through after curfew",
            30,                             # tick — two weeks ago
            LOC_EASTERN_GATE,
            ENT_PLAYER,
            json.dumps([ENT_OTTO]),         # Otto logged it
            "medium",
            json.dumps([]),
        ),
        (
            EVT_MANIFEST_BURNED, "player_action",
            "Burned the Syndicate's supply manifest rather than handing it to the resistance",
            50,                             # tick — this morning
            LOC_NORTHERN_DISTRICT,
            ENT_PLAYER,
            json.dumps([]),                 # no direct witnesses; spread through channels
            "high",
            json.dumps([]),
        ),
    ]
    conn.executemany(
        'INSERT INTO events (id, type, what, "when", location_id, actor_id, witnesses, significance, consequences)'
        " VALUES (?,?,?,?,?,?,?,?,?)",
        rows
    )
    conn.commit()
    print("  3 events.")


def seed_player_choices(conn):
    rows = [
        (EVT_WOMAN_AT_GATE,    "high",   0),  # primary callback target for Otto
        (EVT_CURFEW_BRIBE,     "medium", 0),
        (EVT_MANIFEST_BURNED,  "high",   0),
    ]
    conn.executemany(
        "INSERT INTO player_choices (event_id, significance, callback_used) VALUES (?,?,?)",
        rows
    )
    conn.commit()
    print("  3 player_choices.")


def seed_npc_knowledge(conn):
    # (npc_id, event_id, channel, source_npc_id, confidence, learned_at)
    rows = [
        # Otto witnessed both gate events directly; heard of manifest via supervisor
        (ENT_OTTO,  EVT_WOMAN_AT_GATE,   "witnessed", None, 1.0, 20),
        (ENT_OTTO,  EVT_CURFEW_BRIBE,    "witnessed", None, 1.0, 30),
        (ENT_OTTO,  EVT_MANIFEST_BURNED, "told_by",   None, 0.8, 50),
        # Serge: supervisor told him the manifest burning triggered the urgency code
        (ENT_SERGE, EVT_MANIFEST_BURNED, "told_by",   None, 0.8, 50),
        # Daria: regular officer mentioned it while picking up a uniform
        (ENT_DARIA, EVT_MANIFEST_BURNED, "told_by",   None, 0.8, 50),
        # Nadia: overheard two guards at the warehouse checkpoint
        (ENT_NADIA, EVT_MANIFEST_BURNED, "rumor",     None, 0.4, 50),
    ]
    conn.executemany(
        "INSERT INTO npc_knowledge (npc_id, event_id, channel, source_npc_id, confidence, learned_at)"
        " VALUES (?,?,?,?,?,?)",
        rows
    )
    conn.commit()
    print("  6 npc_knowledge rows.")


def seed_relationships(conn):
    # (from_id, to_id, type, strength, established_at, last_changed_at)
    rows = [
        # NPC → player: trust levels based on witnessed events
        (ENT_OTTO,  ENT_PLAYER, "trusts",     0.5,  EVT_WOMAN_AT_GATE,   20),  # trust formed at woman-at-gate
        (ENT_SERGE, ENT_PLAYER, "knows",      0.2,  EVT_MANIFEST_BURNED, 50),  # worked out the timing
        (ENT_DARIA, ENT_PLAYER, "knows",      0.1,  EVT_MANIFEST_BURNED, 50),  # heard from officer
        (ENT_NADIA, ENT_PLAYER, "knows",      0.1,  EVT_MANIFEST_BURNED, 50),  # overheard guards

        # Stake relationships — the things each NPC stands to lose
        (ENT_SERGE, ENT_MARTA,   "related",   0.9,  None, 0),  # Serge → sister Marta
        (ENT_DARIA, ENT_MIKHAIL, "related",   1.0,  None, 0),  # Daria → son Mikhail

        # NPC home locations
        (ENT_OTTO,  LOC_EASTERN_GATE,      "located_at", None, None, 0),
        (ENT_SERGE, LOC_NORTHERN_DISTRICT, "located_at", None, None, 0),
        (ENT_DARIA, LOC_CLOTH_MERCHANT,    "located_at", None, None, 0),
        (ENT_NADIA, LOC_CLOTH_MERCHANT,    "located_at", None, None, 0),

        # Nadia's blocker: she knows Reiner Alley but cannot access it
        (ENT_NADIA, LOC_REINER_ALLEY, "knows", None, None, 0),
    ]
    conn.executemany(
        "INSERT INTO relationships (from_id, to_id, type, strength, established_at, last_changed_at)"
        " VALUES (?,?,?,?,?,?)",
        rows
    )
    conn.commit()
    print("  11 relationships.")


def print_counts(conn):
    tables = [
        "entities", "events", "relationships", "player",
        "player_choices", "npc_knowledge", "npc_beliefs", "quests",
    ]
    print("\nRow counts:")
    for t in tables:
        n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t:<22} {n}")


def main():
    print(f"Seeding {DB_PATH}\n")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    if already_seeded(conn):
        print("Database already seeded. Delete blackwater.db and re-run init_db.py to start fresh.")
        print_counts(conn)
        conn.close()
        return

    seed_locations(conn)
    seed_npcs(conn)
    seed_player(conn)
    seed_events(conn)
    seed_player_choices(conn)
    seed_npc_knowledge(conn)
    seed_relationships(conn)
    print_counts(conn)
    conn.close()
    print("\nSeed complete.")


if __name__ == "__main__":
    main()
