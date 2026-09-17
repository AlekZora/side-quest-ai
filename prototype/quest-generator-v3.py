import anthropic
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

client = anthropic.Anthropic()

# ── NPC definitions ──────────────────────────────────────────────────────────
# Embedded inline. One NPC per template, sourced from quest-templates.md.
# No external file dependency.

NPCS = {
    "Serge": {
        "name": "Serge",
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
    },
    "Daria": {
        "name": "Daria",
        "situation": (
            "Runs a small alterations shop two streets from the cloth merchant's "
            "warehouse. Has been altering Syndicate uniforms for junior officers for "
            "three years — the only steady work she could get after her husband was "
            "detained. She does not know if he is alive."
        ),
        "want": (
            "Find out what happened to her husband after his initial detention. She "
            "was told he was transferred to a labor assignment outside the district. "
            "The officer who told her was reassigned six months later and the paperwork "
            "trail went cold. She has been trying to find another officer who touched "
            "his file."
        ),
        "stake": (
            "Her son Mikhail is twelve. Three months ago he stopped asking about his "
            "father. Last week he asked her how old you have to be to apply for Syndicate "
            "youth enrollment. She has not answered him. If she cannot find out what "
            "happened to her husband — if she cannot give Mikhail a true account of who "
            "his father was and what was done to him — she will watch her son become "
            "the kind of person who took him."
        ),
        "network": (
            "Alters uniforms for approximately twenty Syndicate junior officers on a "
            "rotating basis. Knows which officers are newly transferred into the district "
            "(new uniform adjustments), which are being promoted (rank insignia changes), "
            "and which have recently attended disciplinary hearings (dress uniform "
            "alterations ordered on short notice, paid in cash). Has seen three years "
            "of officer rotation patterns."
        ),
    },
    "Otto": {
        "name": "Otto",
        "situation": (
            "Runs the eastern gate checkpoint's unofficial holding room — a converted "
            "storage space where people flagged at the gate wait while their papers are "
            "reviewed. He is not Syndicate; he is contracted. He sees everyone who gets "
            "stopped, everyone who gets waved through, and everyone who pays to avoid both."
        ),
        "want": (
            "Get his contract renewed for another six months. His supervisor has told "
            "him the renewal depends on flagging more resistance contacts — the quota has "
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
            "Sees every person who passes through the eastern gate checkpoint — who "
            "gets stopped, who gets waved through, who pays the guard directly, and who "
            "is carrying something they would prefer not to have inspected. Has two years "
            "of observational records kept in a personal ledger he has never shown anyone."
        ),
    },
    "Nadia": {
        "name": "Nadia",
        "situation": (
            "Cartographer on commission from the eastern merchant guild. She has been "
            "hired to update the district map after the recent guard checkpoint "
            "reconfiguration — new routes, new restricted zones, new administrative "
            "boundaries. She is three weeks into a six-week commission and one street "
            "short of completing the eastern section."
        ),
        "want": (
            "Walk down Reiner Alley with her instruments and finish the survey. The "
            "alley was reclassified as restricted after the reconfiguration. She does "
            "not know why. She has been turned away at the entry checkpoint twice. She "
            "needs either access or someone who can tell her what changed."
        ),
        "stake": (
            "Her apprenticeship with the guild ends in eight weeks. The commission "
            "was supposed to be her exit credential — proof of completed work for the "
            "guild master's reference letter. He is the only person in the city qualified "
            "to vouch for her cartography, because her previous mentor died before her "
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
    },
}

# ── Game states ──────────────────────────────────────────────────────────────
# One per template. Callback includes player_history array.

GAME_STATES = {
    "escalation": {
        "main_quest": "Rescue Elena from the Syndicate",
        "player_action": "Burned the Syndicate's supply manifest rather than handing it to the resistance",
        "npc_name": "Serge",
        "npc_situation": (
            "Serge picked up a packet this morning from the northern district stamped "
            "with the urgency code that precedes prisoner transfers — the first time he "
            "has seen this code addressed to the holding facility in three months. He "
            "was told to deliver it before end of shift."
        ),
        "npc_knowledge": (
            "His supervisor told him the urgent classification was triggered because "
            "someone destroyed the supply manifest and the facility is locking down its "
            "record trail. The supervisor did not say who destroyed it, but Serge worked "
            "out the timing."
        ),
    },
    "personal_crisis": {
        "main_quest": "Rescue Elena from the Syndicate",
        "player_action": "Burned the Syndicate's supply manifest rather than handing it to the resistance",
        "npc_name": "Daria",
        "npc_situation": (
            "A junior officer came in for emergency alterations this morning — dress "
            "uniform, paid in cash, would not give his name. She recognized the insignia: "
            "northern district records office, the same branch that processed her "
            "husband's transfer. He is picking up the uniform tonight."
        ),
        "npc_knowledge": (
            "One of her regular officers mentioned yesterday that someone had destroyed "
            "the supply manifest — he was annoyed because it meant extra paperwork. He "
            "did not say who. But the emergency alteration request came in the same "
            "morning, and Daria knows that dress uniforms paid in cash mean someone is "
            "being moved before the record catches up."
        ),
    },
    "callback": {
        "main_quest": "Rescue Elena from the Syndicate",
        "player_action": "Burned the Syndicate's supply manifest rather than handing it to the resistance",
        "npc_name": "Otto",
        "npc_situation": (
            "The Syndicate supervisor came to the checkpoint this morning to review "
            "Otto's flagging quota. While there, the supervisor mentioned that someone "
            "had destroyed the supply manifest — the first time Otto has heard the "
            "player mentioned in an official context."
        ),
        "npc_knowledge": (
            "The supervisor did not name the player but described the action. Otto "
            "recognized it from his ledger: the same person who, three weeks ago, let "
            "a detained woman go without collecting the release fee."
        ),
        "player_history": [
            {
                "action": "Let a detained woman go at the eastern gate without collecting the standard release fee, telling the guard she had already paid",
                "context": "Three weeks ago. The woman was held for expired transit papers. The player intervened verbally, claiming the fee had been paid at the northern checkpoint. The guard accepted it. Otto was in the holding room and heard the exchange. The player did not know anyone was listening.",
            },
            {
                "action": "Bribed the eastern gate guard to pass through after curfew",
                "context": "Two weeks ago. Standard bribe, nothing unusual. Otto logged it.",
            },
            {
                "action": "Burned the Syndicate's supply manifest rather than handing it to the resistance",
                "context": "This morning. Now propagating through the district.",
            },
        ],
    },
    "world_texture": {
        "main_quest": "Rescue Elena from the Syndicate",
        "player_action": "Burned the Syndicate's supply manifest rather than handing it to the resistance",
        "npc_name": "Nadia",
        "npc_situation": (
            "She was at the checkpoint near the cloth merchant's warehouse when word "
            "spread that someone had destroyed a Syndicate document and slipped the "
            "district before they could be caught. She is not interested in the politics. "
            "She is interested in anyone who knows how to move through checkpoints this "
            "district has decided to make difficult."
        ),
        "npc_knowledge": (
            "Overheard two guards at the warehouse checkpoint discussing the incident "
            "— they were annoyed about the extra watch shift it triggered. She does not "
            "know who destroyed the manifest or why. She knows the person got through."
        ),
    },
}

# ── Prompt builders ──────────────────────────────────────────────────────────

def build_escalation_prompt(gs, npc):
    return f"""You are a quest designer for a narrative RPG.

GAME STATE:
  Main quest: {gs['main_quest']}
  Player's last action: {gs['player_action']}
  Current situation: {gs['npc_situation']}
  How {npc['name']} learned of the player's action: {gs['npc_knowledge']}

NPC — {npc['name']}:
  Who they are: {npc['situation']}
  What they want: {npc['want']}
  What they stand to lose: {npc['stake']}
  Who they know / what they have access to: {npc['network']}

Generate a main quest escalation quest where {npc['name']} approaches the player.
The task is a means to a revelation — the reveal is the reward, not the errand.

Include exactly these five things:

1. WHY {npc['name']} is approaching the player right now — connect the player's
   action to {npc['name']}'s current situation. The player's action is what makes
   {npc['name']} willing to risk this conversation. Be specific about the connection.

2. WHAT {npc['name']} needs from the player — a concrete task that uses the kind
   of capability the player demonstrated in {gs['player_action']}.

3. WHAT it costs the player to help — time, resources, exposure, or moral weight.
   Must be real, not a token errand.

4. WHAT {npc['name']} reveals after the task is complete — must come from their
   actual network access, not invented sources. This revelation must recontextualize
   something specific about {gs['main_quest']} that the player thought they
   understood. Do not invent information the NPC could not plausibly have.

5. WHAT CHANGES — one sentence on how the player's understanding of
   {gs['main_quest']} is different after this reveal than before.

Keep it grounded and specific. The revelation must be something only {npc['name']}
could know through their specific network. This quest must not make sense for a
player who did anything other than {gs['player_action']}."""


def build_personal_crisis_prompt(gs, npc):
    return f"""You are a quest designer for a narrative RPG.

GAME STATE:
  Main quest: {gs['main_quest']}
  Player's last action: {gs['player_action']}
  Current situation: {gs['npc_situation']}
  How {npc['name']} learned of the player's action: {gs['npc_knowledge']}

NPC — {npc['name']}:
  Who they are: {npc['situation']}
  What they want: {npc['want']}
  What they stand to lose: {npc['stake']}
  Who they know / what they have access to: {npc['network']}

Generate an NPC personal crisis quest where {npc['name']} approaches the player.
The quest must emerge entirely from {npc['name']}'s situation and stake.
The main quest is background context only — do not make it the emotional center.

Include exactly these five things:

1. WHY {npc['name']} is approaching the player specifically — the player's action
   is what established the trust or created the specific need. {npc['name']} is not
   approaching because the player is the hero. They are approaching because of
   what {gs['player_action']} revealed about what kind of person the player is.
   Name the quality the player demonstrated that made {npc['name']} choose them.

2. WHAT the crisis is — derive it directly from {npc['stake']}. What is actively
   threatening what {npc['name']} stands to lose, and why is it happening now?
   The crisis must be concrete, not atmospheric.

3. WHAT {npc['name']} needs from the player — a specific ask that reflects both
   their want and what their stake makes them unwilling or unable to do themselves.
   Do not make this an errand. It should require something most people would not offer.

4. WHAT it costs the player to help — must be real. Not time or gold: exposure,
   a relationship, a future option foreclosed.

5. WHAT the emotional weight of the quest is — one sentence naming exactly what
   {npc['name']} is actually protecting and what it would mean to lose it. This
   is not the objective. It is the reason the objective matters to a person.

Keep it grounded and specific. {npc['name']}'s ask must be shaped by what they
stand to lose, not by what would be useful to the player. This quest should
produce the player reaction: "I'm helping because of who she is, not because
of the main quest.\""""


def build_callback_prompt(gs, npc):
    history_lines = "\n".join([
        f"  {i + 1}. {entry['action']}. {entry['context']}"
        for i, entry in enumerate(gs["player_history"])
    ])
    ref = gs["player_history"][0]  # oldest entry is the callback target

    return f"""You are a quest designer for a narrative RPG.

GAME STATE:
  Main quest: {gs['main_quest']}
  Player's most recent action: {gs['player_action']}
  Current situation: {gs['npc_situation']}
  How {npc['name']} knows of the player's recent action: {gs['npc_knowledge']}

PLAYER HISTORY (oldest first):
{history_lines}

REFERENCED PAST CHOICE (the reason for this approach):
  Choice: {ref['action']}
  When and where: {ref['context']}

NPC — {npc['name']}:
  Who they are: {npc['situation']}
  What they want: {npc['want']}
  What they stand to lose: {npc['stake']}
  Who they know / what they have access to: {npc['network']}

Generate a player-choice callback quest where {npc['name']} approaches the player
because of the referenced past choice — not because of the most recent action.
The most recent action is only what created the opening to approach now.

Include exactly these five things:

1. WHY {npc['name']} is approaching now — something in the current situation has
   surfaced the past choice. Explain what made this the moment to act, and why
   the past choice is the actual reason. These are two different things. Be
   explicit about both.

2. WHAT {npc['name']} observed or learned about the referenced choice — how they
   witnessed it, what channel it reached them through, and what they concluded
   about the player from it. Their knowledge must be plausible given their network.

3. WHAT {npc['name']} needs — something that only a player who made that past
   choice would credibly do again, or would be trusted to do. The ask must
   connect to what the past choice revealed about the player's values.

4. WHAT it costs the player to help — must be real, not token.

5. THE RECOGNITION LINE — one exact line of dialogue that {npc['name']} says
   that proves they were watching when the player thought no one was. This is
   the moment the experience goal lands or fails. The line must name the past
   choice specifically enough to trigger recall without summarizing it flatly.
   It should feel like being caught — not accused, caught.

Keep it grounded and specific. The past choice is the reason for the approach.
The player should feel retroactive recognition: the world was tracking something
they did before they knew the world was watching."""


def build_world_texture_prompt(gs, npc):
    return f"""You are a quest designer for a narrative RPG.

GAME STATE:
  Main quest: {gs['main_quest']}
  Player's last action: {gs['player_action']}
  Current situation: {gs['npc_situation']}
  How {npc['name']} learned of the player's action: {gs['npc_knowledge']}

NPC — {npc['name']}:
  Who they are: {npc['situation']}
  What they want: {npc['want']}
  What they stand to lose: {npc['stake']}
  Who they know / what they have access to: {npc['network']}

Generate a world texture quest where {npc['name']} approaches the player.
This quest has no connection to {gs['main_quest']}.
Do not reference {gs['main_quest']} in the quest output.
Do not provide intel about the main story.
Do not escalate any stakes beyond {npc['name']}'s personal situation.

The player's action reached {npc['name']} through the world — that is the only
required connection. The quest is entirely about {npc['name']}'s life.

Include exactly these five things:

1. HOW the player's action reached {npc['name']} — through what specific channel,
   and what {npc['name']} concluded from it. This should feel incidental, not
   fated. The action is why {npc['name']} knows to approach this specific person.
   It is not why the quest exists.

2. WHAT {npc['name']}'s actual situation is — not a summary, but what it feels
   like from the inside. What {npc['name']} is dealing with right now, in concrete
   terms. This is the emotional center of the quest. It must be interesting
   without any reference to the main story.

3. WHAT {npc['name']} needs from the player — specific and shaped by their want.
   Must connect to the kind of capability the player demonstrated in
   {gs['player_action']}.

4. WHAT it costs the player to help — real cost, not a token errand.

5. WHAT STAYS UNRESOLVED — after the player helps, what is still true about
   {npc['name']}'s situation. The deeper problem — what they stand to lose —
   does not go away when the immediate need is met. Name it in one sentence.
   This is what makes the world feel inhabited rather than designed.

Keep it grounded and specific. This quest should feel like it would exist in
this world regardless of the main story. The player's instinct after accepting
should be: "this has nothing to do with my main objective — I'm just helping
someone.\""""


# ── Routing ──────────────────────────────────────────────────────────────────

PROMPT_BUILDERS = {
    "escalation":     build_escalation_prompt,
    "personal_crisis": build_personal_crisis_prompt,
    "callback":       build_callback_prompt,
    "world_texture":  build_world_texture_prompt,
}

TEMPLATE_NPCS = {
    "escalation":     "Serge",
    "personal_crisis": "Daria",
    "callback":       "Otto",
    "world_texture":  "Nadia",
}

TEMPLATE_LABELS = {
    "escalation":     "TEMPLATE 1 — MAIN QUEST ESCALATION",
    "personal_crisis": "TEMPLATE 2 — NPC PERSONAL CRISIS",
    "callback":       "TEMPLATE 3 — PLAYER CHOICE CALLBACK",
    "world_texture":  "TEMPLATE 4 — WORLD TEXTURE",
}

# ── Run all four ─────────────────────────────────────────────────────────────

TEMPLATES = ["escalation", "personal_crisis", "callback", "world_texture"]

total_in = 0
total_out = 0

for template_type in TEMPLATES:
    npc_name = TEMPLATE_NPCS[template_type]
    npc = NPCS[npc_name]
    gs = GAME_STATES[template_type]
    prompt = PROMPT_BUILDERS[template_type](gs, npc)

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )

    result = message.content[0].text
    in_tok = message.usage.input_tokens
    out_tok = message.usage.output_tokens
    total_in += in_tok
    total_out += out_tok

    print(f"\n{'=' * 62}")
    print(f"  {TEMPLATE_LABELS[template_type]}")
    print(f"  NPC            : {npc_name}")
    print(f"  Player action  : {gs['player_action']}")
    print(f"{'=' * 62}\n")
    print(result)
    print(f"\n── tokens: {in_tok} in / {out_tok} out ──")

print(f"\n{'=' * 62}")
print("  ALL FOUR TEMPLATES COMPLETE")
print(f"  Total tokens: {total_in} in / {total_out} out")
print(f"{'=' * 62}")
