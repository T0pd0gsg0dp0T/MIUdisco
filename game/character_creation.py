"""Character creation: deciding what kind of mind is going to do this.

Four attributes, twenty-four skills, and a set of decisions made before the
first cycle that the whole run then has to live inside. This exists because
a fixed six-skill Oliver gives a second playthrough nothing new to be - the
prose is the same, the checks land the same way, and the only variable left
is dice. An investigator who dumped everything into Fortitude meets a
genuinely different Silvora Reefs from one who went all Intellect: different
checks pass, different skills interrupt, different things get noticed at
all.

The flow, all of it selectable, none of it typed:

  1. An archetype - four pre-built minds, or Custom.
  2. (Custom only) distribute attribute points.
  3. Spend individual skill points.
  4. Choose a signature skill.
  5. Confirm, with a chance to go back and start over.

Archetypes are not shortcuts to a lesser version of this. They are the same
data a custom build produces, pre-filled by someone who has thought about
it, because "I do not yet know what these twenty-four words mean" is the
normal state of a first-time player and making them guess is bad design.
"""

from __future__ import annotations

import ui
from config import CONFIG
from skill_checks import (
    ATTRIBUTES,
    ATTRIBUTE_DESCRIPTIONS,
    ATTRIBUTE_SKILLS,
    SKILLS,
    SKILL_DESCRIPTIONS,
    modifier_for,
)

#: name -> (blurb, attributes, skill investments, signature)
ARCHETYPES: dict[str, tuple[str, dict[str, int], list[str], str]] = {
    "The Rhetorician": (
        "You talk. It is the whole of your method and most of your problem. "
        "Doors open because you argued them open, and close behind you for "
        "the same reason.",
        {"INTELLECT": 5, "PSYCHE": 3, "FORTITUDE": 2, "MOTORICS": 2},
        ["RHETORIC", "ETYMOLOGY", "SUGGESTION", "CONCEPTUALISATION"],
        "RHETORIC",
    ),
    "The Empiricist": (
        "Things leave marks. You read the marks. You would rather have one "
        "measured fact than an afternoon of somebody's feelings about it.",
        {"INTELLECT": 4, "PSYCHE": 2, "FORTITUDE": 2, "MOTORICS": 4},
        ["VISUAL_CALCULUS", "PERCEPTION", "LOGIC", "INTERFACING"],
        "VISUAL_CALCULUS",
    ),
    "The Sensitive": (
        "You feel the room before you enter it. Half of what you know arrived "
        "without paperwork and none of it will hold up in a report.",
        {"INTELLECT": 2, "PSYCHE": 5, "FORTITUDE": 3, "MOTORICS": 2},
        ["INLAND_EMPIRE", "EMPATHY", "SHIVERS", "VOX_POPULI"],
        "INLAND_EMPIRE",
    ),
    "The Survivor": (
        "You came out of the harbour and you are still walking. The body has "
        "opinions now, and it has earned them, and it is usually right.",
        {"INTELLECT": 2, "PSYCHE": 2, "FORTITUDE": 5, "MOTORICS": 3},
        ["PHYSIQUE", "PAIN_THRESHOLD", "HALF_LIGHT", "SEA_LEGS"],
        "PAIN_THRESHOLD",
    ),
}


def _skill_label(name: str) -> str:
    return name.replace("_", "-").title()


def _preview(player) -> list[str]:
    """The build as it currently stands, attribute by attribute."""
    lines = []
    for attribute in ATTRIBUTES:
        score = player.attribute(attribute)
        lines.append(f"{attribute.title()} {score}")
        parts = []
        for skill in ATTRIBUTE_SKILLS[attribute]:
            value = player.skill(skill)
            star = "*" if skill == player.signature_skill else ""
            parts.append(f"{_skill_label(skill)}{star} {value} [{modifier_for(value):+d}]")
        lines.append("   " + " · ".join(parts))
    return lines


def _distribute_attributes(player) -> None:
    """Spend the attribute pool, one point at a time.

    One point at a time rather than a typed number per attribute: it keeps
    the whole thing inside the same select-and-confirm idiom as the rest of
    the game, and it lets the running preview update between every choice so
    the player can watch what a point actually buys.
    """
    pool = CONFIG["player"]["attribute_points"]
    ceiling = CONFIG["player"]["attribute_max"]
    for attribute in ATTRIBUTES:
        player.set_attribute(attribute, 1)

    while pool > 0:
        ui.blank()
        ui.aside(f"{pool} attribute point{'s' if pool != 1 else ''} left.")
        for line in _preview(player):
            ui.narrate(line)

        options = []
        targets = []
        for attribute in ATTRIBUTES:
            score = player.attribute(attribute)
            if score >= ceiling:
                continue
            options.append(
                f"{attribute.title()} {score} → {score + 1}   "
                f"{ATTRIBUTE_DESCRIPTIONS[attribute].split('.')[0]}."
            )
            targets.append(attribute)
        if not targets:
            break
        choice = ui.menu(options)
        if 0 <= choice < len(targets):
            player.set_attribute(targets[choice], player.attribute(targets[choice]) + 1)
            pool -= 1


