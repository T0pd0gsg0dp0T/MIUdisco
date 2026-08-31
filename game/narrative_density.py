"""Prose selection, locked to the fullest telling.

This used to be a 1-10 player-facing pacing dial. It is not any more: the
game is written at what that dial called density 1 - world-building,
texture, the long look, every object described in full and ambient lines
firing freely - and there is no way to ask for less.

The class survives because ~200 call sites read `state.density.pick(...)`,
and because content files still carry `{"low": ..., "high": ...}` variants
that were authored as genuinely different tellings rather than as
truncations. `pick()` now always resolves to the fullest one available.
The thinner variants are kept in the files rather than deleted: they are
real writing, they cost nothing to carry, and throwing them away would be
irreversible in a way that removing a menu entry is not.
"""

from __future__ import annotations

from config import CONFIG

LOW, MID, HIGH = "low", "mid", "high"


class NarrativeDensity:
    #: The single band the game renders at. LOW is the fullest telling.
    BAND = LOW

    def __init__(self, level: int | None = None) -> None:
        # `level` is accepted and ignored so that older saves, the fuzzer and
        # any stray caller constructing this with a number keep working.
        self.level = 1
        self.pinned = True

    @property
    def band(self) -> str:
        return self.BAND

    def set_level(self, level: int, pin: bool = True) -> None:
        """No-op. Kept so old saves and callers do not need special-casing."""

    def scale_to_progress(self, beat_index: int, total_beats: int) -> None:
        """No-op. The prose no longer tightens as the plot advances."""

    # --- content selection -------------------------------------------------

    def pick(self, passage) -> str:
        """Resolve a passage that may be a string or a band-keyed dict.

        Always prefers the fullest authored variant, then falls back through
        the thinner ones so a file that only supplied `high` still renders.
        """
        if passage is None:
            return ""
        if isinstance(passage, str):
            return passage
        if isinstance(passage, list):
            return "\n\n".join(str(part) for part in passage)
        if not isinstance(passage, dict):
            return str(passage)

        for key in (LOW, MID, HIGH):
            if passage.get(key):
                return passage[key]
        # A dict with no band keys is a content mistake; return whatever text
        # it does contain rather than nothing.
        for value in passage.values():
            if isinstance(value, str) and value:
                return value
        return ""

    # --- budgets -----------------------------------------------------------

    @property
    def show_ambient(self) -> bool:
        return bool(CONFIG["features"]["ambient_lines"])

    @property
    def ambient_chance(self) -> float:
        return 0.9 if self.show_ambient else 0.0

    @property
    def thought_budget(self) -> int:
        return CONFIG["narrative"]["max_thoughts_per_scene"]

    @property
    def passive_budget(self) -> int:
        """Max passive skill voices per scene.

        Raised from three now that the roster is twenty-four skills rather
        than six: with the old budget a wide build would be silently gagged,
        and the voices are the whole reason to have chosen those skills.
        """
        return CONFIG["narrative"]["max_passives_per_scene"]

    def describe(self) -> str:
        return "Narrative: full - every detail, the long look."

    # --- persistence -------------------------------------------------------

    def to_dict(self) -> dict:
        return {"level": self.level, "pinned": self.pinned}

    @classmethod
    def from_dict(cls, data: dict) -> "NarrativeDensity":
        return cls()
