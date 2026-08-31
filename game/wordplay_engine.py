"""Linguistic machinery: reversals, anagrams, homophones, alliteration.

An honest note on scope, because this is the module most likely to be
oversold. Generating *good* alliterative prose procedurally is not
achievable at this budget - naive synonym substitution produces nonsense
that reads as a bug rather than as a flourish. So this module splits into
two halves:

  1. Real computation, on real letters. Reversal and anagram detection are
     exact, verifiable operations, and the lorebook's central pun survives
     them: "Oliver Onions" reversed character-for-character is exactly
     "Snoino Revilo". That is a puzzle the player can be invited to solve
     and the engine can check.

  2. Curated banks. Alliteration, homophones and the Woolbinkle can/can't
     tangle are authored, indexed, and selected - not generated. The engine
     picks; the writer wrote.

The intoxication hook applies (2): as Oliver drinks, his narration draws
from alliterative variants where the content file supplies them.
"""

from __future__ import annotations

import random
import re

from config import CONFIG

# --- 1. exact letter operations --------------------------------------------


def letters_only(text: str) -> str:
    """Lowercase alphabetic characters, in order. Accents folded crudely."""
    folded = (
        text.lower()
        .replace("ö", "o")
        .replace("é", "e")
        .replace("è", "e")
        .replace("ü", "u")
        .replace("ä", "a")
    )
    return re.sub(r"[^a-z]", "", folded)


def reverse_string(text: str) -> str:
    """Reverse the letters of `text`, preserving nothing else."""
    return letters_only(text)[::-1]


def is_reversal(first: str, second: str) -> bool:
    """True if the two strings are exact letter-for-letter reversals.

    >>> is_reversal("Oliver Onions", "Snoino Revilo")
    True
    """
    return bool(letters_only(first)) and reverse_string(first) == letters_only(second)


def is_anagram(first: str, second: str) -> bool:
    """True if the two strings use exactly the same letters."""
    a, b = letters_only(first), letters_only(second)
    return bool(a) and sorted(a) == sorted(b)


def anagram_report(first: str, second: str) -> str:
    """Explain the relationship between two strings, whatever it turns out to be.

    Used by the RHETORIC checks that let Oliver interrogate a sign. It tells
    the truth even when the truth is 'these do not match', because a town
    that rearranges letters *incorrectly* is more unsettling than one that
    does it perfectly.
    """
    a, b = letters_only(first), letters_only(second)
    if is_reversal(first, second):
        return f"'{first}' reversed is '{second}'. Exactly. Not approximately."
    if is_anagram(first, second):
        return f"'{first}' and '{second}' are built from identical letters."
    shared = sorted(set(a) & set(b))
    surplus = sorted(set(b) - set(a))
    detail = f"shared: {''.join(shared) or 'none'}"
    if surplus:
        detail += f"; letters in '{second}' that were never in '{first}': {''.join(surplus)}"
    return (
        f"'{first}' does not rearrange into '{second}'. It is close enough to "
        f"read as if it did, which is worse ({detail})."
    )


# --- 2. curated banks -------------------------------------------------------

# Names whose joke is phonetic. Oliver's ear catches these; the player's may
# not, so RHETORIC and SAVANT-FAIRE offer to explain them once each.
PHONETIC_JOKES: dict[str, str] = {
    "darek": (
        "Darek Dwayne Wayne. Say it at speed, in his drawl, and it is "
        "'Durry Kwain' - the man is his own signage."
    ),
    "durry_kwain": (
        "The restaurant is named after the way its manager's name sounds "
        "when he says it. Or the manager is named after the restaurant. "
        "Nobody in Silvora Reefs considers this a chicken-and-egg problem."
    ),
    "rishrush": (
        "Chef D. Rishrush. 'Delicious', pronounced by a mouth with no teeth "
        "in it. The name is a recipe for saying the name."
    ),
    "ben": (
        "Wutchu 'Ben' Uptu. What you been up to. He greets you with his own "
        "name and it lands as a question every time."
    ),
    "mary": (
        "Mary Guana. An iguana called Mary Guana, who deals in fine greens. "
        "The joke has three floors and she lives on all of them."
    ),
    "sir_jerry": (
        "Sir Jerry. Surgery. A barber-surgeon whose name is his profession "
        "held slightly too long at the end."
    ),
    "ginja": (
        "Ginny 'Gin' Ginja. Not by the hair of her chinny chin chin, and she "
        "will not be blown down, and she drinks the good stuff."
    ),
    "wino_t": (
        "Wino-T. Why not. A whole philosophy compressed into two syllables "
        "and a hyphen."
    ),
    "asimov": (
        "Asimov Sobeleaux. Say the surname and listen: 'so below'. As above, "
        "so below, and this building's second floor hangs from the sky."
    ),
    "soliloquy": (
        "Soliloquy. A speech delivered to nobody, by the woman who keeps the "
        "town's supply of nobody."
    ),
    "insta_gators": (
        "The Insta-gators. Instigators. Alligators. Instant. Three jokes, one "
        "security detail, no warning."
    ),
}

