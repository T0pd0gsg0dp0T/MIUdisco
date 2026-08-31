"""Dialogue as a conditional node graph.

A conversation is a dict of nodes. Each node has speaker text and a list of
options; each option may carry `requires` (visibility conditions), a `check`
(a skill roll with separate success and failure destinations), and `effects`
(state changes). Options never auto-resolve: even a single surviving option
is presented as a numbered choice, because the act of choosing is what makes
a dialogue tree a game rather than a cutscene.

Two rules the engine enforces that the content files do not have to think
about:

  * A failed check always has somewhere to go. If an option's check omits a
    failure destination, the engine routes back to the current node with the
    failure text shown - so a bad roll costs you an approach, never the
    conversation.
  * Exhausted nodes hide themselves. Options tagged `once` disappear after
    they have been taken, so a player cannot re-mine a good line, and the
    option list shrinks toward the exits the way a real conversation does.

Node schema (content/dialogue/<npc>.json):

    {"nodes": {
       "root": {
          "text": "..." | {"low":..,"mid":..,"high":..},
          "lucid": {"2": "extra paragraph at lucidity stage 2+"},
          "effects": {...},
          "options": [
             {"text": "...",
              "requires": {...},
              "check": {"skill":"RHETORIC","dc":13,"kind":"white",
                        "success":"node_a","failure":"node_b",
                        "success_text":"...","failure_text":"..."},
              "goto": "node_c",
              "effects": {...},
              "once": true}
          ]}}}
"""

from __future__ import annotations

import json
import os

import ui
from locations import _stage_variant
from skill_checks import CheckKind, roll_check
from config import CONFIG

CONTENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content")
DIALOGUE_DIR = os.path.join(CONTENT_DIR, "dialogue")

# Sentinel used by options that end the conversation.
EXIT_NODE = "__exit__"


