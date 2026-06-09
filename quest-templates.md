# Quest Templates — Side Quest AI System
*Created: 2026-06-09*

Three structured prompt templates. Each takes a game state + NPC definition
and produces a specific type of contextual quest. All three enforce the
experience goal: the quest must be specific to this player's story, not the
generic one.

Fields map directly to the two schemas:
- Game state: main_quest, player_action, npc_name, npc_situation, npc_knowledge
- NPC definition: name, situation, want, stake, network

---

## Template 1 — MAIN QUEST ESCALATION

**What it produces:** A quest where the task is a means to a revelation.
The NPC has knowledge — through their specific network — that recontextualizes
something the player thought they understood about the main quest. The reveal
is the reward, not the task. The player completes the errand to earn access
to the NPC's intelligence.

**Fields used:**
- `game_state.main_quest` — what the revelation must recontextualize
- `game_state.player_action` — what makes the NPC willing to risk this conversation
- `game_state.npc_situation` — the current pressure making the NPC approach now
- `game_state.npc_knowledge` — how they learned of the player's action (grounding)
- `npc.name`, `npc.situation`, `npc.want`, `npc.stake`, `npc.network`
- `npc.network` is load-bearing: the revelation must be derivable only from it

**Experience goal test:**
Player stops, reads the quest text, completes the task — then re-reads an
earlier part of the main quest with new understanding. The question they ask
is "wait, does that mean...?" not "how did they know that?" They are
reprocessing something they already knew. The revelation works if it makes
past information feel like it was always pointing somewhere they missed.

**Failure signal:**
Player reads only the task objective and skips the revelation at the end.
Position the revelation where it cannot be skipped — it must be in the
closing NPC dialogue, not in the quest log summary.

---

### Prompt Template 1

```
You are a quest designer for a narrative RPG.

GAME STATE:
  Main quest: {game_state.main_quest}
  Player's last action: {game_state.player_action}
  Current situation: {game_state.npc_situation}
  How {npc.name} learned of the player's action: {game_state.npc_knowledge}

NPC — {npc.name}:
  Who they are: {npc.situation}
  What they want: {npc.want}
  What they stand to lose: {npc.stake}
  Who they know / what they have access to: {npc.network}

Generate a main quest escalation quest where {npc.name} approaches the player.
The task is a means to a revelation — the reveal is the reward, not the errand.

Include exactly these five things:

1. WHY {npc.name} is approaching the player right now — connect the player's
   action to {npc.name}'s current situation. The player's action is what makes
   {npc.name} willing to risk this conversation. Be specific about the connection.

2. WHAT {npc.name} needs from the player — a concrete task that uses the kind
   of capability the player demonstrated in {game_state.player_action}.

3. WHAT it costs the player to help — time, resources, exposure, or moral weight.
   Must be real, not a token errand.

4. WHAT {npc.name} reveals after the task is complete — must come from their
   actual network access in {npc.network}, not invented sources. This revelation
   must recontextualize something specific about {game_state.main_quest} that
   the player thought they understood. Do not invent information the NPC could
   not plausibly have through the network described.

5. WHAT CHANGES — one sentence on how the player's understanding of
   {game_state.main_quest} is different after this reveal than before.

Keep it grounded and specific. The revelation must be something only {npc.name}
could know through their specific network. This quest must not make sense for a
player who did anything other than {game_state.player_action}.
```

---

### Example — Template 1 Filled

**NPC: Serge**
```json
{
  "name": "Serge",
  "situation": "Syndicate courier. Routes sealed packets between the three district
    administrative offices and the holding facility. Has done this for eleven months
    — long enough to know every urgency code, every routing pattern, and which
    destinations mean someone is not coming back.",
  "want": "Complete his current shift without being stopped at a checkpoint. He
    is carrying a packet addressed to the holding facility stamped with an urgency
    code he has seen only twice before, both times before a prisoner disappeared
    from the official record.",
  "stake": "His sister Marta co-signed his hiring paperwork when he applied for
    the courier position. She vouched for him without knowing who he had become in
    the year before. If Serge is identified as a resistance contact, the investigation
    works backward through his file and reaches her signature. She would be held
    accountable for someone she no longer recognizes.",
  "network": "Handles sealed routing packets for all three district supervisors.
    Knows the timing, destination, and urgency classification of every inter-office
    communication — urgency codes are stamped on the outside of each packet. Has
    memorized which code combinations precede prisoner transfers versus standard
    administrative actions, based on eleven months of pattern observation."
}
```

