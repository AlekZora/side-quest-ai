# Experience Goal — Side Quest AI System
*Created: 2026-06-04*

---

## The Experience Goal

The player feels a moment of disorienting recognition: the world has been paying attention to their specific story, not the generic one, and an NPC is now speaking directly to it. When this recognition occurs, the player's instinct is to retell it — the quest summary is the shareable artifact of that retelling.

---

## Why This Feeling Matters

This feeling is the only valid proof that the system works. Logical consistency, grammatical correctness, and thematic relevance are necessary but not sufficient — a well-written generic quest can have all three and still produce nothing. The test is whether recognition occurs, and recognition requires specificity: the quest must reference something this player did, in this playthrough, in a way that could not have appeared for any other player. When that happens, the player experiences what `information-asymmetry.md` calls retroactive recontextualization — they realize the world was tracking a choice they made without knowing the world was watching. That realization is a high-arousal spike. Per `emotional-memory.md`, it will be encoded deeply, recalled durably, and retold to others. The system's core claim — that generated quests can feel more personal than handcrafted ones — lives or dies in this moment.

The feeling also solves the sharing problem automatically. Per `recommendation-as-identity.md`, players share what they could not have authored themselves; per `self-expression-as-play.md`, the most engaging experiences are ones where the player's choices are visibly reflected back at them. A quest that produces recognition gives the player a story that is genuinely theirs — not "I played this game" but "I was at the market and this merchant came up to me because she somehow knew I'd let her brother take the blame at the council meeting, and now she needs..." — a story that no other player got, that the player can claim as autobiography, and that is shareable precisely because of its specificity. The viral mechanic is not a feature added on top of the system. It is what the experience goal produces naturally.

The recognition is only possible because a simulator layer exists beneath the generator — a world model tracking actual player history and NPC knowledge states; without it, the system produces a renderer: surface plausibility without grounded state, which is exactly why generic quests feel generic.

---

## The Test

Three observable player behaviors that would confirm the experience goal was achieved in a playtest:

1. **The player stops moving and reads the quest text carefully.** In playtesting, players skim quests that feel generic and read quests that feel personal. A full stop and careful read is the first reliable signal that recognition was triggered — the player senses something specific is being said to them.

2. **When asked "what just happened?" the player describes the NPC's reason for approaching them, not just the task.** Generic quest recall sounds like: "I have to go get something from the forest." Personal quest recall sounds like: "This blacksmith came up to me — she said she heard I'd spoken up for her brother at the checkpoint — and now her forge got robbed and she thinks the same guards did it." If the player leads with the trigger reason rather than the objective, the context landed.

3. **The player asks "how did they know that?"** This question is the ARG-mechanics signal (`arg-mystery-mechanics.md`, `apophenia.md`): productive pattern-finding. The player found a connection between their past behavior and the NPC's approach, recognized it as real rather than coincidental, and wants to understand the system behind it. A player who asks this question has experienced the recognition and is now curious about its source — exactly the engagement loop the system is designed to produce.

---

## The Failure Signal

Three observable player behaviors that would confirm the experience goal was NOT achieved:

1. **The player accepts the quest without reading it.** Skipping the quest text means the opening line — where the NPC's trigger reason must appear — did not hold attention. The player categorized it as a task to add to a list, not a response to their story. This is the clearest single failure signal.

2. **When asked "what just happened?" the player describes only the objective.** "I have to kill some bandits" or "I need to deliver a package" means the personal context either was not present, was not legible, or was present but generic enough to be invisible. Task-only recall is the verbal equivalent of not reading — the quest was processed as a chore.

3. **The player expresses confusion about why this NPC approached them specifically.** "What does this have to do with anything?" or "Why is she asking me?" means the trigger reason failed. The connection between the player's history and the quest giver is either implausible, invisible, or too thin to land. This failure mode is distinct from the first two — the player noticed something unusual but could not resolve it into recognition. Per `apophenia.md`, unresolvable patterns produce paranoid spiraling, not productive engagement. A confused player is worse than an indifferent one.
