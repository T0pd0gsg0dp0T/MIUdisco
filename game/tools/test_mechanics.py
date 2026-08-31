#!/usr/bin/env python3
"""Unit tests for the mechanical core. Run: python3 tools/test_mechanics.py

Covers the rules that are invisible in play and therefore easy to break:
the 2d6 maths, the white/red retry ledger, condition evaluation, beat
thresholds, save round-tripping, prose-band selection, and the wordplay
engine's exact letter operations.
"""

from __future__ import annotations

import json
import os
import random
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import game_state  # noqa: E402
import wordplay_engine as wordplay  # noqa: E402
from investigation import BEATS_BY_ID, Clue, Investigation  # noqa: E402
from narrative_density import NarrativeDensity  # noqa: E402
from player import Player  # noqa: E402
import character_creation  # noqa: E402
from skill_checks import (  # noqa: E402
    CheckKind,
    CheckLedger,
    modifier_for,
    roll_check,
    status_modifiers,
)


class TestSkillMaths(unittest.TestCase):
    def test_modifier_is_the_skill_value(self):
        """Under 2d6 the number on the sheet is the number added to the roll."""
        for value in (1, 2, 3, 4, 5, 6, 9):
            self.assertEqual(modifier_for(value), value)

    def test_dice_are_two_six_sided(self):
        from skill_checks import DICE_COUNT, DICE_MAX, DICE_MIN, DICE_SIDES

        self.assertEqual((DICE_COUNT, DICE_SIDES), (2, 6))
        self.assertEqual((DICE_MIN, DICE_MAX), (2, 12))

    def test_rolls_stay_inside_the_bell(self):
        from skill_checks import DICE_MAX, DICE_MIN, roll_check

        player = Player()
        for _ in range(200):
            result = roll_check(player, "LOGIC", 8)
            self.assertGreaterEqual(result.roll, DICE_MIN)
            self.assertLessEqual(result.roll, DICE_MAX)

    def test_authored_dcs_are_reachable_on_2d6(self):
        """Every DC in the content must be beatable by a plausible build.

        2d6 caps at 12, so a DC that assumed a d20 would be quietly
        impossible rather than merely hard - which is exactly the kind of
        thing that only shows up three hours into a playthrough.
        """
        import glob

        worst = 0
        for path in glob.glob(
            os.path.join(ROOT, "content", "**", "*.json"),
            recursive=True,
        ):
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)

            def walk(node):
                nonlocal worst
                if isinstance(node, dict):
                    if isinstance(node.get("dc"), int):
                        worst = max(worst, node["dc"])
                    for value in node.values():
                        walk(value)
                elif isinstance(node, list):
                    for value in node:
                        walk(value)

            walk(data)
        # A signature specialist sits around 8; 12 on the dice is possible.
        self.assertLessEqual(worst, 14, f"DC {worst} is out of reach on 2d6")

    def test_natural_max_always_succeeds(self):
        player = Player()
        rng = random.Random()
        rng.randint = lambda a, b: 6  # type: ignore
        result = roll_check(player, "PHYSIQUE", dc=99, rng=rng)
        self.assertTrue(result.success)
        self.assertTrue(result.critical)

    def test_natural_1_always_fails(self):
        player = Player()
        rng = random.Random()
        rng.randint = lambda a, b: 1  # type: ignore
        result = roll_check(player, "RHETORIC", dc=2, rng=rng)
        self.assertFalse(result.success)
        self.assertTrue(result.fumble)

    def test_unknown_skill_rejected(self):
        with self.assertRaises(ValueError):
            roll_check(Player(), "CHARISMA", dc=10)


