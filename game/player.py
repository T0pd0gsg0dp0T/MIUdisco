"""Oliver Otto Onions: skills, status, inventory, thought cabinet.

Characterisation follows the lorebook rather than any summary of it: Oliver
is a 44-year-old crash survivor and concerned citizen turned investigator,
raised by an artist and an actress, orphaned at eighteen, sardonic and
inquisitive. He is not an academic. He simply cannot stop talking.

Equipment note: the gold monocle is *starting equipment*, not a discovery.
The lorebook is explicit that it is his most distinctive accessory and that
it reveals hidden aspects of reality. Making it a tool the player wields
from cycle one is worth far more than making it a plot token found in act
one, because it turns "look harder" into a verb.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from config import CONFIG
from skill_checks import (
    ATTRIBUTES,
    ATTRIBUTE_SKILLS,
    SKILLS,
    SKILL_ATTRIBUTE,
    SKILL_DESCRIPTIONS,
    modifier_for,
)


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


@dataclass
class Item:
    id: str
    name: str
    description: str


STARTING_ITEMS = [
    Item(
        "monocle",
        "gold monocle",
        "Gold rim, gold chain, a lens that has never once been merely glass. "
        "Through it, things admit what they are made of.",
    ),
    Item(
        "watch",
        "gold pocket watch",
        "Stopped at 3:33. It has been stopped at 3:33 for as long as there "
        "has been a 3:33 to be stopped at.",
    ),
    Item(
        "cane",
        "cane with a gold onion handle",
        "The handle is an onion. The onion is gold. Layers, presumably, were "
        "the joke, and nobody has ever had to explain it twice.",
    ),
    Item(
        "notebook",
        "waterlogged notebook",
        "Came out of the crash. Most pages are a blue smear. Three are not, "
        "and those three are in your handwriting, and you do not remember "
        "writing them.",
    ),
]


class Player:
    """Oliver's mutable state."""

    # Under 2d6 the skill value *is* the modifier, so a skill's floor is
    # simply its attribute: Fortitude 4 means all six Fortitude skills sit
    # at 4 and add 4 to a roll. Every number the player sees is small and
    # means exactly one thing.
    ATTRIBUTE_BASE = 0
    ATTRIBUTE_STEP = 1

    def __init__(self) -> None:
        cfg = CONFIG["player"]
        self.name = "Oliver Otto Onions"
        # The game opens in the wreckage with no idea who that is. Every
        # surface that would print the name prints `display_name` instead,
        # so the status bar cannot quietly hand the player the answer to
        # the question the first act is asking.
        self.name_known = False
        self._attributes: dict[str, int] = dict(cfg["attributes"])
        # Points spent on individual skills at creation, over and above what
        # the parent attribute already grants.
        self._skill_points: dict[str, int] = {s: 0 for s in SKILLS}
        # Permanent bonuses granted by internalised thoughts.
        self._skill_bonuses: dict[str, int] = {s: 0 for s in SKILLS}
        self.signature_skill: str | None = None

        self.morale: int = cfg["morale"]
        self.health: int = cfg["health"]
        self.intoxication: int = cfg["intoxication"]
        # Backed by a float: gains late in the curve are fractional and would
        # otherwise round to nothing. Exposed as an int property so that
        # assigning `player.lucidity = 70` keeps both in step.
        self._lucidity_exact: float = float(cfg["lucidity"])
        self.exhaustion: int = 0

        self.inventory: dict[str, Item] = {item.id: item for item in STARTING_ITEMS}

        # Thought cabinet. Thoughts are internalised over a number of cycles
        # and then confer a permanent effect - see furthermore.py.
        self.thoughts_known: list[str] = []
        self.thoughts_internalising: dict[str, int] = {}  # id -> cycles remaining
        self.thoughts_internalised: list[str] = []

    # --- skills ------------------------------------------------------------

    #: What to call yourself before you have found out.
    UNKNOWN_NAME = "the man from the harbour"

    @property
    def display_name(self) -> str:
        return self.name if self.name_known else self.UNKNOWN_NAME

    def learn_name(self) -> bool:
        """Returns True the first time, so the caller can narrate it."""
        if self.name_known:
            return False
        self.name_known = True
        return True

    def attribute(self, name: str) -> int:
        return self._attributes.get(name, 1)

    def set_attribute(self, name: str, value: int) -> None:
        if name in self._attributes:
            self._attributes[name] = clamp(value, 1, 6)

    def skill(self, name: str) -> int:
        """Effective skill value: attribute floor + investment + thoughts."""
        return (
            self.base_skill(name)
            + self._skill_points.get(name, 0)
            + self._skill_bonuses.get(name, 0)
        )

    def base_skill(self, name: str) -> int:
        """The floor this skill inherits from its attribute alone."""
        attribute = SKILL_ATTRIBUTE.get(name)
        if attribute is None:
            return 10
        return self.ATTRIBUTE_BASE + self.ATTRIBUTE_STEP * self.attribute(attribute)

    def invest_skill(self, name: str, amount: int = 1) -> None:
        """Spend creation points on one skill, above its attribute floor."""
        if name in self._skill_points:
            self._skill_points[name] += amount

    def adjust_skill(self, name: str, amount: int) -> None:
        if name in self._skill_bonuses:
            self._skill_bonuses[name] += amount

    def top_skill(self) -> str:
        return max(SKILLS, key=self.skill)

    def top_skills(self, count: int = 3) -> list[str]:
        return sorted(SKILLS, key=self.skill, reverse=True)[:count]

    # --- status ------------------------------------------------------------

    def adjust_morale(self, amount: int) -> int:
        before = self.morale
        self.morale = clamp(self.morale + amount, 0, 100)
        return self.morale - before

    def adjust_health(self, amount: int) -> int:
        before = self.health
        self.health = clamp(self.health + amount, 0, 100)
        return self.health - before

    def adjust_intoxication(self, amount: int) -> int:
        before = self.intoxication
        self.intoxication = clamp(self.intoxication + amount, 0, 10)
        return self.intoxication - before

    @property
    def lucidity(self) -> int:
        return int(self._lucidity_exact)

    @lucidity.setter
    def lucidity(self, value: int) -> None:
        """Setting lucidity directly rewrites the underlying float too.

        Two fields that can disagree is a bug waiting to happen; the test
        suite found it within a minute of the float being introduced.
        """
        self._lucidity_exact = float(clamp(int(value), 0, 100))

    def adjust_lucidity(self, amount: int) -> int:
        """Lucidity is the spine of the whole story.

        It rises whenever Oliver registers the manuscript bleeding through -
        typewriter sounds, the office in the mirror, his own name on a vault
        plate. It never falls on its own; only the C.C.C.C., the Insta-gators,
        and Bud Onkuhdonk's aggressive denial can push it back down.

        Gains suffer **diminishing returns**. The content grants roughly 1900
        raw lucidity against a scale of 100, so a flat sum saturated the whole
        mechanic inside the first fifth of the game - a playtest hit 100/100
        at cycle 14 with two of six beats done, which retired Furthermore's
        entire clarity arc before it had started. Each gain is now scaled by
        the remaining headroom, so waking up is asymptotic: fast at first,
        and the last stretch has to be earned.

        Losses are applied flat. Denial is not subject to diminishing
        returns; Bud gets his full effect every time.
        """
        before = self.lucidity
        if amount > 0:
            headroom = 100.0 - self._lucidity_exact
            if headroom > 0:
                scale = CONFIG["world"]["lucidity_approach"]
                gain = amount * headroom / max(1, scale)
                # No discovery is ever worth literally nothing.
                self._lucidity_exact = min(100.0, self._lucidity_exact + max(gain, 0.2))
        elif amount < 0:
            self._lucidity_exact = max(0.0, self._lucidity_exact + amount)
        return self.lucidity - before

    def adjust_exhaustion(self, amount: int) -> int:
        before = self.exhaustion
        self.exhaustion = clamp(self.exhaustion + amount, 0, 10)
        return self.exhaustion - before

    @property
    def lucidity_stage(self) -> int:
        """0-4. Drives how honestly the world describes itself."""
        stages = CONFIG["world"]["lucidity_stages"]
        stage = 0
        for index, threshold in enumerate(stages):
            if self.lucidity >= threshold:
                stage = index
        return stage

    def is_alive(self) -> bool:
        return self.health > 0

    # --- inventory ---------------------------------------------------------

    def has_item(self, item_id: str) -> bool:
        return item_id in self.inventory

    def add_item(self, item: Item) -> None:
        self.inventory[item.id] = item

    def remove_item(self, item_id: str) -> Item | None:
        return self.inventory.pop(item_id, None)

    # --- thought cabinet ---------------------------------------------------

    def offer_thought(self, thought_id: str) -> bool:
        """Make a thought available for internalisation. True if it is new."""
        if thought_id in self.thoughts_known or thought_id in self.thoughts_internalised:
            return False
        self.thoughts_known.append(thought_id)
        return True

    @property
    def thought_slots(self) -> int:
        return CONFIG["narrative"]["thought_slots"]

    @property
    def slots_free(self) -> int:
        return max(0, self.thought_slots - len(self.thoughts_internalising))

    def begin_internalising(self, thought_id: str, cycles: int) -> bool:
        """Start turning a thought over. Fails if the cabinet is full.

        The cap is the whole point of a cabinet: without it the player takes
        every thought and the choice evaporates.
        """
        if thought_id not in self.thoughts_known:
            return False
        if thought_id in self.thoughts_internalising:
            return False
        if self.slots_free <= 0:
            return False
        self.thoughts_known.remove(thought_id)
        self.thoughts_internalising[thought_id] = cycles
        return True

    def tick_thoughts(self) -> list[str]:
        """Advance internalisation by one cycle; return newly finished ids."""
        finished: list[str] = []
        for thought_id in list(self.thoughts_internalising):
            self.thoughts_internalising[thought_id] -= 1
            if self.thoughts_internalising[thought_id] <= 0:
                del self.thoughts_internalising[thought_id]
                self.thoughts_internalised.append(thought_id)
                finished.append(thought_id)
        return finished

    def has_thought(self, thought_id: str) -> bool:
        return thought_id in self.thoughts_internalised

    # --- presentation ------------------------------------------------------

    def sheet_lines(self) -> list[tuple[str, str]]:
        """(label, value) pairs for the character sheet."""
        rows: list[tuple[str, str]] = []
        for attribute in ATTRIBUTES:
            # Header row, signalled to the renderer by an empty value.
            rows.append((f"{attribute.title()} {self.attribute(attribute)}", ""))
            for name in ATTRIBUTE_SKILLS[attribute]:
                value = self.skill(name)
                marks = []
                if self._skill_points.get(name):
                    marks.append(f"+{self._skill_points[name]}")
                if self._skill_bonuses.get(name):
                    marks.append(f"+{self._skill_bonuses[name]} thought")
                suffix = f" ({', '.join(marks)})" if marks else ""
                star = " *" if name == self.signature_skill else ""
                label = "  " + name.replace("_", "-").title() + star
                rows.append(
                    (
                        label,
                        f"{value:>2}{suffix}  [{modifier_for(value):+d}]  "
                        f"{SKILL_DESCRIPTIONS[name].split('.')[0]}.",
                    )
                )
        return rows

    def status_lines(self) -> list[str]:
        def bar(value: int, maximum: int = 100, size: int = 12) -> str:
            filled = int(round(size * value / maximum)) if maximum else 0
            return "█" * filled + "·" * (size - filled)

        return [
            f"Morale        {bar(self.morale)} {self.morale:>3}/100",
            f"Health        {bar(self.health)} {self.health:>3}/100",
            f"Intoxication  {bar(self.intoxication, 10)} {self.intoxication:>3}/10",
            f"Exhaustion    {bar(self.exhaustion, 10)} {self.exhaustion:>3}/10",
            f"Lucidity      {bar(self.lucidity)} {self.lucidity:>3}/100",
        ]

    # --- persistence -------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "attributes": self._attributes,
            "skill_points": self._skill_points,
            "skill_bonuses": self._skill_bonuses,
            "signature_skill": self.signature_skill,
            "name_known": self.name_known,
            "morale": self.morale,
            "health": self.health,
            "intoxication": self.intoxication,
            "lucidity": self.lucidity,
            "lucidity_exact": self._lucidity_exact,
            "exhaustion": self.exhaustion,
            "inventory": [
                {"id": i.id, "name": i.name, "description": i.description}
                for i in self.inventory.values()
            ],
            "thoughts_known": self.thoughts_known,
            "thoughts_internalising": self.thoughts_internalising,
            "thoughts_internalised": self.thoughts_internalised,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        player = cls()
        player._attributes.update(data.get("attributes", {}))
        player._skill_points.update(data.get("skill_points", {}))
        player._skill_bonuses.update(data.get("skill_bonuses", {}))
        player.signature_skill = data.get("signature_skill")
        player.name_known = data.get("name_known", False)
        player.morale = data.get("morale", player.morale)
        player.health = data.get("health", player.health)
        player.intoxication = data.get("intoxication", player.intoxication)
        player._lucidity_exact = float(
            data.get("lucidity_exact", data.get("lucidity", 0))
        )
        player.exhaustion = data.get("exhaustion", player.exhaustion)
        player.inventory = {
            entry["id"]: Item(entry["id"], entry["name"], entry["description"])
            for entry in data.get("inventory", [])
        }
        player.thoughts_known = data.get("thoughts_known", [])
        player.thoughts_internalising = {
            k: int(v) for k, v in data.get("thoughts_internalising", {}).items()
        }
        player.thoughts_internalised = data.get("thoughts_internalised", [])
        return player