class DialogueEngine:
    def __init__(self, state) -> None:
        self.state = state
        self._cache: dict[str, dict] = {}

    # --- loading -----------------------------------------------------------

    def load(self, npc) -> dict | None:
        filename = npc.dialogue_file or f"{npc.id}.json"
        if filename in self._cache:
            return self._cache[filename]
        path = os.path.join(DIALOGUE_DIR, filename)
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, ValueError):
            return None
        self._cache[filename] = data
        return data

    # --- running -----------------------------------------------------------

    def converse(self, npc_id: str) -> None:
        """Run a full conversation with the given NPC."""
        state = self.state
        npc = state.npcs.get(npc_id)
        if npc is None:
            ui.warn("There is nobody by that name here.")
            return

        tree = self.load(npc)
        if tree is None or not tree.get("nodes"):
            ui.warn(
                f"{state.npcs.display_name(npc.id)} has nothing to say that "
                "anyone has written down."
            )
            return

        shown = state.npcs.display_name(npc.id)
        ui.heading(f"{shown} — {state.npcs.display_title(npc.id)}")
        if npc.appearance and state.density.band != "high":
            ui.narrate(state.density.pick(npc.appearance))

        greeting = state.npcs.greeting(npc_id)
        if greeting and not state.npcs.has_spoken_to(npc_id):
            ui.speech(shown, greeting, npc.colour, voice_id=npc.id)

        node_id = npc.entry_node
        guard = 0
        # Nodes already delivered in *this* conversation. Returning to a hub
        # after a failed check should not replay its whole paragraph; the
        # player read it ninety seconds ago and wants the options.
        shown: set[str] = set()
        while node_id and node_id != EXIT_NODE:
            guard += 1
            if guard > 200:
                # Cheap infinite-loop protection for malformed content.
                ui.warn("The conversation has begun to repeat itself. You step back.")
                break
            node_id = self._run_node(npc, tree, node_id, shown)

        state.time.spend(1)

    def _run_node(
        self, npc, tree: dict, node_id: str, shown: set[str] | None = None
    ) -> str | None:
        """Display one node and return the id of the next one."""
        state = self.state
        node = tree["nodes"].get(node_id)
        if node is None:
            ui.warn(f"[content error: node '{node_id}' is missing]")
            return EXIT_NODE

        shown = shown if shown is not None else set()
        repeat_visit = node_id in shown
        shown.add(node_id)

        # Speaker text. Suppressed on a return visit within one conversation.
        text = state.density.pick(node.get("text", ""))
        if text and not repeat_visit:
            speaker = node.get("speaker", state.npcs.display_name(npc.id))
            if node.get("narration"):
                ui.narrate(text)
            else:
                ui.speech(speaker, text, npc.colour, voice_id=npc.id)
        elif repeat_visit:
            ui.aside(f"{state.npcs.display_name(npc.id)} waits.")

        overlay = _stage_variant(node.get("lucid", {}), state.player.lucidity_stage)
        if overlay and not repeat_visit:
            ui.narrate(overlay)

        # Node-level effects fire once per node per playthrough.
        if node.get("effects") and not state.npcs.seen(npc.id, node_id):
            state.apply_effects(node["effects"], source=f"{npc.name}")
        state.npcs.mark_seen(npc.id, node_id)

        # Passive skill commentary attached to the node, once per visit.
        if not repeat_visit:
            for passive in node.get("passive", []):
                state.run_passive(passive, context=f"dialogue:{npc.id}:{node_id}")

        # Build the visible option list.
        options = self._visible_options(npc, node.get("options", []))
        if not options:
            ui.aside("There is nothing further to say.")
            return EXIT_NODE

        # A node whose every option is a spent check would loop for ever:
        # each pick prints a refusal and returns here. Guarantee a way out.
        # This costs nothing when the author has already provided one.
        if all(option.get("_locked") for option in options):
            options = options + [
                {
                    "id": "__escape__",
                    "text": "Let it go, for now.",
                    "goto": EXIT_NODE,
                }
            ]

        labels = [self._label(option, npc) for option in options]
        choice = ui.menu(labels)
        chosen = options[choice]

        return self._resolve_option(npc, node_id, chosen)

    def _visible_options(self, npc, options: list[dict]) -> list[dict]:
        state = self.state
        visible: list[dict] = []
        for option in options:
            if option.get("once") and state.npcs.seen(
                npc.id, self._option_key(npc, option)
            ):
                continue
            if not state.meets(option.get("requires", {})):
                continue
            check = option.get("check")
            if check:
                check_id = self._check_id(npc, option)
                kind = CheckKind(check.get("kind", "white"))
                already = state.checks.succeeded(check_id)
                if already and check.get("hide_when_passed", True):
                    # The successful outcome is normally reachable another way;
                    # keep the option only if the author asked for it.
                    continue
                if not state.checks.can_attempt(
                    check_id, kind, state.state_token()
                ):
                    if not check.get("show_when_locked", True):
                        continue
                    option = dict(option, _locked=True)
            visible.append(option)

        # Spent checks sink to the bottom. Leaving a dead option in slot 1
        # reads as the game ignoring you - it was the first thing a playtest
        # complained about - while removing it entirely loses the useful
        # information that there is something here to come back for.
        visible.sort(key=lambda option: bool(option.get("_locked")))
        return visible

    @staticmethod
    def _option_key(npc, option: dict) -> str:
        return f"opt:{npc.id}:{option.get('id') or option['text'][:40]}"

    @staticmethod
    def _check_id(npc, option: dict) -> str:
        check = option.get("check", {})
        return check.get("id") or f"{npc.id}:{option.get('id') or option['text'][:40]}"

    def _label(self, option: dict, npc=None) -> str:
        """Render an option, annotating any attached check the DE way."""
        text = option["text"]
        check = option.get("check")
        if not check:
            return text
        skill = check["skill"].replace("_", "-").title()
        dc = check["dc"] + CONFIG["difficulty"]["dc_offset"]
        kind = check.get("kind", "white").upper()
        check_id = self._check_id(npc, option) if npc is not None else check.get("id")
        if option.get("_locked"):
            return (
                f"{text}  [{skill} {dc} — {kind}, tried and failed; "
                f"learn something new and you may try again]"
            )
        odds = self._odds(check, check_id)
        persistence = self.state.persistence_bonus(check_id)
        if persistence:
            return f"{text}  [{skill} {dc} — {kind}, {odds}, +{persistence} for stubbornness]"
        return f"{text}  [{skill} {dc} — {kind}, {odds}]"

    def _odds(self, check: dict, check_id: str | None = None) -> str:
        """A qualitative difficulty read, not a percentage.

        Exposing the exact number would turn every choice into arithmetic.
        The player gets the same information a person gets: a sense.

        This must account for every bonus the roll will actually receive -
        clue, flag, thought and persistence - or the game misreports its own
        difficulty, which a playtest caught it doing.
        """
        from skill_checks import modifier_for, status_modifiers

        state = self.state
        skill = check["skill"]
        modifier = modifier_for(state.player.skill(skill))
        modifier += sum(amount for _, amount in status_modifiers(state.player, skill))
        modifier += state.check_bonus(check, check_id)
        dc = check["dc"] + CONFIG["difficulty"]["dc_offset"]
        needed = dc - modifier
        # 2d6 is a bell, so these bands are much tighter than the old d20
        # ones: needing 7 is a coin flip, needing 10 is already a long shot,
        # and needing 12 is one exact outcome in thirty-six.
        if needed <= 4:
            return "trivial"        # 92%+
        if needed <= 6:
            return "comfortable"    # ~72%
        if needed <= 8:
            return "even odds"      # ~42%
        if needed <= 10:
            return "unlikely"       # ~17%
        if needed <= 12:
            return "desperate"      # ~3%
        return "impossible"

    def _resolve_option(self, npc, node_id: str, option: dict) -> str | None:
        state = self.state

        if option.get("once"):
            state.npcs.mark_seen(npc.id, self._option_key(npc, option))

        # An option the player picked despite it being locked: say so plainly
        # and return to the same node rather than silently doing nothing.
        if option.get("_locked"):
            ui.aside(
                "You have already made that argument, in those words, to that "
                "face. Learn something new and it may sound different."
            )
            return node_id

        check = option.get("check")
        if not check:
            if option.get("effects"):
                state.apply_effects(option["effects"], source=npc.name)
            return option.get("goto", EXIT_NODE)

        check_id = self._check_id(npc, option)
        kind = CheckKind(check.get("kind", "white"))
        result = roll_check(
            state.player,
            check["skill"],
            check["dc"],
            context=check_id,
            kind=kind,
            bonus=state.check_bonus(check, check_id),
            bonus_label=check.get("bonus_label", "circumstance"),
        )
        state.checks.record(check_id, result, state.state_token())

        if CONFIG["features"]["show_dice"]:
            ui.aside(result.describe())

        if result.success:
            text = state.density.pick(check.get("success_text", ""))
            if text:
                ui.narrate(text)
            if check.get("success_effects"):
                state.apply_effects(check["success_effects"], source=npc.name)
            if option.get("effects"):
                state.apply_effects(option["effects"], source=npc.name)
            return check.get("success", option.get("goto", node_id))

        text = state.density.pick(check.get("failure_text", ""))
        if text:
            ui.narrate(text)
        if check.get("failure_effects"):
            state.apply_effects(check["failure_effects"], source=npc.name)
        # Rule: failure always has somewhere to go. Default is back here.
        return check.get("failure", node_id)
