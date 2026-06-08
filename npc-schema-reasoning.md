# NPC Schema — Reasoning

Derived from game-state-schema-reasoning.md and test-states.json 
v1. This document explains the relationship between the NPC 
definition schema (static, world-builder-authored) and the game 
state schema (dynamic, runtime-populated), and specifically how 
the NPC schema addresses the sim-to-feel gap.

---

## The distinction that drives the schema design

The game state schema contains two NPC fields:
- `npc_situation` — the NPC's current problem, dynamic
- `npc_knowledge` — what the NPC knows about the player's 
  action, dynamic per interaction

Both are runtime values. They change with every interaction. 
The NPC schema is different: it contains only what is true 
about the NPC before the player has done anything. The world 
builder fills it once. The game state draws on it.

This means the NPC schema cannot replicate `npc_situation` 
or `npc_knowledge` — it must contain the static material 
that those fields are constructed from.

---

## The 5 fields and what they each do

### 1. `name`
**Contains:** The NPC's name, as a standalone string.

**Why necessary:** Same reason as in the game state schema — 
the generator references the NPC by name in prompt 
construction and in dialogue. Keeping it separate avoids 
parsing. It also functions as the primary key linking this 
static record to runtime game state instances: when the 
game state populates `npc_name: "Petra"`, the system can 
look up the full NPC definition and inject relevant fields.

**Example:** `"Petra"`

---

### 2. `situation`
**Contains:** The NPC's persistent, ongoing circumstance — 
who they are and what they are doing in the world before 
any player interaction.

**Why necessary:** This is the static core that the game 
state's `npc_situation` expands dynamically at runtime. In 
the test states, `npc_situation` values like "sick daughter 
needs medicine from eastern district, blocked by guards" 
combine a static personal situation (daughter is sick) with 
a dynamic element (access is currently blocked). The `situation` 
field in the NPC schema provides the static part.

Without this field, the NPC has no grounded existence 
before the player arrives. They would be a blank canvas 
waiting to be made relevant by the player's actions. The 
`situation` field is the evidence that the world was 
already moving.

It must describe a concrete role or activity, not a 
personality type. "Former Syndicate bookkeeper who now 
keeps accounts for three merchants and has been forging 
records" is situation. "Pragmatic, cautious, morally 
ambiguous" is not — those are outputs from having a 
situation, not a situation itself.

**Example:** `"Former Syndicate bookkeeper, now keeps 
accounts for three eastern market merchants. Has been 
quietly forging transaction records to cover the 
movements of resistance members."`

---

### 3. `want`
**Contains:** The concrete, achievable goal the NPC is 
actively pursuing.

**Why necessary:** The `want` determines what the NPC 
asks the player to do. Without it, the generator defaults 
to generic quests ("help me with my problem") because it 
doesn't know what form of help this NPC actually needs.

The crucial constraint: `want` must be an active pursuit, 
not a trait. "She values safety" tells the generator 
nothing actionable. "She is trying to keep the forgeries 
small enough to remain deniable" tells the generator 
exactly the kind of task she would ask for and the kind 
of reward she would offer.

The `want` also defines the failure mode the NPC is 
trying to avoid — which is where the player's action 
intersects. Petra's want is to maintain deniability. 
If the player burned the Syndicate manifest (State 4's 
action), a Syndicate audit will follow. Her forgeries 
won't survive an audit. Her want is now under direct 
threat from the player's action, and the quest is the 
collision.

**Example:** `"Maintain distance from both sides — keep 
the forgeries small and deniable, keep the merchants 
satisfied enough not to look closely at their books."`

---

### 4. `stake`
**Contains:** What this NPC stands to lose if things go 
wrong — their emotional core; the thing that makes them 
a person rather than a type.

**Why necessary:** This field is the direct answer to 
the sim-to-feel gap.

World-models.md poses the question: "Is there an 
analogous 'sim-to-feel' gap in games where a structurally 
accurate world model produces quests that are logically 
correct but emotionally flat?"

