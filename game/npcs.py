"""NPC definitions and relationship tracking.

Each NPC carries a `voice` block that is documentation for the writer and a
runtime aid for the dialogue engine: the speech quirk, the tell, and the
awareness level. Awareness is the lorebook's own axis - some characters
(Soliloquy, Asimov, Ginny, Revilo) know more about the nature of Silvora
Reefs than others (Bud, Luigi), and it determines both what they will
discuss and how much lucidity a conversation with them can move.

Relationship is a single integer from -3 to +3. It is not a romance meter.
It gates candour: at +2 people tell you things they would deny at 0, and at
-2 they start telling other people about you.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

CONTENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content")

# How much a character can be pushed toward acknowledging the manuscript.
# Ceiling on the lucidity a single conversation with them may grant.
AWARENESS_CEILING = {
    "denial": 0,      # Bud. Talking to him can actively cost you lucidity.
    "oblivious": 2,   # Luigi, Darek, Barney - carriers, not knowers.
    "intuitive": 5,   # Woolbinkle, Mary, Wino-T, Ben, T, Sir Jerry.
    "aware": 9,       # Asimov, Ginny, Soliloquy.
    "lucid": 15,      # Revilo. He knows exactly what he is.
}


@dataclass
class NPC:
    id: str
    name: str
    title: str
    location: str
    # What the player calls this person before learning who they are. The
    # game opens amnesiac, so every name in Silvora Reefs is something the
    # player earns rather than something the UI hands them.
    alias: str = ""
    alias_title: str = ""
    awareness: str = "oblivious"
    # Writer-facing voice notes, also printed by the `who` command so the
    # player can keep twelve eccentrics straight.
    quirk: str = ""
    appearance: str = ""
    colour: str = "cyan"
    # Greeting variants keyed by relationship band: "cold", "neutral", "warm".
    greetings: dict = field(default_factory=dict)
    # Node id in this NPC's dialogue file to enter on `talk`.
    entry_node: str = "root"
    dialogue_file: str = ""

    @property
    def ceiling(self) -> int:
        return AWARENESS_CEILING.get(self.awareness, 2)


class NPCRegistry:
    """Loads NPCs and tracks per-playthrough relationship and history."""

    def __init__(self) -> None:
        self.npcs: dict[str, NPC] = {}
        self.relationship: dict[str, int] = {}
        # npc_id -> list of dialogue node ids already delivered. Used to hide
        # exhausted options rather than letting players re-mine one line.
        self.history: dict[str, list[str]] = {}
        self.load()

    def load(self) -> None:
        path = os.path.join(CONTENT_DIR, "npcs.json")
        try:
            with open(path, "r", encoding="utf-8") as handle:
                entries = json.load(handle)
        except (OSError, ValueError):
            entries = []
        for entry in entries:
            npc = NPC(
                id=entry["id"],
                name=entry["name"],
                title=entry.get("title", ""),
                location=entry.get("location", ""),
                alias=entry.get("alias", ""),
                alias_title=entry.get("alias_title", ""),
                awareness=entry.get("awareness", "oblivious"),
                quirk=entry.get("quirk", ""),
                appearance=entry.get("appearance", ""),
                colour=entry.get("colour", "cyan"),
                greetings=entry.get("greetings", {}),
                entry_node=entry.get("entry_node", "root"),
                dialogue_file=entry.get("dialogue_file", f"{entry['id']}.json"),
            )
            self.npcs[npc.id] = npc
            self.relationship.setdefault(npc.id, 0)
            self.history.setdefault(npc.id, [])

    # --- access ------------------------------------------------------------

    def get(self, npc_id: str) -> NPC | None:
        return self.npcs.get(npc_id)

    def at_location(self, location_id: str) -> list[NPC]:
        return [npc for npc in self.npcs.values() if npc.location == location_id]

    # --- names -------------------------------------------------------------
    #
    # A name is information, and information in this game is earned. Until
    # you have actually spoken to someone, every surface that would print
    # their name - the bar, the `who` list, the speech header, the travel
    # menu - prints what you can actually see about them instead.

    def knows_name(self, npc_id: str) -> bool:
        return bool(self.history.get(npc_id))

    def display_name(self, npc_id: str) -> str:
        npc = self.npcs.get(npc_id)
        if npc is None:
            return "somebody"
        if self.knows_name(npc_id) or not npc.alias:
            return npc.name
        return npc.alias

    def display_title(self, npc_id: str) -> str:
        npc = self.npcs.get(npc_id)
        if npc is None:
            return ""
        if self.knows_name(npc_id) or not npc.alias_title:
            return npc.title
        return npc.alias_title

    # --- relationship ------------------------------------------------------

    def standing(self, npc_id: str) -> int:
        return self.relationship.get(npc_id, 0)

    def adjust(self, npc_id: str, amount: int) -> int:
        current = self.relationship.get(npc_id, 0)
        current = max(-3, min(3, current + amount))
        self.relationship[npc_id] = current
        return current

    def band(self, npc_id: str) -> str:
        value = self.standing(npc_id)
        if value <= -2:
            return "cold"
        if value >= 2:
            return "warm"
        return "neutral"

    def greeting(self, npc_id: str) -> str:
        npc = self.get(npc_id)
        if npc is None:
            return ""
        greetings = npc.greetings
        band = self.band(npc_id)
        return greetings.get(band) or greetings.get("neutral") or ""

    # --- history -----------------------------------------------------------

    def seen(self, npc_id: str, node_id: str) -> bool:
        return node_id in self.history.get(npc_id, [])

    def mark_seen(self, npc_id: str, node_id: str) -> None:
        self.history.setdefault(npc_id, [])
        if node_id not in self.history[npc_id]:
            self.history[npc_id].append(node_id)

    def has_spoken_to(self, npc_id: str) -> bool:
        return bool(self.history.get(npc_id))

    # --- persistence -------------------------------------------------------

    def to_dict(self) -> dict:
        return {"relationship": self.relationship, "history": self.history}

    def load_dict(self, data: dict) -> None:
        self.relationship.update(data.get("relationship", {}))
        self.history.update(data.get("history", {}))
