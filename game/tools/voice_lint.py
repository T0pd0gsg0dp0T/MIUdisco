#!/usr/bin/env python3
"""Enforce the narration rules across every content file.

Two rules, both from the design brief, both mechanically checkable:

  1. Narration is second person. Content that slips into "I walk" or
     "Oliver walks" in a *narration* field is flagged.
  2. Narration never dictates the player's interior. "You feel", "you
     think", "you want", "you decide" and friends are banned outright,
     because the player owns Oliver's inside and the game owns his outside.

Rule 2 is the one that matters and the one that is easy to violate at
three in the morning, so it is a hard failure. Character *speech* is
exempt from both rules: an NPC may say "I think" all day.

Usage:  python3 tools/voice_lint.py [--strict]
Exit code 1 if any hard violation is found.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "content")

# Hard failures: these impose an interior state on the player.
BANNED = [
    r"\byou feel\b",
    r"\byou felt\b",
    r"\byou think\b",
    r"\byou thought\b",
    r"\byou believe\b",
    r"\byou want\b",
    r"\byou wanted\b",
    r"\byou wonder\b",
    r"\byou wondered\b",
    r"\byou decide\b",
    r"\byou decided\b",
    r"\byou realise\b",
    r"\byou realize\b",
    r"\byou remember\b",
    r"\byou fear\b",
    r"\byou hope\b",
    r"\byou are afraid\b",
    r"\byou're afraid\b",
    r"\byou love\b",
    r"\byou hate\b",
    r"\byou need to\b",
]

# Soft warnings under --strict: first person leaking into narration.
FIRST_PERSON = [r"\bI walk\b", r"\bI examine\b", r"\bwe walk\b"]

# Fields whose contents are narration (subject to the rules). Everything
# else - "text" inside a dialogue node, greetings, appearance - is speech
# or third-person description and is exempt.
QUOTED = re.compile(r"[\"“‘][^\"”’]*[\"”’]")


def strip_quoted(text: str) -> str:
    """Blank out quoted spans before linting.

    Narration fields legitimately contain NPC speech, and an NPC saying
    "you think I haven't paced the corridor?" is dialogue, not the narrator
    telling the player what Oliver thinks. Replacing rather than deleting
    keeps character offsets stable for the error snippets.
    """
    return QUOTED.sub(lambda m: " " * len(m.group()), text)


NARRATION_FIELDS = {
    "description",
    "repeat",
    "lucid",
    "monocle",
    "revisit",
    "ambient",
    "prompt",
    "success",
    "failure",
    "success_text",
    "failure_text",
    "premise",
    "conclusion",
    "subtitle",
    # Epilogues are pure narration and get the strictest reading of all.
    "body",
    "coda",
}


def walk_strings(node, field: str | None = None):
    """Yield (field_name, string) for every string in a nested structure."""
    if isinstance(node, str):
        if field:
            yield field, node
    elif isinstance(node, dict):
        for key, value in node.items():
            # A nested dict under a narration field (density/stage variants)
            # inherits that field's classification.
            next_field = key if key in NARRATION_FIELDS else field
            yield from walk_strings(value, next_field)
    elif isinstance(node, list):
        for item in node:
            yield from walk_strings(item, field)


def check_file(path: str, strict: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except ValueError as exc:
        return [f"{path}: invalid JSON — {exc}"], []

    rel = os.path.relpath(path, ROOT)
    for field, text in walk_strings(data):
        if field not in NARRATION_FIELDS:
            continue
        lowered = strip_quoted(text).lower()
        for pattern in BANNED:
            for match in re.finditer(pattern, lowered):
                start = max(0, match.start() - 40)
                snippet = text[start : match.end() + 40].replace("\n", " ")
                errors.append(f"{rel} [{field}]: '{match.group()}' — ...{snippet}...")
        if strict:
            for pattern in FIRST_PERSON:
                if re.search(pattern, text):
                    warnings.append(f"{rel} [{field}]: first person — {pattern}")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    all_errors: list[str] = []
    all_warnings: list[str] = []
    checked = 0

    for dirpath, _dirs, files in os.walk(CONTENT):
        for name in sorted(files):
            if not name.endswith(".json") or name == "lorebook_entries.json":
                continue
            errors, warnings = check_file(os.path.join(dirpath, name), args.strict)
            all_errors.extend(errors)
            all_warnings.extend(warnings)
            checked += 1

    for warning in all_warnings:
        print(f"warn: {warning}")
    for error in all_errors:
        print(f"FAIL: {error}")

    print(f"\nvoice_lint: {checked} file(s) checked, {len(all_errors)} violation(s).")
    return 1 if all_errors else 0


if __name__ == "__main__":
    sys.exit(main())