The answer is yes, and `stake` is the field that closes 
it. A world model can track that Petra has been forging 
records. That fact alone produces a logically coherent 
quest: "Petra needs help covering up her forgeries before 
an audit." That quest is correct. It is also flat. It 
could be about any cautious person in any dangerous 
situation.

The `stake` adds: she has a brother, Andrei, who still 
works for the Syndicate. If the investigation finds her 
forgeries, it will reach him. She would be destroying 
her only remaining family to protect people she barely 
knows. She hasn't spoken to him in three months because 
every conversation feels like a goodbye she hasn't 
explained.

With that context the generator produces something 
different: a quest about a woman who has been sitting 
with an impossible choice, who now has to make it faster 
than she planned, and who will ask the player for help 
in a way that reveals she's not doing this for herself.

The `stake` must name something specific and irreplaceable: 
a person, a relationship, an identity, not an abstraction. 
"Her freedom" is not a stake. "Her brother Andrei" is.

Looking at the test state NPCs retroactively, every one 
of them had an implicit stake that made them feel human:
- Mira: her daughter's life
- Tomás: his uncle's reputation and his own family 
  belonging
- Sera: her brother's survival and her own powerlessness 
  to help him
- Voss: his soldiers who died because of the player's 
  choice
- Daria: her child's safety

None of the test states included an explicit `stake` 
field — it was embedded in `npc_situation`. The NPC 
schema makes it explicit, which forces the world builder 
to define it deliberately rather than hoping it emerges 
from the situation description.

**Example:** `"Her brother Andrei still works as a 
junior clerk for the Syndicate. If her forgeries are 
discovered, the investigation will reach him regardless 
of what he knew."`

---

### 5. `network`
**Contains:** Who the NPC knows, interacts with regularly, 
and has access to information through.

**Why necessary:** The game state's `npc_knowledge` field 
(the grounding constraint) is only believable if there's 
a specified information pathway. Without the `network` 
field, the generator either invents implausible channels 
("she somehow knew") or the world builder has to specify 
knowledge manually for every game state instance.

The `network` field makes `npc_knowledge` generatable: 
given that Petra processes accounts for the eastern 
market merchants and her brother's supervisor is a 
regular customer, the generator knows what information 
could plausibly reach her. If the player bribes the 
eastern gate guard, Petra hears about it through the 
grain merchant, whose supply deliveries depend on that 
gate. If the player burns the Syndicate manifest, 
Petra knows because the manifest covered supply routes 
that passed through the accounts she maintains.

`Network` also defines what the NPC can offer as a 
reward. A bookkeeper's network includes financial records, 
information about transactions, and relationships with 
merchants. A resistance commander's network includes 
safe houses and intelligence contacts. The generator 
needs to know which before it can produce a grounded 
reward.

The field must be concrete — named roles, locations, 
relationships. Not "she knows many people in the market" 
but "she processes accounts for the grain merchant, the 
cloth trader, and the apothecary, and sees Syndicate 
supply purchases made through front businesses."

**Example:** `"Processes accounts for the grain merchant, 
the cloth trader, and the apothecary. Her brother's 
Syndicate supervisor is a regular at the grain merchant."`

---

## Is 5 fields enough?

**Yes — for a world builder creating NPCs before player 
interaction.**

The 5 fields give the generator everything it needs to 
produce a quest through this NPC that:
- Has a grounded, believable situation (situation)
- Asks the player for something specific (want)
- Feels like it comes from a person with something at 
  stake (stake)
- Has a plausible information channel (network)
- Can be addressed directly (name)

Every one of the 5 test state NPCs could have been 
defined with this schema. The schema would have made 
their emotional weight explicit rather than emergent.

---

## What breaks with fewer

**4 fields — drop `name`:**
Minor loss. Embeddable in `situation`. But dropping it 
forces the generator to parse the NPC's name from a 
description, which degrades prompt construction and 
breaks the primary key link to game state records.

