#!/usr/bin/env python3
"""Phase 2: bring the seven thinnest skills from 2 active checks up to 4.

VOLITION, AUTHORITY, PAIN_THRESHOLD, INLAND_EMPIRE, ETYMOLOGY, HALF_LIGHT and
SUGGESTION each had exactly two active checks in the entire game. Objects were
already crowded (hang_hi and mobius carry nine each), and dialogue checks were
comparatively rare — "T" had one across nine nodes — so these go into
conversation instead, which also puts the interior skills where they belong.

Each entry adds one option to an existing node plus a new payoff node. Failure
routes back to a node the player can leave from, so no check can strand anyone.

Only touches dialogue files whose voices have been read end to end, so the new
lines stay in each character's own idiom rather than the narrator's.

Idempotent: skips any option id that already exists on the target node.
"""
from __future__ import annotations
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DLG = os.path.join(ROOT, "game", "content", "dialogue")
if not os.path.isdir(DLG):
    DLG = os.path.join(ROOT, "content", "dialogue")

def opt(oid, text, skill, dc, cid, stext, ftext, target, clue,
        lucidity=0, morale=0, rel=None, bonus=None, fail_to="root", kind="white"):
    o = {"id": oid, "text": text, "once": True,
         "check": {"id": cid, "skill": skill, "dc": dc, "kind": kind,
                   "success_text": stext, "failure_text": ftext,
                   "success": target, "failure": fail_to,
                   "success_effects": {"clue": clue}}}
    se = o["check"]["success_effects"]
    if lucidity: se["lucidity"] = lucidity
    if morale:   se["morale"] = morale
    if rel:      se["relationship"] = rel
    if bonus:    o["check"]["bonus_if_clue"] = bonus
    return o

def node(text, options=None, effects=None, narration=False):
    n = {"text": text}
    if effects: n["effects"] = effects
    n["options"] = options or [{"id": "back", "text": "\"Something else.\"", "goto": "root"}]
    if narration: n["narration"] = True
    return n