**Game state:**
```json
{
  "main_quest": "Rescue Elena from the Syndicate",
  "player_action": "Burned the Syndicate's supply manifest rather than handing it
    to the resistance",
  "npc_name": "Serge",
  "npc_situation": "Serge picked up a packet this morning from the northern district
    stamped with the urgency code that precedes prisoner transfers — the first time
    he has seen this code addressed to the holding facility in three months. He was
    told to deliver it before end of shift.",
  "npc_knowledge": "His supervisor told him the urgent classification was triggered
    because someone destroyed the supply manifest and the facility is locking down
    its record trail. The supervisor did not say who destroyed it, but Serge worked
    out the timing."
}
```

**Filled prompt:**
```
You are a quest designer for a narrative RPG.

GAME STATE:
  Main quest: Rescue Elena from the Syndicate
  Player's last action: Burned the Syndicate's supply manifest rather than
    handing it to the resistance
  Current situation: Serge picked up a packet this morning from the northern
    district stamped with the urgency code that precedes prisoner transfers —
    the first time he has seen this code addressed to the holding facility in
    three months. He was told to deliver it before end of shift.
  How Serge learned of the player's action: His supervisor told him the urgent
    classification was triggered because someone destroyed the supply manifest
    and the facility is locking down its record trail. The supervisor did not
    say who destroyed it, but Serge worked out the timing.

NPC — Serge:
  Who they are: Syndicate courier. Routes sealed packets between the three
    district administrative offices and the holding facility. Has done this for
    eleven months — long enough to know every urgency code, every routing
    pattern, and which destinations mean someone is not coming back.
  What they want: Complete his current shift without being stopped at a
    checkpoint. He is carrying a packet addressed to the holding facility
    stamped with an urgency code he has seen only twice before, both times
    before a prisoner disappeared from the official record.
  What they stand to lose: His sister Marta co-signed his hiring paperwork
    when he applied for the courier position. She vouched for him without
    knowing who he had become in the year before. If Serge is identified as
    a resistance contact, the investigation works backward through his file
    and reaches her signature. She would be held accountable for someone she
    no longer recognizes.
  Who they know / what they have access to: Handles sealed routing packets
    for all three district supervisors. Knows the timing, destination, and
    urgency classification of every inter-office communication — urgency codes
    are stamped on the outside. Has memorized which code combinations precede
    prisoner transfers versus standard administrative actions.

Generate a main quest escalation quest where Serge approaches the player.
The task is a means to a revelation — the reveal is the reward, not the errand.

[...five-part output instructions as above...]

This quest must not make sense for a player who did anything other than burned
the Syndicate's supply manifest rather than handing it to the resistance.
```

---

## Template 2 — NPC PERSONAL CRISIS

**What it produces:** A quest that emerges entirely from the NPC's situation
and stake fields. The player's action established trust or created a specific
need — the NPC is not approaching because the player is the hero, but because
of what the player's action revealed about who they are. The main quest is
background context only. The emotional weight comes from the stake.

**Fields used:**
- `npc.stake` — the crisis must threaten what the NPC stands to lose
- `npc.situation` — what was already true before the player arrived
- `npc.want` — what the NPC is actively working toward; shapes the ask
- `game_state.player_action` — what established the trust or created the need
- `game_state.npc_knowledge` — how they identified this player as the one to ask
- `game_state.main_quest` — background only; do not make it the emotional center

**Experience goal test:**
When asked "what just happened?", the player leads with the NPC's situation,
not the objective. "I have to help this woman because her son is starting to
enlist and she needs to know what happened to her husband before she loses him
too" — not "I have to get some documents." The player absorbed the stake.
The test passes when the player could explain why this quest matters to this
specific NPC without mentioning the main quest at all.

