"""Location and interactive-object loading.

Locations are data, not code: each lives in content/locations/<id>.json and
is lazy-loaded on first entry, then cached. Twelve locations of dense prose
is a few hundred kilobytes, which is nothing, but lazy loading keeps the
start-up instant and means a content error in a location you never visit
cannot stop the game booting.

An object's text can vary along three independent axes without the author
writing a branch for each combination:

  * narrative density  - via density-keyed dicts (see narrative_density.py)
  * lucidity stage     - via `lucid` variants, keyed by stage number
  * visit count        - via `repeat`, shown from the second examination on

That is the machinery behind "returning to locations reveals new details".
The world does not change state on a script; it changes state because
Oliver has.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

CONTENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content")
LOCATIONS_DIR = os.path.join(CONTENT_DIR, "locations")


@dataclass
class InteractiveObject:
    """A thing in a room that rewards attention."""

    id: str
    name: str
    aliases: list[str] = field(default_factory=list)
    description: object = ""          # str or density-keyed dict
    repeat: object = ""               # shown on re-examination
    # Stage-keyed overrides: {"2": "...", "4": "..."} - highest stage <= current wins.
    lucid: dict = field(default_factory=dict)
    # What the gold monocle reveals. Absent means the monocle adds nothing,
    # which is itself information.
    monocle: object = ""
    # Passive checks rolled silently on examination.
    passive: list = field(default_factory=list)
    # An optional active check the player may attempt.
    check: dict = field(default_factory=dict)
    # Effects applied the first time this object is examined.
    effects: dict = field(default_factory=dict)
    requires: dict = field(default_factory=dict)
    # Hidden objects only appear in the room listing once revealed by a flag.
    hidden: bool = False

    def matches(self, text: str) -> bool:
        text = text.strip().lower()
        if not text:
            return False
        candidates = [self.id, self.name] + self.aliases
        for candidate in candidates:
            candidate = candidate.lower()
            if text == candidate or text in candidate.split():
                return True
        # Allow partial matches on the display name so "spray-painted snake"
        # finds "the spray-painted snake" without exact typing.
        return text in self.name.lower()


@dataclass
class Location:
    id: str
    name: str
    subtitle: str = ""
    description: object = ""
    lucid: dict = field(default_factory=dict)
    revisit: object = ""
    ambient: list = field(default_factory=list)
    objects: list[InteractiveObject] = field(default_factory=list)
    exits: dict = field(default_factory=dict)
    # Effects applied on first arrival.
    on_enter: dict = field(default_factory=dict)
    requires: dict = field(default_factory=dict)

    def find_object(self, text: str) -> InteractiveObject | None:
        for obj in self.objects:
            if obj.matches(text):
                return obj
        return None


def _stage_variant(variants: dict, stage: int) -> str:
    """Pick the highest-numbered variant not above the current stage."""
    if not variants:
        return ""
    applicable = [int(k) for k in variants if str(k).lstrip("-").isdigit() and int(k) <= stage]
    if not applicable:
        return ""
    return variants[str(max(applicable))]


class LocationRegistry:
    """Lazy-loading store for locations."""

    def __init__(self) -> None:
        self._cache: dict[str, Location] = {}
        self._index: dict[str, str] = {}   # id -> display name, cheap to build
        self._build_index()

    def _build_index(self) -> None:
        if not os.path.isdir(LOCATIONS_DIR):
            return
        for filename in sorted(os.listdir(LOCATIONS_DIR)):
            if not filename.endswith(".json"):
                continue
            location_id = filename[:-5]
            # Read just enough to get the name without parsing the whole file
            # into objects. The files are small; a full json.load is fine and
            # far simpler than a partial parse.
            try:
                with open(
                    os.path.join(LOCATIONS_DIR, filename), "r", encoding="utf-8"
                ) as handle:
                    data = json.load(handle)
                self._index[location_id] = data.get("name", location_id)
            except (OSError, ValueError):
                continue

    @property
    def ids(self) -> list[str]:
        return list(self._index)

    def display_name(self, location_id: str) -> str:
        return self._index.get(location_id, location_id)

    def get(self, location_id: str) -> Location | None:
        if location_id in self._cache:
            return self._cache[location_id]
        path = os.path.join(LOCATIONS_DIR, f"{location_id}.json")
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, ValueError):
            return None

        objects = [
            InteractiveObject(
                id=entry["id"],
                name=entry.get("name", entry["id"]),
                aliases=entry.get("aliases", []),
                description=entry.get("description", ""),
                repeat=entry.get("repeat", ""),
                lucid=entry.get("lucid", {}),
                monocle=entry.get("monocle", ""),
                passive=entry.get("passive", []),
                check=entry.get("check", {}),
                effects=entry.get("effects", {}),
                requires=entry.get("requires", {}),
                hidden=entry.get("hidden", False),
            )
            for entry in data.get("objects", [])
        ]

        location = Location(
            id=data.get("id", location_id),
            name=data.get("name", location_id),
            subtitle=data.get("subtitle", ""),
            description=data.get("description", ""),
            lucid=data.get("lucid", {}),
            revisit=data.get("revisit", ""),
            ambient=data.get("ambient", []),
            objects=objects,
            exits=data.get("exits", {}),
            on_enter=data.get("on_enter", {}),
            requires=data.get("requires", {}),
        )
        self._cache[location_id] = location
        return location

    # --- text resolution ---------------------------------------------------

    @staticmethod
    def describe_location(location: Location, density, stage: int, visits: int) -> str:
        """Assemble the room description for the current conditions."""
        parts: list[str] = []
        base = density.pick(location.description)
        if visits > 1 and location.revisit:
            base = density.pick(location.revisit)
        if base:
            parts.append(base)
        overlay = _stage_variant(location.lucid, stage)
        if overlay:
            parts.append(overlay)
        return "\n\n".join(parts)

    @staticmethod
    def describe_object(
        obj: InteractiveObject, density, stage: int, times_examined: int
    ) -> str:
        """Assemble an object description for the current conditions."""
        parts: list[str] = []
        if times_examined > 0 and obj.repeat:
            parts.append(density.pick(obj.repeat))
        else:
            parts.append(density.pick(obj.description))
        overlay = _stage_variant(obj.lucid, stage)
        if overlay:
            parts.append(overlay)
        return "\n\n".join(part for part in parts if part)