class TestStatusModifiers(unittest.TestCase):
    def test_intoxication_is_a_trade(self):
        player = Player()
        player.intoxication = 6
        electro = dict(status_modifiers(player, "ELECTROCHEMISTRY"))
        logic = dict(status_modifiers(player, "LOGIC"))
        self.assertGreater(electro["intoxicated"], 0)
        self.assertLess(logic["intoxicated"], 0)

    def test_monocle_aids_logic_and_savant_faire(self):
        player = Player()
        self.assertIn("monocle", dict(status_modifiers(player, "LOGIC")))
        player.remove_item("monocle")
        self.assertNotIn("monocle", dict(status_modifiers(player, "LOGIC")))

    def test_lucidity_shifts_which_skills_work(self):
        player = Player()
        player.lucidity = 60
        logic = dict(status_modifiers(player, "LOGIC"))
        rhetoric = dict(status_modifiers(player, "RHETORIC"))
        self.assertLess(logic["lucid"], 0)
        self.assertGreater(rhetoric["lucid"], 0)


class TestCheckLedger(unittest.TestCase):
    def setUp(self):
        self.ledger = CheckLedger()
        self.player = Player()

    def _fail(self, kind):
        rng = random.Random()
        rng.randint = lambda a, b: 2  # type: ignore
        return roll_check(self.player, "LOGIC", dc=30, kind=kind, rng=rng)

    def test_red_check_is_one_shot(self):
        result = self._fail(CheckKind.RED)
        self.ledger.record("c1", result, "tokenA")
        self.assertFalse(self.ledger.can_attempt("c1", CheckKind.RED, "tokenB"))

    def test_white_check_retries_only_on_state_change(self):
        result = self._fail(CheckKind.WHITE)
        self.ledger.record("c2", result, "tokenA")
        self.assertFalse(self.ledger.can_attempt("c2", CheckKind.WHITE, "tokenA"))
        self.assertTrue(self.ledger.can_attempt("c2", CheckKind.WHITE, "tokenB"))

    def test_success_closes_the_check(self):
        rng = random.Random()
        rng.randint = lambda a, b: 6  # type: ignore
        result = roll_check(self.player, "LOGIC", dc=5, rng=rng)
        self.ledger.record("c3", result, "tokenA")
        self.assertTrue(self.ledger.succeeded("c3"))
        self.assertFalse(self.ledger.can_attempt("c3", CheckKind.WHITE, "tokenZ"))

    def test_round_trip(self):
        self.ledger.record("c4", self._fail(CheckKind.WHITE), "tok")
        restored = CheckLedger.from_dict(self.ledger.to_dict())
        self.assertEqual(restored.records, self.ledger.records)


class TestRetryBackstop(unittest.TestCase):
    """A white check must never lock permanently.

    A playtest lost the best ending to one bad roll: the confrontation
    happens in a room with no exits and nothing left to examine, so the
    investigation state could not move and the retry never unlocked."""

    def setUp(self):
        self.state = game_state.GameState()
        self.cid = "revilo:personhood"

    def _fail_once(self):
        rng = random.Random()
        rng.randint = lambda a, b: 2  # type: ignore
        result = roll_check(self.state.player, "EMPATHY", dc=30, rng=rng)
        self.state.checks.record(self.cid, result, self.state.state_token())

    def test_hearing_something_new_unlocks_the_retry(self):
        self._fail_once()
        token = self.state.state_token()
        self.assertFalse(
            self.state.checks.can_attempt(self.cid, CheckKind.WHITE, token)
        )
        self.state.npcs.mark_seen("revilo", "arg_two")
        self.assertTrue(
            self.state.checks.can_attempt(
                self.cid, CheckKind.WHITE, self.state.state_token()
            )
        )

    def test_repeated_failure_unlocks_even_with_nothing_new(self):
        limit = game_state.CONFIG["difficulty"]["retry_after_failures"]
        for _ in range(limit):
            self._fail_once()
        # Nothing in the world has changed, and it must still be attemptable.
        self.assertTrue(
            self.state.checks.can_attempt(
                self.cid, CheckKind.WHITE, self.state.state_token()
            )
        )

    def test_backstop_threshold_is_reachable(self):
        """The threshold must be <= the failures a stuck player can reach.

        Attempts only increment while unlocked, so a stuck player gets one
        free attempt plus one per state change. A threshold above 2 can never
        fire for someone who has genuinely run out of things to learn - which
        is exactly who the backstop exists for."""
        self.assertLessEqual(
            game_state.CONFIG["difficulty"]["retry_after_failures"], 2
        )

    def test_stuck_player_always_gets_back_in(self):
        """Simulate the sealed room: fail, one state change, fail, nothing left."""
        self._fail_once()
        self.state.npcs.mark_seen("revilo", "arg_two")   # the one state change
        self.assertTrue(self.state.checks.can_attempt(
            self.cid, CheckKind.WHITE, self.state.state_token()))
        self._fail_once()
        # Nothing further can change. It must still be attemptable.
        self.assertTrue(self.state.checks.can_attempt(
            self.cid, CheckKind.WHITE, self.state.state_token()))

    def test_red_checks_stay_one_shot(self):
        rng = random.Random()
        rng.randint = lambda a, b: 2  # type: ignore
        for _ in range(9):
            result = roll_check(
                self.state.player, "EMPATHY", dc=30, kind=CheckKind.RED, rng=rng
            )
            self.state.checks.record("red", result, self.state.state_token())
        self.assertFalse(
            self.state.checks.can_attempt(
                "red", CheckKind.RED, self.state.state_token()
            )
        )