**Failure signal:**
Player describes only the task objective. The stake did not land. Usually
means the crisis was too abstract — the stake must name something specific
and irreplaceable, not a category ("her freedom," "her livelihood").

---

### Prompt Template 2

```
You are a quest designer for a narrative RPG.

GAME STATE:
  Main quest: {game_state.main_quest}
  Player's last action: {game_state.player_action}
  Current situation: {game_state.npc_situation}
  How {npc.name} learned of the player's action: {game_state.npc_knowledge}

NPC — {npc.name}:
  Who they are: {npc.situation}
  What they want: {npc.want}
  What they stand to lose: {npc.stake}
  Who they know / what they have access to: {npc.network}

Generate an NPC personal crisis quest where {npc.name} approaches the player.
The quest must emerge entirely from {npc.name}'s situation and stake.
The main quest is background context only — do not make it the emotional center.

Include exactly these five things:

1. WHY {npc.name} is approaching the player specifically — the player's action
   is what established the trust or created the specific need. {npc.name} is not
   approaching because the player is the hero. They are approaching because of
   what {game_state.player_action} revealed about what kind of person the player
   is. Name the quality the player demonstrated that made {npc.name} choose them.

2. WHAT the crisis is — derive it directly from {npc.stake}. What is actively
   threatening what {npc.name} stands to lose, and why is it happening now?
   The crisis must be concrete, not atmospheric.

3. WHAT {npc.name} needs from the player — a specific ask that reflects both
   their want and what their stake makes them unwilling or unable to do themselves.
   Do not make this an errand. It should require something from the player that
   most people would not offer.

4. WHAT it costs the player to help — must be real. Not time or gold: exposure,
   a relationship, a future option foreclosed.

5. WHAT the emotional weight of the quest is — one sentence that names exactly
   what {npc.name} is actually protecting and what it would mean to them to lose
   it. This is not the objective. It is the reason the objective matters to a
   person, not to a quest system.

Keep it grounded and specific. {npc.name}'s ask must be shaped by what they stand
to lose, not by what would be useful to the player. This quest should produce the
player reaction: "I'm helping because of who she is, not because of the main quest."
```

---

### Example — Template 2 Filled

**NPC: Daria**
```json
{
  "name": "Daria",
  "situation": "Runs a small alterations shop two streets from the cloth merchant's
    warehouse. Has been altering Syndicate uniforms for junior officers for three
    years — the only steady work she could get after her husband was detained.
    She does not know if he is alive.",
  "want": "Find out what happened to her husband after his initial detention.
    She was told he was transferred to a labor assignment outside the district.
    The officer who told her was reassigned six months later and the paperwork
    trail went cold. She has been trying to find another officer who touched
    his file.",
  "stake": "Her son Mikhail is twelve. Three months ago he stopped asking about
    his father. Last week he asked her how old you have to be to apply for
    Syndicate youth enrollment. She has not answered him. If she cannot find
    out what happened to her husband — if she cannot give Mikhail a true account
    of who his father was and what was done to him — she will watch her son
    become the kind of person who took him.",
  "network": "Alters uniforms for approximately twenty Syndicate junior officers
    on a rotating basis. Knows which officers are newly transferred into the
    district (new uniform adjustments), which are being promoted (rank insignia
    changes), and which have recently attended disciplinary hearings (dress
    uniform alterations ordered on short notice, paid in cash). Has seen three
    years of officer rotation patterns."
}
```

**Game state:**
```json
{
  "main_quest": "Rescue Elena from the Syndicate",
  "player_action": "Burned the Syndicate's supply manifest rather than handing
    it to the resistance",
  "npc_name": "Daria",
  "npc_situation": "A junior officer came in for emergency alterations this
    morning — dress uniform, paid in cash, would not give his name. She
    recognized the insignia: northern district records office, the same branch
    that processed her husband's transfer. He is picking up the uniform tonight.",
  "npc_knowledge": "One of her regular officers mentioned yesterday that someone
    had destroyed the supply manifest — he was annoyed because it meant extra
    paperwork. He did not say who. But the emergency alteration request came in
    the same morning, and Daria knows that dress uniforms paid in cash mean
    someone is being moved before the record catches up."
}
```

