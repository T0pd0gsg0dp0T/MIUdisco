#!/usr/bin/env python3
"""Structural validation of the content files.

This catches the class of bug that a text game is worst at surfacing: a
dangling `goto`, an unreachable node, a skill name typo that only fires on
a rare branch, a clue that counts toward a beat that does not exist, or a
beat whose threshold cannot be met by the clues that actually exist.

That last check is the important one. A beat needing 3 clues when only 2
are authored is an unwinnable game, and no amount of playtesting the
happy path will find it.

Usage:  python3 tools/validate_content.py
Exit code 1 on any error.
"""

from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from investigation import BEATS_BY_ID  # noqa: E402
from skill_checks import SKILLS  # noqa: E402

CONTENT = os.path.join(ROOT, "content")
LOCATIONS = os.path.join(CONTENT, "locations")
DIALOGUE = os.path.join(CONTENT, "dialogue")

errors: list[str] = []
warnings: list[str] = []


def load(path: str):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def collect_checks(node, where: str) -> None:
    """Validate every skill name and DC found anywhere in a structure."""
    if isinstance(node, dict):
        skill = node.get("skill")
        if skill is not None and "dc" in node:
            if skill not in SKILLS:
                errors.append(f"{where}: unknown skill '{skill}'")
            dc = node.get("dc")
            # 2d6 + skill (skills run ~1-8): above 16 is unreachable even
            # for a signature specialist, below 6 is a formality.
            if not isinstance(dc, int) or not 6 <= dc <= 16:
                errors.append(f"{where}: implausible DC {dc!r} for {skill}")
            kind = node.get("kind", "white")
            if kind not in ("white", "red"):
                errors.append(f"{where}: unknown check kind '{kind}'")
        for key, value in node.items():
            collect_checks(value, f"{where}.{key}")
    elif isinstance(node, list):
        for index, item in enumerate(node):
            collect_checks(item, f"{where}[{index}]")


def collect_clues(node, where: str, out: dict) -> None:
    """Gather every clue definition and check its beat is real.

    `requires` blocks also carry a "clue" key, but there it holds ids rather
    than definitions, so those subtrees are skipped.
    """
    if isinstance(node, dict):
        if "clue" in node and isinstance(node.get("clue"), (dict, list)):
            specs = node["clue"]
            if isinstance(specs, dict):
                specs = [specs]
            for spec in specs:
                if not isinstance(spec, dict) or "id" not in spec:
                    errors.append(f"{where}: malformed clue spec")
                    continue
                beat = spec.get("beat")
                if beat is not None and beat not in BEATS_BY_ID:
                    errors.append(f"{where}: clue '{spec['id']}' -> unknown beat '{beat}'")
                if spec["id"] in out and out[spec["id"]] != beat:
                    errors.append(
                        f"clue '{spec['id']}' defined twice with different beats"
                    )
                out[spec["id"]] = beat
        for key, value in node.items():
            if key == "requires":
                continue
            collect_clues(value, f"{where}.{key}", out)
    elif isinstance(node, list):
        for index, item in enumerate(node):
            collect_clues(item, f"{where}[{index}]", out)


def collect_requires(node, where: str, out: list) -> None:
    """Gather every clue id referenced by a condition block."""
    if isinstance(node, dict):
        req = node.get("requires")
        if isinstance(req, dict):
            for key in ("clue", "not_clue"):
                value = req.get(key)
                if value is None:
                    continue
                for clue_id in value if isinstance(value, list) else [value]:
                    out.append((clue_id, where))
        for key, value in node.items():
            collect_requires(value, f"{where}.{key}", out)
    elif isinstance(node, list):
        for index, item in enumerate(node):
            collect_requires(item, f"{where}[{index}]", out)


def collect_bonus_clues(node, where: str, out: list) -> None:
    if isinstance(node, dict):
        for key in ("bonus_if_clue",):
            mapping = node.get(key)
            if isinstance(mapping, dict):
                for clue_id in mapping:
                    out.append((clue_id, where))
        for key, value in node.items():
            collect_bonus_clues(value, f"{where}.{key}", out)
    elif isinstance(node, list):
        for index, item in enumerate(node):
            collect_bonus_clues(item, f"{where}[{index}]", out)