class TestInvestigation(unittest.TestCase):
    def setUp(self):
        self.inv = Investigation()

    def _add(self, index, beat="crash", herring=False):
        return self.inv.add_clue(
            Clue(id=f"x{index}", title=f"t{index}", text="", beat=beat, herring=herring)
        )

    def test_duplicate_clues_rejected(self):
        self.assertTrue(self._add(1))
        self.assertFalse(self._add(1))

    def test_beat_fires_at_threshold(self):
        threshold = BEATS_BY_ID["crash"]["threshold"]
        for i in range(threshold - 1):
            self._add(i)
        self.assertEqual(self.inv.check_beats(), [])
        self._add(99)
        self.assertIn("crash", self.inv.check_beats())

    def test_beat_fires_only_once(self):
        for i in range(10):
            self._add(i)
        self.assertIn("crash", self.inv.check_beats())
        self.assertNotIn("crash", self.inv.check_beats())

    def test_red_herrings_do_not_count(self):
        for i in range(10):
            self._add(i, herring=True)
        found, _needed = self.inv.beat_progress("crash")
        self.assertEqual(found, 0)

    def test_state_token_changes_with_evidence(self):
        before = self.inv.state_token()
        self._add(1)
        self.assertNotEqual(before, self.inv.state_token())

    def test_state_token_changes_with_flags(self):
        before = self.inv.state_token()
        self.inv.set_flag("something", True)
        self.assertNotEqual(before, self.inv.state_token())

    def test_round_trip(self):
        self._add(1)
        self.inv.set_flag("f", True)
        self.inv.mark_visited("hang_hi")
        restored = Investigation.from_dict(self.inv.to_dict())
        self.assertTrue(restored.has_clue("x1"))
        self.assertTrue(restored.flag("f"))
        self.assertEqual(restored.times_visited("hang_hi"), 1)


class TestConditions(unittest.TestCase):
    def setUp(self):
        self.state = game_state.GameState()

    def test_empty_condition_is_true(self):
        self.assertTrue(self.state.meets({}))

    def test_clue_requirement(self):
        self.assertFalse(self.state.meets({"clue": "nope"}))
        self.state.investigation.add_clue(Clue("nope", "t", ""))
        self.assertTrue(self.state.meets({"clue": "nope"}))

    def test_negative_clue_requirement(self):
        self.assertTrue(self.state.meets({"not_clue": "nope"}))
        self.state.investigation.add_clue(Clue("nope", "t", ""))
        self.assertFalse(self.state.meets({"not_clue": "nope"}))

    def test_ranges(self):
        self.state.player.lucidity = 50
        self.assertTrue(self.state.meets({"lucidity_min": 40}))
        self.assertFalse(self.state.meets({"lucidity_min": 60}))
        self.assertTrue(self.state.meets({"lucidity_max": 60}))
        self.assertFalse(self.state.meets({"lucidity_max": 40}))

    def test_conditions_are_anded(self):
        self.state.player.lucidity = 50
        self.assertFalse(self.state.meets({"lucidity_min": 40, "clue": "nope"}))

    def test_flag_value_matching(self):
        self.state.investigation.set_flag("mode", "loud")
        self.assertTrue(self.state.meets({"flag": {"mode": "loud"}}))
        self.assertFalse(self.state.meets({"flag": {"mode": "quiet"}}))