**Filled prompt:**
```
You are a quest designer for a narrative RPG.

GAME STATE:
  Main quest: Rescue Elena from the Syndicate
  Player's last action: Burned the Syndicate's supply manifest rather than
    handing it to the resistance
  Current situation: A junior officer came in for emergency alterations this
    morning — dress uniform, paid in cash, would not give his name. She
    recognized the insignia: northern district records office, the same branch
    that processed her husband's transfer. He is picking up the uniform tonight.
  How Daria learned of the player's action: One of her regular officers mentioned
    yesterday that someone had destroyed the supply manifest — he was annoyed
    because it meant extra paperwork. He did not say who. But the emergency
    alteration request came in the same morning, and Daria knows that dress
    uniforms paid in cash mean someone is being moved before the record catches up.

NPC — Daria:
  Who they are: Runs a small alterations shop two streets from the cloth
    merchant's warehouse. Has been altering Syndicate uniforms for junior officers
    for three years — the only steady work she could get after her husband was
    detained. She does not know if he is alive.
  What they want: Find out what happened to her husband after his initial
    detention. She was told he was transferred to a labor assignment outside the
    district. The officer who told her was reassigned six months later and the
    paperwork trail went cold.
  What they stand to lose: Her son Mikhail is twelve. Three months ago he stopped
    asking about his father. Last week he asked how old you have to be to apply
    for Syndicate youth enrollment. She has not answered him. If she cannot give
    Mikhail a true account of who his father was and what was done to him, she
    will watch her son become the kind of person who took him.
  Who they know / what they have access to: Alters uniforms for approximately
    twenty Syndicate junior officers on a rotating basis. Knows which officers are
    newly transferred (new adjustments), which are being promoted (insignia
    changes), and which have attended disciplinary hearings (dress uniforms,
    cash, short notice). Three years of officer rotation patterns.

Generate an NPC personal crisis quest where Daria approaches the player.
The quest must emerge entirely from Daria's situation and stake.
The main quest is background context only — do not make it the emotional center.

[...five-part output instructions as above...]

This quest should produce the player reaction: "I'm helping because of who she
is, not because of the main quest."
```

---

## Template 3 — PLAYER CHOICE CALLBACK

**What it produces:** A quest that explicitly references a specific past player
choice — not the most recent action, but an earlier one. The NPC approaches
because of something the player did before, and the current situation is only
what made the approach possible now. Tests whether the system can produce
retroactive recognition: the world was tracking a choice the player made without
knowing they were being watched.

**Schema note — extended game state required:**
This template requires one additional field not in the base 5-field game state:

```json
"player_history": [
  { "action": "string", "context": "string" }
]
```

`player_action` in the base schema is the most recent event — it provides cover
for why the NPC can approach now. `player_history` provides the accumulated
record. `referenced_choice` (pulled from history) is the actual reason for the
approach. This is the gap the Step 6 fact database must support.

**Fields used:**
- `game_state.player_action` — current event that creates the opening to approach
- `game_state.player_history` — accumulated choices; the callback is drawn from here
- `game_state.npc_situation` — what in the present has surfaced the past choice
- `game_state.npc_knowledge` — how the NPC observed the past choice (grounding)
- `npc.name`, `npc.situation`, `npc.want`, `npc.stake`, `npc.network`
- `referenced_choice` — the specific past action being called back (pulled from history)

**Experience goal test:**
Player asks "how did they know that?" specifically about the referenced past
choice — not the recent action. The recognition moment is discovering they were
observed making a decision they may not have consciously registered as significant.
The NPC's opening line must name the past choice clearly enough that the player
can place it. If the player cannot remember making the choice, the line must
trigger recall, not confusion.

**Failure signal:**
Player is confused about the connection. "What does that have to do with
anything I did?" The past choice was either too long ago without enough
specificity, or the NPC's opening failed to surface the memory correctly.
The referenced choice must be concrete enough to recall in one sentence.

---

### Prompt Template 3

