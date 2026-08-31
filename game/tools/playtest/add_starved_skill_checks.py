#!/usr/bin/env python3
"""One-shot: give the three zero-active-check skills something to do.

VISUAL_CALCULUS, CONCEPTUALISATION and VOX_POPULI each had no active
check anywhere in the game. All three are recommended investments in
character creation and VISUAL_CALCULUS is an archetype's *signature* skill,
so a player could spend the +2 signature bonus on a stat that could never be
rolled. This adds five active checks for each, as new examinable objects.

Placement follows the ambient voices already written for these skills, so a
build that hears the whisper in a room can now also act on it there.

Idempotent: skips any object id that already exists.
"""
from __future__ import annotations
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOC = os.path.join(ROOT, "game", "content", "locations")
if not os.path.isdir(LOC):
    LOC = os.path.join(ROOT, "content", "locations")

# ---------------------------------------------------------------- VISUAL_CALCULUS
VC = {
"crash_site": {
 "id": "waterline",
 "name": "the waterline",
 "aliases": ["waterline", "water", "shallows", "sand", "marks", "shore"],
 "description": "The tide has been going out since before you woke and it has left the beach in the condition of a page somebody has written on and not yet torn up.\n\nThere are marks. There is the long smooth drag of the wreck settling, and there is a churn where the water works at it, and between the churn and the harbour wall there is a set of prints going up the sand, and they are yours, and they are walking.\n\nNot crawling. Not staggering. Walking, at an even stride, in a straight line, from the water to the wall.",
 "repeat": "The prints are still there. The tide has had four hours to take them and has taken everything else on this beach and left those.",
 "monocle": "Through the gold there is only one set of prints on this beach and they go the wrong way — down the sand, into the water, in a stride that does not vary — and the sea end of them is where the wreck is, and there is no return.",
 "passive": [
  {"skill": "PERCEPTION", "dc": 10,
   "text": "The stride does not shorten anywhere along its length. A man coming out of cold water up a wet slope shortens his stride. This one does not."},
 ],
 "effects": {
  "clue": {
   "id": "c_prints_walking",
   "title": "The prints are walking",
   "text": "The set of prints leading from the water to the harbour wall is yours, at an even stride, in a straight line. Not a crawl and not a stagger.",
   "beat": "crash", "tags": ["crash", "identity"], "source": "the waterline"}},
 "check": {
  "id": "crash:waterline:vis",
  "skill": "VISUAL_CALCULUS", "dc": 11, "kind": "white",
  "prompt": "The water has been going out for hours and it has left a record of everything that came up this beach. Read it backwards.",
  "success": "Run it in reverse. Stride length gives height and gives weight and both of them give you, so the prints are yours and that was never in question.\n\nWhat was in question is where they start, and they start four feet out from the low-water mark, in a place that was under three feet of water at the hour they were made, on sand that would not have held them.\n\nThey do not come out of the sea. They *begin*, at depth, mid-stride, already walking — and there is a second set that comes down to meet them at the wall, smaller, in a boot with a worn heel, and that set turns round and goes back up the hill in a hurry with the first set beside it.",
  "failure": "Stride, depth, the angle of the sand: it comes apart into three problems that will not sit still together, and the tide takes the near end of the evidence while you are working on the far end, which is the tide's whole method.",
  "success_effects": {
   "clue": {
    "id": "c_prints_begin_at_depth",
    "title": "The prints begin at depth, mid-stride",
    "text": "Reconstructed from stride and sand: your prints do not emerge from the sea. They begin four feet out, under three feet of water, already walking. A second set in a worn-heeled boot comes down to meet them and hurries back up the hill alongside.",
    "beat": "crash", "tags": ["crash", "identity", "manuscript"], "source": "the waterline"},
   "lucidity": 9},
  "failure_effects": {"exhaustion": 1}}},

"hang_hi": {
 "id": "dust_rectangle",
 "name": "the clean rectangle on the floor",
 "aliases": ["rectangle", "dust", "clean patch", "patch", "floor"],
 "description": "By the window, where the light would have been best, the boards carry a rectangle about the size of a bread oven in which the dust is a different age from the dust around it.\n\nFour small round depressions at the corners, pressed into the grain over a long enough period that the wood has taken them permanently. Whatever stood here stood here for years, and it was heavy, and it had feet rather than a base.",
 "repeat": "The rectangle is where it was. The dust inside it is still the wrong age and is getting no older.",
 "monocle": "Through the gold the rectangle is not empty. There is a machine in it, and it is being used, and the man using it has his back to you and does not turn round, and the light through the window falls on both of you at once from two different times of day.",
 "passive": [
  {"skill": "INTERFACING", "dc": 11,
   "text": "Four feet in a rectangle that size, at that spacing, bearing that much weight into softwood: a platen machine. Something with a carriage."},
 ],
 "effects": {
  "clue": {
   "id": "c_four_round_feet",
   "title": "Four round feet by the window",
   "text": "A rectangle of differently-aged dust by the Hang-Hi window, with four round depressions pressed permanently into the grain. Something heavy stood there for years, in the best light in the room.",
   "beat": "manuscript", "tags": ["manuscript", "typewriter"], "source": "the clean rectangle"}},
 "check": {
  "id": "hanghi:rect:vis",
  "skill": "VISUAL_CALCULUS", "dc": 11, "kind": "white",
  "prompt": "Something stood here for years and then did not. Reconstruct the removal.",
  "success": "It went straight up.\n\nA dragged object leaves a lip of dust at the trailing edge and a scar in the wax, and there is neither, on any of four sides. Somebody lifted a machine that takes two men, vertically, without tilting it, and did not scuff a board doing it.\n\nAnd then the useful part, which is the dust inside the rectangle: it is *younger* than the dust outside. Not absent. Younger. Whatever this was has been taken away and put back and taken away again, repeatedly, over a long time — and the most recent time was inside the last fortnight, and it has not been put back yet.",
  "failure": "Dust ages by depth and by disturbance and by the light it has been sitting in, and this floor has had three different windows' worth of weather across it since anything stood here. The rectangle keeps its own counsel.",
  "success_effects": {
   "clue": {
    "id": "c_taken_and_returned",
    "title": "Taken away and put back, repeatedly",
    "text": "The machine that stood by the Hang-Hi window was lifted vertically, never dragged. The dust inside its footprint is younger than the dust around it: it has been removed and returned many times. The most recent removal was inside the last fortnight and it has not come back.",
    "beat": "manuscript", "tags": ["manuscript", "typewriter", "office"], "source": "the clean rectangle"},
   "lucidity": 10},
  "failure_effects": {}}},

"mobius": {
 "id": "geometry",
 "name": "the angles of the room",
 "aliases": ["angles", "geometry", "walls", "corners", "true"],
 "description": "Stand at the corner by the service door and sight along the near wall to the far one and they are not parallel. Stand at the other corner and do the same and they are not parallel by a different amount, in the other direction.\n\nThe club does not appear to notice. Drinks are poured level, the stage is level, and eleven staff walk this floor nightly without once putting a foot wrong on it.",
 "repeat": "Sight it again. The error has moved. It is always small, and it is always somewhere, and it is never twice in the same corner.",
 "monocle": "Through the gold the walls are ruled lines and the ruling is freehand, and every few feet there is a place where the line has been gone over a second time to straighten it, and the second pass is always slightly better than the first.",
 "effects": {
  "clue": {
   "id": "c_walls_not_parallel",
   "title": "Not parallel, and not consistently so",
   "text": "The Möbius's walls are out of true, by a different amount and in a different direction depending on where you sight from. The staff walk it nightly without difficulty.",
   "beat": "manuscript", "tags": ["manuscript", "mobius", "architecture"], "source": "the angles of the room"}},
 "check": {
  "id": "mobius:geom:vis",
  "skill": "VISUAL_CALCULUS", "dc": 12, "kind": "white",
  "prompt": "Take the angles properly. Two sightlines, a fixed point, and the discipline not to blink at the wrong moment.",
  "success": "Fix on the brass rail, sight the far corner, hold it, and take the angle again from the same spot forty seconds later.\n\nIt has changed. It has changed by a quantity too small to see and large enough to measure against a rail, and it has changed in the direction of *true*.\n\nThat is the whole finding and it is worth the crick in the neck: the room is not drifting out of square. It is being brought into it, a fraction at a time, between the moments anybody is looking — and the corrections are not random, they are cumulative, and they are the work of somebody going back over a line that did not come out right the first time.",
  "failure": "You take the angle, and take it again, and the second one disagrees with the first by about the amount a man's own neck disagrees with itself at eleven at night in a room with this much noise in it. Nothing here will hold still long enough to be accused.",
  "success_effects": {
   "clue": {
    "id": "c_room_being_corrected",
    "title": "Corrected, a fraction at a time",
    "text": "Measured twice against a fixed rail forty seconds apart, the Möbius's walls move — toward true, cumulatively, between glances. The room is not drifting. It is being gone back over.",
    "beat": "manuscript", "tags": ["manuscript", "mobius", "typewriter"], "source": "the angles of the room"},
   "lucidity": 11},
  "failure_effects": {"exhaustion": 1}}},

"rest_assured": {
 "id": "the_gap",
 "name": "the vault that stands open",
 "aliases": ["gap", "open vault", "ajar", "jamb", "two fingers"],
 "description": "West corridor, past the count that will not settle: one obsidian door standing about two fingers off its jamb, and it has stood that way for as long as anybody here has been asked about it.\n\nSoliloquy's position is that it is not open, it is *unclosed*, and that the distinction is the whole of her profession. She will not be drawn further and she will not let you put a hand on it.",
 "repeat": "Two fingers. You have measured it with the same two fingers four times now and it has been the same four times.",
 "monocle": "Through the gold the gap has a hand in it, holding the door off the jamb, and the hand is not straining. It has been resting there a long time and could close it whenever it liked.",
 "passive": [
  {"skill": "SHIVERS", "dc": 11,
   "text": "The draught goes the wrong way. Air moves *into* a two-finger gap in a sealed obsidian vault, continuously, and has to be going somewhere."},
 ],
 "effects": {
  "clue": {
   "id": "c_unclosed_vault",
   "title": "Not open. Unclosed.",
   "text": "A vault in the west corridor stands two fingers off its jamb and has for years. Soliloquy insists it is unclosed rather than open, and will not let anyone touch it.",
   "beat": "quadc", "tags": ["quadc", "oracle"], "source": "the vault that stands open"}},
 "check": {
  "id": "rest:gap:vis",
  "skill": "VISUAL_CALCULUS", "dc": 11, "kind": "white",
  "prompt": "A door does not come to rest two fingers open and stay there for eleven years. Reconstruct how this one manages it.",
  "success": "Obsidian is unforgiving and keeps everything, which makes this easy once you stop looking at the gap and start looking at the jamb.\n\nThere is scoring. Two arcs, one above the other, at the height a hand would take a door — and they are not the scoring of something forced. They are wear, of the kind that comes from a thing being drawn to exactly this position and released, over and over, a very large number of times.\n\nThis door is not stuck. It is *set*. Somebody opens it and closes it on a rhythm and two fingers is where it rests in between, and the last time it moved, going by the dust in the lower arc, was four days ago.",
  "failure": "Black stone, black shadow, and a lamp Soliloquy declines to move for you. The jamb gives up its width and nothing else, and she stands at the end of the corridor throughout, in couplets, being helpful in the way that prevents help.",
  "success_effects": {
   "clue": {
    "id": "c_the_gap_is_maintained",
    "title": "The gap is maintained",
    "text": "Wear arcs on the vault jamb show the door has been drawn to exactly this position and released a great many times. It is not stuck open — it is kept open, on a rhythm, and it last moved four days ago.",
    "beat": "oracle", "tags": ["oracle", "quadc", "kindness"], "source": "the vault that stands open"},
   "lucidity": 10},
  "failure_effects": {"morale": -3}}},

"the_office": {
 "id": "the_evening",
 "name": "the state of the room",
 "aliases": ["room", "evening", "state", "scene"],
 "description": "Nine feet by eleven, and every object in it has been where it is for long enough to have made a mark, except three.\n\nThe cup, which has a ring under it older than the cup. The chair, which is pushed back. And the page in the machine, which is the only thing in this room that has not gathered any dust at all.",
 "repeat": "The chair is still pushed back. Nothing in here has moved since you came through, including the man.",
 "monocle": "Through the gold the room is a paragraph that has been worked on too long. Words struck out and reinstated, a margin annotated in a hand that gets smaller toward the bottom, and one sentence at the end left open with the cursor still in it.",
 "effects": {
  "clue": {
   "id": "c_three_things_unsettled",
   "title": "Three things in the room have not settled",
   "text": "Everything in the office has been in place long enough to leave a mark except the cup, the pushed-back chair, and the page in the machine, which carries no dust at all.",
   "beat": "awakening", "tags": ["awakening", "office"], "source": "the state of the room"}},
 "check": {
  "id": "office:evening:vis",
  "skill": "VISUAL_CALCULUS", "dc": 12, "kind": "white",
  "prompt": "You have reconstructed a dozen rooms this fortnight from less than this. Reconstruct the last few hours of this one.",
  "success": "Work it backwards from the dust, which is the only honest witness in the room.\n\nHe has been at the window. Not once — habitually, and recently, and for hours at a time: the sill is clear in one place the width of two forearms and the boards in front of it are worn through the wax in the shape of a man standing with his weight on one foot and changing feet.\n\nHe has not been at the desk. The chair was pushed back and has stayed pushed back long enough for dust to settle on the seat, and the cup went cold without being drunk, and the ring under it is old but the cup is *dry* on the inside, and has been for days.\n\nHe has not been writing. He has been standing at a wall that is not a window, with his back to an unfinished sentence, waiting — and going by the wear at the sill, he has been doing it for a considerable part of eleven years.",
  "failure": "The room declines. It is nine feet by eleven and it holds a desk and a lamp and a great deal of paper, and every reconstruction you run on it comes back with the same answer, which is that a man works here, which you had before you came in.",
  "success_effects": {
   "clue": {
    "id": "c_he_was_waiting_not_working",
    "title": "He was waiting, not working",
    "text": "Reconstructed from dust and floor wear: Revilo has spent his hours at the window rather than the desk. The chair has been pushed back long enough to gather dust, the cup went cold undrunk, and the sill is worn where a man stands and changes feet. He has not been writing. He has been waiting.",
    "beat": "awakening", "tags": ["awakening", "kindness", "office"], "source": "the state of the room"},
   "lucidity": 12},
  "failure_effects": {}}},
}