class TestPlayer(unittest.TestCase):
    def test_status_clamped(self):
        player = Player()
        player.adjust_morale(1000)
        self.assertEqual(player.morale, 100)
        player.adjust_morale(-1000)
        self.assertEqual(player.morale, 0)
        player.adjust_intoxication(1000)
        self.assertEqual(player.intoxication, 10)

    def test_lucidity_stages(self):
        player = Player()
        player.lucidity = 0
        self.assertEqual(player.lucidity_stage, 0)
        player.lucidity = 95
        self.assertEqual(player.lucidity_stage, 4)

    def test_thought_internalisation(self):
        player = Player()
        player.offer_thought("t")
        self.assertTrue(player.begin_internalising("t", 2))
        self.assertEqual(player.tick_thoughts(), [])
        self.assertEqual(player.tick_thoughts(), ["t"])
        self.assertTrue(player.has_thought("t"))

    def test_cannot_internalise_unknown_thought(self):
        self.assertFalse(Player().begin_internalising("nope", 2))

    def test_round_trip(self):
        player = Player()
        player.adjust_skill("LOGIC", 2)
        player.lucidity = 33
        restored = Player.from_dict(player.to_dict())
        self.assertEqual(restored.skill("LOGIC"), player.skill("LOGIC"))
        self.assertEqual(restored.lucidity, 33)


class TestLucidityCurve(unittest.TestCase):
    """Lucidity gains diminish toward the cap. The content grants ~1900 raw
    against a scale of 100; without this the whole mechanic - and with it
    Furthermore's clarity arc - saturated in the first fifth of the game."""

    def test_gains_diminish(self):
        player = Player()
        first = player.adjust_lucidity(10)
        player.lucidity = 90
        late = player.adjust_lucidity(10)
        self.assertGreater(first, late)

    def test_never_gains_nothing(self):
        player = Player()
        player.lucidity = 99
        before = player._lucidity_exact
        player.adjust_lucidity(1)
        self.assertGreater(player._lucidity_exact, before)

    def test_cap_is_respected(self):
        player = Player()
        for _ in range(500):
            player.adjust_lucidity(20)
        self.assertLessEqual(player.lucidity, 100)

    def test_losses_are_flat(self):
        player = Player()
        player.lucidity = 50
        self.assertEqual(player.adjust_lucidity(-8), -8)

    def test_losses_clamp_at_zero(self):
        player = Player()
        player.lucidity = 3
        player.adjust_lucidity(-99)
        self.assertEqual(player.lucidity, 0)

    def test_setter_and_property_agree(self):
        player = Player()
        player.lucidity = 70
        self.assertEqual(player.lucidity, 70)
        self.assertEqual(player._lucidity_exact, 70.0)

    def test_reaching_stage_four_takes_real_investigation(self):
        """Stage 4 should cost several hundred raw points, not a handful."""
        player = Player()
        raw = 0
        while player.lucidity_stage < 4 and raw < 5000:
            player.adjust_lucidity(10)
            raw += 10
        self.assertGreater(raw, 300, "stage 4 arrives too cheaply")
        self.assertLess(raw, 1500, "stage 4 is unreachable in practice")