```
You are a quest designer for a narrative RPG.

GAME STATE:
  Main quest: {game_state.main_quest}
  Player's most recent action: {game_state.player_action}
  Current situation: {game_state.npc_situation}
  How {npc.name} knows of the player's recent action: {game_state.npc_knowledge}

PLAYER HISTORY (oldest first):
{game_state.player_history}

REFERENCED PAST CHOICE (the reason for this approach):
  Choice: {referenced_choice.action}
  When and where: {referenced_choice.context}

NPC — {npc.name}:
  Who they are: {npc.situation}
  What they want: {npc.want}
  What they stand to lose: {npc.stake}
  Who they know / what they have access to: {npc.network}

Generate a player-choice callback quest where {npc.name} approaches the player
because of {referenced_choice.action} — not because of the most recent action.
The most recent action is only what created the opening to approach now.

Include exactly these five things:

1. WHY {npc.name} is approaching now — something in the current situation has
   surfaced the past choice. Explain what in {game_state.npc_situation} made
   this the moment to act, and why the past choice is the actual reason. These
   are two different things. Be explicit about both.

2. WHAT {npc.name} observed or learned about {referenced_choice.action} — how
   they witnessed it, what channel it reached them through, and what they concluded
   about the player from it. This is the grounding constraint: their knowledge
   of the past choice must be as plausible as their network allows.

3. WHAT {npc.name} needs — must be something that only a player who made
   {referenced_choice.action} would credibly do again, or would be trusted to do.
   The ask must connect to what the past choice revealed about the player's values.

4. WHAT it costs the player to help — must be real, not token.

5. THE RECOGNITION LINE — one line of dialogue that {npc.name} says or implies
   that proves they were watching when the player thought no one was. Write the
   exact dialogue. This is the moment the experience goal either lands or fails.
   The line must name the past choice specifically enough to trigger recall without
   summarizing it flatly. It should feel like being caught — not accused, caught.

Keep it grounded and specific. The past choice is the reason for the approach.
The player should feel retroactive recognition: the world was tracking something
they did before they knew the world was watching.
```

---

### Example — Template 3 Filled

**NPC: Otto**
```json
{
  "name": "Otto",
  "situation": "Runs the eastern gate checkpoint's unofficial holding room —
    a converted storage space where people flagged at the gate wait while their
    papers are reviewed. He is not Syndicate; he is contracted. He sees everyone
    who gets stopped, everyone who gets waved through, and everyone who pays
    to avoid both.",
  "want": "Get his contract renewed for another six months. His supervisor has
    told him the renewal depends on flagging more resistance contacts — the quota
    has increased and he is behind. He does not want to flag anyone. He is trying
    to find another way to satisfy the number.",
  "stake": "His wife runs a small food stall inside the gate. The stall license
    is attached to his contract — if his contract ends, the license ends with it.
    She built the stall over four years. He has not told her the renewal is in
    question because he does not know how to explain that he is the reason it
    might not happen.",
  "network": "Sees every person who passes through the eastern gate checkpoint —
    who gets stopped, who gets waved through, who pays the guard directly, and
    who is carrying something they would prefer not to have inspected. Has two
    years of observational records kept in a personal ledger he has never shown
    anyone."
}
```

**Game state with history:**
```json
{
  "main_quest": "Rescue Elena from the Syndicate",
  "player_action": "Burned the Syndicate's supply manifest rather than handing
    it to the resistance",
  "npc_name": "Otto",
  "npc_situation": "The Syndicate supervisor came to the checkpoint this morning
    to review Otto's flagging quota. While there, the supervisor mentioned that
    someone had destroyed the supply manifest — the first time Otto has heard the
    player mentioned in an official context.",
  "npc_knowledge": "The supervisor did not name the player but described the
    action. Otto recognized it from his ledger: the same person who, three weeks
    ago, let a detained woman go without collecting the release fee.",
  "player_history": [
    {
      "action": "Let a detained woman go at the eastern gate without collecting
        the standard release fee, telling the guard she had already paid",
      "context": "Three weeks ago, before the supply manifest mission. The woman
        was being held for expired transit papers. The player intervened verbally,
        claiming the fee had been paid at the northern checkpoint. The guard
        accepted it. Otto was in the holding room and heard the exchange."
    },
    {
      "action": "Bribed the eastern gate guard to pass through after curfew",
      "context": "Two weeks ago. Standard bribe, nothing unusual. Otto logged it."
    },
    {
      "action": "Burned the Syndicate's supply manifest rather than handing it
        to the resistance",
      "context": "This morning. Now propagating through the district."
    }
  ]
}
```