def _spend_skill_points(player) -> None:
    """Individual +1s, chosen from within one attribute at a time.

    Presenting all twenty-four at once is a wall of unfamiliar words. Asking
    which attribute first turns it into two small readable choices, and it
    reinforces the structure the player just spent points on.
    """
    pool = CONFIG["player"]["skill_points"]
    while pool > 0:
        ui.blank()
        ui.aside(f"{pool} skill point{'s' if pool != 1 else ''} left.")
        attr_choice = ui.menu(
            [
                f"{attribute.title()} {player.attribute(attribute)}   "
                f"{ATTRIBUTE_DESCRIPTIONS[attribute].split('.')[0]}."
                for attribute in ATTRIBUTES
            ]
            + ["Keep the rest. Some things are better left unpractised."]
        )
        if attr_choice < 0 or attr_choice >= len(ATTRIBUTES):
            return
        attribute = ATTRIBUTES[attr_choice]

        ui.blank()
        skills = ATTRIBUTE_SKILLS[attribute]
        labels = []
        for skill in skills:
            value = player.skill(skill)
            labels.append(
                f"{_skill_label(skill)} {value} → {value + 1}   "
                f"{SKILL_DESCRIPTIONS[skill].split('.')[0]}."
            )
        labels.append("Back.")
        skill_choice = ui.menu(labels)
        if 0 <= skill_choice < len(skills):
            player.invest_skill(skills[skill_choice], 1)
            pool -= 1


def _choose_signature(player) -> None:
    """The one skill that is *you*, worth a flat bonus and a louder voice."""
    bonus = CONFIG["player"]["signature_bonus"]
    ui.blank()
    ui.narrate(
        "One of them is you. Not your best - the one that talks first, that "
        "you reach for without deciding to, that people will describe you by "
        "afterwards."
    )
    attr_choice = ui.menu(
        [
            f"{attribute.title()}   {ATTRIBUTE_DESCRIPTIONS[attribute].split('.')[0]}."
            for attribute in ATTRIBUTES
        ]
    )
    attribute = ATTRIBUTES[max(0, min(attr_choice, len(ATTRIBUTES) - 1))]

    ui.blank()
    skills = ATTRIBUTE_SKILLS[attribute]
    choice = ui.menu(
        [
            f"{_skill_label(skill)}   {SKILL_DESCRIPTIONS[skill].split('.')[0]}."
            for skill in skills
        ]
    )
    skill = skills[max(0, min(choice, len(skills) - 1))]
    player.signature_skill = skill
    player.invest_skill(skill, bonus)


def _apply_archetype(player, name: str) -> None:
    _blurb, attributes, investments, signature = ARCHETYPES[name]
    for attribute, value in attributes.items():
        player.set_attribute(attribute, value)
    for skill in investments:
        player.invest_skill(skill, 1)
    player.signature_skill = signature
    player.invest_skill(signature, CONFIG["player"]["signature_bonus"])


def _reset(player) -> None:
    for attribute in ATTRIBUTES:
        player.set_attribute(attribute, 1)
    for skill in SKILLS:
        player._skill_points[skill] = 0
    player.signature_skill = None


def run(player) -> None:
    """Build the mind. Loops until the player confirms."""
    while True:
        _reset(player)

        ui.blank()
        ui.heading("What Kind of Mind")
        ui.narrate(
            "Twenty-four ways of paying attention, hanging off four ways of "
            "being a person. You do not get all of them. What you get instead "
            "is a shape, and the shape is going to decide which parts of "
            "Silvora Reefs are legible to you and which parts go past unread."
        )

        names = list(ARCHETYPES)
        choice = ui.menu(
            [f"{name} — {ARCHETYPES[name][0].split('.')[0]}." for name in names]
            + ["Custom. I will decide what I am."]
        )

        if 0 <= choice < len(names):
            _apply_archetype(player, names[choice])
            ui.blank()
            ui.narrate(ARCHETYPES[names[choice]][0])
        else:
            _distribute_attributes(player)
            _spend_skill_points(player)
            _choose_signature(player)

        ui.blank()
        ui.heading("The Shape of You")
        for line in _preview(player):
            ui.narrate(line)
        if player.signature_skill:
            ui.aside(
                f"Signature: {_skill_label(player.signature_skill)} — it speaks "
                f"first, and more often than the rest."
            )

        ui.blank()
        if ui.menu(["Yes. Begin.", "No. Start again."]) == 0:
            return
