import os

import psycopg
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")

TABLE_NAMES = [
    "entities", "events", "relationships", "player",
    "player_choices", "npc_knowledge", "npc_beliefs", "quests",
]


def init_db():
    conn = psycopg.connect(os.environ["DATABASE_URL"])
    with open(SCHEMA_PATH) as f:
        conn.execute(f.read())
    conn.commit()
    for name in TABLE_NAMES:
        print(f"  table '{name}' ready.")
    conn.close()
    print("Database ready.")


if __name__ == "__main__":
    print(f"Initializing schema from {SCHEMA_PATH}")
    init_db()
