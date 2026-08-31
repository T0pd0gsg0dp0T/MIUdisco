"""Malice in Underland - entry point and command loop.

The loop is a verb parser rather than a menu, because a menu of "things you
may examine" tells the player what matters before they have looked. Typing
`look at the mirror` and being told the mirror is not important is a real
outcome; a mirror missing from a list is a missing mirror.

Verbs are deliberately few. Everything interesting happens inside them.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys

import character_creation
import ui
import wordplay_engine as wordplay
from config import CONFIG
from dialogue_engine import DialogueEngine
from game_state import GameState
from investigation import BEATS, BEATS_BY_ID
from locations import LocationRegistry
from skill_checks import (
    SKILLS,
    SKILL_DESCRIPTIONS,
    CheckKind,
    modifier_for,
    roll_check,
)

TITLE = r"""
        MALICE IN UNDERLAND
        an investigation in Silvora Reefs
"""

OPENING = (
    "You are lying on your back in shallow water, and the sky above is doing "
    "what it apparently always does: bruising slowly from violet into a "
    "crimson it never quite commits to. Something came down out of that sky. "
    "You were in it. The evidence for this is that you are wet, that the "
    "harbour is full of a smell like hot metal apologising, and that you can "
    "still hear rotor blades somewhere above the fog.\n\n"
    "Your monocle is intact. Your watch says 3:33. Your pockets have been "
    "gone through by the tide and are still full of gold.\n\n"
    "You do not know your name. You do not know this town's name, though the "
    "word *Silvora* is sitting at the front of your head with no paperwork to "
    "support it. Somewhere to your left, an elephant the colour of a bruise "
    "is waiting for you to finish a sentence you do not remember starting."
)

HELP_TEXT = """
  survey                    take the whole location in again
  look at <thing>           examine something (the game's main verb)
  monocle <thing>           look at it through the gold monocle
  talk to <person>          begin a conversation
  who                       who is here, and what is wrong with them
  go to <place>             travel; `go` alone lists the ways out
  log                       the investigation log: clues, by beat
  case                      what you currently believe, and how sure you are
  sheet                     skills, status, inventory
  cabinet                   the thought cabinet
  think                     ask Furthermore for a nudge
  wait                      spend a cycle doing nothing in particular
  rest                      sleep, where there is somewhere to sleep
  save [slot] / load [slot] / saves
  help / quit
"""


class Game:
    def __init__(self, state: GameState | None = None) -> None:
        self.state = state or GameState()
        self.locations = LocationRegistry()
        self.dialogue = DialogueEngine(self.state)
        self.rng = random.Random()

    # --- lifecycle ---------------------------------------------------------

    # --- the command bar ---------------------------------------------------

    def available_actions(self) -> list[dict]:
        """Everything the player can do right now, in bar order.

        The bar only ever shows what is actually available - `rest` appears
        where there is a bed, `monocle` only while Oliver still has the lens,
        `talk` only when somebody is here - so the row doubles as a readout
        of what this place affords.

        Each entry is {verb, command, targets}. A verb with targets opens the
        vertical list; one without runs immediately.
        """
        state = self.state
        location = self.locations.get(state.location_id)
        actions: list[dict] = [
            {"verb": "survey", "command": "survey", "targets": None, "group": "world"}
        ]

        objects = []
        if location:
            objects = [
                (obj.name, obj.id)
                for obj in location.objects
                if not obj.hidden and state.meets(obj.requires)
            ]
        if objects:
            actions.append({"verb": "examine", "command": "look at",
                            "targets": objects, "group": "world"})
            if state.player.has_item("monocle"):
                actions.append({"verb": "monocle", "command": "monocle",
                                "targets": objects, "group": "world"})

        people = [
            (f"{state.npcs.display_name(npc.id)} — {state.npcs.display_title(npc.id)}", npc.id)
            for npc in state.npcs.at_location(state.location_id)
        ]
        if people:
            actions.append({"verb": "talk", "command": "talk to",
                            "targets": people, "group": "world"})

        if location and location.exits:
            exits = [
                (self.locations.display_name(target), target)
                for target in location.exits
            ]
            actions.append({"verb": "go", "command": "go to",
                            "targets": exits, "group": "world"})

        if state.location_id in self.BEDS:
            actions.append({"verb": "rest", "command": "rest",
                            "targets": None, "group": "world"})
        actions += [
            {"verb": "wait", "command": "wait", "targets": None, "group": "world"},
            {"verb": "think", "command": "think", "targets": None, "group": "world"},
        ]

        if (
            state.player.thoughts_known
            or state.player.thoughts_internalising
            or state.player.thoughts_internalised
        ):
            actions.append({"verb": "cabinet", "command": "cabinet",
                            "targets": None, "group": "info"})
        if state.investigation.clues:
            actions.append({"verb": "log", "command": "log",
                            "targets": None, "group": "info"})
        actions += [
            {"verb": "case", "command": "case", "targets": None, "group": "info"},
            {"verb": "sheet", "command": "sheet", "targets": None, "group": "info"},
        ]

        # Saving and loading pick a slot from a list. Nothing here is typed:
        # a brand-new slot is auto-named rather than prompted for.
        slots = [name for name, _ in GameState.list_saves()]
        new_slot = self.next_slot_name(slots)
        actions.append({
            "verb": "save",
            "command": "save",
            "targets": [(f"a new slot — {new_slot}", new_slot)]
            + [(f"overwrite {name}", name) for name in slots],
            "group": "meta",
        })
        if slots:
            actions.append({
                "verb": "load",
                "command": "load",
                "targets": [
                    (f"{name}   ({when})", name) for name, when in GameState.list_saves()
                ],
                "group": "meta",
            })
        actions.append(
            {"verb": "quit", "command": "quit", "targets": None, "group": "meta"}
        )
        return actions

    @staticmethod
    def next_slot_name(existing: list[str]) -> str:
        """Auto-name a fresh save slot, so creating one never needs a keyboard."""
        index = 1
        while f"save-{index}" in existing:
            index += 1
        return f"save-{index}"


    # One line of context per verb, shown on the hint row as you scroll.
    VERB_HINTS = {
        "survey": "take the whole place in again",
        "examine": "look closely at something here",
        "monocle": "see what a thing is actually made of",
        "talk": "somebody here knows something",
        "go": "the ways out of this place",
        "rest": "sleep it off; clears exhaustion",
        "think": "ask for a nudge",
        "cabinet": "dwell on a thought until it changes you",
        "log": "everything you have written down",
        "case": "what you currently believe, and how sure",
        "sheet": "skills, condition, what you are carrying",
        "wait": "spend a cycle doing nothing in particular",
        "save": "write the state to a slot",
        "load": "return to a saved state",
        "quit": "stop investigating",
    }

    _last_status: dict | None = None

    def status_snapshot(self) -> dict:
        player = self.state.player
        return {
            "morale": player.morale,
            "health": player.health,
            "lucidity": player.lucidity,
            "exhaustion": player.exhaustion,
        }

    def mark_status_baseline(self) -> None:
        """Freeze the comparison point, so arrows show what the last command did."""
        self._last_status = self.status_snapshot()

    def header_lines(self) -> tuple[str, list[list[str]]]:
        """Box title, and two rows of segments in priority order.

        `ui.justify` spreads the segments and drops the rightmost ones when
        the terminal is narrow, so the panel degrades a column at a time.
        """
        state = self.state
        player = state.player
        inv = state.investigation

        # Deltas are measured against the snapshot taken before the current
        # command, and are *not* reset here: the header now redraws on every
        # effect, so consuming the marker on read meant the arrow flashed past
        # before anyone could see it. `snapshot_status` moves the baseline.
        now = self.status_snapshot()
        previous = self._last_status or now
        deltas = {k: now[k] - previous.get(k, now[k]) for k in now}

        # The nearest unmet beat: the first with evidence against it, or
        # failing that the first unmet one at all.
        beat_label, beat_ratio = "case closed", 1.0
        unmet = [b for b in BEATS if b["id"] not in inv.beats_reached]
        if unmet:
            with_progress = [b for b in unmet if inv.beat_progress(b["id"])[0]]
            beat = (with_progress or unmet)[0]
            found, needed = inv.beat_progress(beat["id"])
            beat_label = f"{beat['name']} {found}/{needed}"
            beat_ratio = found / needed if needed else 0.0

        context = [
            ui.paint(player.display_name, ui.PALETTE["white"]),
            f"{state.time.phase}, cycle {state.time.cycle}",
            f"day {state.time.day}",
            f"clues {len(inv.clues)}",
            f"beats {len(inv.beats_reached)}/{len(BEATS)}",
        ]

        meters = [
            ui.meter("morale", player.morale, 100) + ui.delta_mark(deltas["morale"]),
            ui.meter("health", player.health, 100) + ui.delta_mark(deltas["health"]),
            ui.meter("lucid", player.lucidity, 100) + ui.delta_mark(deltas["lucidity"]),
            ui.meter("worn", player.exhaustion, 10, size=4, invert=True)
            + ui.delta_mark(-deltas["exhaustion"]),
        ]
        if player.intoxication:
            meters.append(ui.meter("gin", player.intoxication, 10, size=4, invert=True))
        meters.append(
            ui.meter(beat_label, int(beat_ratio * 100), 100, size=6)
        )

        return self.locations.display_name(state.location_id), [context, meters]

    def refresh_header(self) -> None:
        title, lines = self.header_lines()
        ui.draw_header(title, lines)

    def run_bar(self) -> None:
        """Interactive loop: the persistent bottom bar drives everything."""
        focus = 0
        while self.state.running:
            self.refresh_header()
            actions = self.available_actions()
            labels = [a["verb"] for a in actions]
            focus = min(focus, len(labels) - 1)

            # Divide wherever the group changes, so the row reads as
            # "things you do here | things you consult | housekeeping".
            dividers = {
                index
                for index in range(len(actions) - 1)
                if actions[index]["group"] != actions[index + 1]["group"]
            }
            chosen, focus = ui.bar_choose(
                labels, focus, hints=self.VERB_HINTS, dividers=dividers
            )

            if chosen == "__QUIT__":
                if self.confirm_quit():
                    break
                continue

            action = actions[focus]
            if action["verb"] == "quit":
                if self.confirm_quit():
                    break
                continue

            if action["targets"]:
                ui.blank()
                count = len(action["targets"])
                index = ui.vertical_choose(
                    [label for label, _ in action["targets"]] + ["never mind"],
                    title=f"{action['verb']} — {count} here"
                    if action["verb"] in ("examine", "monocle", "talk")
                    else action["verb"],
                    allow_blank=True,
                    transform_case=True,
                    cancel_index=count,
                )
                if index < 0 or index >= len(action["targets"]):
                    continue
                command = f"{action['command']} {action['targets'][index][1]}"
            else:
                command = action["command"]

            ui.blank()
            self.mark_status_baseline()
            self.dispatch(command)
            self.after_command()

    def confirm_quit(self) -> bool:
        """A single keystroke should not end a three-hour investigation."""
        ui.blank()
        choice = ui.vertical_choose(
            ["keep going", "stop investigating"],
            title="quit",
            allow_blank=True,
            transform_case=True,
            cancel_index=0,
        )
        if choice == 1:
            self.cmd_quit()
            return True
        return False

    def after_command(self) -> None:
        """Shared post-command bookkeeping for both input modes."""
        self.state.flush_beats()
        if self.state.pending_travel:
            destination = self.state.pending_travel
            self.state.pending_travel = None
            self.enter(destination)
        if self.state.ending:
            self.run_ending(self.state.ending)
            self.state.running = False
        elif not self.state.player.is_alive():
            self.on_collapse()

    def run(self, skip_intro: bool = False, create_character: bool = True) -> None:
        if not skip_intro:
            ui.clear()
            ui.block(TITLE.strip("\n"), colour_key="purple")
            ui.rule()
            # Who you are is decided before the town gets a look at you: the
            # opening narration lands differently depending on which voices
            # are loud, so the build comes first.
            if create_character:
                character_creation.run(self.state.player)
                ui.blank()
            ui.narrate(OPENING)
            ui.pause()

        if ui.interactive():
            ui.open_scroll_region()
            ui.install_resize_handler(self.refresh_header)
            self.state.on_change = self.refresh_header
        self.enter(self.state.location_id, first=True)

        try:
            if ui.interactive():
                self.run_bar()
            else:
                self.run_typed()
        finally:
            ui.close_scroll_region()

    def run_typed(self) -> None:
        """Fallback loop: a typed verb parser, read from stdin.

        This is the path pipes and the test suite take, and it remains a
        first-class way to play - the bar is an input method layered over it,
        not a replacement for it.
        """
        while self.state.running:
            try:
                raw = ui.ask("\n> ")
            except (EOFError, KeyboardInterrupt):
                ui.narrate("\nThe sentence goes unfinished. It usually does.")
                break
            if not raw:
                continue
            try:
                self.dispatch(raw)
            except (EOFError, KeyboardInterrupt):
                # Ctrl-C or end of piped input inside a nested prompt - a
                # dialogue menu, a check offer - must end the session
                # cleanly rather than escaping as a traceback.
                ui.narrate("\nThe sentence goes unfinished. It usually does.")
                break
            self.after_command()

    def run_ending(self, ending_id: str) -> None:
        """Render an epilogue from content/endings.json and stop.

        Endings are content, not code: each is a title, a body, and a coda,
        plus a set of consequence lines that only print if the player earned
        the clue behind them. Two people who take the same ending do not read
        the same epilogue, because they did not do the same investigation.
        """
        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "content", "endings.json"
        )
        try:
            with open(path, "r", encoding="utf-8") as handle:
                endings = json.load(handle)
        except (OSError, ValueError):
            ui.warn(f"[content error: endings.json unreadable — ending '{ending_id}']")
            self.state.running = False
            return

        ending = endings.get(ending_id)
        if ending is None:
            ui.warn(f"[content error: no ending '{ending_id}']")
            self.state.running = False
            return

        # Epilogues are always shown at full length. This is the one place in
        # the game where density does not get a vote.
        ui.blank(2)
        ui.rule()
        ui.heading(ending["title"])
        paging = True
        for paragraph in ending["body"]:
            ui.narrate(paragraph)
            if not paging:
                continue
            try:
                ui.pause("")
            except (EOFError, KeyboardInterrupt):
                # The epilogue is the one thing that must always finish. If
                # input has gone away, stop *paging* — never stop printing.
                paging = False

        for consequence in ending.get("consequences", []):
            if self.state.meets(consequence.get("requires", {})):
                ui.aside(consequence["text"])

        if ending.get("furthermore"):
            ui.furthermore(ending["furthermore"])

        ui.rule()
        ui.narrate(ending["coda"])
        self.report_card()
        self.state.running = False

    _clue_total: int | None = None

    @classmethod
    def total_clues(cls) -> int:
        """Count every clue the content can grant.

        Computed once, at the end of a playthrough, by scanning content rather
        than hardcoding a number that goes stale the moment anybody writes a
        location. `requires` blocks are skipped: they reference clue ids
        rather than defining them.
        """
        if cls._clue_total is not None:
            return cls._clue_total

        found: set[str] = set()

        def walk(node) -> None:
            if isinstance(node, dict):
                spec = node.get("clue")
                if isinstance(spec, dict):
                    spec = [spec]
                if isinstance(spec, list):
                    for entry in spec:
                        if isinstance(entry, dict) and "id" in entry:
                            found.add(entry["id"])
                for key, value in node.items():
                    if key != "requires":
                        walk(value)
            elif isinstance(node, list):
                for item in node:
                    walk(item)

        root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content")
        for sub in ("locations", "dialogue"):
            directory = os.path.join(root, sub)
            if not os.path.isdir(directory):
                continue
            for name in sorted(os.listdir(directory)):
                if not name.endswith(".json"):
                    continue
                try:
                    with open(os.path.join(directory, name), "r", encoding="utf-8") as h:
                        walk(json.load(h))
                except (OSError, ValueError):
                    continue

        cls._clue_total = len(found)
        return cls._clue_total

    def report_card(self) -> None:
        """What this playthrough actually consisted of."""
        state = self.state
        inv = state.investigation
        ui.rule()
        rows = [
            f"Clues found        {len(inv.clues)} of {self.total_clues()}",
            f"Beats reached      {len(inv.beats_reached)} of {len(BEATS)}",
            f"Locations visited  {len(inv.visited)} of {len(self.locations.ids)}",
            f"People spoken to   {sum(1 for n in state.npcs.npcs if state.npcs.has_spoken_to(n))}"
            f" of {len(state.npcs.npcs)}",
            f"Lucidity           {state.player.lucidity}/100",
            f"Cycles spent       {state.time.cycle}",
            f"Kindness noticed   {state.tag_count('kindness')}",
            f"Personhood noticed {state.tag_count('personhood')}",
        ]
        ui.block("\n".join(rows))

    def on_collapse(self) -> None:
        ui.heading("You Stop")
        ui.narrate(
            "The body you had been treating as a rumour submits its "
            "resignation. Silvora Reefs accepts it without comment, the way it "
            "accepts everything."
        )
        ui.furthermore("Nevermind.")
        self.state.running = False

    # --- command dispatch --------------------------------------------------

    def dispatch(self, raw: str) -> None:
        text = raw.strip()
        lowered = text.lower()

        def after(*prefixes: str) -> str | None:
            for prefix in prefixes:
                if lowered.startswith(prefix):
                    return text[len(prefix):].strip()
            return None

        if lowered in ("quit", "exit", "q"):
            self.cmd_quit()
        elif lowered in ("help", "?", "commands"):
            ui.aside(HELP_TEXT)
        elif lowered in ("survey", "look", "l", "look around"):
            self.describe_current(reprint=True)
        elif (target := after("look at ", "examine ", "x ", "inspect ")) is not None:
            self.cmd_examine(target)
        elif (target := after("monocle ", "look through monocle at ")) is not None:
            self.cmd_monocle(target)
        elif (target := after("talk to ", "talk ", "speak to ", "ask ")) is not None:
            self.cmd_talk(target)
        elif lowered in ("who", "people"):
            self.cmd_who()
        elif lowered in ("go", "exits", "leave"):
            self.cmd_exits()
        elif (target := after("go to ", "go ", "travel to ")) is not None:
            self.cmd_travel(target)
        elif lowered in ("log", "clues", "notes"):
            self.cmd_log()
        elif lowered in ("case", "theory"):
            self.cmd_case()
        elif lowered in ("sheet", "stats", "character", "me"):
            self.cmd_sheet()
        elif lowered in ("cabinet", "thoughts"):
            self.cmd_cabinet()
        elif lowered in ("think", "furthermore", "hint"):
            self.cmd_think()
        elif lowered in ("wait", "z"):
            self.cmd_wait()
        elif lowered in ("rest", "sleep", "lie down"):
            self.cmd_rest()
        elif lowered.startswith("save"):
            self.state.save(text[4:].strip() or "save")
        elif lowered.startswith("load"):
            self.cmd_load(text[4:].strip() or "save")
        elif lowered == "saves":
            self.cmd_saves()
        else:
            ui.aside(
                "That is not a thing you know how to do. `help` lists the "
                "things that are."
            )

    # --- location ----------------------------------------------------------

    def enter(self, location_id: str, first: bool = False) -> None:
        location = self.locations.get(location_id)
        if location is None:
            ui.warn(f"[content error: no location '{location_id}']")
            return

        self.state.location_id = location_id
        self.state.begin_scene()
        visits = self.state.investigation.mark_visited(location_id)

        ui.heading(location.name)
        if location.subtitle:
            ui.aside(location.subtitle)

        self.describe_current(reprint=False, visits=visits)

        if visits == 1 and location.on_enter:
            self.state.apply_effects(location.on_enter, source=location.name)

        # Ambient flavour, budgeted by density.
        if location.ambient and self.rng.random() < self.state.density.ambient_chance:
            line = self.state.density.pick(self.rng.choice(location.ambient))
            line = wordplay.intoxication_flourish(
                line, self.state.player.intoxication, self.rng
            )
            ui.narrate(line)

        # What *this* investigator notices here, as opposed to what the room
        # contains. Runs after the room's own description so the voices are
        # commenting on something the player has already been shown.
        self.state.ambient_skill_voices(location_id)

        self.cmd_who(quiet=True)
        self.state.flush_beats()

    def describe_current(self, reprint: bool = True, visits: int | None = None) -> None:
        location = self.locations.get(self.state.location_id)
        if location is None:
            return
        if visits is None:
            visits = self.state.investigation.times_visited(location.id)
        if reprint:
            self.state.begin_scene()

        text = self.locations.describe_location(
            location, self.state.density, self.state.player.lucidity_stage, visits
        )
        text = wordplay.intoxication_flourish(
            text, self.state.player.intoxication, self.rng
        )
        ui.narrate(text)

        # What is here to be looked at. Named, not numbered - naming them is
        # not the same as telling you which ones matter.
        visible = [
            obj
            for obj in location.objects
            if not obj.hidden and self.state.meets(obj.requires)
        ]
        if visible:
            names = ", ".join(obj.name for obj in visible)
            ui.aside(f"Worth a look: {names}.")

        exits = self.exit_names(location)
        if exits:
            ui.aside(f"Ways out: {', '.join(exits)}.")

    def exit_names(self, location) -> list[str]:
        names = []
        for target in location.exits:
            names.append(self.locations.display_name(target))
        return names

    # --- verbs -------------------------------------------------------------

    def cmd_examine(self, target: str) -> None:
        location = self.locations.get(self.state.location_id)
        if location is None:
            return
        obj = location.find_object(target)
        if obj is None or not self.state.meets(obj.requires):
            self.miss(target)
            return

        seen = self.state.investigation.times_examined(obj.id)
        text = self.locations.describe_object(
            obj, self.state.density, self.state.player.lucidity_stage, seen
        )
        text = wordplay.intoxication_flourish(
            text, self.state.player.intoxication, self.rng
        )
        ui.narrate(text)

        # Passive commentary fires on every examination; the budget stops it
        # from becoming noise.
        for passive in obj.passive:
            self.state.run_passive(passive, context=f"obj:{obj.id}")

        if seen == 0 and obj.effects:
            self.state.apply_effects(obj.effects, source=obj.name)

        self.state.investigation.mark_examined(obj.id)

        if obj.check:
            self.offer_check(obj)

        self.state.advance_time(1)

    def offer_check(self, obj) -> None:
        """Present an object's active check as an opt-in, never a surprise."""
        check = obj.check
        check_id = check.get("id") or f"obj:{obj.id}"
        kind = CheckKind(check.get("kind", "white"))

        # Most object checks are discoveries: once found, there is nothing
        # left to find. Vices are not discoveries - a man may order a second
        # drink - so they opt out of both the success lock and the retry gate.
        repeatable = check.get("repeatable", False)

        if not repeatable and self.state.checks.succeeded(check_id):
            return
        if not self.state.meets(check.get("requires", {})):
            return
        if not repeatable and not self.state.checks.can_attempt(
            check_id, kind, self.state.state_token()
        ):
            ui.aside(
                "You have already tried that, in that way, with that face on. "
                "Something would have to change."
            )
            return

        skill = check["skill"].replace("_", "-").title()
        dc = check["dc"] + CONFIG["difficulty"]["dc_offset"]
        prompt = self.state.density.pick(check.get("prompt", "Press further?"))
        ui.narrate(prompt)
        persistence = self.state.persistence_bonus(check_id)
        odds = self.dialogue._odds(check, check_id)
        suffix = f", +{persistence} for stubbornness" if persistence else ""
        choice = ui.menu(
            [
                f"Yes.  [{skill} {dc} — {kind.value.upper()}, {odds}{suffix}]",
                "Leave it.",
            ]
        )
        if choice == 1:
            return

        if check.get("irreversible"):
            # A generic "Yes." is the right amount of ceremony for eating
            # something strange. It is not enough ceremony for a one-way
            # door out of the entire investigation - a sweep that says yes
            # to everything it finds (a real playtest pattern) crossed the
            # seam by accident with three locations still unvisited. The
            # consequence has to be stated in the UI, not left to prose a
            # player is skimming, and the safe answer goes first so a stray
            # ENTER does not do the irreversible thing.
            ui.warn("There is no way back from this. Whatever is unfinished stays unfinished.")
            confirm = ui.menu(["No. Not yet.", "Yes. Go through."], allow_blank=True)
            if confirm != 1:
                return

        result = roll_check(
            self.state.player,
            check["skill"],
            check["dc"],
            context=check_id,
            kind=kind,
            bonus=self.state.check_bonus(check, check_id),
        )
        self.state.checks.record(
            check_id, result, self.state.state_token()
        )
        if CONFIG["features"]["show_dice"]:
            ui.aside(result.describe())

        if result.success:
            ui.skill_voice(
                check["skill"], self.state.density.pick(check.get("success", "")), True
            )
            self.state.apply_effects(check.get("success_effects", {}), source=obj.name)
        else:
            ui.skill_voice(
                check["skill"], self.state.density.pick(check.get("failure", "")), False
            )
            self.state.apply_effects(check.get("failure_effects", {}), source=obj.name)

    def cmd_monocle(self, target: str) -> None:
        """The monocle: Oliver's standing instrument, not a plot token.

        It is starting equipment because the lorebook says so, and making it
        a verb turns 'look harder' into a decision the player makes rather
        than an item they wait for.
        """
        if not self.state.player.has_item("monocle"):
            ui.warn("You no longer have the monocle. You notice this constantly.")
            return
        location = self.locations.get(self.state.location_id)
        if location is None:
            return
        obj = location.find_object(target)
        if obj is None or not self.state.meets(obj.requires):
            self.miss(target)
            return

        reveal = self.state.density.pick(obj.monocle)
        if not reveal:
            ui.monocle(
                f"The {obj.name} is exactly what it appears to be. In Silvora "
                f"Reefs this is not reassuring; it is a category of evidence."
            )
        else:
            ui.monocle(reveal)
            if obj.effects.get("monocle_effects"):
                self.state.apply_effects(
                    obj.effects["monocle_effects"], source="the monocle"
                )
        self.state.advance_time(1)

    def cmd_talk(self, target: str) -> None:
        here = self.state.npcs.at_location(self.state.location_id)
        match = None
        lowered = target.lower()
        for npc in here:
            # Exact id, or a substring of at least three characters, so that
            # `talk to a` does not silently pick the first person in the room.
            if lowered == npc.id or (
                len(lowered) >= 3
                and (
                    lowered in npc.name.lower()
                    or lowered in npc.id
                    or (npc.alias and lowered in npc.alias.lower())
                )
            ):
                match = npc
                break
        if match is None:
            ui.aside(
                "Nobody by that description is here, and the ones who are "
                "have not offered."
            )
            return
        self.state.begin_scene()
        self.dialogue.converse(match.id)

    def cmd_who(self, quiet: bool = False) -> None:
        here = self.state.npcs.at_location(self.state.location_id)
        if not here:
            if not quiet:
                ui.aside("Nobody. The room is doing its own supervision.")
            return
        lines = []
        for npc in here:
            standing = self.state.npcs.standing(npc.id)
            mark = {-3: "hostile", -2: "cold", -1: "wary", 0: "", 1: "civil", 2: "warm", 3: "candid"}
            note = mark.get(standing, "")
            suffix = f" ({note})" if note else ""
            shown = self.state.npcs.display_name(npc.id)
            shown_title = self.state.npcs.display_title(npc.id)
            lines.append(f"  · {shown}, {shown_title}{suffix}")
            if not quiet and npc.quirk:
                lines.append(f"      {npc.quirk}")
        ui.aside("Here:\n" + "\n".join(lines))

    def cmd_exits(self) -> None:
        location = self.locations.get(self.state.location_id)
        if location is None or not location.exits:
            ui.aside("No way out has presented itself, which is a first.")
            return
        for target, blurb in location.exits.items():
            ui.aside(f"  → {self.locations.display_name(target)} — {blurb}")

    def cmd_travel(self, target: str) -> None:
        location = self.locations.get(self.state.location_id)
        if location is None:
            return
        lowered = target.lower()
        destination = None
        for candidate in location.exits:
            name = self.locations.display_name(candidate).lower()
            # Match the id, the display name, or a >=3 character fragment of
            # either. Names carry apostrophes and umlauts that nobody is going
            # to type, so `go to dudes` must still find `dudes_dews`.
            if lowered == candidate or name in lowered:
                destination = candidate
                break
            if len(lowered) >= 3 and (lowered in name or lowered in candidate):
                destination = candidate
                break
        if destination is None:
            # The name may be a real place that simply is not adjacent. Saying
            # only "you cannot get there" makes the player guess at the map;
            # naming the first step keeps the geography meaningful without
            # turning travel into a puzzle.
            step = self.first_step_toward(lowered)
            if step:
                target, first = step
                ui.aside(
                    f"{self.locations.display_name(target)} is not on this "
                    f"street. The way there begins with "
                    f"{self.locations.display_name(first)}."
                )
            else:
                ui.aside(
                    "You cannot get there from here. Several people in this "
                    "town would say that is true of everywhere."
                )
            return
        self.state.advance_time(1)
        ui.narrate(
            self.rng.choice(
                [
                    "The streets do their usual trick of being shorter than "
                    "the distance and longer than the walk.",
                    "Fog closes behind you like a sentence being edited.",
                    "The green lampposts hand you off to one another, each "
                    "throwing more shadow than its flame can account for.",
                ]
            )
        )
        self.enter(destination)

    def first_step_toward(self, text: str) -> tuple[str, str] | None:
        """Resolve a non-adjacent destination and return (target, next hop).

        A breadth-first walk of the exit graph. Returns None if the name does
        not match any location, or if there is genuinely no route.
        """
        from collections import deque

        target = None
        for candidate in self.locations.ids:
            if candidate == "the_office":
                continue
            name = self.locations.display_name(candidate).lower()
            if text == candidate or name in text:
                target = candidate
                break
            if len(text) >= 3 and (text in name or text in candidate):
                target = candidate
                break
        if target is None or target == self.state.location_id:
            return None

        start = self.state.location_id
        queue = deque([[start]])
        seen = {start}
        while queue:
            route = queue.popleft()
            if route[-1] == target:
                return (target, route[1]) if len(route) > 1 else None
            location = self.locations.get(route[-1])
            if location is None:
                continue
            for nxt in location.exits:
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(route + [nxt])
        return None

    def miss(self, target: str) -> None:
        ui.aside(
            f"There is no '{target}' here worth the attention, or there is and "
            f"it is not admitting to the name."
        )

    # --- information verbs -------------------------------------------------

    def cmd_log(self) -> None:
        inv = self.state.investigation
        if not inv.clue_order:
            ui.aside("The notebook is still mostly a blue smear.")
            return
        ui.heading("Investigation Log")
        by_beat: dict[str, list] = {}
        for clue_id in inv.clue_order:
            clue = inv.clues[clue_id]
            by_beat.setdefault(clue.beat or "loose", []).append(clue)
        for beat in BEATS:
            entries = by_beat.get(beat["id"])
            if not entries:
                continue
            found, needed = inv.beat_progress(beat["id"])
            ui.aside(f"{beat['name']}  ({found}/{needed})")
            for clue in entries:
                tag = " (red herring?)" if clue.herring else ""
                ui.narrate(f"  · {clue.title}{tag} — {clue.text}")
        loose = by_beat.get("loose")
        if loose:
            ui.aside("Loose ends and local colour")
            for clue in loose:
                ui.narrate(f"  · {clue.title} — {clue.text}")

    def cmd_case(self) -> None:
        """What Oliver currently believes, stated as belief rather than fact."""
        inv = self.state.investigation
        ui.heading("The Case, Such As It Is")
        for beat in BEATS:
            found, needed = inv.beat_progress(beat["id"])
            if beat["id"] in inv.beats_reached:
                mark, verdict = "✓", "you are as sure as this town permits"
            elif found:
                mark, verdict = "·", f"{found} of {needed} — a suspicion with a limp"
            else:
                mark, verdict = " ", "nothing"
            ui.aside(f" {mark} {beat['name']}: {verdict}")
        ui.narrate(self.state.density.describe())

    def cmd_sheet(self) -> None:
        """The character sheet, as a browser rather than a wall of text.

        Twenty-four skills with two paragraphs each is far too much to
        print at once, and printing only the first sentence - which is what
        the six-skill sheet did - throws away the half of each description
        that actually helps a player decide anything. So: scroll the list,
        read the highlighted one in the panel.
        """
        player = self.state.player
        from skill_checks import ATTRIBUTES, ATTRIBUTE_SKILLS
        from skill_detail import paragraphs

        groups = []
        for attribute in ATTRIBUTES:
            entries = []
            for name in ATTRIBUTE_SKILLS[attribute]:
                value = player.skill(name)
                star = " *" if name == player.signature_skill else ""
                label = name.replace("_", "-").title() + star
                entries.append(
                    (name, label, f"{value:>2}  [{modifier_for(value):+d}]")
                )
            groups.append((f"{attribute.title()} {player.attribute(attribute)}", entries))

        if ui.interactive():
            ui.skill_browser(
                groups,
                paragraphs,
                status_lines=self.sheet_status_strip(),
                title=player.display_name,
            )
            return

        # Piped/non-interactive: the old linear sheet, still readable.
        ui.heading(player.display_name)
        ui.skill_browser(groups, paragraphs, status_lines=player.status_lines())
        ui.rule()
        ui.aside("Carrying:")
        for item in player.inventory.values():
            ui.narrate(f"  · {item.name} — {item.description}")
        ui.aside(f"{self.state.time.describe()}. Day {self.state.time.day}.")

    def sheet_status_strip(self) -> list[str]:
        """One compact line of condition, for the browser's footer."""
        player = self.state.player
        return [
            f"morale {player.morale}",
            f"health {player.health}",
            f"lucidity {player.lucidity}",
            f"worn {player.exhaustion}/10",
            f"{self.state.time.describe()}, day {self.state.time.day}",
            "↑ ↓ move    esc  close",
        ]

    def cmd_cabinet(self) -> None:
        state = self.state
        player = state.player
        ui.heading("The Thought Cabinet")
        ui.block(state.elephant.describe_cabinet(
            player, include_available=not ui.interactive()
        ))

        available = list(player.thoughts_known)
        if not available:
            return
        if player.slots_free <= 0:
            ui.aside(
                f"Both slots are occupied. Nothing new goes in until something "
                f"settles — that is what a cabinet is."
            )
            return

        ui.narrate(
            f"Dwell on one of them? It takes cycles, and it changes you, and "
            f"there is room for {player.slots_free}."
        )
        labels = [
            state.elephant.thoughts.get(tid, {}).get("name", tid) for tid in available
        ] + ["Not now."]
        # Blank input is "not now": looking at the cabinet must never trap you
        # in a menu you did not ask for.
        choice = ui.menu(labels, allow_blank=True)
        if choice < 0 or choice >= len(available):
            return
        thought_id = available[choice]
        thought = state.elephant.thoughts.get(thought_id, {})
        if state.elephant.internalise(player, thought_id):
            ui.furthermore(thought.get("premise", "You begin turning it over."))
            cycles = thought.get("cycles", 4)
            ui.aside(
                f"It will take {cycles} {'cycle' if cycles == 1 else 'cycles'} to settle."
            )

    def cmd_think(self) -> None:
        """Ask for a nudge.

        `think` is the command a stuck player reaches for, so it must always
        return something actionable. Furthermore's clarity is gated by
        Lucidity — that gating *is* his arc and it stays — which meant that
        early on, exactly when a player is most likely to be lost, the hint
        was pure atmosphere. A playtest found three consecutive `think`s
        producing no information at all.

        So the two jobs are separated. The elephant does his gag and his
        weather; the *hint* falls back to Oliver's own best skill working the
        problem out loud. He is, after all, a man who cannot stop going over
        things.
        """
        state = self.state
        state.elephant.begin_scene()

        # The anticlimax still fires, but it no longer eats the answer.
        if state.player.lucidity_stage < 4 and self.rng.random() < 0.3:
            line = state.elephant.nevermind(state.player, state.density)
            if line:
                ui.furthermore(line)

        line = state.elephant.hint(state.player, state.investigation, state.density)
        clear_enough = state.player.lucidity_stage >= 2
        if line and clear_enough:
            ui.furthermore(line)
        else:
            if line:
                # He got something across; it just was not words yet.
                ui.furthermore(line)
            self.reason_it_out()
        state.advance_time(1)

    def reason_it_out(self) -> None:
        """Oliver works the nearest unmet beat out himself, in a skill voice.

        This is the hint of last resort and it never fails. It names the kind
        of evidence still missing and where the trail has gone cold, but never
        an object to click.
        """
        state = self.state
        inv = state.investigation

        target = None
        for beat in BEATS:
            if beat["id"] in inv.beats_reached:
                continue
            found, needed = inv.beat_progress(beat["id"])
            if found and target is None:
                target = (beat, found, needed)
            elif target is None:
                target = (beat, found, needed)
            if found:
                break

        skill = "LOGIC" if state.player.skill("LOGIC") >= 12 else state.player.top_skill()

        if target is None:
            ui.skill_voice(
                skill,
                "Everything that can be established has been established. "
                "What is left is not a question of evidence.",
                True,
            )
            return

        beat, found, needed = target

        # Name somewhere that actually carries evidence for *this* beat.
        # Pointing at an arbitrary unvisited location implies a connection
        # that may not exist, which is worse than saying nothing.
        candidates = [
            loc
            for loc in self.beat_locations().get(beat["id"], ())
            if loc != "the_office" and not inv.times_visited(loc)
        ]
        where = ""
        if candidates:
            names = [self.locations.display_name(loc) for loc in candidates]
            others = len(names) - 1
            tail = ""
            if others:
                tail = (
                    f", and in {others} other place you have not been"
                    if others == 1
                    else f", and in {others} other places you have not been"
                )
            where = f" There is something bearing on it in {names[0]}{tail}."
        else:
            where = (
                " Every place that bears on it has been visited at least once. "
                "The rest of it is in somebody's mouth, not on a shelf."
            )

        # "1 of the 3 pieces ... is in the notebook": the noun agrees with the
        # total, the verb with how many you actually hold.
        pieces = "piece" if needed == 1 else "pieces"
        verb = "is" if found == 1 else "are"
        ui.skill_voice(
            skill,
            f"{beat['summary']} {found} of the {needed} {pieces} that would "
            f"let you believe it {verb} in the notebook.{where}",
            True,
        )

    _beat_locations: dict[str, set[str]] | None = None

    @classmethod
    def beat_locations(cls) -> dict[str, set[str]]:
        """Map each beat to the locations whose content can grant its clues.

        Built once from the content files. Dialogue is attributed to the NPC's
        location, so "go and talk to somebody in Giddyup" is expressible.
        """
        if cls._beat_locations is not None:
            return cls._beat_locations

        root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content")
        result: dict[str, set[str]] = {}

        def collect(node, where: str) -> None:
            if isinstance(node, dict):
                spec = node.get("clue")
                if isinstance(spec, dict):
                    spec = [spec]
                if isinstance(spec, list):
                    for entry in spec:
                        if isinstance(entry, dict) and entry.get("beat"):
                            result.setdefault(entry["beat"], set()).add(where)
                for key, value in node.items():
                    if key != "requires":
                        collect(value, where)
            elif isinstance(node, list):
                for item in node:
                    collect(item, where)

        try:
            with open(os.path.join(root, "npcs.json"), encoding="utf-8") as handle:
                npc_home = {n["id"]: n.get("location", "") for n in json.load(handle)}
        except (OSError, ValueError):
            npc_home = {}

        for sub in ("locations", "dialogue"):
            directory = os.path.join(root, sub)
            if not os.path.isdir(directory):
                continue
            for name in sorted(os.listdir(directory)):
                if not name.endswith(".json"):
                    continue
                stem = name[:-5]
                where = stem if sub == "locations" else npc_home.get(stem, "")
                if not where:
                    continue
                try:
                    with open(os.path.join(directory, name), encoding="utf-8") as handle:
                        collect(json.load(handle), where)
                except (OSError, ValueError):
                    continue

        cls._beat_locations = result
        return result

    def cmd_wait(self) -> None:
        ui.narrate(
            self.rng.choice(
                [
                    "You wait. Silvora Reefs waits with you, and is better at it.",
                    "Time passes, in the local sense: the clocks disagree by a "
                    "slightly different margin than before.",
                    "You stand still long enough for the fog to consider you "
                    "part of the architecture, then move before it decides.",
                ]
            )
        )
        self.state.advance_time(1)

    # Where a man can put his head down, and what it says when he does.
    BEDS = {
        "hang_hi": (
            "Your own flat, your own bed, in a building that hangs from "
            "nothing and has never once dropped anybody.\n\nYou do not dream. "
            "That is worth recording, because a man in your position has "
            "started keeping track: you lie down in a town with no dawn and "
            "nothing whatsoever happens behind your eyes, and you get up, and "
            "the corridor is a corridor for about an hour afterwards."
        ),
        "outside_inn": (
            "Seven a night and the weather is included, which Barney says "
            "every time and has never once been asked to explain.\n\nThe room "
            "has a ceiling with stars in it that are almost the ones you know. "
            "Somewhere below, a stream goes into a wall. You sleep the way "
            "people sleep outdoors, which is badly and completely, and wake up "
            "with the specific clean tiredness of a man who has been rained on "
            "by something that meant well."
        ),
    }

    def cmd_rest(self) -> None:
        """Sleep off the exhaustion.

        A playtest found the exhaustion economy was one-way: the clock added
        it every few cycles and the entire game contained a single source of
        relief, so every player arrived at the confrontation permanently
        penalised. There is an inn in this town with rooms at seven a night.
        Now they are for something.
        """
        where = self.state.location_id
        if where not in self.BEDS:
            nearby = self.first_step_toward("outside inn")
            hint = ""
            if nearby:
                hint = (
                    f" The nearest bed that is not yours is at The Outside "
                    f"Inn, and the way there begins with "
                    f"{self.locations.display_name(nearby[1])}."
                )
            elif where != "outside_inn":
                hint = " Your own flat has a bed in it. So does The Outside Inn."
            ui.aside(
                "There is nowhere here to lie down that would not be a "
                "statement." + hint
            )
            return

        if self.state.player.exhaustion == 0 and self.state.player.health >= 95:
            ui.aside("You are not tired enough to justify it, and you have tried.")
            return

        ui.narrate(self.BEDS[where])
        rested = self.state.player.adjust_exhaustion(-10)
        healed = self.state.player.adjust_health(12)
        if rested:
            ui.aside(f"Exhaustion cleared ({rested}).")
        if healed:
            ui.aside(f"Health {healed:+d}.")
        # Sleep is not free: the town gets a few cycles to itself.
        self.state.advance_time(4)

    def cmd_saves(self) -> None:
        rows = GameState.list_saves()
        if not rows:
            ui.aside("No saves.")
            return
        for slot, when in rows:
            ui.aside(f"  {slot:<16}{when}")

    def cmd_load(self, slot: str) -> None:
        loaded = GameState.load(slot)
        if loaded is None:
            ui.warn(f"No save called '{slot}'.")
            return
        self.state = loaded
        self.dialogue = DialogueEngine(self.state)
        if ui.interactive():
            self.state.on_change = self.refresh_header
        ui.aside(f"Loaded '{slot}'.")
        self.enter(self.state.location_id)

    def cmd_quit(self) -> None:
        ui.narrate(
            "You stop investigating. The town does not stop being investigable."
        )
        ui.furthermore("Nevermind.")
        self.state.running = False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Malice in Underland")
    parser.add_argument("--load", metavar="SLOT", help="load a save on start")
    parser.add_argument("--seed", type=int, help="seed the RNG for reproducible runs")
    parser.add_argument("--no-intro", action="store_true")
    parser.add_argument("--no-create", action="store_true",
                        help="skip character creation, use the fallback build")
    parser.add_argument("--debug", action="store_true", help="show dice and tracebacks")
    parser.add_argument("--voice", action="store_true",
                        help="speak everything aloud with Piper TTS (see content/voices.json)")
    args = parser.parse_args(argv)

    if args.voice:
        import voice as _voice
        if not _voice.enable(True):
            print("voice: unavailable (need `pip install piper-tts` and an audio player); continuing silently")

    if args.seed is not None:
        random.seed(args.seed)
    if args.debug:
        CONFIG["features"]["show_dice"] = True
        CONFIG["features"]["debug"] = True

    state = GameState.load(args.load) if args.load else None
    if args.load and state is None:
        ui.warn(f"No save called '{args.load}'. Starting fresh.")
    game = Game(state)

    try:
        game.run(
            skip_intro=args.no_intro or bool(args.load),
            create_character=not args.no_create and not args.load,
        )
    except KeyboardInterrupt:
        ui.narrate("\nNevermind.")
    except Exception:
        if CONFIG["features"]["debug"]:
            raise
        ui.warn(
            "Something in Silvora Reefs failed in a way it is not prepared to "
            "narrate. Re-run with --debug for the traceback."
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