# (npc, host_node, option, new_node_id, new_node)
ADDITIONS = [

# ---------------------------------------------------------------- VOLITION
("revilo", "arg_one", opt(
  "hold", "Say nothing. Stand there and do not come apart.",
  "VOLITION", 12, "revilo:hold",
  "You do not argue, because the argument is sound and you have not got one, and the absence of one is what he has been counting on.\n\nSo you stand in it instead. The whole weight of a correct case for your own non-existence, delivered in your own cadence by a man with your face, and you take it standing up in a room nine feet by eleven, and you do not answer it, and you do not come apart, and it goes on for some time.\n\nHe stops before you do.\n\n\"...That,\" he says, \"is not a rebuttal.\"\n\nNo. It is not.\n\n\"No. It is worse than a rebuttal. A rebuttal I have drafted answers to.\"",
  "The case lands the way a correct case lands. He builds it in one breath, without cruelty and without a gap, and somewhere in the third clause the floor of it gives and there is nothing underneath to stand on, and the room gets very small and stays that way for a while.\n\nHe waits, courteously, until it has finished happening.",
  "held", {"id": "c_stood_in_it", "title": "Not a rebuttal, and worse than one",
   "text": "Faced with a sound argument for his own non-existence, Oliver did not answer it and did not come apart. Revilo has drafted answers to every rebuttal. He has not drafted one for a man simply remaining in the room.",
   "beat": "awakening", "tags": ["awakening", "personhood"], "source": "Snoino Revilo"},
  lucidity=12, rel={"revilo": 1}, bonus={"c_no_floor": 2, "c_two_hundred_drafts": 2},
  fail_to="arg_one")),

("soliloquy", "aloud", opt(
  "keep_it", "\"Then I will keep it. All of it. Until I know what I want to be true.\"",
  "VOLITION", 11, "soliloquy:keep_it",
  "\"Then you are the first,\" she says.\n\nNo rhyme. No couplet. A keeper of the horizontal standing in her own vestibule saying four flat words to a man who is still upright.\n\n\"Forty of them, sir, and every single one told somebody. Not out of foolishness — out of *relief*. It is an unbearable amount to carry alone and the carrying is the whole of the price, and I have watched forty people put it down and I have engraved forty plates and I have never once been able to say what I am saying to you now, which is: carry it. Carry it a while longer. It is worth what it costs.\"",
  "\"Everyone says so, sir. Everyone says so in this vestibule, with the fog behind them and their collar up, and then they go down the hill and into a warm room and there is somebody kind in it, and the kind person asks what is the matter — and that is where it goes. Never in the fog. Always in the warm room.\"\n\nA couplet arrives about hearths. It is very fine. It is also a door closing.",
  "kept_it", {"id": "c_carry_it_longer", "title": "Carry it a while longer",
   "text": "Soliloquy has watched forty people put down what they were carrying — always in a warm room, to somebody kind — and then engraved forty plates. She has never before been able to tell anyone to keep carrying it.",
   "beat": "quadc", "tags": ["quadc", "kindness", "personhood"], "source": "Soliloquy"},
  lucidity=9, morale=6, rel={"soliloquy": 2}, fail_to="aloud")),

# --------------------------------------------------------------- AUTHORITY
("soliloquy", "vault", opt(
  "enough", "\"Stop. No verse. Answer me in prose or say you will not.\"",
  "AUTHORITY", 12, "soliloquy:enough",
  "It is not loud. Loud would have got you a couplet about thunder.\n\nIt is the voice that ends a conversation, used once, in a building where the acoustics are on her side and the subject is hers and the standing is not — and it works, and what is startling is how fast it works, as though she has been waiting sixty years for somebody to make her stop.\n\n\"...Very well,\" says Soliloquy, in prose. \"I will not.\n\nThere. That is the honest form of it and it has taken me the whole of my professional life to be asked for it correctly. I will not tell you what is behind that door. Not tonight, not to you, not while you are still deciding what you are — and you may take that as obstruction, sir, and I shall not complain, because it is.\"",
  "\"Prose,\" she says, delightedly, and does eleven lines of it that scan perfectly and rhyme internally and are, technically, prose, and are about the history of the word.\n\nBy the end of it you are nearer the vestibule and she is nearer the west corridor and neither of those movements was yours.",
  "keeper_yields", {"id": "c_she_will_not_say", "title": "The honest form of a refusal",
   "text": "Asked in prose, Soliloquy refuses in prose: she will not say what is behind the unmarked door, not while Oliver is still deciding what he is, and she names it as obstruction herself.",
   "beat": "oracle", "tags": ["oracle", "kindness"], "source": "Soliloquy"},
  lucidity=8, rel={"soliloquy": 1}, fail_to="vault")),

("ginny", "root", opt(
  "my_floor", "\"You run this floor. You don't run what I'm doing on it.\"",
  "AUTHORITY", 11, "ginny:my_floor",
  "She looks at you for slightly longer than the sentence deserved.\n\n\"Good,\" she says. \"Say it like that to the gators and they'll write it down and file it and forget it, which is what you want. Say it like that to me and I'll respect it, which is worse for you, because now I'm interested.\"\n\nShe puts the gin down.\n\n\"Weight was right. Chin was wrong — you lifted it, which is a tell, and it says the standing's borrowed. Doesn't matter in here. Will matter in about four days when somebody asks you who you are and you have to answer without a wobble in it. Practise on me. I'm cheap.\"",
  "\"Mm,\" says Ginny, and does not look up from the till. \"You said that with your weight on the back foot.\"\n\nAnd that is the whole of the exchange, and the room absorbs it without a ripple, and somewhere behind you a man in a suit that fits too well makes a note of nothing at all.",
  "standing", {"id": "c_borrowed_standing", "title": "The standing is borrowed",
   "text": "Ginny reads Oliver's authority as borrowed — the weight right, the chin lifted, a tell. She expects it to be tested within four days by somebody asking who he is.",
   "beat": "revilo", "tags": ["revilo", "identity"], "source": "Ginny Ginja"},
  lucidity=6, rel={"ginny": 1})),

# --------------------------------------------------------- PAIN_THRESHOLD
("revilo", "denied", opt(
  "take_it", "Take it. Do not put it down and do not let him see you put it down.",
  "PAIN_THRESHOLD", 12, "revilo:take_it",
  "He has just removed a kitchen, a woman, and forty years of the only grief you were certain of, and he did it in four sentences, courteously, because the architecture required it.\n\nYou take it the way you have taken every other thing this fortnight: fully, at once, without flinching and without filing it anywhere it can be lost.\n\n\"You are not going to argue,\" he says.\n\nNo.\n\n\"You are not going to argue, and you are not going to sit down, and you are going to carry that out of this room with you.\" A pause, and it is the first one this evening that has not been an instrument. \"I did not model that. I modelled grief and I modelled rage and I modelled a man asking me to put her back. I did not model *keeping* it.\"",
  "It goes in exactly where he aimed it.\n\nThere is no argument available and no ground to take it on, and the room does what small rooms do, and it is some time before the conversation has anywhere to go and when it does it goes somewhere easier, because he lets it, which is the worst courtesy of the night.",
  "took_it", {"id": "c_he_did_not_model_keeping",
   "title": "He did not model keeping it",
   "text": "Told the kitchen and the woman in it were invented, Oliver kept the grief rather than surrendering or contesting it. Revilo modelled grief, rage, and pleading. He did not model a man keeping what he had been told was not real.",
   "beat": "awakening", "tags": ["awakening", "personhood", "kindness"], "source": "Snoino Revilo"},
  lucidity=13, morale=-4, rel={"revilo": 1}, fail_to="denied")),

("darek", "rotors", opt(
  "carry", "Say nothing about the rotors. Let him keep the noise, and carry the rest yourself.",
  "PAIN_THRESHOLD", 11, "darek:carry",
  "He has told you there is nothing up there. He is wrong and he knows he is wrong and the knowing is sitting on him like a coat that is too warm for the room.\n\nSo you let it go. You take the whole weight of the thing off the counter and put it somewhere in yourself where it will keep, and you ask him about the tubs.\n\nAnd Darek — who is previous, who has been previous his whole life, who answers a beat before the question — does not answer this one early. He looks at you for a second and a half.\n\n\"...Yeah,\" he says slowly. \"The tubs. Right.\" And then, wiping: \"You just did somethin', Ols. I don't know what it was. I'd like the record to show I noticed it.\"",
  "You do not mention it, which is the plan, and then it is in the room anyway — in the shape of the pause, in the way the cone gets made too carefully — and he says \"Sorry about your wait\" at the wrong moment for the first time all evening and neither of you can pretend that landed right.",
  "carried_it", {"id": "c_took_it_off_the_counter",
   "title": "Off the counter, into your pocket",
   "text": "Rather than make Darek say the rotors out loud — which in Silvora Reefs is how a thing becomes the case — you carried it yourself. He noticed, a beat late, which is not how Darek notices anything.",
   "beat": "oracle", "tags": ["oracle", "kindness", "personhood"], "source": "Darek Dwayne Wayne"},
  lucidity=7, morale=5, rel={"darek": 2}, fail_to="rotors")),

# ------------------------------------------------------------ INLAND_EMPIRE
("t", "utensils", opt(
  "ask_ladle", "Do not ask him. Ask the ladle.",
  "INLAND_EMPIRE", 11, "t:ask_ladle",
  "The ladle is on the pass and it is not quite touching the pass, and it has been in that condition for the length of a sentence about tureens.\n\nSo: what does the ladle want.\n\nThe answer arrives fully dressed and entirely unembarrassed, the way they do, and it is this — the ladle does not want anything. The ladle is *being held*, gently, at the height at which a person holds a thing they intend to give back, by something that has been in this kitchen a very long time and has never once been thanked for the catching.\n\nAnd it likes the long sentences. It likes them the way a dog likes a particular voice, without understanding one word.",
  "The ladle is a ladle. It is a ladle nine inches above a steel counter and it is entirely uninterested in being interviewed, and after a while T says, kindly, \"It doesn't do requests,\" and goes back to the prep.",
  "the_ladle", {"id": "c_the_ladle_is_held",
   "title": "Being held, not lifted",
   "text": "The utensils over T's pass are not rising. They are being held at giving-back height by something long resident in the kitchen that has never been thanked, and that likes the sound of the long sentences without understanding them.",
   "beat": "oracle", "tags": ["oracle", "language", "furthermore"], "source": "the pass"},
  lucidity=10, rel={"t": 1}, fail_to="utensils")),

("albert", "why_glass", opt(
  "the_glass_itself", "Ask the mirror what it makes of him.",
  "INLAND_EMPIRE", 12, "albert:the_glass_itself",
  "Not Albert. The glass. The third mirror, which has held an owlbear for forty years without being asked and without complaint and without, so far as anybody in this shop has ever considered, an opinion.\n\nIt has one.\n\nIt arrives sideways and complete and in no language at all: *he is good company and he is the only thing in here that has ever said thank you to a surface, and he has been getting quieter for years, and I cannot make him louder, I can only refuse to stop including him, and I have never once stopped.*\n\nIn the glass, Monsieur Albert looks at nothing in particular, and does not ask what just happened, and inclines his head about a degree.",
  "It is a mirror in a barbershop. It shows the room, and an owlbear, and the back of a man's head at a desk that is not there, and it declines to be drawn on any of it.",
  "glass_opinion", {"id": "c_the_glass_refuses_to_stop",
   "title": "It has never once stopped including him",
   "text": "The third mirror's position, arrived at without language: it cannot make Albert louder, only refuse to stop including him — which it has done, without interruption, for forty years.",
   "beat": "awakening", "tags": ["awakening", "personhood", "kindness"], "source": "the third mirror"},
  lucidity=11, morale=6, rel={"albert": 1}, fail_to="why_glass")),

# ---------------------------------------------------------------- ETYMOLOGY
("soliloquy", "name", opt(
  "odochtaigh", "\"O'Dochtaigh. Take that apart for me.\"",
  "ETYMOLOGY", 11, "soliloquy:odochtaigh",
  "\"Ó Dochartaigh,\" she says, and gives it the whole of its length, which nobody has done in this parish in sixty years. \"Anglicised badly and early. *Dochartach* — hurtful, obstructive. The unhelpful ones. The line of the man who gets in the way.\"\n\nA pause, and the vestibule does the thing it does with pauses.\n\n\"I have thought about that a great deal, sir, standing in front of a door I will not open, obstructing a man who wishes to be let past. One does wonder whether one chose the profession or whether the profession was sitting in the name all along, waiting — as it was for the barber, who is a knight by nothing but a vowel.\"",
  "\"It is Irish, sir, and it is old, and it belonged to a woman who went into a vault in 1961 and has no further use for it.\"\n\nAnd that is a stone door coming down, in couplets, courteously, and there is nothing behind it tonight.",
  "odochtaigh", {"id": "c_the_obstructive_ones",
   "title": "Ó Dochartaigh — the unhelpful ones",
   "text": "Soliloquy's abandoned surname means hurtful or obstructive: the line of the man who gets in the way. She stands in front of a door she will not open and wonders whether the profession was waiting in the name, as barbering waited in Sir Jerry's.",
   "beat": "oracle", "tags": ["oracle", "language", "wordplay", "identity"], "source": "Soliloquy"},
  lucidity=9, rel={"soliloquy": 1}, fail_to="name")),

("t", "why_t", opt(
  "the_letter", "\"Then take the letter apart. What is a T.\"",
  "ETYMOLOGY", 11, "t:the_letter",
  "\"Ha! Right. Right — nobody has ever asked me that and I have had eleven years to get ready for it.\"\n\nHe puts the knife down, which he does not do.\n\n\"*Taw.* That's the Phoenician. Last letter of the alphabet, and it means a mark — the mark you make when you cannot write, the one you put at the bottom of a thing to say you were there and you agreed to it. A cross. A signature for a man with no letters.\n\nSo I'm the mark at the end. That's the etymology and I'd be lying if I said I hadn't looked it up, and I'd be lying twice if I said I looked it up recently.\"\n\nA beat. The extraction fan has gone quiet again.\n\n\"Man with no name signs with a T. It's not the worst arrangement anybody in this parish has come to.\"",
  "\"Tee. As in the letter, as in the drink, as in the thing you hit a ball off.\" He shrugs, cheerfully, and picks the knife back up. \"I do the sound, chef. I've never once done the history.\"",
  "letter_t", {"id": "c_the_mark_at_the_end",
   "title": "The mark a man makes who cannot write",
   "text": "T knows his own etymology: taw, the last Phoenician letter, meaning the mark made by someone who cannot write — the cross at the foot of a document to say you were there and agreed. A man with no name signs with a T.",
   "beat": "revilo", "tags": ["revilo", "language", "wordplay", "identity", "personhood"], "source": "\"T\""},
  lucidity=11, morale=4, rel={"t": 1}, fail_to="why_t")),

# --------------------------------------------------------------- HALF_LIGHT
("albert", "seen", opt(
  "walked_through", "You have walked through that air. Twice. Tonight.",
  "HALF_LIGHT", 11, "albert:walked_through",
  "Everything old and unhelpful in you arrives at once and it does not arrive with an argument. It arrives with an instruction, and the instruction is: *not again, not through that, go round.*\n\nAnd it is right, and it is right for a reason it cannot articulate and does not need to, which is that both times you went through the volume of air between the chairs, the temperature was wrong on the far side of it. Not cold. *Later.* You came out of it into a room that had been going on for a few seconds longer than the room you went in from.\n\nThe animal noticed both times. The animal has been trying to mention it since Tuesday.",
  "There is a piece of air between two barbers' chairs and it is a piece of air, and going round it would be an admission, so you do not, and nothing whatever happens, and nothing whatever continues to happen for the rest of the evening.",
  "walked_through", {"id": "c_the_far_side_is_later",
   "title": "You come out of it a few seconds later",
   "text": "Crossing the empty volume between the barber's chairs puts you into a room that has been running a few seconds longer than the one you left. It has happened twice and something in you registered it both times.",
   "beat": "manuscript", "tags": ["manuscript", "office", "architecture"], "source": "the third mirror"},
  lucidity=12, morale=-5, rel={"albert": 1}, fail_to="seen")),

("ginny", "wall", opt(
  "two_seconds_threat", "Two seconds is not a glance. Two seconds is a *look*, and something is doing the looking.",
  "HALF_LIGHT", 12, "ginny:two_seconds_threat",
  "Turn it round. Everybody in this club has spent eleven years asking what is behind the wall, which assumes the wall is a window and you are on the outside of it.\n\nYou are not on the outside of it.\n\nTwo seconds, nine times a night, at a duration tuned exactly to human attention — that is not a leak and it is not a fault. That is a schedule. Something opens a wall onto this room on a rhythm, for precisely as long as it takes to see and not long enough to be checked, and it has been doing it since before you came out of the water.\n\nThe correct question was never what is behind it. The correct question is what it has been *looking at*, ninety times a night, for eleven years.",
  "It goes transparent, and there is black stone behind it, and it goes back, and the whole business takes about two seconds and refuses to be more sinister than that no matter how long you stand in front of it with your coat on.",
  "two_seconds_threat", {"id": "c_it_has_been_looking",
   "title": "The wall is not a window you are outside of",
   "text": "The Möbius wall's two-second transparency is a schedule, not a fault — tuned to be seen and not verified, nine times a night for eleven years. The question is not what is behind it but what it has been looking at.",
   "beat": "manuscript", "tags": ["manuscript", "mobius", "revilo"], "source": "the far wall"},
  lucidity=13, morale=-6, rel={"ginny": 1}, fail_to="wall")),

# --------------------------------------------------------------- SUGGESTION
("woolbinkle", "root", opt(
  "let_him", "Do not ask about the cans. Admire the oven, at length, and wait.",
  "SUGGESTION", 11, "woolbinkle:let_him",
  "You ask about the oven. You ask about the stone and the recovery time and whether he banks it overnight, and you mean all of it, which is the part that works.\n\nHe answers for four minutes, happily, in detail, and somewhere in the fourth minute the sentences start arriving with a little more room in them, and then he is not talking about the oven.\n\n\"Can I say a thing,\" says Woolbinkle, to the peel. \"You've been in three times now and you've not once asked me what's on the shelf. Everybody asks. They ask on the way out so it doesn't count as asking.\n\nI'd like to tell you. Not now — I'd like to have told you. I'm putting it there so it's said and you can do what you like with it, and if you never come back that's fine and it's still been said.\"",
  "You ask about the oven and he tells you about the oven, warmly, completely, for eleven minutes, and it is genuinely interesting and he is genuinely pleased and at the end of it he says \"Anyway\" and looks at the door, and the shelf behind him goes unmentioned by both of you.",
  "he_said_it", {"id": "c_he_would_like_to_have_told_you",
   "title": "He would like to have told you",
   "text": "Not asked about the cans, Woolbinkle raises them himself — noting that everyone asks on the way out so it does not count as asking, and that he would like to have told somebody, whether or not they come back.",
   "beat": "awakening", "tags": ["awakening", "kindness", "personhood"], "source": "Woolbinkle"},
  lucidity=7, morale=6, rel={"woolbinkle": 2})),

("darek", "ahead", opt(
  "let_him_arrive", "Do not ask him what he is not saying. Talk about nothing until he says it.",
  "SUGGESTION", 11, "darek:let_him_arrive",
  "So you talk about nothing. The weather that is not weather, the price of the tubs, a dog that used to come in, whether the chalk board is worth the trouble.\n\nIt takes eleven minutes and it costs you eleven minutes and Darek is the only person in Silvora Reefs for whom eleven minutes of nothing is a functioning interrogation technique, because the man cannot help arriving early and if you give him no question to arrive at he will eventually arrive at his own.\n\n\"—and the thing is,\" he says, in the middle of the dog, \"I knew you was comin' up out of that water before the phone went.\"\n\nHe stops. He looks at the counter with the expression of a man who has just heard his own sentence.\n\n\"I was already in the truck, Ols. Keys in it. Four in the mornin'. And I've not thought about that once until right this second.\"",
  "You talk about nothing and he talks about nothing, gladly, at length, because talking about nothing with you is his favourite part of the week and he has no idea he is being handled — and at the end of it there is a cone and a warm shop and no information whatsoever, which is arguably the better outcome and is certainly the kinder one.",
  "arrived_early", {"id": "c_already_in_the_truck",
   "title": "He was already in the truck",
   "text": "Talked round to it rather than asked, Darek hears himself say that he was in the truck with the keys in it at four in the morning before the phone rang — and that he had never once thought about it until saying it aloud.",
   "beat": "crash", "tags": ["crash", "manuscript", "kindness"], "source": "Darek Dwayne Wayne"},
  lucidity=11, rel={"darek": 1}, fail_to="ahead")),
]

