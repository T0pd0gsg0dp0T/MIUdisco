"""Furthermore, the Irrelevant Elephant - companion, thought cabinet, and hint system.

The lorebook is precise about him and the implementation follows it exactly:

  * He is Oliver's subconscious attempting to reach the conscious mind.
    Mechanically, that means his clarity is a *function of lucidity*, not a
    fixed voice. Early on he cannot finish a sentence. Late on he is the
    only thing in the book that says what it means.
  * He is older than language and regards it as a fad. So at low lucidity he
    communicates in weight, temperature, and gesture rather than words.
  * His one-word catchphrase is "Nevermind", deployed after suspenseful
    build-ups to anticlimactic effect. This is the joke that has to land, so
    it is a first-class mechanic: `build_up()` sets a charge, and the charge
    is discharged as an anticlimax unless lucidity is high enough for him to
    actually deliver.
  * He is a trusted companion and guide. He hints; he never solves.

He is also the delivery vehicle for the thought cabinet, because a thought
arriving from a purple elephant standing in a doorway is a better piece of
theatre than a menu entry.
"""

from __future__ import annotations

import json
import os
import random

from config import CONFIG
from investigation import BEATS

CONTENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content")

# How clearly he comes through, by lucidity stage 0-4.
CLARITY_LABEL = {
    0: "a pressure behind the sternum",
    1: "a shape that is almost a sentence",
    2: "words, arriving slightly out of order",
    3: "words, in order",
    4: "a voice, plainly, at last",
}

# Non-verbal communication for stages 0-1, where language has not yet won.
WORDLESS = [
    "The elephant shifts his weight. The floor does not register it. Somewhere "
    "behind your eyes, a door you did not know about is being leaned against.",
    "He looks at the thing. Then at you. Then at the thing. The ornate saddle "
    "on his back has never been used and today it looks specifically unused.",
    "A warmth, low and purple, settles across the back of your neck. It has the "
    "grammar of a warning and none of the vocabulary.",
    "Furthermore breathes out. The sound is much too large for the room, and "
    "the room accommodates it without comment.",
    "He puts one foot down with enormous care, as though the floor were a "
    "sentence he did not wish to interrupt.",
]

# The anticlimax. He builds, and builds, and then does not deliver.
NEVERMIND_BUILDS = [
    "Furthermore draws himself up. The air thickens. Something vast is being "
    "assembled behind his soft eyes, something that has been waiting since "
    "before there were words to wait in, something that will, at last, explain",
    "He turns to face you fully, which he almost never does. His trunk lifts. "
    "The green flame in the nearest lamppost leans away. He is about to say the "
    "thing, the actual thing, the one you have been",
    "The elephant goes very still. Stiller than the room. Stiller than the "
    "town. Every whisper in Silvora Reefs pauses to hear what he is going to",
]


