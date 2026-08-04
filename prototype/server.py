"""
server.py — FastAPI bridge between Godot and the quest pipeline.

Step 7: exposes the Python pipeline over HTTP so the game engine can
request a generated, validated quest on player interaction.

Run:
    uvicorn server:app --reload --port 8000
"""

import os
import sqlite3

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import pipeline
import quest_generator_v4 as generator

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blackwater.db")

app = FastAPI(title="Side Quest AI")

# Godot web export runs from a different origin; desktop builds don't care.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ── Contract ──────────────────────────────────────────────────────────────

class QuestRequest(BaseModel):
    player_action: str
    player_location_id: int | None = None   # falls back to the player table


class QuestResponse(BaseModel):
    ok: bool
    quest_text: str | None = None
    npc_name: str | None = None
    template: str | None = None
    validation_status: str | None = None
    attempts: int = 0
    retry_reason: str | None = None
    attempt_log: list[dict] | None = None
    error: str | None = None


# ── Routes ────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Cheap liveness check — no API call, no tokens spent."""
    conn = get_conn()
    try:
        npcs = conn.execute(
            "SELECT COUNT(*) FROM entities WHERE type = 'npc'"
        ).fetchone()[0]
        return {"ok": True, "npc_count": npcs, "tick": pipeline.get_current_tick(conn)}
    finally:
        conn.close()


@app.post("/generate-quest", response_model=QuestResponse)
def generate_quest(req: QuestRequest):
    conn = get_conn()
    try:
        location_id = req.player_location_id
        if location_id is None:
            location_id = pipeline.get_player_location(conn)
        if location_id is None:
            return QuestResponse(ok=False, error="No player location found")

        # Phase A — candidate selection + game state assembly
        result, status = pipeline.run_pipeline(conn, req.player_action, location_id)
        if result is None:
            return QuestResponse(ok=False, error=status)

        # Phase B + C — generation and validation
        # max_attempts=2: unlike the CLI, a failed request leaves a player
        # standing in front of an NPC with nothing on screen.
        gen = generator.generate_quest(conn, result, max_attempts=2)

        return QuestResponse(
            ok=True,
            quest_text=gen["quest_text"],
            npc_name=gen["npc_name"],
            template=gen["template"],
            validation_status="passed" if gen["passed"] else "failed_validation",
            attempts=gen["attempts"],
            retry_reason=gen["retry_reason"],
            attempt_log=gen["attempt_log"],
        )
    except Exception as e:
        return QuestResponse(ok=False, error=f"{type(e).__name__}: {e}")
    finally:
        conn.close()