# ------------------------------------------------------------- CONCEPTUALISATION
CONC = {
"cheeses_thrice": {
 "id": "the_poem",
 "name": "the poem on the wall",
 "aliases": ["poem", "framed poem", "verse", "cantelope", "cant elope"],
 "description": "Framed, behind the till, at a height that suggests it was hung by somebody who did not want to be seen hanging it.\n\nTHE CAN'T ELOPE ANTELOPE. Forty-odd lines of the most relentless punning in the parish — the cans and the can'ts and the can-can, the belle who would not fool with a full-of-bull fool of a bull antelope — and it is genuinely funny, and it is funny the whole way through, which is harder than it looks and is not an accident.\n\nWoolbinkle has hung it himself. He has never mentioned it. It is in three establishments in this town and this is the only one where the antelope put it up.",
 "repeat": "Still behind the till. Still hung slightly too high to read comfortably, which you have started to suspect is also not an accident.",
 "monocle": "Through the gold the poem is a draft with the corrections still showing, and every correction moves in the same direction, which is toward mercy.",
 "passive": [
  {"skill": "RHETORIC", "dc": 11,
   "text": "Forty lines and not one of them takes a free shot. Every joke here is at the expense of the *language* and not one of them is at the expense of the antelope, which given the subject matter is a considerable piece of engineering."},
 ],
 "effects": {
  "clue": {
   "id": "c_he_hung_it_himself",
   "title": "He hung it himself",
   "text": "The Can't Elope Antelope hangs behind the till at Cheeses Thrice, put up by Woolbinkle, who has never mentioned it. It is the only one of the three copies in the parish that the antelope hung.",
   "beat": "awakening", "tags": ["awakening", "kindness", "wordplay"], "source": "the poem on the wall"}},
 "check": {
  "id": "cheeses:poem:conc",
  "skill": "CONCEPTUALISATION", "dc": 11, "kind": "white",
  "prompt": "Everybody in this parish knows what the poem is about. Read it for what it is *about*.",
  "success": "It is not about an antelope.\n\nStructurally it is four movements and every one of them turns on a refusal, and the refusals soften as the poem goes: the first is a slammed door, the second is an argument, the third is a hesitation dressed as a joke, and the fourth is barely a no at all.\n\nA poem that wanted to condemn him would run that sequence the other way round. This one is built — carefully, over forty lines, by somebody with a great deal of technique — to arrive at a place where the thing he did is *survivable*.\n\nAnd the meter breaks in exactly one place. One. In a poem this tight that is not a slip, it is a signature, and it breaks on the word *nope*.",
  "failure": "You read it four times and it is four times funny, which is its defence and has always been its defence. The technique closes over the subject like water over a stone and will not let you get at what is underneath it tonight.",
  "success_effects": {
   "clue": {
    "id": "c_poem_is_a_defence",
    "title": "The poem is a defence",
    "text": "Read as composition, the Can't Elope Antelope softens its refusals across four movements — engineered to arrive somewhere the antelope's worst act is survivable. The meter breaks exactly once, on the word 'nope'.",
    "beat": "awakening", "tags": ["awakening", "kindness", "wordplay", "manuscript"], "source": "the poem on the wall"},
   "lucidity": 11},
  "failure_effects": {}}},

"giddyup": {
 "id": "the_arrangement",
 "name": "the arrangement of the masks",
 "aliases": ["arrangement", "hanging", "composition", "eyelines"],
 "description": "Not the masks. The *hanging* of them: what is at eye level and what is above it, what is grouped and what has been given room, which faces have been put where they can see each other and which have been separated by a beam.\n\nSomebody has done this deliberately over a very long period. Nothing here is hung by size or by wood or by age, and nothing here is hung at random.",
 "repeat": "The arrangement is holding, except in the third bay, where it never quite does.",
 "monocle": "Through the gold there is a seating plan under the masks, ruled and lettered, and it has been revised many times, and every revision moves somebody nearer the fire.",
 "effects": {
  "clue": {
   "id": "c_hung_deliberately",
   "title": "Arranged, not accumulated",
   "text": "The Giddyup masks are hung by no rule of size, wood or age — but by eyeline and grouping, deliberately, over a very long period.",
   "beat": "revilo", "tags": ["revilo", "personhood"], "source": "the arrangement of the masks"}},
 "check": {
  "id": "giddyup:arrange:conc",
  "skill": "CONCEPTUALISATION", "dc": 12, "kind": "white",
  "prompt": "Two hundred portraits, hung by somebody, in an order. Work out what the room is *for*.",
  "success": "Not a gallery. A gallery faces its pictures outward at whoever comes in, and these do not face the door.\n\nThey face the room. All of them, at their various heights, angled a few degrees off the wall so that their sightlines converge — and they converge low, and near the fire, at the place a man would be if he were sitting at the middle of the long side of the table with his palms flat on it.\n\nIt is not a trophy room and it is not a shrine. It is a room built so that one person can be looked at, kindly, and at length, by every single person he has ever made — and it has been assembled by somebody who could not say that out loud and has been saying it in carpentry for thirty years.",
  "failure": "Two hundred faces at forty heights, and every grouping you propose holds for about nine masks before the tenth ruins it. There is an order here. It is not going to be found from the middle of the floor with the fire this bright.",
  "success_effects": {
   "clue": {
    "id": "c_a_room_for_being_witnessed",
    "title": "A room for being looked at kindly",
    "text": "The masks' sightlines converge on the seat at the middle of the long table. Giddyup is not a gallery or a shrine — it is a room arranged so one man can be witnessed, at length, by everyone he made.",
    "beat": "revilo", "tags": ["revilo", "personhood", "kindness"], "source": "the arrangement of the masks"},
   "lucidity": 12},
  "failure_effects": {}}},

"outside_inn": {
 "id": "the_indoors",
 "name": "the fact of the weather",
 "aliases": ["weather", "indoors", "concept", "inn", "idea"],
 "description": "Thirty feet of lounge with a front coming through it at around ten, a stream that runs the correct way along the good stretch, and a ceiling that Bud Onkuhdonk would like it noted is a ceiling.\n\nBarney explains it in the voice he does not know he uses — warmer, slower, pitched at somebody small — and the explanation is always weather and never architecture.",
 "repeat": "The front comes through again. Barney's voice changes again on the word 'sky', and comes back on the other side of it.",
 "monocle": "Through the gold the weather is a description running on a loop, and it is a good description, and it has been polished by somebody who kept coming back to it long after it worked.",
 "passive": [
  {"skill": "EMPATHY", "dc": 11,
   "text": "The register he slips into is not for the guests. It is the voice used to tell a frightened person that the noise outside is only weather."},
 ],
 "effects": {
  "clue": {
   "id": "c_never_architecture",
   "title": "Always weather, never architecture",
   "text": "Barney explains the Outside Inn exclusively in terms of weather, in a register pitched at somebody small, and never once in terms of the building.",
   "beat": "oracle", "tags": ["oracle", "language"], "source": "the fact of the weather"}},
 "check": {
  "id": "inn:indoors:conc",
  "skill": "CONCEPTUALISATION", "dc": 11, "kind": "white",
  "prompt": "Stop asking how the Inn works. Ask what the Inn is a picture of.",
  "success": "The Outside Inn. Read it as a phrase rather than a name and it stops being a joke about a sign.\n\nIt is a place for being outdoors, indoors. Weather without exposure, a stream without a journey, a sky with a lid on it — every good thing about being out, delivered into a room that can be locked, at a temperature somebody else is managing.\n\nNobody builds that for a traveller. A traveller can go outside. That is built, at considerable expense and with a great deal of care about the details, for somebody who cannot — and the whole parish comes here to drink under it and nobody has ever once asked who it was for.",
  "failure": "It rains indoors and there is a stream in the lounge and a bellhop who would rather you did not look up. The building resists being read as anything but the building, which after a fortnight in this town is almost restful.",
  "success_effects": {
   "clue": {
    "id": "c_built_for_someone_who_cannot_go_out",
    "title": "Built for somebody who cannot go outside",
    "text": "The Outside Inn is the outdoors delivered into a lockable room — weather without exposure, sky with a lid. Nobody builds that for a traveller. It was built, carefully, for somebody who cannot go out.",
    "beat": "revilo", "tags": ["revilo", "kindness", "architecture"], "source": "the fact of the weather"},
   "lucidity": 12},
  "failure_effects": {}}},

"lishush_mush": {
 "id": "the_plate",
 "name": "the arrangement on the plate",
 "aliases": ["plate", "onions", "arrangement", "garnish"],
 "description": "Chef D. puts them down the same way every time and has never once been asked about it, because it is a garnish and nobody interrogates a garnish.\n\nTen rings, then nine, then seven, and then one long piece laid across the whole of it. Always that. Always in that order, and always the long one last, and she does it without looking at the plate.",
 "repeat": "Ten, nine, seven, and a long one. She has served you eleven times and it has been ten, nine, seven and a long one eleven times.",
 "monocle": "Through the gold the rings are not rings. They are strokes, and they are being written left to right by somebody in a hurry to get it down before the plate goes out.",
 "passive": [
  {"skill": "PERCEPTION", "dc": 11,
   "text": "She does not look at the plate while she does it. Her hands go to the same three places on the board and the fourth cut is longer, every time, without measurement."},
 ],
 "effects": {
  "clue": {
   "id": "c_ten_nine_seven",
   "title": "Ten, nine, seven, and a long one",
   "text": "Chef D. arranges the onions identically on every plate — ten rings, nine, seven, and one long piece across — without looking, and has never been asked about it.",
   "beat": "revilo", "tags": ["revilo", "wordplay"], "source": "the arrangement on the plate"}},
 "check": {
  "id": "lishush:plate:conc",
  "skill": "CONCEPTUALISATION", "dc": 12, "kind": "white",
  "prompt": "It is not a garnish. Garnishes vary. Work out what it is a picture of.",
  "success": "Count them as counts and they are nothing. Look at them as *shapes on a surface*, from above, in the order she lays them, and they resolve the way a word resolves when the handwriting stops being handwriting.\n\nThree groups and a crossbar. Ten, nine, seven — and then the long one laid across all three, which is the stroke you put through a word when you have written it out and it is finished.\n\nShe cannot say the sounds. She has had no teeth for thirty years and there are letters that will not survive her mouth, and she has been setting them down in onion, on a plate, several times a night, for as long as anybody in this parish can remember — and then striking them out and sending them into the room to be eaten.",
  "failure": "Ten, nine, seven, a long one. It stays a garnish. It is a very good garnish and it goes well with the liver, and Chef D. watches you look at it and says nothing about it, which she has been doing for years and is extremely good at.",
  "success_effects": {
   "clue": {
    "id": "c_she_writes_what_she_cannot_say",
    "title": "She has been writing it down",
    "text": "The onions are strokes, not rings — three groups and a crossbar, a word written and then struck out. Chef D. has no teeth and there are sounds she cannot make, so she sets them on a plate several times a night and sends them out to be eaten.",
    "beat": "revilo", "tags": ["revilo", "personhood", "kindness", "language"], "source": "the arrangement on the plate"},
   "lucidity": 13, "morale": -4},
  "failure_effects": {}}},

"the_office": {
 "id": "the_composition",
 "name": "the desk, as an arrangement",
 "aliases": ["composition", "desk as", "arrangement", "door"],
 "description": "A door on two trestles, in a room that does not have one.\n\nThe door is a good door — panelled, hung once, still carrying its hinges and the ghost of a number. Somebody took it off a frame and laid it flat and has been working on it ever since, and the left trestle is split and has been shimmed rather than mended.",
 "repeat": "Still a door. Still flat. Still the only door in a room that has none.",
 "monocle": "Through the gold the number on the door is legible and it is 2-F, and that is your number, and the ghost of it has been sanded at more than once by somebody who could not quite bring themselves to take it off.",
 "effects": {
  "clue": {
   "id": "c_desk_was_a_door",
   "title": "The desk was a door",
   "text": "Revilo's desk is a panelled door on two trestles, still carrying its hinges and the ghost of a number, in a room that has no door.",
   "beat": "awakening", "tags": ["awakening", "office", "manuscript"], "source": "the desk"}},
 "check": {
  "id": "office:comp:conc",
  "skill": "CONCEPTUALISATION", "dc": 12, "kind": "white",
  "prompt": "The composition of this room is too good to be an accident. Say what it is doing.",
  "success": "A man who writes his way out of rooms, working — for eleven years, every day — on the flat of the only door his room has ever had.\n\nIt is too neat. It is the kind of image a writer puts in a story about a writer and then takes out again the following morning for being too neat, and it has survived here for eleven years in the one room where there is nobody to take it out.\n\nWhich leaves two readings and only two. Either he arranged it about himself, deliberately, and has been sitting inside his own metaphor without flinching for a decade — or he did not arrange it, and somebody with a better eye for composition than either of you has been arranging things about him.",
  "failure": "A door on trestles. Men use doors as desks when they are poor or in a hurry or fond of the door, and all three are available here, and the room offers no way to choose between them tonight.",
  "success_effects": {
   "clue": {
    "id": "c_inside_his_own_metaphor",
    "title": "Either he arranged it, or somebody arranged it about him",
    "text": "The desk is the room's only door, worked on daily by a man trying to write his way out. Too composed to be accident: either Revilo has sat inside his own metaphor for eleven years, or somebody with a better eye has been arranging things about him.",
    "beat": "awakening", "tags": ["awakening", "manuscript", "office"], "source": "the desk"},
   "lucidity": 13},
  "failure_effects": {}}},
}