class Furthermore:
    """The companion's state and voice."""

    def __init__(self) -> None:
        self.thoughts: dict[str, dict] = self._load_thoughts()
        # Scene-scoped budget, reset by the location loop.
        self._spoken_this_scene = 0
        self._nevermind_count = 0
        self._rng = random.Random()

    # --- content -----------------------------------------------------------

    @staticmethod
    def _load_thoughts() -> dict[str, dict]:
        path = os.path.join(CONTENT_DIR, "thoughts", "thoughts.json")
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return {t["id"]: t for t in json.load(handle)}
        except (OSError, ValueError):
            return {}

    # --- scene budget ------------------------------------------------------

    def begin_scene(self) -> None:
        self._spoken_this_scene = 0

    def may_speak(self, density) -> bool:
        if not CONFIG["features"]["furthermore"]:
            return False
        return self._spoken_this_scene < density.thought_budget

    def _spend(self) -> None:
        self._spoken_this_scene += 1

    # --- voice -------------------------------------------------------------

    def clarity(self, player) -> int:
        return player.lucidity_stage

    def say(self, player, text: str, density) -> str | None:
        """Render a line in whatever fidelity Furthermore currently has.

        Returns the text to print, or None if he cannot get through at all
        this scene. At stage 0-1 the *content* of the line is withheld and
        replaced with a wordless approach; the player learns that the
        elephant knew something without learning what.
        """
        if not self.may_speak(density):
            return None
        self._spend()

        stage = self.clarity(player)
        if stage == 0:
            return self._rng.choice(WORDLESS)
        if stage == 1:
            # He gets a fragment out. The first clause, and then nothing.
            fragment = text.split(",")[0].split(".")[0]
            return f"{fragment}— " + self._rng.choice(
                ["and then the rest of it goes somewhere you cannot follow.",
                 "The remainder arrives as weather rather than words.",
                 "He stops. Not from reluctance. From translation difficulty."]
            )
        if stage == 2:
            words = text.split()
            if len(words) > 8:
                # Out of order, but recoverable.
                head, tail = words[: len(words) // 2], words[len(words) // 2 :]
                return " ".join(tail + head)
            return text
        return text

    def nevermind(self, player, density) -> str | None:
        """The catchphrase, with its full build-up.

        At high lucidity he stops doing this, because at high lucidity he is
        finally able to finish the sentence - which is the whole arc of the
        character rendered as a running gag that eventually stops running.
        """
        if not self.may_speak(density):
            return None
        self._spend()
        self._nevermind_count += 1

        build = self._rng.choice(NEVERMIND_BUILDS)
        if player.lucidity_stage >= 4:
            return None  # handled by the caller; he has better things to say now
        return f"{build}—\n\nNevermind."

    # --- hints -------------------------------------------------------------

    def hint(self, player, investigation, density) -> str | None:
        """Offer a nudge toward the nearest unmet beat threshold.

        This is deliberately soft. It names the *kind* of thing still
        missing, never the object to click. Furthermore is a guide, and a
        guide who gives coordinates is a walkthrough.
        """
        if not self.may_speak(density):
            return None

        target = None
        for beat in BEATS:
            if beat["id"] in investigation.beats_reached:
                continue
            found, needed = investigation.beat_progress(beat["id"])
            if found > 0:
                target = (beat, found, needed)
                break
            if target is None:
                target = (beat, found, needed)

        if target is None:
            self._spend()
            return self.say(
                player,
                "There is nothing left to find. That is not the same as there "
                "being nothing left to do.",
                density,
            )

        beat, found, needed = target
        remaining = needed - found
        line = (
            f"{beat['summary']} You have {found} of the {needed} pieces that "
            f"would let you believe it. {remaining} more and it stops being a "
            f"suspicion."
        )
        self._spend()
        return self.say(player, line, density)

    # --- thought cabinet ---------------------------------------------------

    def offer(self, player, thought_id: str) -> dict | None:
        """Make a thought available. Returns the thought record if it is new."""
        thought = self.thoughts.get(thought_id)
        if thought is None:
            return None
        if player.offer_thought(thought_id):
            return thought
        return None

    def internalise(self, player, thought_id: str) -> bool:
        thought = self.thoughts.get(thought_id)
        if thought is None:
            return False
        return player.begin_internalising(thought_id, thought.get("cycles", 4))

    def apply_completed(self, player, thought_id: str) -> dict | None:
        """Apply a finished thought's permanent effects."""
        thought = self.thoughts.get(thought_id)
        if thought is None:
            return None
        effects = thought.get("effects", {})
        for skill, amount in effects.get("skills", {}).items():
            player.adjust_skill(skill, amount)
        if "morale" in effects:
            player.adjust_morale(effects["morale"])
        if "lucidity" in effects:
            player.adjust_lucidity(effects["lucidity"])
        if "health" in effects:
            player.adjust_health(effects["health"])
        return thought

    def describe_cabinet(self, player, include_available: bool = True) -> str:
        """One pre-formatted block, as a string rather than a line list, so
        the UI can print it without a blank line between every entry.

        `include_available` is off in the framed interface, where the same
        thoughts are about to be shown as a selectable list - printing them
        twice was just noise.
        """
        lines: list[str] = []
        if player.thoughts_internalising:
            lines.append(
                f"Turning over  ({len(player.thoughts_internalising)}"
                f"/{player.thought_slots} slots in use):"
            )
            for tid, remaining in player.thoughts_internalising.items():
                thought = self.thoughts.get(tid, {})
                unit = "cycle" if remaining == 1 else "cycles"
                lines.append(
                    f"  · {thought.get('name', tid)} — {remaining} {unit} to settle"
                )
            lines.append("")
        if player.thoughts_known and include_available:
            lines.append("Waiting to be dwelt on:")
            for tid in player.thoughts_known:
                thought = self.thoughts.get(tid, {})
                lines.append(f"  · {thought.get('name', tid)}")
            lines.append("")
        if player.thoughts_internalised:
            lines.append("Settled:")
            for tid in player.thoughts_internalised:
                thought = self.thoughts.get(tid, {})
                lines.append(
                    f"  · {thought.get('name', tid)} — {thought.get('effect_text', '')}"
                )
            lines.append("")
        if not lines:
            lines.append(
                "Nothing yet. The elephant is standing in the corner of your"
            )
            lines.append(
                "skull with an unused saddle and infinite patience."
            )
        return "\n".join(lines).rstrip()
