"""Configuration loading.

Reads config.yaml when PyYAML is present, otherwise falls back to an
embedded copy of the same defaults. The game must never fail to start
because of a missing optional dependency.
"""

from __future__ import annotations

import copy
import os
from typing import Any

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")

# Mirror of config.yaml. Kept in sync by tools/check_config.py.
DEFAULTS: dict[str, Any] = {
    "display": {
        "wrap_width": 78,
        "color": "auto",
        "command_bar": "auto",
        "crawl_speed": 0.0,
        "paragraph_gap": 1,
    },
    "difficulty": {
        "dc_offset": 0,
        "critical_success": 12,
        "critical_failure": 2,
        "allow_white_retry": True,
        "retry_after_failures": 2,
    },
    "narrative": {
        "default_density": 6,
        "auto_scale": True,
        "max_thoughts_per_scene": 3,
        "max_passives_per_scene": 4,
        "thought_slots": 2,
        "silent_passive_failure": True,
    },
    "player": {
        # Fallback build, used when character creation is skipped (--no-intro,
        # the fuzzer, the test suite). Character creation overwrites all of it.
        # Oliver-as-written: a talker with a neglected body.
        "attributes": {
            "INTELLECT": 4,
            "PSYCHE": 3,
            "FORTITUDE": 2,
            "MOTORICS": 3,
        },
        # Points the player distributes at creation.
        "attribute_points": 8,   # on top of 1 in each, for 12 total
        "attribute_max": 6,
        "skill_points": 4,       # individual +1s, on top of attribute floors
        "signature_bonus": 2,
        "morale": 70,
        "health": 80,
        "intoxication": 0,
        "lucidity": 0,
    },
    "world": {
        "cycles_per_phase": 6,
        "autosave_every_cycles": 5,
        "lucidity_stages": [0, 20, 45, 70, 90],
        "lucidity_approach": 250,
    },
    "features": {
        "furthermore": True,
        "passive_checks": True,
        "wordplay": True,
        "ambient_lines": True,
        "autosave": True,
        "show_dice": True,
        "debug": False,
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Overlay `override` onto `base` without dropping unspecified keys.

    This lets config.yaml specify only the values a player wants to change.
    """
    out = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def load_config(path: str = CONFIG_PATH) -> dict[str, Any]:
    """Return the merged configuration dictionary."""
    try:
        import yaml  # type: ignore
    except ImportError:
        return copy.deepcopy(DEFAULTS)

    try:
        with open(path, "r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle) or {}
    except (OSError, Exception):  # malformed YAML should not be fatal
        return copy.deepcopy(DEFAULTS)

    if not isinstance(loaded, dict):
        return copy.deepcopy(DEFAULTS)
    return _deep_merge(DEFAULTS, loaded)


CONFIG = load_config()
