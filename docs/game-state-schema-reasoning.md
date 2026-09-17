# Game State Schema — Reasoning

Derived from test-states.json v1 (5 validated states) and 
quest-generator-v1.py. This document explains why each 
field is necessary, what would break without it, and 
whether 5 is the right number.

---

## The 5 fields and what they each do

### 1. `main_quest`
**Contains:** The player's primary story objective for the 
current act. Human-authored, fixed.

**Why necessary:** The quest generator needs a story anchor 
to place the NPC inside a larger narrative. Without it, 
the NPC's intel reward — "one piece of information 
connecting to the main quest" — has nothing to connect to. 
The field also acts as a soft constraint: it tells the 
generator what the NPC is allowed to know about (Syndicate 
operations, not the king's tax records). Every test state 
shared the same main_quest value, which is correct — the 
NPC's personal crisis runs parallel to the main story, 
not instead of it.

**Example:** `"Rescue Elena from the Syndicate"`

---

### 2. `player_action`
**Contains:** The specific action the player took most 
recently that has reached this NPC's awareness.

**Why necessary:** This is the triggering event — the 
reason this NPC approaches the player NOW rather than at 
any other moment. It is also the primary specificity 
constraint: the generated quest must only make sense for 
a player who took this exact action. The generator prompt 
makes this explicit: "This quest should only make sense 
for a player who took this exact action."

Every test state demonstrated this. State 3 (Sera) only 
works because the player released a courier — not because 
they're "the kind of player who is soft on enemies." 
State 5 (Daria) only works because the player used 
Syndicate coin specifically — not because they were 
generous. Generic player archetypes can't produce these 
quests. The action can.

**Note on naming:** test-states.json used `last_player_action`. 
The schema uses `player_action`. The "last" qualifier is 
implicit — this field always holds the most recent 
propagated action. Dropping the prefix is cleaner.

**Example:** `"Bribed the eastern gate guard"`

---

### 3. `npc_name`
**Contains:** The NPC's name, as a standalone string.

**Why necessary:** The generator references this field 
directly in prompt construction (`where {npc_name} 
approaches the player`) and in generated dialogue. Keeping 
it as its own field — not embedded in npc_situation — 
means the generator can address the NPC by name without 
parsing a description string. It also enables cross-session 
continuity: when the NPC schema is built (Step 4), 
npc_name becomes the key that links a game state instance 
to the full NPC record.

**Example:** `"Mira"`

---

### 4. `npc_situation`
**Contains:** The NPC's pre-existing problem, goal, or 
circumstance — independent of the player.

**Why necessary:** This is the most important field for 
the experience goal. Without it, every NPC is purely 
reactive — they exist to respond to the player. With it, 
the NPC was already living their life before the player's 
action intersected with it.

The quest lives in the collision between npc_situation 
and player_action. In State 1: Mira's daughter was already 
sick (situation) before the player bribed the guard 
(action). The quest exists at their intersection — the 
player's action accidentally opened a door the NPC 
desperately needed. That collision is what produces the 
"disorienting recognition" feeling: the world was already 
moving, and the player's action landed inside it.

Drop this field and the quests become requests. Include 
it and they become consequences.

**Example:** `"Sick daughter needs medicine from the 
eastern district, blocked by guards"`

---

### 5. `npc_knowledge`
**Contains:** Exactly what the NPC knows about the 
player's action and how they came to know it.

**Why necessary:** This is the grounding constraint. It 
answers the question the experience goal is built on: 
"how did they know that?"

The 5 test states used 5 different information channels:
- State 1 (Mira): rumor — "heard someone bribed..."
- State 2 (Tomás): eyewitness — "watched from across 
  the square"
- State 3 (Sera): eyewitness — "was hiding nearby"
- State 4 (Voss): second-hand — "a resistance contact 
  told him"
- State 5 (Daria): deduction — "recognized the coin stamp"

Each channel is specific and plausible. Without this 
field, the LLM generates knowledge without a source — 
the NPC "somehow knows" what the player did. That breaks 
the grounding. With it, the NPC's knowledge has a 
traceable path through the world, which is exactly what 
the gossip propagation system (Step 3+) will formalize.

This field is also the foundation for the constraint 
validator (Step 6): the validator will check that what 
the NPC claims to know is consistent with a plausible 
information path from the player's action.

**Example:** `"Heard someone bribed the eastern guard 
this morning"`

---

## Is 5 fields enough?

**Yes — for this step.** 

The 5 fields together give the generator everything it 
needs to produce a quest that passes the experience goal 
test. All 5 test states passed that test. A player reading 
any of the 5 generated quests would ask "how did they 
know that?" rather than accepting it without reading.

The 5 fields cover:
- Story anchor (main_quest)
- Triggering event (player_action)
- Who is speaking (npc_name)
- Why the NPC has stakes (npc_situation)
- Why the NPC's knowledge is credible (npc_knowledge)

This is the minimum viable unit of context for grounded 
quest generation. Nothing in this list is redundant. 
Removing any one field breaks a distinct part of the 
output.

---

## What would be lost with fewer

**4 fields — drop npc_name:**
Minor loss. The generator can infer a name from 
npc_situation or be prompted to invent one. Output 
quality degrades slightly but doesn't break. This is 
the safest field to drop — but keeping it as a separate 
key costs nothing and enables cleaner prompt construction.

**4 fields — drop main_quest:**
The quest becomes disconnected from the larger story. 
The NPC's intel reward has nothing to anchor to. Side 
quests start feeling like random favors rather than part 
of a world the player is actively reshaping. The 
constraint preventing NPCs from resolving main story 
beats also loses its reference point.

**4 fields — drop player_action:**
The NPC has a situation but no reason to approach the 
player now. Every NPC feels like they're standing around 
waiting to issue a quest. The specificity constraint 
collapses — any player, regardless of what they did, 
gets the same NPC approach. This is the generic quest 
problem the whole system exists to solve.

**4 fields — drop npc_situation:**
NPCs become purely reactive. The world is built to serve 
the player. Quests become requests rather than 
consequences. The "disorienting recognition" is replaced 
by "oh, another person who needs something from me." 
This is the most damaging drop.

**4 fields — drop npc_knowledge:**
The grounding constraint disappears. The LLM invents 
implausible knowledge channels or uses vague formulations 
("somehow knew," "had heard rumors"). The gossip 
propagation system has no foundation to build on. The 
"how did they know that?" test fails consistently.

**3 fields — any combination:**
At 3 fields the generator starts hallucinating context 
it needs but wasn't given. Output becomes plausible-
sounding but not grounded. The quests feel like generic 
RPG quests with the player's name inserted.

---

## What would be gained with more

The natural 6th, 7th, 8th fields are already visible 
in the test states as implied structure:

**`player_history` (array):**
The 5 states only test single-action awareness. A real 
session involves many actions. An array of significant 
past actions enables callbacks ("you helped me last 
month when..."), rewards consistent behavior patterns, 
and powers the gossip network — other NPCs can reference 
things the player did two sessions ago if the propagation 
chain reaches them. This is Step 3's natural extension 
toward Step 5 (quest templates with player-choice 
callbacks).

player_history is now confirmed necessary by Template 3 
(Player Choice Callback). The template requires past 
choices as an array, not just the most recent action. 
This field should be added to the game state schema 
for step 6 implementation.

**`world_state_flags` (object):**
Named boolean consequences of player actions that have 
altered the world. Example: `{"eastern_guard_bribed": true, 
"manifest_destroyed": true}`. This is the substrate for 
the constraint validator (Step 6) — instead of asking 
the LLM to infer what changed, you tell it explicitly. 
Also prevents contradictions: if the eastern guard was 
later killed, `eastern_guard_bribed` becomes stale and 
the validator catches it.

**`npc_relationship` (string or enum):**
How the NPC knows the player. First encounter vs. prior 
interaction changes dialogue register, trust level, and 
what the NPC would reasonably ask for. Mira asking a 
stranger for help vs. asking someone who helped her 
before are different quests even if everything else is 
identical.

These three fields belong to Step 4 (NPC schema) and 
Step 6 (fact database). Adding them now would be 
premature — they require the NPC schema and constraint 
validator infrastructure that doesn't exist yet.

The 5-field schema is complete for Step 3. Build the 
NPC schema next, then extend the game state when the 
NPC record gives the additional fields somewhere to live.

---

## One-line summary

5 fields is the right number for this step: enough to 
generate grounded, specific, contextually appropriate 
quests; not so many that the schema outpaces the 
infrastructure to populate it.
