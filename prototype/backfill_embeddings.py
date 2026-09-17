"""
backfill_embeddings.py — generate and store embeddings for events.what.

Idempotent: only processes rows where events.embedding IS NULL, so
re-running after new events are added only embeds the new ones.
"""

import os

import openai
import psycopg
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMS  = 1536

client = openai.OpenAI()


def vector_literal(embedding):
    return "[" + ",".join(str(x) for x in embedding) + "]"


def backfill(conn):
    rows = conn.execute(
        "SELECT id, what FROM events WHERE embedding IS NULL ORDER BY id"
    ).fetchall()

    if not rows:
        print("No events need embeddings.")
        return

    print(f"Embedding {len(rows)} event(s)...")
    for event_id, what in rows:
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=what)
        embedding = response.data[0].embedding
        assert len(embedding) == EMBEDDING_DIMS, (
            f"expected {EMBEDDING_DIMS} dims, got {len(embedding)}"
        )
        conn.execute(
            "UPDATE events SET embedding = %s::vector WHERE id = %s",
            (vector_literal(embedding), event_id),
        )
        conn.commit()
        print(f"  event {event_id}: {what[:60]}...")

    print("Backfill complete.")


def main():
    # prepare_threshold=None: DATABASE_URL is a PgBouncer transaction-mode
    # pooler connection, which can hand different client sessions the same
    # backend and collide on psycopg's auto-named prepared statements.
    conn = psycopg.connect(os.environ["DATABASE_URL"], prepare_threshold=None)
    backfill(conn)
    conn.close()


if __name__ == "__main__":
    main()