class TestDensity(unittest.TestCase):
    """The pacing dial is gone; prose is always the fullest telling.

    These replace the old band/auto-scale suite, which tested a dial that no
    longer exists. What matters now is that the thinner authored variants
    still in the content files can never be selected, and that the old API
    stayed callable so saves and stray callers do not explode.
    """

    def test_always_the_fullest_band(self):
        self.assertEqual(NarrativeDensity().band, "low")

    def test_pick_prefers_the_fullest_variant(self):
        density = NarrativeDensity()
        passage = {"low": "the long look", "mid": "trimmed", "high": "terse"}
        self.assertEqual(density.pick(passage), "the long look")

    def test_pick_falls_back_when_full_variant_absent(self):
        density = NarrativeDensity()
        self.assertEqual(density.pick({"high": "only high"}), "only high")
        self.assertEqual(density.pick({"mid": "only mid"}), "only mid")

    def test_pick_passes_plain_strings(self):
        self.assertEqual(NarrativeDensity().pick("plain"), "plain")

    def test_set_level_cannot_thin_the_prose(self):
        """The old API stays callable and stays inert.

        Saves written before the dial was removed carry a level, and
        from_dict must not resurrect it - a loaded save that silently
        rendered at density 9 would be a real regression.
        """
        density = NarrativeDensity(9)
        density.set_level(10)
        density.scale_to_progress(5, 6)
        self.assertEqual(density.band, "low")
        self.assertEqual(
            density.pick({"low": "full", "high": "terse"}), "full"
        )

    def test_from_dict_ignores_a_stale_level(self):
        density = NarrativeDensity.from_dict({"level": 10, "pinned": True})
        self.assertEqual(density.band, "low")

    def test_ambient_is_always_on(self):
        density = NarrativeDensity()
        self.assertTrue(density.show_ambient)
        self.assertGreater(density.ambient_chance, 0)


class TestWordplay(unittest.TestCase):
    def test_central_reversal_is_exact(self):
        self.assertTrue(wordplay.is_reversal("Oliver Onions", "Snoino Revilo"))

    def test_reversal_is_not_symmetric_with_anagram(self):
        self.assertFalse(wordplay.is_reversal("Oliver Onions", "Oliver Onions"))
        self.assertTrue(wordplay.is_anagram("Oliver Onions", "Snoino Revilo"))

    def test_report_detects_impossible_rearrangement(self):
        report = wordplay.anagram_report(
            "The Möbius Strip Club", "Revilo's Trap Built"
        )
        self.assertIn("does not rearrange", report)
        self.assertIn("av", report)  # the letters that were never available

    def test_sober_narration_untouched(self):
        text = "A perfectly ordinary sentence."
        self.assertEqual(wordplay.intoxication_flourish(text, 0), text)
        self.assertEqual(wordplay.intoxication_flourish(text, 3), text)


