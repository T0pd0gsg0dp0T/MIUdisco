"""The hub: everything mutable, plus the condition and effect vocabulary.

GameState owns the player, the investigation, the NPC registry, the check
ledger, the clock and the density dial - which makes it the only sensible
home for `meets()` and `apply_effects()`, the two functions every content
file speaks through. Locations and dialogue nodes share one schema for both,
so an author who has learned to write a dialogue condition already knows how
to write an object condition.
"""

from __future__ import annotations

import json
import os
import random
import time as _time

import ui
from config import CONFIG
from furthermore import Furthermore
from investigation import BEATS, BEATS_BY_ID, Clue, Investigation
from narrative_density import NarrativeDensity
from npcs import NPCRegistry
from player import Item, Player
from skill_checks import CheckKind, CheckLedger, roll_check

CONTENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content")

SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saves")

# Silvora Reefs has no dawn. These are the closest thing it has to hours,
# and residents use them without ever agreeing on when one becomes the next.
# Varied wrappers for a thought becoming available. Three of these can fire
# in one room, and one fixed sentence three times reads as a template.
THOUGHT_ARRIVALS = [
    "A thought arrives, unhurried, and lies down across your mind like "
    "something that intends to stay: \"{name}\".",
    "Something settles at the back of it all and declines to be dislodged. "
    "It has a shape, and the shape has a name, and the name is \"{name}\".",
    "The elephant puts one enormous foot down beside a thought you were not "
    "going to pick up. \"{name}\". He waits.",
    "\"{name}\", he does not say, in the way he does not say things, and the "
    "not-saying is now taking up room.",
]

PHASES = [
    "Early Dark",
    "Deep Dark",
    "The Small Hours",
    "False Dawn",
    "The Long Violet",
]