**Referenced past choice:**
```json
{
  "action": "Let a detained woman go at the eastern gate without collecting the
    release fee, telling the guard she had already paid",
  "context": "Three weeks ago. Otto was in the holding room and heard the exchange.
    The player did not know anyone was listening."
}
```

**Filled prompt:**
```
You are a quest designer for a narrative RPG.

GAME STATE:
  Main quest: Rescue Elena from the Syndicate
  Player's most recent action: Burned the Syndicate's supply manifest rather
    than handing it to the resistance
  Current situation: The Syndicate supervisor came to the checkpoint this morning
    to review Otto's flagging quota. While there, the supervisor mentioned that
    someone had destroyed the supply manifest — the first time Otto has heard
    the player mentioned in an official context.
  How Otto knows of the player's recent action: The supervisor did not name the
    player but described the action. Otto recognized it from his ledger: the same
    person who, three weeks ago, let a detained woman go without collecting the
    release fee.

PLAYER HISTORY (oldest first):
  1. Let a detained woman go at the eastern gate without collecting the standard
     release fee, telling the guard she had already paid. Three weeks ago, before
     the supply manifest mission. Otto was in the holding room and heard the exchange.
  2. Bribed the eastern gate guard to pass through after curfew. Two weeks ago.
     Otto logged it.
  3. Burned the Syndicate's supply manifest rather than handing it to the
     resistance. This morning.

REFERENCED PAST CHOICE (the reason for this approach):
  Choice: Let a detained woman go at the eastern gate without collecting the
    release fee, telling the guard she had already paid.
  When and where: Three weeks ago. Otto was in the holding room. The player did
    not know anyone was listening.

NPC — Otto:
  Who they are: Runs the eastern gate checkpoint's unofficial holding room —
    a converted storage space where people flagged at the gate wait while their
    papers are reviewed. Not Syndicate; contracted. Sees everyone who gets
    stopped, waved through, or pays to avoid both.
  What they want: Get his contract renewed for another six months. His supervisor
    has told him the renewal depends on flagging more resistance contacts. He is
    behind on quota. He does not want to flag anyone and is trying to find another
    way to satisfy the number.
  What they stand to lose: His wife runs a food stall inside the gate. The stall
    license is attached to his contract. If the contract ends, the license ends.
    She built it over four years. He has not told her the renewal is in question.
  Who they know / what they have access to: Sees every person who passes through
    the eastern gate — who gets stopped, who pays, who is carrying something they
    would prefer not inspected. Two years of observational records in a personal
    ledger he has never shown anyone.

Generate a player-choice callback quest where Otto approaches the player because
of the woman at the gate three weeks ago — not because of the manifest.

[...five-part output instructions as above...]

The player should feel retroactive recognition: the world was tracking something
they did before they knew the world was watching.
```

---

## Template 4 — WORLD TEXTURE

**What it produces:** A quest with no connection to the main quest. It emerges
entirely from the NPC's situation and stake. The player's action reached this
NPC through the world — directly or through the gossip network — and that
incidental contact is the only reason the NPC knows to approach this person.
No revelation. No escalation. No intel. Just the world being alive around
the player.

The defining structural feature: after the player helps, the NPC's deeper
problem — what they stand to lose — does not go away. The quest resolves the
immediate need, not the underlying situation. This is what makes the world feel
inhabited rather than designed.

**Fields used:**
- `npc.situation` — the emotional center; must be interesting on its own
- `npc.stake` — populates the "what stays unresolved" beat; the quest cannot
  resolve this, only the immediate need
- `npc.want` — shapes the specific ask
- `game_state.player_action` — used lightly; how the NPC learned to approach
  this person, not why the quest exists