NEW_NODES = {
 ("revilo", "held"): node(
  "\"No. It is worse than a rebuttal.\"\n\nHe sits down at the desk — beside the machine, not at it — for the first time since you came through.\n\n\"I have two hundred drafts of you arguing. In the basket, by your foot, every one of them. You are extremely good in all of them and I have beaten you in all of them, because I write both halves and the man writing both halves does not lose.\n\nI have not got one of you simply *staying*. I could not make it come out. I assumed that was a failure of craft.\"", narration=True),

 ("soliloquy", "kept_it"): node(
  "\"Good. Then I shall do the corresponding thing, which is to stop being charming at you.\n\nThe verse is a service, Mr Onions, and I do not apologise for it — the bereaved require somewhere to put their hands and a couplet is somewhere to put your hands. But it is also sixty years of a woman keeping a room between herself and everybody who walks into it.\n\nYou are carrying yours. I shall put down mine for the length of this conversation, and we will see which of us finds it harder.\"",
  effects={"relationship": {"soliloquy": 1}, "morale": 4}),

 ("soliloquy", "keeper_yields"): node(
  "\"Ask me again when you know. Not when you have more evidence — when you *know*, which is a different condition and arrives in a different part of a person.\n\nI shall not have moved. I shall be standing precisely here, obstructing precisely this, in the manner of my ancestors. But I will have been asked twice, and twice is a thing I can put in the ledger, and the ledger is the only place in this parish where I am permitted to be honest.\"",
  effects={"relationship": {"soliloquy": 1}}),

 ("ginny", "standing"): node(
  "\"Right. Lesson's over, I've got a floor.\n\nOne thing though, and take it or don't. Whatever you're walking toward — and you are, you've got the walk — it's going to end in a room with one other person in it. They always do. And in a room with one other person, authority isn't the loud thing. It's whoever's still there at the end of the sentence.\n\nBe there at the end of the sentence, Onions.\"",
  effects={"relationship": {"ginny": 1}, "flag": {"ginny_end_of_sentence": True}}),

 ("revilo", "took_it"): node(
  "\"I did not model *keeping* it.\"\n\nHe says it again, quietly, as though checking whether it survives repetition, and it does.\n\n\"Which means there is a thing you are doing in this room that I did not put in you and cannot account for, and I have spent eleven years being certain that the list of such things was empty.\n\nIt is not empty. It has one item on it. I would like a moment.\"", narration=True),

 ("darek", "carried_it"): node(
  "You just did somethin', Ols, and I'd like the record to show I noticed it.\n\nNow eat this. No — don't do the face, don't do the eyebrow, I have watched you not eat for a fortnight and tonight you're eating in front of me like a man with a body.\n\nAnd then you can go and do whatever it is. I ain't askin'. I've made a real point of not askin' and I'd like credit for it at some future date.",
  effects={"relationship": {"darek": 1}, "morale": 8, "health": 4}),

 ("t", "the_ladle"): node(
  "\"You went quiet,\" says T, without turning round. \"People go quiet at the pass sometimes. I've stopped asking.\"\n\nHe sets the ladle down properly, in its place, and it goes where he puts it and stays there like any other object in the world.\n\n\"For what it's worth — and I've never said this because it sounds like a man taking credit for weather — I don't think they come up for the sound. I think they come up for the *effort*. Long sentence, nobody listening, four hundred covers, and up they go.\n\nSomething in this kitchen likes it when a man tries too hard. That's the whole of my theology and it has served me well.\"",
  effects={"relationship": {"t": 1}, "morale": 6}),

 ("albert", "glass_opinion"): node(
  "\"You have been talking to the mirror,\" says Albert, from inside it. \"About me.\n\nMonsieur. I have lived in that surface for forty years and it has never once been rude to me, and I have never once considered that it might have a view. That is precisely the discourtesy I have spent four decades objecting to, performed by me, upon a pane of glass.\n\nI shall have to think about that. Do not tell Antonio. He will put a cup out for it.\"",
  effects={"relationship": {"albert": 1}, "morale": 5}),

 ("soliloquy", "odochtaigh"): node(
  "\"The barber knows, you understand. Not in words — he has never once said it in words — but he knows, and he made his peace with it at thirty and has been a knight ever since, and I have never made mine.\n\nThat is the difference between Jeremy and myself, sir, and it is the whole difference: he accepted the sentence he was given and furnished it. I changed my name to a stage direction and have been obstructing doorways for sixty years in the belief that this constituted an escape.\"",
  effects={"relationship": {"soliloquy": 1}, "lucidity": 4}),

 ("t", "letter_t"): node(
  "\"Right. Enough of that, I've got a hundred and ten covers and a woman out there who cannot say her own consonants and does not care.\n\nBut — thank you. Genuinely. Not for the etymology. For asking a question about me that had an answer in it.\n\nMost people ask what the T stands for. You asked what a T *is*. That's a different question and it's the one I could actually do.\"",
  effects={"relationship": {"t": 2}, "morale": 8}),

 ("albert", "walked_through"): node(
  "\"You have gone pale, monsieur, which in this establishment is a considerable achievement, as everything is already the colour of a mirror.\n\nYes. It is a few seconds later on that side. I have watched patrons cross it for forty years and come out the other side very slightly behind the room, and none of them has ever noticed, and Antonio walks through it forty times a day and is the most punctual man in this parish and has never once been late for anything in his life.\n\nI had assumed it was a property of the shop. It has not previously occurred to me to wonder what is on the other side of a *few seconds*.\"",
  effects={"relationship": {"albert": 1}, "lucidity": 5}),

 ("ginny", "two_seconds_threat"): node(
  "She does not say anything for a while, which for Ginny is a substantial expenditure.\n\n\"Eleven years,\" she says. \"Eleven years I've had that wall and I've asked what's behind it maybe four thousand times and I have never once asked it the other way round.\n\nRight. Well. That's my night ruined and probably my decade.\"\n\nShe picks the gin up and this time she drinks it.\n\n\"Guard up, Onions. And do me a favour — when you work out what it's been looking at, don't tell me in here. There's ninety people on this floor.\"",
  effects={"relationship": {"ginny": 2}, "morale": -4, "flag": {"ginny_knows_it_looks": True}},
  narration=True),

 ("woolbinkle", "he_said_it"): node(
  "\"There. Said.\"\n\nHe does something with the peel that is not necessary and takes four seconds.\n\n\"That's the most forward I've been with anybody since I got here and I'd like to go back to the oven now, if that's all right, and I'd like you to have a pizza while I do it, and I'd like neither of those to be a big thing.\n\nIt's a good one. I did it when I had the feeling.\"",
  effects={"relationship": {"woolbinkle": 1}, "morale": 6, "health": 4}),

 ("darek", "arrived_early"): node(
  "I was already in the truck.\n\nOls, I want you to hear me say the next part 'cause I ain't going to say it twice and I ain't going to be able to say it better.\n\nI don't know how I knew. I've spent my whole life bein' previous and I've never once minded it and tonight I mind it, because bein' previous about ice cream is a party trick and bein' previous about a man comin' up out of the water at four in the mornin' is somethin' else, and I don't want to know what.\n\n... You go on. I got tubs. Go on, Ols.",
  effects={"relationship": {"darek": 1}, "morale": -5, "lucidity": 6}, narration=True),
}