**4 fields — drop `situation`:**
The NPC has no grounded existence. They're traits and 
goals without a life. The generator produces quests 
where the NPC feels like a function ("quest giver who 
needs help with forgeries") rather than a person who 
was doing something specific before the player arrived. 
The "world was already moving" feeling is gone.

**4 fields — drop `want`:**
The generator defaults to generic tasks. The quest ask 
becomes underspecified — the generator infers what the 
NPC would want from their situation, which produces 
plausible but not precise quests. Also breaks the 
collision mechanism: the `want` is what the player's 
action threatens or enables. Without it, the generator 
can't reliably produce the intersection that makes the 
quest feel specific.

**4 fields — drop `stake`:**
The sim-to-feel gap opens. The quest is logically correct 
but emotionally flat. The NPC feels like a puzzle to be 
solved rather than a person to be helped. Every NPC 
sounds the same because there is nothing that makes 
them specifically vulnerable. This is the most 
damaging drop for the experience goal.

**4 fields — drop `network`:**
The grounding constraint for `npc_knowledge` loses its 
foundation. The generator invents information channels 
or they become implausibly vague. The gossip propagation 
system (Step 5+) has nothing to build on. The reward 
grounding also degrades — the generator doesn't know 
what the NPC can plausibly offer.

---

## What naturally belongs in a 6th field

**`secret`:**
What the NPC knows but will not reveal unless the player 
has earned sufficient trust. This is distinct from 
`network` (which defines information access) and from 
`stake` (which defines what's at risk). The secret is 
what the NPC is actively concealing.

For Petra: she knows the name of the resistance contact 
who first paid her to forge records. She has never told 
anyone. If the resistance finds out she knows that name, 
they will consider her a liability.

The `secret` field is the natural foundation for the 
gossip propagation system — secrets are the currency 
of the NPC knowledge network. It's also what makes NPCs 
feel like they have more depth than they're showing.

It belongs at Step 5 (quest templates with player-choice 
callbacks) or Step 6 (fact database), not now. Including 
it at this step would require the consistency validator 
to track what each NPC has revealed to the player and 
when, which is infrastructure that doesn't exist yet. 
Adding `secret` to the NPC schema before the validator 
exists would create a field that the generator could use 
but that nothing would enforce — NPCs would reveal 
secrets at the wrong time or contradict prior reveals.

---

## How this schema connects to the sim-to-feel gap

World-models.md identifies the gap precisely: 
"a structurally accurate world model produces quests 
that are logically correct but emotionally flat."

The game state schema solves the structural problem: 
with the right 5 fields the generator produces quests 
that are grounded, specific, and internally consistent. 
A quest generated from State 4 (Commander Voss) cannot 
appear in any other playthrough. That's structural 
accuracy.

But structural accuracy is not the same as emotional 
resonance. A correct quest about covering up forgeries 
is not the same as a quest where the player understands 
that this woman is about to decide whether to protect 
her brother or the people she's been quietly helping 
for months.

The `stake` field is specifically designed to close 
that gap. It gives the generator something the world 
model cannot produce from facts alone: the weight of 
what's at risk for this specific person. The generator 
doesn't just know that Petra is in danger — it knows 
what danger means to her, which family member's face 
she sees when she thinks about being caught.

The sim-to-feel gap also explains why the `stake` 
field cannot be a structural category like "type: family" 
or "risk: medium." Structuring the emotional content 
kills it. The field has to be written in language that 
the generator can incorporate into dialogue and quest 
framing — specific, concrete, human-scale.

A structurally accurate world model tracks:
- Petra is forging records (entity: Petra, action: 
  forging, status: active)
- Andrei works for the Syndicate (entity: Andrei, 
  role: Syndicate clerk)
- If Petra is discovered, Andrei is at risk (causal 
  relationship)

Those facts are correct. The `stake` field is what 
transforms "Andrei is at risk" into "she would be 
destroying the only family she has left to protect 
people she barely knows." That transformation is what 
makes the quest feel personal rather than procedural.

---

## One-line summary

5 fields is the right number for this step: `situation` 
grounds the NPC in a life, `want` focuses the quest 
task, `stake` bridges the sim-to-feel gap, `network` 
makes knowledge plausible, and `name` enables clean 
reference. The natural 6th field — `secret` — belongs 
when the consistency validator exists to enforce it.