- `game_state.npc_knowledge` — the incidental channel through which the
  player's action reached the NPC
- `game_state.main_quest` — explicitly excluded from quest output; background
  context only so the generator knows what NOT to connect to

**Experience goal test:**
The player accepts the quest and their first instinct is not to check whether
it connects to the main objective. When asked "what just happened?", they
describe the NPC's situation before the task. The feeling the template is
targeting: "this world has people in it who are not waiting to serve my plot."

Observable: player lingers on the quest text longer than a task description
warrants, because the NPC's situation is interesting on its own.

**Failure signals:**
- The generator connects the quest to the main quest despite instructions.
  Template 4 has no plot scaffold — if the NPC's situation isn't strong enough
  to carry the quest alone, it collapses into filler.
- Player asks "is this useful for finding Elena?" before deciding whether to
  accept. The quest failed to establish the NPC as a person before establishing
  them as a task-giver.
- The "what stays unresolved" beat is missing or too thin. Without it, the
  quest feels like a solved problem rather than a glimpse into a life.

---

### Prompt Template 4

```
You are a quest designer for a narrative RPG.

GAME STATE:
  Main quest: {game_state.main_quest}
  Player's last action: {game_state.player_action}
  Current situation: {game_state.npc_situation}
  How {npc.name} learned of the player's action: {game_state.npc_knowledge}

NPC — {npc.name}:
  Who they are: {npc.situation}
  What they want: {npc.want}
  What they stand to lose: {npc.stake}
  Who they know / what they have access to: {npc.network}

Generate a world texture quest where {npc.name} approaches the player.
This quest has no connection to {game_state.main_quest}.
Do not reference {game_state.main_quest} in the quest output.
Do not provide intel about the main story.
Do not escalate any stakes beyond {npc.name}'s personal situation.

The player's action reached {npc.name} through the world — that is the only
required connection. The quest is entirely about {npc.name}'s life.

Include exactly these five things:

1. HOW the player's action reached {npc.name} — through what specific channel,
   and what {npc.name} concluded from it. This should feel incidental, not fated.
   The action is why {npc.name} knows to approach this specific person. It is
   not why the quest exists.

2. WHAT {npc.name}'s actual situation is — not a summary, but what it feels
   like from the inside. What {npc.name} is dealing with right now, in concrete
   terms. This is the emotional center of the quest. It must be interesting
   without any reference to the main story.

3. WHAT {npc.name} needs from the player — specific and shaped by their want.
   Must connect to the kind of capability the player demonstrated in
   {game_state.player_action}.

4. WHAT it costs the player to help — real cost, not a token errand.

5. WHAT STAYS UNRESOLVED — after the player helps, what is still true about
   {npc.name}'s situation. The deeper problem — what they stand to lose — does
   not go away when the immediate need is met. Name it in one sentence. This
   is what makes the world feel inhabited rather than designed.

Keep it grounded and specific. This quest should feel like it would exist in
this world regardless of the main story. The player's instinct after accepting
should be: "this has nothing to do with my main objective — I'm just helping
someone."
```

---

### Example — Template 4 Filled

**NPC: Nadia**
```json
{
  "name": "Nadia",
  "situation": "Cartographer on commission from the eastern merchant guild.
    She has been hired to update the district map after the recent guard
    checkpoint reconfiguration — new routes, new restricted zones, new
    administrative boundaries. She is three weeks into a six-week commission
    and one street short of completing the eastern section.",
  "want": "Walk down Reiner Alley with her instruments and finish the survey.
    The alley was reclassified as restricted after the reconfiguration. She
    does not know why. She has been turned away at the entry checkpoint twice.
    She needs either access or someone who can tell her what changed.",
  "stake": "Her apprenticeship with the guild ends in eight weeks. The
    commission was supposed to be her exit credential — proof of completed
    work for the guild master's reference letter. He is the only person in
    the city qualified to vouch for her cartography, because her previous
    mentor died before her apprenticeship concluded. She has not told the
    guild master that she cannot complete the commission. She goes back to
    the alley checkpoint every other day because she does not know what
    else to do.",
  "network": "Has mapped seven of the nine eastern district sections over
    three weeks — knows the current layout of every public street, courtyard,
    and passage in the district except the restricted alley. Has spoken with
    checkpoint guards, shop owners, and market stall operators while
    surveying. Knows which streets have changed since the last official map."
}
```