def main() -> int:
    all_clues: dict[str, str | None] = {}
    required_clues: list[tuple[str, str]] = []
    location_ids: set[str] = set()

    # --- locations ---------------------------------------------------------
    for name in sorted(os.listdir(LOCATIONS)):
        if not name.endswith(".json"):
            continue
        path = os.path.join(LOCATIONS, name)
        data = load(path)
        loc_id = data.get("id", name[:-5])
        location_ids.add(loc_id)
        if loc_id != name[:-5]:
            errors.append(f"{name}: id '{loc_id}' does not match filename")

        seen_objects: set[str] = set()
        for obj in data.get("objects", []):
            if obj["id"] in seen_objects:
                errors.append(f"{loc_id}: duplicate object id '{obj['id']}'")
            seen_objects.add(obj["id"])
            if not obj.get("description"):
                errors.append(f"{loc_id}.{obj['id']}: no description")
            check = obj.get("check")
            if check:
                # An object check must narrate both outcomes.
                for field in ("success", "failure"):
                    if not check.get(field):
                        errors.append(
                            f"{loc_id}.{obj['id']}: check has no '{field}' text — "
                            f"failure must never be a dead end"
                        )

        collect_checks(data, loc_id)
        collect_clues(data, loc_id, all_clues)
        collect_requires(data, loc_id, required_clues)
        collect_bonus_clues(data, loc_id, required_clues)

    # Exits must point at real locations, in both directions where sensible.
    for name in sorted(os.listdir(LOCATIONS)):
        if not name.endswith(".json"):
            continue
        data = load(os.path.join(LOCATIONS, name))
        loc_id = data.get("id", name[:-5])
        for target in data.get("exits", {}):
            if target not in location_ids:
                errors.append(f"{loc_id}: exit to unknown location '{target}'")
            else:
                back = load(os.path.join(LOCATIONS, f"{target}.json")).get("exits", {})
                if loc_id not in back:
                    warnings.append(f"{loc_id} -> {target} is one-way")

    # --- npcs and dialogue -------------------------------------------------
    npcs = load(os.path.join(CONTENT, "npcs.json"))
    npc_ids = {npc["id"] for npc in npcs}
    for npc in npcs:
        if npc.get("location") not in location_ids:
            errors.append(f"npc '{npc['id']}': location '{npc.get('location')}' unknown")
        filename = npc.get("dialogue_file", f"{npc['id']}.json")
        path = os.path.join(DIALOGUE, filename)
        if not os.path.exists(path):
            errors.append(f"npc '{npc['id']}': missing dialogue file {filename}")
            continue

        tree = load(path)
        nodes = tree.get("nodes", {})
        entry = npc.get("entry_node", "root")
        if entry not in nodes:
            errors.append(f"{filename}: entry node '{entry}' missing")

        # Dangling gotos, and reachability from the entry node.
        reachable = {entry}
        frontier = [entry]
        while frontier:
            current = frontier.pop()
            node = nodes.get(current)
            if node is None:
                continue
            for option in node.get("options", []):
                targets = [option.get("goto")]
                check = option.get("check")
                if check:
                    targets += [check.get("success"), check.get("failure")]
                    for field in ("success_text", "failure_text"):
                        if not check.get(field):
                            errors.append(
                                f"{filename}.{current}: check missing '{field}' — "
                                f"failure must narrate, not stall"
                            )
                for target in targets:
                    if target in (None, "__exit__"):
                        continue
                    if target not in nodes:
                        errors.append(
                            f"{filename}.{current}: goto '{target}' does not exist"
                        )
                    elif target not in reachable:
                        reachable.add(target)
                        frontier.append(target)

        for node_id in nodes:
            if node_id not in reachable:
                warnings.append(f"{filename}: node '{node_id}' is unreachable")
            options = nodes[node_id].get("options")
            if not options:
                warnings.append(f"{filename}: node '{node_id}' has no options")
                continue
            # Every option that carries a check can become unavailable once
            # that check is spent; every option with `requires` or `once` can
            # vanish. A node with nothing else offers no way out on its own.
            # The engine injects an escape at runtime, but the author should
            # know they are relying on it.
            unconditional = [
                option
                for option in options
                if not option.get("requires")
                and not option.get("check")
                and not option.get("once")
            ]
            if not unconditional:
                warnings.append(
                    f"{filename}: node '{node_id}' has no unconditional option — "
                    f"relies on the engine's injected escape"
                )

        collect_checks(tree, filename)
        collect_clues(tree, filename, all_clues)
        collect_requires(tree, filename, required_clues)
        collect_bonus_clues(tree, filename, required_clues)

        for option in (n for node in nodes.values() for n in node.get("options", [])):
            for npc_id in (option.get("effects", {}).get("relationship") or {}):
                if npc_id not in npc_ids:
                    errors.append(f"{filename}: relationship to unknown npc '{npc_id}'")

    # --- thoughts ----------------------------------------------------------
    thoughts = load(os.path.join(CONTENT, "thoughts", "thoughts.json"))
    thought_ids = {t["id"] for t in thoughts}
    for thought in thoughts:
        for skill in (thought.get("effects", {}).get("skills") or {}):
            if skill not in SKILLS:
                errors.append(f"thought '{thought['id']}': unknown skill '{skill}'")

    # Every thought offered by content must exist.
    def find_thought_refs(node, where):
        if isinstance(node, dict):
            ref = node.get("thought")
            if isinstance(ref, str) and ref not in thought_ids:
                errors.append(f"{where}: offers unknown thought '{ref}'")
            for key, value in node.items():
                find_thought_refs(value, f"{where}.{key}")
        elif isinstance(node, list):
            for item in node:
                find_thought_refs(item, where)

    for directory in (LOCATIONS, DIALOGUE):
        for name in sorted(os.listdir(directory)):
            if name.endswith(".json"):
                find_thought_refs(load(os.path.join(directory, name)), name)

    # --- endgame -----------------------------------------------------------
    # The endgame is the part most likely to break silently: it is reached by
    # effects rather than by exits, so none of the graph checks above touch it.
    endings = load(os.path.join(CONTENT, "endings.json"))
    referenced_endings: set[str] = set()
    referenced_travel: set[str] = set()

    def find_endgame_refs(node, where):
        if isinstance(node, dict):
            if isinstance(node.get("ending"), str):
                referenced_endings.add(node["ending"])
            if isinstance(node.get("goto_location"), str):
                referenced_travel.add(node["goto_location"])
            for key, value in node.items():
                find_endgame_refs(value, f"{where}.{key}")
        elif isinstance(node, list):
            for item in node:
                find_endgame_refs(item, where)

    for directory in (LOCATIONS, DIALOGUE):
        for name in sorted(os.listdir(directory)):
            if name.endswith(".json"):
                find_endgame_refs(load(os.path.join(directory, name)), name)

    for ending_id in sorted(referenced_endings):
        if ending_id not in endings:
            errors.append(f"content references ending '{ending_id}' that endings.json lacks")
    for ending_id, ending in endings.items():
        if ending_id not in referenced_endings:
            errors.append(
                f"ending '{ending_id}' exists but nothing in the game can reach it"
            )
        for field in ("title", "body", "coda"):
            if not ending.get(field):
                errors.append(f"ending '{ending_id}': missing '{field}'")
        if not isinstance(ending.get("body"), list):
            errors.append(f"ending '{ending_id}': 'body' must be a list of paragraphs")
        for index, consequence in enumerate(ending.get("consequences", [])):
            if not consequence.get("text"):
                errors.append(f"ending '{ending_id}'.consequences[{index}]: no text")

    for loc_id in sorted(referenced_travel):
        if loc_id not in location_ids:
            errors.append(f"goto_location points at unknown location '{loc_id}'")

    # A location with no exits is a dead end unless something travels into it.
    for name in sorted(os.listdir(LOCATIONS)):
        if not name.endswith(".json"):
            continue
        data = load(os.path.join(LOCATIONS, name))
        loc_id = data.get("id", name[:-5])
        if not data.get("exits"):
            if loc_id not in referenced_travel:
                errors.append(
                    f"{loc_id}: no exits and nothing travels into it — unreachable"
                )
            else:
                warnings.append(
                    f"{loc_id}: no exits (reached by goto_location; one-way by design)"
                )

    # --- beat solvability --------------------------------------------------
    # The check that prevents an unwinnable game.
    beat_counts: dict[str, int] = {}
    for beat in all_clues.values():
        if beat:
            beat_counts[beat] = beat_counts.get(beat, 0) + 1

    for beat_id, beat in BEATS_BY_ID.items():
        available = beat_counts.get(beat_id, 0)
        needed = beat["threshold"]
        if available < needed:
            errors.append(
                f"BEAT '{beat_id}' needs {needed} clues but only {available} "
                f"exist in content — this beat can never fire"
            )
        elif available == needed:
            warnings.append(
                f"beat '{beat_id}': exactly {needed} clues exist for a "
                f"threshold of {needed} — only one route through it"
            )

    # --- dangling references ----------------------------------------------
    for clue_id, where in required_clues:
        if clue_id not in all_clues:
            errors.append(f"{where}: references clue '{clue_id}' that nothing grants")

    # --- report ------------------------------------------------------------
    for warning in warnings:
        print(f"warn: {warning}")
    for error in errors:
        print(f"FAIL: {error}")

    print(
        f"\nvalidate_content: {len(all_clues)} clues, {len(npc_ids)} npcs, "
        f"{len(location_ids)} locations, {len(thought_ids)} thoughts."
    )
    print("beat coverage: " + ", ".join(
        f"{bid} {beat_counts.get(bid, 0)}/{b['threshold']}"
        for bid, b in BEATS_BY_ID.items()
    ))
    print(f"{len(errors)} error(s), {len(warnings)} warning(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