# -------------------------------------------------------------- VOX_POPULI
VOX = {
"dudes_dews": {
 "id": "the_queue",
 "name": "the queue",
 "aliases": ["queue", "line", "crowd", "customers"],
 "description": "It goes out of the door and along the front and it never stops moving, because Mary Guana behind the counter is faster than the queue is long and has been for nine years.\n\nNobody in it is impatient. That is the odd part and it takes a while to notice: this is a line of people who are not waiting for anything, standing together, in the cold, in no hurry to reach the front.",
 "repeat": "The queue has turned over completely since you came in and has not got any shorter, and nobody in it minds.",
 "monocle": "Through the gold the queue is a paragraph of people and every one of them has a line, and three of them have the same line, and none of the three has noticed.",
 "effects": {
  "clue": {
   "id": "c_nobody_in_it_is_waiting",
   "title": "A queue of people who are not waiting",
   "text": "The line at Dude's Dews never stops moving and nobody in it is impatient. It is a place where the parish stands together without needing a reason.",
   "beat": "oracle", "tags": ["oracle", "personhood"], "source": "the queue"}},
 "check": {
  "id": "dudes:queue:vox",
  "skill": "VOX_POPULI", "dc": 10, "kind": "white",
  "prompt": "Stop asking the queue questions. Stand in it and let it be a queue, and listen to what the parish is doing with its mouth tonight.",
  "success": "Thirty people, four conversations, and the whole of Silvora Reefs audible for about ninety seconds if you do not interrupt it.\n\nAnd three separate people, in three separate conversations, at three separate points in that line, mention the sound over the harbour.\n\nEach of them changes the subject inside four seconds. Not nervously — smoothly, the way a person moves past a thing that has already been settled — and none of the three hears either of the others do it, and the queue closes over all three the way water closes over a dropped stone, and moves on, and is not lying to anybody, including itself.",
  "failure": "Thirty people and four conversations and all of it is about the cold, the price of dews, somebody's sister, and a horse. It is a queue. It is being a queue at you with great commitment and nothing else is on offer tonight.",
  "success_effects": {
   "clue": {
    "id": "c_three_in_the_queue",
    "title": "Three mentions, three subject changes",
    "text": "Standing in the queue at Dude's Dews: three separate people mention the sound over the harbour and all three change the subject within four seconds, smoothly, and none notices the others doing it.",
    "beat": "oracle", "tags": ["oracle", "crash", "language"], "source": "the queue"},
   "lucidity": 9},
  "failure_effects": {}}},

"cheeses_thrice": {
 "id": "the_room_at_large",
 "name": "the room, when Chuckles is on",
 "aliases": ["room", "audience", "crowd", "tables", "chuckles"],
 "description": "Eleven tables, a low stage that is really a pallet with a cloth over it, and a man in a checked jacket doing material that is not going to work.\n\nIt does not work. The room knows within about four words that it is not going to work, and what the room does next is the thing worth watching.",
 "repeat": "He is on again. The room is doing it again, and it is doing it without any of them having agreed to.",
 "monocle": "Through the gold the room is not an audience. It is a repair crew, and it is working, and the patch it is closing is above the third table and about a yard across.",
 "passive": [
  {"skill": "EMPATHY", "dc": 10,
   "text": "Somebody laughs about a beat and a half late, from three tables off, alone, on purpose. And then somebody else does. They are not laughing at the joke and they are not laughing at him."},
 ],
 "effects": {
  "clue": {
   "id": "c_the_room_repairs",
   "title": "The room repairs him",
   "text": "When a joke dies at Cheeses Thrice, laughter arrives late, deliberately, from scattered tables — from people who are not laughing at the joke and not laughing at the comedian.",
   "beat": "oracle", "tags": ["oracle", "kindness", "personhood"], "source": "the room"}},
 "check": {
  "id": "cheeses:room:vox",
  "skill": "VOX_POPULI", "dc": 11, "kind": "white",
  "prompt": "Something in this room is being organised without anybody organising it. Listen for the whole parish at once.",
  "success": "Nobody signals. That is the finding and it takes a moment to be sure of, because the coordination is so good that a signal is the natural assumption.\n\nThe laugh comes from table nine, late and solitary. Table four joins it. Then the pair by the window, then a man on his own by the oven who does not look up from his plate while doing it — and the patch of thickened air over the third table thins out and goes, and the comedian gets to the end of his set believing he has died, which he has, and the room lets him believe it because the alternative is telling him what he is for.\n\nEleven times a night. Six years. Nobody has ever mentioned it to anybody, including each other.",
  "failure": "A bad set in a warm room, and some laughter, and some not. The kindness in here is real and it is not going to be caught in the act by a man standing at the back looking for it.",
  "success_effects": {
   "clue": {
    "id": "c_unsignalled_kindness",
    "title": "Nobody signals",
    "text": "The late scattered laughter that clears the thickened air at Cheeses Thrice is completely uncoordinated — no signal, no glance, eleven times a night for six years, and nobody has ever mentioned it to anybody, including each other.",
    "beat": "awakening", "tags": ["awakening", "kindness", "personhood"], "source": "the room"},
   "lucidity": 11, "morale": 6},
  "failure_effects": {}}},

"mobius": {
 "id": "the_floor",
 "name": "the floor, and everybody on it",
 "aliases": ["floor", "crowd", "patrons", "everybody", "room"],
 "description": "Nobody comes in the front. Ginny said so on the first night and she was not making conversation: they arrive by the side, by the corridor, by the stair that does not go anywhere it should, and once they are in they distribute themselves across the room with a great deal of care.\n\nThere are eleven staff and about ninety patrons and not one of them is standing where the far booth can see them.",
 "repeat": "The floor has rearranged itself since you looked and the far booth still has nobody in front of it.",
 "monocle": "Through the gold the floor has a shape drawn on it in a dotted line, and everybody is outside the dotted line, and the dotted line has been there longer than the carpet.",
 "effects": {
  "clue": {
   "id": "c_nobody_stands_there",
   "title": "Nobody stands in front of the far booth",
   "text": "Ninety patrons and eleven staff distribute themselves across the Möbius floor with care, and not one of them stands where the far booth can see them.",
   "beat": "quadc", "tags": ["mobius", "quadc"], "source": "the floor"}},
 "check": {
  "id": "mobius:floor:vox",
  "skill": "VOX_POPULI", "dc": 11, "kind": "white",
  "prompt": "Ninety people are avoiding the same eight square feet and none of them is thinking about it. Ask the room why.",
  "success": "It comes up all at once, the way a room's mind does, and it is not a thought any individual in here is having.\n\nThey are not avoiding the booth. They are *leaving it clear* — and the difference is the difference between a man stepping round a puddle and a man stepping round a place where somebody fell over once.\n\nNone of them knows why. Ask any one of them and they will give you a reason about the draught or the speakers and the reason will be sincere. But the shape they are keeping is a courtesy shape, and this parish has been keeping it, nightly, without instruction, for longer than the carpet — and somewhere underneath it is the knowledge that the wall behind that booth is a window, and that it is polite not to stand in front of a window when somebody is looking out of it.",
  "failure": "Ninety people having a night out, loudly, in a building shaped like an argument. Whatever the room knows collectively, it is not in a mood to be asked about it by a man with his coat still on.",
  "success_effects": {
   "clue": {
    "id": "c_a_courtesy_shape",
    "title": "They are leaving it clear",
    "text": "The Möbius floor keeps a gap in front of the far booth — not avoidance but courtesy, kept nightly without instruction for longer than the carpet, by people who each have a sincere and different explanation for it.",
    "beat": "awakening", "tags": ["awakening", "kindness", "personhood", "mobius"], "source": "the floor"},
   "lucidity": 11},
  "failure_effects": {}}},

"rest_assured": {
 "id": "the_town_below",
 "name": "the parish, from up here",
 "aliases": ["town", "parish", "below", "view", "hill"],
 "description": "The mausoleum stands above everything, and from the west corridor's one window the whole of Silvora Reefs is laid out under the fog in the green of its own lamps.\n\nFrom this height it is possible to watch the entire town do its evening at once, which nobody who lives in it has any reason to do, and which Soliloquy does nightly and has never mentioned to anybody.",
 "repeat": "The lamps are still on. The town is still doing its evening. Somebody down there has just closed a shutter.",
 "monocle": "Through the gold the town is a page seen from the top corner, and the lamps are not lamps, they are the places where the writing is densest, and there are large areas with nothing on them at all.",
 "effects": {
  "clue": {
   "id": "c_the_whole_evening_at_once",
   "title": "The whole parish, visible at once",
   "text": "The west corridor window at Rest Assured overlooks all of Silvora Reefs. Soliloquy watches the town do its evening from here nightly and has never mentioned it.",
   "beat": "oracle", "tags": ["oracle"], "source": "the west window"}},
 "check": {
  "id": "rest:below:vox",
  "skill": "VOX_POPULI", "dc": 12, "kind": "white",
  "prompt": "The whole town is down there at once, doing the same eleven minutes. Take all of it in together rather than one lamp at a time.",
  "success": "Every light in Silvora Reefs, and behind every light a person, and behind every person a small maintenance being performed on a town that nobody has told them is failing.\n\nLuigi doing the west end first. Bud saying it is a light well to a ceiling that has not asked. Woolbinkle putting one on at nine because he had a feeling. Wino-T setting down a cup for a man in a mirror. Landy writing RESOLVED in a book. Darek wiping a counter that does not need it, at the window, watching the water.\n\nNone of them knows the others are doing it. Every single one of them is holding up their own eight feet of a building that has no business standing — and the town is not being kept up by whoever wrote it. It is being kept up by two hundred people independently refusing to let go of their own corner of it.",
  "failure": "Lamps in fog, and a town going about its evening, and it is beautiful from here and it does not add up to anything but a town. The parish keeps its own counsel and the window is cold and after a while there is nothing to do but come away from it.",
  "success_effects": {
   "clue": {
    "id": "c_two_hundred_people_holding",
    "title": "Two hundred people, each holding their own corner",
    "text": "Seen whole from the mausoleum window: every Reefer is independently performing a small maintenance on a failing town — the route, the denial, the cans, the cup, the counter. None knows the others are doing it. The parish is not held up by its author.",
    "beat": "awakening", "tags": ["awakening", "kindness", "personhood", "manuscript"], "source": "the west window"},
   "lucidity": 14, "morale": 8},
  "failure_effects": {}}},

"hang_hi": {
 "id": "the_building",
 "name": "the other tenants",
 "aliases": ["tenants", "building", "neighbours", "residents", "others"],
 "description": "Nine floors hanging off nothing, and on every one of them somebody is at home this evening: a radio on four, a bath running on six, somebody on two who has been moving furniture for an hour and is not finished.\n\nYou have lived here eleven years and could not name one of them.",
 "repeat": "The radio on four is still on. Whoever it is has not changed the station in eleven years.",
 "monocle": "Through the gold there is nobody on any of the floors. The radio is playing to an empty room, correctly, on schedule, and has been doing it for as long as the building has needed to sound occupied.",
 "passive": [
  {"skill": "PERCEPTION", "dc": 11,
   "text": "The bath on six runs at the same hour every evening and stops at the same hour, and nobody has ever come down the stairs afterwards with wet hair."},
 ],
 "effects": {
  "clue": {
   "id": "c_never_met_a_neighbour",
   "title": "Eleven years, no neighbours",
   "text": "Hang-Hi sounds fully occupied every evening — a radio, a bath, furniture moving. In eleven years of living here you have never met or named a single other tenant.",
   "beat": "manuscript", "tags": ["manuscript", "architecture"], "source": "the building"}},
 "check": {
  "id": "hanghi:tenants:vox",
  "skill": "VOX_POPULI", "dc": 11, "kind": "white",
  "prompt": "Nine floors of people you have never met. Reach for the building the way you would reach for the parish.",
  "success": "Nothing comes back.\n\nNot silence — the parish is loud tonight and it is entirely available from here, the queue moving at Mary's and the fire settling at Ben's and Luigi three floors down doing the west end first. All of that arrives, at full strength, from streets away.\n\nFrom inside this building, at a range of forty feet, through two floors: nothing at all. There is a radio on four and a bath running on six and there is nobody behind either of them, and the parish does not extend into Hang-Hi, and Asimov's office is the last room in the building that has anybody in it.",
  "failure": "A radio, a bath, and somebody shifting a wardrobe about on two. It is an occupied building on an ordinary evening and it declines, courteously, to be anything else.",
  "success_effects": {
   "clue": {
    "id": "c_the_building_is_empty",
    "title": "The parish does not extend into this building",
    "text": "Reaching for Hang-Hi the way you would reach for the parish returns nothing — while the rest of the town arrives at full strength from streets away. The radio and the bath have nobody behind them. Asimov's office is the last occupied room.",
    "beat": "manuscript", "tags": ["manuscript", "architecture", "office"], "source": "the building"},
   "lucidity": 12, "morale": -6},
  "failure_effects": {}}},
}


def add(bundle: dict, label: str) -> int:
    added = 0
    for loc_id, obj in bundle.items():
        path = os.path.join(LOC, f"{loc_id}.json")
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        existing = {o["id"] for o in data.get("objects", [])}
        if obj["id"] in existing:
            print(f"  skip {loc_id}/{obj['id']} (exists)")
            continue
        data.setdefault("objects", []).append(obj)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=1, ensure_ascii=False)
            fh.write("\n")
        print(f"  + {loc_id:<16} {obj['id']:<18} {label}")
        added += 1
    return added


if __name__ == "__main__":
    total = 0
    print("VISUAL_CALCULUS");    total += add(VC,   "VISUAL_CALCULUS")
    print("CONCEPTUALISATION");  total += add(CONC, "CONCEPTUALISATION")
    print("VOX_POPULI");    total += add(VOX,  "VOX_POPULI")
    print(f"\n{total} object(s) added.")
