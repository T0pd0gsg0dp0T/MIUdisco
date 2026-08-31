"""The 2d6 skill check system.

Rule: 2d6 + skill + situational modifiers vs DC.

Two six-sided dice rather than one twenty-sided one, because 2d6 is a bell:
7 is the commonest result and the extremes are rare, so a check mostly
resolves the way your build says it should and the dice supply texture
rather than chaos. The skill value IS the modifier - a Logic of 4 adds 4 -
which keeps every number a player sees small, comparable and directly
meaningful. Skills run 1-6 from attributes, a little higher with
investment; DCs run about 5-14.

Skills run 1-6 from attributes (a signature specialist reaches about 8),
and DCs run 9-15:

  DC  9   most people, most days
  DC 10   takes some competence
  DC 11   a coin flip for someone who invested here
  DC 12   the standard hard check: 28% untrained, 58% for a specialist
  DC 14   go and become someone else first

The design principle that matters more than the maths: **a failed check
never blocks progress.** It forks it. Every check therefore carries both a
success and a failure narration, and the failure is written to be as
interesting as the success. A locked door the player cannot open is a bug;
a door the player breaks in a way that wakes the whole building is content.

Two check kinds, borrowed from Disco Elysium because the distinction does
real work:

  WHITE - retryable. Once the investigation state changes (a new clue, a
          skill increase, a status shift), the player may try again. These
          model persistence.
  RED   - one attempt, ever. The result is written into the world. These
          model consequence.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum

from config import CONFIG

# --- the roster ------------------------------------------------------------
#
# Twenty-four skills under four attributes. The six the game shipped with
# (LOGIC, RHETORIC, EMPATHY, PHYSIQUE, ELECTROCHEMISTRY, SAVOIR_FAIRE) keep
# their exact ids, because 205 authored checks across the content files name
# them - renaming any one of those would silently orphan real writing. They
# happen to spread across all four attributes already, so they anchor the
# roster rather than sitting awkwardly inside it.
#
# The attributes are deliberately NOT named "PHYSIQUE": that id is taken by a
# skill, and a system where `PHYSIQUE` means two different things depending on
# which dict you reach into is a bug with a countdown on it.

ATTRIBUTES = ["INTELLECT", "PSYCHE", "FORTITUDE", "MOTORICS"]

ATTRIBUTE_DESCRIPTIONS = {
    "INTELLECT": (
        "The mind that parses. Deduction, vocabulary, the reconstruction of "
        "events from what they left behind."
    ),
    "PSYCHE": (
        "The mind that feels. Other people, your own interior, and the parts "
        "of both that do not answer to argument."
    ),
    "FORTITUDE": (
        "The body that endures. Appetite, damage, fear, and the town coming "
        "in through the skin."
    ),
    "MOTORICS": (
        "The body that acts. Precision, timing, poise, and the machines a "
        "town like this leaves lying about."
    ),
}

# attribute -> its six skills, in sheet order.
ATTRIBUTE_SKILLS = {
    "INTELLECT": [
        "LOGIC",
        "RHETORIC",
        "ETYMOLOGY",
        "ENCYCLOPEDIA",
        "VISUAL_CALCULUS",
        "CONCEPTUALISATION",
    ],
    "PSYCHE": [
        "EMPATHY",
        "INLAND_EMPIRE",
        "AUTHORITY",
        "VOLITION",
        "VOX_POPULI",
        "SUGGESTION",
    ],
    "FORTITUDE": [
        "PHYSIQUE",
        "ELECTROCHEMISTRY",
        "PAIN_THRESHOLD",
        "SHIVERS",
        "HALF_LIGHT",
        "SEA_LEGS",
    ],
    "MOTORICS": [
        "SAVOIR_FAIRE",
        "PERCEPTION",
        "COMPOSURE",
        "REACTION_SPEED",
        "HAND_EYE",
        "INTERFACING",
    ],
}

SKILLS = [skill for attr in ATTRIBUTES for skill in ATTRIBUTE_SKILLS[attr]]

SKILL_ATTRIBUTE = {
    skill: attr for attr, skills in ATTRIBUTE_SKILLS.items() for skill in skills
}

# What each skill is for, shown on the character sheet and used to pick which
# voice comments on what. Tuned to Silvora Reefs - a town made of wordplay,
# built on a harbour, running on a manuscript - rather than to a generic
# detective.
SKILL_DESCRIPTIONS = {
    # --- INTELLECT ---
    "LOGIC": (
        "Deduction, contradiction, the tyranny of the coherent. Logic wants "
        "the world to add up, and grows louder the less it does."
    ),
    "RHETORIC": (
        "Argument as architecture. Wordplay as leverage. Your best skill and "
        "the reason people leave the room."
    ),
    "ETYMOLOGY": (
        "Where a word has been before it got here. In a town whose every "
        "name is a pun with a job, this is not trivia. It is cartography."
    ),
    "ENCYCLOPEDIA": (
        "The silt of everything you have ever read, still settling. Offers "
        "the relevant fact and four adjacent ones nobody asked for."
    ),
    "VISUAL_CALCULUS": (
        "Reconstructing the event from what it left. Angles, dust, the shape "
        "of an absence. The part of you that reads a room backwards."
    ),
    "CONCEPTUALISATION": (
        "What a thing is *about*. Metaphor, composition, the difference "
        "between a detail and a motif. Dangerous in a world that is written."
    ),
    # --- PSYCHE ---
    "EMPATHY": (
        "Reading the room, the face, the pause before the answer. Knows what "
        "a person is protecting."
    ),
    "INLAND_EMPIRE": (
        "The hunch that arrives fully dressed and refuses to explain itself. "
        "Lets objects have opinions and occasionally believes them."
    ),
    "AUTHORITY": (
        "Standing, and the use of it. The voice that ends a conversation. "
        "Fragile in exact proportion to how much you need it to work."
    ),
    "VOLITION": (
        "The part that holds. Resolve against despair, against a drink, "
        "against a very reasonable argument that you do not exist."
    ),
    "VOX_POPULI": (
        "The town thinking about itself, briefly audible. What the other "
        "Reefers are doing while you are not in the room."
    ),
    "SUGGESTION": (
        "Charm as a delivery mechanism. Leading a person to a conclusion and "
        "letting them find it themselves, pleased."
    ),
    # --- FORTITUDE ---
    "PHYSIQUE": (
        "The body you have neglected in favour of the sentence you were "
        "composing. It endures anyway."
    ),
    "ELECTROCHEMISTRY": (
        "Appetite. Gin, donuts, smoke, the fine greens. Volunteers "
        "enthusiastically and is almost never correct."
    ),
    "PAIN_THRESHOLD": (
        "How much of it you can hold without putting it down. Knows the "
        "difference between an injury and an insult, and takes both."
    ),
    "SHIVERS": (
        "Silvora Reefs on your skin. The green lampposts, the fog with the "
        "rotors in it, the parish going about its business four streets over."
    ),
    "HALF_LIGHT": (
        "The oldest voice you have. Threat, teeth, the animal that wants to "
        "act before the sentence finishes. Frequently wrong and never quiet."
    ),
    "SEA_LEGS": (
        "Balance, in a harbour town that does not hold still. Weathering the "
        "literal storm and the other kind with the same set of knees."
    ),
    # --- MOTORICS ---
    "SAVOIR_FAIRE": (
        "Knowing how, and knowing when. Timing, sleight, the unremarked exit. "
        "Grace under observation, and the good sense to stop talking."
    ),
    "PERCEPTION": (
        "What the room is doing while you look at one part of it. The detail "
        "at the edge, the sound underneath, the thing that has moved."
    ),
    "COMPOSURE": (
        "Not showing it. Posture, the level voice, the tell you decline to "
        "give. What is left of dignity, deployed tactically."
    ),
    "REACTION_SPEED": (
        "The fast thing, before deliberation gets a vote. Catches the glass, "
        "the slip, the half-second where a face forgets to be careful."
    ),
    "HAND_EYE": (
        "Precision of the hands. The steady pour, the exact cut, the page "
        "turned without tearing what is left of it."
    ),
    "INTERFACING": (
        "Machines, locks, mechanisms, and the things a typewriter knows. "
        "Understands objects by their working parts rather than their names."
    ),
}


class CheckKind(Enum):
    WHITE = "white"   # retryable once circumstances change
    RED = "red"       # one attempt, permanently resolved


@dataclass
class CheckResult:
    """Everything the narration layer needs to describe what just happened."""

    skill: str
    dc: int
    roll: int = 0
    modifier: int = 0
    total: int = 0
    success: bool = False
    critical: bool = False
    fumble: bool = False
    kind: CheckKind = CheckKind.WHITE
    # Populated when the check was skipped because it was already resolved.
    already_resolved: bool = False
    breakdown: list[str] = field(default_factory=list)

    @property
    def margin(self) -> int:
        return self.total - self.dc

    def describe(self) -> str:
        """Human-readable dice math, printed when features.show_dice is on."""
        parts = " ".join(self.breakdown)
        verdict = "SUCCESS" if self.success else "FAILURE"
        if self.critical:
            verdict = "CRITICAL SUCCESS"
        elif self.fumble:
            verdict = "CRITICAL FAILURE"
        label = self.skill.replace("_", "-").title()
        return (
            f"{label} {self.kind.value} check  "
            f"2d6({self.roll}) {parts} = {self.total} vs {self.dc}  ->  {verdict}"
        )


#: How many dice, and of what size. Exposed so the tests and the odds
#: readout cannot drift away from the roller.
DICE_COUNT = 2
DICE_SIDES = 6
DICE_MIN = DICE_COUNT
DICE_MAX = DICE_COUNT * DICE_SIDES


def modifier_for(value: int) -> int:
    """A skill's contribution to a roll.

    Identity, deliberately: under 2d6 the skill number and the bonus it
    grants are the same small number, so "Logic 4" needs no arithmetic to
    interpret. The function is kept rather than inlined because the sheet,
    the odds readout and the roller must never disagree about this.
    """
    return value


def status_modifiers(player, skill: str) -> list[tuple[str, int]]:
    """Situational modifiers derived from Oliver's current condition.

    These are the mechanical teeth of the status system: intoxication is a
    genuine trade-off rather than a penalty, morale gates persuasion, and
    exhaustion taxes the body.
    """
    mods: list[tuple[str, int]] = []
    attribute = SKILL_ATTRIBUTE.get(skill)

    # Intoxication (0-10) sharpens appetite and blunts precision. The trade is
    # deliberately steep at the top end so that drinking is a real decision.
    intox = player.intoxication
    if intox:
        step = (intox + 1) // 2
        if skill in ("ELECTROCHEMISTRY", "HALF_LIGHT"):
            # Disinhibition. The appetite and the animal both get louder.
            mods.append(("intoxicated", step))
        elif skill in ("LOGIC", "VISUAL_CALCULUS", "ENCYCLOPEDIA"):
            mods.append(("intoxicated", -step))
        elif skill in ("INLAND_EMPIRE", "SHIVERS") and intox >= 4:
            # The intuitive channels open up. Whether that is insight or
            # gin is left, deliberately, as an exercise for the player.
            mods.append(("loosened", 1))
        elif skill == "RHETORIC" and intox >= 6:
            # Past a point the wordplay stops landing and starts alliterating.
            mods.append(("slurring", -1))
        elif skill in ("PHYSIQUE", "SEA_LEGS") and intox >= 7:
            mods.append(("unsteady", -2))
        elif attribute == "MOTORICS" and intox >= 5:
            mods.append(("unsteady hands", -1))

    # Morale (0-100) is confidence, and confidence is most of PSYCHE.
    if player.morale <= 25:
        if skill in ("RHETORIC", "EMPATHY", "AUTHORITY", "SUGGESTION", "COMPOSURE"):
            mods.append(("low morale", -2))
    elif player.morale >= 80:
        if skill in ("RHETORIC", "EMPATHY", "AUTHORITY", "SUGGESTION", "COMPOSURE"):
            mods.append(("high morale", 1))

    # Health (0-100) is the body's willingness to co-operate.
    hurt_by_injury = ("PHYSIQUE", "SEA_LEGS", "HAND_EYE", "REACTION_SPEED")
    if player.health <= 30 and skill in hurt_by_injury:
        mods.append(("injured", -3))
    elif player.health <= 60 and skill in hurt_by_injury:
        mods.append(("battered", -1))
    # Pain Threshold is the one skill that reads damage as evidence rather
    # than as an obstacle: it gets better the worse you are doing.
    if player.health <= 50 and skill == "PAIN_THRESHOLD":
        mods.append(("hurting", 2))

    if player.exhaustion >= 8:
        mods.append(("exhausted", -2))
    elif player.exhaustion >= 5 and attribute in ("INTELLECT", "MOTORICS"):
        mods.append(("tired", -1))

    # Lucidity: the more Oliver suspects the world is a manuscript, the less
    # the world's internal logic constrains him - and the worse Logic performs,
    # because there is genuinely nothing coherent left to deduce. The channels
    # that were never asking for coherence in the first place get better.
    if player.lucidity >= 45:
        if skill in ("LOGIC", "ENCYCLOPEDIA"):
            mods.append(("lucid", -1))
        if skill in ("RHETORIC", "SAVOIR_FAIRE", "INLAND_EMPIRE", "SHIVERS",
                     "CONCEPTUALISATION"):
            mods.append(("lucid", 1))

    # Equipment. The monocle is not a clue to be found - Oliver already wears
    # it - it is a standing instrument that makes hidden structure legible.
    if player.has_item("monocle") and skill in (
        "LOGIC", "SAVOIR_FAIRE", "PERCEPTION", "VISUAL_CALCULUS", "INTERFACING"
    ):
        mods.append(("monocle", 1))
    if player.has_item("cane") and skill in ("PHYSIQUE", "SEA_LEGS"):
        mods.append(("onion cane", 1))

    return mods


def roll_check(
    player,
    skill: str,
    dc: int,
    context: str = "",
    kind: CheckKind | str = CheckKind.WHITE,
    bonus: int = 0,
    bonus_label: str = "circumstance",
    rng: random.Random | None = None,
) -> CheckResult:
    """Resolve one skill check.

    `context` is a free-text tag used for logging and for the retry ledger.
    `bonus` covers one-off modifiers granted by clues, Furthermore's advice,
    or an NPC's goodwill.
    """
    if isinstance(kind, str):
        kind = CheckKind(kind)
    if skill not in SKILLS:
        raise ValueError(f"unknown skill: {skill}")

    generator = rng or random
    difficulty = dc + CONFIG["difficulty"]["dc_offset"]

    result = CheckResult(skill=skill, dc=difficulty, kind=kind)
    result.roll = sum(
        generator.randint(1, DICE_SIDES) for _ in range(DICE_COUNT)
    )

    total_mod = modifier_for(player.skill(skill))
    breakdown = [f"{total_mod:+d}(skill)"]

    for label, amount in status_modifiers(player, skill):
        total_mod += amount
        breakdown.append(f"{amount:+d}({label})")

    if bonus:
        total_mod += bonus
        breakdown.append(f"{bonus:+d}({bonus_label})")

    result.modifier = total_mod
    result.total = result.roll + total_mod
    result.breakdown = breakdown

    crit = CONFIG["difficulty"]["critical_success"]
    fumble = CONFIG["difficulty"]["critical_failure"]

    if result.roll >= crit:
        result.success = True
        result.critical = True
    elif result.roll <= fumble:
        result.success = False
        result.fumble = True
    else:
        result.success = result.total >= result.dc

    return result


class CheckLedger:
    """Remembers which checks have been attempted, and how they went.

    This is what makes white/red checks meaningful and what lets a location
    show different text on a second visit. It lives on the game state and is
    serialised with the save.
    """

    def __init__(self) -> None:
        # check_id -> {"resolved": bool, "success": bool, "attempts": int,
        #              "kind": str, "state_token": str}
        self.records: dict[str, dict] = {}

    def attempted(self, check_id: str) -> bool:
        return check_id in self.records

    def succeeded(self, check_id: str) -> bool:
        record = self.records.get(check_id)
        return bool(record and record["success"])

    def can_attempt(self, check_id: str, kind: CheckKind, state_token: str) -> bool:
        """May the player roll this check right now?

        A red check may be attempted once. A white check may be re-attempted
        whenever `state_token` differs from the token recorded at the last
        attempt - that token is a fingerprint of the investigation state, so
        "come back when you know more" is enforced mechanically rather than
        by the player spamming the same option.
        """
        record = self.records.get(check_id)
        if record is None:
            return True
        if record["success"]:
            return False
        if kind is CheckKind.RED:
            return False
        if not CONFIG["difficulty"]["allow_white_retry"]:
            return False
        if record.get("state_token") != state_token:
            return True
        # Backstop: a player who has failed this repeatedly has earned the
        # attempt whether or not anything else has moved. Without this, a
        # check inside a location with no exits and nothing left to examine
        # can lock permanently - which cost the best ending in a playtest.
        #
        # The threshold must be *reachable*: attempts only increment while the
        # check is unlocked, so a value above what a stuck player can actually
        # accumulate never fires. Two works - one free attempt, one more after
        # any single state change. The first version of this fix shipped with
        # three, which was unreachable and therefore did nothing at all.
        return record.get("attempts", 0) >= CONFIG["difficulty"]["retry_after_failures"]

    def record(self, check_id: str, result: CheckResult, state_token: str) -> None:
        entry = self.records.setdefault(
            check_id,
            {"resolved": False, "success": False, "attempts": 0, "kind": result.kind.value},
        )
        entry["attempts"] += 1
        entry["success"] = entry["success"] or result.success
        entry["kind"] = result.kind.value
        entry["state_token"] = state_token
        entry["resolved"] = result.success or result.kind is CheckKind.RED

    def to_dict(self) -> dict:
        return {"records": self.records}

    @classmethod
    def from_dict(cls, data: dict) -> "CheckLedger":
        ledger = cls()
        ledger.records = data.get("records", {})
        return ledger
