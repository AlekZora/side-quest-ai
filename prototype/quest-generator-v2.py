import anthropic
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

with open(SCRIPT_DIR / "../test-npcs.json") as f:
    npc_index = {npc["name"]: npc for npc in json.load(f)}

# Combined test: game state + NPC definition
# Game state provides the dynamic runtime context (what happened, what the NPC
# knows about it). NPC definition provides the static authored context (who
# they are, what they want, what they stand to lose, who they know).
game_state = {
    "main_quest": "Rescue Elena from the Syndicate",
    "player_action": "Burned the Syndicate's supply manifest rather than handing it to the resistance",
    "npc_name": "Rook",
    "npc_situation": "The Syndicate summoned him the morning after the manifest was burned and ordered him to provide vault access to three eastern merchants by tomorrow night — to reconstruct supply records from their private ledgers",
    "npc_knowledge": "The district supervisor told him directly that a saboteur destroyed the manifest and that Rook would be compensated for fast cooperation — and quietly blamed if the records could not be reconstructed in time"
}

npc = npc_index[game_state["npc_name"]]

client = anthropic.Anthropic()

prompt = f"""You are a quest designer for a narrative RPG.

GAME STATE:
  Main quest: {game_state["main_quest"]}
  Player's last action: {game_state["player_action"]}
  Current situation: {game_state["npc_situation"]}
  How {npc["name"]} learned of the player's action: {game_state["npc_knowledge"]}

NPC — {npc["name"]}:
  Who they are: {npc["situation"]}
  What they want: {npc["want"]}
  What they stand to lose: {npc["stake"]}
  Who they know / what they have access to: {npc["network"]}

Generate a contextual side quest where {npc["name"]} approaches the player.
Include exactly these five things:

1. WHY {npc["name"]} is approaching the player right now — connect the player's action to {npc["name"]}'s current situation
2. WHAT {npc["name"]} needs from the player
3. WHAT it costs the player to help
4. WHAT {npc["name"]} offers in return — must come from their actual network access, not invented resources
5. ONE piece of information {npc["name"]} reveals that connects to the main quest

Keep it grounded and specific. {npc["name"]}'s ask must reflect both their want and their stake.
This quest should only make sense for a player who burned that manifest."""

message = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=600,
    messages=[
        {"role": "user", "content": prompt}
    ]
)

print(f"=== V2: COMBINED GAME STATE + NPC SCHEMA ===")
print(f"Player action : {game_state['player_action']}")
print(f"NPC           : {npc['name']}")
print()
print(message.content[0].text)
print()
print(f"=== STATS ===")
print(f"Tokens: {message.usage.input_tokens} in / {message.usage.output_tokens} out")