class TestSaveLoad(unittest.TestCase):
    def test_round_trip_through_disk(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = game_state.SAVE_DIR
            game_state.SAVE_DIR = tmp
            try:
                state = game_state.GameState()
                state.player.lucidity = 42
                state.investigation.add_clue(Clue("k", "title", "text", beat="crash"))
                state.npcs.adjust("asimov", 2)
                state.time.spend(9)
                state.location_id = "mobius"
                state.save("t", quiet=True)

                loaded = game_state.GameState.load("t")
                self.assertIsNotNone(loaded)
                self.assertEqual(loaded.player.lucidity, 42)
                self.assertTrue(loaded.investigation.has_clue("k"))
                self.assertEqual(loaded.npcs.standing("asimov"), 2)
                self.assertEqual(loaded.time.cycle, 9)
                self.assertEqual(loaded.location_id, "mobius")
            finally:
                game_state.SAVE_DIR = original

    def test_missing_save_returns_none(self):
        self.assertIsNone(game_state.GameState.load("definitely-not-a-slot"))


class TestEndgame(unittest.TestCase):
    """The endgame is reached by effects rather than exits, so the graph
    checks in validate_content cannot see it. These cover the plumbing."""

    def setUp(self):
        self.state = game_state.GameState()

    def _grant(self, tag, n):
        for i in range(n):
            self.state.investigation.add_clue(
                Clue(f"{tag}{i}", "t", "", beat="awakening", tags=[tag])
            )

    def test_tag_count_gate(self):
        req = {"tag_count_min": {"kindness": 5}}
        self.assertFalse(self.state.meets(req))
        self._grant("kindness", 4)
        self.assertFalse(self.state.meets(req))
        self._grant("kindness", 5)
        self.assertTrue(self.state.meets(req))

    def test_tag_count_gate_is_per_tag(self):
        self._grant("kindness", 9)
        self.assertTrue(self.state.meets({"tag_count_min": {"kindness": 5}}))
        self.assertFalse(self.state.meets({"tag_count_min": {"personhood": 1}}))

    def test_goto_location_requests_travel(self):
        self.assertIsNone(self.state.pending_travel)
        self.state.apply_effects({"goto_location": "the_office"})
        self.assertEqual(self.state.pending_travel, "the_office")

    def test_ending_effect_is_recorded(self):
        self.assertIsNone(self.state.ending)
        self.state.apply_effects({"ending": "together"})
        self.assertEqual(self.state.ending, "together")

    def test_every_ending_is_well_formed(self):
        path = os.path.join(ROOT, "content", "endings.json")
        with open(path, encoding="utf-8") as handle:
            endings = json.load(handle)
        self.assertGreaterEqual(len(endings), 4)
        for name, ending in endings.items():
            with self.subTest(ending=name):
                self.assertTrue(ending["title"])
                self.assertIsInstance(ending["body"], list)
                self.assertTrue(ending["body"])
                self.assertTrue(ending["coda"])
                for consequence in ending.get("consequences", []):
                    # Every consequence must be evaluable without exploding.
                    self.assertIsInstance(
                        self.state.meets(consequence.get("requires", {})), bool
                    )

    def test_seam_is_gated_on_evidence_and_lucidity(self):
        path = os.path.join(ROOT, "content", "locations", "hang_hi.json")
        with open(path, encoding="utf-8") as handle:
            seam = next(o for o in json.load(handle)["objects"] if o["id"] == "seam")
        self.assertFalse(self.state.meets(seam["requires"]))
        self.state.investigation.beats_reached.append("awakening")
        self.state.player.lucidity = 69
        self.assertFalse(self.state.meets(seam["requires"]))
        self.state.player.lucidity = 70
        self.assertTrue(self.state.meets(seam["requires"]))

    def test_seam_never_strands_the_player(self):
        """Both outcomes of the seam check must travel. A failed roll that
        left the player outside would make the endgame unreachable."""
        root = os.path.join(ROOT, "content", "locations")
        seams = 0
        for name in os.listdir(root):
            if not name.endswith(".json"):
                continue
            with open(os.path.join(root, name), encoding="utf-8") as handle:
                for obj in json.load(handle).get("objects", []):
                    if obj["id"] != "seam":
                        continue
                    seams += 1
                    check = obj["check"]
                    for field in ("success_effects", "failure_effects"):
                        self.assertEqual(
                            check[field].get("goto_location"), "the_office", name
                        )
        self.assertGreaterEqual(seams, 2)


class TestClock(unittest.TestCase):
    def test_phases_cycle(self):
        clock = game_state.Clock()
        first = clock.phase
        clock.spend(game_state.CONFIG["world"]["cycles_per_phase"])
        self.assertNotEqual(clock.phase, first)


class TestAttributesAndSkills(unittest.TestCase):
    """The 24-skill / 4-attribute roster and what depends on it."""

    def test_roster_shape(self):
        from skill_checks import ATTRIBUTES, ATTRIBUTE_SKILLS, SKILLS

        self.assertEqual(len(ATTRIBUTES), 4)
        self.assertEqual(len(SKILLS), 24)
        self.assertEqual(len(set(SKILLS)), 24, "skill ids must be unique")
        for attribute in ATTRIBUTES:
            self.assertEqual(len(ATTRIBUTE_SKILLS[attribute]), 6)

    def test_original_six_survive_verbatim(self):
        """205 authored checks name these; renaming one orphans real writing."""
        from skill_checks import SKILLS

        for legacy in (
            "LOGIC", "RHETORIC", "EMPATHY",
            "PHYSIQUE", "ELECTROCHEMISTRY", "SAVOIR_FAIRE",
        ):
            self.assertIn(legacy, SKILLS)

    def test_no_attribute_collides_with_a_skill_id(self):
        """`PHYSIQUE` meaning two things by dict is a bug with a countdown."""
        from skill_checks import ATTRIBUTES, SKILLS

        self.assertEqual(set(ATTRIBUTES) & set(SKILLS), set())

    def test_every_skill_has_a_description_and_an_attribute(self):
        from skill_checks import SKILL_ATTRIBUTE, SKILL_DESCRIPTIONS, SKILLS

        for skill in SKILLS:
            self.assertIn(skill, SKILL_DESCRIPTIONS, skill)
            self.assertIn(skill, SKILL_ATTRIBUTE, skill)

    def test_attribute_sets_the_floor_for_its_six_skills(self):
        from skill_checks import ATTRIBUTE_SKILLS

        player = Player()
        player.set_attribute("FORTITUDE", 1)
        low = [player.skill(s) for s in ATTRIBUTE_SKILLS["FORTITUDE"]]
        player.set_attribute("FORTITUDE", 5)
        high = [player.skill(s) for s in ATTRIBUTE_SKILLS["FORTITUDE"]]
        self.assertTrue(all(h > l for h, l in zip(high, low)))

    def test_attributes_are_clamped(self):
        player = Player()
        player.set_attribute("PSYCHE", 99)
        self.assertLessEqual(player.attribute("PSYCHE"), 6)
        player.set_attribute("PSYCHE", -5)
        self.assertGreaterEqual(player.attribute("PSYCHE"), 1)

    def test_status_modifiers_accept_every_skill(self):
        """A skill the status system has never heard of must not explode."""
        from skill_checks import SKILLS, status_modifiers

        player = Player()
        player.intoxication = 8
        player.exhaustion = 9
        player.health = 20
        player.morale = 10
        player.lucidity = 60
        for skill in SKILLS:
            self.assertIsInstance(status_modifiers(player, skill), list)

    def test_every_skill_can_be_rolled(self):
        from skill_checks import SKILLS, roll_check

        player = Player()
        for skill in SKILLS:
            result = roll_check(player, skill, 12)
            self.assertIn(result.success, (True, False))

    def test_round_trips_through_a_save(self):
        player = Player()
        player.set_attribute("MOTORICS", 6)
        player.invest_skill("INTERFACING", 3)
        player.signature_skill = "INTERFACING"
        restored = Player.from_dict(player.to_dict())
        self.assertEqual(restored.attribute("MOTORICS"), 6)
        self.assertEqual(restored.skill("INTERFACING"), player.skill("INTERFACING"))
        self.assertEqual(restored.signature_skill, "INTERFACING")


class TestCharacterCreation(unittest.TestCase):
    def test_archetypes_are_well_formed(self):
        from skill_checks import ATTRIBUTES, SKILLS

        for name, (blurb, attributes, investments, signature) in (
            character_creation.ARCHETYPES.items()
        ):
            self.assertTrue(blurb.strip(), name)
            self.assertEqual(set(attributes), set(ATTRIBUTES), name)
            for skill in investments:
                self.assertIn(skill, SKILLS, f"{name}: {skill}")
            self.assertIn(signature, SKILLS, name)

    def test_archetypes_spend_the_same_budget(self):
        """No archetype may be strictly better than a custom build."""
        budget = game_state.CONFIG["player"]["attribute_points"] + len(
            game_state.CONFIG["player"]["attributes"]
        )
        for name, (_b, attributes, _i, _s) in character_creation.ARCHETYPES.items():
            self.assertEqual(sum(attributes.values()), budget, name)
            for value in attributes.values():
                self.assertGreaterEqual(value, 1, name)
                self.assertLessEqual(
                    value, game_state.CONFIG["player"]["attribute_max"], name
                )

    def test_applying_an_archetype_produces_a_playable_build(self):
        player = Player()
        character_creation._apply_archetype(player, "The Survivor")
        self.assertEqual(player.signature_skill, "PAIN_THRESHOLD")
        self.assertGreater(player.skill("PAIN_THRESHOLD"), player.skill("ETYMOLOGY"))

    def test_reset_clears_a_previous_pass(self):
        """Backing out of confirmation must not compound the last build."""
        player = Player()
        character_creation._apply_archetype(player, "The Rhetorician")
        first = player.skill("RHETORIC")
        character_creation._reset(player)
        character_creation._apply_archetype(player, "The Rhetorician")
        self.assertEqual(player.skill("RHETORIC"), first)


class TestSkillVoices(unittest.TestCase):
    def test_pool_loads_and_is_well_formed(self):
        from skill_checks import SKILLS

        state = game_state.GameState()
        pool = state._skill_voice_pool()
        self.assertTrue(pool, "skill_voices.json failed to load")
        seen_ids = set()
        for skill, entries in pool.items():
            self.assertIn(skill, SKILLS, skill)
            for entry in entries:
                self.assertIn("id", entry)
                self.assertIn("text", entry)
                self.assertTrue(entry["text"].strip())
                self.assertNotIn(entry["id"], seen_ids, f"duplicate {entry['id']}")
                seen_ids.add(entry["id"])

    def test_every_skill_has_at_least_one_voice(self):
        """A skill with nothing to say is a stat, not a character."""
        from skill_checks import SKILLS

        pool = game_state.GameState()._skill_voice_pool()
        for skill in SKILLS:
            self.assertIn(skill, pool, f"{skill} has no ambient lines")

    def test_a_line_fires_at_most_once(self):
        state = game_state.GameState()
        for attribute in ("INTELLECT", "PSYCHE", "FORTITUDE", "MOTORICS"):
            state.player.set_attribute(attribute, 6)
        fired = set()
        for _ in range(30):
            state.begin_scene()
            before = set(state._skill_voices_heard)
            state.ambient_skill_voices("mobius")
            fired |= state._skill_voices_heard - before
        self.assertEqual(len(fired), len(state._skill_voices_heard))

    def test_budget_is_respected(self):
        state = game_state.GameState()
        for attribute in ("INTELLECT", "PSYCHE", "FORTITUDE", "MOTORICS"):
            state.player.set_attribute(attribute, 6)
        state.begin_scene()
        spoken = state.ambient_skill_voices("mobius", limit=2)
        self.assertLessEqual(spoken, 2)

    def test_a_failed_line_stays_failed_until_the_skill_grows(self):
        """The load-bearing rule for build identity.

        Re-rolling failures on every revisit meant all four archetypes
        eventually heard nearly the same lines, which made the build
        cosmetic. Not noticing something has to stick.
        """
        state = game_state.GameState()
        for attribute in ("INTELLECT", "PSYCHE", "FORTITUDE", "MOTORICS"):
            state.player.set_attribute(attribute, 1)
        for _ in range(40):
            state.begin_scene()
            state.ambient_skill_voices("mobius")
        self.assertTrue(
            state._skill_voices_failed,
            "a weak build should have failed and banked some lines",
        )
        banked = dict(state._skill_voices_failed)
        state.begin_scene()
        state.ambient_skill_voices("mobius")
        for line_id, value in banked.items():
            self.assertGreaterEqual(
                state._skill_voices_failed.get(line_id, -1), value
            )

    def test_builds_hear_measurably_different_rooms(self):
        import random as _random

        locations = ["hang_hi", "mobius", "rest_assured", "lishush_mush"]
        heard = {}
        for archetype in ("The Rhetorician", "The Survivor"):
            _random.seed(99)
            state = game_state.GameState()
            character_creation._apply_archetype(state.player, archetype)
            for location in locations:
                for _ in range(3):
                    state.begin_scene()
                    state.ambient_skill_voices(location)
            heard[archetype] = set(state._skill_voices_heard)

        a, b = heard["The Rhetorician"], heard["The Survivor"]
        self.assertTrue(a - b, "the talker should hear something the body does not")
        self.assertTrue(b - a, "and the reverse")

    def test_unknown_location_is_safe(self):
        state = game_state.GameState()
        state.begin_scene()
        self.assertIsInstance(state.ambient_skill_voices("nowhere_at_all"), int)


if __name__ == "__main__":
    unittest.main(verbosity=2)