class Clock:
    """Cycle-based time. One cycle is roughly one meaningful action."""

    def __init__(self) -> None:
        self.cycle = 0

    @property
    def phase(self) -> str:
        per = CONFIG["world"]["cycles_per_phase"]
        return PHASES[(self.cycle // max(1, per)) % len(PHASES)]

    @property
    def day(self) -> int:
        per = CONFIG["world"]["cycles_per_phase"]
        return 1 + self.cycle // max(1, per * len(PHASES))

    def spend(self, cycles: int = 1) -> int:
        self.cycle += cycles
        return self.cycle

    def describe(self) -> str:
        return f"{self.phase}, cycle {self.cycle}"

    def to_dict(self) -> dict:
        return {"cycle": self.cycle}

    @classmethod
    def from_dict(cls, data: dict) -> "Clock":
        clock = cls()
        clock.cycle = data.get("cycle", 0)
        return clock


class GameState:
    def __init__(self) -> None:
        self.player = Player()
        self.investigation = Investigation()
        self.npcs = NPCRegistry()
        self.checks = CheckLedger()
        self.density = NarrativeDensity()
        self.elephant = Furthermore()
        self.time = Clock()
        self.location_id = "crash_site"
        self.running = True
        self.rng = random.Random()
        self._passives_this_scene = 0
        self._last_autosave = 0
        # Ambient skill-voice lines already heard, so each fires once per
        # playthrough; and the lazily loaded pool they come from.
        self._skill_voices_heard: set[str] = set()
        # line id -> the skill value it was last failed at, so a failure only
        # reopens once that skill has genuinely grown.
        self._skill_voices_failed: dict[str, int] = {}
        self._skill_voice_cache = None
        # Set by main when a beat fires, so the loop can narrate it after the
        # current action finishes rather than interrupting mid-sentence.
        self.pending_beats: list[str] = []
        # Endgame plumbing: content requests travel and endings, the loop acts.
        self.pending_travel: str | None = None
        self.ending: str | None = None
        # Set by the UI layer: called whenever visible state changes, so the
        # status panel tracks a conversation instead of only updating between
        # commands.
        self.on_change = None

    # --- scene bookkeeping -------------------------------------------------

    def begin_scene(self) -> None:
        self._passives_this_scene = 0
        self.elephant.begin_scene()

    # --- conditions --------------------------------------------------------

    def meets(self, requires: dict) -> bool:
        """Evaluate a condition block. An empty block is always true.

        Supported keys (all optional, all ANDed together):
          clue / not_clue          str or list of clue ids
          flag / not_flag          str, list, or {name: value}
          beat / not_beat          str or list of beat ids
          item / not_item          str or list of item ids
          thought                  str or list of internalised thought ids
          lucidity_min / _max      int
          intoxication_min / _max  int
          morale_min / _max        int
          health_min / _max        int
          skill_min                {"LOGIC": 12}
          relationship_min / _max  {"npc_id": 2}
          spoken_to                str or list of npc ids
          check_passed / _failed   check id
          visited_min              {"location_id": 2}
          cycle_min / cycle_max    int
          tag_count_min            {"kindness": 5} - hold >=5 clues so tagged

        `tag_count_min` is what gates the endgame's harder answers. Rather
        than naming specific clues - which would make one route mandatory and
        break the whole design - it asks how much of a *kind* of evidence the
        player has gathered. A player who has understood that the author has
        been protective can prove it from any five of eighteen clues.
        """
        if not requires:
            return True

        def as_list(value) -> list:
            if value is None:
                return []
            return value if isinstance(value, list) else [value]

        inv = self.investigation
        player = self.player

        for clue_id in as_list(requires.get("clue")):
            if not inv.has_clue(clue_id):
                return False
        for clue_id in as_list(requires.get("not_clue")):
            if inv.has_clue(clue_id):
                return False

        flag_req = requires.get("flag")
        if isinstance(flag_req, dict):
            for name, expected in flag_req.items():
                if inv.flag(name) != expected:
                    return False
        else:
            for name in as_list(flag_req):
                if not inv.flag(name):
                    return False
        for name in as_list(requires.get("not_flag")):
            if inv.flag(name):
                return False

        for beat_id in as_list(requires.get("beat")):
            if beat_id not in inv.beats_reached:
                return False
        for beat_id in as_list(requires.get("not_beat")):
            if beat_id in inv.beats_reached:
                return False

        for item_id in as_list(requires.get("item")):
            if not player.has_item(item_id):
                return False
        for item_id in as_list(requires.get("not_item")):
            if player.has_item(item_id):
                return False

        for thought_id in as_list(requires.get("thought")):
            if not player.has_thought(thought_id):
                return False

        ranges = [
            ("lucidity_min", "lucidity_max", player.lucidity),
            ("intoxication_min", "intoxication_max", player.intoxication),
            ("morale_min", "morale_max", player.morale),
            ("health_min", "health_max", player.health),
            ("cycle_min", "cycle_max", self.time.cycle),
        ]
        for low_key, high_key, value in ranges:
            if low_key in requires and value < requires[low_key]:
                return False
            if high_key in requires and value > requires[high_key]:
                return False

        for skill, minimum in (requires.get("skill_min") or {}).items():
            if player.skill(skill) < minimum:
                return False

        for npc_id, minimum in (requires.get("relationship_min") or {}).items():
            if self.npcs.standing(npc_id) < minimum:
                return False
        for npc_id, maximum in (requires.get("relationship_max") or {}).items():
            if self.npcs.standing(npc_id) > maximum:
                return False

        for npc_id in as_list(requires.get("spoken_to")):
            if not self.npcs.has_spoken_to(npc_id):
                return False

        for check_id in as_list(requires.get("check_passed")):
            if not self.checks.succeeded(check_id):
                return False
        for check_id in as_list(requires.get("check_failed")):
            if not (self.checks.attempted(check_id) and not self.checks.succeeded(check_id)):
                return False

        for loc_id, minimum in (requires.get("visited_min") or {}).items():
            if inv.times_visited(loc_id) < minimum:
                return False

        for tag, minimum in (requires.get("tag_count_min") or {}).items():
            if len(inv.clues_with_tag(tag)) < minimum:
                return False

        return True

    def state_token(self) -> str:
        """Fingerprint of everything that justifies retrying a white check.

        This wraps the investigation's own token with a count of dialogue
        nodes heard. Hearing something new *is* learning something, and
        without it a conversation in a room with no exits - the confrontation
        - could never move the token, so one bad roll permanently retired the
        branch behind it. The count only grows on genuinely new nodes, so it
        self-limits: exhaust an NPC and you must go and do something else.
        """
        heard = sum(len(v) for v in self.npcs.history.values())
        return f"{self.investigation.state_token()}:{heard}"

    def tag_count(self, tag: str) -> int:
        """How many clues carrying `tag` the player holds. Used by the endgame."""
        return len(self.investigation.clues_with_tag(tag))

    # --- effects -----------------------------------------------------------

    def apply_effects(self, effects: dict, source: str = "") -> None:
        """Apply a content-authored effect block and narrate the visible parts."""
        if not effects:
            return

        inv = self.investigation
        player = self.player

        # Clues first, so beat checks below see them.
        clue_specs = effects.get("clue")
        if clue_specs:
            if isinstance(clue_specs, dict):
                clue_specs = [clue_specs]
            for spec in clue_specs:
                clue = Clue(
                    id=spec["id"],
                    title=spec["title"],
                    text=spec.get("text", ""),
                    beat=spec.get("beat"),
                    tags=spec.get("tags", []),
                    source=spec.get("source", source),
                    herring=spec.get("herring", False),
                )
                if inv.add_clue(clue):
                    ui.discovery(clue.title, clue.text)

        for name, value in (effects.get("flag") or {}).items():
            inv.set_flag(name, value)

        # Status. Each change is reported, because an unreported status change
        # is indistinguishable from a bug.
        status_map = [
            ("morale", player.adjust_morale, "Morale"),
            ("health", player.adjust_health, "Health"),
            ("intoxication", player.adjust_intoxication, "Intoxication"),
            ("exhaustion", player.adjust_exhaustion, "Exhaustion"),
        ]
        for key, setter, label in status_map:
            if key in effects:
                delta = setter(effects[key])
                if delta:
                    ui.aside(f"{label} {delta:+d}.")

        if "lucidity" in effects:
            delta = player.adjust_lucidity(effects["lucidity"])
            if delta:
                self._narrate_lucidity(delta)

        for skill, amount in (effects.get("skill") or {}).items():
            player.adjust_skill(skill, amount)
            ui.aside(f"{skill.replace('_', '-').title()} {amount:+d}, permanently.")

        item_spec = effects.get("item")
        if item_spec:
            if isinstance(item_spec, dict):
                item_spec = [item_spec]
            for spec in item_spec:
                player.add_item(
                    Item(spec["id"], spec["name"], spec.get("description", ""))
                )
                ui.aside(f"Acquired: {spec['name']}.")

        for item_id in (
            effects.get("remove_item")
            if isinstance(effects.get("remove_item"), list)
            else [effects["remove_item"]] if effects.get("remove_item") else []
        ):
            removed = player.remove_item(item_id)
            if removed:
                ui.aside(f"Lost: {removed.name}.")

        for npc_id, amount in (effects.get("relationship") or {}).items():
            self.npcs.adjust(npc_id, amount)

        thought_ids = effects.get("thought")
        if thought_ids:
            if isinstance(thought_ids, str):
                thought_ids = [thought_ids]
            for thought_id in thought_ids:
                thought = self.elephant.offer(player, thought_id)
                if thought:
                    # Picking up "And Furthermore—" is how the player learns
                    # what the elephant is called; until then every purple
                    # intrusion is headed "the elephant", because that is
                    # genuinely all the amnesiac knows about him.
                    if thought_id == "and_furthermore":
                        ui.name_the_elephant("Furthermore")
                        inv.set_flag("knows_elephant_name", True)
                    line = self.rng.choice(THOUGHT_ARRIVALS).format(
                        name=thought["name"]
                    )
                    # Teach the mechanic once. A playtest ran 295 cycles and
                    # internalised nothing at all, because the varied arrival
                    # lines had quietly dropped the word "cabinet".
                    if not inv.flag("taught_cabinet"):
                        inv.set_flag("taught_cabinet", True)
                        line += (
                            "\n\nThoughts can be dwelt on — `cabinet` — and "
                            "dwelling on one changes you, permanently, which "
                            "is the only kind of change this town offers."
                        )
                    elif player.thoughts_known and player.slots_free:
                        waiting = len(player.thoughts_known)
                        free = player.slots_free
                        line += (
                            f"\n\n({waiting} waiting in the cabinet, "
                            f"{free} slot{'' if free == 1 else 's'} free.)"
                        )
                    ui.furthermore(line)

        if effects.get("learn_name") and player.learn_name():
            ui.discovery(
                f"Your name is {player.name}",
                "It is on the rent book, the door plate, and the spine of "
                "every ruined notebook in the drawer, in the handwriting "
                "that matches the callus on your finger. It does not arrive "
                "as a memory. It arrives as a fact about somebody else that "
                "you happen to be holding.",
            )

        if effects.get("cycles"):
            self.advance_time(int(effects["cycles"]))

        # Forced travel. Content cannot move the player directly because the
        # location loop lives in main; it raises a request the loop honours
        # after the current action finishes narrating.
        if effects.get("goto_location"):
            self.pending_travel = effects["goto_location"]

        # An ending closes the game. Same deferral: the current scene gets to
        # finish its sentence before the epilogue starts.
        if effects.get("ending"):
            self.ending = effects["ending"]

        # Beat accounting happens after every effect block.
        for beat_id in inv.check_beats():
            self.pending_beats.append(beat_id)

        if self.on_change:
            self.on_change()

    # The lucidity aside fires on almost every discovery, so it needs both
    # variety and a sense of progression. At stage 0 the sound is unplaceable;
    # by stage 4 Oliver knows exactly what it is, and "you almost place it"
    # would be a line from four hours ago.
    LUCIDITY_RISING = {
        0: [
            "Something in the arrangement of the world loosens by one notch.",
            "A detail refuses to file itself with the others.",
            "Somewhere at the edge of hearing, a small mechanical noise, and gone.",
        ],
        1: [
            "The seam is a little more visible than it was.",
            "Somewhere, a key strikes a platen. You almost place the sound.",
            "The town holds its shape, and holding it is visibly work.",
        ],
        2: [
            "Keys. Four of them, struck close together, and then a pause with a "
            "decision in it.",
            "The seam is not a seam in anything. It is where two accounts meet.",
            "A carriage goes back somewhere, at the end of a line.",
        ],
        3: [
            "The typing is not distant and has never been distant. It is the "
            "room, being put.",
            "A pause of exactly the length a person needs to reconsider a word.",
            "Somebody, somewhere, has gone back over the last sentence.",
        ],
        4: [
            "He is typing. You know the rhythm now the way you know your own "
            "handwriting, and for the same reason.",
            "A word is struck out. You are standing in the paragraph while it "
            "happens and it does not hurt.",
            "The machine stops. It stops whenever you look directly at what it "
            "is doing, and it starts again the moment you look away.",
        ],
    }

    LUCIDITY_FALLING = [
        "The world tightens its collar and stands up straight.",
        "The seam closes. Of course there was no seam.",
        "Whatever you were about to notice has been filed elsewhere.",
        "The thought is taken off you, courteously, and not given back.",
        "Somebody says it is a light well, out loud, somewhere, and it is.",
    ]

    def _narrate_lucidity(self, delta: int) -> None:
        """Report lucidity in prose rather than as a number going up.

        Lucidity is the story, so it gets a sentence, not a stat line - and
        the sentence tracks how far along the story is. A playtest at 91
        lucidity was still being told it *almost* placed the sound.
        """
        if delta > 0:
            pool = self.LUCIDITY_RISING.get(
                self.player.lucidity_stage, self.LUCIDITY_RISING[4]
            )
            ui.aside(self.rng.choice(pool))
        else:
            ui.aside(self.rng.choice(self.LUCIDITY_FALLING))

    # --- checks ------------------------------------------------------------

    # How much each previous failure is worth on a retry, and the ceiling.
    PERSISTENCE_STEP = 1
    PERSISTENCE_CAP = 3

    def persistence_bonus(self, check_id: str | None) -> int:
        """A bonus for having tried this before and failed.

        Playtesting turned up the real problem with the check economy: the
        median check is a coin flip at starting stats, and over half of them
        carry no clue bonus at all, so losing the flip retired the content
        behind them with no way to earn it back. Retrying a white check
        already costs a genuine advance in the investigation - that is what
        the state token enforces - and this makes that loop pay.

        It is also the most in-character modifier in the game. Oliver's
        defining trait is that he cannot stop going over a thing.
        """
        if not check_id:
            return 0
        record = self.checks.records.get(check_id)
        if not record or record.get("success"):
            return 0
        failures = record.get("attempts", 0)
        return min(failures * self.PERSISTENCE_STEP, self.PERSISTENCE_CAP)

    def check_bonus(self, check: dict, check_id: str | None = None) -> int:
        """Situational bonus granted by clues, flags, thoughts and persistence.

        Content can say `"bonus_if_clue": {"typewriter_sound": 2}` and the
        engine finds it. This is how earlier investigation makes later checks
        easier without the author wiring a separate branch.
        """
        bonus = self.persistence_bonus(check_id or check.get("id"))
        for clue_id, amount in (check.get("bonus_if_clue") or {}).items():
            if self.investigation.has_clue(clue_id):
                bonus += amount
        for flag_name, amount in (check.get("bonus_if_flag") or {}).items():
            if self.investigation.flag(flag_name):
                bonus += amount
        for thought_id, amount in (check.get("bonus_if_thought") or {}).items():
            if self.player.has_thought(thought_id):
                bonus += amount
        return bonus

    def ambient_skill_voices(self, location_id: str, limit: int = 2) -> int:
        """Let the build's loud skills comment on the room.

        The authored per-object passives are what a *place* has to say. This
        is what a *person* has to say about it, and it is the whole reason
        the roster is twenty-four skills rather than six: the lines are
        offered in descending order of skill value, so an Intellect build
        and a Fortitude build are told different things about the identical
        room, and neither of them is told everything.

        A line is rolled *once* at a given skill value, and a failure sticks
        until that skill actually grows. Re-rolling on every revisit was the
        first version and it quietly destroyed the whole feature: with three
        or four visits per location, every build eventually passed nearly
        every line, so all four archetypes ended up hearing the same
        eighteen skills and the build stopped meaning anything. Failing to
        notice something has to be permanent for noticing it to be worth a
        character choice.
        """
        if not CONFIG["features"]["passive_checks"]:
            return 0
        pool = self._skill_voice_pool()
        if not pool:
            return 0

        candidates = []
        for skill, entries in pool.items():
            value = self.player.skill(skill)
            for entry in entries:
                entry_id = entry.get("id")
                if entry_id in self._skill_voices_heard:
                    continue
                # Already failed at this skill level: nothing has changed
                # about the ear doing the listening, so nothing new is heard.
                if self._skill_voices_failed.get(entry_id, -1) >= value:
                    continue
                where = entry.get("where", ["*"])
                if "*" not in where and location_id not in where:
                    continue
                candidates.append((self.player.skill(skill), skill, entry))

        # Loudest skill first. Ties broken by the order the file lists them,
        # which `sorted` preserves.
        candidates.sort(key=lambda item: item[0], reverse=True)

        spoken = 0
        # One line per skill per room. Without this a dominant attribute
        # monologues - a Fortitude build's first room opened with two
        # consecutive Pain-Threshold paragraphs, which reads as one voice
        # talking to itself rather than as a mind with several of them.
        used_skills: set[str] = set()
        for _value, skill, entry in candidates:
            if spoken >= limit:
                break
            if skill in used_skills:
                continue
            if self._passives_this_scene >= self.density.passive_budget:
                break
            result = roll_check(
                self.player,
                skill,
                entry.get("dc", 12),
                context=f"voice:{entry.get('id')}",
                kind=CheckKind.WHITE,
            )
            if not result.success:
                self._skill_voices_failed[entry["id"]] = self.player.skill(skill)
                continue
            self._skill_voices_heard.add(entry["id"])
            self._passives_this_scene += 1
            used_skills.add(skill)
            spoken += 1
            ui.skill_voice(skill, entry["text"], True)
        return spoken

    def _skill_voice_pool(self) -> dict:
        if self._skill_voice_cache is None:
            path = os.path.join(CONTENT_DIR, "skill_voices.json")
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
            except (OSError, ValueError):
                data = {}
            self._skill_voice_cache = {
                key: value
                for key, value in data.items()
                if not key.startswith("_") and isinstance(value, list)
            }
        return self._skill_voice_cache

    def run_passive(self, passive: dict, context: str = "") -> bool:
        """Roll a passive check and let the skill speak if it makes it.

        Passive checks are the texture of the whole game. They are budgeted
        per scene by narrative density so a room never turns into six voices
        shouting at once.
        """
        if not CONFIG["features"]["passive_checks"]:
            return False
        if self._passives_this_scene >= self.density.passive_budget:
            return False
        if not self.meets(passive.get("requires", {})):
            return False

        result = roll_check(
            self.player,
            passive["skill"],
            passive["dc"],
            context=context,
            kind=CheckKind.WHITE,
            bonus=self.check_bonus(passive),
        )

        if result.success:
            self._passives_this_scene += 1
            ui.skill_voice(passive["skill"], self.density.pick(passive["text"]), True)
            if passive.get("effects"):
                self.apply_effects(passive["effects"], source=passive["skill"])
            return True

        # A failed passive may still speak, if the author wrote the wrong
        # answer for it. A skill that is confidently mistaken is the best
        # thing this system does.
        fail_text = passive.get("failure_text")
        if fail_text and not CONFIG["narrative"]["silent_passive_failure"]:
            self._passives_this_scene += 1
            ui.skill_voice(passive["skill"], self.density.pick(fail_text), False)
            return True
        return False

    # --- time --------------------------------------------------------------

    def advance_time(self, cycles: int = 1) -> None:
        for _ in range(max(0, cycles)):
            self.time.spend(1)
            # Bodies wear down and sober up on the same clock.
            # Slower than it was: exhaustion is now a thing you manage by
            # sleeping rather than an unavoidable slide to the cap.
            if self.time.cycle % 5 == 0:
                self.player.adjust_exhaustion(1)
            if self.time.cycle % 2 == 0 and self.player.intoxication > 0:
                self.player.adjust_intoxication(-1)
            for thought_id in self.player.tick_thoughts():
                thought = self.elephant.apply_completed(self.player, thought_id)
                if thought:
                    ui.furthermore(
                        f"\"{thought['name']}\" has finished settling. "
                        f"{thought.get('conclusion', '')}"
                    )
                    if thought.get("effect_text"):
                        ui.aside(thought["effect_text"])

        if CONFIG["features"]["autosave"]:
            interval = CONFIG["world"]["autosave_every_cycles"]
            if interval and self.time.cycle - self._last_autosave >= interval:
                self._last_autosave = self.time.cycle
                self.save("autosave", quiet=True)

        if CONFIG["narrative"]["auto_scale"]:
            self.density.scale_to_progress(
                self.investigation.furthest_beat_index, len(BEATS)
            )

    # --- beats -------------------------------------------------------------

    def flush_beats(self) -> None:
        """Narrate any beats that fired during the last action."""
        while self.pending_beats:
            beat_id = self.pending_beats.pop(0)
            beat = BEATS_BY_ID[beat_id]
            ui.heading(f"⟡  {beat['name']}")
            ui.narrate(beat["summary"])
            self.density.scale_to_progress(
                self.investigation.furthest_beat_index, len(BEATS)
            )

    # --- persistence -------------------------------------------------------

    def save(self, slot: str = "save", quiet: bool = False) -> str:
        os.makedirs(SAVE_DIR, exist_ok=True)
        path = os.path.join(SAVE_DIR, f"{slot}.json")
        payload = {
            "version": 1,
            "saved_at": _time.strftime("%Y-%m-%d %H:%M:%S"),
            "location_id": self.location_id,
            "player": self.player.to_dict(),
            "investigation": self.investigation.to_dict(),
            "npcs": self.npcs.to_dict(),
            "checks": self.checks.to_dict(),
            "density": self.density.to_dict(),
            # Without these a reload replays lines the player has already
            # been told, and re-opens ones their build already failed.
            "skill_voices_heard": sorted(self._skill_voices_heard),
            "skill_voices_failed": self._skill_voices_failed,
            "time": self.time.to_dict(),
        }
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=1)
        os.replace(tmp, path)  # atomic: a crash mid-save cannot corrupt a slot
        if not quiet:
            ui.aside(f"Saved to '{slot}'.")
        return path

    @classmethod
    def load(cls, slot: str = "save") -> "GameState | None":
        path = os.path.join(SAVE_DIR, f"{slot}.json")
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, ValueError):
            return None

        state = cls()
        state.player = Player.from_dict(data.get("player", {}))
        state.investigation = Investigation.from_dict(data.get("investigation", {}))
        state.npcs.load_dict(data.get("npcs", {}))
        state.checks = CheckLedger.from_dict(data.get("checks", {}))
        state.density = NarrativeDensity.from_dict(data.get("density", {}))
        if state.investigation.flag("knows_elephant_name"):
            ui.name_the_elephant("Furthermore")
        else:
            ui.name_the_elephant("the elephant")
        state._skill_voices_heard = set(data.get("skill_voices_heard", []))
        state._skill_voices_failed = {
            str(k): int(v) for k, v in (data.get("skill_voices_failed") or {}).items()
        }
        state.time = Clock.from_dict(data.get("time", {}))
        state.location_id = data.get("location_id", "crash_site")
        state._last_autosave = state.time.cycle
        return state

    @staticmethod
    def list_saves() -> list[tuple[str, str]]:
        if not os.path.isdir(SAVE_DIR):
            return []
        rows: list[tuple[str, str]] = []
        for filename in sorted(os.listdir(SAVE_DIR)):
            if not filename.endswith(".json"):
                continue
            slot = filename[:-5]
            try:
                with open(
                    os.path.join(SAVE_DIR, filename), "r", encoding="utf-8"
                ) as handle:
                    data = json.load(handle)
                rows.append((slot, data.get("saved_at", "unknown")))
            except (OSError, ValueError):
                continue
        return rows
