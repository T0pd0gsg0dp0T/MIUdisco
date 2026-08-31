"""Clue accumulation and scene state.

The rule this module exists to enforce: **clues accumulate, they do not
gate.** No plot beat is behind a single mandatory clue. Beats advance on a
*threshold* of evidence, and multiple clues satisfy each threshold, so two
players can reach the same revelation having examined entirely different
things. Dead ends still hand out clues; they simply hand out clues that are
about the town rather than about the case, which is the point of a dead end
in a game where the town is the case.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field


@dataclass
class Clue:
    id: str
    title: str
    text: str
    # Which plot beat this clue counts toward. A clue may count toward none,
    # in which case it is atmosphere - still logged, still re-readable.
    beat: str | None = None
    # Free tags used by dialogue conditions and by Furthermore's hint logic.
    tags: list[str] = field(default_factory=list)
    # Where it came from, shown in the log so the player can retrace.
    source: str = ""
    # A red herring is a true observation that supports a false conclusion.
    # It is logged identically; only the beat accounting ignores it.
    herring: bool = False


# ---------------------------------------------------------------------------
# Plot beats.
#
# These follow the lorebook's actual shape rather than a generic conspiracy
# ladder. The surface story is a corporate one - a shadowy syndicate, a
# device, a countdown - and the player is meant to believe it, because Oliver
# believes it. The real story is that C.C.C.C. is Oliver's analytical mind,
# O.R.A.C.L.E. is not a device at all, and Snoino Revilo is Oliver looking
# back. The beats are therefore named for what Oliver thinks is happening,
# and reinterpreted underneath.
# ---------------------------------------------------------------------------

BEATS = [
    {
        "id": "crash",
        "name": "The Crash",
        "threshold": 3,
        "summary": "Something came down over Silvora Reefs. You were in it.",
    },
    {
        "id": "manuscript",
        "name": "The Sound of Typing",
        "threshold": 6,
        "summary": (
            "Typewriter keys where there is no typewriter. An office behind "
            "the mirrors. The town has a noise problem it will not discuss."
        ),
    },
    {
        "id": "quadc",
        "name": "The Coalition",
        "threshold": 6,
        "summary": (
            "Someone is filing paperwork about the impossible. Someone is "
            "very concerned that it be filed correctly."
        ),
    },
    {
        "id": "oracle",
        "name": "O.R.A.C.L.E.",
        "threshold": 8,
        "summary": (
            "A countdown to an activation, for a machine nobody can point to."
        ),
    },
    {
        "id": "revilo",
        "name": "The Man in the Warped Mirror",
        "threshold": 8,
        "summary": "Green with purple accents. Your cadence. Your vocabulary.",
    },
    {
        "id": "awakening",
        "name": "The Last Word",
        "threshold": 7,
        "summary": "The choice about which of you gets to keep the language.",
    },
]

BEATS_BY_ID = {beat["id"]: beat for beat in BEATS}


class Investigation:
    """Tracks clues, examined objects, visited locations, and beat progress."""

    def __init__(self) -> None:
        self.clues: dict[str, Clue] = {}
        self.clue_order: list[str] = []
        # object_id -> number of times examined; drives "you have been here"
        # variant text without any authored branching.
        self.examined: dict[str, int] = {}
        self.visited: dict[str, int] = {}
        self.beats_reached: list[str] = []
        # Arbitrary story flags set by dialogue and object outcomes.
        self.flags: dict[str, object] = {}

    # --- clues -------------------------------------------------------------

    def add_clue(self, clue: Clue) -> bool:
        """Log a clue. Returns False if it was already known."""
        if clue.id in self.clues:
            return False
        self.clues[clue.id] = clue
        self.clue_order.append(clue.id)
        return True

    def has_clue(self, clue_id: str) -> bool:
        return clue_id in self.clues

    def clues_for_beat(self, beat_id: str) -> list[Clue]:
        return [
            clue
            for clue in self.clues.values()
            if clue.beat == beat_id and not clue.herring
        ]

    def clues_with_tag(self, tag: str) -> list[Clue]:
        return [clue for clue in self.clues.values() if tag in clue.tags]

    # --- beats -------------------------------------------------------------

    def beat_progress(self, beat_id: str) -> tuple[int, int]:
        beat = BEATS_BY_ID[beat_id]
        return len(self.clues_for_beat(beat_id)), beat["threshold"]

    def check_beats(self) -> list[str]:
        """Return beats newly satisfied by the current evidence.

        Beats are checked in order but do not require their predecessors:
        an unusually thorough player who spends the whole game in Rest
        Assured can reach 'revilo' before 'quadc'. That is allowed. The
        narrative copes because each beat is written to stand alone.
        """
        newly: list[str] = []
        for beat in BEATS:
            if beat["id"] in self.beats_reached:
                continue
            found, needed = self.beat_progress(beat["id"])
            if found >= needed:
                self.beats_reached.append(beat["id"])
                newly.append(beat["id"])
        return newly

    @property
    def furthest_beat_index(self) -> int:
        if not self.beats_reached:
            return 0
        return max(
            next(i for i, b in enumerate(BEATS) if b["id"] == bid)
            for bid in self.beats_reached
        )

    # --- scene state -------------------------------------------------------

    def mark_examined(self, object_id: str) -> int:
        self.examined[object_id] = self.examined.get(object_id, 0) + 1
        return self.examined[object_id]

    def times_examined(self, object_id: str) -> int:
        return self.examined.get(object_id, 0)

    def mark_visited(self, location_id: str) -> int:
        self.visited[location_id] = self.visited.get(location_id, 0) + 1
        return self.visited[location_id]

    def times_visited(self, location_id: str) -> int:
        return self.visited.get(location_id, 0)

    # --- flags -------------------------------------------------------------

    def set_flag(self, key: str, value: object = True) -> None:
        self.flags[key] = value

    def flag(self, key: str, default: object = False) -> object:
        return self.flags.get(key, default)

    # --- retry token -------------------------------------------------------

    def state_token(self) -> str:
        """A fingerprint of everything that could justify retrying a check.

        White checks compare against this. Because it hashes the clue set,
        the flag set, and the beat list, "go and learn something, then come
        back" is enforced without the author having to hand-specify what the
        player must learn.
        """
        material = "|".join(
            [
                ",".join(sorted(self.clues)),
                ",".join(sorted(f"{k}={v}" for k, v in self.flags.items())),
                ",".join(sorted(self.beats_reached)),
            ]
        )
        return hashlib.sha1(material.encode("utf-8")).hexdigest()[:12]

    # --- persistence -------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "clues": [
                {
                    "id": c.id,
                    "title": c.title,
                    "text": c.text,
                    "beat": c.beat,
                    "tags": c.tags,
                    "source": c.source,
                    "herring": c.herring,
                }
                for c in (self.clues[cid] for cid in self.clue_order)
            ],
            "examined": self.examined,
            "visited": self.visited,
            "beats_reached": self.beats_reached,
            "flags": self.flags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Investigation":
        inv = cls()
        for entry in data.get("clues", []):
            clue = Clue(
                id=entry["id"],
                title=entry["title"],
                text=entry["text"],
                beat=entry.get("beat"),
                tags=entry.get("tags", []),
                source=entry.get("source", ""),
                herring=entry.get("herring", False),
            )
            inv.add_clue(clue)
        inv.examined = data.get("examined", {})
        inv.visited = data.get("visited", {})
        inv.beats_reached = data.get("beats_reached", [])
        inv.flags = data.get("flags", {})
        return inv