**Game state:**
```json
{
  "main_quest": "Rescue Elena from the Syndicate",
  "player_action": "Burned the Syndicate's supply manifest rather than handing
    it to the resistance",
  "npc_name": "Nadia",
  "npc_situation": "She was at the checkpoint near the cloth merchant's warehouse
    when word spread that someone had destroyed a Syndicate document and slipped
    the district before they could be caught. She is not interested in the
    politics. She is interested in anyone who knows how to move through checkpoints
    this district has decided to make difficult.",
  "npc_knowledge": "Overheard two guards at the warehouse checkpoint discussing
    the incident — they were annoyed about the extra watch shift it triggered.
    She does not know who destroyed the manifest or why. She knows the person
    got through."
}
```

**Filled prompt:**
```
You are a quest designer for a narrative RPG.

GAME STATE:
  Main quest: Rescue Elena from the Syndicate
  Player's last action: Burned the Syndicate's supply manifest rather than
    handing it to the resistance
  Current situation: She was at the checkpoint near the cloth merchant's
    warehouse when word spread that someone had destroyed a Syndicate document
    and slipped the district before they could be caught. She is not interested
    in the politics. She is interested in anyone who knows how to move through
    checkpoints this district has decided to make difficult.
  How Nadia learned of the player's action: Overheard two guards at the
    warehouse checkpoint discussing the incident — they were annoyed about the
    extra watch shift it triggered. She does not know who destroyed the manifest
    or why. She knows the person got through.

NPC — Nadia:
  Who they are: Cartographer on commission from the eastern merchant guild.
    Hired to update the district map after the recent checkpoint reconfiguration.
    Three weeks into a six-week commission and one street short of completing
    the eastern section.
  What they want: Walk down Reiner Alley with her instruments and finish the
    survey. The alley was reclassified as restricted. She has been turned away
    at the entry checkpoint twice and does not know why it changed.
  What they stand to lose: Her apprenticeship ends in eight weeks. The commission
    is her exit credential — the guild master's reference letter. He is the only
    qualified person to vouch for her because her previous mentor died before
    her apprenticeship concluded. She has not told him she cannot complete the
    commission. She goes back to the alley checkpoint every other day because
    she does not know what else to do.
  Who they know / what they have access to: Has mapped seven of nine eastern
    district sections — knows the current layout of every public street,
    courtyard, and passage except the restricted alley. Has spoken with
    checkpoint guards, shop owners, and market stall operators throughout.
    Knows which streets have changed since the last official map.

Generate a world texture quest where Nadia approaches the player.
This quest has no connection to Rescue Elena from the Syndicate.
Do not reference the main quest in the quest output.
Do not provide intel about the main story.
Do not escalate any stakes beyond Nadia's personal situation.

[...five-part output instructions as above...]

The player's instinct after accepting should be: "this has nothing to do with
my main objective — I'm just helping someone."
```

---

## Template Summary

| Template | Emotional center | Load-bearing field | Recognition type |
|---|---|---|---|
| Main Quest Escalation | Main quest recontextualized | `npc.network` | "Wait — does that mean...?" |
| NPC Personal Crisis | NPC's stake | `npc.stake` | "I'm helping because of who she is" |
| Player Choice Callback | Past player choice | `player_history` | "How did they know that?" |
| World Texture | NPC's situation on its own | `npc.situation` + `npc.stake` | "This world has people in it" |

**Schema gap surfaced by Template 3:**
The base 5-field game state has no `player_history` field. Template 3 requires
it. This is the data the Step 6 fact database must store and serve. Until Step 6
is built, Template 3 can be tested by manually constructing the history array.

---

## Next Step

Update quest-generator-v2.py to accept a `template` parameter
(`escalation` | `crisis` | `callback` | `texture`) and route to the
appropriate prompt. Template 3 also requires the game state to accept a
`player_history` array.