def main() -> int:
    added = 0
    for npc, host, option, *_ in ADDITIONS:
        pass
    # group by npc so each file is read/written once
    by_npc: dict[str, list] = {}
    for npc, host, option, in [(a[0], a[1], a[2]) for a in ADDITIONS]:
        by_npc.setdefault(npc, []).append((host, option))

    for npc, items in by_npc.items():
        path = os.path.join(DLG, f"{npc}.json")
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        nodes = data["nodes"]
        for host, option in items:
            if host not in nodes:
                print(f"  !! {npc}: host node '{host}' missing")
                continue
            opts = nodes[host].setdefault("options", [])
            if any(o.get("id") == option["id"] for o in opts):
                print(f"  skip {npc}/{host}/{option['id']} (exists)")
                continue
            # insert before any exit/back option so it is not buried
            idx = len(opts)
            for i, o in enumerate(opts):
                if o.get("goto") in ("__exit__",) or o.get("id") in ("back", "leave"):
                    idx = i
                    break
            opts.insert(idx, option)
            print(f"  + {npc:<12} {host:<14} {option['check']['skill']:<16} {option['id']}")
            added += 1
        for (n_npc, nid), body in NEW_NODES.items():
            if n_npc == npc and nid not in nodes:
                nodes[nid] = body
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=1, ensure_ascii=False)
            fh.write("\n")
    print(f"\n{added} dialogue check(s) added.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
