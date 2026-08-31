"""Long-form descriptions for all twenty-four skills.

Two paragraphs each, in the Disco Elysium shape:

  ABOUT - what this part of you is for, and what it sounds like when it
          speaks. Written as a character sketch rather than a stat blurb,
          because that is what these are: twenty-four small people who
          live in your head and disagree.

  RANGE - what a high score and a low score actually do to your behaviour.
          Both ends are written as real outcomes with real costs. A high
          skill is never simply better - it is louder, and a loud skill
          takes the wheel at moments when a quieter one would have been
          right. This is the paragraph that should make a player think
          twice before dumping twelve points into one attribute.

Kept out of skill_checks.py deliberately: that module is the dice, and it
is read by people debugging the dice. This is prose, and it is read by
people deciding who to be.
"""

from __future__ import annotations

#: skill id -> (about, range)
SKILL_DETAIL: dict[str, tuple[str, str]] = {
    # ---------------------------------------------------------------- INTELLECT
    "LOGIC": (
        "The part of you that insists the world is required to make sense. "
        "Logic assembles a case out of what is actually in front of it, "
        "objects when two facts cannot both be true, and does not care "
        "whose feelings are involved in the contradiction. In Silvora "
        "Reefs it is doing overtime and drawing no conclusions, because "
        "this is a parish where a corridor can be longer than the building "
        "it is inside and nobody has filed a complaint.",
        "High Logic hands you the contradiction before you have finished "
        "reading the room — the number that does not add up, the alibi with "
        "a seam in it — and it will keep handing it to you at three in the "
        "morning. Taken far enough it becomes a man who cannot accept an "
        "answer that works, only one that is consistent, which is a bad "
        "trait in a town built out of jokes. Low Logic lets you walk past "
        "an impossibility without flinching, which is restful and "
        "occasionally fatal: the seam stays invisible, the sums are "
        "somebody else's problem, and you will take a comfortable lie home "
        "with you and sleep soundly next to it."
    ),
    "RHETORIC": (
        "Argument as a load-bearing structure. Rhetoric builds the case, "
        "finds the joint in the other person's position, and applies "
        "pressure with a smile on. It is not honesty and it is not lying; "
        "it is construction, and like all construction it can be used to "
        "shelter somebody or to drop something heavy on them.",
        "High Rhetoric wins rooms. You will find the sentence that turns a "
        "hostile witness civil, and you will also find the one that ends a "
        "friendship in eleven words, and the skill will not distinguish "
        "between them because winning is the only thing it was built to "
        "measure. At the top end people stop telling you things because "
        "they have learned that anything they say will be returned to them "
        "sharpened. Low Rhetoric means you say the true thing plainly and "
        "watch it land wrong, over and over — though a man who cannot "
        "argue is occasionally trusted for exactly that reason, and gets "
        "told things a cleverer man would have been protected from."
    ),
    "ETYMOLOGY": (
        "Words have histories, and in this parish the histories are still "
        "load-bearing. Etymology tracks where a name has been before it "
        "arrived here — what it used to mean, what it got shortened from, "
        "which pun it is quietly the punchline of. Silvora Reefs is a town "
        "where the names came first and the things grew to fit them, which "
        "makes this the closest thing the investigation has to a map.",
        "High Etymology turns signage into evidence. You will hear the "
        "second meaning under a shop name and follow it to something real, "
        "and you will occasionally derail an urgent conversation for four "
        "minutes over the root of a word nobody else has noticed. Pushed "
        "high it becomes a conviction that the name explains the thing, "
        "which in most towns is a delusion and here is only mostly true. "
        "Low Etymology leaves the parish as a list of silly names — you "
        "will laugh at the jokes and never notice that the jokes are "
        "instructions."
    ),
    "ENCYCLOPEDIA": (
        "Everything you have ever read, still settling, occasionally "
        "surfacing something relevant. Encyclopedia supplies the fact — "
        "the date, the precedent, the technical term for what is happening "
        "to that wall — along with three adjacent facts nobody requested "
        "and one that turns out to matter more than the first.",
        "High Encyclopedia means context arrives unbidden and mostly "
        "useful: you know what green flame indicates, what a vault plate "
        "is normally struck with, why an inn with weather in it has "
        "precedents. It also means you will explain this at length to a "
        "man who asked a simple question, and the room will drift, and the "
        "moment will pass. Low Encyclopedia leaves you present but "
        "unfurnished — you will see clearly and have nothing to compare it "
        "to, which occasionally means you meet the thing itself rather "
        "than a memory of something like it."
    ),
    "VISUAL_CALCULUS": (
        "The reconstruction. Visual Calculus takes the room as it stands "
        "and runs it backwards: the angle of the spray, the drag mark, the "
        "clean rectangle in the dust with four round gaps at the corners. "
        "It does not care what anybody says happened. It cares what the "
        "geometry will support.",
        "High Visual Calculus gives you the event as a diagram — where "
        "people stood, what was lifted rather than dragged, which way the "
        "thing came down — and it is very hard to argue with, including "
        "when it is wrong, because a reconstruction feels like a memory "
        "once it has been assembled. Low Visual Calculus leaves the scene "
        "as scenery: a mess is just a mess, dust is just dust, and the "
        "shape of the absent machine on your own desk stays a smudge you "
        "have been meaning to wipe."
    ),
    "CONCEPTUALISATION": (
        "What the thing is *about*. Conceptualisation reads composition, "
        "motif and intent — the difference between a detail and a symbol, "
        "between a coincidence and a decision by somebody with a pen. It "
        "is the art critic in the back of the skull, and in a world that "
        "turns out to be written it is closer to a forensic instrument "
        "than it has any right to be.",
        "High Conceptualisation shows you the authorship: three "
        "recurrences become a motif, a desk made of a door becomes a "
        "statement, and you begin to see the shape of the person arranging "
        "all of it. It also encourages you to find meaning in a stain, and "
        "there is no internal check that tells you which of the two you "
        "are doing. Low Conceptualisation keeps you literal and safe from "
        "your own pattern-matching — the desk is a desk, the joke is a "
        "joke — and the largest structure in the case goes on standing "
        "over you, unremarked."
    ),
    # ------------------------------------------------------------------- PSYCHE
    "EMPATHY": (
        "Reading the person rather than the statement. Empathy watches the "
        "pause before the answer, the hand that goes to the counter, the "
        "cheerfulness applied slightly too thickly, and reports what is "
        "being protected. It is the difference between hearing what "
        "somebody said and knowing what it cost them.",
        "High Empathy makes the parish legible and expensive. You will "
        "know that the bellhop is terrified of the ceiling, that the cook "
        "feeds people because of one specific afternoon, that a man is "
        "lying to keep somebody else out of it — and knowing that makes it "
        "very difficult to press an advantage you can see is a wound. Low "
        "Empathy leaves people as sources: you will get the information "
        "and miss the person, close doors you did not notice were open, "
        "and be surprised by what people do next roughly as often as they "
        "are."
    ),
    "INLAND_EMPIRE": (
        "The hunch that arrives fully dressed and declines to show its "
        "working. Inland Empire lets objects have opinions, lets a room "
        "have an intention, and hands you conclusions that no chain of "
        "reasoning connects to anything. It is either the deepest "
        "instrument you own or a man talking to a lamppost, and Silvora "
        "Reefs is not going to settle that argument for you.",
        "High Inland Empire will tell you the truth about this town before "
        "any other skill can get near it, because the truth about this "
        "town is not arrived at by reasoning. It will also tell you things "
        "that are simply not so, in exactly the same confident voice, with "
        "no label distinguishing the two. Low Inland Empire keeps you in "
        "the world as reported: nothing whispers, nothing warns you, and "
        "the several occasions on which a mirror was trying to get your "
        "attention will pass entirely unrecorded."
    ),
    "AUTHORITY": (
        "Standing, and the willingness to spend it. Authority is the voice "
        "that ends a conversation, the refusal to be moved along, the "
        "assumption — usually unearned — that you are the one asking the "
        "questions here. It is more fragile than it sounds, and it is most "
        "fragile exactly when you need it most.",
        "High Authority gets you through doors and gets you obeyed, and it "
        "escalates: every challenge becomes a thing that must be answered, "
        "and a man with a great deal of Authority and a poor grasp of when "
        "to spend it will pick a fight with an alligator in a suit over a "
        "point of procedure. Low Authority means you get talked over, "
        "moved past, and quietly not taken seriously — which is its own "
        "kind of access, because nobody bothers to manage a man they have "
        "already dismissed."
    ),
    "VOLITION": (
        "The part that holds the line. Volition is resolve against "
        "despair, against a very good argument, against the drink that "
        "would genuinely help. It is not optimism. It is the structural "
        "member that keeps the rest of you from being talked out of "
        "existing, which in this particular investigation is not a "
        "metaphor.",
        "High Volition keeps your morale where you put it and makes you "
        "very hard to unmake — you can be told, persuasively, by somebody "
        "with standing, that you are not real, and go on operating anyway. "
        "It can also harden into refusing a true thing simply because "
        "accepting it would cost something. Low Volition leaves you "
        "porous: the town's suggestions get in, morale drains faster than "
        "it fills, and an argument you cannot answer becomes an argument "
        "you begin to live inside."
    ),
    "VOX_POPULI": (
        "The parish thinking about itself, briefly audible through you. "
        "Vox Populi is not telepathy and is not deduction; it is the "
        "sense of the other Reefers going about their business in rooms "
        "you are not in — the crate set down, the squeegee arcing, the "
        "same worried glance at the same fog, four streets over, right "
        "now.",
        "High Vox Populi gives you the town as a single organism and "
        "occasionally shows you a scene you have no business witnessing, "
        "which is the closest this game comes to handing you an answer for "
        "free. It also makes solitude difficult: a man who can feel the "
        "whole parish at once has a hard time locating where he stops. Low "
        "Vox Populi leaves Silvora Reefs as a series of separate "
        "rooms containing separate strangers, and the fact that all of "
        "them are quietly doing the same thing will never once come into "
        "focus."
    ),
    "SUGGESTION": (
        "Charm with a destination. Suggestion is the art of leading "
        "somebody to a conclusion and letting them arrive at it themselves, "
        "pleased, believing they walked. Where Rhetoric wins the argument "
        "and Authority ends it, Suggestion arranges for there not to have "
        "been one.",
        "High Suggestion opens people who were closed, gets you the thing "
        "that was not going to be offered, and leaves everyone feeling "
        "rather good about it. The cost is that you will do this "
        "reflexively, including to people who deserved a straight "
        "question, and you will lose track of which of your friendships "
        "are constructions. Low Suggestion means you ask directly and take "
        "the answer you get — a blunter instrument, but the people who do "
        "open up to you have genuinely chosen to, and that turns out to "
        "matter later."
    ),
    # ---------------------------------------------------------------- FORTITUDE
    "PHYSIQUE": (
        "The body you have neglected in favour of the sentence you were "
        "composing. Physique is raw physical capacity — carrying, forcing, "
        "enduring, staying upright — and it has been keeping this "
        "operation running on very little support and no thanks "
        "whatsoever.",
        "High Physique means doors, weights and distances stop being "
        "obstacles and the harbour cold stops being a factor; it also "
        "makes force the first available answer, and an available answer "
        "gets used. Low Physique makes the town physically expensive — "
        "stairs are a negotiation, the knee has opinions, and some things "
        "will simply remain shut — which pushes you toward talking your "
        "way through, and the parish tends to remember men who talked "
        "rather than men who shoved."
    ),
    "ELECTROCHEMISTRY": (
        "Appetite, in the round: gin, donuts, smoke, the fine greens, the "
        "second drink and the argument for it. Electrochemistry "
        "volunteers enthusiastically at every opportunity and is almost "
        "never correct, and the once or twice it is correct are the "
        "reason it never stops being asked.",
        "High Electrochemistry reads pleasure and vice like a map — you "
        "will know what a man is drinking and why, and what will be "
        "available two streets over, and it will keep proposing that you "
        "find out personally. Some of the town's strangest and most "
        "useful revelations are on the other side of a bad decision, and "
        "this is the skill that makes them. Low Electrochemistry keeps "
        "you sober and clear and slightly outside it: the parish's "
        "pleasures stay other people's pleasures, and the doors that open "
        "only for a man who said yes stay closed."
    ),
    "PAIN_THRESHOLD": (
        "How much you can carry without setting it down. Pain Threshold "
        "covers the injury and the insult with the same equipment, and it "
        "is the reason you walked out of the harbour rather than being "
        "found in it. It does not make things stop hurting. It makes "
        "hurting a thing you can continue through.",
        "High Pain Threshold lets you take the hit, the humiliation and "
        "the long cold walk and keep going, and it gets *better* the worse "
        "your condition gets — it is the one part of you that reads damage "
        "as information. It will also let you push a body that should have "
        "been stopped hours ago, and it does not send a warning first. Low "
        "Pain Threshold means damage lands and stays landed: you will "
        "stop, you will flinch visibly, people will see it — and stopping "
        "when you should stop is a skill that men with a high score in "
        "this never get to practise."
    ),
    "SHIVERS": (
        "Silvora Reefs, arriving through the skin. Shivers is the town "
        "itself — the green flame leaning away, the fog with rotors in it, "
        "the temperature of a street that has not been walked yet tonight. "
        "It reports on the parish as a living thing with a mood, and in "
        "this parish that is a literal description rather than a poetic "
        "one.",
        "High Shivers means the town talks to you: you will know the "
        "weather before it turns, sense the streets you have not yet "
        "reached, and receive the occasional flat statement about what is "
        "happening elsewhere that no other skill could have provided. "
        "Carried far enough, the boundary between what you are noticing "
        "and what the town is doing becomes hard to police. Low Shivers "
        "leaves the parish as scenery and weather as weather — you will "
        "be dry, and sensible, and the several occasions on which Silvora "
        "Reefs tried to warn you will register as a draught."
    ),
    "HALF_LIGHT": (
        "The oldest voice in the building. Half Light handles threat: it "
        "counts the exits, tracks the man at the edge of vision, and wants "
        "to act before the sentence finishes. It is frequently wrong, it "
        "is never quiet, and once every so often it is the only reason a "
        "man is still standing.",
        "High Half Light keeps you alive in the moments that move quickly "
        "— you will have registered the danger while everyone else is "
        "still being polite about it — at the cost of a running commentary "
        "of threat where there is none, and a standing recommendation to "
        "escalate. It makes fear into fuel and hands you the option of "
        "violence early and often. Low Half Light leaves you calm in rooms "
        "you should be reading more carefully: you will be the last to "
        "notice, the slowest to move, and the least likely to swing at "
        "somebody who did not deserve it."
    ),
    "SEA_LEGS": (
        "Balance, in a harbour town that does not hold still. Sea Legs is "
        "the body's quiet negotiation with a floor that is off-level, a "
        "room drifting four inches to the left on a cycle, and a night "
        "that has already gone on too long. It handles the literal storm "
        "and the other kind with the same set of knees.",
        "High Sea Legs means the parish's instability stops registering as "
        "a problem — you will ride a moving room, hold a drink, take the "
        "wet stone at speed, and stay upright through revelations that put "
        "other men on the floor. It can also make you comfortable in "
        "conditions that ought to alarm you, and comfort is how people "
        "stay somewhere. Low Sea Legs makes Silvora Reefs a hostile "
        "surface: you will stumble, you will need the wall, and you will "
        "be very aware at all times that the ground here is not being "
        "entirely straight with you."
    ),
    # ---------------------------------------------------------------- MOTORICS
    "SAVOIR_FAIRE": (
        "Knowing how, and knowing when. Savoir Faire is timing, sleight "
        "and the unremarked exit — the pocket entered without ceremony, "
        "the room left before the question, the half-second in which "
        "nobody happens to be looking at you. It is grace under "
        "observation, and the good sense to stop talking.",
        "High Savoir Faire lets you move through the parish without "
        "leaving a wake: you take the moment, you are already gone, and "
        "the room reconstructs events without you in them. It also "
        "encourages the elegant solution over the honest one, and an "
        "elegant solution has a way of requiring a second one later. Low "
        "Savoir Faire means you are visible and slightly clumsy in every "
        "room you enter — you will knock something, you will be noticed "
        "leaving — and being obviously incapable of sleight is a "
        "surprisingly effective way of being trusted with things."
    ),
    "PERCEPTION": (
        "What the room is doing while you are looking at one part of it. "
        "Perception is the sweep — the detail at the edge, the sound "
        "underneath the sound, the object that is a slightly different "
        "colour than it was when you came in. It supplies raw noticing, "
        "and leaves the interpreting to whoever else is awake.",
        "High Perception means the world hands you more than you asked "
        "for, constantly: the ring under the cup that is older than the "
        "cup, the rhythm under the room noise that is not machinery. Every "
        "room becomes dense, and some of that density is nothing at all, "
        "and there is no marker on which is which. Low Perception gives "
        "you the room as summarised — clean, legible, and missing the "
        "specific small wrong thing that the entire case turns on, which "
        "will still be sitting there the next three times you walk past "
        "it."
    ),
    "COMPOSURE": (
        "Not showing it. Composure is posture, the level voice, the tell "
        "you decline to give — what is left of dignity, deployed "
        "tactically. It governs what other people are able to read off "
        "you, which in a parish of watchers is most of what you actually "
        "control.",
        "High Composure keeps your face your own: the shock does not "
        "land visibly, the lie is not written on you, and people tell you "
        "things because they cannot tell how you are taking them. Held "
        "too tightly it becomes a man who never lets anything show, "
        "including to people who needed to see something. Low Composure "
        "puts everything on the surface — every flinch is public and every "
        "reaction is evidence — and there are rooms in this town where "
        "being visibly shaken is the only thing that gets a person to "
        "soften toward you."
    ),
    "REACTION_SPEED": (
        "The fast thing, arriving before deliberation gets a vote. "
        "Reaction Speed catches the falling glass, takes the half-second "
        "where a face forgets to be careful, and answers before the "
        "silence has had a chance to become meaningful. It is reflex "
        "rather than thought, and it is right about as often as reflexes "
        "are.",
        "High Reaction Speed gets you the tell — the pause before the "
        "answer, the flicker of arithmetic behind somebody's eyes — and "
        "gets your hands to things before they hit the floor. It also "
        "answers questions you would have preferred to think about, and "
        "commits you to positions your slower skills would have argued "
        "against. Low Reaction Speed means the moment is over before you "
        "are in it: the glass breaks, the expression is gone, and you "
        "arrive at exactly the right response about four seconds after it "
        "would have worked."
    ),
    "HAND_EYE": (
        "Precision of the hands. Hand-Eye is the steady pour, the exact "
        "cut, the waterlogged page separated from its neighbour without "
        "turning three of them into confetti. Small, physical, and "
        "responsible for a surprising proportion of the evidence in this "
        "case surviving contact with you.",
        "High Hand-Eye means delicate things stay intact and difficult "
        "physical operations simply work — the ruined notebook gives up "
        "its three legible pages, the mechanism yields, the throw lands. "
        "It tends toward confidence with other people's fragile property. "
        "Low Hand-Eye makes the physical world faintly hostile to detail: "
        "you will tear what you meant to open and drop what you meant to "
        "examine, and some evidence in Silvora Reefs is only going to "
        "tolerate being handled once."
    ),
    "INTERFACING": (
        "Machines, locks, mechanisms, and the things a typewriter knows. "
        "Interfacing understands objects by their working parts rather "
        "than by their names — which side the mechanism is on, what the "
        "footprint means, how a thing expects to be operated by somebody "
        "who belongs here. In a town where an absent machine is the "
        "central fact, this is not a niche competence.",
        "High Interfacing gets you inside things: the vault whose "
        "mechanism is on the wrong side, the footprint that is a "
        "typewriter's rather than a filing cabinet's, the lock that was "
        "designed to be opened from within. Objects give up their "
        "purposes to you, and you will trust a mechanism's account of "
        "itself over a person's, which is usually but not always correct. "
        "Low Interfacing leaves machinery opaque and nameable only from "
        "the outside — a box is a box, a lock is shut — and the specific "
        "shape of the thing that is missing from your desk stays a "
        "rectangle in the dust."
    ),
}


def about(skill: str) -> str:
    return SKILL_DETAIL.get(skill, ("", ""))[0]


def behaviour(skill: str) -> str:
    return SKILL_DETAIL.get(skill, ("", ""))[1]


def paragraphs(skill: str) -> list[str]:
    detail = SKILL_DETAIL.get(skill)
    return [part for part in detail if part] if detail else []
