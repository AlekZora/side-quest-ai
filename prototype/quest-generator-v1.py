import anthropic
import json

with open("test-states.json") as f:
    states = json.load(f)

client = anthropic.Anthropic()

for i, game_state in enumerate(states, 1):
    prompt = f"""You are a quest designer for a narrative RPG.

Here is the current game state:
{json.dumps(game_state, indent=2)}

Generate a contextual side quest where {game_state['npc_name']} approaches the player.
Include exactly these five things:

1. WHY she is approaching the player right now (connect it to what the player just did)
2. WHAT she needs from the player
3. WHAT it costs the player to help her
4. WHAT she offers in return
5. ONE piece of information she reveals that connects to the main quest

Keep it grounded and specific. This quest should only make sense for a player who took this exact action."""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    print(f"=== STATE {i} / {len(states)}: {game_state['last_player_action']} ===\n")
    print(message.content[0].text)
    print(f"\n=== STATS ===")
    print(f"Tokens used: {message.usage.input_tokens} in / {message.usage.output_tokens} out")
    print()
