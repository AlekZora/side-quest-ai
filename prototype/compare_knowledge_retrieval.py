"""
compare_knowledge_retrieval.py — keyword vs semantic retrieval, side by side.

Runs the same (npc_id, trigger_action) through both
pipeline.build_npc_knowledge_text_keyword (LIKE match) and
pipeline.build_npc_knowledge_text (embedding similarity), and prints
both results so they can be compared directly.

Usage:
    python3 compare_knowledge_retrieval.py ["<trigger action>"] [npc_id]

Defaults to Otto (npc_id=9) and the curfew-bribe trigger if not given.
"""

import os
import sys

import psycopg
from dotenv import load_dotenv

import pipeline as pipe

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

DEFAULT_NPC_ID = 9  # Otto, from seed_db.py
DEFAULT_TRIGGER = "Bribed the eastern gate guard to pass through after curfew"


def compare(conn, npc_id, trigger_action):
    keyword  = pipe.build_npc_knowledge_text_keyword(conn, npc_id, trigger_action)
    semantic = pipe.build_npc_knowledge_text(conn, npc_id, trigger_action)

    print(f"Trigger: {trigger_action}")
    print(f"NPC id:  {npc_id}\n")
    print("─" * 62)
    print("  KEYWORD (LIKE match)")
    print("─" * 62)
    print(keyword)
    print()
    print("─" * 62)
    print("  SEMANTIC (embedding similarity)")
    print("─" * 62)
    print(semantic)


def main():
    trigger_action = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TRIGGER
    npc_id = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_NPC_ID

    conn = psycopg.connect(os.environ["DATABASE_URL"])
    compare(conn, npc_id, trigger_action)
    conn.close()


if __name__ == "__main__":
    main()
