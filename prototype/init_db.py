import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blackwater.db")

TABLES = [
    (
        "entities",
        """
        CREATE TABLE IF NOT EXISTS entities (
            id              INTEGER PRIMARY KEY,
            type            TEXT    NOT NULL CHECK(type IN ('npc','location','item','document')),
            name            TEXT    NOT NULL,
            status          TEXT    NOT NULL CHECK(status IN ('alive','dead','destroyed','missing','intact')),
            location_id     INTEGER REFERENCES entities(id),
            owner_id        INTEGER REFERENCES entities(id),
            properties      TEXT,
            created_at      INTEGER NOT NULL,
            last_changed_at INTEGER NOT NULL
        )
        """,
    ),
    (
        "events",
        """
        CREATE TABLE IF NOT EXISTS events (
            id           INTEGER PRIMARY KEY,
            type         TEXT    NOT NULL CHECK(type IN ('player_action','npc_action','world_event')),
            what         TEXT    NOT NULL,
            "when"       INTEGER NOT NULL,
            location_id  INTEGER REFERENCES entities(id),
            actor_id     INTEGER REFERENCES entities(id),
            witnesses    TEXT,
            significance TEXT    NOT NULL CHECK(significance IN ('high','medium','low')),
            consequences TEXT
        )
        """,
    ),
    (
        "relationships",
        """
        CREATE TABLE IF NOT EXISTS relationships (
            id              INTEGER PRIMARY KEY,
            from_id         INTEGER NOT NULL REFERENCES entities(id),
            to_id           INTEGER NOT NULL REFERENCES entities(id),
            type            TEXT    NOT NULL CHECK(type IN (
                                'knows','trusts','distrusts','allied','opposed',
                                'related','employed_by','owns','located_at'
                            )),
            strength        REAL    CHECK(strength IS NULL OR (strength >= -1.0 AND strength <= 1.0)),
            established_at  INTEGER REFERENCES events(id),
            last_changed_at INTEGER NOT NULL
        )
        """,
    ),
    (
        "player",
        """
        CREATE TABLE IF NOT EXISTS player (
            id                    INTEGER PRIMARY KEY,
            current_location_id   INTEGER REFERENCES entities(id),
            current_situation     TEXT,
            inventory             TEXT,
            visited_locations     TEXT,
            known_facts           TEXT,
            reputation_by_faction TEXT
        )
        """,
    ),
    (
        "player_choices",
        """
        CREATE TABLE IF NOT EXISTS player_choices (
            event_id      INTEGER NOT NULL REFERENCES events(id),
            significance  TEXT    NOT NULL CHECK(significance IN ('high','medium','low')),
            callback_used INTEGER NOT NULL DEFAULT 0 CHECK(callback_used IN (0, 1))
        )
        """,
    ),
    (
        "npc_knowledge",
        """
        CREATE TABLE IF NOT EXISTS npc_knowledge (
            id            INTEGER PRIMARY KEY,
            npc_id        INTEGER NOT NULL REFERENCES entities(id),
            event_id      INTEGER NOT NULL REFERENCES events(id),
            channel       TEXT    NOT NULL CHECK(channel IN ('witnessed','told_by','deduced','rumor')),
            source_npc_id INTEGER REFERENCES entities(id),
            confidence    REAL    NOT NULL CHECK(confidence >= 0.0 AND confidence <= 1.0),
            learned_at    INTEGER NOT NULL
        )
        """,
    ),
    (
        "npc_beliefs",
        """
        CREATE TABLE IF NOT EXISTS npc_beliefs (
            id                     INTEGER PRIMARY KEY,
            npc_id                 INTEGER NOT NULL REFERENCES entities(id),
            belief_text            TEXT    NOT NULL,
            confidence             REAL    NOT NULL CHECK(confidence >= 0.0 AND confidence <= 1.0),
            contradicting_event_id INTEGER REFERENCES events(id),
            formed_at              INTEGER NOT NULL
        )
        """,
    ),
    (
        "quests",
        """
        CREATE TABLE IF NOT EXISTS quests (
            id                  INTEGER PRIMARY KEY,
            npc_id              INTEGER NOT NULL REFERENCES entities(id),
            template_type       TEXT    NOT NULL CHECK(template_type IN (
                                    'escalation','personal_crisis','callback','world_texture'
                                )),
            status              TEXT    NOT NULL CHECK(status IN (
                                    'generated','validated','offered','accepted',
                                    'completed','declined','failed_validation'
                                )),
            generated_text      TEXT,
            referenced_event_id INTEGER REFERENCES events(id),
            created_at          INTEGER NOT NULL,
            validation_log      TEXT
        )
        """,
    ),
]


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    for name, ddl in TABLES:
        cursor.execute(ddl)
        conn.commit()
        print(f"  table '{name}' ready.")

    conn.close()
    print("Database ready.")


if __name__ == "__main__":
    print(f"Initializing {DB_PATH}")
    init_db()