# Woolbinkle's can/can't/can-can/cantaloupe/elope/antelope tangle, the
# lorebook's longest sustained piece of wordplay. Offered as escalating
# fragments so a conversation can pay it out over several exchanges.
CANT_ELOPE = [
    "If he and she can't elope, he can can a belle easier than he can can a bull.",
    "Any do-well bull antelope must can-can, and well - and he can't. But "
    "that's bull. He can can-can as well as any canny bull antelope can hope.",
    "So he un-canned his own canned cantaloupe and went cannibal on that canny "
    "belle, and cooked her with some cantaloupe.",
    "A dish he calls 'Can't Elope Antelope with Fresh Canned Cantaloupe'. Now "
    "that antelope belle can't very well elope with any other bull antelope.",
]

# Alliterative connective tissue, banked by letter. Drawn on when Oliver is
# drunk enough that his narration starts organising itself by sound rather
# than sense. Authored, not generated - see the module docstring.
ALLITERATION_BANK: dict[str, list[str]] = {
    "b": ["a bruised and blundering brightness", "brackish, bothersome, brief"],
    "c": ["crooked, careful, and catastrophically calm", "a curdled little clarity"],
    "d": ["dim, deliberate, and deeply disinclined", "a drowsy, dreadful decorum"],
    "g": ["gilt, gutted, and grinning", "a green and grieving gloom"],
    "l": ["long, lightless, and lovely", "a lolling, luminous lie"],
    "m": ["mauve, molten, and mildly malicious", "a murmuring municipal murk"],
    "p": ["purple, patient, and perfectly plausible", "a prim, persistent pretence"],
    "s": ["slow, salted, and softly seditious", "a susurrus of settled secrets"],
    "t": ["twilit, tilted, and terribly tidy", "a thin, tolerant tremor"],
    "w": ["wet, watchful, and wholly welcoming", "a wan, wandering warmth"],
}


def alliterative_flourish(seed: str, rng: random.Random | None = None) -> str:
    """Return a banked alliterative phrase keyed to `seed`'s first letter.

    Returns an empty string when the bank has nothing for that letter, which
    the caller must treat as "add nothing" rather than substituting filler.
    """
    if not CONFIG["features"]["wordplay"]:
        return ""
    key = letters_only(seed)[:1]
    options = ALLITERATION_BANK.get(key)
    if not options:
        return ""
    return (rng or random).choice(options)


def intoxication_flourish(
    text: str, intoxication: int, rng: random.Random | None = None
) -> str:
    """Optionally append an alliterative aside, scaled by how drunk Oliver is.

    Below 4 this does nothing at all. The effect is meant to creep up on the
    player, not to announce itself.
    """
    if not CONFIG["features"]["wordplay"] or intoxication < 4:
        return text
    generator = rng or random
    chance = min(0.6, 0.08 * intoxication)
    if generator.random() > chance:
        return text
    anchor = next((word for word in text.split() if len(word) > 4), text)
    flourish = alliterative_flourish(anchor, generator)
    if not flourish:
        return text
    return f"{text} Everything here is {flourish}."


def phonetic_note(key: str) -> str:
    """Look up a curated name-joke explanation. Empty string if absent."""
    if not CONFIG["features"]["wordplay"]:
        return ""
    return PHONETIC_JOKES.get(key, "")


def cant_elope(index: int) -> str:
    """Fetch one escalating fragment of the Woolbinkle tangle."""
    if not CANT_ELOPE:
        return ""
    return CANT_ELOPE[min(index, len(CANT_ELOPE) - 1)]
