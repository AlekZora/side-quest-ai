## What the System Is

A minimal world-state consistency layer for AI-driven 
quest generation. Solves four problems simultaneously:
grounding, simulator layer, persistent memory, and 
design language.

## Division of Labor

Humans create: characters, world, emotional spine, 
NPC situations.
System generates: collisions between NPC situations 
and player history, contextual quests, playthrough variation.

## Who It Helps

World builders who lack the resources to hire large 
writing teams can now realize their full creative vision.
The creative work stays human. The mechanical production 
work becomes automated.

## The One Sentence

We don't replace world builders — we make them more 
powerful.

## Design Philosophy

Stephen King does not plot his novels. 
He creates characters with full inner lives and puts them 
in situations. The story emerges from who they are.

Our system applies this philosophy to games. World builders 
create fully realized NPC characters with situations. 
The system puts those characters in contact with player 
history. The quest emerges from who the character is, 
not from what the writer pre-planned.

The writer's job: know your characters deeply.
The system's job: generate the collisions.

## The Enterprise AI Connection

The fact database and constraint validator in this 
project solve the same architectural problem as 
enterprise AI automation:

- Tacit knowledge problem → NPC knowledge that 
  exists nowhere explicit
- Skills files → NPC schema + fact database rows
- Company brain → the world state extraction system
- Grounded agent execution → quest generator that 
  only references verified facts

The architecture that prevents hallucination in 
enterprise AI agents is the same architecture that 
prevents hallucinated quests in this game. 
Same problem, different domain.

## Scope Boundary

Scope boundary: the system generates side quests that 
enrich the world around the main story. It does not 
touch main story structure. NPCs can respond to player 
history but cannot resolve main story beats. This 
boundary is enforced by the constraint layer and is 
a deliberate design decision, not a limitation.
